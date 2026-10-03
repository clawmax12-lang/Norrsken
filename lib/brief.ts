import { z } from "zod";

export const goals = ["signups", "downloads", "understand", "purchase"] as const;

export const briefSchema = z.object({
  project_id: z.string().min(1).max(80).regex(/^[a-zA-Z0-9_-]+$/),
  product_name: z.string().trim().min(1).max(80),
  one_liner: z.string().trim().min(1).max(140),
  screenshots: z.array(z.string().min(1)).min(3).max(6),
  goal: z.enum(goals),
  goal_note: z.string().trim().max(240).optional(),
  audience: z.string().trim().min(1).max(300),
  brand_color: z.string().regex(/^#[0-9a-fA-F]{6}$/).optional(),
  logo: z.string().optional(),
});

export type Brief = z.infer<typeof briefSchema>;

export type BriefDraft = Omit<Brief, "screenshots"> & {
  screenshots: string[];
};

export type BriefField = "product_name" | "one_liner" | "goal" | "goal_note" | "audience";

export type FieldSource = "voice" | "typed" | "asset";

export type SourceMap = Partial<Record<BriefField, FieldSource>>;

export const emptyBrief = (projectId: string): BriefDraft => ({
  project_id: projectId,
  product_name: "",
  one_liner: "",
  screenshots: [],
  goal: "signups",
  goal_note: "",
  audience: "",
});
