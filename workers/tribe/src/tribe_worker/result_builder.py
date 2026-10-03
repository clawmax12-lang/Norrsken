"""Assemble the :class:`SimulationResult` the backend consumes from one trimmed prediction."""

from dataclasses import dataclass

from preflight.contracts import BrainArtifact, SimulationResult, SimulatorName

from tribe_worker.analysis import (
    PRIMARY_SERIES,
    RESPONSE_REFERENCE,
    SCALE_VERSION,
    find_events,
    reduce_to_series,
)
from tribe_worker.atlas import ATLAS_SLUG, RegionGroups
from tribe_worker.media import VideoProbe
from tribe_worker.predictor import Prediction, PredictorInfo

ACTIVITY_ARTIFACT = "activity.npy"
GROUPS_ARTIFACT = "groups.json"
HEMODYNAMIC_NOTE = (
    "tribev2 predictions already compensate a 5 s hemodynamic lag; timestamps are the segment "
    "starts the model returned and no further shift was applied."
)


@dataclass(frozen=True)
class RunFacts:
    """Environment and timings of one inference, recorded for the go/no-go evidence (PRD §14.2)."""

    info: PredictorInfo
    inference_seconds: float
    warm_run: bool
    silent_audio_added: bool


def build_result(
    *,
    variant_id: str,
    video_sha256: str,
    probe: VideoProbe,
    prediction: Prediction,
    groups: RegionGroups,
    facts: RunFacts,
) -> SimulationResult:
    """Translate a genuine prediction into the shared contract; artifacts are named, not embedded.

    ``prediction`` must already be trimmed to the video (see ``analysis.trim_to_video``).
    Artifact paths are bare file names; the consumer rewrites them to its own storage.
    """
    series = reduce_to_series(prediction.activity, groups)
    timestamps = prediction.start_times_s
    return SimulationResult(
        variant_id=variant_id,
        simulator=SimulatorName.TRIBE_V2,
        version=f"tribev2 {facts.info.revision}; atlas {ATLAS_SLUG}; scale {SCALE_VERSION}",
        hz=prediction.hz,
        video_sha256=video_sha256,
        duration_s=probe.duration_s,
        timestamps_s=timestamps,
        series=series,
        primary_series=PRIMARY_SERIES,
        events=find_events(timestamps, series, groups),
        precomputed=False,
        brain=BrainArtifact(
            n_vertices=groups.n_vertices,
            activity_path=ACTIVITY_ARTIFACT,
            atlas=groups.atlas,
            groups_path=GROUPS_ARTIFACT,
        ),
        meta=_meta(probe, facts),
    )


def _meta(probe: VideoProbe, facts: RunFacts) -> dict[str, object]:
    info = facts.info
    return {
        "device": info.device,
        "gpu_name": info.gpu_name,
        "vram_total_mb": info.vram_total_mb,
        "torch_version": info.torch_version,
        "tribev2_revision": info.tribev2_revision,
        "checkpoint_revision": info.checkpoint_revision,
        "model_load_seconds": info.load_seconds,
        "inference_seconds": round(facts.inference_seconds, 3),
        "warm_run": facts.warm_run,
        "silent_audio_track_added": facts.silent_audio_added,
        "video_width": probe.width,
        "video_height": probe.height,
        "response_scale": SCALE_VERSION,
        "response_reference": RESPONSE_REFERENCE,
        "hemodynamic_offset": HEMODYNAMIC_NOTE,
    }
