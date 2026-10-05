"""Planning times scenes to the voice; a narrator outage pauses the run instead of muting it."""

from preflight.contracts import RunState
from preflight.errors import ProviderError
from preflight.ports import SpeechClip
from tests.factories import make_concept
from tests.orchestrator.fakes import HYPOTHESES, VARIANTS, FakePlanner, World
from tests.sound.helpers import tone_clip


class FlakyVoice:
    """Fails its first ``outages`` lines, then speaks 0.4 s per word."""

    def __init__(self, outages: int = 0) -> None:
        self.outages = outages
        self.calls = 0

    async def synthesize(self, text: str) -> SpeechClip:
        self.calls += 1
        if self.outages > 0:
            self.outages -= 1
            raise ProviderError("spending cap reached")
        return tone_clip(0.4 * len(text.split()))


def voiced_planner() -> FakePlanner:
    def voiced(variant: str):
        concept = make_concept(variant, hypothesis=HYPOTHESES[variant])
        lines = ("Sort it fast", "Find any note", "Done in seconds", "Try it now", None)
        scenes = tuple(
            scene.model_copy(update={"voice": line})
            for scene, line in zip(concept.scenes, lines, strict=True)
        )
        return concept.model_copy(update={"scenes": scenes})

    return FakePlanner(tuple(voiced(v) for v in VARIANTS))


async def test_planned_scenes_carry_their_measured_voice(world: World) -> None:
    world.planner = voiced_planner()
    world.voice = FlakyVoice()

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    concepts = world.store.paths(world.project_id).concept("A")
    assert '"voice_words"' in concepts.read_text()


async def test_a_narrator_outage_pauses_after_planning_and_resumes_with_the_same_concepts(
    world: World,
) -> None:
    world.planner = voiced_planner()
    world.voice = FlakyVoice(outages=1)

    paused = await world.pipeline().run(world.project_id)

    assert paused.state is RunState.FAILED
    assert "paused after planning" in (paused.error or "")
    resumed = await world.pipeline().run(world.project_id)

    assert resumed.state is RunState.DONE
    assert world.planner.calls == 1
