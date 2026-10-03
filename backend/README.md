# Preflight backend

## How to run

Prerequisites: Python 3.12 with [uv](https://docs.astral.sh/uv/), ffmpeg and ffprobe, Node.js 22.18 or later and Chrome (or let Remotion download Chrome Headless Shell on first render).

```bash
cp .env.example .env                       # at the repo root; fill in GEMINI_API_KEY and CONDENSE_API_KEY
(cd workers/renderer && npm ci)            # once: the Remotion renderer
cd backend && uv sync && make run          # API on http://localhost:8000
```

`make run` serves `preflight.api.main:create_production_app`, which wires the real pipeline:

| Step | Component | Notes |
| --- | --- | --- |
| Plan (FR-02) | `GeminiPlanner` | Gemini through the Condense proxy. |
| Backgrounds (§9.2) | `TemplateBackdrops` | Template-only for now; the template draws its own backgrounds. |
| Compose and render (FR-03) | `TemplateComposer`, `RemotionRenderer` | Runs `node workers/renderer/render.mjs` per variant; 1080x1920, 30 fps, 15 s H.264. About 50-60 s per video, two at a time. |
| Simulate (FR-04) | `GeminiViewerPanel`, `TribeSimulator` | The panel goes through Condense. TRIBE runs only when `TRIBE_ENDPOINT` points at our worker (`workers/tribe`); otherwise the run completes with the panel only and the report says `brain_sim: false` ("Brain sim off"). |
| Score (FR-05) | `score_and_rank` | Deterministic; the rule is written into `ranking.json`. |
| Explain (FR-06) | `GeminiExplainer` | Moments, timestamps and scenes come from the deterministic `RuleBasedExplainer`; Gemini (through Condense) only rewords each one, and the rule-based text is kept if Gemini fails. |
| Sound (PRD §9.3) | `SoundStudio` | Narration (Gemini TTS), music and effects for the winner and runner-up, mastered and muxed with ffmpeg. Needs `ffmpeg` and `ffprobe` on `PATH`; without them the videos are exported silent. |

Each run gets its own `TokenLedger` and Condense session id, so `report.json`'s `token_savings` covers that run. Settings are read from `<repo>/.env` (then `./.env`); projects are stored in `<repo>/data/projects/` unless `DATA_DIR` is set. Other settings: `RENDERER_DIR`, `NODE_BINARY`, `RENDER_CONCURRENCY`, `PREFLIGHT_CHROME` (read by the renderer), `MAX_VARIANTS`, `STEP_TIMEOUT_S`, `STEP_RETRIES`, `CORS_ORIGINS`, and for sound `SOUND_ENABLED`, `NARRATION_ENABLED`, `TTS_MODEL`, `NARRATION_VOICE`, `FFMPEG_BINARY`, `FFPROBE_BINARY`.

A full live run (4 screenshots, 3 variants, Gemini panel, no TRIBE) took 2 min 36 s from `POST /run` to `DONE`.

### API

| Method and path | Purpose |
| --- | --- |
| `GET /api/health` | Liveness plus `runs`, `gemini`, `condense`, `brain_sim` flags so the UI can show "not configured" or "Brain sim off" before a run. |
| `POST /api/briefs` | Multipart brief: `product_name`, `one_liner`, `goal`, `audience`, optional `goal_note`, `brand_color`, 3-6 `screenshots` files, optional `logo`. Returns the `Brief` with its new `project_id`. |
| `POST /api/projects/{id}/run` | Starts (or resumes) the run in the background; safe to repeat. |
| `GET /api/projects/{id}` | `run.json` state plus the brief. |
| `GET /api/projects/{id}/log` | Server-sent events: one `activity` event per log line, then `end` with the final state. Supports `Last-Event-ID`. |
| `GET /api/projects/{id}/results` | Concepts, render records, simulation series and events, ranking and report (including `token_savings`), plus file URLs. |
| `GET /api/projects/{id}/files/{video,video-final,brain-activity,brain-groups}/{variant}` | The variant's tested silent MP4, its cut with sound (`video-final`, when sound was added; range requests supported) and TRIBE brain data. |
| `GET /api/projects/{id}/export/{winner.mp4,runner_up.mp4,report.json,launch_brief.md}` | The four FR-08 downloads. |

## LLM and Condense

All Gemini calls go through `preflight.llm.GeminiClient` (structured JSON validated with Pydantic, one repair call, one retry of transient errors). Settings: `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`, the default in Google's docs on 2026-10-03), `CONDENSE_API_KEY`, `CONDENSE_BASE_URL` (default `https://api.condense.chat`), `CONDENSE_COMPRESSION_RATE` (default `0.2`), `CONDENSE_PROXY` (default `true`), `CONDENSE_UPSTREAM_URL` (default Gemini's OpenAI-compatible endpoint). Without `GEMINI_API_KEY` the client refuses to build (the UI should show "not configured"); without `CONDENSE_API_KEY` Gemini still works and the savings are exactly zero.

Settings are read from the environment before `.env`: a stale `GEMINI_API_KEY` exported in the shell (Conductor workspaces inject one) silently overrides the key in `.env`.

### Condense proxy (verified live on 2026-10-03)

With `CONDENSE_API_KEY` set, `CondenseProxyBackend` sends each generation to `POST {CONDENSE_BASE_URL}/openai/v1/chat/completions` with `X-Condense-Upstream-Url` pointing at Gemini's OpenAI-compatible endpoint. Text, PNG screenshots, MP4 video (as a data URI) and `response_format` JSON Schema all work through it with `gemini-3.8-flash`.

- Each project gets a stable `X-Condense-Session-Id` (uuid5 of the project id), so one run's requests are grouped in the Condense dashboard.
- Condense rewrites the user message: it merges all text parts without separators and moves every image or video after the text. We send the message pre-merged, with `[Attachment N: ...]` references in the text and the media in the same order, so nothing is lost in the rewrite. It also adds its own system message.
- Every generation (planner, viewer panel, explanations) goes through the proxy. The planner's one repair per proxied run came from Gemini's scene lengths not summing to 15 s; code now scales them to exactly 15 s, and over-long panel labels are shortened at a word boundary, so neither costs a repair call. Only the free `countTokens` calls that measure the savings go to Gemini directly. All clients of a run share one `TokenLedger` (see `preflight/wiring.py`).
- Any proxy failure (timeout, 4xx/5xx, malformed answer) and media over 20 MB go to Gemini directly and are logged without keys; Condense never stops a run.
- Large *text* marked `compressible` (for example a previous answer sent back for repair) is additionally compressed with `POST {CONDENSE_BASE_URL}/v1/compress`. Instructions and schemas are never marked compressible.

### How savings are measured

Condense returns no savings header or field, so we measure. For each proxied call, the original request is counted with Gemini's native `countTokens` (which matches Gemini's own prompt-token count for text and images) and compared with the prompt tokens Gemini reports for what Condense actually forwarded. `countTokens` overcounts video (2340 vs 1713 for a 15 s clip), so calls with video claim no saving. If the original cannot be counted, the call claims no saving. `TokenLedger` reports the totals as `TokenSavings`. Short one-shot prompts are passed through uncompressed by Condense, so expect single-digit percentages; a full live run saved 1.5% over 14 proxied calls. Condense's marketing numbers are not used.

The Gemini SDK is isolated in `preflight/llm/genai_backend.py` (`google-genai` 2.28.0, `client.aio.models.generate_content`, `count_tokens` and the Files API for media over 20 MB). A move to the Interactions API means one new `GeminiBackend` implementation.

## Sound

After the report is written, `SoundStage` gives the ranked top two variants a soundtrack (`preflight.sound`):

- **Narration.** One Gemini text-to-speech call per distinct on-screen line (scene text, then the CTA), timed to its scene. Lines are trimmed, levelled, sped up at most 1.3x to fit their scene, or left out if they cannot fit. Results are cached under `sound/work/cache/`. A voice failure leaves music and effects only.
- **Music and effects.** Synthesized in numpy (`dsp.py`, `music.py`): a 120 BPM bed whose drop and outro follow the scene boundaries and CTA card (whole-second scenes land on beats), and effects chosen by each scene's transition style.
- **Mix and master.** Music ducks under speech; ffmpeg's two-pass `loudnorm` sets about -14 LUFS and the encoded file is measured again (true peak at or below -1 dBTP). The video stream is copied unchanged.
- **Outputs.** `videos/{id}.final.mp4` and `sound/{id}.json` (what was said, effects, loudness, tested vs. final hashes, TTS tokens). Export uses the sound cut when present; the pretest covers the silent render and the launch brief says so.

Narration bypasses Condense (a logged exception to FR-10; see PRD §9.3). Nothing in the sound path has been run against the live Gemini TTS API in this repository's tests: those use a fake backend over the real SDK. Verify with a real key before relying on it, including the model id (`TTS_MODEL`) and the voice (`NARRATION_VOICE`).
