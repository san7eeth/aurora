class AuroraPcmCapture extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0];
    const output = outputs[0];
    if (input && input.length && input[0].length) {
      const mono = new Float32Array(input[0].length);
      for (let channel = 0; channel < input.length; channel++) {
        const samples = input[channel];
        for (let i = 0; i < samples.length; i++) mono[i] += samples[i] / input.length;
      }
      this.port.postMessage(mono, [mono.buffer]);
    }
    if (output) for (const channel of output) channel.fill(0);
    return true;
  }
}
registerProcessor('aurora-pcm-capture', AuroraPcmCapture);
