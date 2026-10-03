"""Run the TRIBE worker on a Modal cloud GPU and package one genuine result as a demo bundle.

FR-04 go/no-go and the FR-12/FR-14 example (PRD §8, §14). This file adds no model behaviour: the
remote function boots the unmodified worker app (``tribe_worker.api.create_app``) with the real
``Tribev2Predictor`` and drives it through its own HTTP routes, exactly as the backend's
``TribeSimulator`` would. The result is written next to the video it analysed with
``precomputed=true`` so the brain shows it as "Demo example · precomputed", never as a current run.

Usage (from the repository root, after ``modal token new`` and the ``preflight-huggingface``
secret; see ``workers/tribe/README.md``)::

    modal run workers/tribe/deploy/modal_app.py --video path/to/owned.mp4 \
        --title "Example" --license "Owned by the team; shown with permission"

Weights, feature caches and the atlas live on a Modal volume, never in the repository. Output goes
to ``.context/demo-bundles/<sha12>/`` (ignored by Git) unless ``--out`` says otherwise.
"""

import hashlib
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import modal

APP_NAME = "preflight-tribe"
GPU = "L40S"  # 48 GB; the worker needs roughly 28-32 GB (jobs.py), the PRD asks for 40 GB+.
CACHE = Path("/cache")
HF_SECRET = "preflight-huggingface"  # holds HF_TOKEN with approved meta-llama/Llama-3.2-3B access
POLL_SECONDS = 5
JOB_TIMEOUT_SECONDS = 3 * 60 * 60

REPO = Path(__file__).resolve().parents[3] if modal.is_local() else Path("/repo")
_IGNORE = ["**/node_modules", "**/.venv", "**/__pycache__", "**/data", "**/.pytest_cache", "**/*.ipynb"]

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg", "git", "build-essential")
    .pip_install("uv")
    .add_local_dir(REPO / "backend", "/repo/backend", copy=True, ignore=_IGNORE)
    .add_local_dir(REPO / "vendor/tribev2", "/repo/vendor/tribev2", copy=True, ignore=_IGNORE)
    .add_local_dir(REPO / "workers/tribe", "/repo/workers/tribe", copy=True, ignore=_IGNORE)
    .run_commands(
        "uv pip install --system /repo/backend /repo/vendor/tribev2 /repo/workers/tribe httpx"
    )
    .env(
        {
            "HF_HOME": str(CACHE / "hf"),
            "TORCH_HOME": str(CACHE / "torch"),
            "UV_CACHE_DIR": str(CACHE / "uv"),  # tribev2 runs whisperx through ``uvx``
            "TRIBE_WORKER_DATA_DIR": str(CACHE / "worker"),
            "TRIBE_WORKER_ATLAS_DATA_DIR": str(CACHE / "nilearn"),
            "TRIBE_WORKER_DEVICE": "cuda",
        }
    )
)

app = modal.App(APP_NAME, image=image)
cache = modal.Volume.from_name("preflight-tribe-cache", create_if_missing=True)


@app.function(
    gpu=GPU,
    volumes={str(CACHE): cache},
    secrets=[modal.Secret.from_name(HF_SECRET)],
    timeout=JOB_TIMEOUT_SECONDS,
    max_containers=1,
)
def analyse(video: bytes, variant_id: str = "A") -> dict[str, object]:
    """Submit ``video`` to the real worker and return its job, health evidence and artifacts."""
    from fastapi.testclient import TestClient  # noqa: PLC0415 - container-only dependency
    from tribe_worker.api import create_app  # noqa: PLC0415

    started = time.monotonic()
    try:
        with TestClient(create_app()) as client:  # runs the worker lifespan (queue + preload)
            submitted = client.post(
                "/jobs",
                files={"video": ("video.mp4", video, "video/mp4")},
                data={"variant_id": variant_id},
            )
            submitted.raise_for_status()
            job = submitted.json()
            while job["status"] in {"queued", "running"}:
                time.sleep(POLL_SECONDS)
                job = client.get(f"/jobs/{job['job_id']}").json()
            health = client.get("/health").json()
            if job["status"] != "succeeded":
                return {"job": job, "health": health, "wall_seconds": time.monotonic() - started}
            artifacts = {
                name: client.get(f"/jobs/{job['job_id']}/artifacts/{name}").content
                for name in ("activity.npy", "groups.json")
            }
    finally:
        cache.commit()  # keep downloaded weights and features for the next run
    return {
        "job": job,
        "health": health,
        "artifacts": artifacts,
        "wall_seconds": round(time.monotonic() - started, 3),
    }


@app.local_entrypoint()
def main(
    video: str = "",
    title: str = "",
    license: str = "",  # noqa: A002 - CLI flag name
    out: str = "",
    variant_id: str = "A",
) -> None:
    """Run one genuine inference and write a ``preflight.demo-bundle.v1`` next to its video."""
    if not (video and title.strip() and license.strip()):
        raise SystemExit("--video, --title and --license (permission to show the video) are required")
    source = Path(video)
    data = source.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"Submitting {source.name} ({len(data) / 1e6:.1f} MB, sha256 {sha[:12]}) to {GPU}")  # noqa: T201
    run = analyse.remote(data, variant_id)
    job = run["job"]
    evidence = {k: run.get(k) for k in ("health", "wall_seconds")} | {"job_id": job["job_id"]}
    if job["status"] != "succeeded":
        print(json.dumps({"status": job["status"], "error": job.get("error"), **evidence}, indent=2))  # noqa: T201
        raise SystemExit("TRIBE job failed; no bundle written")
    result = job["result"]
    if result["video_sha256"] != sha:
        raise SystemExit("worker analysed different bytes than were sent; refusing to write a bundle")

    target = Path(out) if out else REPO / ".context" / "demo-bundles" / sha[:12]
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target / "video.mp4")
    for name, content in run["artifacts"].items():
        (target / name).write_bytes(content)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result["precomputed"] = True
    result["meta"] = {
        **result["meta"],
        "precomputed_from": {"runner": f"modal {GPU}", "job_id": job["job_id"], "at": generated_at},
    }
    manifest = {
        "kind": "preflight.demo-bundle.v1",
        "title": title.strip(),
        "license": license.strip(),
        "source_video": {"url": "video.mp4", "sha256": sha, "duration_s": result["duration_s"]},
        "simulation": result,
        "activity_url": "activity.npy",
        "groups_url": "groups.json",
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), "utf-8")
    (target / "run-evidence.json").write_text(json.dumps(evidence, indent=2), "utf-8")
    print(json.dumps(evidence, indent=2))  # noqa: T201
    print(f"Demo bundle written to {target}")  # noqa: T201
