from collections.abc import AsyncIterator

import httpx
import pytest

from preflight.api import create_app
from preflight.api.sse import StreamTiming
from preflight.config import Settings
from preflight.storage import ProjectStore
from tests.api.fakes import FakeRunService
from tests.export.seed import NOW

FAST = StreamTiming(poll_interval_s=0.01, heartbeat_interval_s=0.05)


@pytest.fixture
def store(tmp_path) -> ProjectStore:
    return ProjectStore(tmp_path / "projects")


@pytest.fixture
def run_service(store) -> FakeRunService:
    return FakeRunService(store)


@pytest.fixture
def make_client(store, tmp_path):
    """Builds a client for an app wired with the given run service (none by default)."""

    def build(run_service=None) -> httpx.AsyncClient:
        settings = Settings(data_dir=tmp_path / "projects")
        app = create_app(
            settings, store=store, run_service=run_service, stream_timing=FAST, clock=lambda: NOW
        )
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        )

    return build


@pytest.fixture
async def client(make_client, run_service) -> AsyncIterator[httpx.AsyncClient]:
    async with make_client(run_service) as http:
        yield http
