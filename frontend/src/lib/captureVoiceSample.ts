/** Capture a short mono PCM sample for the optional local speaker-match profile. */
export async function captureVoiceSample(durationMs = 4000): Promise<Blob> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
  const context = new AudioContext();
  const chunks: Float32Array[] = [];
  try {
    await context.audioWorklet.addModule('/pcm-processor.js');
    const source = context.createMediaStreamSource(stream);
    const node = new AudioWorkletNode(context, 'aurora-pcm-capture');
    node.port.onmessage = (event: MessageEvent<Float32Array>) => chunks.push(new Float32Array(event.data));
    source.connect(node);
    node.connect(context.destination);
    await new Promise(resolve => window.setTimeout(resolve, durationMs));
    node.disconnect();
    source.disconnect();
    const sampleCount = chunks.reduce((count, chunk) => count + chunk.length, 0);
    const audio = new Float32Array(sampleCount);
    let offset = 0;
    for (const chunk of chunks) { audio.set(chunk, offset); offset += chunk.length; }
    const outputCount = Math.floor(sampleCount * 16000 / context.sampleRate);
    const pcm = new Int16Array(outputCount);
    for (let index = 0; index < outputCount; index++) {
      const position = index * context.sampleRate / 16000;
      const lower = Math.floor(position);
      const fraction = position - lower;
      const value = audio[lower] * (1 - fraction) + (audio[Math.min(lower + 1, sampleCount - 1)] ?? 0) * fraction;
      const clipped = Math.max(-1, Math.min(1, value));
      pcm[index] = clipped < 0 ? clipped * 32768 : clipped * 32767;
    }
    return new Blob([pcm.buffer], { type: 'application/octet-stream' });
  } finally {
    stream.getTracks().forEach(track => track.stop());
    await context.close();
  }
}
