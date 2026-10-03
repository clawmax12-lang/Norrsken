"""One place for per-step timeouts and the single retry (PRD §9 guardrails)."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Self

from preflight.config import Settings
from preflight.errors import ProviderError, TransientProviderError

_LOG = logging.getLogger(__name__)
TRANSIENT: tuple[type[Exception], ...] = (TransientProviderError,)


@dataclass(frozen=True)
class StepPolicy:
    """How long one attempt of a step may take and how many retries a failure earns."""

    timeout_s: float
    retries: int

    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        """Take the limits from ``step_timeout_s`` and ``step_retries``."""
        return cls(timeout_s=settings.step_timeout_s, retries=settings.step_retries)

    async def run[T](
        self,
        call: Callable[[], Awaitable[T]],
        *,
        retry_on: tuple[type[Exception], ...] = TRANSIENT,
    ) -> T:
        """Await ``call()`` under the timeout, retrying only errors in ``retry_on``.

        Anything else, including a timeout, propagates at once so a hung provider cannot
        multiply the wait. A timeout surfaces as :class:`ProviderError`.
        """
        for _ in range(self.retries):
            try:
                return await self._attempt(call)
            except retry_on as exc:
                _LOG.warning("retrying after %s: %s", type(exc).__name__, exc)
        return await self._attempt(call)

    async def _attempt[T](self, call: Callable[[], Awaitable[T]]) -> T:
        try:
            async with asyncio.timeout(self.timeout_s):
                return await call()
        except TimeoutError as exc:
            raise ProviderError(f"step timed out after {self.timeout_s:g}s") from exc
