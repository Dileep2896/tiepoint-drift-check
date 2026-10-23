// The checker workspace: revision switch, summary, contract table and the selected row's detail.
import { useCallback, useEffect, useState } from "react";
import DetailPanel from "../components/DetailPanel";
import ImpactList from "../components/ImpactList";
import SummaryStrip from "../components/SummaryStrip";
import TiePointTable from "../components/TiePointTable";
import { api } from "../lib/api";
import type { DocRef, Report, Rev } from "../lib/types";

export default function Workspace() {
  const [rev, setRev] = useState<Rev>("C");
  const [report, setReport] = useState<Report | null>(null);
  const [docs, setDocs] = useState<DocRef[]>([]);
  const [selected, setSelected] = useState<string | null>("TP-01");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (r: Rev) => {
    const [rep, d] = await Promise.all([api.check(r), api.documents(r)]);
    setReport(rep);
    setDocs(d);
  }, []);

  useEffect(() => {
    load(rev).catch((e) => setError(String(e.message ?? e)));
  }, [rev, load]);

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await load(rev);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const row = report?.tie_points.find((t) => t.id === selected) ?? null;
  const rowImpacts = report?.impacts.filter((i) => i.deliverable.tie_point === selected) ?? [];

  return (
    <main className="mx-auto max-w-7xl px-4 sm:px-6 py-6 space-y-5">
      <div className="flex flex-wrap items-end gap-4">
        <div className="min-w-0">
          <div className="text-[11px] uppercase tracking-wider text-graphite font-medium">Interface register · two scopes</div>
          <h1 className="text-xl font-semibold tracking-tight">{report?.project ?? "Loading…"}</h1>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {docs.map((d) => (
              <span key={d.number} className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-sheet ring-1 ring-rule" title={`${d.title} · ${d.scope}`}>
                {d.number} <b>Rev {d.rev}</b>
              </span>
            ))}
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="inline-flex rounded-sheet ring-1 ring-rule bg-sheet p-0.5" role="tablist" aria-label="revision">
            {(["B", "C"] as Rev[]).map((r) => (
              <button
                key={r}
                role="tab"
                aria-selected={rev === r}
                onClick={() => setRev(r)}
                className={`px-3 py-1.5 text-sm rounded-[4px] font-medium ${rev === r ? "bg-ink text-sheet" : "text-graphite hover:text-ink"}`}
              >
                Rev {r} <span className="text-[11px] opacity-70">{r === "B" ? "FEL2 freeze" : "after process change"}</span>
              </button>
            ))}
          </div>
          <button onClick={() => act(api.reset)} disabled={busy} className="text-sm text-graphite hover:text-ink px-2 py-1.5 disabled:opacity-40">
            Reset
          </button>
        </div>
      </div>

      {error && <div className="rounded-sheet bg-signal/10 text-signal text-sm px-3 py-2 ring-1 ring-signal/30">{error}</div>}

      {report && (
        <>
          <SummaryStrip s={report.summary} />
          <div className="grid lg:grid-cols-[1fr_420px] gap-5 items-start">
            <div className="space-y-5 min-w-0">
              <TiePointTable rows={report.tie_points} selected={selected} onSelect={setSelected} />
              <div className="rounded-sheet bg-sheet ring-1 ring-rule p-4">
                <h2 className="font-semibold text-sm">Deliverables sized on tie-point values</h2>
                <p className="text-xs text-graphite">Every datasheet and calc that consumed an interface condition, checked against today's line list.</p>
                <ImpactList items={report.impacts} />
              </div>
            </div>
            {row && (
              <DetailPanel
                key={row.id + row.status}
                row={row}
                impacts={rowImpacts}
                busy={busy}
                onAccept={(tag) => act(() => api.accept(row.id, rev, tag))}
                onAttest={(party) => act(() => api.attest(row.id, party, rev))}
                onRedraft={(n) => act(() => api.redraft(n, rev))}
              />
            )}
          </div>
        </>
      )}
    </main>
  );
}
