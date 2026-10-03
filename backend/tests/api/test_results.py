from preflight.contracts import RenderStatus, RunRecord, RunState, VariantRecord
from tests.export.seed import NOW, PROJECT_ID, add_sound, seed_project


async def get_results(client, project_id=PROJECT_ID):
    return await client.get(f"/api/projects/{project_id}/results")


async def test_a_finished_project_returns_ranking_report_and_variants(client, store):
    seed_project(store)

    response = await get_results(client)

    body = response.json()
    assert response.status_code == 200
    assert body["state"] == "DONE"
    assert body["ranking"]["order"] == ["A", "B"]
    assert body["report"]["winner"] == "A"
    assert [variant["variant_id"] for variant in body["variants"]] == ["A", "B"]


async def test_variants_carry_concept_and_simulation_series_and_events(client, store):
    seed_project(store)

    variant = (await get_results(client)).json()["variants"][0]

    assert variant["concept"]["hook"] == "Notes that organise themselves"
    simulation = variant["simulations"][0]
    assert simulation["simulator"] == "gemini_panel"
    assert simulation["series"]["signal"] == [0.5] * 15
    assert simulation["events"] == []


async def test_files_list_only_what_exists_with_urls(client, store):
    seed_project(store, brain=True)

    variants = (await get_results(client)).json()["variants"]

    assert variants[0]["files"] == {
        "video": f"/api/projects/{PROJECT_ID}/files/video/A",
        "brain-activity": f"/api/projects/{PROJECT_ID}/files/brain-activity/A",
        "brain-groups": f"/api/projects/{PROJECT_ID}/files/brain-groups/A",
    }
    assert variants[1]["files"] == {"video": f"/api/projects/{PROJECT_ID}/files/video/B"}


async def test_brain_data_is_never_inlined(client, store):
    seed_project(store, brain=True)

    tribe = next(
        s
        for s in (await get_results(client)).json()["variants"][0]["simulations"]
        if s["simulator"] == "tribe_v2"
    )

    assert tribe["brain"]["activity_path"] == "brain/A/activity.npy"
    assert set(tribe["brain"]) == {"mesh", "n_vertices", "activity_path", "atlas", "groups_path"}


async def test_results_so_far_before_scoring_have_no_ranking_or_report(client, store):
    seed_project(store, finished=False, state=RunState.SIMULATED)

    body = (await get_results(client)).json()

    assert body["state"] == "SIMULATED"
    assert body["ranking"] is None
    assert body["report"] is None
    assert len(body["variants"]) == 2


async def test_a_project_that_has_only_started_has_no_variants(client, store):
    seed_project(store, variants=(), finished=False, state=RunState.BRIEF_RECEIVED)

    body = (await get_results(client)).json()

    assert body["variants"] == []


async def test_render_progress_comes_from_the_run_record(client, store):
    paths = seed_project(store, finished=False, state=RunState.RENDERED)
    store.write(
        paths.run,
        RunRecord(
            project_id=PROJECT_ID,
            state=RunState.RENDERED,
            variants=(VariantRecord(variant_id="A", render_status=RenderStatus.RENDERED),),
            updated_at=NOW,
        ),
    )

    variants = (await get_results(client)).json()["variants"]

    assert variants[0]["render"]["render_status"] == "rendered"
    assert variants[1]["render"] is None


async def test_unknown_project_is_404(client):
    assert (await get_results(client, "missing")).status_code == 404


async def test_sound_is_listed_with_its_file_and_record_once_added(client, store):
    paths = seed_project(store)
    add_sound(store, paths, "A")

    variants = (await client.get(f"/api/projects/{PROJECT_ID}/results")).json()["variants"]

    assert variants[0]["files"]["video-final"] == f"/api/projects/{PROJECT_ID}/files/video-final/A"
    assert variants[0]["sound"]["narrated"] is True
    assert variants[0]["sound"]["voice"] == "Kore"
    assert variants[1]["sound"] is None
    assert "video-final" not in variants[1]["files"]
