from datetime import UTC, datetime

import httpx

from preflight.api import create_app
from preflight.config import Settings
from preflight.contracts import RunRecord, RunState
from preflight.storage import ProjectStore
from tests.export.seed import PROJECT_ID, seed_project
from tests.intake.imaging import png

ORIGIN = "http://localhost:3000"


async def test_health(client):
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_routes_use_the_error_envelope(client):
    response = await client.get("/api/nothing")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}


async def test_wrong_method_uses_the_error_envelope(client):
    response = await client.delete("/api/health")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


async def test_the_local_frontend_origin_is_allowed_by_default(client):
    response = await client.get("/api/health", headers={"Origin": ORIGIN})

    assert response.headers["access-control-allow-origin"] == ORIGIN


async def test_preflight_requests_allow_the_headers_the_frontend_needs(client):
    response = await client.options(
        "/api/briefs",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN


async def test_other_origins_get_no_cors_headers(client):
    response = await client.get("/api/health", headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers


async def test_range_headers_are_exposed_to_the_browser(client):
    response = await client.get("/api/health", headers={"Origin": ORIGIN})

    assert "Content-Range" in response.headers["access-control-expose-headers"]


async def test_allowed_origins_are_configurable(tmp_path):
    settings = Settings(data_dir=tmp_path, cors_origins=["https://preflight.example"])
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        allowed = await http.get("/api/health", headers={"Origin": "https://preflight.example"})
        denied = await http.get("/api/health", headers={"Origin": ORIGIN})

    assert allowed.headers["access-control-allow-origin"] == "https://preflight.example"
    assert "access-control-allow-origin" not in denied.headers


def test_default_cors_origin_is_the_local_frontend():
    assert Settings().cors_origins == [ORIGIN]


async def test_in_flight_runs_are_cancelled_on_shutdown(store, tmp_path, run_service):
    seed_project(store, finished=False, state=RunState.BRIEF_RECEIVED)
    app = create_app(Settings(data_dir=tmp_path / "projects"), store=store, run_service=run_service)
    transport = httpx.ASGITransport(app=app)

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
            await http.post(f"/api/projects/{PROJECT_ID}/run")
            await run_service.started.wait()
        runs = app.state.context.runs
        assert runs.is_running(PROJECT_ID)

    assert not runs.is_running(PROJECT_ID)


async def test_the_default_clock_stamps_real_time(tmp_path):
    app = create_app(Settings(data_dir=tmp_path / "projects"))
    before = datetime.now(UTC)
    files = [("screenshots", (f"{n}.png", png(), "image/png")) for n in range(3)]
    fields = {"product_name": "Acme", "one_liner": "x", "goal": "signups", "audience": "founders"}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as http:
        project_id = (await http.post("/api/briefs", data=fields, files=files)).json()["project_id"]

    run = ProjectStore(tmp_path / "projects").read(
        ProjectStore(tmp_path / "projects").paths(project_id).run, RunRecord
    )
    assert before <= run.updated_at <= datetime.now(UTC)
