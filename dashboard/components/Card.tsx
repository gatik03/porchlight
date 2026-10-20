"use client";

import React from "react";
import { Card as CardType } from "../lib/api";

interface CardProps {
  card: CardType;
  onDismiss?: () => void;
  isTvMode?: boolean;
}

export const Card: React.FC<CardProps> = ({ card, onDismiss, isTvMode = false }) => {
  const { severity, headline, sentence, expectedLine, deviceName, timeLocal, frameUrl } = card;

  // Severity styles
  const severityStyles = {
    calm: {
      border: "border-emerald-500",
      bgBadge: "bg-emerald-950 text-emerald-400 border-emerald-500",
      label: "CALM • EXPECTED",
    },
    attention: {
      border: "border-amber-500",
      bgBadge: "bg-amber-950 text-amber-400 border-amber-500",
      label: "ATTENTION • UNEXPECTED",
    },
    info: {
      border: "border-blue-500",
      bgBadge: "bg-blue-950 text-blue-400 border-blue-500",
      label: "INFO • ACTIVITY",
    },
  }[severity] || {
    border: "border-zinc-700",
    bgBadge: "bg-zinc-800 text-zinc-300 border-zinc-600",
    label: "EVENT",
  };

  return (
    <div
      role="region"
      aria-label={`${headline}: ${sentence}`}
      className={`relative w-full rounded-2xl bg-[#16161A] text-white p-6 shadow-2xl border-4 ${
        severityStyles.border
      } ${isTvMode ? "p-12 border-8" : ""}`}
    >
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
              severityStyles.bgBadge
            } ${isTvMode ? "text-xl px-5 py-2" : ""}`}
          >
            {severityStyles.label}
          </span>
          <h2 className={`font-semibold text-zinc-300 ${isTvMode ? "text-3xl" : "text-lg"}`}>
            {headline}
          </h2>
        </div>
        <span className={`text-zinc-400 font-mono ${isTvMode ? "text-2xl" : "text-sm"}`}>
          {deviceName} • {timeLocal}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div className="md:col-span-2 space-y-4">
          <p
            className={`font-bold tracking-tight text-white leading-tight ${
              isTvMode ? "text-6xl" : "text-2xl md:text-3xl"
            }`}
          >
            {sentence}
          </p>

          {expectedLine && (
            <p className={`font-medium text-emerald-400 ${isTvMode ? "text-4xl" : "text-lg"}`}>
              {expectedLine}
            </p>
          )}

          {onDismiss && (
            <div className="pt-4">
              <button
                onClick={onDismiss}
                className="px-6 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white font-medium focus:ring-2 focus:ring-white transition"
              >
                Dismiss Card
              </button>
            </div>
          )}
        </div>

        {frameUrl && (
          <div className="flex justify-end">
            <img
              src={frameUrl}
              alt="Doorstep camera snapshot"
              className="rounded-xl border border-zinc-700 max-h-64 object-cover shadow-lg"
            />
          </div>
        )}
      </div>
    </div>
  );
};
