import type { BriefDraft } from "@/lib/brief";
import type { SourceField, VariantId } from "@/lib/canvas-draft";

export type TypedBriefField = "product_name" | "one_liner" | "audience" | "goal";

export type TypedCommand =
  | { kind: "brief"; field: TypedBriefField; value: string }
  | { kind: "select"; variant: VariantId; scene: number }
  | { kind: "use-copy"; field: SourceField }
  | { kind: "move"; from: number; to: number }
  | { kind: "run" };

const copySourceByPhrase: Record<string, SourceField> = {
  "product name": "product_name",
  description: "one_liner",
  goal: "goal",
  "goal detail": "goal_note",
  audience: "audience",
};

const briefPatterns: Array<[TypedBriefField, RegExp]> = [
  ["product_name", /^(?:product|product name)\s*(?:is|to|:)\s*(.+)$/i],
  ["one_liner", /^(?:description|one[- ]?liner)\s*(?:is|to|:)\s*(.+)$/i],
  ["audience", /^audience\s*(?:is|to|:)\s*(.+)$/i],
  ["goal", /^goal\s*(?:is|to|:)\s*(.+)$/i],
];

export function normalizeGoal(value: string): BriefDraft["goal"] | null {
  const normalized = value.toLowerCase().replace(/[\s_-]+/g, "");
  if (normalized.includes("signup")) return "signups";
  if (normalized.includes("download")) return "downloads";
  if (normalized.includes("understand") || normalized.includes("awareness")) return "understand";
  if (normalized.includes("purchase") || normalized.includes("buy")) return "purchase";
  return null;
}

/** True when every meaningful word of `text` appears in the confirmed `source` field. */
export function isGroundedCopy(text: string, source: string): boolean {
  const normalize = (value: string) => value.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  const candidate = normalize(text);
  const evidence = normalize(source);
  if (!candidate || !evidence) return false;
  if (evidence.includes(candidate)) return true;
  const evidenceWords = new Set(evidence.split(" "));
  return candidate.split(" ").filter((word) => word.length > 2).every((word) => evidenceWords.has(word));
}

/** Parses the structured phrases the canvas understands while Gemini Live is off. */
export function parseTypedCommand(message: string): TypedCommand | null {
  const text = message.trim();
  for (const [field, pattern] of briefPatterns) {
    const match = text.match(pattern);
    if (match) return { kind: "brief", field, value: match[1] };
  }
  let match = text.match(/^select\s+(?:concept\s+)?([abc])(?:\s+scene)?\s+(\d)$/i);
  if (match) return { kind: "select", variant: match[1].toUpperCase() as VariantId, scene: Number(match[2]) };
  match = text.match(/^use\s+(product name|description|goal|goal detail|audience)(?:\s+as|\s+for)?\s+(?:the\s+)?copy$/i);
  if (match) return { kind: "use-copy", field: copySourceByPhrase[match[1].toLowerCase()] };
  match = text.match(/^move\s+scene\s+(\d)\s+(?:to|before)\s+(\d)$/i);
  if (match) return { kind: "move", from: Number(match[1]), to: Number(match[2]) };
  if (/^(?:run|run preflight|start run)$/i.test(text)) return { kind: "run" };
  return null;
}
