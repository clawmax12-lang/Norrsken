# Preflight

Launch videos that are tested before anyone sees them.

Preflight turns a product brief and 3–6 screenshots into three 15-second motion graphics videos, pretests them with simulated viewers, and exports a recommended winner, a runner up and a launch brief. The first customer is a founder launching an app or SaaS product. E-commerce is a later audience.

**Current approved specification: [PRD v1.1](PRD.md).** It supersedes earlier brainstorming, including editing an existing customer video. This repository is the shared reference for the hackathon team and its coding agents.

## Start here

| Document | Purpose |
| --- | --- |
| [PRD.md](PRD.md) | Product scope, FR-01–FR-15, acceptance criteria, architecture, UI, timeline and decision log. The source of truth for what to build. |
| [TEAM.md](TEAM.md) | Owners, task status, integration evidence, open blockers and the shared Git/Conductor workflow. |
| [AGENTS.md](AGENTS.md) | Instructions every coding agent must follow. Claude loads these through [CLAUDE.md](CLAUDE.md). |
| [Original PDF](docs/source/Preflight-PRD-v1.1.pdf) | Unchanged, 20-page source supplied by the product owner. [Provenance and checksum](docs/source/README.md). |

Humans: start with PRD §1–§7. Builders: also read §8–§14. Agents: read AGENTS.md and PRD §15, §8, §9, §10 and §12 before implementing.

## How to run

The repository currently includes the native SwiftUI dashboard shell for iPhone and iPad. It is an entry surface only: brief persistence, rendering, simulation, scoring, and results are not implemented, and no functional requirement acceptance criteria should be inferred from the dashboard.

```bash
git clone https://github.com/clawmax12-lang/Norrsken.git
cd Norrsken
open Preflight.xcodeproj
```

Select the shared **Preflight** scheme and run it on an iOS 17 or newer iPhone or iPad simulator. The app has no external package dependencies and does not require environment variables for the dashboard.

Command-line build verification on a Mac with Xcode 16 or newer:

```bash
xcodebuild \
  -project Preflight.xcodeproj \
  -scheme Preflight \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

Read the documents above and claim work in TEAM.md before extending the dashboard into the P0 flow. Keep this section current as runtime services are added.

## Planned build stack

The current dashboard shell uses SwiftUI. The PRD proposes Next.js, TypeScript, Tailwind and three.js for the web experience; Python/FastAPI for orchestration; Remotion for rendering; and a GPU worker for TRIBE v2. Gemini provides planning, the viewer panel and explanations, with all LLM calls routed through Condense. The dashboard does not yet connect to those services.

The PRD designates **Claude Opus 5.5** as the primary coding agent. This is a build plan, not a claim that the application has already been implemented with it. This documentation bootstrap was prepared with Codex from the supplied PDF.

Required environment variable names from PRD §10.4: `GEMINI_API_KEY`, `CONDENSE_API_KEY`, `TRIBE_ENDPOINT`. Implementation must provide `.env.example` with placeholders; never commit real credentials or model weights.

## Demo and research honesty

- Complete P0 before P1. FR-12 and FR-14 are conditional on the TRIBE go/no-go in PRD §14.2.
- Use genuine simulation output in the demo. Disclose precomputed TRIBE output in both the UI and this README when introduced. Never present test mocks as real results.
- Without TRIBE, finish with Gemini and show **Brain sim off**. Without brain data, show **No brain data**. Record the actual go/no-go result in TEAM.md.
- Document the implemented scoring/confidence rule here when FR-05 lands. Simulator agreement is not a demonstrated probability of real-world success.
- Do not claim that neural response predicts retention, virality, emotions or sales. Live A/B testing is the eventual validation.

Current TRIBE mode, scoring implementation and Condense integration: **not yet implemented or verified in this repository**.

## Attribution and eligibility

[TRIBE v2](https://github.com/facebookresearch/tribev2), by **Meta FAIR**, is the planned brain simulation component. Its code and [model weights](https://huggingface.co/facebook/tribev2) are published under [CC BY-NC 4.0](https://github.com/facebookresearch/tribev2/blob/main/LICENSE). The PRD frames its use as research for the hackathon; commercial rights and downstream model licensing remain to be resolved before commercialization. This attribution does not relicense Preflight or imply Meta endorsement.

The supplied PRD calls for Gemini + Condense, a public repository and a two-minute demo. Rules and the exact submission deadline still require platform confirmation. Repository visibility was **PRIVATE** at the 3 Oct 2026 documentation import; visibility has not been changed by this setup. Track these items in TEAM.md.
