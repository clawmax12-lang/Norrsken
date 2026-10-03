# Preflight

Launch videos that are tested before anyone sees them.

Preflight turns a product brief and 3–6 screenshots into three 15-second motion graphics videos, pretests them with simulated viewers, and exports a recommended winner, a runner up and a launch brief. The first customer is a founder launching an app or SaaS product. E-commerce is a later audience.

**Current approved specification: [PRD v1.2](PRD.md).** It supersedes earlier brainstorming, including editing an existing customer video. This repository is the shared reference for the hackathon team and its coding agents.

## Start here

| Document | Purpose |
| --- | --- |
| [PRD.md](PRD.md) | Product scope, FR-01–FR-15, acceptance criteria, architecture, UI, timeline and decision log. The source of truth for what to build. |
| [TEAM.md](TEAM.md) | Owners, task status, integration evidence, open blockers and the shared Git/Conductor workflow. |
| [AGENTS.md](AGENTS.md) | Instructions every coding agent must follow. Claude loads these through [CLAUDE.md](CLAUDE.md). |
| [Original PDF](docs/source/Preflight-PRD-v1.1.pdf) | Unchanged, 20-page source supplied by the product owner. [Provenance and checksum](docs/source/README.md). |

Humans: start with PRD §1–§7. Builders: also read §8–§14. Agents: read AGENTS.md and PRD §15, §8, §9, §10 and §12 before implementing.

## How to run

The implemented vertical slice is the FR-01 voice-native Preflight Director: interruptible Gemini Live audio, transcripts, typed fallback, a permission-scoped local asset shelf, a six-scene draft storyboard, a visible decision thread and persisted `brief.json`. Planning, rendering, simulation, scoring and export are not implemented yet.

```bash
git clone https://github.com/clawmax12-lang/Norrsken.git
cd Norrsken
cp .env.example .env.local
npm install
npm run dev
```

Use Node.js 20.9 or newer. Set `GEMINI_API_KEY` in `.env.local` to an AI Studio key with access to `gemini-3.8-live`, then open `http://localhost:3000` in current desktop Chrome. Click **Start Director** once to grant microphone permission. **Choose folder** grants read access to one folder through the browser; Preflight indexes at most 100 PNG/JPG filenames locally and uploads only the 3–6 screens selected when **Run Preflight** is clicked.

The permanent key is read only by `/api/live-token`, which exchanges it for a one-use, short-lived token. It must never be named `NEXT_PUBLIC_GEMINI_API_KEY`, placed in client code or committed. The temporary hackathon account and its project may be deleted after the event, so replace the key for any later deployment.

Verification commands:

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm audit --omit=dev
```

## Build stack

The FR-01 slice uses Next.js 16, React 19, TypeScript, Zod and `@google/genai`. `gemini-3.8-live` provides low-latency native audio, automatic voice activity detection, barge-in, transcripts and function calls; the Director uses the firm `Kore` voice. A Next.js server route mints ephemeral Live tokens, while Live audio flows directly between the browser and Gemini. Later orchestration remains planned for Python/FastAPI, rendering for Remotion and the TRIBE v2 worker for a GPU environment.

The direct Gemini Live WebSocket is the narrow PRD v1.2 exception to Condense routing because the required full-duplex transport is not available through the adopted Condense path. Planning, viewer-panel and explanation calls must still go through Condense and report real token savings when implemented.

The PRD designates **Claude Opus 5.5** as the primary coding agent. This is a build plan, not a claim that the application has already been implemented with it. This documentation bootstrap was prepared with Codex from the supplied PDF.

Environment variable names from PRD §10.4: `GEMINI_API_KEY`, `CONDENSE_API_KEY`, `TRIBE_ENDPOINT`. Only `GEMINI_API_KEY` is consumed by the current slice. `.env.example` contains placeholders; `.env*` files remain ignored except for that example.

## Demo and research honesty

- Complete P0 before P1. FR-12 and FR-14 are conditional on the TRIBE go/no-go in PRD §14.2.
- Use genuine simulation output in the demo. Disclose precomputed TRIBE output in both the UI and this README when introduced. Never present test mocks as real results.
- Without TRIBE, finish with Gemini and show **Brain sim off**. Without brain data, show **No brain data**. Record the actual go/no-go result in TEAM.md.
- Document the implemented scoring/confidence rule here when FR-05 lands. Simulator agreement is not a demonstrated probability of real-world success.
- Do not claim that neural response predicts retention, virality, emotions or sales. Live A/B testing is the eventual validation.

Current TRIBE mode, scoring implementation and Condense integration: **not yet implemented or verified in this repository**. The Director UI labels its intake advice **Creative rationale · no simulation yet** and cannot call TRIBE. With no configured `GEMINI_API_KEY`, typed intake and folder selection still work, while voice shows a configuration error instead of fake output.

## Attribution and eligibility

[TRIBE v2](https://github.com/facebookresearch/tribev2), by **Meta FAIR**, is the planned brain simulation component. Its code and [model weights](https://huggingface.co/facebook/tribev2) are published under [CC BY-NC 4.0](https://github.com/facebookresearch/tribev2/blob/main/LICENSE). The PRD frames its use as research for the hackathon; commercial rights and downstream model licensing remain to be resolved before commercialization. This attribution does not relicense Preflight or imply Meta endorsement.

The supplied PRD calls for Gemini + Condense, a public repository and a two-minute demo. Rules and the exact submission deadline still require platform confirmation. Repository visibility was **PRIVATE** at the 3 Oct 2026 documentation import; visibility has not been changed by this setup. Track these items in TEAM.md.
