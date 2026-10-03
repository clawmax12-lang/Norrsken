import asyncio
import json

from preflight.api.sse import start_offset
from preflight.contracts import RunState, Step, StepStatus
from tests.api.fakes import activity, set_state
from tests.export.seed import PROJECT_ID, seed_project


def frames(response):
    return [frame for frame in response.text.split("\n\n") if frame]


def activity_frames(response):
    return [f for f in frames(response) if "event: activity" in f]


def event_ids(response):
    return [int(f.split("\n")[0].removeprefix("id: ")) for f in activity_frames(response)]


def log_url(project_id=PROJECT_ID, query=""):
    return f"/api/projects/{project_id}/log{query}"


def seed_with_log(store, count=4, state=RunState.DONE):
    seed_project(store, finished=False, state=state)
    for index in range(count):
        store.append_event(PROJECT_ID, activity(f"line {index}"))


async def test_replays_every_logged_event_then_ends_when_done(client, store):
    seed_with_log(store)

    response = await client.get(log_url())

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache, no-transform"
    assert event_ids(response) == [0, 1, 2, 3]
    assert frames(response)[-1] == 'event: end\ndata: {"state": "DONE"}'


async def test_event_data_is_the_activity_event_json(client, store):
    seed_with_log(store, count=1)

    frame = activity_frames(await client.get(log_url()))[0]

    payload = json.loads(frame.split("data: ", 1)[1])
    assert payload["message"] == "line 0"
    assert payload["step"] == "plan"
    assert payload["status"] == "started"


async def test_resumes_after_last_event_id(client, store):
    seed_with_log(store)

    response = await client.get(log_url(), headers={"Last-Event-ID": "1"})

    assert event_ids(response) == [2, 3]


async def test_start_offset_query_picks_the_first_line(client, store):
    seed_with_log(store)

    assert event_ids(await client.get(log_url(query="?from=3"))) == [3]


async def test_last_event_id_wins_over_the_query_offset(client, store):
    seed_with_log(store)

    response = await client.get(log_url(query="?from=0"), headers={"Last-Event-ID": "2"})

    assert event_ids(response) == [3]


async def test_resuming_past_the_end_sends_only_the_end_frame(client, store):
    seed_with_log(store)

    response = await client.get(log_url(), headers={"Last-Event-ID": "3"})

    assert activity_frames(response) == []
    assert "event: end" in response.text


async def test_a_garbage_last_event_id_replays_from_the_start(client, store):
    seed_with_log(store, count=2)

    response = await client.get(log_url(), headers={"Last-Event-ID": "banana"})

    assert event_ids(response) == [0, 1]


async def test_a_negative_start_offset_is_rejected(client, store):
    seed_with_log(store)

    assert (await client.get(log_url(query="?from=-1"))).status_code == 422


async def test_failed_runs_end_the_stream_too(client, store):
    seed_with_log(store, state=RunState.FAILED)

    assert 'event: end\ndata: {"state": "FAILED"}' in (await client.get(log_url())).text


async def test_tails_new_lines_until_the_run_finishes(client, store):
    seed_with_log(store, count=1, state=RunState.PLANNED)

    reader = asyncio.create_task(client.get(log_url()))
    await asyncio.sleep(0.05)
    store.append_event(PROJECT_ID, activity("rendering", Step.RENDER))
    await asyncio.sleep(0.05)
    store.append_event(PROJECT_ID, activity("rendered", Step.RENDER, StepStatus.SUCCEEDED))
    set_state(store, PROJECT_ID, RunState.DONE)
    response = await asyncio.wait_for(reader, timeout=2)

    assert event_ids(response) == [0, 1, 2]
    assert "rendered" in response.text


async def test_sends_heartbeats_while_the_run_is_quiet(client, store):
    seed_with_log(store, count=1, state=RunState.PLANNED)

    reader = asyncio.create_task(client.get(log_url()))
    await asyncio.sleep(0.3)
    set_state(store, PROJECT_ID, RunState.DONE)
    response = await asyncio.wait_for(reader, timeout=2)

    assert ": heartbeat" in frames(response)
    assert event_ids(response) == [0]


async def test_a_project_without_a_log_yet_streams_just_the_end(client, store):
    seed_project(store, finished=False, state=RunState.DONE)

    response = await client.get(log_url())

    assert activity_frames(response) == []
    assert "event: end" in response.text


async def test_unknown_project_is_404(client):
    response = await client.get(log_url("missing"))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_start_offset_prefers_the_event_id_header():
    assert start_offset("4", 0) == 5
    assert start_offset(None, 7) == 7
    assert start_offset("-3", 2) == 2
