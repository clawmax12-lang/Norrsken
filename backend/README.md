# Preflight backend

## LLM and Condense

All Gemini calls go through `preflight.llm.GeminiClient` (structured JSON validated with Pydantic, one repair call, one retry of transient errors). Settings: `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`, the default in Google's docs on 2026-10-03), `CONDENSE_API_KEY`, `CONDENSE_BASE_URL` (default `https://api.condense.chat`), `CONDENSE_COMPRESSION_RATE` (default `0.2`), `CONDENSE_PROXY` (default `true`), `CONDENSE_UPSTREAM_URL` (default Gemini's OpenAI-compatible endpoint). Without `GEMINI_API_KEY` the client refuses to build (the UI should show "not configured"); without `CONDENSE_API_KEY` Gemini still works and the savings are exactly zero.

Settings are read from the environment before `.env`: a stale `GEMINI_API_KEY` exported in the shell (Conductor workspaces inject one) silently overrides the key in `.env`.

### Condense proxy (verified live on 2026-10-03)

With `CONDENSE_API_KEY` set, `CondenseProxyBackend` sends each generation to `POST {CONDENSE_BASE_URL}/openai/v1/chat/completions` with `X-Condense-Upstream-Url` pointing at Gemini's OpenAI-compatible endpoint. Text, PNG screenshots, MP4 video (as a data URI) and `response_format` JSON Schema all work through it with `gemini-3.8-flash`.

- Each project gets a stable `X-Condense-Session-Id` (uuid5 of the project id), so one run's requests are grouped in the Condense dashboard.
- Condense rewrites the user message: it merges all text parts without separators and moves every image or video after the text. We send the message pre-merged, with `[Attachment N: ...]` references in the text and the media in the same order, so nothing is lost in the rewrite. It also adds its own system message.
- Even so, the planner (many labelled screenshots plus a strict storyboard schema) needed one repair per run through the proxy and none directly, so `build_gemini_client(..., proxy=False)` builds the planner's client; the viewer panel and other calls go through the proxy. Share one `TokenLedger` across all clients.
- Any proxy failure (timeout, 4xx/5xx, malformed answer) and media over 20 MB go to Gemini directly and are logged without keys; Condense never stops a run.
- Large *text* marked `compressible` (for example a previous answer sent back for repair) is additionally compressed with `POST {CONDENSE_BASE_URL}/v1/compress`. Instructions and schemas are never marked compressible.

### How savings are measured

Condense returns no savings header or field, so we measure. For each proxied call, the original request is counted with Gemini's native `countTokens` (which matches Gemini's own prompt-token count for text and images) and compared with the prompt tokens Gemini reports for what Condense actually forwarded. `countTokens` overcounts video (2340 vs 1713 for a 15 s clip), so calls with video claim no saving. If the original cannot be counted, the call claims no saving. `TokenLedger` reports the totals as `TokenSavings`. Short one-shot prompts are passed through uncompressed by Condense, so expect single-digit percentages; a live planner-plus-panel run saved 1.3%. Condense's marketing numbers are not used.

The Gemini SDK is isolated in `preflight/llm/genai_backend.py` (`google-genai` 2.28.0, `client.aio.models.generate_content`, `count_tokens` and the Files API for media over 20 MB). A move to the Interactions API means one new `GeminiBackend` implementation.
