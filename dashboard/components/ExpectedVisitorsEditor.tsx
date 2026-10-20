"use client";

import React, { useState } from "react";
import { ExpectedVisitor } from "../lib/api";

interface ExpectedVisitorsEditorProps {
  visitors: ExpectedVisitor[];
  onChange: (visitors: ExpectedVisitor[]) => void;
}

const ROLES = [
  { value: "service_worker", label: "Service Worker / Nurse / Caretaker" },
  { value: "courier", label: "Courier / Package Delivery" },
  { value: "delivery_food", label: "Food / Grocery Delivery" },
  { value: "neighbor_or_friend", label: "Neighbor or Friend" },
  { value: "solicitor", label: "Solicitor / Canvasser" },
  { value: "child", label: "Child" },
  { value: "unknown_adult", label: "Other Adult" },
];

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

export const ExpectedVisitorsEditor: React.FC<ExpectedVisitorsEditorProps> = ({
  visitors,
  onChange,
}) => {
  const [newLabel, setNewLabel] = useState("");
  const [newRole, setNewRole] = useState("service_worker");
  const [newDays, setNewDays] = useState<string[]>(["tue", "thu"]);
  const [newStart, setNewStart] = useState("09:30");
  const [newEnd, setNewEnd] = useState("11:00");
  const [newCarries, setNewCarries] = useState("");

  const handleAdd = () => {
    if (!newLabel.trim()) return;

    const newVisitor: ExpectedVisitor = {
      id: `v_${Date.now()}`,
      label: newLabel.trim(),
      role: newRole,
      days: newDays,
      windowStart: newStart,
      windowEnd: newEnd,
      carries: newCarries
        ? newCarries.split(",").map((c) => c.trim().toLowerCase())
        : [],
    };

    onChange([...visitors, newVisitor]);
    setNewLabel("");
    setNewCarries("");
  };

  const handleRemove = (id: string) => {
    onChange(visitors.filter((v) => v.id !== id));
  };

  const toggleDay = (day: string) => {
    if (newDays.includes(day)) {
      setNewDays(newDays.filter((d) => d !== day));
    } else {
      setNewDays([...newDays, day]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
        <h3 className="text-lg font-bold text-white">Expected Visitors Schedule</h3>
        <span className="text-xs text-zinc-400">Zero facial recognition • Role & time matching only</span>
      </div>

      {/* Visitor List */}
      <div className="space-y-3">
        {visitors.length === 0 ? (
          <p className="text-sm text-zinc-500 italic py-4">
            No expected visitors registered. Add recurring visitors (like visiting nurses or delivery windows) below.
          </p>
        ) : (
          visitors.map((v) => (
            <div
              key={v.id}
              className="flex items-center justify-between p-4 bg-[#16161A] border border-zinc-800 rounded-xl"
            >
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-bold text-white text-base">{v.label}</span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-950 text-blue-400 border border-blue-800 uppercase font-mono">
                    {v.role.replace("_", " ")}
                  </span>
                </div>
                <p className="text-sm text-zinc-400 mt-1">
                  Days: <span className="text-zinc-200 uppercase">{v.days.join(", ")}</span> • Window:{" "}
                  <span className="text-zinc-200">{v.windowStart} - {v.windowEnd}</span>
                  {v.carries && v.carries.length > 0 && ` • Carries: ${v.carries.join(", ")}`}
                </p>
              </div>

              <button
                type="button"
                onClick={() => handleRemove(v.id)}
                className="text-xs px-3 py-1.5 bg-red-950 text-red-400 hover:bg-red-900 rounded-lg transition"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>

      {/* Add New Visitor Form */}
      <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-2xl space-y-4">
        <h4 className="text-sm font-bold text-zinc-300">Add Expected Visitor Schedule</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">
              Private Household Label (e.g. Nurse Priya)
            </label>
            <input
              type="text"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder="e.g. Physical Therapist"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">Recognized Role</label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-zinc-400 mb-2">Active Days</label>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((d) => (
              <button
                type="button"
                key={d}
                onClick={() => toggleDay(d)}
                className={`px-3 py-1 text-xs font-bold uppercase rounded-md border transition ${
                  newDays.includes(d)
                    ? "bg-blue-600 border-blue-500 text-white"
                    : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-700"
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex gap-2 items-center">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-zinc-400 mb-1">Window Start</label>
              <input
                type="time"
                value={newStart}
                onChange={(e) => setNewStart(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-zinc-400 mb-1">Window End</label>
              <input
                type="time"
                value={newEnd}
                onChange={(e) => setNewEnd(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">
              Expected Carried Items (comma separated)
            </label>
            <input
              type="text"
              value={newCarries}
              onChange={(e) => setNewCarries(e.target.value)}
              placeholder="e.g. parcel, clipboard, toolbox"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleAdd}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-bold text-white transition"
        >
          Add to Expected Schedule
        </button>
      </div>
    </div>
  );
};
