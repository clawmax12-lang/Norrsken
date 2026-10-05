import asyncio

import httpx
import pytest

from preflight.api import create_app
from preflight.contracts import RunRecord, RunState, SimulationResult, SimulatorName
from preflight.contracts.finalization import FinalStatus
from preflight.errors import PreflightValidationError, ProviderError, RenderError
from preflight.finalization.source import read_source
from preflight.hashing import sha256_file
from preflight.storage import ProjectStore
from tests.factories import FIXED_NOW
from tests.finalization.helpers import seed_final_world
from tests.orchestrator.fakes import FakeSimulator


async def complete(service):
    await asyncio.gather(*service._tasks.values())


async def test_exact_final_audio_bytes_are_retested_without_replacing_originals(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    paths = final.world.store.paths(final.world.project_id)
    originals = {
        p: p.read_bytes()
        for p in [
            paths.video("B"),
            paths.video("C"),
            paths.report,
            paths.ranking,
            paths.run,
            paths.spec("B"),
        ]
    }
    initial_calls = len(final.world.gemini.calls)
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    record = final.record()
    assert record.status is FinalStatus.DONE
    assert record.sound is not None
    assert record.video_sha256 == record.sound.final_video_sha256 != record.source_video_sha256
    assert all(r.video_sha256 == record.video_sha256 for r in record.simulations)
    assert len(final.world.gemini.calls) == initial_calls + 1
    assert final.opus.calls == 1
    assert record.brain_sim is False
    assert record.comparison is not None
    assert all(p.read_bytes() == content for p, content in originals.items())
    service.start("proj-1", final.command)
    assert not service._tasks and final.opus.calls == 1


async def test_duplicate_starts_across_service_instances_use_one_file_lock(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    a, b = final.service(), final.service()
    first = a.start("proj-1", final.command)
    duplicate = b.start("proj-1", final.command)
    assert first.command_id == duplicate.command_id
    assert not b._tasks
    await complete(a)
    assert final.opus.calls == 1


async def test_render_failure_resume_uses_saved_composition_not_another_opus_call(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    final.renderer.failures.add("B", RenderError("MOCK failed"), RenderError("MOCK failed"))
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.FAILED
    assert final.opus.calls == 1
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.DONE
    assert final.opus.calls == 1


async def test_no_hidden_opus_retry_and_attempts_capped_across_resume(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    final.opus.failures = 10
    service = final.service()
    for _ in range(3):
        service.start("proj-1", final.command)
        await complete(service)
    assert final.opus.calls == 2
    assert final.record().opus_attempts == 2
    assert final.record().status is FinalStatus.FAILED
    assert "limit" in final.record().error


async def test_stale_winner_nonwinner_changed_assets_and_missing_keys_rejected_before_cost(
    tmp_path,
):
    final = await seed_final_world(ProjectStore(tmp_path))
    service = final.service()
    for command in [
        final.command.model_copy(update={"variant_id": "C"}),
        final.command.model_copy(update={"source_video_sha256": "a" * 64}),
    ]:
        with pytest.raises(PreflightValidationError):
            service.start("proj-1", command)
    with pytest.raises(ProviderError, match="ANTHROPIC"):
        final.service(anthropic_api_key=None).start("proj-1", final.command)
    assert final.opus.calls == 0


async def test_source_changes_after_failed_job_cannot_buy_another_composition(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    final.renderer.failures.always("B", RenderError("MOCK failed"))
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    (final.world.store.paths("proj-1").uploads / "1.png").write_bytes(b"changed")
    with pytest.raises(PreflightValidationError, match="source changed"):
        service.start("proj-1", final.command)
    assert final.opus.calls == 1


async def test_source_changed_during_job_withholds_final_evidence(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    original = final.world.gemini.simulate

    async def mutate(request):
        result = await original(request)
        (final.world.store.paths("proj-1").uploads / "1.png").write_bytes(b"changed-mid-run")
        return result

    final.world.gemini.simulate = mutate
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.FAILED
    assert not final.record().files


async def test_optional_tribe_failure_has_honest_fallback_and_gemini_failure_blocks_export(
    tmp_path,
):
    final = await seed_final_world(ProjectStore(tmp_path))
    tribe = FakeSimulator(SimulatorName.TRIBE_V2)
    tribe.failures.always("B", ProviderError("offline"))
    final.world.extra_simulators = [tribe]
    final.world.gemini.failures.add("B", ProviderError("offline"))
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.FAILED and not final.record().files
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.DONE and final.record().brain_sim is False


async def test_wrong_video_hash_never_becomes_final_evidence(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    final.world.gemini.wrong_variant = True
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.FAILED
    assert not final.record().files
    assert (
        final.world.store.read(final.world.store.paths("proj-1").run, RunRecord).state
        is RunState.DONE
    )


async def test_api_requires_consent_and_download_is_read_only_hash_guarded(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    service = final.service()
    app = create_app(
        final.settings,
        store=final.world.store,
        finalization_service=service,
        clock=lambda: FIXED_NOW,
    )
    base = "/api/projects/proj-1/finalization"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as http:
        assert (await http.get(base)).json() is None
        command = final.command.model_dump()
        assert (await http.post(base, json={**command, "confirmed": False})).status_code == 422
        assert (await http.post(base, json={**command, "composition": {}})).status_code == 422
        assert final.opus.calls == 0
        assert (await http.post(base, json=command)).status_code == 202
        await complete(service)
        assert (await http.get(base + "/video")).status_code == 200
        evidence = (await http.get(base + "/report")).json()
        assert evidence["video_sha256"] != evidence["source_video_sha256"]
        assert final.opus.calls == 1
        (final.world.store.paths("proj-1").opus_dir / "final.mp4").write_bytes(b"tampered")
        assert (await http.get(base + "/video")).status_code == 409


async def test_api_without_finalizer_is_explicitly_unavailable(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    app = create_app(final.settings, store=final.world.store)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as http:
        response = await http.post(
            "/api/projects/proj-1/finalization", json=final.command.model_dump()
        )
        assert response.status_code == 503
        assert final.opus.calls == 0


async def test_gemini_finish_needs_no_opus_keys_and_keeps_its_director_on_resume(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    gemini = final.command.model_copy(update={"director": "gemini"})
    service = final.service(anthropic_api_key=None, condense_api_key=None)

    service.start("proj-1", gemini)
    await complete(service)

    record = final.record()
    assert record.director == "gemini"
    assert record.status is FinalStatus.DONE
    with pytest.raises(ProviderError, match="ANTHROPIC"):
        final.service(anthropic_api_key=None).start("proj-1", final.command)


async def test_a_failed_finish_resumes_only_with_the_director_it_started_with(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    final.opus.failures = 1
    service = final.service()
    service.start("proj-1", final.command)
    await complete(service)
    assert final.record().status is FinalStatus.FAILED

    with pytest.raises(PreflightValidationError, match="started with opus"):
        final.service().start("proj-1", final.command.model_copy(update={"director": "gemini"}))


async def test_the_winner_tested_with_its_soundtrack_can_be_finished(tmp_path):
    final = await seed_final_world(ProjectStore(tmp_path))
    store, project = final.world.store, final.world.project_id
    paths = store.paths(project)
    paths.final_video("B").write_bytes(b"MOCK video with narration")
    sounded = sha256_file(paths.final_video("B"))
    run = store.read(paths.run, RunRecord)
    variants = tuple(
        v.model_copy(update={"video_path": "videos/B.final.mp4", "video_sha256": sounded})
        if v.variant_id == "B"
        else v
        for v in run.variants
    )
    store.write(paths.run, run.model_copy(update={"variants": variants}))
    tested_path = paths.simulation("B", "gemini_panel")
    tested = store.read(tested_path, SimulationResult)
    store.write(tested_path, tested.model_copy(update={"video_sha256": sounded}))
    command = final.command.model_copy(update={"source_video_sha256": sounded})

    source = read_source(store, project, command, final.settings)

    assert source.concept.variant_id == "B"
