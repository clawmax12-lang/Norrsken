import json

import httpx
import pytest

from preflight.contracts import BrainArtifact, SimulatorName
from preflight.errors import ProviderError, SimulatorUnavailableError, TransientProviderError
from preflight.ports import SimulationRequest
from preflight.simulators.tribe import TribeSimulator
from tests.factories import SHA, make_brief, make_concept, make_result

ENDPOINT = "http://gpu:8080"
BRAIN = BrainArtifact(
    n_vertices=20484, activity_path="activity.npy", atlas="destrieux", groups_path="groups.json"
)


def result_json(brain: BrainArtifact | None = BRAIN) -> dict:
    result = make_result("A", SimulatorName.TRIBE_V2, brain=brain)
    return json.loads(result.model_dump_json())


def job(status: str, result: dict | None = None, error: str | None = None) -> dict:
    return {
        "job_id": "j1",
        "status": status,
        "video_sha256": SHA,
        "cached": False,
        "error": error,
        "result": result,
    }


def make_simulator(tmp_path, handler):
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(record))
    simulator = TribeSimulator(http, f"{ENDPOINT}/", tmp_path, poll_interval_s=0)
    video = tmp_path / "videos" / "A.mp4"
    video.parent.mkdir()
    video.write_bytes(b"mp4-bytes")
    request = SimulationRequest(
        brief=make_brief(),
        concept=make_concept("A"),
        video_path=video,
        video_sha256=SHA,
        artifacts_dir=tmp_path / "brain" / "A",
    )
    return simulator, request, seen


def worker(statuses: list[dict]):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path == "/jobs":
            return httpx.Response(202, json=statuses.pop(0))
        if path == "/jobs/j1":
            return httpx.Response(200, json=statuses.pop(0))
        if path.startswith("/jobs/j1/artifacts/"):
            return httpx.Response(200, content=path.rsplit("/", 1)[1].encode())
        return httpx.Response(404)

    return handler


async def test_uploads_polls_and_stores_the_brain_artifacts_in_the_project(tmp_path) -> None:
    statuses = [job("queued"), job("running"), job("succeeded", result_json())]
    simulator, request, seen = make_simulator(tmp_path, worker(statuses))

    result = await simulator.simulate(request)

    upload = seen[0]
    assert (upload.method, str(upload.url)) == ("POST", f"{ENDPOINT}/jobs")
    assert b'name="variant_id"\r\n\r\nA' in upload.content
    assert b"mp4-bytes" in upload.content
    assert result.brain is not None
    assert result.brain.activity_path == "brain/A/activity.npy"
    assert result.brain.groups_path == "brain/A/groups.json"
    assert (tmp_path / "brain" / "A" / "activity.npy").read_bytes() == b"activity.npy"
    assert (tmp_path / "brain" / "A" / "groups.json").read_bytes() == b"groups.json"


async def test_result_without_brain_artifacts_is_returned_as_is(tmp_path) -> None:
    simulator, request, _ = make_simulator(
        tmp_path, worker([job("succeeded", result_json(brain=None))])
    )

    result = await simulator.simulate(request)

    assert result.brain is None


async def test_failed_job_is_a_provider_error(tmp_path) -> None:
    simulator, request, _ = make_simulator(
        tmp_path, worker([job("queued"), job("failed", error="CUDA out of memory")])
    )

    with pytest.raises(ProviderError, match="CUDA out of memory"):
        await simulator.simulate(request)


@pytest.mark.parametrize(
    ("status", "error"),
    [(503, TransientProviderError), (500, TransientProviderError), (422, ProviderError)],
)
async def test_worker_errors_are_mapped(tmp_path, status, error) -> None:
    simulator, request, _ = make_simulator(tmp_path, lambda _r: httpx.Response(status, text="x"))

    with pytest.raises(error):
        await simulator.simulate(request)


async def test_unreachable_worker_means_the_simulator_is_unavailable(tmp_path) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    simulator, request, _ = make_simulator(tmp_path, refuse)

    with pytest.raises(SimulatorUnavailableError):
        await simulator.simulate(request)


async def test_unexpected_body_is_a_provider_error(tmp_path) -> None:
    simulator, request, _ = make_simulator(tmp_path, lambda _r: httpx.Response(202, json=[1]))

    with pytest.raises(ProviderError, match="unexpected body"):
        await simulator.simulate(request)
