"use client";

import React from "react";

export interface TimelineItem {
  timeLocal: string;
  headline: string;
  sentence: string;
  severity: "calm" | "attention" | "info";
  deviceName?: string;
}

interface TimelineProps {
  items: TimelineItem[];
}

export const Timeline: React.FC<TimelineProps> = ({ items }) => {
  if (items.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-zinc-500 italic">
        No doorbell activity recorded for this period.
      </div>
    );
  }

  const badgeStyles = {
    calm: "bg-emerald-950 text-emerald-400 border-emerald-700",
    attention: "bg-amber-950 text-amber-400 border-amber-700",
    info: "bg-blue-950 text-blue-400 border-blue-700",
  };

  return (
    <div className="relative border-l-2 border-zinc-800 ml-4 space-y-6 py-2">
      {items.map((item, idx) => (
        <div key={idx} className="relative pl-6">
          {/* Dot on timeline */}
          <span
            className={`absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 ${
              item.severity === "calm"
                ? "bg-emerald-500 border-black"
                : item.severity === "attention"
                ? "bg-amber-500 border-black"
                : "bg-blue-500 border-black"
            }`}
          />

          <div className="bg-[#16161A] p-4 rounded-2xl border border-zinc-800/80 shadow-md">
            <div className="flex flex-wrap justify-between items-center gap-2 mb-2">
              <span className="text-xs font-mono font-medium text-zinc-400">
                {item.timeLocal}
              </span>
              <span
                className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold uppercase border ${
                  badgeStyles[item.severity] || "bg-zinc-800 text-zinc-400 border-zinc-700"
                }`}
              >
                {item.severity}
              </span>
            </div>

            <h4 className="text-sm font-semibold text-white mb-1">{item.headline}</h4>
            <p className="text-sm text-zinc-300">{item.sentence}</p>
          </div>
        </div>
      ))}
    </div>
  );
};
