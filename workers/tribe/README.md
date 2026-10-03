# TRIBE worker

## Any GPU machine

On a CUDA machine with roughly 32 GB+ of GPU memory and `HF_TOKEN` set in its environment (approved Llama-3.2-3B access), run `make install-gpu && make run` here. Then, from any machine that can reach it:

```bash
python workers/tribe/deploy/demo_bundle.py --endpoint http://<gpu-host>:8001 --video owned.mp4 \
  --title "Example" --license "Owned by <company>; shown with permission"
```

It uses only the worker's own routes, checks that the result belongs to exactly the uploaded bytes and writes the same bundle as below. The same address is what the backend's `TRIBE_ENDPOINT` points to.

## Cloud GPU run (Modal)

`deploy/modal_app.py` runs this unmodified worker on a Modal cloud GPU (L40S, 48 GB) and turns one genuine TRIBE v2 inference into a `preflight.demo-bundle.v1` that the brain's `CanvasBrain demoBundleUrl` seam loads as **Demo example · precomputed**. It does not deploy a public endpoint and adds no model behaviour.

One-time setup (no keys in chat, files or commits):

1. Hugging Face: accept the licence for [meta-llama/Llama-3.2-3B](https://huggingface.co/meta-llama/Llama-3.2-3B) (Meta approves it) and create a read token.
2. Modal: create an account and add a payment method (Modal refuses GPU functions without one), then in this workspace run `pip install modal && modal token new` and finish the browser login.
3. In the Modal dashboard, create a secret named `preflight-huggingface` with the key `HF_TOKEN`.

Run from the repository root:

```bash
modal run workers/tribe/deploy/check_access.py          # CPU only: token present, gated repos readable
modal run workers/tribe/deploy/modal_app.py --video owned.mp4 \
  --title "Example" --license "Owned by <company>; shown with permission"
```

The video must be an MP4 of at most 60 s that the team may show. The bundle (video, `activity.npy`, `groups.json`, `manifest.json`, `run-evidence.json`) is written to `.context/demo-bundles/<sha12>/`, which Git ignores. Hosting it for the web app is a separate decision. Weights and caches stay on the `preflight-tribe-cache` Modal volume. The first run downloads the checkpoints and feature models, so it is slow. Record the GPU, load time and inference time from `run-evidence.json` in TEAM.md as the FR-04 go/no-go evidence.

TRIBE v2 is CC BY-NC 4.0 (research and non-commercial use; see PRD §11).
