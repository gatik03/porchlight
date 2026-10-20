"use client";

import React from "react";

interface CaptionOverlayProps {
  partialText: string;
  finalTexts: string[];
  fontSizePx?: number;
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  partialText,
  finalTexts,
  fontSizePx = 28,
}) => {
  if (!partialText && finalTexts.length === 0) {
    return null;
  }

  // Show last 2 final lines + active partial line
  const displayFinal = finalTexts.slice(-2);

  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute bottom-12 left-6 right-6 flex flex-col items-center pointer-events-none z-50"
    >
      <div className="bg-black/85 backdrop-blur-md rounded-2xl px-8 py-4 border border-zinc-700 shadow-2xl max-w-4xl text-center">
        {displayFinal.map((line, idx) => (
          <p
            key={idx}
            style={{ fontSize: `${fontSizePx}px` }}
            className="text-white font-bold tracking-wide drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
          >
            {line}
          </p>
        ))}
        {partialText && (
          <p
            style={{ fontSize: `${fontSizePx}px` }}
            className="text-slate-300 italic font-medium drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
          >
            {partialText}
          </p>
        )}
      </div>
    </div>
  );
};
