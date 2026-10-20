"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Card as CardComponent } from "../components/Card";
import { Card, dismissCard, fetchCurrentCard } from "../lib/api";

export default function TodayPage() {
  const [currentCard, setCurrentCard] = useState<Card | null>(null);
  const [loading, setLoading] = useState(true);

  const loadCard = async () => {
    try {
      const card = await fetchCurrentCard();
      setCurrentCard(card);
    } catch (err) {
      console.error("Polling card error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCard();
    const interval = setInterval(loadCard, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDismiss = async () => {
    try {
      await dismissCard();
      setCurrentCard(null);
    } catch (err) {
      console.error("Failed to dismiss card:", err);
    }
  };

  return (
    <main className="min-h-screen bg-[#0A0A0C] text-zinc-100 p-8 md:p-12">
      <header className="flex justify-between items-center max-w-5xl mx-auto border-b border-zinc-800 pb-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Porchlight</h1>
          <p className="text-sm text-zinc-400 mt-1">Smart Doorbell Visual Chime & Caretaking</p>
        </div>
        <nav className="flex gap-4">
          <Link href="/live" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition">
            Live View & Captions
          </Link>
          <Link href="/digest" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold transition">
            Digest
          </Link>
          <Link href="/settings" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold transition">
            Settings
          </Link>
          <Link href="/card-preview" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold transition">
            TV Preview
          </Link>
        </nav>
      </header>

      <section className="max-w-5xl mx-auto">
        {loading && !currentCard ? (
          <div className="text-center py-24 text-zinc-500">Checking for doorstep activity...</div>
        ) : currentCard ? (
          <CardComponent card={currentCard} onDismiss={handleDismiss} />
        ) : (
          <div className="rounded-2xl border border-zinc-800 bg-[#16161A] p-16 text-center">
            <h2 className="text-xl font-semibold text-zinc-300 mb-2">Porchlight is Watching the Door</h2>
            <p className="text-zinc-500 max-w-md mx-auto">
              No active events at this moment. When someone presses the doorbell or approaches, an accessible visual card will appear here.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
