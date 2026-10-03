"""Send one owned video to a running TRIBE worker and write a ``preflight.demo-bundle.v1``.

For any GPU machine that runs the unmodified worker (``make install-gpu && make run`` in
``workers/tribe``). Uses only the worker's own routes (``POST /jobs``, ``GET /jobs/{id}``,
``GET /jobs/{id}/artifacts/{name}``, ``GET /health``), stdlib only, Python 3.9+::

    python workers/tribe/deploy/demo_bundle.py --endpoint http://gpu-host:8001 \
        --video owned.mp4 --title "Example" --license "Owned by <company>; shown with permission"

The result is genuine worker output for exactly these bytes; it is only marked ``precomputed``
because it is shown later as an example, never as the current run (PRD §8 FR-12).
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
POLL_SECONDS = 5


def _request(url: str, data: "bytes | None" = None, headers: "dict[str, str] | None" = None) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers or {}), timeout=120) as r:
        return r.read()


def _submit(endpoint: str, video: bytes, variant_id: str) -> dict:
    boundary = uuid.uuid4().hex
    body = b"".join(
        [
            f'--{boundary}\r\nContent-Disposition: form-data; name="variant_id"\r\n\r\n{variant_id}\r\n'.encode(),
            f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="video.mp4"\r\n'.encode(),
            b"Content-Type: video/mp4\r\n\r\n",
            video,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    return json.loads(_request(f"{endpoint}/jobs", body, headers))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--endpoint", required=True, help="base URL of the running TRIBE worker")
    parser.add_argument("--video", required=True, help="MP4 of at most 60 s the team may show")
    parser.add_argument("--title", required=True)
    parser.add_argument("--license", required=True, help="permission to show the video")
    parser.add_argument("--out", default="", help="default: .context/demo-bundles/<sha12>/")
    parser.add_argument("--variant-id", default="A")
    args = parser.parse_args()
    if not (args.title.strip() and args.license.strip()):
        sys.exit("--title and --license must not be empty")

    endpoint = args.endpoint.rstrip("/")
    source = Path(args.video)
    data = source.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print("health before:", _request(f"{endpoint}/health").decode())
    started = time.monotonic()
    job = _submit(endpoint, data, args.variant_id)
    print(f"job {job['job_id']} {job['status']} (video sha256 {sha[:12]})")
    while job["status"] in {"queued", "running"}:
        time.sleep(POLL_SECONDS)
        job = json.loads(_request(f"{endpoint}/jobs/{job['job_id']}"))
        print(f"  {job['status']} after {time.monotonic() - started:.0f} s", flush=True)
    health = json.loads(_request(f"{endpoint}/health"))
    evidence = {"job_id": job["job_id"], "health": health, "wall_seconds": round(time.monotonic() - started, 3)}
    if job["status"] != "succeeded":
        print(json.dumps({"status": job["status"], "error": job.get("error"), **evidence}, indent=2))
        sys.exit("TRIBE job failed; no bundle written")
    result = job["result"]
    if result["video_sha256"] != sha:
        sys.exit("worker analysed different bytes than were sent; refusing to write a bundle")

    target = Path(args.out) if args.out else REPO / ".context" / "demo-bundles" / sha[:12]
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target / "video.mp4")
    for name in ("activity.npy", "groups.json"):
        (target / name).write_bytes(_request(f"{endpoint}/jobs/{job['job_id']}/artifacts/{name}"))
    result["precomputed"] = True
    result["meta"] = {
        **result["meta"],
        "precomputed_from": {
            "runner": f"tribe worker at {endpoint}",
            "job_id": job["job_id"],
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }
    manifest = {
        "kind": "preflight.demo-bundle.v1",
        "title": args.title.strip(),
        "license": args.license.strip(),
        "source_video": {"url": "video.mp4", "sha256": sha, "duration_s": result["duration_s"]},
        "simulation": result,
        "activity_url": "activity.npy",
        "groups_url": "groups.json",
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), "utf-8")
    (target / "run-evidence.json").write_text(json.dumps(evidence, indent=2), "utf-8")
    print(json.dumps(evidence, indent=2))
    print(f"Demo bundle written to {target}")


if __name__ == "__main__":
    main()
