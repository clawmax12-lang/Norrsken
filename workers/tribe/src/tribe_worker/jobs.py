"""Single-flight job queue: one inference at a time, a bounded line behind it.

The GPU holds one model and one clip at a time (PRD §11 needs roughly 28-32 GB of VRAM), so jobs
run strictly one after another. When the line is full, ``submit`` fails fast and the API answers
503 instead of letting requests pile up behind a slow GPU.
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import numpy as np
from preflight.contracts import SimulationResult

from tribe_worker.analysis import trim_to_video
from tribe_worker.atlas import RegionGroups
from tribe_worker.media import VideoProbe, ensure_audio_track
from tribe_worker.predictor import Prediction, TribePredictor
from tribe_worker.result_builder import RunFacts, build_result
from tribe_worker.result_store import ResultStore, StoredResult

logger = logging.getLogger(__name__)


class JobStatus(StrEnum):
    """Lifecycle of one analysis job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class QueueFullError(RuntimeError):
    """Too many jobs are already waiting."""


@dataclass
class Job:
    """One analysis request and its progress. Mutated only by the service."""

    id: str
    variant_id: str
    video_sha256: str
    video_path: Path
    probe: VideoProbe
    status: JobStatus = JobStatus.QUEUED
    cached: bool = False
    error: str | None = None
    result: SimulationResult | None = None
    artifacts_dir: Path | None = field(default=None, repr=False)


class JobService:
    """Owns the queue, the runner task and the result cache lookups."""

    def __init__(
        self,
        predictor: TribePredictor,
        groups: RegionGroups,
        store: ResultStore,
        work_dir: Path,
        *,
        queue_size: int,
        new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        """Wire the service; call :meth:`start` inside a running event loop."""
        self._predictor = predictor
        self._groups = groups
        self._store = store
        self._work_dir = work_dir
        self._new_id = new_id
        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=queue_size)
        self._jobs: dict[str, Job] = {}
        self._runner: asyncio.Task[None] | None = None
        self._inferences_done = 0

    @property
    def waiting(self) -> int:
        """Jobs queued behind the running one."""
        return self._queue.qsize()

    def start(self) -> None:
        """Start the single runner task."""
        self._runner = asyncio.create_task(self._run_forever())

    async def stop(self) -> None:
        """Cancel the runner; a running inference finishes its thread but is not awaited."""
        if self._runner is not None:
            self._runner.cancel()
            await asyncio.gather(self._runner, return_exceptions=True)

    def get(self, job_id: str) -> Job | None:
        """Look a job up by id."""
        return self._jobs.get(job_id)

    def submit(
        self, variant_id: str, video_path: Path, video_sha256: str, probe: VideoProbe
    ) -> Job:
        """Register a job; an identical video and model revision is answered from the cache.

        Raises:
            QueueFullError: the bounded queue has no room.
        """
        job = Job(self._new_id(), variant_id, video_sha256, video_path, probe)
        if not self._answer_from_cache(job):
            try:
                self._queue.put_nowait(job)
            except asyncio.QueueFull as error:
                raise QueueFullError("TRIBE worker queue is full") from error
        self._jobs[job.id] = job
        return job

    def _answer_from_cache(self, job: Job) -> bool:
        revision = self._predictor.info().revision
        if revision is None:
            return False
        stored = self._store.get(job.video_sha256, revision)
        if stored is None:
            return False
        self._finish(job, stored, cached=True)
        return True

    def _finish(self, job: Job, stored: StoredResult, *, cached: bool) -> None:
        job.result = stored.result.model_copy(update={"variant_id": job.variant_id})
        job.artifacts_dir = stored.directory
        job.cached = cached
        job.status = JobStatus.SUCCEEDED

    async def _run_forever(self) -> None:
        while True:
            job = await self._queue.get()
            await self._run(job)
            self._queue.task_done()

    async def _run(self, job: Job) -> None:
        job.status = JobStatus.RUNNING
        try:
            await asyncio.to_thread(self._predictor.load)
            if not self._answer_from_cache(job):
                self._finish(job, await self._analyse(job), cached=False)
        except Exception as error:  # job boundary: record the failure, keep the worker alive
            logger.exception("job %s failed", job.id)
            job.status = JobStatus.FAILED
            job.error = f"{type(error).__name__}: {error}"

    async def _analyse(self, job: Job) -> StoredResult:
        prediction, facts = await self._infer(job)
        revision = facts.info.revision
        if revision is None:
            raise RuntimeError("model finished inference without a known revision")
        trimmed = trim_to_video(prediction, job.probe.duration_s)
        result = build_result(
            variant_id=job.variant_id,
            video_sha256=job.video_sha256,
            probe=job.probe,
            prediction=trimmed,
            groups=self._groups,
            facts=facts,
        )
        activity = trimmed.activity.astype(np.float16)
        return self._store.save(result, revision, activity, self._groups.to_json())

    async def _infer(self, job: Job) -> tuple[Prediction, RunFacts]:
        """Run the model on the job's video, timing only the inference itself."""
        self._work_dir.mkdir(parents=True, exist_ok=True)
        model_input = await ensure_audio_track(
            job.video_path, job.probe, self._work_dir / f"{job.video_sha256}-silent.mp4"
        )
        try:
            started = time.monotonic()
            prediction = await asyncio.to_thread(self._predictor.predict, model_input)
            seconds = time.monotonic() - started
        finally:
            if model_input != job.video_path:
                model_input.unlink(missing_ok=True)
        facts = RunFacts(
            info=self._predictor.info(),
            inference_seconds=seconds,
            warm_run=self._inferences_done > 0,
            silent_audio_added=model_input != job.video_path,
        )
        self._inferences_done += 1
        return prediction, facts
