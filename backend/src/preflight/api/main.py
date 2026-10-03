"""The production server: ``uvicorn preflight.api.main:create_production_app --factory``."""

import logging
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI

from preflight.config import get_settings
from preflight.storage import ProjectStore
from preflight.wiring import ProductionRunService

from .app import create_app

_HTTP_TIMEOUT = httpx.Timeout(300.0, connect=10.0)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def create_production_app() -> FastAPI:
    """The API wired to the real pipeline (Gemini via Condense, Remotion, optional TRIBE)."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = get_settings()
    store = ProjectStore(settings.data_dir)
    http = httpx.AsyncClient(timeout=_HTTP_TIMEOUT)
    service = ProductionRunService(settings, store, http, _utc_now)
    return create_app(
        settings, store=store, run_service=service, clock=_utc_now, on_shutdown=http.aclose
    )
