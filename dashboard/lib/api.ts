/**
 * API client for Porchlight Read API.
 */

export interface Card {
  cardId: string;
  accountId: string;
  severity: "calm" | "attention" | "info";
  headline: string;
  sentence: string;
  expectedLine?: string;
  deviceName: string;
  timeLocal: string;
  frameUrl?: string;
  createdAt: string;
  dismissedAt?: string | null;
  latencyMs?: {
    webhookToEnqueue: number;
    frame: number;
    vision: number;
    total: number;
  };
}

export interface ExpectedVisitor {
  id: string;
  label: string;
  role: string;
  days: string[];
  windowStart: string;
  windowEnd: string;
  carries?: string[];
}

export interface Settings {
  accountId: string;
  timezone: string;
  deviceNames: Record<string, string>;
  expectedVisitors: ExpectedVisitor[];
  quietHours: { start: string; end: string };
  flashIntensity: "off" | "low" | "high";
  caretakerEmail?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";
const API_KEY = process.env.NEXT_PUBLIC_PASSPHRASE || "test-dashboard-passphrase";

export async function fetchCurrentCard(since?: string): Promise<Card | null> {
  const url = since
    ? `${API_BASE}/api/card/current?since=${encodeURIComponent(since)}`
    : `${API_BASE}/api/card/current`;

  const res = await fetch(url, {
    headers: { "x-porchlight-key": API_KEY },
  });

  if (res.status === 204) {
    return null;
  }
  if (!res.ok) {
    throw new Error(`Failed to fetch current card: ${res.status}`);
  }
  return res.json();
}

export async function dismissCard(): Promise<void> {
  await fetch(`${API_BASE}/api/card/dismiss`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-porchlight-key": API_KEY,
    },
  });
}

export async function fetchSettings(): Promise<Settings> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    headers: { "x-porchlight-key": API_KEY },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch settings: ${res.status}`);
  }
  return res.json();
}

export async function updateSettings(settings: Settings): Promise<void> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "x-porchlight-key": API_KEY,
    },
    body: jsonStringify(settings),
  });
  if (!res.ok) {
    throw new Error(`Failed to update settings: ${res.status}`);
  }
}

export interface DigestAnomaly {
  kind: string;
  window?: string;
  explanation?: string;
  [key: string]: unknown;
}

export interface Digest {
  narrative: string;
  anomalies?: DigestAnomaly[];
}

/** Returns null when no digest exists for the date (404). */
export async function fetchDigest(date: string): Promise<Digest | null> {
  const res = await fetch(`${API_BASE}/api/digest/${encodeURIComponent(date)}`, {
    headers: { "x-porchlight-key": API_KEY },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to fetch digest: ${res.status}`);
  return res.json();
}

function jsonStringify(data: any): string {
  return JSON.stringify(data);
}
