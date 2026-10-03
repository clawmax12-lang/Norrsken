import pytest

from preflight.config import Settings

_PROVIDER_ENV = ("GEMINI_API_KEY", "CONDENSE_API_KEY", "TRIBE_ENDPOINT")


@pytest.fixture(autouse=True)
def _no_real_configuration(monkeypatch):
    """Tests never see the developer's .env or exported provider keys."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for name in _PROVIDER_ENV:
        monkeypatch.delenv(name, raising=False)
