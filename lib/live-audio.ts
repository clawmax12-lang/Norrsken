export interface StoppableAudioSource {
  stop(): void;
}

export function normalizedRms(samples: Float32Array, boost = 1) {
  if (samples.length === 0) return 0;
  let sum = 0;
  for (const sample of samples) sum += sample * sample;
  return Math.min(1, Math.sqrt(sum / samples.length) * boost);
}

export function outputVisualState(samples: Float32Array, activeSources: number, muted: boolean) {
  const level = muted || activeSources === 0 ? 0 : normalizedRms(samples, 4.5);
  return { level, isSpeaking: level > 0.012 };
}

export function stopQueuedPlayback<T extends StoppableAudioSource>(sources: Set<T>) {
  for (const source of sources) {
    try {
      source.stop();
    } catch {
      // An already-ended source is safe to discard with the rest of the queue.
    }
  }
  sources.clear();
}
