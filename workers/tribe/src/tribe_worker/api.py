"""HTTP surface of the worker: health, job submission, job status and artifact download."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from preflight.contracts import SimulationResult
from pydantic import BaseModel

from tribe_worker.atlas import (
    RegionGroups,
    load_destrieux_atlas,
    load_group_definitions,
    resolve_groups,
)
from tribe_worker.config import WorkerSettings
from tribe_worker.jobs import Job, JobService, JobStatus, QueueFullError
from tribe_worker.media import InvalidVideoError, UploadTooLargeError, probe_video, store_upload
from tribe_worker.predictor import TribePredictor
from tribe_worker.result_store import ARTIFACT_NAMES, ResultStore

logger = logging.getLogger(__name__)
RETRY_AFTER_SECONDS = "30"


class HealthResponse(BaseModel):
    """Model and machine state, for the go/no-go evidence and for the backend's health check."""

    model_loaded: bool
    device: str
    gpu_name: str | None
    vram_total_mb: int | None
    torch_version: str | None
    tribev2_revision: str
    checkpoint_revision: str | None
    queue_waiting: int


class JobResponse(BaseModel):
    """A job's status; ``result`` appears once it succeeded."""

    job_id: str
    status: JobStatus
    video_sha256: str
    cached: bool
    error: str | None
    result: SimulationResult | None

    @classmethod
    def of(cls, job: Job) -> "JobResponse":
        """Public view of ``job``."""
        return cls(
            job_id=job.id,
            status=job.status,
            video_sha256=job.video_sha256,
            cached=job.cached,
            error=job.error,
            result=job.result,
        )


def create_app(
    settings: WorkerSettings | None = None,
    predictor: TribePredictor | None = None,
    groups: RegionGroups | None = None,
) -> FastAPI:
    """Build the worker app.

    Production passes nothing: settings come from the environment, the predictor is the real
    :class:`Tribev2Predictor` and the region groups are resolved from the Destrieux atlas.
    Tests inject their own predictor and groups.
    """
    settings = settings or WorkerSettings()
    predictor = predictor or _real_predictor(settings)
    groups = groups or resolve_groups(
        load_group_definitions(), load_destrieux_atlas(settings.atlas_data_dir)
    )
    service = JobService(
        predictor,
        groups,
        ResultStore(settings.result_dir),
        settings.data_dir / "work",
        queue_size=settings.queue_size,
    )

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        service.start()
        preload = asyncio.create_task(_preload(predictor)) if settings.preload_model else None
        yield
        if preload is not None:
            preload.cancel()
        await service.stop()

    app = FastAPI(title="Preflight TRIBE worker", lifespan=lifespan)
    app.state.service = service
    app.state.settings = settings
    app.state.predictor = predictor
    app.include_router(_router())
    return app


def _real_predictor(settings: WorkerSettings) -> TribePredictor:
    from tribe_worker.tribev2_predictor import Tribev2Predictor  # noqa: PLC0415 - needs torch

    return Tribev2Predictor(
        model_repo=settings.model_repo,
        cache_folder=settings.feature_cache_dir,
        device=settings.device,
    )


async def _preload(predictor: TribePredictor) -> None:
    try:
        await asyncio.to_thread(predictor.load)
    except Exception:  # health keeps reporting model_loaded=false; jobs retry and fail loudly
        logger.exception("model preload failed")


def _router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health(request: Request) -> HealthResponse:
        info = request.app.state.predictor.info()
        return HealthResponse(
            model_loaded=info.loaded,
            device=info.device,
            gpu_name=info.gpu_name,
            vram_total_mb=info.vram_total_mb,
            torch_version=info.torch_version,
            tribev2_revision=info.tribev2_revision,
            checkpoint_revision=info.checkpoint_revision,
            queue_waiting=request.app.state.service.waiting,
        )

    @router.post("/jobs", status_code=202)
    async def submit_job(
        request: Request,
        video: Annotated[UploadFile, File()],
        variant_id: Annotated[str, Form(pattern=r"^[A-Z]$")],
    ) -> JSONResponse:
        job = await _accept_upload(request, video, variant_id)
        location = request.url_for("get_job", job_id=job.id).path
        return JSONResponse(
            JobResponse.of(job).model_dump(mode="json"),
            status_code=202,
            headers={"Location": location},
        )

    @router.get("/jobs/{job_id}")
    async def get_job(request: Request, job_id: str) -> JobResponse:
        return JobResponse.of(_job_or_404(request, job_id))

    @router.get("/jobs/{job_id}/artifacts/{name}")
    async def get_artifact(request: Request, job_id: str, name: str) -> FileResponse:
        job = _job_or_404(request, job_id)
        if name not in ARTIFACT_NAMES:
            raise HTTPException(404, f"unknown artifact {name!r}")
        if job.status is not JobStatus.SUCCEEDED or job.artifacts_dir is None:
            raise HTTPException(409, "job has not succeeded")
        return FileResponse(job.artifacts_dir / name)

    return router


async def _accept_upload(request: Request, video: UploadFile, variant_id: str) -> Job:
    settings: WorkerSettings = request.app.state.settings
    service: JobService = request.app.state.service
    try:
        stored = await asyncio.to_thread(
            store_upload, video.file, settings.upload_dir, max_bytes=settings.max_upload_bytes
        )
    except UploadTooLargeError as error:
        raise HTTPException(413, str(error)) from error
    try:
        probe = await probe_video(stored.path, max_duration_s=settings.max_video_duration_s)
    except InvalidVideoError as error:
        stored.path.unlink(missing_ok=True)
        raise HTTPException(422, str(error)) from error
    try:
        return service.submit(variant_id, stored.path, stored.sha256, probe)
    except QueueFullError as error:
        raise HTTPException(
            503, str(error), headers={"Retry-After": RETRY_AFTER_SECONDS}
        ) from error


def _job_or_404(request: Request, job_id: str) -> Job:
    service: JobService = request.app.state.service
    job = service.get(job_id)
    if job is None:
        raise HTTPException(404, f"unknown job {job_id!r}")
    return job
