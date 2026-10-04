"""Narration, music and effects for every rendered variant (PRD §9.3).

Runs after picture render and before simulated viewers, so the pretest watches the mixed
file. Sound is an enhancement: a variant that cannot be finished is logged as skipped and
stays silent; it never fails the run.
"""

from functools import partial

from preflight.contracts import CompositionSpec, RenderStatus, RunState, SoundRecord, Step
from preflight.errors import PreflightError
from preflight.hashing import sha256_file
from preflight.motion.scene import MotionSpec
from preflight.orchestrator.concurrency import gather_bounded
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import SoundFinisher, SoundRequest

SOUND_CONCURRENCY = 1


class SoundStage:
    """Adds sound to every rendered variant before simulation."""

    step = Step.AUDIO
    completes = RunState.MIXED
    title = "Adding narration, music and sound effects"

    def __init__(self, finisher: SoundFinisher, policy: StepPolicy) -> None:
        """Finish videos with ``finisher`` under ``policy``."""
        self._finisher = finisher
        self._policy = policy

    async def run(self, ctx: RunContext) -> str:
        """Give each rendered variant its sound."""
        targets = [v.variant_id for v in ctx.rendered_variants()]
        await gather_bounded(
            SOUND_CONCURRENCY, [partial(self._finish_one, ctx, v) for v in targets]
        )
        finished = sum(1 for v in targets if ctx.paths.final_video(v).is_file())
        return f"Added sound to {finished} of {len(targets)} videos"

    async def _finish_one(self, ctx: RunContext, variant_id: str) -> bool:
        paths, store = ctx.paths, ctx.store
        video_sha256 = _tested_sha256(ctx, variant_id)
        if _already_finished(ctx, variant_id, video_sha256):
            return True
        motion_path = paths.motion_spec(variant_id)
        motion = store.read(motion_path, MotionSpec) if motion_path.is_file() else None
        request = SoundRequest(
            spec=store.read(paths.spec(variant_id), CompositionSpec),
            video_path=paths.video(variant_id),
            video_sha256=video_sha256,
            output_path=paths.final_video(variant_id),
            work_dir=paths.sound_work,
            motion_spec=motion,
            allow_narration=True,
        )
        title = f"Adding sound to variant {variant_id}"
        with ctx.log.step(Step.AUDIO, title, variant_id=variant_id) as handle:
            try:
                record = await self._policy.run(partial(self._finisher.finish, request))
            except PreflightError as exc:
                handle.skip(f"Sound unavailable ({exc}); exporting the silent video")
                return False
            store.write(paths.sound(variant_id), record)
            _point_variant_at_mix(ctx, variant_id, record)
            handle.report(_summary(record))
        return True


def _tested_sha256(ctx: RunContext, variant_id: str) -> str:
    """Hash of the silent picture file (never the mixed final)."""
    sound_path = ctx.paths.sound(variant_id)
    if sound_path.is_file():
        return ctx.store.read(sound_path, SoundRecord).tested_video_sha256
    silent = ctx.paths.video(variant_id)
    if not silent.is_file():
        raise PreflightError(f"variant {variant_id} has no silent video")
    return sha256_file(silent)


def _already_finished(ctx: RunContext, variant_id: str, picture_sha256: str) -> bool:
    """True when a previous attempt mixed this exact picture, so a resume skips it."""
    path = ctx.paths.sound(variant_id)
    if not path.is_file() or not ctx.paths.final_video(variant_id).is_file():
        return False
    record = ctx.store.read(path, SoundRecord)
    return record.tested_video_sha256 == picture_sha256


def _point_variant_at_mix(ctx: RunContext, variant_id: str, sound: SoundRecord) -> None:
    """Simulators hash-match the mixed file the panel will watch."""
    current = next(v for v in ctx.tracker.record.variants if v.variant_id == variant_id)
    ctx.tracker.update_variant(
        current.model_copy(
            update={
                "video_path": str(ctx.paths.final_video(variant_id).relative_to(ctx.paths.root)),
                "video_sha256": sound.final_video_sha256,
                "render_status": RenderStatus.RENDERED,
            }
        )
    )


def _summary(record: SoundRecord) -> str:
    voice = f"narration by {record.voice}" if record.narrated else "music and effects only"
    return (
        f"Added sound to variant {record.variant_id}: {voice} "
        f"({record.integrated_lufs:.1f} LUFS, {record.true_peak_dbtp:.1f} dBTP)"
    )
