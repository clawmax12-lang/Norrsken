"""Schedule one consent-bound finalization per project, with a cross-process file lock."""

import asyncio
import fcntl
from collections.abc import Callable
from functools import partial
from typing import IO

from preflight.config import Settings
from preflight.contracts.finalization import FinalizationRecord, FinalizeCommand, FinalStatus
from preflight.errors import PreflightError, PreflightValidationError, ProviderError
from preflight.ports import Clock
from preflight.storage import ProjectStore

from .job import FinalizationJob
from .source import FinalSource, read_source

JobFactory = Callable[[str, FinalSource], FinalizationJob]


class FinalizationService:
    """Background work belongs on the durable Python renderer host, not a Vercel function."""

    def __init__(
        self,
        settings: Settings,
        store: ProjectStore,
        factory: JobFactory,
        clock: Clock,
    ) -> None:
        """Inject composition root; credentials never come from request bodies or headers."""
        self._settings, self._store = settings, store
        self._factory, self._clock = factory, clock
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def start(self, project_id: str, command: FinalizeCommand) -> FinalizationRecord:
        """Validate explicit approval before any paid call; identical requests are idempotent.

        A completed final asset is reused, never purchased again. A failed attempt can resume
        only with its original command id and explicit confirmation; at most two Opus attempts
        are allowed across requests/crashes. Render and simulation checkpoints are reused.
        """
        self._configured(command.director)
        source = read_source(self._store, project_id, command, self._settings)
        paths = self._store.paths(project_id)
        paths.opus_dir.mkdir(exist_ok=True)
        lock = (paths.opus_dir / "job.lock").open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            record = self._store.read(paths.finalization, FinalizationRecord)
            _check_source(record, source, command)
            return record
        try:
            record = self._prepare(project_id, source, command)
            if record.status is FinalStatus.DONE:
                lock.close()
                return record
            self._tasks[project_id] = asyncio.create_task(
                self._supervise(project_id, source, command, lock)
            )
            return record
        except BaseException:
            lock.close()
            raise

    async def shutdown(self) -> None:
        """Cancel tasks and release locks on shutdown; persisted checkpoints remain resumable."""
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def _configured(self, director: str) -> None:
        if self._settings.gemini_api_key is None:
            raise ProviderError("GEMINI_API_KEY is required to pretest the finished video")
        if director == "gemini":
            return
        if (
            self._settings.anthropic_api_key is None
            or not self._settings.anthropic_api_key.get_secret_value().strip()
        ):
            raise ProviderError("ANTHROPIC_API_KEY is not set on the backend")
        if (
            self._settings.condense_api_key is None
            or not self._settings.condense_api_key.get_secret_value().strip()
        ):
            raise ProviderError("CONDENSE_API_KEY is required for Opus finalization")

    def _prepare(
        self, project_id: str, source: FinalSource, command: FinalizeCommand
    ) -> FinalizationRecord:
        path = self._store.paths(project_id).finalization
        if path.is_file():
            record = self._store.read(path, FinalizationRecord)
            _check_source(record, source, command)
            if record.status is FinalStatus.DONE:
                return record
            if record.command_id != command.command_id:
                raise PreflightValidationError("Resume with the existing finalization command id")
            if record.director != command.director:
                raise PreflightValidationError(
                    f"This finish was started with {record.director}; resume it with the same "
                    "director"
                )
            record = record.model_copy(
                update={"status": FinalStatus.QUEUED, "error": None, "updated_at": self._clock()}
            )
        else:
            record = FinalizationRecord(
                command_id=command.command_id,
                variant_id=command.variant_id,
                source_video_sha256=command.source_video_sha256,
                source_fingerprint=source.fingerprint,
                status=FinalStatus.QUEUED,
                updated_at=self._clock(),
                director=command.director,
            )
        self._store.write(path, record)
        return record

    async def _supervise(
        self, project_id: str, source: FinalSource, command: FinalizeCommand, lock: IO[str]
    ) -> None:
        job = None
        try:
            job = self._factory(project_id, source)
            await job.run(verify_source=partial(self._verify_source, project_id, source, command))
        except asyncio.CancelledError:
            if job:
                job.fail("Finalization interrupted; confirm resume to continue from checkpoints")
            raise
        except Exception as exc:
            # Only our sanitized domain errors are visible. No raw HTTP/SDK errors or secrets.
            message = (
                str(exc)
                if isinstance(exc, PreflightError)
                else f"Finalization failed ({type(exc).__name__})"
            )
            if job:
                job.fail(message)
            else:
                self._fail_start(project_id, message)
        finally:
            lock.close()
            self._tasks.pop(project_id, None)

    def _fail_start(self, project_id: str, message: str) -> None:
        path = self._store.paths(project_id).finalization
        record = self._store.read(path, FinalizationRecord)
        self._store.write(
            path,
            record.model_copy(
                update={"status": FinalStatus.FAILED, "error": message, "updated_at": self._clock()}
            ),
        )

    def _verify_source(
        self, project_id: str, source: FinalSource, command: FinalizeCommand
    ) -> None:
        current = read_source(self._store, project_id, command, self._settings)
        if current.fingerprint != source.fingerprint:
            raise PreflightValidationError(
                "Source inputs changed during finalization; final evidence withheld"
            )


def _check_source(
    record: FinalizationRecord, source: FinalSource, command: FinalizeCommand
) -> None:
    if record.source_fingerprint != source.fingerprint or record.variant_id != command.variant_id:
        raise PreflightValidationError("Finalization source changed; start a new project/pretest")
