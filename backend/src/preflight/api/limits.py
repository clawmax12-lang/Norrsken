"""Request size limit, enforced while the body streams in."""

from fastapi import status
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .errors import ErrorInfo, error_response

_TOO_LARGE = ErrorInfo(
    status.HTTP_413_CONTENT_TOO_LARGE, "payload_too_large", "request body is too large"
)


class BodyLimitMiddleware:
    """Reject bodies over ``max_bytes`` with 413 before they are buffered in full.

    A declared ``Content-Length`` is checked up front; a body that lies about it or uses
    chunked encoding is cut off as soon as it crosses the limit. No authentication exists
    (non-goal), so this is the only defence against memory and disk exhaustion by uploads.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        """Wrap ``app``; bodies larger than ``max_bytes`` are refused."""
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass HTTP requests through a size-counting ``receive``."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        declared = Headers(scope=scope).get("content-length", "")
        if declared.isdigit() and int(declared) > self._max_bytes:
            await error_response(_TOO_LARGE)(scope, receive, send)
            return
        await self._app(scope, self._counting(receive), send)

    def _counting(self, receive: Receive) -> Receive:
        received = 0

        async def counting_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b"")) if message["type"] == "http.request" else 0
            if received > self._max_bytes:
                raise HTTPException(_TOO_LARGE.status_code, _TOO_LARGE.message)
            return message

        return counting_receive
