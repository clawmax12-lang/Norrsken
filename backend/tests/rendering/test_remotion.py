import hashlib
import json
import sys
import textwrap

import pytest

from preflight.errors import PreflightValidationError, RenderError
from preflight.generation.compose import TemplateComposer
from preflight.rendering import RemotionRenderer
from tests.factories import make_brief, make_concept

SPEC = TemplateComposer().compose(make_brief(), make_concept("A"), ())


def fake_worker(tmp_path, body: str):
    """A stand-in for ``render.mjs``, run by Python instead of Node."""
    worker = tmp_path / "worker"
    worker.mkdir()
    header = "import json, sys\nargs = sys.argv[1:]\nopts = dict(zip(args[::2], args[1::2]))\n"
    (worker / "render.mjs").write_text(header + textwrap.dedent(body))
    return worker


def renderer(tmp_path, body: str, **kwargs) -> RemotionRenderer:
    return RemotionRenderer(
        fake_worker(tmp_path, body), tmp_path / "project", node=sys.executable, **kwargs
    )


async def test_renders_the_spec_and_hashes_the_video(tmp_path) -> None:
    body = """\
    seen = {"spec": json.load(open(opts["--spec"])), "opts": opts}
    json.dump(seen, open(opts["--out"] + ".seen", "w"))
    open(opts["--out"], "wb").write(b"video")
    """
    output = tmp_path / "project" / "videos" / "A.mp4"

    result = await renderer(tmp_path, body, concurrency=2).render(SPEC, output)

    assert result.variant_id == "A"
    assert result.video_sha256 == hashlib.sha256(b"video").hexdigest()
    assert result.render_seconds >= 0
    seen = json.loads((output.parent / "A.mp4.seen").read_text())
    assert seen["spec"]["variant_id"] == "A"
    assert seen["opts"]["--assets-root"] == str(tmp_path / "project")
    assert seen["opts"]["--concurrency"] == "2"


async def test_invalid_spec_exit_is_not_retryable(tmp_path) -> None:
    body = 'sys.stderr.write("SpecValidationError: bad"); sys.exit(2)'

    with pytest.raises(PreflightValidationError, match="SpecValidationError: bad"):
        await renderer(tmp_path, body).render(SPEC, tmp_path / "out.mp4")


async def test_render_failure_is_a_render_error(tmp_path) -> None:
    with pytest.raises(RenderError, match="renderer failed"):
        await renderer(tmp_path, "sys.exit(1)").render(SPEC, tmp_path / "out.mp4")


async def test_success_without_a_video_is_a_render_error(tmp_path) -> None:
    with pytest.raises(RenderError, match="wrote no video"):
        await renderer(tmp_path, "pass").render(SPEC, tmp_path / "out.mp4")


async def test_missing_node_is_a_render_error(tmp_path) -> None:
    missing = RemotionRenderer(tmp_path, tmp_path, node=str(tmp_path / "no-node"))

    with pytest.raises(RenderError, match="cannot start the renderer"):
        await missing.render(SPEC, tmp_path / "out.mp4")
