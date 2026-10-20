"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ExpectedVisitorsEditor } from "../../components/ExpectedVisitorsEditor";
import { ExpectedVisitor, fetchSettings, Settings, updateSettings } from "../../lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    accountId: "acct_demo_household",
    timezone: "America/Los_Angeles",
    deviceNames: { dev_front: "Front Door" },
    expectedVisitors: [],
    quietHours: { start: "22:00", end: "06:00" },
    flashIntensity: "high",
    caretakerEmail: "",
  });
  const [loading, setLoading] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchSettings();
        setSettings(data);
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to load settings");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(false);
    setErrorMsg("");
    try {
      await updateSettings(settings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update settings");
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0A0A0C] text-zinc-100 p-8 flex items-center justify-center">
        <p className="text-zinc-500">Loading household settings...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0A0A0C] text-zinc-100 p-6 md:p-12">
      <header className="flex justify-between items-center max-w-4xl mx-auto border-b border-zinc-800 pb-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Household Settings</h1>
          <p className="text-sm text-zinc-400 mt-1">Configure door accessibility, schedules, and notifications</p>
        </div>
        <Link href="/" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-semibold">
          Back to Today
        </Link>
      </header>

      <form onSubmit={handleSave} className="max-w-4xl mx-auto space-y-10">
        {saveSuccess && (
          <div className="p-4 rounded-xl bg-emerald-950 border border-emerald-500 text-emerald-300 text-sm font-semibold">
            ✓ Settings saved successfully to DynamoDB
          </div>
        )}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-red-950 border border-red-500 text-red-300 text-sm font-semibold">
            ⚠ {errorMsg}
          </div>
        )}

        {/* Expected Visitors Schedule */}
        <div className="p-6 bg-[#16161A] border border-zinc-800 rounded-3xl shadow-xl">
          <ExpectedVisitorsEditor
            visitors={settings.expectedVisitors || []}
            onChange={(newVisitors: ExpectedVisitor[]) =>
              setSettings({ ...settings, expectedVisitors: newVisitors })
            }
          />
        </div>

        {/* Quiet Hours & Flashing Border Preferences */}
        <div className="p-6 bg-[#16161A] border border-zinc-800 rounded-3xl shadow-xl space-y-6">
          <h3 className="text-lg font-bold text-white border-b border-zinc-800 pb-3">
            Night & Television Accessibility
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-zinc-300 mb-2">
                Quiet Hours (Night Activity Alert)
              </label>
              <div className="flex gap-3 items-center">
                <input
                  type="time"
                  value={settings.quietHours.start}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      quietHours: { ...settings.quietHours, start: e.target.value },
                    })
                  }
                  className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
                />
                <span className="text-zinc-500 text-sm">to</span>
                <input
                  type="time"
                  value={settings.quietHours.end}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      quietHours: { ...settings.quietHours, end: e.target.value },
                    })
                  }
                  className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <p className="text-xs text-zinc-500 mt-2">
                Door events during quiet hours trigger an immediate ATTENTION card.
              </p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-zinc-300 mb-2">
                Fire TV Flashing Border Intensity
              </label>
              <select
                value={settings.flashIntensity}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    flashIntensity: e.target.value as "off" | "low" | "high",
                  })
                }
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              >
                <option value="high">High (24px pulsating border - standard visual chime)</option>
                <option value="low">Low (8px subtle outline)</option>
                <option value="off">Off (Solid border, photosensitive friendly)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-zinc-800">
            <div>
              <label className="block text-sm font-semibold text-zinc-300 mb-1">Timezone</label>
              <input
                type="text"
                value={settings.timezone}
                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-zinc-300 mb-1">
                Caregiver Email Address (Optional SES Digest)
              </label>
              <input
                type="email"
                value={settings.caretakerEmail || ""}
                onChange={(e) => setSettings({ ...settings, caretakerEmail: e.target.value })}
                placeholder="caregiver@family.org"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-4">
          <Link href="/" className="px-6 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm font-semibold">
            Cancel
          </Link>
          <button
            type="submit"
            className="px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-bold text-white shadow-xl transition"
          >
            Save Household Preferences
          </button>
        </div>
      </form>
    </main>
  );
}
