"""FR-01: turn a submitted brief form and its uploads into a saved project.

The service validates everything before it touches the disk, writes uploads under names it
generates itself (client filenames are never trusted), and leaves a project that the
orchestrator can run: ``brief.json`` plus a ``run.json`` in ``BRIEF_RECEIVED``.
"""

import shutil
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import ValidationError

from preflight.contracts import Brief, RenderMode, RunRecord, RunState
from preflight.contracts.brief import MAX_SCREENSHOTS, MIN_SCREENSHOTS
from preflight.errors import PreflightValidationError
from preflight.ports import Clock
from preflight.storage import ProjectPaths, ProjectStore

from .images import ValidatedImage, validate_image


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_project_id() -> str:
    """Unguessable, filesystem-safe id that satisfies ``ProjectStore``'s id pattern."""
    return uuid.uuid4().hex[:16]


@dataclass(frozen=True)
class BriefForm:
    """The text fields of the intake form, exactly as submitted."""

    product_name: str
    one_liner: str
    goal: str
    audience: str
    goal_note: str | None = None
    brand_color: str | None = None
    render_mode: str = RenderMode.SHOWCASE.value
    buyer_cta: str | None = None
    proof_points: str | None = None


def create_project(
    store: ProjectStore,
    form: BriefForm,
    screenshots: Sequence[bytes],
    logo: bytes | None = None,
    *,
    clock: Clock = _utc_now,
    new_project_id: Callable[[], str] = _new_project_id,
) -> Brief:
    """Validate a submission, persist the project and return its :class:`Brief`.

    Nothing is written unless the whole submission is valid, and a failure while writing
    removes the half-created project.

    Raises:
        PreflightValidationError: A field or upload breaks the FR-01 rules.
    """
    images = _validate_screenshots(screenshots)
    logo_image = validate_image(logo, label="logo") if logo is not None else None
    brief = _build_brief(form, new_project_id(), images, logo_image)

    paths = store.create(brief.project_id)
    try:
        _write_uploads(paths, brief, images, logo_image)
        store.write(paths.brief, brief)
        store.write(
            paths.run,
            RunRecord(
                project_id=brief.project_id, state=RunState.BRIEF_RECEIVED, updated_at=clock()
            ),
        )
    except BaseException:
        shutil.rmtree(paths.root, ignore_errors=True)
        raise
    return brief


def _validate_screenshots(screenshots: Sequence[bytes]) -> list[ValidatedImage]:
    if not MIN_SCREENSHOTS <= len(screenshots) <= MAX_SCREENSHOTS:
        raise PreflightValidationError(
            f"upload {MIN_SCREENSHOTS} to {MAX_SCREENSHOTS} screenshots, got {len(screenshots)}"
        )
    return [
        validate_image(content, label=f"screenshot {number}")
        for number, content in enumerate(screenshots, start=1)
    ]


def _build_brief(
    form: BriefForm,
    project_id: str,
    screenshots: Sequence[ValidatedImage],
    logo: ValidatedImage | None,
) -> Brief:
    try:
        return Brief.model_validate(
            {
                "project_id": project_id,
                "product_name": form.product_name,
                "one_liner": form.one_liner,
                "screenshots": [
                    _upload_name(f"screenshot-{number}", image)
                    for number, image in enumerate(screenshots, start=1)
                ],
                "goal": form.goal,
                "goal_note": _blank_to_none(form.goal_note),
                "audience": form.audience,
                "buyer_cta": _blank_to_none(form.buyer_cta),
                "proof_points": _blank_to_none(form.proof_points),
                "brand_color": _blank_to_none(form.brand_color),
                "logo": _upload_name("logo", logo) if logo else None,
                "render_mode": form.render_mode or RenderMode.SHOWCASE.value,
            }
        )
    except ValidationError as exc:
        raise PreflightValidationError(_describe(exc)) from exc


def _upload_name(stem: str, image: ValidatedImage) -> str:
    """Project-relative path of an upload, as stored in the brief."""
    return f"uploads/{stem}.{image.extension}"


def _blank_to_none(value: str | None) -> str | None:
    """Optional form fields arrive as empty strings when left blank."""
    return value if value and value.strip() else None


def _describe(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
        for issue in error.errors()
    )


def _write_uploads(
    paths: ProjectPaths,
    brief: Brief,
    screenshots: Sequence[ValidatedImage],
    logo: ValidatedImage | None,
) -> None:
    for relative, image in zip(brief.screenshots, screenshots, strict=True):
        (paths.root / relative).write_bytes(image.content)
    if brief.logo and logo:
        (paths.root / brief.logo).write_bytes(logo.content)
