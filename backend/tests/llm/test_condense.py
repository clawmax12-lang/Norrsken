import json
import logging

import httpx
import pytest
from pydantic import SecretStr

from preflight.llm import CondenseCompressor

LONG_TEXT = "alpha beta gamma " * 200


def make_compressor(
    handler, *, api_key: str | None = "ak_secret", session_id: str | None = None
) -> tuple[CondenseCompressor, list]:
    requests: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(recording))
    compressor = CondenseCompressor(
        http,
        api_key=SecretStr(api_key) if api_key else None,
        base_url="https://api.condense.test/",
        compression_rate=0.2,
        session_id=session_id,
    )
    return compressor, requests


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200, json={"model": "helene-1", "messages": [{"role": "user", "content": "short"}]}
    )


async def test_posts_documented_request_and_returns_compressed_text() -> None:
    compressor, requests = make_compressor(ok)

    assert await compressor.compress(LONG_TEXT) == "short"

    (request,) = requests
    assert str(request.url) == "https://api.condense.test/v1/compress"
    assert request.headers["X-Condense-Auth-Token"] == "ak_secret"
    assert json.loads(request.content) == {
        "model": "helene-1",
        "compression_rate": 0.2,
        "messages": [{"role": "user", "content": LONG_TEXT}],
    }


async def test_session_header_groups_requests_in_the_dashboard() -> None:
    compressor, requests = make_compressor(ok, session_id="s-1")

    await compressor.compress(LONG_TEXT)

    assert requests[0].headers["X-Condense-Session-Id"] == "s-1"


async def test_without_a_key_nothing_is_sent() -> None:
    compressor, requests = make_compressor(ok, api_key=None)

    assert await compressor.compress(LONG_TEXT) is None
    assert requests == []


async def test_short_text_is_not_worth_a_call() -> None:
    compressor, requests = make_compressor(ok)

    assert await compressor.compress("tiny") is None
    assert requests == []


@pytest.mark.parametrize("status", [401, 403, 429, 500])
async def test_http_errors_degrade_to_the_original_without_leaking_the_key(
    status: int, caplog: pytest.LogCaptureFixture
) -> None:
    compressor, _ = make_compressor(lambda _r: httpx.Response(status, headers={"Retry-After": "3"}))

    with caplog.at_level(logging.WARNING):
        assert await compressor.compress(LONG_TEXT) is None

    assert f"HTTP {status}" in caplog.text
    assert "ak_secret" not in caplog.text


async def test_timeout_degrades_to_the_original() -> None:
    def time_out(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    compressor, _ = make_compressor(time_out)

    assert await compressor.compress(LONG_TEXT) is None


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": []},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user", "content": 5}]},
        {"messages": [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}]},
        ["not", "an", "object"],
    ],
)
async def test_malformed_response_degrades_to_the_original(payload: object) -> None:
    compressor, _ = make_compressor(lambda _r: httpx.Response(200, json=payload))

    assert await compressor.compress(LONG_TEXT) is None


async def test_non_json_response_degrades_to_the_original() -> None:
    compressor, _ = make_compressor(lambda _r: httpx.Response(200, text="<html>"))

    assert await compressor.compress(LONG_TEXT) is None
