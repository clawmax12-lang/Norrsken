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
