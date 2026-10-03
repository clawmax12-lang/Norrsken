import json

import httpx
import pytest
from pydantic import SecretStr

from preflight.config import Settings
from preflight.contracts.composition import Layout
from preflight.errors import PreflightValidationError, ProviderError
from preflight.finalization.opus import OpusComposer, apply_recipe
from tests.export.seed import make_report
from tests.factories import make_brief, make_concept
from tests.finalization.helpers import recipe
from tests.orchestrator.fakes import FakeComposer


def spec():
    return FakeComposer().compose(make_brief(), make_concept("B"), ())


def test_motion_cannot_change_copy_sources_assets_or_brand():
    original = spec()
    final = apply_recipe(original, recipe(original))
    assert final.duration_frames == 450
    assert final.theme == original.theme
    assert final.cta == original.cta and final.cta_source_field == original.cta_source_field
    for a, b in zip(original.scenes, final.scenes, strict=True):
        assert (a.text, a.source_field, a.screenshot, a.backdrop) == (
            b.text,
            b.source_field,
            b.screenshot,
            b.backdrop,
        )
    assert all(s.layout == "device_float" for s in final.scenes)


def test_motion_rejects_incorrect_total_duration_and_lost_screenshots():
    motion = recipe(spec())
    with pytest.raises(PreflightValidationError, match="450"):
        apply_recipe(spec(), motion.model_copy(update={"scenes": motion.scenes[:-1]}))
    with pytest.raises(PreflightValidationError, match="screenshots"):
        apply_recipe(
            spec(),
            motion.model_copy(
                update={
                    "scenes": tuple(
                        s.model_copy(update={"layout": Layout.TEXT_ONLY}) for s in motion.scenes
                    )
                }
            ),
        )


async def test_documented_model_native_schema_condense_route_and_usage():
    requests = []

    def transport(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "model": "claude-opus-5-5",
                "stop_reason": "end_turn",
                "content": [
                    {"type": "thinking", "thinking": "not persisted"},
                    {"type": "text", "text": recipe(spec()).model_dump_json()},
                ],
                "usage": {"input_tokens": 123, "output_tokens": 456},
            },
        )

    settings = Settings(
        anthropic_api_key=SecretStr("MOCK-ant"), condense_api_key=SecretStr("MOCK-con")
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        final, usage = await OpusComposer(settings, http).compose(spec(), make_report(), "proj-1")
    request = requests[0]
    assert str(request.url) == "https://api.condense.chat/anthropic/v1/messages"
    assert request.headers["x-api-key"] == "MOCK-ant"
    assert request.headers["x-condense-auth-token"] == "MOCK-con"
    body = json.loads(request.content)
    assert body["model"] == "claude-opus-5-5" and body["max_tokens"] == 4096
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert "uploads/" not in body["messages"][0]["content"]
    assert usage.input_tokens == 123 and usage.output_tokens == 456
    assert final.variant_id == "B"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(401, text="secret-provider-body"),
        httpx.Response(429, json={"error": "secret-provider-body"}),
        httpx.Response(200, json={"stop_reason": "max_tokens"}),
        httpx.Response(200, json=None),
        httpx.Response(200, json={"stop_reason": "end_turn", "content": []}),
    ],
)
async def test_failures_are_sanitized_and_no_direct_fallback(response):
    calls = []

    def transport(request):
        calls.append(request)
        return response

    settings = Settings(
        anthropic_api_key=SecretStr("MOCK-ant"), condense_api_key=SecretStr("MOCK-con")
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        with pytest.raises(ProviderError) as error:
            await OpusComposer(settings, http).compose(spec(), make_report(), "proj-1")
    assert "secret-provider-body" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize("kwargs", [{}, {"anthropic_api_key": SecretStr("MOCK-ant")}])
async def test_keys_required_before_network(kwargs):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: pytest.fail("network called"))
    ) as http:
        with pytest.raises(ProviderError):
            await OpusComposer(Settings(**kwargs), http).compose(spec(), make_report(), "proj-1")
