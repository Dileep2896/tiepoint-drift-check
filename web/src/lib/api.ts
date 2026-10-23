// Thin client for the engine's HTTP API.
import type { DocRef, ExtractionResult, Party, Report, Rev } from "./types";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  check: (rev: Rev) => call<Report>(`/api/check?rev=${rev}`),
  documents: (rev: Rev) => call<{ documents: DocRef[] }>(`/api/project?rev=${rev}`).then((p) => p.documents),
  accept: (id: string, rev: Rev, stream_tag?: string) =>
    call(`/api/tiepoints/${id}/accept?rev=${rev}`, { method: "POST", body: JSON.stringify({ stream_tag: stream_tag ?? null }) }),
  attest: (id: string, party: Party, rev: Rev) =>
    call(`/api/tiepoints/${id}/attest?rev=${rev}`, { method: "POST", body: JSON.stringify({ party }) }),
  redraft: (number: string, rev: Rev) => call(`/api/deliverables/${number}/redraft?rev=${rev}`, { method: "POST" }),
  reset: () => call(`/api/reset`, { method: "POST" }),
  sample: () => call<{ text: string }>(`/api/extract/sample`).then((r) => r.text),
  extract: (text: string) => call<ExtractionResult>(`/api/extract`, { method: "POST", body: JSON.stringify({ text }) }),
};
