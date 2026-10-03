import json
from types import SimpleNamespace

import httpx
import pytest
from google import genai
from google.genai import types

from preflight.errors import ProviderError, TransientProviderError
from preflight.llm import GenAIBackend, MediaPart, TextPart
from preflight.llm.genai_backend import INLINE_LIMIT_BYTES

SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}}}


def sdk_client(handler) -> tuple[genai.Client, list[httpx.Request]]:
    """The real SDK over a fake transport: proves our mapping against the SDK's own errors."""
    requests: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(recording))
    options = types.HttpOptions(httpx_async_client=http)
    return genai.Client(api_key="test-key", http_options=options), requests


def answer(text: str = '{"a": 1}') -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [{"content": {"parts": [{"text": text}], "role": "model"}}],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 3,
                "thoughtsTokenCount": 2,
            },
        },
    )


async def generate(backend: GenAIBackend, parts=None):
    return await backend.generate(
        model="gemini-test",
        system="be careful",
        parts=parts or [TextPart("hello")],
        response_schema=SCHEMA,
        temperature=0.3,
    )


async def test_generate_sends_schema_system_prompt_and_inline_media() -> None:
    client, requests = sdk_client(lambda _r: answer())

    response = await generate(
        GenAIBackend(client), [TextPart("hello"), MediaPart(b"img", "image/png")]
    )

    assert (response.text, response.input_tokens, response.output_tokens) == ('{"a": 1}', 10, 5)
    (request,) = requests
    body = json.loads(request.content)
    assert request.url.path.endswith("/models/gemini-test:generateContent")
    assert body["systemInstruction"]["parts"][0]["text"] == "be careful"
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["responseJsonSchema"] == SCHEMA
    assert body["contents"][0]["parts"][1]["inlineData"]["mime_type"] == "image/png"


@pytest.mark.parametrize("status", [429, 500, 503, 408])
async def test_transient_http_statuses_map_to_transient_error(status: int) -> None:
    client, _ = sdk_client(lambda _r: httpx.Response(status, json={"error": {"message": "slow"}}))

    with pytest.raises(TransientProviderError, match=str(status)):
        await generate(GenAIBackend(client))


@pytest.mark.parametrize("status", [400, 401, 403, 404])
async def test_client_errors_map_to_non_transient_provider_error(status: int) -> None:
    client, _ = sdk_client(lambda _r: httpx.Response(status, json={"error": {"message": "no"}}))

    with pytest.raises(ProviderError) as info:
        await generate(GenAIBackend(client))

    assert not isinstance(info.value, TransientProviderError)


async def test_timeout_maps_to_transient_error() -> None:
    def time_out(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    client, _ = sdk_client(time_out)

    with pytest.raises(TransientProviderError, match="ReadTimeout"):
        await generate(GenAIBackend(client))


async def test_empty_answer_is_a_provider_error_with_the_reason() -> None:
    client, _ = sdk_client(
        lambda _r: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})
    )

    with pytest.raises(ProviderError, match="SAFETY"):
        await generate(GenAIBackend(client))


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({"candidates": [{"finishReason": "SAFETY"}]}, "SAFETY"),
        ({"candidates": []}, "no candidates"),
    ],
)
async def test_empty_answer_reason_comes_from_candidates(body: dict, expected: str) -> None:
    client, _ = sdk_client(lambda _r: httpx.Response(200, json=body))

    with pytest.raises(ProviderError, match=expected):
        await generate(GenAIBackend(client))


async def test_missing_usage_metadata_records_zero_tokens() -> None:
    client, _ = sdk_client(
        lambda _r: httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "{}"}], "role": "model"}}]}
        )
    )

    response = await generate(GenAIBackend(client))

    assert (response.input_tokens, response.output_tokens) == (0, 0)


async def test_count_text_tokens_returns_the_provider_total() -> None:
    client, requests = sdk_client(lambda _r: httpx.Response(200, json={"totalTokens": 42}))

    assert await GenAIBackend(client).count_text_tokens(model="gemini-test", text="hi") == 42
    assert requests[0].url.path.endswith(":countTokens")


async def test_count_text_tokens_without_total_is_an_error() -> None:
    client, _ = sdk_client(lambda _r: httpx.Response(200, json={}))

    with pytest.raises(ProviderError, match="no total"):
        await GenAIBackend(client).count_text_tokens(model="gemini-test", text="hi")


class FakeFiles:
    """Stands in for ``client.aio.files``: PROCESSING for ``processing_polls`` polls."""

    def __init__(self, processing_polls: int, final: types.FileState = types.FileState.ACTIVE):
        self.polls_left = processing_polls
        self.final = final
        self.uploaded: list[bytes] = []
        self.gets = 0

    def _file(self, state: types.FileState) -> types.File:
        return types.File(name="files/abc", uri="https://files/abc", state=state)

    async def upload(self, *, file, config):
        self.uploaded.append(file.read())
        assert config.mime_type == "video/mp4"
        return self._file(types.FileState.PROCESSING)

    async def get(self, *, name: str):
        self.gets += 1
        self.polls_left -= 1
        state = types.FileState.PROCESSING if self.polls_left > 0 else self.final
        return self._file(state)


class FakeSdk:
    def __init__(self, files: FakeFiles, generated: list) -> None:
        async def generate_content(*, model, contents, config):
            generated.append(contents)
            return types.GenerateContentResponse(
                candidates=[types.Candidate(content=types.Content(parts=[types.Part(text="{}")]))]
            )

        self.aio = SimpleNamespace(
            files=files, models=SimpleNamespace(generate_content=generate_content)
        )


async def no_sleep(_seconds: float) -> None:
    return None


BIG_VIDEO = MediaPart(b"v" * (INLINE_LIMIT_BYTES + 1), "video/mp4")


async def test_large_media_is_uploaded_polled_and_referenced_by_uri() -> None:
    files, generated = FakeFiles(processing_polls=3), []
    backend = GenAIBackend(FakeSdk(files, generated), sleep=no_sleep)

    await generate(backend, [BIG_VIDEO])

    assert files.uploaded == [BIG_VIDEO.data]
    assert files.gets == 3
    (part,) = generated[0].parts
    assert part.file_data.file_uri == "https://files/abc"
    assert part.inline_data is None


async def test_media_at_the_limit_stays_inline() -> None:
    files, generated = FakeFiles(processing_polls=0), []
    backend = GenAIBackend(FakeSdk(files, generated), sleep=no_sleep)

    await generate(backend, [MediaPart(b"v" * INLINE_LIMIT_BYTES, "video/mp4")])

    assert files.uploaded == []
    assert generated[0].parts[0].inline_data is not None


async def test_failed_upload_processing_is_a_provider_error() -> None:
    files = FakeFiles(processing_polls=1, final=types.FileState.FAILED)
    backend = GenAIBackend(FakeSdk(files, []), sleep=no_sleep)

    with pytest.raises(ProviderError, match="could not process"):
        await generate(backend, [BIG_VIDEO])


async def test_upload_that_never_finishes_is_transient() -> None:
    files = FakeFiles(processing_polls=10_000)
    backend = GenAIBackend(FakeSdk(files, []), sleep=no_sleep, max_polls=3)

    with pytest.raises(TransientProviderError, match="poll limit"):
        await generate(backend, [BIG_VIDEO])


async def test_upload_response_without_uri_is_a_provider_error() -> None:
    files = FakeFiles(processing_polls=1)

    async def get_without_uri(*, name: str):
        return types.File(name=name, state=types.FileState.ACTIVE)

    files.get = get_without_uri
    backend = GenAIBackend(FakeSdk(files, []), sleep=no_sleep)

    with pytest.raises(ProviderError, match="missing a name or uri"):
        await generate(backend, [BIG_VIDEO])


def test_from_api_key_builds_an_sdk_backed_instance() -> None:
    assert isinstance(GenAIBackend.from_api_key("k", timeout_s=5), GenAIBackend)
