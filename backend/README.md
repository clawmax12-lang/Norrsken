# Preflight backend

## LLM and Condense

All Gemini calls go through `preflight.llm.GeminiClient` (structured JSON validated with Pydantic, one repair call, one retry of transient errors). Settings: `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`, the default in Google's docs on 2026-10-03), `CONDENSE_API_KEY`, `CONDENSE_BASE_URL` (default `https://api.condense.chat`), `CONDENSE_COMPRESSION_RATE` (default `0.2`). Without `GEMINI_API_KEY` the client refuses to build (the UI should show "not configured"); without `CONDENSE_API_KEY` Gemini still works and the savings are exactly zero.

**Gemini routing through Condense is UNVERIFIED with the vendor.** Condense documents proxy routes for Anthropic and OpenAI only: no Gemini route, nothing about image or video parts, and no usage field or header in any response. So we do not proxy Gemini. Instead:

- Large *text* context marked `compressible` (for example a previous model answer sent back for repair) is compressed with `POST {CONDENSE_BASE_URL}/v1/compress` and then sent to Gemini directly. Instructions, schemas, brief fields that copy must be grounded on, screenshots and video are never compressed.
- Any Condense failure (no key, timeout, 4xx/5xx, malformed answer) degrades to the original text and is logged; nothing is counted.
- Savings are measured by us: the text is counted before and after compression with Gemini's own `count_tokens`, and if the compressed text is not smaller the original is sent. Sent and output tokens come from Gemini's usage metadata. `TokenLedger` reports these as `TokenSavings`; zero compressions means zero savings. Because most prompts are short one-shot requests, expect small savings (possibly 0%). Condense's marketing numbers are not used.
- Not verified here: that Condense's `compression_rate` semantics match its docs example, that `/v1/compress` is entitled for our key, and that Gemini accepts the `$ref`-based JSON Schemas Pydantic generates (no API key was available in the build sandbox; the SDK is exercised against faked transports only).

Questions for the Condense team:

1. Is there a Gemini / Google route (for example `/google/v1beta/...`), or will they enable `X-Condense-Upstream-Url` for our key?
2. How are image, video and inline-data parts handled when proxied?
3. Is there a per-request savings field or header, or a dashboard API to read tokens removed?
4. Hackathon credits and an entitlement-enabled `ak_` key.

The Gemini SDK is isolated in `preflight/llm/genai_backend.py` (`google-genai` 2.28.0, `client.aio.models.generate_content`, `count_tokens` and the Files API for media over 20 MB). A move to the Interactions API means one new `GeminiBackend` implementation.
