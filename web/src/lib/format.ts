// Display helpers: status labels/tones, attribute names and value formatting.
import type { AttributeCheck, Status } from "./types";

export const STATUS_LABEL: Record<Status, string> = {
  pass: "Pass",
  current: "Current",
  drift: "Drift",
  orphaned: "Orphaned",
  ambiguous: "Ambiguous",
  lapsed: "Lapsed",
  pending: "Pending",
};

export type Tone = "good" | "bad" | "warn" | "odd";

export function statusTone(s: Status): Tone {
  if (s === "pass" || s === "current") return "good";
  if (s === "drift") return "bad";
  if (s === "orphaned" || s === "ambiguous") return "odd";
  return "warn";
}

export const ATTRIBUTE_LABEL: Record<AttributeCheck["attribute"], string> = {
  pressure: "Pressure",
  temperature: "Temperature",
  phase: "Phase",
  vapor_fraction: "Vapor fraction",
};

export function fmtValue(v: number | string | null | undefined, unit = ""): string {
  if (v === null || v === undefined) return "n/a";
  if (typeof v === "string") return v;
  const s = Number.isInteger(v) ? v.toLocaleString("en-US") : v.toFixed(2);
  return unit ? `${s} ${unit}` : s;
}

export function fmtDelta(d: number | null): string {
  if (d === null) return "";
  const s = Number.isInteger(d) ? String(Math.abs(d)) : Math.abs(d).toFixed(2);
  return d > 0 ? `+${s}` : d < 0 ? `−${s}` : "0";
}

export function percent(part: number, whole: number): number {
  return whole === 0 ? 0 : Math.round((part / whole) * 100);
}
