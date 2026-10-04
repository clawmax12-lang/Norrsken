/** Extra frames the outgoing shot keeps playing while the next one starts. */
export const OVERLAP_FRAMES = 20;

export function shotWindow(
  startFrame: number,
  endFrame: number,
  durationFrames: number,
  overlap: number,
): { readonly from: number; readonly duration: number } {
  const length = endFrame - startFrame;
  return {
    from: startFrame,
    duration: Math.max(1, Math.min(length + overlap, durationFrames - startFrame)),
  };
}
