from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr

from preflight.config import Settings
from preflight.errors import ProviderError
from preflight.llm import CondenseProxyBackend
from preflight.motion import MotionPipeline
from preflight.storage import ProjectStore
from preflight.wiring import ProductionRunService


def build(tmp_path, **overrides):
    settings = Settings(
        data_dir=tmp_path,
        gemini_api_key=SecretStr("g"),
        condense_api_key=SecretStr("c"),
        **overrides,
    )
    http = httpx.AsyncClient()
    service = ProductionRunService(
        settings, ProjectStore(tmp_path), http, lambda: datetime.now(UTC)
    )
    return service.build_pipeline("proj-1")


def stage(pipeline, name):
    return next(s for s in pipeline._stages if type(s).__name__ == name)


def test_every_generation_goes_through_condense(tmp_path) -> None:
    pipeline = build(tmp_path)

    planner = stage(pipeline, "PlanStage")._planner
    panel = stage(pipeline, "SimulateStage")._simulators[0]
    explainer = stage(pipeline, "ExplainStage")._explainer
    assert isinstance(planner._client._backend, CondenseProxyBackend)
    assert isinstance(panel._client._backend, CondenseProxyBackend)
    assert isinstance(explainer._client._backend, CondenseProxyBackend)


def test_brain_sim_is_off_without_a_tribe_endpoint(tmp_path) -> None:
    assert build(tmp_path)._simulator_names == ("gemini_panel",)


def test_tribe_joins_the_panel_when_its_endpoint_is_set(tmp_path) -> None:
    pipeline = build(tmp_path, tribe_endpoint="http://gpu:8080")

    assert pipeline._simulator_names == ("tribe_v2", "gemini_panel")


def test_renderer_uses_the_project_directory_for_assets(tmp_path) -> None:
    renderer = stage(build(tmp_path), "RenderStage")._renderer

    assert renderer._assets_root == tmp_path / "proj-1"
    assert renderer._script.name == "render.mjs"


def test_render_stage_has_a_fail_closed_motion_pipeline(tmp_path) -> None:
    stage_obj = stage(build(tmp_path), "RenderStage")
    assert isinstance(stage_obj._motion, MotionPipeline)


def test_missing_gemini_key_is_an_explicit_error(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path)
    service = ProductionRunService(
        settings, ProjectStore(tmp_path), httpx.AsyncClient(), lambda: datetime.now(UTC)
    )

    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        service.build_pipeline("proj-1")


def test_exported_videos_get_sound_with_a_gemini_voice_by_default(tmp_path) -> None:
    studio = stage(build(tmp_path), "SoundStage")._finisher

    assert studio._speech is not None
    assert (studio._voice, studio._tts_model) == ("Leda", "gemini-3.8-flash-tts")


def test_narration_can_be_switched_off_while_music_and_effects_stay(tmp_path) -> None:
    studio = stage(build(tmp_path, narration_enabled=False), "SoundStage")._finisher

    assert studio._speech is None


def test_sound_can_be_switched_off_entirely(tmp_path) -> None:
    pipeline = build(tmp_path, sound_enabled=False)

    assert all(type(s).__name__ != "SoundStage" for s in pipeline._stages)
