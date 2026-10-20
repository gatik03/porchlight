/**
 * WebRTC HTTP Egress Protocol (WHEP) player client for Ring live view.
 */

export interface WhepPlayerOptions {
  endpoint: string;
  token?: string;
  onTrack?: (track: MediaStreamTrack, stream: MediaStream) => void;
  onError?: (error: Error) => void;
}

export class WhepPlayer {
  private pc: RTCPeerConnection | null = null;
  private endpoint: string;
  private token?: string;
  private onTrackCallback?: (track: MediaStreamTrack, stream: MediaStream) => void;
  private onErrorCallback?: (error: Error) => void;

  constructor(options: WhepPlayerOptions) {
    this.endpoint = options.endpoint;
    this.token = options.token;
    this.onTrackCallback = options.onTrack;
    this.onErrorCallback = options.onError;
  }

  async start(): Promise<MediaStream> {
    const stream = new MediaStream();

    this.pc = new RTCPeerConnection({
      iceServers: [
        { urls: "stun:stun.kandy.io:3478" },
        { urls: "stun:stun.l.google.com:19302" },
      ],
      bundlePolicy: "max-bundle",
    });

    // Request receive-only audio and video
    this.pc.addTransceiver("video", { direction: "recvonly" });
    this.pc.addTransceiver("audio", { direction: "recvonly" });

    this.pc.ontrack = (event) => {
      stream.addTrack(event.track);
      if (this.onTrackCallback) {
        this.onTrackCallback(event.track, stream);
      }
    };

    try {
      const offer = await this.pc.createOffer();
      await this.pc.setLocalDescription(offer);

      const headers: Record<string, string> = {
        "Content-Type": "application/sdp",
      };
      if (this.token) {
        headers["Authorization"] = `Bearer ${this.token}`;
      }

      const res = await fetch(this.endpoint, {
        method: "POST",
        headers,
        body: offer.sdp,
      });

      if (!res.ok) {
        throw new Error(`WHEP negotiation failed: HTTP ${res.status}`);
      }

      const answerSdp = await res.text();
      await this.pc.setRemoteDescription({
        type: "answer",
        sdp: answerSdp,
      });

      return stream;
    } catch (err: any) {
      if (this.onErrorCallback) {
        this.onErrorCallback(err);
      }
      throw err;
    }
  }

  stop(): void {
    if (this.pc) {
      this.pc.close();
      this.pc = null;
    }
  }
}
