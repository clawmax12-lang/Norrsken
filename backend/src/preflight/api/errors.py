"""One JSON error shape for every failure: ``{"error": {"code": ..., "message": ...}}``."""

import logging
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from preflight.errors import (
    PreflightError,
    PreflightValidationError,
    ProviderError,
    StorageError,
)

logger = logging.getLogger(__name__)

_HTTP_CODES = {404: "not_found", 405: "method_not_allowed", 413: "payload_too_large"}


class ApiError(Exception):
    """A failure the API itself decides on (missing project, no runner-up, ...)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        """Create an error that renders as ``status_code`` with ``code`` and ``message``."""
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ErrorInfo:
    """HTTP status plus the public ``code`` and ``message`` of the error body."""

    status_code: int
    code: str
    message: str


def describe_error(exc: Exception) -> ErrorInfo:
    """Map an exception to what the client is told. Server errors never echo internals."""
    if isinstance(exc, ApiError):
        return ErrorInfo(exc.status_code, exc.code, exc.message)
    if isinstance(exc, RequestValidationError):
        return ErrorInfo(422, "validation_error", _describe_request_errors(exc))
    if isinstance(exc, StarletteHTTPException):
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return ErrorInfo(exc.status_code, code, str(exc.detail))
    if isinstance(exc, PreflightValidationError):
        return ErrorInfo(422, "validation_error", str(exc))
    return _describe_server_error(exc)


def _describe_server_error(exc: Exception) -> ErrorInfo:
    if isinstance(exc, StorageError):
        if isinstance(exc.__cause__, FileNotFoundError):
            return ErrorInfo(404, "not_found", "the requested data does not exist yet")
        return ErrorInfo(500, "storage_error", "stored project data could not be read")
    if isinstance(exc, ProviderError):
        return ErrorInfo(502, "provider_error", "an upstream provider failed")
    return ErrorInfo(500, "internal_error", "internal error")


def _describe_request_errors(exc: RequestValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}" for issue in exc.errors()
    )


def error_response(info: ErrorInfo) -> JSONResponse:
    """Render ``info`` in the shared error envelope."""
    body = {"error": {"code": info.code, "message": info.message}}
    return JSONResponse(body, status_code=info.status_code)


async def _handle(request: Request, exc: Exception) -> JSONResponse:
    info = describe_error(exc)
    if info.status_code >= 500:
        logger.error("%s %s failed", request.method, request.url.path, exc_info=exc)
    return error_response(info)


def install_error_handlers(app: FastAPI) -> None:
    """Route every expected failure through :func:`describe_error`."""
    for exception_type in (
        ApiError,
        PreflightError,
        RequestValidationError,
        StarletteHTTPException,
    ):
        app.add_exception_handler(exception_type, _handle)
