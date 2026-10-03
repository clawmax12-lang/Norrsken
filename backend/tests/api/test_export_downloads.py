import pytest

from preflight.contracts import Report
from tests.export.seed import PROJECT_ID, VIDEO_BYTES, make_report, seed_project


def export_url(name, project_id=PROJECT_ID):
    return f"/api/projects/{project_id}/export/{name}"


async def test_winner_and_runner_up_download_as_attachments(client, store):
    seed_project(store)

    winner = await client.get(export_url("winner.mp4"))
    runner_up = await client.get(export_url("runner_up.mp4"))

    assert winner.content == VIDEO_BYTES["A"]
    assert runner_up.content == VIDEO_BYTES["B"]
    assert winner.headers["content-type"] == "video/mp4"
    assert 'filename="winner.mp4"' in winner.headers["content-disposition"]
    assert winner.headers["content-disposition"].startswith("attachment")


async def test_report_json_downloads_and_matches_the_report_contract(client, store):
    seed_project(store)

    response = await client.get(export_url("report.json"))

    assert response.headers["content-type"].startswith("application/json")
    assert Report.model_validate_json(response.content) == make_report()


async def test_launch_brief_downloads_as_markdown(client, store):
    seed_project(store)

    response = await client.get(export_url("launch_brief.md"))

    assert response.headers["content-type"].startswith("text/markdown")
    assert response.text.startswith("# Launch brief: Acme Notes")
    assert "live A/B test" in response.text


async def test_with_one_surviving_variant_the_runner_up_is_a_clear_404(client, store):
    seed_project(store, variants=("A",))

    missing = await client.get(export_url("runner_up.mp4"))
    winner = await client.get(export_url("winner.mp4"))

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "no_runner_up"
    assert "no runner-up video" in missing.json()["error"]["message"]
    assert winner.status_code == 200


@pytest.mark.parametrize("name", ["winner.mp4", "runner_up.mp4", "report.json", "launch_brief.md"])
async def test_exports_before_results_exist_are_404(client, store, name):
    seed_project(store, finished=False)

    response = await client.get(export_url(name))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("name", ["brief.json", "run.json", "log.jsonl", "winner.mov", "x"])
async def test_only_the_four_export_names_are_served(client, store, name):
    seed_project(store)

    response = await client.get(export_url(name))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_exports_for_an_unknown_project_are_404(client):
    assert (await client.get(export_url("report.json", "missing"))).status_code == 404
