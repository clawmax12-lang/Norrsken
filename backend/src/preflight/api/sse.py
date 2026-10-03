"""Server-Sent Events for the activity log (FR-09).

The log is an append-only JSONL file, so a line index is a stable event id: a client that
reconnects with ``Last-Event-ID`` is replayed exactly what it missed, then follows new lines
until the run reaches a terminal state.
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from preflight.contracts import ActivityEvent, RunRecord, RunState
from preflight.storage import ProjectStore

_TERMINAL_STATES = (RunState.DONE, RunState.FAILED)
HEARTBEAT = ": heartbeat\n\n"


@dataclass(frozen=True)
class StreamTiming:
    """How often a stream looks for new lines and how long silence lasts before a heartbeat."""

    poll_interval_s: float = 0.25
    heartbeat_interval_s: float = 15.0


def start_offset(last_event_id: str | None, from_offset: int) -> int:
    """First line to send: just after ``Last-Event-ID`` when valid, else ``from_offset``."""
    if last_event_id is not None and last_event_id.strip().isdigit():
        return int(last_event_id) + 1
    return from_offset


def format_activity(index: int, event: ActivityEvent) -> str:
    """One SSE frame for the log line at ``index``."""
    return f"id: {index}\nevent: activity\ndata: {event.model_dump_json()}\n\n"


def format_end(state: RunState) -> str:
    """The frame that tells the client the run is over and it should not reconnect."""
    return f'event: end\ndata: {{"state": "{state.value}"}}\n\n'


async def stream_activity_log(
    store: ProjectStore, project_id: str, *, start: int, timing: StreamTiming
) -> AsyncIterator[str]:
    """Yield SSE frames from log line ``start`` until the run is DONE or FAILED.

    The run state is read before the log so that a run which finishes between the two reads
    still has its final lines delivered before the stream ends.
    """
    offset = start
    silent_s = 0.0
    while True:
        state = await asyncio.to_thread(_run_state, store, project_id)
        events = await asyncio.to_thread(_read_events, store, project_id, offset)
        for event in events:
            yield format_activity(offset, event)
            offset += 1
        if state in _TERMINAL_STATES:
            yield format_end(state)
            return
        silent_s = 0.0 if events else silent_s + timing.poll_interval_s
        if silent_s >= timing.heartbeat_interval_s:
            yield HEARTBEAT
            silent_s = 0.0
        await asyncio.sleep(timing.poll_interval_s)


def _run_state(store: ProjectStore, project_id: str) -> RunState:
    return store.read(store.paths(project_id).run, RunRecord).state


def _read_events(store: ProjectStore, project_id: str, start: int) -> list[ActivityEvent]:
    return list(store.read_events(project_id, start=start))
