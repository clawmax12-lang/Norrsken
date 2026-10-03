class PreflightCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunk = new Float32Array(2048);
    this.offset = 0;
  }

  process(inputs) {
    const input = inputs[0]?.[0];
    if (input) {
      for (const sample of input) {
        this.chunk[this.offset++] = sample;
        if (this.offset === this.chunk.length) {
          const ready = this.chunk;
          this.port.postMessage(ready.buffer, [ready.buffer]);
          this.chunk = new Float32Array(2048);
          this.offset = 0;
        }
      }
    }
    return true;
  }
}

registerProcessor("preflight-capture", PreflightCaptureProcessor);
