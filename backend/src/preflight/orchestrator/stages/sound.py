"""Narration, music and effects for the videos that get exported (PRD §9.3).

Runs after the results are explained. Sound is an enhancement, so a variant that cannot be
finished is logged as skipped and exported silent; it never fails the run. The silent render
stays untouched on disk: it is what the simulated viewers watched.
"""

from functools import partial

from preflight.contracts import CompositionSpec, Ranking, RunState, SoundRecord, Step
from preflight.errors import PreflightError
from preflight.orchestrator.concurrency import gather_bounded
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import SoundFinisher, SoundRequest

SOUND_CONCURRENCY = 2
EXPORTED_VARIANTS = 2  # the winner and the runner-up are what the founder downloads


class SoundStage:
    """Adds sound to the ranked top ``EXPORTED_VARIANTS`` videos."""

    step = Step.AUDIO
    # DONE is reached when sound has finished or been skipped, so a resumed run repeats only this.
    completes = RunState.DONE
    title = "Adding narration, music and sound effects"

    def __init__(self, finisher: SoundFinisher, policy: StepPolicy) -> None:
        """Finish videos with ``finisher`` under ``policy``."""
        self._finisher = finisher
        self._policy = policy

    async def run(self, ctx: RunContext) -> str:
        """Give each exported variant its sound; report how many succeeded."""
        ranking = ctx.store.read(ctx.paths.ranking, Ranking)
        targets = ranking.order[:EXPORTED_VARIANTS]
        done = await gather_bounded(
            SOUND_CONCURRENCY, [partial(self._finish_one, ctx, v) for v in targets]
        )
        finished = sum(done)
        return f"Added sound to {finished} of {len(targets)} videos"

    async def _finish_one(self, ctx: RunContext, variant_id: str) -> bool:
        paths, store = ctx.paths, ctx.store
        video_sha256 = _tested_sha256(ctx, variant_id)
        if _already_finished(ctx, variant_id, video_sha256):
            return True
        request = SoundRequest(
            spec=store.read(paths.spec(variant_id), CompositionSpec),
            video_path=paths.video(variant_id),
            video_sha256=video_sha256,
            output_path=paths.final_video(variant_id),
            work_dir=paths.sound_work,
        )
        title = f"Adding sound to variant {variant_id}"
        with ctx.log.step(Step.AUDIO, title, variant_id=variant_id) as handle:
            try:
                record = await self._policy.run(partial(self._finisher.finish, request))
            except PreflightError as exc:
                handle.skip(f"Sound unavailable ({exc}); exporting the silent video")
                return False
            store.write(paths.sound(variant_id), record)
            handle.report(_summary(record))
        return True


def _tested_sha256(ctx: RunContext, variant_id: str) -> str:
    record = next(v for v in ctx.rendered_variants() if v.variant_id == variant_id)
    if record.video_sha256 is None:
        raise PreflightError(f"variant {variant_id} has no recorded video hash")
    return record.video_sha256


def _already_finished(ctx: RunContext, variant_id: str, video_sha256: str) -> bool:
    """True when a previous attempt finished this exact render, so a resume skips it."""
    path = ctx.paths.sound(variant_id)
    if not path.is_file() or not ctx.paths.final_video(variant_id).is_file():
        return False
    return ctx.store.read(path, SoundRecord).tested_video_sha256 == video_sha256


def _summary(record: SoundRecord) -> str:
    voice = f"narration by {record.voice}" if record.narrated else "music and effects only"
    return (
        f"Added sound to variant {record.variant_id}: {voice} "
        f"({record.integrated_lufs:.1f} LUFS, {record.true_peak_dbtp:.1f} dBTP)"
    )
