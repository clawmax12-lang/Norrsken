"""Binary downloads: per-variant files and the four export files (FR-08)."""

import asyncio
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Path as PathParam
from fastapi.responses import FileResponse

from preflight.api.context import Context, ProjectDep
from preflight.api.errors import ApiError
from preflight.api.files import FileKind, locate_file
from preflight.contracts import VariantId
from preflight.export import ExportBundle, build_export

router = APIRouter(prefix="/api")


class ExportName(StrEnum):
    """The four files a founder downloads."""

    WINNER = "winner.mp4"
    RUNNER_UP = "runner_up.mp4"
    REPORT = "report.json"
    LAUNCH_BRIEF = "launch_brief.md"


_EXPORT_MEDIA_TYPES = {
    ExportName.WINNER: "video/mp4",
    ExportName.RUNNER_UP: "video/mp4",
    ExportName.REPORT: "application/json",
    ExportName.LAUNCH_BRIEF: "text/markdown; charset=utf-8",
}


@router.get("/projects/{project_id}/files/{kind}/{variant}")
async def get_variant_file(
    project: ProjectDep,
    context: Context,
    kind: FileKind,
    variant: Annotated[VariantId, PathParam()],
) -> FileResponse:
    """Serve a variant's video or brain artifact. Video supports HTTP Range requests."""
    served = await asyncio.to_thread(locate_file, context.store, project.paths, kind, variant)
    if served is None:
        raise ApiError(404, "not_found", f"no {kind.value} file for variant {variant}")
    return FileResponse(served.path, media_type=served.media_type)


@router.get("/projects/{project_id}/export/{name}")
async def download_export(project: ProjectDep, context: Context, name: ExportName) -> FileResponse:
    """Build the export files from the stored results and serve one as a download."""
    bundle = await asyncio.to_thread(build_export, context.store, project.id)
    path = _bundle_path(bundle, name)
    return FileResponse(path, media_type=_EXPORT_MEDIA_TYPES[name], filename=name.value)


def _bundle_path(bundle: ExportBundle, name: ExportName) -> Path:
    paths = {
        ExportName.WINNER: bundle.winner_video,
        ExportName.RUNNER_UP: bundle.runner_up_video,
        ExportName.REPORT: bundle.report,
        ExportName.LAUNCH_BRIEF: bundle.launch_brief,
    }
    path = paths[name]
    if path is None:
        raise ApiError(
            404,
            "no_runner_up",
            "only one variant finished the pretest, so there is no runner-up video",
        )
    return path
