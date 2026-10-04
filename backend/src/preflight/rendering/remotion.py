"""FR-03 ``render_variant``: run the Remotion worker in ``workers/renderer`` as a subprocess.

The worker validates the spec against the exported JSON Schema, renders a 1080x1920, 30 fps
H.264 MP4 and exits 0 (rendered), 2 (invalid spec or assets: retrying cannot help) or 1
(render failure, worth the one retry).
"""

import asyncio
import hashlib
import logging
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

from preflight.contracts import CompositionSpec, RenderResult
from preflight.errors import PreflightValidationError, RenderError
from preflight.motion.scene import MotionSpec

_LOG = logging.getLogger(__name__)
_EXIT_INVALID_INPUT = 2
_STDERR_TAIL_CHARS = 600


class RemotionRenderer:
    """Implements ``ports.Renderer`` for one project; spec paths resolve inside ``assets_root``."""

    def __init__(
        self,
        worker_dir: Path,
        assets_root: Path,
        *,
        node: str = "node",
        browser: str | None = None,
        concurrency: int | None = None,
    ) -> None:
        """Render with ``node <worker_dir>/render.mjs``.

        Args:
            worker_dir: The renderer package (``npm ci`` must have been run there).
            assets_root: The project directory the spec's screenshot/backdrop paths are in.
            node: Node.js binary (>= 22.18).
            browser: Chrome binary; ``None`` lets the worker find one or download its own.
            concurrency: Frames rendered in parallel per video; ``None`` is Remotion's default.
        """
        self._script = worker_dir / "render.mjs"
        self._assets_root = assets_root
        self._node = node
        self._browser = browser
        self._concurrency = concurrency

    async def render(self, spec: CompositionSpec, output: Path) -> RenderResult:
        """Render ``spec`` to ``output`` and return its hash and render time.

        Raises:
            PreflightValidationError: The worker rejected the spec or its assets.
            RenderError: The worker is missing, failed or wrote no video.
        """
        output.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="preflight-spec-") as tmp:
            spec_path = Path(tmp) / f"{spec.variant_id}.json"
            spec_path.write_text(spec.model_dump_json(), encoding="utf-8")
            returncode, stderr = await self._run(self._command(spec_path, output))
        if returncode == _EXIT_INVALID_INPUT:
            raise PreflightValidationError(f"renderer rejected variant {spec.variant_id}: {stderr}")
        if returncode != 0:
            raise RenderError(f"renderer failed for variant {spec.variant_id}: {stderr}")
        sha256 = await asyncio.to_thread(_sha256, output)
        if sha256 is None:
            raise RenderError(f"renderer wrote no video for variant {spec.variant_id}")
        return RenderResult(
            variant_id=spec.variant_id,
            video_path=str(output),
            video_sha256=sha256,
            render_seconds=round(time.monotonic() - started, 2),
        )

    async def render_motion(self, spec: MotionSpec, output: Path) -> RenderResult:
        """Render the isolated 60 fps composition. Does not call Showcase ``render``."""
        output.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="preflight-motion-") as tmp:
            spec_path = Path(tmp) / f"{spec.variant_id}.motion.json"
            spec_path.write_text(spec.model_dump_json(), encoding="utf-8")
            command = self._command(
                spec_path,
                output,
                composition_id="PreflightMotion",
                entry="src/motion/index.ts",
            )
            returncode, stderr = await self._run(command)
        if returncode == _EXIT_INVALID_INPUT:
            raise PreflightValidationError(
                f"motion renderer rejected variant {spec.variant_id}: {stderr}"
            )
        if returncode != 0:
            raise RenderError(f"motion renderer failed for variant {spec.variant_id}: {stderr}")
        sha256 = await asyncio.to_thread(_sha256, output)
        if sha256 is None:
            raise RenderError(f"motion renderer wrote no video for variant {spec.variant_id}")
        return RenderResult(
            variant_id=spec.variant_id,
            video_path=str(output),
            video_sha256=sha256,
            render_seconds=round(time.monotonic() - started, 2),
        )

    def _command(
        self,
        spec_path: Path,
        output: Path,
        *,
        composition_id: str | None = None,
        entry: str | None = None,
    ) -> list[str]:
        command = [self._node, str(self._script), "--spec", str(spec_path), "--out", str(output)]
        command += ["--assets-root", str(self._assets_root)]
        if self._browser:
            command += ["--browser", self._browser]
        if self._concurrency:
            command += ["--concurrency", str(self._concurrency)]
        if composition_id:
            command += ["--composition-id", composition_id]
        if entry:
            command += ["--entry", entry]
        return command

    async def _run(self, command: Sequence[str]) -> tuple[int, str]:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self._script.parent,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise RenderError(f"cannot start the renderer ({command[0]}): {exc}") from exc
        try:
            stdout, stderr = await process.communicate()
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            raise
        _LOG.info("renderer: %s", stdout.decode(errors="replace").strip())
        tail = stderr.decode(errors="replace").strip()[-_STDERR_TAIL_CHARS:]
        return process.returncode or 0, tail


def _sha256(path: Path) -> str | None:
    """Hash of a non-empty file, or ``None`` when there is no video."""
    if not path.is_file() or path.stat().st_size == 0:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
