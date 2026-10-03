"""The explicitly confirmed last step; all GET/download operations are inference-free."""

import asyncio
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse

from preflight.api.context import Context, ProjectDep
from preflight.api.errors import ApiError
from preflight.contracts.finalization import FinalizationRecord, FinalizeCommand, FinalStatus
from preflight.errors import PreflightValidationError, ProviderError
from preflight.hashing import sha256_file

router = APIRouter(prefix="/api/projects/{project_id}/finalization")


@router.post("", status_code=202)
async def start_finalization(
    project: ProjectDep, context: Context, command: FinalizeCommand
) -> FinalizationRecord:
    """Queue one budget-bound winner finish; never accept arbitrary code/specs or credentials."""
    if context.finals is None:
        raise ApiError(503, "finalization_unavailable", "Opus finalization is not connected")
    try:
        return context.finals.start(project.id, command)
    except ProviderError as exc:
        raise ApiError(503, "finalization_not_configured", str(exc)) from exc
    except PreflightValidationError as exc:
        raise ApiError(409, "finalization_conflict", str(exc)) from exc


@router.get("")
async def get_finalization(project: ProjectDep, context: Context) -> FinalizationRecord | None:
    """Read the job, including errors. No Opus/render/simulator work starts here."""
    if not project.paths.finalization.is_file():
        return None
    return await asyncio.to_thread(
        context.store.read, project.paths.finalization, FinalizationRecord
    )


@router.get("/{kind}")
async def download_finalization(
    project: ProjectDep, context: Context, kind: Literal["video", "report"]
) -> FileResponse:
    """Download only a completed exact-byte final asset; never attach the original verdict."""
    record = await asyncio.to_thread(
        context.store.read, project.paths.finalization, FinalizationRecord
    )
    if record.status is not FinalStatus.DONE:
        raise ApiError(
            409, "finalization_incomplete", "The final video has not completed its own pretest"
        )
    video = project.paths.opus_dir / ("final.mp4" if record.sound else "picture.mp4")
    if (
        not video.resolve().is_relative_to(project.paths.root.resolve())
        or not video.is_file()
        or await asyncio.to_thread(sha256_file, video) != record.video_sha256
    ):
        raise ApiError(409, "finalization_changed", "The final artifact is missing or changed")
    return FileResponse(
        video if kind == "video" else project.paths.finalization,
        media_type="video/mp4" if kind == "video" else "application/json",
        filename="final.mp4" if kind == "video" else "final_report.json",
    )
