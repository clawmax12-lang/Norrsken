"""FastAPI application factory (FR-01, FR-07, FR-08, FR-09 over HTTP).

Run with ``uvicorn preflight.api.app:create_app --factory``. All collaborators are injected,
so tests pass fakes and the composition root passes the real pipeline.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from preflight.config import Settings, get_settings
from preflight.intake import MAX_IMAGE_BYTES
from preflight.ports import Clock
from preflight.storage import ProjectStore

from .context import ApiContext
from .errors import install_error_handlers
from .limits import BodyLimitMiddleware
from .routes import downloads, projects
from .run_service import RunService, RunTracker
from .schemas import HealthResponse
from .sse import StreamTiming

_MAX_UPLOADS_PER_REQUEST = 7
_FORM_OVERHEAD_BYTES = 1024 * 1024
MAX_REQUEST_BYTES = _MAX_UPLOADS_PER_REQUEST * MAX_IMAGE_BYTES + _FORM_OVERHEAD_BYTES
_EXPOSED_HEADERS = ["Content-Range", "Accept-Ranges", "Content-Length", "Content-Disposition"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def create_app(
    settings: Settings | None = None,
    *,
    store: ProjectStore | None = None,
    run_service: RunService | None = None,
    stream_timing: StreamTiming | None = None,
    clock: Clock = _utc_now,
    on_shutdown: Callable[[], Awaitable[None]] | None = None,
) -> FastAPI:
    """Build the API.

    Args:
        settings: Configuration; defaults to the environment.
        store: Project persistence; defaults to ``settings.data_dir``.
        run_service: Starts runs. Without one, ``POST /run`` answers 503.
        stream_timing: Log-stream polling and heartbeat intervals.
        clock: Time source for records the API itself writes.
        on_shutdown: Releases resources the run service uses, after runs are cancelled.
    """
    settings = settings or get_settings()
    store = store or ProjectStore(settings.data_dir)
    runs = RunTracker(store, run_service, clock) if run_service else None

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if runs:
            await runs.shutdown()
        if on_shutdown:
            await on_shutdown()

    app = FastAPI(title="Preflight", lifespan=lifespan)
    app.state.context = ApiContext(
        store=store, runs=runs, stream_timing=stream_timing or StreamTiming(), clock=clock
    )
    app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Last-Event-ID", "Range"],
        expose_headers=_EXPOSED_HEADERS,
    )
    install_error_handlers(app)
    app.include_router(projects.router)
    app.include_router(downloads.router)

    configured = HealthResponse(
        runs=runs is not None,
        gemini=settings.gemini_api_key is not None,
        condense=settings.condense_api_key is not None,
        brain_sim=settings.tribe_endpoint is not None,
    )

    @app.get("/api/health")
    async def health() -> HealthResponse:
        """Liveness probe and configured providers."""
        return configured

    return app
