"""FR-04 ``simulate_tribe``: send a rendered variant to our TRIBE GPU worker (``workers/tribe``).

The worker queues one inference at a time: ``POST /jobs`` answers 202 with a job, ``GET
/jobs/{id}`` reports ``queued``/``running``/``succeeded``/``failed`` and, once succeeded,
carries the :class:`SimulationResult`. Its brain artifacts (per-vertex activity and region
groups) are downloaded next to the variant so the API can serve them to the brain viewer.
Nothing here ever produces brain data itself: no worker, no result.
"""

import asyncio
from pathlib import Path
from typing import Any

import httpx

from preflight.contracts import SimulationResult, SimulatorName
from preflight.errors import ProviderError, SimulatorUnavailableError, TransientProviderError
from preflight.ports import SimulationRequest

DEFAULT_POLL_INTERVAL_S = 2.0
_SERVER_ERROR = 500
_QUEUE_FULL = 503


class TribeSimulator:
    """Implements ``ports.Simulator`` against the worker at ``endpoint`` for one project."""

    name = SimulatorName.TRIBE_V2

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        endpoint: str,
        project_root: Path,
        *,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    ) -> None:
        """Artifact paths in results are rewritten relative to ``project_root``."""
        self._http = http_client
        self._endpoint = endpoint.rstrip("/")
        self._project_root = project_root
        self._poll_interval_s = poll_interval_s

    async def simulate(self, request: SimulationRequest) -> SimulationResult:
        """Analyse ``request.video_path`` and return the worker's genuine prediction.

        Raises:
            SimulatorUnavailableError: The worker cannot be reached.
            TransientProviderError: The worker's queue is full or it answered 5xx.
            ProviderError: The job failed or the worker answered something unusable.
        """
        job = await self._submit(request)
        while job["status"] in {"queued", "running"}:
            await asyncio.sleep(self._poll_interval_s)
            job = await self._call("GET", f"/jobs/{job['job_id']}")
        if job["status"] != "succeeded" or job.get("result") is None:
            raise ProviderError(f"TRIBE job {job.get('job_id')} failed: {job.get('error')}")
        result = SimulationResult.model_validate(job["result"])
        return await self._with_local_artifacts(result, str(job["job_id"]), request.artifacts_dir)

    async def _submit(self, request: SimulationRequest) -> dict[str, Any]:
        video = await asyncio.to_thread(request.video_path.read_bytes)
        return await self._call(
            "POST",
            "/jobs",
            files={"video": (request.video_path.name, video, "video/mp4")},
            data={"variant_id": request.concept.variant_id},
        )

    async def _with_local_artifacts(
        self, result: SimulationResult, job_id: str, artifacts_dir: Path
    ) -> SimulationResult:
        if result.brain is None:
            return result
        await asyncio.to_thread(artifacts_dir.mkdir, parents=True, exist_ok=True)
        relative = {}
        for field in ("activity_path", "groups_path"):
            name = Path(getattr(result.brain, field)).name
            target = artifacts_dir / name
            await self._download(f"/jobs/{job_id}/artifacts/{name}", target)
            relative[field] = str(target.relative_to(self._project_root))
        brain = result.brain.model_copy(update=relative)
        return result.model_copy(update={"brain": brain})

    async def _download(self, path: str, target: Path) -> None:
        response = await self._send("GET", path)
        await asyncio.to_thread(target.write_bytes, response.content)

    async def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        response = await self._send(method, path, **kwargs)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError(f"TRIBE worker answered non-JSON to {method} {path}") from exc
        if not isinstance(payload, dict) or "status" not in payload:
            raise ProviderError(f"TRIBE worker answered an unexpected body to {method} {path}")
        return payload

    async def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:  # noqa: ANN401
        try:
            response = await self._http.request(method, f"{self._endpoint}{path}", **kwargs)
        except httpx.TransportError as exc:
            raise SimulatorUnavailableError(f"TRIBE worker unreachable: {exc!r}") from exc
        if response.status_code == _QUEUE_FULL or response.status_code >= _SERVER_ERROR:
            raise TransientProviderError(f"TRIBE worker answered {response.status_code}")
        if response.is_error:
            raise ProviderError(f"TRIBE worker answered {response.status_code}: {response.text}")
        return response
