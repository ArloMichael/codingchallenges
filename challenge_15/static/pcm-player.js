class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.queue = [];
    this.currentChunk = null;
    this.currentIndex = 0;
    this.lastSample = 0;
    this.rampFrom = 0;
    this.rampTotal = 0;
    this.rampRemaining = 0;
    this.meterSum = 0;
    this.meterCount = 0;
    this.meterFrames = 0;

    this.port.onmessage = (event) => {
      if (event.data && event.data.type === "reset") {
        this.queue = [];
        this.currentChunk = null;
        this.currentIndex = 0;
        this.lastSample = 0;
        this.rampRemaining = 0;
        this.meterSum = 0;
        this.meterCount = 0;
        this.meterFrames = 0;
        this.port.postMessage({ type: "level", value: 0 });
        return;
      }

      this.queue.push(new Float32Array(event.data));
    };
  }

  loadNextChunk() {
    this.currentChunk = this.queue.shift() || null;
    this.currentIndex = 0;

    if (this.currentChunk) {
      this.rampFrom = this.lastSample;
      this.rampTotal = Math.min(128, this.currentChunk.length);
      this.rampRemaining = this.rampTotal;
    }
  }

  readSample() {
    while (!this.currentChunk || this.currentIndex >= this.currentChunk.length) {
      this.loadNextChunk();

      if (!this.currentChunk) {
        this.lastSample *= 0.95;
        return Math.abs(this.lastSample) < 0.00001 ? 0 : this.lastSample;
      }
    }

    let sample = this.currentChunk[this.currentIndex++];

    if (this.rampRemaining > 0) {
      const alpha = (this.rampTotal - this.rampRemaining + 1) / this.rampTotal;
      sample = this.rampFrom * (1 - alpha) + sample * alpha;
      this.rampRemaining -= 1;
    }

    this.lastSample = sample;
    return sample;
  }

  process(inputs, outputs) {
    const output = outputs[0];

    for (let i = 0; i < output[0].length; i++) {
      const sample = this.readSample();
      this.meterSum += sample * sample;
      this.meterCount += 1;

      for (let channel = 0; channel < output.length; channel++) {
        output[channel][i] = sample;
      }
    }

    this.meterFrames += 1;
    if (this.meterFrames >= 4) {
      const rms = this.meterCount ? Math.sqrt(this.meterSum / this.meterCount) : 0;
      this.port.postMessage({ type: "level", value: rms });
      this.meterSum = 0;
      this.meterCount = 0;
      this.meterFrames = 0;
    }

    return true;
  }
}

registerProcessor("pcm-player", PCMPlayerProcessor);
