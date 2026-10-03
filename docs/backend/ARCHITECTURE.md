# Backend architecture

Source of truth for requirements is [PRD.md](../../PRD.md) (§8 requirements, §9 agent design and §9.2 generation layer, §10 architecture). This document describes how the code is organised.

```
Brief ─► plan ─► generate assets ─► compose ─► render ─► simulate ─► score ─► explain ─► export
          │          │               │          │          │           │         │
       Planner  AssetGenerator   (pure fn)   Renderer   Simulator[]  (pure)  Explainer
```

The orchestrator (`preflight.orchestrator`) is a deterministic, resumable state machine (`BRIEF_RECEIVED → PLANNED → RENDERED → SIMULATED → SCORED → EXPLAINED → DONE/FAILED`). Each step writes JSON under `data/projects/{id}/` (`preflight.storage`) and appends to a live activity log. Components are wired through the protocols in `preflight/ports.py`.

## Layout

| Path | Responsibility | Requirements |
| --- | --- | --- |
| `backend/src/preflight/contracts/` | Frozen Pydantic models: Brief, CreativeConcept, CompositionSpec, SimulationResult, Ranking, Report, run/log | §10.3 |
| `backend/src/preflight/ports.py` | Protocols between components | §10.2 |
| `backend/src/preflight/storage/` | Atomic per-project JSON/JSONL persistence | §9 |
| `backend/src/preflight/llm/` | Condense-routed Gemini client, usage metering | FR-10 |
| `backend/src/preflight/planning/` | `plan_variants`, grounding checks | FR-02 |
| `backend/src/preflight/generation/` | Asset generation, composition, Remotion invocation | FR-03, §9.2 |
| `backend/src/preflight/simulators/` | TRIBE client, Gemini viewer panel | FR-04 |
| `backend/src/preflight/scoring/` | Deterministic score, rank, confidence | FR-05 |
| `backend/src/preflight/explain/` | Timestamped reasons | FR-06 |
| `backend/src/preflight/export/` | Winner/runner-up MP4, `report.json`, launch brief | FR-08 |
| `backend/src/preflight/orchestrator/` | State machine, retries, activity log, resume | FR-09 |
| `backend/src/preflight/api/` | FastAPI app: briefs, runs, SSE log, results, downloads | FR-01, FR-07 |
| `workers/tribe/` | GPU worker wrapping `vendor/tribev2`; speaks `SimulationResult` over HTTP | FR-04, FR-12 |
| `workers/renderer/` | Remotion project rendering `CompositionSpec` | FR-03 |

## Scoring rule (FR-05, implementation choice logged in PRD §16)

Each simulator names one `primary_series` in `[0, 1]`. Per simulator and variant the sub-score is the mean of that series; sub-scores are min-max normalised across the variants of the run and combined with fixed weights (equal by default). Ties break on the lower variant id. Confidence is `high` when every simulator ranks the same winner, otherwise `low`; with a single simulator it is `low` and the rule text says so. This ranks variants against each other; it is not a validated success predictor.
