import type { CanvasDraft } from "./canvas-draft";

export function assertEditableScene(draft: CanvasDraft, sceneId: string) {
  if (draft.selected_scene_id !== sceneId) throw new Error("Select this scene before editing it.");
  const concept = draft.concepts.find((item) => item.variant_id === draft.selected_variant_id);
  if (!concept?.scenes.some((scene) => scene.id === sceneId)) throw new Error("That scene is not in the selected concept.");
  if (concept.status !== "draft" && concept.status !== "approved") throw new Error("This concept is locked for rendering/testing. Its existing evidence cannot follow changed content.");
}
