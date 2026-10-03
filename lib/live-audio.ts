export interface StoppableAudioSource {
  stop(): void;
}

/** Carry sample windows across capture chunks: 44.1 kHz must not drift at boundaries. */
export class Pcm16StreamEncoder {
  private inputCount = 0;
  private outputCount = 0;
  private sum = 0;
  private count = 0;

  constructor(private inputRate: number, private outputRate = 16_000) {
    if (!Number.isFinite(inputRate) || inputRate < outputRate || outputRate <= 0) throw new Error("Unsupported microphone sample rate.");
  }

  encode(input: Float32Array) {
    const samples: number[] = [];
    for (const value of input) {
      this.sum += Number.isFinite(value) ? Math.max(-1, Math.min(1, value)) : 0;
      this.count += 1;
      this.inputCount += 1;
      if (this.inputCount >= Math.floor((this.outputCount + 1) * this.inputRate / this.outputRate)) {
        const sample = Math.max(-1, Math.min(1, this.sum / this.count));
        samples.push(Math.round(sample < 0 ? sample * 0x8000 : sample * 0x7fff));
        this.outputCount += 1;
        this.sum = 0;
        this.count = 0;
      }
    }
    const bytes = new Uint8Array(samples.length * 2);
    const view = new DataView(bytes.buffer);
    samples.forEach((sample, index) => view.setInt16(index * 2, sample, true));
    return bytes;
  }
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
