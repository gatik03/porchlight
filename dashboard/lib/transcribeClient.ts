/**
 * Real-time speech captioning client using Amazon Transcribe Streaming WebSocket.
 * Downsamples WebRTC audio to 16 kHz Mono PCM16 in browser.
 */

export interface TranscribeClientOptions {
  websocketUrl: string;
  mediaStream: MediaStream;
  onTranscript: (text: string, isPartial: boolean) => void;
  onError?: (error: Error) => void;
}

export class TranscribeStreamingClient {
  private ws: WebSocket | null = null;
  private audioContext: AudioContext | null = null;
  private mediaStreamSource: MediaStreamAudioSourceNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private options: TranscribeClientOptions;
  private isRunning: boolean = false;

  constructor(options: TranscribeClientOptions) {
    this.options = options;
  }

  async start(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      this.ws = new WebSocket(this.options.websocketUrl);
      this.ws.binaryType = "arraybuffer";

      this.ws.onopen = () => {
        this.initAudioCapture();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        this.handleMessage(event.data);
      };

      this.ws.onerror = (event: Event) => {
        if (this.options.onError) {
          this.options.onError(new Error("Transcribe WebSocket error"));
        }
      };

      this.ws.onclose = () => {
        if (this.isRunning) this.options.onError?.(new Error("Transcribe connection closed"));
        this.stop();
      };
    } catch (err: any) {
      if (this.options.onError) {
        this.options.onError(err);
      }
      this.stop();
    }
  }

  private initAudioCapture(): void {
    const audioTrack = this.options.mediaStream.getAudioTracks()[0];
    if (!audioTrack) {
      if (this.options.onError) {
        this.options.onError(new Error("No audio track in media stream"));
      }
      return;
    }

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    this.audioContext = new AudioContextClass({ sampleRate: 16000 });
    this.mediaStreamSource = this.audioContext.createMediaStreamSource(this.options.mediaStream);

    // Buffer size 2048 samples at 16kHz (~128ms per chunk)
    this.scriptProcessor = this.audioContext.createScriptProcessor(2048, 1, 1);

    this.scriptProcessor.onaudioprocess = (e: AudioProcessingEvent) => {
      if (!this.isRunning || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
        return;
      }

      const inputData = e.inputBuffer.getChannelData(0);
      const pcm16 = this.downsampleToPcm16(inputData);
      const eventFrame = this.wrapAudioEvent(pcm16);

      this.ws.send(eventFrame);
    };

    this.mediaStreamSource.connect(this.scriptProcessor);
    this.scriptProcessor.connect(this.audioContext.destination);
  }

  private downsampleToPcm16(floatData: Float32Array): Int16Array {
    const pcm16 = new Int16Array(floatData.length);
    for (let i = 0; i < floatData.length; i++) {
      const s = Math.max(-1, Math.min(1, floatData[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return pcm16;
  }

  private wrapAudioEvent(pcmData: Int16Array): ArrayBuffer {
    return encodeAudioEvent(new Uint8Array(pcmData.buffer, pcmData.byteOffset, pcmData.byteLength));
  }

  private handleMessage(data: ArrayBuffer): void {
    try {
      // Event-stream frame: 12-byte prelude, headers, JSON payload, 4-byte message CRC
      const view = new DataView(data);
      const total = view.getUint32(0);
      const headersLen = view.getUint32(4);
      const payload = new Uint8Array(data, 12 + headersLen, total - 16 - headersLen);
      const parsed = JSON.parse(new TextDecoder("utf-8").decode(payload));

      const results = parsed.Transcript?.Results || [];
      for (const res of results) {
        const isPartial = res.IsPartial === true;
        const alt = res.Alternatives?.[0];
        if (alt && alt.Transcript) {
          this.options.onTranscript(alt.Transcript, isPartial);
        }
      }
    } catch {
      // Non-transcript frames (e.g. exceptions) are ignored
    }
  }

  stop(): void {
    this.isRunning = false;

    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }
    if (this.mediaStreamSource) {
      this.mediaStreamSource.disconnect();
      this.mediaStreamSource = null;
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

let crcTable: Uint32Array | null = null;

export function crc32(bytes: Uint8Array, crc = 0): number {
  if (!crcTable) {
    crcTable = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      crcTable[n] = c >>> 0;
    }
  }
  let c = ~crc >>> 0;
  for (let i = 0; i < bytes.length; i++) c = crcTable[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return ~c >>> 0;
}

function encodeHeader(name: string, value: string): Uint8Array {
  const enc = new TextEncoder();
  const n = enc.encode(name);
  const v = enc.encode(value);
  const out = new Uint8Array(1 + n.length + 1 + 2 + v.length);
  out[0] = n.length;
  out.set(n, 1);
  out[1 + n.length] = 7; // header value type: string
  new DataView(out.buffer).setUint16(2 + n.length, v.length);
  out.set(v, 4 + n.length);
  return out;
}

/** AWS event-stream message: prelude (len, headers len, CRC) + headers + payload + message CRC. */
export function encodeAudioEvent(payload: Uint8Array): ArrayBuffer {
  const headers = [
    encodeHeader(":content-type", "application/octet-stream"),
    encodeHeader(":event-type", "AudioEvent"),
    encodeHeader(":message-type", "event"),
  ];
  const headersLen = headers.reduce((a, h) => a + h.length, 0);
  const total = 16 + headersLen + payload.length;
  const buffer = new ArrayBuffer(total);
  const bytes = new Uint8Array(buffer);
  const view = new DataView(buffer);

  view.setUint32(0, total);
  view.setUint32(4, headersLen);
  view.setUint32(8, crc32(bytes.subarray(0, 8)));
  let off = 12;
  for (const h of headers) {
    bytes.set(h, off);
    off += h.length;
  }
  bytes.set(payload, off);
  view.setUint32(total - 4, crc32(bytes.subarray(0, total - 4)));
  return buffer;
}
