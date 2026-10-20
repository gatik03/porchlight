"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CaptionOverlay } from "../../components/CaptionOverlay";
import { TranscribeStreamingClient } from "../../lib/transcribeClient";
import { WhepPlayer } from "../../lib/whepPlayer";

const DEMO_PHRASES = [
  "Hello! I have a delivery for Arthur.",
  "Just placing the package on the front step.",
  "Have a wonderful afternoon!",
];
const FALLBACK_REASON = "Live captions unavailable (Transcribe not enabled on this AWS plan) - showing demo captions";

export default function LiveViewPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [captionState, setCaptionState] = useState<"off" | "on">("off");
  const captionsActive = captionState === "on";
  const [partialCaption, setPartialCaption] = useState("");
  const [finalCaptions, setFinalCaptions] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState("Ready to connect to Front Door");
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [captionReason, setCaptionReason] = useState("");

  const whepPlayerRef = useRef<WhepPlayer | null>(null);
  const transcribeClientRef = useRef<TranscribeStreamingClient | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  // Check for ?demo=clip query param
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get("demo") === "clip") {
        setIsDemoMode(true);
      }
    }
  }, []);

  // Scripted demo captions run only while demo captions are ON; cleared on off/stop/unmount.
  useEffect(() => {
    if (!(captionsActive && isDemoMode)) return;
    setFinalCaptions([]);
    let idx = 0;
    const timer = setInterval(() => {
      if (idx < DEMO_PHRASES.length) {
        const phrase = DEMO_PHRASES[idx++];
        setFinalCaptions((prev) => [...prev, phrase]);
      } else {
        clearInterval(timer);
      }
    }, 4000);
    return () => clearInterval(timer);
  }, [captionsActive, isDemoMode]);

  const startStream = async () => {
    if (isDemoMode) {
      startDemoStream();
      return;
    }
    setStatusMessage("Negotiating WebRTC WHEP connection...");
    try {
      const endpoint = process.env.NEXT_PUBLIC_RING_WHEP_URL || "https://api.amazonvision.com/v1/devices/dev_front/live";
      const player = new WhepPlayer({
        endpoint,
        onError: (err) => {
          console.warn("WHEP fallback to demo stream:", err);
          startDemoStream();
        },
      });
      whepPlayerRef.current = player;

      const stream = await player.start();
      mediaStreamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setIsPlaying(true);
      setStatusMessage("Live video connected");
      startFrameCaptureInterval();
    } catch {
      startDemoStream();
    }
  };

  const startDemoStream = () => {
    setIsDemoMode(true);
    setIsPlaying(true);
    setStatusMessage("Live stream connected (Demo mode)");

  };

  const toggleCaptions = async () => {
    if (captionsActive) {
      setPartialCaption("");
      transcribeClientRef.current?.stop();
      transcribeClientRef.current = null;
      setCaptionState("off");
      return;
    }

    // Demo mode shows scripted captions; no Transcribe session involved.
    if (isDemoMode) {
      setCaptionState("on");
      return;
    }

    const fallbackToDemo = (err: Error) => {
      console.warn("Live captions unavailable, using demo captions:", err.message);
      transcribeClientRef.current?.stop();
      transcribeClientRef.current = null;
      setIsDemoMode(true);
      setCaptionReason(FALLBACK_REASON);
      setCaptionState("on");
      setStatusMessage(FALLBACK_REASON);
    };

    try {
      setStatusMessage("Requesting Transcribe streaming authorization...");
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";
      const apiKey = process.env.NEXT_PUBLIC_PASSPHRASE || "test-dashboard-passphrase";

      const authRes = await fetch(`${apiBase}/api/transcribe/url`, {
        headers: { "x-porchlight-key": apiKey },
      });
      if (!authRes.ok) throw new Error(`Transcribe authorization failed (${authRes.status})`);
      const authData = await authRes.json();
      if (!authData.url) throw new Error("Transcribe authorization returned no URL");
      if (!mediaStreamRef.current) throw new Error("No active media stream for live captions");

      const client = new TranscribeStreamingClient({
        websocketUrl: authData.url,
        mediaStream: mediaStreamRef.current,
        onTranscript: (text, isPartial) => {
          if (isPartial) {
            setPartialCaption(text);
          } else {
            setFinalCaptions((prev) => [...prev, text]);
            setPartialCaption("");
          }
        },
        onError: (err) => {
          fallbackToDemo(err);
        },
      });

      transcribeClientRef.current = client;
      await client.start();
      setCaptionState("on");
      setStatusMessage("Live Transcribe captions active");
    } catch (err: any) {
      fallbackToDemo(err);
    }
  };

  const startFrameCaptureInterval = () => {
    // Capture canvas frame every 2s while live view is open
    const interval = setInterval(() => {
      if (!videoRef.current) return;
      try {
        const canvas = document.createElement("canvas");
        canvas.width = 640;
        canvas.height = 360;
        const ctx = canvas.getContext("2d");
        if (ctx && videoRef.current.videoWidth > 0) {
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          const base64Jpg = canvas.toDataURL("image/jpeg", 0.7);
          const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";
          const apiKey = process.env.NEXT_PUBLIC_PASSPHRASE || "test-dashboard-passphrase";
          fetch(`${apiBase}/api/frames`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "x-porchlight-key": apiKey },
            body: JSON.stringify({ frame: base64Jpg, deviceId: "dev_front" }),
          }).catch(() => {});
        }
      } catch {}
    }, 2000);

    return () => clearInterval(interval);
  };

  const stopStream = () => {
    if (whepPlayerRef.current) {
      whepPlayerRef.current.stop();
      whepPlayerRef.current = null;
    }
    if (transcribeClientRef.current) {
      transcribeClientRef.current.stop();
      transcribeClientRef.current = null;
    }
    setIsPlaying(false);
    setCaptionState("off");
    setCaptionReason("");
    setPartialCaption("");
    setStatusMessage("Stream stopped");
  };

  return (
    <main className="min-h-screen bg-[#0A0A0C] text-zinc-100 p-6 md:p-10">
      <header className="flex justify-between items-center max-w-5xl mx-auto border-b border-zinc-800 pb-6 mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">Front Door Live View</h1>
          <p className="text-sm text-zinc-400 mt-1">{statusMessage}</p>
        </div>
        <Link href="/" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold">
          Back to Today
        </Link>
      </header>

      <section className="max-w-5xl mx-auto space-y-6">
        {/* Video Player Container */}
        <div className="relative aspect-video w-full rounded-3xl overflow-hidden bg-black border-2 border-zinc-800 shadow-2xl flex items-center justify-center">
          <video
            ref={videoRef}
            className={`w-full h-full object-cover ${isPlaying ? "block" : "hidden"}`}
            playsInline
            muted={false}
          />

          {!isPlaying && (
            <div className="text-center space-y-4 p-8">
              <div className="w-16 h-16 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center mx-auto text-2xl font-bold">
                ▶
              </div>
              <p className="text-zinc-400 max-w-md mx-auto">
                Open live view to see the doorstep camera and read streaming speech-to-text captions.
              </p>
              <button
                onClick={startStream}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold text-white shadow-lg transition"
              >
                Connect to Front Door
              </button>
            </div>
          )}

          {/* Subtitle Caption Overlay */}
          <CaptionOverlay
            partialText={captionsActive ? partialCaption : ""}
            finalTexts={captionsActive ? finalCaptions : []}
            fontSizePx={30}
          />
        </div>

        {/* Video Controls Bar */}
        {isPlaying && (
          <div className="flex flex-wrap gap-4 items-center justify-between p-4 bg-[#16161A] rounded-2xl border border-zinc-800">
            <div className="flex gap-3">
              <button
                onClick={toggleCaptions}
                className={`px-5 py-2.5 rounded-xl text-sm font-bold tracking-wide transition ${
                  captionsActive
                    ? "bg-emerald-600 text-white shadow-lg"
                    : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                }`}
              >
                {captionsActive
                  ? isDemoMode
                    ? "Demo captions: ON"
                    : "Captions: ON (Transcribe)"
                  : "Enable Live Captions"}
              </button>

              <button
                onClick={stopStream}
                className="px-5 py-2.5 bg-red-950 text-red-400 hover:bg-red-900 rounded-xl text-sm font-semibold transition"
              >
                Disconnect
              </button>
            </div>

            <span className="text-xs text-zinc-500 font-mono">
              {isDemoMode ? "Demo captions (scripted, not live speech)" : "WebRTC WHEP • 16kHz PCM16 • Transcribe Streaming"}
            </span>
            {captionReason && captionsActive && (
              <p className="w-full text-xs text-amber-400">{captionReason}</p>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
