"""Bounded fan-out for independent per-variant work."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence


async def gather_bounded[T](limit: int, jobs: Sequence[Callable[[], Awaitable[T]]]) -> list[T]:
    """Run ``jobs`` with at most ``limit`` in flight and return results in job order.

    Every job finishes before the first failure is re-raised, so a crash never leaves
    sibling work running unobserved after ``run()`` has returned.
    """
    gate = asyncio.Semaphore(limit)

    async def guarded(job: Callable[[], Awaitable[T]]) -> T:
        async with gate:
            return await job()

    outcomes = await asyncio.gather(*(guarded(job) for job in jobs), return_exceptions=True)
    values: list[T] = []
    for outcome in outcomes:
        if isinstance(outcome, BaseException):
            raise outcome
        values.append(outcome)
    return values
