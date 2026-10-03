from pathlib import Path

import pytest

from preflight.config import Settings
from preflight.storage import ProjectStore
from tests.orchestrator.fakes import World


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(store=ProjectStore(tmp_path), settings=Settings(step_timeout_s=5.0))
