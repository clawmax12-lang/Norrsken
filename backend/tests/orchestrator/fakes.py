"""Fake port implementations for pipeline tests. Test-only: never imported by application code.

Every fake records its calls so tests can assert which steps ran, and can be told to fail a
number of times before succeeding (``failures``) to exercise retry, outage and resume paths.
"""

import asyncio
import hashlib
from collections import defaultdict, deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from preflight.config import Settings
from preflight.contracts import (
    Brief,
    BriefField,
    CompositionSpec,
    CreativeConcept,
    GeneratedAsset,
    Ranking,
    Reason,
    RenderResult,
    SceneSpec,
    SimulationResult,
    SimulatorName,
    SoundRecord,
    Theme,
    TokenSavings,
)
from preflight.contracts.composition import Layout, Transition
from preflight.orchestrator import Pipeline
from preflight.ports import SimulationRequest, SoundFinisher, SoundRequest, SpeechSynthesizer
from preflight.storage import ProjectStore
from tests.factories import FIXED_NOW, make_brief, make_concept, make_result

VARIANTS = ("A", "B", "C")
HYPOTHESES = {"A": "problem first", "B": "outcome first", "C": "product first"}
# Per-variant primary series level: B wins, C is runner-up, A is last.
LEVELS = {"A": 0.3, "B": 0.8, "C": 0.5}


class FakeClock:
    """Advances one second per reading, so every duration is a deterministic whole number."""

    def __init__(self) -> None:
        self._now = FIXED_NOW

    def __call__(self) -> datetime:
        self._now += timedelta(seconds=1)
        return self._now


class Failures:
    """Per-key queues of exceptions to raise on successive calls (empty queue: succeed)."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[Exception]] = defaultdict(deque)

    def add(self, key: str, *errors: Exception) -> None:
        self._queues[key].extend(errors)

    def always(self, key: str, error: Exception, times: int = 20) -> None:
        self.add(key, *[error] * times)

    def maybe_raise(self, key: str) -> None:
        if self._queues[key]:
            raise self._queues[key].popleft()


class FakePlanner:
    def __init__(self, concepts: Sequence[CreativeConcept] | None = None) -> None:
        self.concepts = tuple(
            concepts or (make_concept(v, hypothesis=HYPOTHESES[v]) for v in VARIANTS)
        )
        self.failures = Failures()
        self.calls = 0
        self.delay_s = 0.0

    async def plan_variants(self, brief: Brief, *, count: int) -> tuple[CreativeConcept, ...]:
        self.calls += 1
        await asyncio.sleep(self.delay_s)
        self.failures.maybe_raise("plan")
        return self.concepts


class FakeAssetGenerator:
    def __init__(self) -> None:
        self.failures = Failures()
        self.calls: list[str] = []

    async def generate(
        self, brief: Brief, concept: CreativeConcept, output_dir: Path
    ) -> tuple[GeneratedAsset, ...]:
        self.calls.append(concept.variant_id)
        self.failures.maybe_raise("generate")
        return ()


class FakeComposer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def compose(
        self, brief: Brief, concept: CreativeConcept, assets: Sequence[GeneratedAsset]
    ) -> CompositionSpec:
        self.calls.append(concept.variant_id)
        scenes = tuple(
            SceneSpec(
                start_frame=round(s.t_start * 30),
                end_frame=round(s.t_end * 30),
                text=s.text,
                source_field=s.source_field,
                screenshot=s.screenshot,
                layout=Layout.DEVICE_CENTER,
                transition_in=Transition.FADE,
            )
            for s in concept.scenes
        )
        return CompositionSpec(
            variant_id=concept.variant_id,
            duration_frames=450,
            theme=Theme(
                background="#000000", foreground="#ffffff", accent="#3366ff", font_family="Inter"
            ),
            scenes=scenes,
            cta=concept.cta,
            cta_source_field=concept.cta_source_field,
            wordmark=brief.product_name,
            headline=brief.one_liner,
            headline_source_field=BriefField.ONE_LINER,
            logo=brief.logo,
        )


class FakeRenderer:
    def __init__(self) -> None:
        self.failures = Failures()
        self.calls: list[str] = []
        self.in_flight = 0
        self.max_in_flight = 0

    async def render(self, spec: CompositionSpec, output: Path) -> RenderResult:
        self.calls.append(spec.variant_id)
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(0.01)
            self.failures.maybe_raise(spec.variant_id)
            data = f"video-{spec.variant_id}".encode()
            await asyncio.to_thread(output.write_bytes, data)
            return RenderResult(
                variant_id=spec.variant_id,
                video_path=str(output),
                video_sha256=hashlib.sha256(data).hexdigest(),
                render_seconds=2.5,
            )
        finally:
            self.in_flight -= 1


class FakeSimulator:
    def __init__(self, name: SimulatorName = SimulatorName.GEMINI_PANEL) -> None:
        self.name = name
        self.failures = Failures()
        self.calls: list[str] = []
        self.wrong_variant = False

    async def simulate(self, request: SimulationRequest) -> SimulationResult:
        variant_id = request.concept.variant_id
        self.calls.append(variant_id)
        self.failures.maybe_raise(variant_id)
        return make_result(
            "A" if self.wrong_variant else variant_id,
            self.name,
            values=(LEVELS[variant_id],) * 15,
            video_sha256=request.video_sha256,
        )


class FakeExplainer:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.failures = Failures()

    async def explain(
        self,
        brief: Brief,
        concept: CreativeConcept,
        ranking: Ranking,
        results: Sequence[SimulationResult],
    ) -> tuple[Reason, ...]:
        self.calls.append(concept.variant_id)
        self.failures.maybe_raise("explain")
        assert {r.variant_id for r in results} == {concept.variant_id}
        return (
            Reason(t=1.0, scene_index=0, text="Holds attention on the opening scene"),
            Reason(t=8.0, scene_index=2, text="Drops while the third scene is on screen"),
        )


class FakeUsage:
    def snapshot(self) -> TokenSavings:
        return TokenSavings(
            calls=4, input_tokens_original=1000, input_tokens_sent=600, output_tokens=120
        )


class FakeSoundFinisher:
    """Writes a stand-in final video and returns the record a real studio would."""

    def __init__(self) -> None:
        self.failures = Failures()
        self.calls: list[str] = []
        self.requests: list[SoundRequest] = []
        # variant id -> how many more finishes come back without a voice
        self.voiceless: dict[str, int] = {}

    async def finish(self, request: SoundRequest) -> SoundRecord:
        variant_id = request.spec.variant_id
        self.calls.append(variant_id)
        self.requests.append(request)
        self.failures.maybe_raise(variant_id)
        data = b"final-" + request.video_path.read_bytes()
        request.output_path.write_bytes(data)
        narrated = request.allow_narration
        if narrated and self.voiceless.get(variant_id, 0) > 0:
            self.voiceless[variant_id] -= 1
            narrated = False
        return SoundRecord(
            variant_id=variant_id,
            tested_video_sha256=request.video_sha256,
            final_video_sha256=hashlib.sha256(data).hexdigest(),
            final_video_path=request.output_path.name,
            narrated=narrated,
            voice="Leda" if narrated else None,
            tts_model="tts-test" if narrated else None,
            bpm=120,
            integrated_lufs=-14.0,
            true_peak_dbtp=-1.5,
            note=None if narrated else "Narration is off.",
        )


def no_suggestions(*_args: object) -> tuple[str, ...]:
    return ("Try a stronger hook",)


@dataclass
class World:
    """All fakes wired into a :class:`Pipeline`; tests tweak the fakes, then call ``pipeline()``."""

    store: ProjectStore
    project_id: str = "proj-1"
    planner: FakePlanner = field(default_factory=FakePlanner)
    generator: FakeAssetGenerator = field(default_factory=FakeAssetGenerator)
    composer: FakeComposer = field(default_factory=FakeComposer)
    renderer: FakeRenderer = field(default_factory=FakeRenderer)
    gemini: FakeSimulator = field(default_factory=FakeSimulator)
    explainer: FakeExplainer = field(default_factory=FakeExplainer)
    settings: Settings = field(default_factory=Settings)
    extra_simulators: list[FakeSimulator] = field(default_factory=list)
    next_time: Callable[..., tuple[str, ...]] = no_suggestions
    sound: SoundFinisher | None = None
    voice: SpeechSynthesizer | None = None

    def __post_init__(self) -> None:
        paths = self.store.create(self.project_id)
        self.store.write(paths.brief, make_brief(project_id=self.project_id))

    def pipeline(self) -> Pipeline:
        return Pipeline(
            self.store,
            self.planner,
            self.generator,
            self.composer,
            self.renderer,
            [self.gemini, *self.extra_simulators],
            self.explainer,
            FakeUsage(),
            self.settings,
            FakeClock(),
            next_time=self.next_time,
            sound=self.sound,
            voice=self.voice,
        )
