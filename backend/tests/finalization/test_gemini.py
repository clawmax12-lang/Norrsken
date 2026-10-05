from itertools import pairwise
from typing import Any

import pytest

from preflight.contracts import BeatKind, Reason, Report, Shot, TokenSavings
from preflight.contracts.finalization import GeminiFinish
from preflight.errors import PreflightValidationError
from preflight.finalization.gemini import GeminiDirector, apply_finish, problems, tidy
from preflight.finalization.source import FinalSource
from preflight.generation.compose import compose
from preflight.llm.client import Measured
from preflight.llm.ledger import CallUsage
from preflight.llm.parts import MediaPart
from tests.factories import make_brief, make_concept


def source() -> FinalSource:
    brief, concept = make_brief(), make_concept()
    spec = compose(brief, concept, ())
    report = Report(
        winner="A",
        runner_up=None,
        reasons={"A": (Reason(t=4.0, scene_index=1, text="Viewers dropped on scene 1"),)},
        next_time=(),
        token_savings=TokenSavings(),
        brain_sim=False,
    )
    return FinalSource(brief, concept, spec, report, "f" * 64)


FOCUS = (0.1, 0.5, 0.4, 0.1)


TWO_TAPS = (FOCUS, (0.5, 0.2, 0.2, 0.1))


def finish(*shots: str, taps: Any = TWO_TAPS, emphasis: str | None = "Notes") -> GeminiFinish:
    return GeminiFinish.model_validate(
        {"scenes": [{"shot": shot, "taps": taps, "emphasis": emphasis} for shot in shots]}
    )


GOOD = ("close_up", "takeover", "tilt", "close_up")


def test_a_good_finish_reframes_every_scene_and_keeps_copy_voice_and_timing() -> None:
    src = source()

    final = apply_finish(src.brief, src.concept, src.spec, finish(*GOOD))

    assert [s.shot for s in final.scenes[:-1]] == [Shot(shot) for shot in GOOD]
    assert all(s.focus == (0.1, 0.5, 0.4, 0.1) for s in final.scenes[:-1])
    assert [s.text for s in final.scenes] == [s.text for s in src.spec.scenes]
    assert [(s.start_frame, s.end_frame) for s in final.scenes] == [
        (s.start_frame, s.end_frame) for s in src.spec.scenes
    ]
    kinds = [beat.kind for beat in final.beats]
    assert kinds.count(BeatKind.TAP) == 9  # two per scene before the end card, one on its button
    assert kinds.count(BeatKind.PUNCH) == 8


def test_the_ad_cut_taps_through_every_element_in_order_on_one_clock() -> None:
    src = source()
    taps = (FOCUS, (0.5, 0.2, 0.2, 0.1), (0.3, 0.8, 0.4, 0.1))

    final = apply_finish(src.brief, src.concept, src.spec, finish(*GOOD, taps=taps))

    for index, scene in enumerate(final.scenes[:-1]):
        beats = [b for b in final.beats if b.scene == index]
        tapped = [b for b in beats if b.kind is BeatKind.TAP]
        punches = [b for b in beats if b.kind is BeatKind.PUNCH]
        assert len(tapped) >= 2
        assert tapped[0].point == (0.3, 0.55)
        assert [b.frame + 4 for b in tapped] == [b.frame for b in punches]
        assert all(b.frame - a.frame >= 24 for a, b in pairwise(tapped))
        assert scene.start_frame < tapped[0].frame and punches[-1].frame + 10 < scene.end_frame
    assert final.scenes[0].focus == FOCUS


def test_problems_name_what_the_repair_call_must_fix() -> None:
    spec = source().spec

    assert problems(finish(*GOOD), spec) == []
    one_tap = problems(finish(*GOOD, taps=(FOCUS,)), spec)
    assert "scene 0: give 2 or 3 taps on different elements, not 1" in one_tap
    assert (
        problems(
            finish("hero", "hero", "close_up", "tilt", taps=(), emphasis="x"), spec, strict=False
        )
        == []
    )
    assert "use hero at most once" in " ".join(
        problems(finish("hero", "close_up", "hero", "tilt"), spec)
    )
    assert problems(finish("hero", "tilt"), spec) == [
        "return exactly 4 scenes, one per scene before the end card"
    ]
    found = problems(finish("hero", "hero", "close_up", "tilt", emphasis="Bananas"), spec)
    assert any("'Bananas' is not in" in p for p in found)
    assert "never use the same shot in two scenes in a row" in found
    assert any(
        "a close_up needs at least one tap" in p for p in problems(finish(*GOOD, taps=()), spec)
    )
    assert any(
        "inside the image" in p
        for p in problems(finish(*GOOD, taps=(FOCUS, (0.8, 0.5, 0.4, 0.1))), spec)
    )


def test_a_sloppy_answer_is_mended_instead_of_failing_the_finish() -> None:
    spec = source().spec
    sloppy = GeminiFinish.model_validate(
        {
            "scenes": [
                {"shot": "close_up", "taps": [], "emphasis": "Tack!"},
                {"shot": "takeover", "taps": [(0.8, 0.5, 0.4, 0.1), (0.1, 0.1, 0.0, 0.2)]},
                {"shot": "takeover", "taps": [FOCUS], "emphasis": "organise notes"},
                {"shot": "tilt", "taps": [FOCUS, FOCUS]},
            ]
        }
    )

    tidied = tidy(sloppy, spec)

    assert [s.shot for s in tidied.scenes] == [
        Shot.TAKEOVER,
        Shot.CLOSE_UP,
        Shot.TAKEOVER,
        Shot.TILT,
    ]
    assert tidied.scenes[0].emphasis is None
    assert tidied.scenes[1].taps == ((0.8, 0.5, 0.2, 0.1),)
    assert tidied.scenes[3].taps == (FOCUS,)
    assert problems(tidied, spec, strict=False) == []


def test_the_ad_opens_close_and_shows_the_small_phone_at_most_once() -> None:
    spec = source().spec

    tidied = tidy(finish("tilt", "hero", "tilt", "hero"), spec)

    assert [s.shot for s in tidied.scenes] == [
        Shot.CLOSE_UP,
        Shot.HERO,
        Shot.CLOSE_UP,
        Shot.TAKEOVER,
    ]


def test_a_focus_on_the_whole_image_is_moved_into_a_mockups_display() -> None:
    src = source()
    scenes = tuple(s.model_copy(update={"crop": (0.25, 0.0, 0.5, 1.0)}) for s in src.concept.scenes)
    cropped = src.concept.model_copy(update={"scenes": scenes})

    final = apply_finish(src.brief, cropped, src.spec, finish(*GOOD, taps=((0.3, 0.5, 0.2, 0.1),)))

    assert final.scenes[1].focus == (0.1, 0.5, 0.4, 0.1)


def test_a_finish_that_breaks_the_template_is_rejected() -> None:
    src = source()
    concept = src.concept.model_copy(
        update={
            "scenes": tuple(s.model_copy(update={"t_end": s.t_end}) for s in src.concept.scenes)
        }
    )
    shifted = src.spec.model_copy(
        update={
            "scenes": (
                src.spec.scenes[0].model_copy(update={"end_frame": 80}),
                *src.spec.scenes[1:],
            )
        }
    )

    with pytest.raises(PreflightValidationError):
        apply_finish(src.brief, concept, shifted, finish(*GOOD))


class FakeGemini:
    model = "gemini-test"

    def __init__(self) -> None:
        self.parts: list[Any] = []

    async def generate_json_measured(self, model_type, system, parts, *, validate=None):
        self.parts = list(parts)
        answer = finish(*GOOD)
        assert validate is not None and validate(answer) == []
        return Measured(answer, CallUsage(input_tokens=900, output_tokens=120))


async def test_the_director_shows_gemini_every_screen_and_reports_its_tokens(tmp_path) -> None:
    src = source()
    for scene in src.spec.scenes:
        (tmp_path / scene.screenshot).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / scene.screenshot).write_bytes(b"MOCK png")
    gemini = FakeGemini()

    final, usage = await GeminiDirector(gemini, src, tmp_path).compose(
        src.spec, src.report, "proj-1"
    )  # type: ignore[arg-type]

    assert sum(isinstance(part, MediaPart) for part in gemini.parts) == 4
    assert "Viewers dropped on scene 1" in gemini.parts[0].text
    assert final.scenes[2].shot is Shot.TILT
    assert (usage.model, usage.route, usage.input_tokens, usage.output_tokens) == (
        "gemini-test",
        "gemini",
        900,
        120,
    )


class FakePlanner:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.reasons: Any = None

    async def rewrite(self, brief, winner, reasons):
        if self.error:
            raise self.error
        self.reasons = reasons
        body = winner.scenes[:-1]
        spans = [(s.t_start, s.t_end) for s in body]
        swapped = [
            scene.model_copy(update={"t_start": start, "t_end": end})
            for scene, (start, end) in zip(reversed(body), spans, strict=True)
        ]
        concept = winner.model_copy(update={"scenes": (*swapped, winner.scenes[-1])})
        return concept, CallUsage(input_tokens=300, output_tokens=40)


def _screens(src: FinalSource, root) -> None:
    for scene in src.spec.scenes:
        (root / scene.screenshot).parent.mkdir(parents=True, exist_ok=True)
        (root / scene.screenshot).write_bytes(b"MOCK png")


async def test_finish_rewrites_the_script_before_directing_its_camera(tmp_path) -> None:
    src = source()
    _screens(src, tmp_path)
    planner = FakePlanner()
    director = GeminiDirector(FakeGemini(), src, tmp_path, planner=planner)  # type: ignore[arg-type]

    final, usage = await director.compose(src.spec, src.report, "proj-1")

    body = [s.screenshot for s in src.spec.scenes[:-1]]
    assert [s.screenshot for s in final.scenes[:-1]] == body[::-1]
    assert planner.reasons == src.report.reasons["A"]
    assert (usage.input_tokens, usage.output_tokens) == (1200, 160)


async def test_a_failed_rewrite_still_finishes_the_pretested_script(tmp_path) -> None:
    src = source()
    _screens(src, tmp_path)
    planner = FakePlanner(PreflightValidationError("still invalid"))
    director = GeminiDirector(FakeGemini(), src, tmp_path, planner=planner)  # type: ignore[arg-type]

    final, usage = await director.compose(src.spec, src.report, "proj-1")

    assert [s.text for s in final.scenes] == [s.text for s in src.spec.scenes]
    assert final.scenes[2].shot is Shot.TILT
    assert usage.input_tokens == 900
