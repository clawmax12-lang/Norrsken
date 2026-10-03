"""CPU-only: is HF_TOKEN present and can it read the TRIBE and gated Llama repos? Never prints the token."""
import modal

app = modal.App("preflight-hf-check", image=modal.Image.debian_slim(python_version="3.12").pip_install("huggingface_hub"))

@app.function(secrets=[modal.Secret.from_name("preflight-huggingface")])
def check() -> dict:
    import os, tempfile
    from huggingface_hub import hf_hub_download, whoami
    report = {"hf_token_present": bool(os.environ.get("HF_TOKEN"))}
    try:
        report["account"] = whoami().get("name")
    except Exception as e:
        report["account"] = f"{type(e).__name__}"
    for repo in ("facebook/tribev2", "meta-llama/Llama-3.2-3B"):
        try:
            hf_hub_download(repo, "config.json" if "llama" in repo else "config.yaml", cache_dir=tempfile.mkdtemp())
            report[repo] = "ok"
        except Exception as e:
            report[repo] = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
    return report

@app.local_entrypoint()
def main():
    import json
    print(json.dumps(check.remote(), indent=2))
