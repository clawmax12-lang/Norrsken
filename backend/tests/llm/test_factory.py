import httpx
import pytest
from pydantic import SecretStr

from preflight.config import Settings
from preflight.errors import ProviderError
from preflight.llm import GeminiClient, TokenLedger, build_gemini_client


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


async def test_builds_a_client_with_the_configured_model() -> None:
    async with httpx.AsyncClient() as http:
        client = build_gemini_client(
            settings(gemini_api_key=SecretStr("g"), gemini_model="gemini-x"),
            ledger=TokenLedger(),
            http_client=http,
        )

    assert isinstance(client, GeminiClient)
    assert client.model == "gemini-x"


async def test_missing_gemini_key_is_an_explicit_error() -> None:
    async with httpx.AsyncClient() as http:
        with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
            build_gemini_client(settings(), ledger=TokenLedger(), http_client=http)


def test_settings_defaults_match_documented_values() -> None:
    config = settings()

    assert config.gemini_model == "gemini-3.8-flash"
    assert config.condense_base_url == "https://api.condense.chat"
    assert 0.0 <= config.condense_compression_rate <= 1.0
