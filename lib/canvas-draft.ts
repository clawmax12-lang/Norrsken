import { z } from "zod";

export const variantIds = ["A", "B", "C"] as const;
export const sourceFields = ["product_name", "one_liner", "goal", "goal_note", "audience"] as const;

export const sceneSchema = z
  .object({
    id: z.string().regex(/^[ABC]-scene-[1-6]$/),
    asset_id: z.string().max(120).optional(),
    text: z.string().trim().max(120).default(""),
    source_field: z.enum(sourceFields).optional(),
    t_start: z.number().min(0).max(15),
    t_end: z.number().min(0).max(15),
  })
  .superRefine((scene, context) => {
    if (scene.t_end <= scene.t_start) context.addIssue({ code: "custom", path: ["t_end"], message: "Scene must end after it starts." });
    if (scene.text && !scene.source_field) context.addIssue({ code: "custom", path: ["source_field"], message: "Scene copy needs a source field." });
  });

export const conceptSchema = z.object({
  variant_id: z.enum(variantIds),
  hypothesis: z.string().trim().min(1).max(180),
  hook: z.string().trim().max(80),
  scenes: z.array(sceneSchema).min(4).max(6),
  duration_s: z.literal(15),
  status: z.enum(["draft", "approved", "rendering", "rendered", "tested", "failed"]).default("draft"),
});

export const decisionSchema = z.object({
  id: z.string().min(1).max(120),
  choice: z.string().trim().min(1).max(240),
  rationale: z.string().trim().min(1).max(500),
  status: z.enum(["recommended", "rejected", "overridden"]),
  created_at: z.string().datetime(),
});

export const canvasDraftSchema = z
  .object({
    project_id: z.string().min(1).max(80).regex(/^[a-zA-Z0-9_-]+$/),
    revision: z.number().int().nonnegative(),
    selected_variant_id: z.enum(variantIds),
    selected_scene_id: z.string().regex(/^[ABC]-scene-[1-6]$/),
    concepts: z.array(conceptSchema).length(3),
    decisions: z.array(decisionSchema).max(30),
    updated_at: z.string().datetime(),
  })
  .superRefine((draft, context) => {
    const ids = draft.concepts.map((concept) => concept.variant_id);
    if (new Set(ids).size !== 3 || variantIds.some((id) => !ids.includes(id))) {
      context.addIssue({ code: "custom", path: ["concepts"], message: "Draft must contain exactly A, B, and C." });
    }
    if (!draft.selected_scene_id.startsWith(`${draft.selected_variant_id}-`)) {
      context.addIssue({ code: "custom", path: ["selected_scene_id"], message: "Selected scene must belong to the selected concept." });
    }
  });

export type CanvasDraft = z.infer<typeof canvasDraftSchema>;
export type Concept = z.infer<typeof conceptSchema>;
export type Scene = z.infer<typeof sceneSchema>;
export type VariantId = (typeof variantIds)[number];
export type SourceField = (typeof sourceFields)[number];

const hypotheses: Record<VariantId, string> = {
  A: "Problem first — establish the launch-week pain before revealing the product.",
  B: "Product first — show the clearest real workflow immediately.",
  C: "Outcome first — lead with the source-backed result the audience wants.",
};

export function createCanvasDraft(projectId: string): CanvasDraft {
  const concepts = variantIds.map((variantId) => ({
    variant_id: variantId,
    hypothesis: hypotheses[variantId],
    hook: "",
    scenes: Array.from({ length: 5 }, (_, index) => ({
      id: `${variantId}-scene-${index + 1}`,
      text: "",
      t_start: index * 3,
      t_end: (index + 1) * 3,
    })),
    duration_s: 15 as const,
    status: "draft" as const,
  }));
  return canvasDraftSchema.parse({
    project_id: projectId,
    revision: 0,
    selected_variant_id: "A",
    selected_scene_id: "A-scene-1",
    concepts,
    decisions: [],
    updated_at: new Date(0).toISOString(),
  });
}

export function replaceScene(draft: CanvasDraft, sceneId: string, update: Partial<Pick<Scene, "asset_id" | "text" | "source_field">>) {
  const next = structuredClone(draft);
  let found = false;
  for (const concept of next.concepts) {
    concept.scenes = concept.scenes.map((scene) => {
      if (scene.id !== sceneId) return scene;
      found = true;
      return { ...scene, ...update };
    });
  }
  if (!found) throw new Error("Scene does not exist in this draft.");
  next.revision += 1;
  next.updated_at = new Date().toISOString();
  return canvasDraftSchema.parse(next);
}

export function reorderScenes(draft: CanvasDraft, variantId: VariantId, from: number, to: number) {
  if (![from, to].every((index) => Number.isInteger(index) && index >= 1 && index <= 6)) throw new Error("Scene positions must be between 1 and 6.");
  const next = structuredClone(draft);
  const concept = next.concepts.find((item) => item.variant_id === variantId);
  if (!concept || from > concept.scenes.length || to > concept.scenes.length) throw new Error("Scene position is outside this concept.");
  const [moved] = concept.scenes.splice(from - 1, 1);
  concept.scenes.splice(to - 1, 0, moved);
  concept.scenes = concept.scenes.map((scene, index) => ({ ...scene, t_start: index * 3, t_end: (index + 1) * 3 }));
  next.revision += 1;
  next.updated_at = new Date().toISOString();
  return canvasDraftSchema.parse(next);
}
