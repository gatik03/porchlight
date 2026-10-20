"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Card as CardComponent } from "../../components/Card";
import { Card as CardType } from "../../lib/api";

const PREVIEW_CARDS: Record<string, CardType> = {
  calm: {
    cardId: "preview-calm",
    accountId: "acct_demo",
    severity: "calm",
    headline: "Expected visitor",
    sentence: "Nurse Priya is walking up the front path.",
    expectedLine: "Expected: Nurse Priya (09:30 - 11:00)",
    deviceName: "Front Door",
    timeLocal: "Tuesday 10:04 AM",
    createdAt: new Date().toISOString(),
  },
  attention: {
    cardId: "preview-attention",
    accountId: "acct_demo",
    severity: "attention",
    headline: "Someone is at the door",
    sentence: "A courier in a high-visibility vest is holding a parcel at the door.",
    deviceName: "Front Door",
    timeLocal: "Tuesday 2:15 PM",
    createdAt: new Date().toISOString(),
  },
  info: {
    cardId: "preview-info",
    accountId: "acct_demo",
    severity: "info",
    headline: "Movement outside",
    sentence: "A domestic cat is sitting on the front doormat.",
    deviceName: "Front Door",
    timeLocal: "Tuesday 4:30 PM",
    createdAt: new Date().toISOString(),
  },
};

export default function CardPreviewPage() {
  const [selectedKey, setSelectedKey] = useState<string>("attention");
  const [tvMode, setTvMode] = useState<boolean>(true);

  return (
    <main className="min-h-screen bg-[#0A0A0C] text-zinc-100 p-8 md:p-12">
      <header className="flex justify-between items-center max-w-5xl mx-auto border-b border-zinc-800 pb-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Fire TV Card Preview & Simulator</h1>
          <p className="text-sm text-zinc-400 mt-1">Simulate 10-foot television visual chime layouts</p>
        </div>
        <Link href="/" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold">
          Back to Today
        </Link>
      </header>

      <section className="max-w-5xl mx-auto space-y-8">
        <div className="flex gap-4 items-center">
          <span className="text-sm font-semibold text-zinc-400">Severity Preset:</span>
          {Object.keys(PREVIEW_CARDS).map((k) => (
            <button
              key={k}
              onClick={() => setSelectedKey(k)}
              className={`px-4 py-2 rounded-lg text-sm font-bold uppercase transition ${
                selectedKey === k ? "bg-blue-600 text-white" : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
              }`}
            >
              {k}
            </button>
          ))}

          <label className="ml-auto flex items-center gap-2 text-sm text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={tvMode}
              onChange={(e) => setTvMode(e.target.checked)}
              className="rounded bg-zinc-800"
            />
            10-Foot TV Mode (Large Typography)
          </label>
        </div>

        <div className="border border-zinc-800 rounded-3xl p-4 bg-black shadow-2xl">
          <CardComponent card={PREVIEW_CARDS[selectedKey]} isTvMode={tvMode} />
        </div>
      </section>
    </main>
  );
}
