import asyncio

from preflight.contracts import RunRecord, RunState
from tests.api.fakes import CrashingRunService
from tests.export.seed import PROJECT_ID, seed_project


def start_url(project_id=PROJECT_ID):
    return f"/api/projects/{project_id}/run"


async def test_starting_a_run_answers_202_and_runs_in_the_background(client, store, run_service):
    seed_project(store, finished=False, state=RunState.BRIEF_RECEIVED)

    response = await client.post(start_url())

    assert response.status_code == 202
    assert response.json()["state"] == "BRIEF_RECEIVED"
    await asyncio.wait_for(run_service.started.wait(), timeout=2)
    assert run_service.calls == [PROJECT_ID]
    run_service.release.set()


async def test_asking_again_while_running_does_not_start_a_second_run(client, store, run_service):
    seed_project(store, finished=False, state=RunState.BRIEF_RECEIVED)
    await client.post(start_url())
    await run_service.started.wait()

    second = await client.post(start_url())

    assert second.status_code == 202
    assert run_service.calls == [PROJECT_ID]
    run_service.release.set()


async def test_a_finished_run_can_be_started_again(client, store, run_service):
    seed_project(store, finished=False, state=RunState.BRIEF_RECEIVED)
    run_service.release.set()

    for _ in range(100):
        await client.post(start_url())
        await asyncio.sleep(0.01)
        if len(run_service.calls) == 2:
            break

    assert run_service.calls == [PROJECT_ID, PROJECT_ID]


async def test_a_project_saved_by_the_web_app_without_run_json_can_start(
    client, store, run_service
):
    seed_project(store, finished=False, state=RunState.BRIEF_RECEIVED)
    store.paths(PROJECT_ID).run.unlink()

    response = await client.post(start_url())

    assert response.status_code == 202
    assert response.json()["state"] == "BRIEF_RECEIVED"
    await asyncio.wait_for(run_service.started.wait(), timeout=2)
    run_service.release.set()


async def test_unknown_project_is_404(client):
    response = await client.post(start_url("nope"))

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "project not found"}}


async def test_malformed_project_id_is_404_not_a_server_error(client):
    assert (await client.post(start_url("a.b"))).status_code == 404
    assert (await client.post(start_url("x" * 100))).status_code == 404


async def test_without_a_run_service_starting_a_run_is_503(make_client, store):
    seed_project(store, finished=False, state=RunState.BRIEF_RECEIVED)

    async with make_client() as client:
        response = await client.post(start_url())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "run_service_unavailable"


async def test_a_crashing_run_marks_the_project_failed(make_client, store):
    seed_project(store, finished=False, state=RunState.PLANNED)

    async with make_client(CrashingRunService()) as client:
        await client.post(start_url())
        record = None
        for _ in range(100):
            record = store.read(store.paths(PROJECT_ID).run, RunRecord)
            if record.state is RunState.FAILED:
                break
            await asyncio.sleep(0.01)

    assert record.state is RunState.FAILED
    assert record.error == "run crashed: RuntimeError: renderer exploded"
    assert record.failed_after is RunState.PLANNED


async def test_a_crash_never_overwrites_a_run_that_already_finished(make_client, store):
    seed_project(store, finished=False, state=RunState.DONE)

    async with make_client(CrashingRunService()) as client:
        await client.post(start_url())
        await asyncio.sleep(0.1)

    assert store.read(store.paths(PROJECT_ID).run, RunRecord).state is RunState.DONE


async def test_project_endpoint_returns_run_and_brief(client, store):
    seed_project(store)

    response = await client.get(f"/api/projects/{PROJECT_ID}")

    body = response.json()
    assert response.status_code == 200
    assert body["run"]["state"] == "DONE"
    assert body["brief"]["product_name"] == "Acme Notes"


async def test_project_with_unreadable_run_record_is_a_storage_error(client, store):
    paths = seed_project(store)
    paths.run.write_text("{not json")

    response = await client.get(f"/api/projects/{PROJECT_ID}")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "storage_error"
    assert "not json" not in response.text


async def test_project_with_missing_run_record_is_404(client, store):
    paths = seed_project(store)
    paths.run.unlink()

    response = await client.get(f"/api/projects/{PROJECT_ID}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
