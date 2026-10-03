// Allowlisted diagnostics only. Never forward SDK messages, URLs, keys or tokens.
export const LIVE_TOKEN_ERRORS = {
  not_configured: "Voice is not configured. Set GOOGLE_API_KEY in this deployment's server environment and redeploy.",
  rate_limited: "Too many Live sessions or quota exhausted. Wait a minute and retry.",
  auth_rejected: "Gemini rejected this deployment's server credentials. Check the Preview environment's key and API restrictions, then redeploy.",
  model_unavailable: "This deployment cannot access the configured Gemini Live model. Check the model and project access on the server.",
  provider_unavailable: "Gemini Live is unavailable. Check this deployment's server configuration and retry.",
} as const;

export function liveTokenFailure(error: unknown) {
  const status = error && typeof error === "object" && "status" in error ? error.status : undefined;
  const code = status === 401 || status === 403 ? "auth_rejected"
    : status === 404 ? "model_unavailable" : status === 429 ? "rate_limited" : "provider_unavailable";
  return { code, error: LIVE_TOKEN_ERRORS[code], status: status === 429 ? 429 : 502 };
}

export function liveTokenMessage(payload: { code?: unknown }, status: number) {
  // The response may come from a proxy. Do not blindly display arbitrary error text.
  if (typeof payload.code === "string" && Object.hasOwn(LIVE_TOKEN_ERRORS, payload.code)) {
    return LIVE_TOKEN_ERRORS[payload.code as keyof typeof LIVE_TOKEN_ERRORS];
  }
  return status === 503 ? LIVE_TOKEN_ERRORS.not_configured
    : status === 429 ? LIVE_TOKEN_ERRORS.rate_limited : LIVE_TOKEN_ERRORS.provider_unavailable;
}
