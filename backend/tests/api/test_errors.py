import pytest

from preflight.api.errors import ApiError, describe_error
from preflight.api.limits import BodyLimitMiddleware
from preflight.errors import (
    PreflightError,
    PreflightValidationError,
    ProviderError,
    SimulatorUnavailableError,
    StorageError,
)


def missing_file_error() -> StorageError:
    error = StorageError("missing file: /secret/place/run.json")
    error.__cause__ = FileNotFoundError()
    return error


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (ApiError(409, "conflict", "nope"), 409, "conflict"),
        (PreflightValidationError("bad"), 422, "validation_error"),
        (missing_file_error(), 404, "not_found"),
        (StorageError("invalid Brief in x"), 500, "storage_error"),
        (ProviderError("gemini said 503"), 502, "provider_error"),
        (SimulatorUnavailableError("tribe down"), 502, "provider_error"),
        (PreflightError("anything else"), 500, "internal_error"),
    ],
)
def test_expected_failures_map_to_status_and_code(error, status, code):
    info = describe_error(error)

    assert (info.status_code, info.code) == (status, code)


@pytest.mark.parametrize(
    "error", [missing_file_error(), StorageError("x"), ProviderError("key=abc")]
)
def test_server_side_details_are_never_echoed(error):
    message = describe_error(error).message

    assert "secret" not in message
    assert "abc" not in message
    assert "/" not in message


def test_validation_messages_reach_the_client():
    assert describe_error(PreflightValidationError("one_liner: too long")).message == (
        "one_liner: too long"
    )


async def test_the_body_limit_ignores_non_http_scopes():
    seen = []

    async def app(scope, receive, send):
        seen.append(scope["type"])

    await BodyLimitMiddleware(app, max_bytes=1)({"type": "lifespan"}, None, None)

    assert seen == ["lifespan"]
