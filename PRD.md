# Preflight · Product Requirements Document

**Version:** 1.3 · **Date:** 3 Oct 2026 · **Status:** Hackathon build ({Tech: Europe} Agentic AI Hack, Norrsken Stockholm)

**Owner:** William (product) · **Tech owners:** see §14.3 and [TEAM.md](TEAM.md)

**Repository:** https://github.com/clawmax12-lang/Norrsken

**Built with (PRD plan):** Claude Opus 5.5 as the coding agent · Gemini · Condense · TRIBE v2 (Meta FAIR, research use)

> This is the team's canonical, editable product specification. It supersedes earlier brainstorming and advisor briefs. Imported from the complete, 20-page [Preflight PRD v1.1.pdf](docs/source/Preflight-PRD-v1.1.pdf). The original is preserved unchanged; see [source provenance](docs/source/README.md). Formatting and the repository URL have been normalized for Git. The claims, priorities, acceptance criteria, open questions and research caveats below are retained from the supplied PRD. Actual implementation progress lives in [TEAM.md](TEAM.md), not in these requirements.

**What changed in 1.1:** new §12 UI with the analysis intro (the "Preflight sequence") and the interactive 3D brain viewer; brain viewer and intro moved to P0 (conditional on TRIBE running); A/B compare mode added; repo and build info added; timeline and owners updated.

**What changed in 1.2:** FR-01 intake is now led by an interruptible, voice-native Preflight Director powered by Gemini Live, with visible transcripts, explicit folder permission and a complete text fallback. The Director can retrieve approved screenshots and challenge creative choices, but all claims remain source-backed and all TRIBE evidence must come from a completed simulation. Direct Gemini Live transport is the only exception to the Condense routing rule because no compatible Live WebSocket proxy is available in the adopted architecture; planning, viewer-panel and explanation calls remain routed through Condense.

**What changed in 1.3:** removed per-folder and per-screen approval from the Director workflow. Every screenshot attached to the current project is available to the Director for search and inspection immediately; the user can override its selections. Browser security still requires the user to attach local files, and the Director never receives access to arbitrary device files.

## 0. How to read this document

- **Humans:** read §1 to §7 (why, who, journey). Builders continue with §8 to §14.
- **AI coding agents:** read §15 (Rules for AI agents) first, then §8 (requirements) and §10 (architecture). Every requirement has an ID, a priority and acceptance criteria (AC). Build all P0 before touching any P1.
- **Labels:** `[FACT]` verified · `[ASSUMPTION]` not yet verified · `[DECISION]` decided by the team today.
- **Priorities:** P0 = must exist for the demo · P1 = do if P0 is done · P2 = after the hackathon.

## 1. TL;DR

Startups need a demo video for every launch, but agencies take weeks and nobody knows which version will actually work until after they have posted and paid for ads. Preflight's agent turns your product into several motion graphics demo videos, pretests them on simulated viewers (TRIBE v2 brain simulation plus a Gemini viewer panel), and hands you the winner, why it won, and the runner up for a live A/B test.

## 2. Working backwards

### 2.1 Press release (the day we launch)

**Preflight: launch videos that are tested before anyone sees them**

Startups launching a product today either pay an agency and wait weeks, or make a video themselves. Either way they only find out if it works after it is posted and the ad budget is spent.

Preflight changes that. Upload a few screenshots of your product, say what you want viewers to do, and in minutes Preflight's agent produces three motion graphics demo videos, each built on a different idea of what will make viewers act. It plays every version to simulated viewers, including a simulation of the human brain's response, and tells you which one to launch, why, and which one to A/B test against it.

> "I was about to pay for my app's launch video and had no way of knowing which style would work. I wanted to know before I paid, not after." (William, founder of tablehopp and Preflight)

### 2.2 Customer FAQ

- **What do I need?** 3 to 6 screenshots of your product, one sentence on what it does, your goal (for example sign ups), and who it is for.
- **How long does it take?** Target under 10 minutes for three tested videos.
- **Does it guarantee results?** No. It ranks versions by simulated viewer response so you only spend real money testing the strongest ones. Confirm with a live A/B test.
- **What is the brain view?** A research model (TRIBE v2 from Meta FAIR) that predicts the average human brain response to video, audio and language, second by second. It is one of several simulated viewers.
- **Will it make things up about my product?** No. Every word and screen in the video comes from what you provided.

### 2.3 Internal FAQ

- **Why generate videos at all?** `[DECISION]` Customers pay for a finished asset, not a report. Polishing a weak existing video does not fix it, so we generate from the product itself.
- **Why not only generate?** Generation is becoming a commodity. Knowing which version works is the scarce part. Generation plus pretest is the product.
- **TRIBE v2 is non commercial. How is this a business?** `[FACT]` TRIBE v2 is CC BY-NC 4.0. We use it for research and this hackathon. The commercial path is our own audience model trained on outcome data (simulated response paired with real A/B results).
- **What must be true for this company to exist?** Simulated pretesting must pick the real winner more often than chance and more often than an LLM alone. See §13 and the validation plan.

## 3. Problem

### 3.1 Problem statement

When a startup launches something, it needs a video that makes people understand the product and act. Today it cannot afford agency quality for every launch, and it has no way of knowing which version works before posting and paying. So it ships one video based on gut feeling and learns nothing for next time.

### 3.2 Evidence

| Claim | Status |
| --- | --- |
| tablehopp (William's app) launches 7 Oct and needs a launch video. William collected reference videos, most were rejected, and he was about to pay for production without knowing which style would work. | `[FACT]` (founder's own case) |
| Ad pretesting is an established paid category (for example Kantar, Neurons, System1 appear in comparisons). Companies pay to know before they spend. | `[FACT]` |
| Early stage startups need a demo video for most launches and cannot pay an agency every time. | `[ASSUMPTION]` |
| They would pay for a pretested video. | `[ASSUMPTION]` |
| Simulated viewer response correlates with real video performance. | `[ASSUMPTION]` critical, unproven |

### 3.3 Alternatives today

| Alternative | What it gives | What it lacks |
| --- | --- | --- |
| Agency or freelancer | High quality | Weeks, expensive, one version, untested |
| DIY screen recording tools | Fast, cheap | Looks amateur, untested |
| AI video generators | Many variants | No idea which one works |
| Ad testing platforms | Tests | No asset, built for larger brands and slower studies |
| Live A/B test on Meta or TikTok | Real data | Costs money and days per variant |

## 4. Users

**Primary persona: the launch week founder.** Founder or first marketer at a 1 to 20 person startup (app or SaaS). No motion designer. Launches on LinkedIn, X, Instagram, TikTok, often with a small paid boost. Success means sign ups or downloads from the launch.

**Secondary (later):** e-commerce marketers, small agencies producing for several clients.

**Anti personas (we do not design for them):** big brands with research departments, creators chasing entertainment virality, anyone who wants a guarantee.

**Job to be done:** "When I am about to launch, help me ship a demo video I am confident in, so the launch brings users and I do not waste the launch moment or ad money."

## 5. User journey

### 5.1 Today

| Stage | What they do | Pain |
| --- | --- | --- |
| 1. Trigger | Launch date is set | "We need a video" panic |
| 2. Find a style | Scroll reference videos | Most references feel wrong, hours lost |
| 3. Make it | Agency (weeks, cost) or DIY (amateur) | Time, money, quality |
| 4. Choose | Gut feeling, ask friends | No real signal |
| 5. Publish and boost | Pay for ads, wait days | Money spent before knowing |
| 6. Learn | Rarely | Next launch starts from zero |

### 5.2 With Preflight

| Stage | What happens | User sees |
| --- | --- | --- |
| 1. Trigger | "We launch Wednesday" | Opens Preflight |
| 2. Brief (2 min) | Uploads screenshots, one sentence, goal, audience | Simple form |
| 3. Agent at work (under 8 min) | Agent plans 3 hypotheses, renders 3 videos, runs simulated viewers | Live step log and previews |
| 4. Verdict | Winner, why, where others lose viewers | Preflight sequence, then leaderboard, synced curves, brain view |
| 5. Export | Winner plus runner up plus launch brief | Downloads |
| 6. Launch and learn (V1) | Live A/B results flow back | Model gets better per launch |

### 5.3 Moments of truth

1. **The videos must look good enough to post.** If not, the test is meaningless. Quality of the template matters more than the number of variants.
2. **The verdict must feel credible.** Always show why, with timestamps, never a bare score.
3. **It must be fast.** If it takes longer than making a video yourself, it fails.

Journey rule: the user never sees "TRIBE output". They see: which video, why, what next.

## 6. Product principles

1. **Decision over data.** Every screen leads to "launch this one".
2. **Show the why.** Every ranking comes with timestamped reasons.
3. **Honest uncertainty.** Show a confidence label. Never say "will go viral" or "predicts sales".
4. **Truth in the video.** Only use claims and screens the customer provided. No invented features, numbers, logos or testimonials.
5. **Fast beats perfect.** Under 10 minutes end to end.
6. **Model agnostic.** Every viewer simulator sits behind one interface. TRIBE is one viewer, not the product.

## 7. Scope

### 7.1 Hackathon MVP (today)

Brief → agent plans 3 variants → renders 3 motion graphics videos (one template) → pretest with TRIBE v2 and Gemini panel, shown through the analysis intro and the interactive 3D brain viewer → ranking with reasons → export. P1: A/B compare and difference view, one iteration on the winner.

### 7.2 V1 (only after validation, see §13)

Ad account connection, launch live A/B tests, ingest real results, brand kit, more templates, backtest mode.

### 7.3 Moonshot

A simulated audience for all content: every launch video, ad, trailer and landing page is tested on simulated people before it meets real ones. Every customer's real results train our own audience model. AI made making content free; Preflight owns knowing what works.

### 7.4 Non goals (today)

- Editing customers' existing videos `[DECISION]`
- Text to video generative models (no generated footage, only motion graphics from real screens)
- Accounts, auth, payments, teams
- Publishing to social platforms
- More than one template family
- Mobile layout, multi language UI

## 8. Functional requirements

### P0

#### FR-01 Brief intake

**Inputs:** product name; one line description (max 140 chars); 3 to 6 screenshots (PNG or JPG); goal (sign ups / downloads / understand the product / purchase, plus optional free text); audience (free text); optional brand color and logo.

**Experience:** the default intake is an interruptible, voice-native conversation with the Preflight Director. The Director displays input and output transcripts, updates the visible brief as fields are confirmed, can search and inspect every screenshot attached to the project without further approval, and gives concise creative pushback grounded in the brief or visible assets. A complete typed fallback remains available. Starting generation requires an explicit spoken or clicked confirmation.

**AC:** voice and typed paths validate the same required fields; interrupting the Director stops queued playback and continues the same session; every confirmed field shows its source; every project screenshot is searchable and inspectable by the Director without a second permission step; arbitrary device files remain inaccessible; brief saved as `brief.json` matching schema §10.3; a fixture brief for tablehopp exists in `/fixtures`.

#### FR-02 Creative plan

The agent produces exactly 3 concepts. Each concept has: a hypothesis (for example problem first, outcome first, product first), hook text (max 8 words), 4 to 6 scenes, screenshot per scene, on screen text per scene, CTA, duration 15 s.

**AC:** output validates against `CreativeConcept` schema; the 3 hypotheses are different; every text claim can be traced to the brief (agent stores the source field for each claim).

#### FR-03 Render

Each concept renders to MP4, 1080x1920, 15 s, 30 fps, using one motion graphics template driven by the concept data.

**AC:** 3 MP4s render with no manual step; render time logged per video; a failed render is retried once, then marked failed without stopping the run.

#### FR-04 Pretest (simulate)

Every variant runs through the simulators: TRIBE v2 (brain sim) and Gemini viewer panel (3 personas derived from the audience field).

**AC:** one `SimulationResult` per variant per simulator, matching schema; TRIBE results in the demo are real model output (live or precomputed, and if precomputed, disclosed in UI and README); if TRIBE is unavailable the run still completes with Gemini only and the UI shows "Brain sim off".

#### FR-05 Score and rank

A goal aligned score per variant, a ranking, and a confidence label (High if simulators agree on the winner, Low if they disagree).

**AC:** same inputs give the same ranking; confidence rule documented in code and README.

#### FR-06 Explain

For each variant, 2 to 4 reasons, each tied to a timestamp and to what is on screen at that moment (hold moments and drop moments).

**AC:** every reason has a timestamp inside the video length and references a real scene from the concept.

#### FR-07 Results UI

Leaderboard; video player with per second curves synced to playback; verdict card ("Launch C. A/B test it against A.").

**AC:** curves follow scrubbing; verdict visible without scrolling on a 1440 px wide screen.

#### FR-08 Export

Download winner MP4, runner up MP4, `report.json`, and a Markdown launch brief (which to post, which to A/B test, what to change next time).

**AC:** all four files download and open.

#### FR-09 Agent activity log

Visible step by step log: plan, render, simulate, score, explain, each with status and duration.

**AC:** log updates live during a run and is saved with the project.

#### FR-10 Partner tech

Gemini for the live Director, planning, viewer panel and explanations. Planning, viewer-panel and explanation calls go through Condense. Gemini Live uses a direct, ephemeral-token WebSocket because no compatible Condense full-duplex Live proxy has been demonstrated for FR-01; this exception does not apply to non-Live calls. Show Condense token savings in the UI.

**AC:** savings number visible on the results screen. This is required for eligibility (at least two partner technologies).

#### FR-12 Interactive 3D brain viewer

**P0 if TRIBE passes the 12:30 go/no-go, otherwise dropped.** Brain mesh (fsaverage5) inside a head silhouette, with predicted activity synced to video playback. Controls and behaviour as specified in §12.3.

**AC:** activity comes from real TRIBE results only; with no data the viewer shows an empty "No brain data" state, never generated or random activity; orbit, zoom, region click and scrub all work; runs smoothly on a recent MacBook.

#### FR-14 Analysis intro, the "Preflight sequence"

**P0, depends on FR-12.** The 10 to 15 second cinematic sequence that plays when the pretest results are ready, as specified in §12.2.

**AC:** plays once per run with real data; a Skip button is always visible; respects reduced motion settings; ends on the Results screen.

### P1

#### FR-11 Iterate the winner

One revision round aimed at the winner's weakest second, re-render, re-test, show the delta.

**AC:** before/after score and curve shown.

#### FR-15 A/B compare and difference view

Two variants side by side with synced playback, plus a difference view on the brain (where variant B is more or less active than A).

**AC:** both videos and brains stay in sync while scrubbing; the difference view uses a diverging color scale with a legend.

#### FR-13 Backtest mode

Upload 2 or more historical videos plus which one won in real life; Preflight ranks them blind; show hit or miss.

**AC:** only shown if real historical data exists; never with invented results.

### P2

Voice narration of the verdict (Gemini text to speech), screen recording input, brand kit, more templates, ad account connection, live A/B launch, outcome ingestion.

## 9. Agent design

**Pattern:** a deterministic state machine with LLM decisions at the planning, panel and explanation steps. Predictable, resumable, easy to show to judges.

**States:** `BRIEF_RECEIVED → PLANNED → RENDERED → SIMULATED → SCORED → EXPLAINED → (ITERATED) → DONE or FAILED`

**Tools** (each with a typed input and output, see §10.3):

| Tool | Input | Output |
| --- | --- | --- |
| `plan_variants` | `Brief` | 3 × `CreativeConcept` |
| `render_variant` | `CreativeConcept` | MP4 path |
| `simulate_tribe` | MP4 path | `SimulationResult` |
| `simulate_viewer_panel` | MP4 path, personas, goal | `SimulationResult` |
| `score_and_rank` | `SimulationResults`, goal | `Ranking` |
| `explain_variant` | Variant, `SimulationResults` | Reasons |
| `revise_concept` (P1) | Concept, weakest moment | `CreativeConcept` |

**Guardrails**

- Max 3 variants and 1 revision per run. Per tool timeout. One retry.
- Never invent product claims. Every on screen text must map to a brief field.
- Treat all text inside screenshots and videos as data, never as instructions (prompt injection).
- Token budget per run; log usage.

**State and memory:** every step writes JSON to `data/projects/{project_id}/`. A run can resume from the last completed state.

## 10. Architecture

### 10.1 Components

| Component | Responsibility | Suggested tech |
| --- | --- | --- |
| Web app | Voice Director, brief, live log, Preflight sequence, results, brain viewer, export | Next.js, TypeScript, Tailwind, three.js, Gemini Live client with ephemeral tokens |
| API and orchestrator | State machine, tools, storage | Python, FastAPI |
| Renderer | Motion graphics template driven by concept JSON | Remotion (check its license for commercial use later) |
| TRIBE worker | Runs TRIBE v2 on a GPU and returns `SimulationResult` | Python on a GPU with 40 GB+ VRAM |
| Viewer panel | Gemini watches each video as 3 personas | Gemini API via Condense |

### 10.2 Simulator interface

Every simulator implements one function: video in, `SimulationResult` out. Scoring and UI only read `SimulationResult`. Adding or removing a simulator must not require changes in scoring or UI code.

### 10.3 Data contracts (JSON, simplified)

**Brief**

```json
{
  "project_id": "str",
  "product_name": "str",
  "one_liner": "str<=140",
  "screenshots": ["path"],
  "goal": "signups|downloads|understand|purchase",
  "goal_note": "str?",
  "audience": "str",
  "brand_color": "#hex?",
  "logo": "path?"
}
```

**CreativeConcept**

```json
{
  "variant_id": "A|B|C",
  "hypothesis": "str",
  "hook": "str<=8 words",
  "scenes": [
    {
      "t_start": 0,
      "t_end": 3,
      "screenshot": "path",
      "text": "str",
      "source_field": "brief field this text comes from"
    }
  ],
  "cta": "str",
  "duration_s": 15
}
```

**SimulationResult**

```json
{
  "variant_id": "A",
  "simulator": "tribe_v2|gemini_panel",
  "version": "str",
  "hz": 1,
  "series": { "name": [0.0] },
  "events": [{ "t": 3, "type": "hold|drop", "label": "str" }],
  "precomputed": false,
  "meta": {}
}
```

**Ranking**

```json
{
  "order": ["C", "A", "B"],
  "scores": { "A": 0.0 },
  "confidence": "high|low",
  "rule": "str"
}
```

**Report**

```json
{
  "winner": "C",
  "runner_up": "A",
  "reasons": { "C": [{ "t": 2, "text": "str" }] },
  "next_time": ["str"],
  "token_savings": { "tokens_saved": 0, "percent": 0 }
}
```

### 10.4 Secrets and repo

- Keys in environment variables only (`GEMINI_API_KEY`, `CONDENSE_API_KEY`, `TRIBE_ENDPOINT`). The server may exchange `GEMINI_API_KEY` for a short-lived, one-use Live token; the permanent key never reaches browser code. Commit `.env.example`, never `.env`.
- No model weights in the repo. README credits TRIBE v2 (Meta FAIR) and states its CC BY-NC license.
- Repo must be public (hackathon rule). URL: https://github.com/clawmax12-lang/Norrsken.
- The README states the build stack, including that the code was written with Claude Opus 5.5 as the coding agent.

## 11. TRIBE v2: what it is and how we use it

**Facts (from third party write ups, verify on the Hugging Face model card in hour 1)**

- Predicts group average brain response to video, audio and text.
- Output at 1 Hz on the fsaverage5 cortical surface (about 20,484 vertices).
- Needs roughly 28 to 32 GB VRAM. A T4 is not enough.
- License CC BY-NC 4.0: research and non commercial use.

**How we use it**

- Run each variant once and store the result. Playback in the UI is synced to the stored result, so it looks live.
- Reduce vertices to a few region groups (for example visual, auditory, language) using a standard atlas, and show those as curves.

**Rules**

- No emotion, desire or buying intent read from brain regions. Region cards describe what a region is known for, nothing more.
- Never claim TRIBE predicts retention, virality or sales.
- If TRIBE does not run by 12:30, it is dropped from live runs. Never show fake brain data.

## 12. UI and the analysis intro

### 12.1 Design direction

- **Feeling:** a lab instrument with a cinematic moment. Think heads up display from a film, but every number on screen is real and readable.
- **Reference:** the TRIBE v2 demo viewer (screenshot shared in the team chat): black background, a dark head silhouette in profile, a light gray brain mesh, activity in a red to yellow heat scale, rounded segmented controls at the bottom. We match that quality bar. We do not copy Meta branding.
- **Rule:** the cinema is the wrapper, the decision is the content. Every screen still ends in "launch this one".

### 12.2 The analysis intro: the "Preflight sequence" (FR-14)

Plays once when pretest results are ready. 10 to 15 seconds. Real TRIBE data only.

| Beat | Time | What happens on screen |
| --- | --- | --- |
| 1. Black out | 0 to 1.5 s | Screen dims to black. The variant video shrinks into a floating frame on the left. Small mono text: "Running simulated viewers · Variant A". |
| 2. Assemble | 1.5 to 4 s | Head silhouette fades in. The brain builds from a thin wireframe into the shaded gray mesh while slowly rotating to a side view. |
| 3. Watch | 4 to 9 s | The video plays in its frame. The brain lights up second by second with the predicted response (interpolated between the 1 Hz frames so it moves smoothly). Thin HUD lines connect three live meters (Visual, Auditory, Language) to their regions. A timeline under everything shows the scrubber moving. |
| 4. Lock on | 9 to 12 s | At the strongest moment, the camera pushes in on the most active region. An info card slides in: region group, what it is known for (one line), timestamp, and what is on screen at that second (for example "0:03 · product screen appears"). |
| 5. Hand over | 12 to 15 s | Camera pulls back. The brain shrinks into the center panel of the Results screen and the leaderboard slides in from the left. |

**Always:** a Skip button top right; reduced motion setting replaces the camera moves with fades; a small "precomputed" label if the TRIBE results were computed ahead of time.

### 12.3 Interactive brain viewer (FR-12)

Bottom controls, as segmented pills like the reference:

| Control | Options | Behaviour |
| --- | --- | --- |
| Variant | A · B · C | Switch which variant's response is shown. This replaces the reference's "True / Predicted", because we only have predicted data and our job is comparing variants. |
| Surface | Normal · Inflated | Inflated unfolds the brain so activity hidden in folds becomes visible. |
| View | Closed · Open | Open splits the two hemispheres apart to show the inner surfaces. |
| Mode (P1) | Activity · Difference | Difference shows where the selected variant is more (warm) or less (cool) active than variant A. |

**Interaction**

- Drag to orbit, scroll to zoom, double click to reset the camera.
- Click a region to open its info card (same content rules as §12.5).
- Scrubbing the timeline moves video, brain and curves together.
- Keyboard: space play or pause, left and right arrows step one second, F fullscreen.

**Fullscreen mode:** brain centered and large, video as a small floating frame, controls at the bottom, info cards on the right. This is the mode for the demo video and the stage.

### 12.4 Screens

1. **Brief:** voice-native Director with live captions, a visible structured brief, a project-wide asset shelf and a typed fallback. The user explicitly says or clicks "Run Preflight" after the required fields validate.
2. **Agent at work:** live step log, three video cards filling in as they render, then simulation progress per variant.
3. **Preflight sequence:** the intro above.
4. **Results:** leaderboard left; center stage with video, brain viewer and synced curves; verdict card and timestamped reasons right; token savings from Condense in the footer.
5. **Compare (P1):** two variants side by side, synced, with the difference view.
6. **Export:** four downloads and the launch brief preview.

### 12.5 Info card rules

- Region names come from a standard atlas, grouped into a few groups (for example visual, auditory, language).
- "Known for" text comes from a fixed, hand checked list in the repo, not from free LLM text.
- What is on screen comes from the concept's scene data at that timestamp.
- Never emotion, desire, attention guarantees or buying intent.

### 12.6 Visual tokens

- Background near black (`#0A0A0A`). Panels dark gray (`#151515`) with 1 px borders (`#2A2A2A`).
- Brain base light gray. Activity heat scale dark red → orange → yellow, with a threshold so low activity stays gray (like the reference).
- Difference view: diverging scale, warm for more, cool for less, legend always visible.
- Text white and gray. Timestamps and HUD labels in a monospace font. One accent color for the winner badge.
- Segmented controls: rounded pills, dark gray background, active option filled lighter.

### 12.7 Performance

- Target smooth playback on a recent MacBook. fsaverage5 is about 10,000 vertices per hemisphere, which is light for three.js.
- Preload all variants' brain data before the intro starts. First paint of Results under 2 seconds after the intro.

### 12.8 Words

**We use:** simulated viewers, brain sim, pretest, winner, why, launch brief.

**We never use:** "TRIBE output", "will go viral", "predicts sales", "reads emotions", "mind reading".

## 13. Metrics and validation

**Hackathon success**

- All P0 acceptance criteria pass.
- Full run with 3 variants in under 10 minutes.
- 2 minute demo video recorded with the real product.
- Public repo with a README that lets someone run it.

**Product metrics (after validation)**

- Time to verdict.
- Share of runs that end in an export.
- Backtest hit rate: how often Preflight picks the real winner of historical A/B tests, compared with 50% (chance) and with Gemini alone. This is the number the company lives or dies on.
- Live agreement rate: how often the pretest winner also wins the live A/B test.
- Paying customers.

**Validation plan (logged, not started until tablehopp has a paying customer)** Collect 20 to 50 historical A/B tests with known winners from 5 small companies, run backtest mode, and compare the hit rate against chance and Gemini alone.

## 14. Hackathon execution

### 14.1 Rules (from the opening talk; verify on the platform)

- Submit by 19:00 (heard as "nineteen past seven", check the platform).
- Public GitHub repo, code written today.
- 2 minute demo video: you using the product and explaining it. No AI style presentation.
- Use at least 2 of the 3 partner technologies. Our plan: Gemini and Condense. Ask Metrix if they have GPUs.
- Team of 1 to 5, everyone registered on the platform and in the team.
- Judging: 50% technical, 30% creativity, 20% real problem. Top 5 go to a 5 minute live final.

### 14.2 Timeline (from 12:00)

| Time | Milestone |
| --- | --- |
| 12:00 | Idea locked. Owners assigned. Repo public. Team on platform. Gemini key. Condense form. Brain viewer work starts in parallel (mesh, controls, empty state, no data needed yet). |
| 12:30 | Go/no-go: TRIBE runs on one clip; template renders one video. |
| 14:00 | FR-01 to FR-03: brief, plan, 3 rendered videos. Brain viewer renders the mesh with all controls. |
| 15:30 | FR-04 to FR-06: simulate, score, explain. First real TRIBE data shown in the brain viewer. |
| 16:30 | FR-07 to FR-10: results UI, export, log, Condense. |
| 17:15 | FR-14 Preflight sequence. Then P1: compare view, iterate winner. |
| 17:45 | Code freeze. |
| 18:00 to 18:40 | Record the 2 minute video (3 takes), finish README. |
| 18:45 | Submit. |

**Cut order if late:** iteration first, then compare view, then the camera moves in the intro (keep fades). If TRIBE fails at 12:30, the brain viewer and intro are dropped. Never cut brief → 3 videos → pretest → winner.

### 14.3 Owners (fill in now)

The source PRD leaves technical owners blank. Assign and maintain the live assignments in [TEAM.md](TEAM.md); these areas come from the PRD.

| Area | Owner |
| --- | --- |
| Template and renderer (FR-03) | Unassigned — see TEAM.md |
| TRIBE worker (FR-04) | Unassigned — see TEAM.md |
| Agent, Gemini, Condense (FR-02, 05, 06, 10) | Unassigned — see TEAM.md |
| Web app, results and export (FR-07, 08, 09) | Unassigned — see TEAM.md |
| Brain viewer and Preflight sequence (FR-12, 14, 15) | Unassigned — see TEAM.md |
| Demo video and pitch | William |

### 14.4 Two minute demo script

- **0:00** "I'm launching my app tablehopp on Wednesday. I need a launch video and I had no idea which version would work." Show the brief with real tablehopp screenshots.
- **0:15** Run. The agent plans three hypotheses and renders three videos (sped up).
- **0:40** The Preflight sequence plays: the brain assembles, lights up with the video, locks on the strongest moment. Then the leaderboard.
- **1:20** Why the winner wins, with timestamps. Iteration delta if built.
- **1:45** Export. "This is the video we launch on Wednesday." Mention Gemini, Condense, and TRIBE as one of the simulated viewers.

### 14.5 Five minute final (if top 5)

Problem (40 s) → live demo (2 min 30) → how it works, the agent and the simulator interface (50 s) → moonshot (30 s) → close: "AI made making videos free. Knowing which one works is the new bottleneck."

### 14.6 Judge Q&A

- **Isn't this a TRIBE wrapper?** TRIBE is one of the simulated viewers behind a common interface. The product is the agent that plans, makes, tests and decides. Turn the brain sim off and it still works.
- **Does it predict sales?** No. It pretests so you only spend real money on the strongest versions. Our first proof point after today is the backtest against real historical A/B results.
- **TRIBE is non commercial?** Correct. It is research use today. The commercial path is our own model trained on simulated response paired with real outcomes.
- **Why would someone pay?** Companies already pay for ad pretesting. We do it for small teams in minutes, and we deliver the finished video.
- **What stops Meta?** Meta has the outcomes but sells the testing. A neutral pretest that saves spend is not their incentive. This is our reasoning, not a proven fact.

## 15. Rules for AI coding agents

1. Read §15, then §8, §9, §10, §12. Build in requirement ID order. No P1 until every P0 acceptance criterion passes.
2. Never mock TRIBE or simulation output in the demo path. Mocks are allowed only in tests and must show a visible "MOCK" banner if rendered in the UI.
3. Never invent product claims, numbers, logos or testimonials in generated videos. Every on screen text needs a `source_field`.
4. Keep simulators behind the interface in §10.2. Adding a simulator must not change scoring or UI code.
5. Secrets only in environment variables. No model weights in the repo.
6. Small, runnable commits. Keep the README "How to run" section correct after every change.
7. Definition of done: acceptance criteria pass, the app runs from a clean clone using README steps, and there are no console errors on the demo path.
8. When unsure, choose the simpler option and write the choice in the decision log (§16).
9. The brain viewer may be built before data exists, but must then show the "No brain data" empty state. Never fill it with random or generated activity.
10. Primary coding agent for this repo: Claude Opus 5.5. Keep this PRD in the repo root as `PRD.md` and update the decision log when a requirement changes.

## 16. Decision log

Entries below are retained from the supplied PRD. Append new decisions with their date, rationale and affected requirement IDs. Requirement changes must also update the relevant section and version/change notes in this document.

| Date | Decision | Why |
| --- | --- | --- |
| 3 Oct | B2B: startups and companies, not creators | Companies have money metrics and already pay to pretest |
| 3 Oct | Output is generated motion graphics product demos | Customers pay for the asset; polishing a weak existing video does not fix it |
| 3 Oct | We do not edit customers' existing videos | Same reason |
| 3 Oct | TRIBE v2 is used for analysis inside the pretest, as one of at least two simulators | Strong signal, but research only and must not be the product |
| 3 Oct | Pretest selects, live A/B confirms | Honest about what simulation can and cannot prove |
| 3 Oct | Rejected: creator focus, AI editing of base videos, chief of staff agent | Weaker money metric, does not fix weak content, off track |
| 3 Oct, 12:00 | The interactive 3D brain viewer and the analysis intro are part of the core demo (P0 if TRIBE runs) | Strongest creativity moment (30% of judging); makes the pretest visible |
| 3 Oct, 12:00 | Variant toggle replaces "True / Predicted" from the reference viewer | We only have predicted data; our job is comparing variants |
| 3 Oct, 2026 | Make the Preflight Director the default FR-01 intake, using Gemini Live for interruption-capable voice and typed input as a full fallback | The founder should ideate the launch video with an opinionated creative director that can pull approved product screens into view, rather than complete a static form |
| 3 Oct, 2026 | Permit direct Gemini Live WebSocket calls authenticated by server-minted ephemeral tokens; keep all non-Live planning, panel and explanation calls through Condense | Full-duplex audio and barge-in require Gemini Live transport, while the permanent API key must remain server-side and Condense eligibility remains required for the existing LLM stages |
| 3 Oct, 2026 | Give the Director immediate access to every screenshot attached to the project; remove per-folder and per-screen approval UI | The Director is the creative operator for the project and must be able to search, inspect and select screens fluidly; browser sandboxing still prevents undisclosed access to device files |

## 17. Open questions

- Public repo URL to paste into the header and §10.4. **Repository import update:** URL filled in as https://github.com/clawmax12-lang/Norrsken; visibility was PRIVATE when checked on 3 Oct 2026. Public visibility remains outstanding; see TEAM.md.
- Exact submission time (19:00 or 19:19).
- GPU source for TRIBE (sponsors, Metrix, Colab, cloud).
- Template style. Reference: modern SaaS launch videos (for example the Lovable 2.0 launch video).
- Lunch time (unclear in the opening talk).

## 18. Glossary

- **Pretest:** testing video variants on simulated viewers before spending on real ads.
- **Simulated viewer:** any model that predicts how people respond to a video (TRIBE v2, Gemini panel).
- **Brain sim:** TRIBE v2's predicted average brain response.
- **Preflight sequence:** the 10 to 15 second analysis intro where the brain watches the video.
- **Launch brief:** exported Markdown with which video to post, which to A/B test, and what to change next time.
- **Backtest:** running Preflight on historical A/B tests with known winners to measure its hit rate.
