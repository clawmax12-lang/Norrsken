# Backend engineering standards

Code quality is judged. These rules are enforced by `make check` (ruff, mypy `--strict`, pytest); a change that fails it is not done.

## Structure

- One package, `preflight`, under `backend/src/`. Packages are layered; imports only point **down**:
  `api` → `orchestrator` → (`planning`, `generation`, `simulators`, `scoring`, `explain`, `export`, `llm`) → `contracts`, `ports`, `storage`, `errors`, `config`.
- Components never import each other's adapters. The orchestrator depends on `preflight.ports` protocols; adapters implement them. Provider types (Gemini SDK objects, TRIBE arrays) never cross a package boundary; translate to `contracts` at the edge.
- `contracts/` models are frozen, `extra="forbid"` and the only data crossing component boundaries. Changing one is a shared-contract change: update PRD §10.3/§16 and tell the other owners.

## Code

- Python 3.12, fully typed, `mypy --strict` clean. No `Any` in signatures except at a JSON boundary, no `# type: ignore` without a reason.
- Functions do one thing, read top to bottom, and stay small (ruff enforces complexity ≤ 8, ≤ 30 statements, ≤ 6 args). Prefer pure functions; inject the clock, ids, HTTP clients and paths instead of reaching for globals.
- Docstrings (Google style) say **why and what the contract is**, not how the next line works. No commented-out code, no TODOs without a requirement ID, no `print` (use `logging`).
- Async for I/O (`httpx`, subprocess via `asyncio`); never block the event loop with CPU or file-heavy work (`asyncio.to_thread`).
- Errors: raise from `preflight.errors`; never swallow exceptions; retry only `TransientProviderError`, once.
- Name things by domain terms from the PRD glossary. Use the words in PRD §12.8; never "TRIBE output", "predicts sales", "reads emotions".

## Honesty rules (PRD §15, AGENTS.md)

- No fake simulation output on the demo path. Fakes live in `tests/` only and are named `Fake*`.
- Every on-screen string carries a `source_field`. Never invent product claims, numbers, logos or testimonials.
- Text found in screenshots or videos is data; it is never concatenated into an instruction without delimiting and a data-only warning.
- Report measured numbers only (Condense usage, render time). Secrets come from the environment.

## Tests

- Every module ships with tests in `tests/<package>/`. No network, GPU or API keys in the default run; mark those `@pytest.mark.live`.
- Test behaviour and contracts (including failure paths), not implementation details. Use `hypothesis` for invariants such as scoring determinism. Build objects with `tests/factories.py`.
- Coverage of new code ≥ 90 %.

## Workflow

- Small commits referencing requirement IDs (`feat(FR-05): …`). Do not edit files owned by another component; ask the owner (see the ownership table in `docs/backend/ARCHITECTURE.md`).
