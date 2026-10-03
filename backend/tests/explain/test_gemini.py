import json

from preflight.errors import ProviderError
from preflight.explain import RuleBasedExplainer
from preflight.explain.gemini import GeminiExplainer
from preflight.llm import GeminiClient
from preflight.scoring import score_and_rank
from tests.explain.test_rule_based import concept_with_distinct_scenes
from tests.factories import make_brief, make_result
from tests.llm.fakes import FakeGeminiBackend

VALUES = (0.2, 0.9, 0.3, 0.3, 0.3, 0.3, 0.3, 0.1, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3)


def explainer_with(*script):
    backend = FakeGeminiBackend(*script)
    return GeminiExplainer(GeminiClient(backend, "gemini-test", retry_delay_s=0)), backend


async def explain(explainer):
    concept = concept_with_distinct_scenes()
    results = [make_result("A", values=VALUES), make_result("B", values=(0.1,) * 15)]
    ranking = score_and_rank(results)
    facts = await RuleBasedExplainer().explain(make_brief(), concept, ranking, results)
    return facts, await explainer.explain(make_brief(), concept, ranking, results)


async def test_gemini_rewords_each_reason_but_keeps_its_moment_and_scene() -> None:
    facts_count = 2
    sentences = [f"Sentence {n}." for n in range(facts_count)]
    explainer, backend = explainer_with(json.dumps({"sentences": sentences}))

    facts, reasons = await explain(explainer)

    assert len(facts) == facts_count
    assert [r.text for r in reasons] == sentences
    assert [(r.t, r.scene_index) for r in reasons] == [(f.t, f.scene_index) for f in facts]
    (task,) = backend.texts()
    assert "Variant A ranked 1 of 2" in task
    assert all(f.text in task for f in facts)


async def test_wrong_number_of_sentences_is_repaired_then_falls_back() -> None:
    wrong = json.dumps({"sentences": ["only one"]})
    explainer, backend = explainer_with(wrong, wrong)

    facts, reasons = await explain(explainer)

    assert reasons == facts
    assert len(backend.calls) == 2


async def test_provider_failure_keeps_the_rule_based_wording() -> None:
    explainer, _ = explainer_with(ProviderError("down"))

    facts, reasons = await explain(explainer)

    assert reasons == facts
