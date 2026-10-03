"""Briefs, runs, the live log and results (FR-01, FR-07, FR-09)."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Query, Response, UploadFile
from fastapi.responses import StreamingResponse

from preflight.api.context import Context, ProjectDep
from preflight.api.errors import ApiError
from preflight.api.results import build_results
from preflight.api.schemas import ProjectResponse, ResultsResponse
from preflight.api.sse import start_offset, stream_activity_log
from preflight.contracts import Brief, Goal, RunRecord
from preflight.intake import MAX_IMAGE_BYTES, BriefForm, create_project

router = APIRouter(prefix="/api")


def brief_form(
    product_name: Annotated[str, Form()],
    one_liner: Annotated[str, Form()],
    goal: Annotated[Goal, Form()],
    audience: Annotated[str, Form()],
    goal_note: Annotated[str | None, Form()] = None,
    brand_color: Annotated[str | None, Form()] = None,
) -> BriefForm:
    """Collect the text fields of the multipart intake form."""
    return BriefForm(
        product_name=product_name,
        one_liner=one_liner,
        goal=goal.value,
        audience=audience,
        goal_note=goal_note,
        brand_color=brand_color,
    )


@router.post("/briefs", status_code=201)
async def submit_brief(
    context: Context,
    response: Response,
    form: Annotated[BriefForm, Depends(brief_form)],
    screenshots: Annotated[list[UploadFile], File()],
    logo: Annotated[UploadFile | None, File()] = None,
) -> Brief:
    """Validate the intake form and uploads, save the project and return its brief."""
    screenshot_bytes = [await _read_upload(upload) for upload in screenshots]
    logo_bytes = await _read_optional_logo(logo)
    brief = await asyncio.to_thread(
        create_project, context.store, form, screenshot_bytes, logo_bytes, clock=context.clock
    )
    response.headers["Location"] = f"/api/projects/{brief.project_id}"
    return brief


async def _read_upload(upload: UploadFile) -> bytes:
    """Read at most one byte over the per-file limit; intake rejects the oversize file."""
    return await upload.read(MAX_IMAGE_BYTES + 1)


async def _read_optional_logo(logo: UploadFile | None) -> bytes | None:
    """Browsers send an empty, nameless file part when no logo was chosen; that means none."""
    if logo is None:
        return None
    content = await _read_upload(logo)
    return content if content or logo.filename else None


@router.post("/projects/{project_id}/run", status_code=202)
async def start_run(project: ProjectDep, context: Context) -> RunRecord:
    """Start the run in the background; asking again while it runs changes nothing."""
    if context.runs is None:
        raise ApiError(503, "run_service_unavailable", "this server has no run service configured")
    context.runs.start(project.id)
    return await asyncio.to_thread(context.store.read, project.paths.run, RunRecord)


@router.get("/projects/{project_id}")
async def get_project(project: ProjectDep, context: Context) -> ProjectResponse:
    """The run record and brief of one project."""
    run = await asyncio.to_thread(context.store.read, project.paths.run, RunRecord)
    brief = await asyncio.to_thread(context.store.read, project.paths.brief, Brief)
    return ProjectResponse(run=run, brief=brief)


@router.get("/projects/{project_id}/log")
async def stream_log(
    project: ProjectDep,
    context: Context,
    last_event_id: Annotated[str | None, Header()] = None,
    from_offset: Annotated[int, Query(alias="from", ge=0)] = 0,
) -> StreamingResponse:
    """Server-Sent Events: replay the activity log, then follow it until the run ends."""
    frames = stream_activity_log(
        context.store,
        project.id,
        start=start_offset(last_event_id, from_offset),
        timing=context.stream_timing,
    )
    return StreamingResponse(
        frames,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/projects/{project_id}/results")
async def get_results(project: ProjectDep, context: Context) -> ResultsResponse:
    """Ranking, report and per-variant concept and simulation results, as far as they exist."""
    return await asyncio.to_thread(build_results, context.store, project.id)
