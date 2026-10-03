"""Per-app dependencies, and the dependency that resolves a project from the URL."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from preflight.errors import PreflightValidationError
from preflight.finalization.service import FinalizationService
from preflight.ports import Clock
from preflight.storage import ProjectPaths, ProjectStore

from .errors import ApiError
from .run_service import RunTracker
from .sse import StreamTiming


@dataclass(frozen=True)
class ApiContext:
    """Everything the routes need, injected once by ``create_app``.

    ``runs`` is ``None`` when the app was built without a run service; starting a run then
    answers 503 instead of pretending to work.
    """

    store: ProjectStore
    runs: RunTracker | None
    stream_timing: StreamTiming
    clock: Clock
    finals: FinalizationService | None = None


def get_context(request: Request) -> ApiContext:
    """FastAPI dependency returning the context installed on the app."""
    context: ApiContext = request.app.state.context
    return context


Context = Annotated[ApiContext, Depends(get_context)]


@dataclass(frozen=True)
class Project:
    """A project that exists on disk."""

    id: str
    paths: ProjectPaths


def get_project(project_id: str, context: Context) -> Project:
    """Resolve ``{project_id}``; unknown and malformed ids are both a plain 404."""
    try:
        paths = context.store.paths(project_id)
    except PreflightValidationError as exc:
        raise ApiError(404, "not_found", "project not found") from exc
    if not paths.root.is_dir():
        raise ApiError(404, "not_found", "project not found")
    return Project(id=project_id, paths=paths)


ProjectDep = Annotated[Project, Depends(get_project)]
