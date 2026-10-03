# Vendored third-party code

## tribev2 (Meta FAIR)

- Upstream: https://github.com/facebookresearch/tribev2
- Vendored commit: `af58661791a351a448a489042a28f6c37e1c14b7` (upstream `main`, 23 Jun 2026, "Update README.md")
- Copied unmodified from that commit, without upstream Git history. `vendor/tribev2/LICENSE` is kept as supplied.
- License: [CC BY-NC 4.0](tribev2/LICENSE). Research and non-commercial use only. See PRD §2.3 and §11.
- Model weights are not included and must never be committed. They are downloaded from https://huggingface.co/facebook/tribev2 at runtime. The text encoder also needs approved access to Llama-3.2-3B.
- Used by the TRIBE worker (FR-04, FR-12, FR-14). Preflight code reaches it only through the `SimulationResult` boundary (PRD §10.2); do not edit files under `vendor/tribev2/`. To update, re-copy from a newer upstream commit and change the commit above.
