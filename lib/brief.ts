import { z } from "zod";

export const goals = ["signups", "downloads", "understand", "purchase"] as const;

export const briefSchema = z.object({
  project_id: z.string().min(1).max(80).regex(/^[a-zA-Z0-9_-]+$/),
  product_name: z.string().trim().min(1).max(80),
  one_liner: z.string().trim().min(1).max(140),
  screenshots: z.array(z.string().min(1)).min(3).max(6),
  goal: z.enum(goals),
  goal_note: z.string().trim().max(240).optional(),
  buyer_cta: z.string().trim().max(40).optional(),
  proof_points: z.string().trim().max(400).optional(),
  audience: z.string().trim().min(1).max(300),
  brand_color: z.string().regex(/^#[0-9a-fA-F]{6}$/).optional(),
  logo: z.string().optional(),
  render_mode: z.enum(["showcase", "generative_motion"]).default("showcase"),
});

export type Brief = z.infer<typeof briefSchema>;

export type BriefDraft = Omit<Brief, "screenshots"> & {
  screenshots: string[];
};

export type BriefField = "product_name" | "one_liner" | "goal" | "goal_note" | "audience";
export type RenderMode = NonNullable<Brief["render_mode"]>;

/** Optional copy inputs that steer the videos but are not voice/canvas source fields. */
export type BriefExtraField = "buyer_cta" | "proof_points";

export const BRIEF_EXTRA_MAX = { buyer_cta: 40, proof_points: 400 } as const satisfies Record<BriefExtraField, number>;

export type BriefTextField = Exclude<BriefField, "goal">;

export type FieldSource = "voice" | "typed" | "asset";

export type SourceMap = Partial<Record<BriefField, FieldSource>>;

/** Character caps for typed brief fields (matches `briefSchema`). */
export const BRIEF_FIELD_MAX = {
  product_name: 80,
  one_liner: 140,
  audience: 300,
  goal_note: 240,
} as const satisfies Record<BriefTextField, number>;

const LIMIT_ERROR: Record<BriefTextField, string> = {
  product_name: "Product name must be 80 characters or fewer.",
  one_liner: "Description must be 140 characters or fewer.",
  audience: "Audience must be 300 characters or fewer.",
  goal_note: "Call to action must be 240 characters or fewer.",
};

/**
 * Live typing keeps inner/trailing spaces so “Sell anything” can be entered.
 * Commit (blur, voice, persist) trims ends. Never invents words.
 */
export function applyBriefFieldInput(
  field: BriefTextField,
  rawValue: string,
  mode: "live" | "commit",
): string {
  const value = mode === "commit" ? rawValue.trim() : rawValue;
  if (value.length > BRIEF_FIELD_MAX[field]) throw new Error(LIMIT_ERROR[field]);
  return value;
}

export const emptyBrief = (projectId: string): BriefDraft => ({
  project_id: projectId,
  product_name: "",
  one_liner: "",
  screenshots: [],
  goal: "signups",
  goal_note: "",
  audience: "",
  render_mode: "showcase",
});
