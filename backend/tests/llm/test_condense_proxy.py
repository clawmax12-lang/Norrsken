import base64
import json
import logging
import uuid

import httpx
import pytest
from pydantic import SecretStr

from preflight.llm import (
    CondenseProxyBackend,
    MediaPart,
    TextPart,
    condense_session_id,
)
from preflight.llm.backend import BackendResponse
from preflight.llm.genai_backend import INLINE_LIMIT_BYTES
from tests.llm.fakes import FakeGeminiBackend

PROXY_URL = "https://api.condense.test/openai/v1/chat/completions"
COUNT_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:countTokens"
UPSTREAM = "https://generativelanguage.googleapis.com/v1beta/openai"
SCHEMA = {"type": "object", "properties": {"word": {"type": "string"}}}
PNG = MediaPart(b"\x89PNG-bytes", "image/png")
MP4 = MediaPart(b"mp4-bytes", "video/mp4")


def answer(text: str = '{"word": "hi"}', prompt: int = 80, total: int = 130) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": prompt, "completion_tokens": 10, "total_tokens": total},
        },
    )


def counted(total: int = 100) -> httpx.Response:
    return httpx.Response(200, json={"totalTokens": total})


def make_backend(proxy_handler, count_handler=None, *, fallback=None, session_id="s-1"):
    requests: list[httpx.Request] = []

    def route(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if str(request.url) == COUNT_URL:
            return (count_handler or (lambda _r: counted()))(request)
        return proxy_handler(request)

    fallback = fallback or FakeGeminiBackend("fallback")
    backend = CondenseProxyBackend(
        httpx.AsyncClient(transport=httpx.MockTransport(route)),
        fallback=fallback,
        condense_api_key=SecretStr("ak_condense"),
        gemini_api_key=SecretStr("g_gemini"),
        base_url="https://api.condense.test/",
        upstream_url=UPSTREAM,
        session_id=session_id,
    )
    return backend, requests, fallback


async def generate(backend, parts, system="rules"):
    return await backend.generate(
        model="gemini-test", system=system, parts=parts, response_schema=SCHEMA, temperature=0.3
    )


def proxy_requests(requests):
    return [r for r in requests if str(r.url) == PROXY_URL]


def count_requests(requests):
    return [r for r in requests if str(r.url) == COUNT_URL]


async def test_sends_the_request_through_condense_to_gemini() -> None:
    backend, requests, fallback = make_backend(lambda _r: answer())

    response = await generate(backend, [TextPart("go"), PNG])

    assert response.text == '{"word": "hi"}'
    assert (response.input_tokens, response.output_tokens) == (80, 50)
    (request,) = proxy_requests(requests)
    assert request.headers["X-Condense-Auth-Token"] == "ak_condense"
    assert request.headers["Authorization"] == "Bearer g_gemini"
    assert request.headers["X-Condense-Upstream-Url"] == UPSTREAM
    assert request.headers["X-Condense-Session-Id"] == "s-1"
    png_uri = f"data:image/png;base64,{base64.b64encode(PNG.data).decode()}"
    assert json.loads(request.content) == {
        "model": "gemini-test",
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "rules"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "go\n\n[Attachment 1: the 1st image attached]"},
                    {"type": "image_url", "image_url": {"url": png_uri}},
                ],
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": SCHEMA},
        },
    }
    assert fallback.calls == []


async def test_video_travels_as_a_data_uri() -> None:
    backend, requests, _ = make_backend(lambda _r: answer())

    await generate(backend, [MP4, TextPart("watch")])

    content = json.loads(proxy_requests(requests)[0].content)["messages"][1]["content"]
    assert content == [
        {"type": "text", "text": "[Attachment 1: the 1st video attached]\n\nwatch"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:video/mp4;base64,{base64.b64encode(MP4.data).decode()}"},
        },
    ]


async def test_media_keep_their_order_after_one_text_with_references() -> None:
    backend, requests, _ = make_backend(lambda _r: answer())

    await generate(
        backend, [TextPart("Screenshot index 0:"), PNG, TextPart("Screenshot index 1:"), PNG]
    )

    content = json.loads(proxy_requests(requests)[0].content)["messages"][1]["content"]
    assert content[0]["text"] == (
        "Screenshot index 0:\n\n[Attachment 1: the 1st image attached]\n\n"
        "Screenshot index 1:\n\n[Attachment 2: the 2nd image attached]"
    )
    assert [part["type"] for part in content] == ["text", "image_url", "image_url"]


async def test_measures_the_uncompressed_request_with_count_tokens() -> None:
    backend, requests, _ = make_backend(lambda _r: answer(prompt=80), lambda _r: counted(100))

    response = await generate(backend, [TextPart("go"), PNG])

    assert response.uncompressed_input_tokens == 100
    (request,) = count_requests(requests)
    assert request.headers["x-goog-api-key"] == "g_gemini"
    assert json.loads(request.content) == {
        "generateContentRequest": {
            "model": "models/gemini-test",
            "systemInstruction": {"parts": [{"text": "rules"}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": "go"},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(PNG.data).decode(),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": SCHEMA,
            },
        }
    }


async def test_video_requests_claim_no_saving_because_count_tokens_overcounts_video() -> None:
    backend, requests, _ = make_backend(lambda _r: answer(prompt=80))

    response = await generate(backend, [MP4, TextPart("watch")])

    assert response.uncompressed_input_tokens == 80
    assert count_requests(requests) == []


@pytest.mark.parametrize(
    "count_handler",
    [
        lambda _r: httpx.Response(500),
        lambda _r: httpx.Response(200, json={"unexpected": 1}),
        lambda _r: httpx.Response(200, json={"totalTokens": "many"}),
    ],
)
async def test_unmeasurable_request_claims_no_saving(count_handler) -> None:
    backend, _, _ = make_backend(lambda _r: answer(prompt=80), count_handler)

    response = await generate(backend, [TextPart("go")])

    assert response.uncompressed_input_tokens == 80


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500])
async def test_proxy_errors_fall_back_to_gemini_directly_without_leaking_keys(
    status: int, caplog: pytest.LogCaptureFixture
) -> None:
    backend, _, fallback = make_backend(lambda _r: httpx.Response(status))

    with caplog.at_level(logging.WARNING):
        response = await generate(backend, [TextPart("go")])

    assert response == BackendResponse("fallback", input_tokens=100, output_tokens=20)
    assert len(fallback.calls) == 1
    assert f"HTTP {status}" in caplog.text
    assert "ak_condense" not in caplog.text
    assert "g_gemini" not in caplog.text


async def test_timeout_falls_back_to_gemini_directly() -> None:
    def time_out(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    backend, _, fallback = make_backend(time_out)

    assert (await generate(backend, [TextPart("go")])).text == "fallback"
    assert len(fallback.calls) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"choices": []},
        {
            "choices": [{"message": {"content": ""}}],
            "usage": {"prompt_tokens": 1, "total_tokens": 2},
        },
        {"choices": [{"message": {"content": "x"}}]},
        {
            "choices": [{"message": {"content": "x"}}],
            "usage": {"prompt_tokens": "a", "total_tokens": 2},
        },
        ["not", "an", "object"],
    ],
)
async def test_malformed_proxy_answer_falls_back(payload: object) -> None:
    backend, _, fallback = make_backend(lambda _r: httpx.Response(200, json=payload))

    assert (await generate(backend, [TextPart("go")])).text == "fallback"
    assert len(fallback.calls) == 1


async def test_media_too_large_to_inline_goes_directly_to_gemini() -> None:
    backend, requests, fallback = make_backend(lambda _r: answer())
    huge = MediaPart(b"0" * (INLINE_LIMIT_BYTES + 1), "video/mp4")

    assert (await generate(backend, [huge])).text == "fallback"
    assert requests == []
    assert len(fallback.calls) == 1


async def test_without_a_session_no_session_header_is_sent() -> None:
    backend, requests, _ = make_backend(lambda _r: answer(), session_id=None)

    await generate(backend, [TextPart("go")])

    assert "X-Condense-Session-Id" not in proxy_requests(requests)[0].headers


async def test_counting_is_never_proxied() -> None:
    backend, requests, fallback = make_backend(lambda _r: answer())

    assert await backend.count_text_tokens(model="gemini-test", text="three short words") == 3
    assert fallback.counted == ["three short words"]
    assert requests == []


def test_session_id_is_a_stable_uuid_per_project_and_fresh_without_one() -> None:
    first = condense_session_id("tablehopp-demo")

    assert uuid.UUID(first)
    assert condense_session_id("tablehopp-demo") == first
    assert condense_session_id("other") != first
    assert condense_session_id(None) != condense_session_id(None)
