/** Normalize API/provider failures into a string the canvas can render. */

export function publicErrorMessage(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.trim()) return value;
  if (value && typeof value === "object") {
    const record = value as { message?: unknown; error?: unknown };
    if (typeof record.message === "string" && record.message.trim()) return record.message;
    if (typeof record.error === "string" && record.error.trim()) return record.error;
    if (record.error && typeof record.error === "object") {
      const nested = (record.error as { message?: unknown }).message;
      if (typeof nested === "string" && nested.trim()) return nested;
    }
  }
  return fallback;
}

export const SERVER_UNREACHABLE =
  "The Preflight server did not answer (it may be restarting). Nothing was started; try again in a minute.";

/**
 * The JSON body of ``response``. A non-JSON body (a proxy or tunnel error page) becomes
 * ``{ error }`` with a readable message instead of the browser's parse error.
 */
export async function readJson(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  try {
    const parsed: unknown = JSON.parse(text);
    if (parsed && typeof parsed === "object") return parsed as Record<string, unknown>;
  } catch {
    // fall through
  }
  return { error: SERVER_UNREACHABLE };
}
