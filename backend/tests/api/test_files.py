import pytest

from preflight.contracts import BrainArtifact, SimulatorName
from tests.export.seed import BRAIN_BYTES, PROJECT_ID, VIDEO_BYTES, add_sound, seed_project
from tests.factories import make_result


def file_url(kind, variant="A", project_id=PROJECT_ID):
    return f"/api/projects/{project_id}/files/{kind}/{variant}"


async def test_video_is_served_as_mp4_with_range_support_advertised(client, store):
    seed_project(store)

    response = await client.get(file_url("video"))

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.content == VIDEO_BYTES["A"]


async def test_a_byte_range_gets_a_206_partial_response(client, store):
    seed_project(store)

    response = await client.get(file_url("video"), headers={"Range": "bytes=10-19"})

    assert response.status_code == 206
    assert response.content == VIDEO_BYTES["A"][10:20]
    assert response.headers["content-range"] == f"bytes 10-19/{len(VIDEO_BYTES['A'])}"


async def test_an_open_ended_and_a_suffix_range_work(client, store):
    seed_project(store)
    video = VIDEO_BYTES["A"]

    tail = await client.get(file_url("video"), headers={"Range": f"bytes={len(video) - 5}-"})
    suffix = await client.get(file_url("video"), headers={"Range": "bytes=-7"})

    assert tail.content == video[-5:]
    assert suffix.content == video[-7:]
    assert tail.status_code == suffix.status_code == 206


async def test_an_unsatisfiable_range_is_416(client, store):
    seed_project(store)

    response = await client.get(file_url("video"), headers={"Range": "bytes=999999-"})

    assert response.status_code == 416


async def test_brain_artifacts_are_served(client, store):
    seed_project(store, brain=True)

    activity = await client.get(file_url("brain-activity"))
    groups = await client.get(file_url("brain-groups"))

    assert activity.content == BRAIN_BYTES
    assert activity.headers["content-type"] == "application/octet-stream"
    assert groups.json() == {"visual": [0, 1, 2]}


@pytest.mark.parametrize("kind", ["brain-activity", "brain-groups"])
async def test_brain_files_are_404_when_the_brain_sim_did_not_run(client, store, kind):
    seed_project(store)

    response = await client.get(file_url(kind))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_a_missing_video_is_404(client, store):
    seed_project(store)

    assert (await client.get(file_url("video", "C"))).status_code == 404


@pytest.mark.parametrize("kind", ["passwd", "brief", "run", "exports", "..", "log"])
async def test_only_allow_listed_kinds_are_served(client, store, kind):
    seed_project(store)

    response = await client.get(file_url(kind))

    assert response.status_code in (404, 422)


@pytest.mark.parametrize("variant", ["a", "AA", "1", "A.mp4", "%2e%2e", "..%2f..%2fbrief"])
async def test_variant_must_be_a_single_capital_letter(client, store, variant):
    seed_project(store)

    response = await client.get(file_url("video", variant))

    assert response.status_code in (404, 422)
    assert response.json()["error"]["code"] in ("not_found", "validation_error")


@pytest.mark.parametrize(
    "path",
    [
        "/api/projects/..%2F..%2Fetc/results",
        "/api/projects/..%2Fproj-1/results",
        f"/api/projects/{PROJECT_ID}/files/video/..%2F..%2Fbrief.json",
        f"/api/projects/{PROJECT_ID}/export/..%2Fbrief.json",
        f"/api/projects/{PROJECT_ID}/export/%2e%2e/%2e%2e/etc/passwd",
        f"/api/projects/{PROJECT_ID}/../../../etc/passwd",
    ],
)
async def test_path_traversal_in_the_url_reaches_nothing(client, store, tmp_path, path):
    seed_project(store)
    (tmp_path / "secret.txt").write_text("secret")

    response = await client.get(path)

    assert response.status_code in (404, 422)
    assert "secret" not in response.text
    assert "root:" not in response.text


def point_brain_at(store, paths, activity_path):
    artifact = BrainArtifact(
        n_vertices=3, activity_path=activity_path, atlas="a", groups_path="brain/A/groups.json"
    )
    store.write(
        paths.simulation("A", "tribe_v2"), make_result("A", SimulatorName.TRIBE_V2, brain=artifact)
    )


async def test_a_brain_path_that_climbs_out_of_the_project_is_not_served(client, store, tmp_path):
    paths = seed_project(store)
    (tmp_path / "secret.txt").write_text("secret")
    point_brain_at(store, paths, "../../secret.txt")

    response = await client.get(file_url("brain-activity"))

    assert response.status_code == 404
    assert "secret" not in response.text


async def test_an_absolute_brain_path_outside_the_project_is_not_served(client, store, tmp_path):
    paths = seed_project(store)
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    point_brain_at(store, paths, str(outside))

    assert (await client.get(file_url("brain-activity"))).status_code == 404


async def test_a_symlink_that_escapes_the_project_is_not_served(client, store, tmp_path):
    paths = seed_project(store)
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    (paths.brain_dir("A")).mkdir(parents=True)
    (paths.brain_dir("A") / "activity.npy").symlink_to(outside)
    point_brain_at(store, paths, "brain/A/activity.npy")

    response = await client.get(file_url("brain-activity"))

    assert response.status_code == 404
    assert "secret" not in response.text


async def test_brain_files_are_404_when_the_tribe_result_has_no_brain_artifact(client, store):
    paths = seed_project(store)
    store.write(paths.simulation("A", "tribe_v2"), make_result("A", SimulatorName.TRIBE_V2))

    assert (await client.get(file_url("brain-activity"))).status_code == 404


async def test_the_player_video_prefers_the_cut_with_sound_once_it_exists(client, store):
    paths = seed_project(store)
    before = await client.get(file_url("video"))
    final = add_sound(store, paths, "A")

    with_sound = await client.get(file_url("video-final"))
    player = await client.get(file_url("video"))

    assert before.content == VIDEO_BYTES["A"]
    assert with_sound.status_code == 200
    assert with_sound.headers["content-type"] == "video/mp4"
    assert with_sound.content == final
    assert player.content == final


async def test_there_is_no_cut_with_sound_until_sound_was_added(client, store):
    seed_project(store)

    assert (await client.get(file_url("video-final"))).status_code == 404
