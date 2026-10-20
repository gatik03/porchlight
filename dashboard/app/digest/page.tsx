"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Timeline, TimelineItem } from "../../components/Timeline";
import { DigestAnomaly, fetchDigest } from "../../lib/api";

export default function DigestPage() {
  const [selectedDate, setSelectedDate] = useState(() => {
    return new Date().toISOString().split("T")[0];
  });
  const [timelineItems, setTimelineItems] = useState<TimelineItem[]>([]);
  const [anomalies, setAnomalies] = useState<DigestAnomaly[]>([]);
  const [narrative, setNarrative] = useState<string | null>(null);
  const [counts, setCounts] = useState({
    buttonPresses: 0,
    motion: 0,
    expected: 0,
    unexpected: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDigest() {
      setLoading(true);
      setNarrative(null);
      setAnomalies([]);
      try {
        fetchDigest(selectedDate)
          .then((digest) => {
            setNarrative(digest?.narrative ?? null);
            setAnomalies(digest?.anomalies ?? []);
          })
          .catch((err) => console.error("Failed to load digest:", err));

        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";
        const apiKey = process.env.NEXT_PUBLIC_PASSPHRASE || "test-dashboard-passphrase";

        const res = await fetch(`${apiBase}/api/events?date=${selectedDate}`, {
          headers: { "x-porchlight-key": apiKey },
        });

        if (res.ok) {
          const data = await res.json();
          const events = data.events || [];

          let bp = 0;
          let mo = 0;
          let exp = 0;
          let unexp = 0;
          const items: TimelineItem[] = [];

          for (const ev of events) {
            if (ev.type === "button_press") bp++;
            if (ev.type === "motion_detected") mo++;
            const card = ev.card;
            if (card) {
              if (card.severity === "calm") exp++;
              if (card.severity === "attention") unexp++;

              items.push({
                timeLocal: ev.occurredAt || ev.timeLocal,
                headline: card.headline || "Door Activity",
                sentence: card.sentence || "",
                severity: card.severity || "info",
                deviceName: ev.deviceName || "Front Door",
              });
            }
          }

          setCounts({ buttonPresses: bp, motion: mo, expected: exp, unexpected: unexp });
          setTimelineItems(items);
        }
      } catch (err) {
        console.error("Failed to load digest events:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDigest();
  }, [selectedDate]);

  return (
    <main className="min-h-screen bg-[#0A0A0C] text-zinc-100 p-6 md:p-12">
      <header className="flex flex-wrap justify-between items-center max-w-4xl mx-auto border-b border-zinc-800 pb-6 mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Caretaker Doorstep Digest</h1>
          <p className="text-sm text-zinc-400 mt-1">Daily timeline, anomaly detection, and AI caregiver narration</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 text-white rounded-lg px-3 py-1.5 text-sm"
          />
          <Link href="/" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold">
            Today View
          </Link>
        </div>
      </header>

      <section className="max-w-4xl mx-auto space-y-8">
        {/* Metric Cards Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-[#16161A] border border-zinc-800 rounded-2xl">
            <span className="text-xs font-semibold text-zinc-500 uppercase">Doorbell Rings</span>
            <p className="text-3xl font-bold text-white mt-1">{counts.buttonPresses}</p>
          </div>
          <div className="p-4 bg-[#16161A] border border-zinc-800 rounded-2xl">
            <span className="text-xs font-semibold text-zinc-500 uppercase">Motion Events</span>
            <p className="text-3xl font-bold text-white mt-1">{counts.motion}</p>
          </div>
          <div className="p-4 bg-[#16161A] border border-zinc-800 rounded-2xl">
            <span className="text-xs font-semibold text-zinc-500 uppercase">Expected Visits</span>
            <p className="text-3xl font-bold text-emerald-400 mt-1">{counts.expected}</p>
          </div>
          <div className="p-4 bg-[#16161A] border border-zinc-800 rounded-2xl">
            <span className="text-xs font-semibold text-zinc-500 uppercase">Attention Alerts</span>
            <p className="text-3xl font-bold text-amber-400 mt-1">{counts.unexpected}</p>
          </div>
        </div>

        {/* Anomaly Alerts Banner */}
        {anomalies.length > 0 && (
          <div className="space-y-3">
            {anomalies.map((a, i) => (
              <div
                key={i}
                className="p-4 bg-amber-950/60 border border-amber-600 rounded-2xl flex items-start gap-3"
              >
                <span className="text-xl">⚠</span>
                <div>
                  <h4 className="text-sm font-bold text-amber-300 uppercase tracking-wide">
                    Anomaly Flagged: {a.kind.replace(/_/g, " ")}{a.window ? ` (${a.window})` : ""}
                  </h4>
                  {a.explanation && <p className="text-sm text-zinc-300 mt-0.5">{a.explanation}</p>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Bedrock AI Caregiver Narrative */}
        <div className="p-6 bg-[#16161A] border border-zinc-800 rounded-3xl shadow-xl space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-white uppercase tracking-wider">
              Caregiver Daily Summary
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950 text-blue-400 border border-blue-800">
              Bedrock AI Narration
            </span>
          </div>
          {narrative ? (
            <p className="text-base text-zinc-300 leading-relaxed italic">"{narrative}"</p>
          ) : (
            !loading && <p className="text-base text-zinc-500">No digest yet for this date</p>
          )}
        </div>

        {/* Visual Doorstep Activity Timeline */}
        <div className="p-6 bg-[#16161A] border border-zinc-800 rounded-3xl shadow-xl space-y-6">
          <h3 className="text-lg font-bold text-white">Doorstep Activity Timeline</h3>
          {loading ? (
            <p className="text-sm text-zinc-500">Loading timeline...</p>
          ) : (
            <Timeline items={timelineItems} />
          )}
        </div>
      </section>
    </main>
  );
}
