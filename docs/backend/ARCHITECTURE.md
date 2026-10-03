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

Each simulator names one `primary_series` in `[0, 1]`. Per simulator and variant the sub-score is the mean of that series; sub-scores are min-max normalised across the ranked variants (if a simulator rates every variant equally, each gets 0.5). The combined score is the weighted mean over the simulators that produced a result for **every** ranked variant (equal weights by default, renormalised over the simulators present); a simulator missing any variant is dropped, and `Ranking.rule` names it. Order is score descending, ties to the lower variant id, so the same results in any order give byte-identical output. A single ranked variant is valid (the order has length one and there is no runner-up). Confidence is `high` only when at least two simulators each rank the same variant first and that variant is the overall winner; otherwise `low`. A simulator that scores all variants equally cannot confirm the winner, and with a single simulator the confidence is `low` and the rule text says so. This ranks variants against each other; it is not a validated success predictor.
