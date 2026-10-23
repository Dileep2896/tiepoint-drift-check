// The headline comparison: what the table claims (attested on paper) vs what is actually current.
import type { Summary } from "../lib/types";

function Cell({ label, value, tone, sub }: { label: string; value: string; tone?: string; sub?: string }) {
  return (
    <div className="px-4 py-3 border-r last:border-r-0 border-rule min-w-[120px]">
      <div className="text-[11px] uppercase tracking-wider text-graphite font-medium">{label}</div>
      <div className={`mt-0.5 text-2xl font-semibold tabular ${tone ?? ""}`}>{value}</div>
      {sub && <div className="text-[11px] text-graphite">{sub}</div>}
    </div>
  );
}

export default function SummaryStrip({ s }: { s: Summary }) {
  return (
    <div className="flex flex-wrap rounded-sheet bg-sheet ring-1 ring-rule overflow-hidden" data-testid="summary">
      <Cell label="Attested on paper" value={`${s.attested_on_paper}/${s.total}`} sub="what the table says" />
      <Cell label="Actually current" value={`${s.current}/${s.total}`} tone={s.current === s.total ? "text-good" : "text-signal"} sub="all three checks pass" />
      <Cell label="Drift" value={String(s.drift)} tone={s.drift ? "text-signal" : ""} sub="outside tolerance band" />
      <Cell label="Orphaned" value={String(s.orphaned)} tone={s.orphaned ? "text-orphan" : ""} sub="stream tag gone" />
      <Cell label="Ambiguous" value={String(s.ambiguous)} tone={s.ambiguous ? "text-orphan" : ""} sub="maps to 2+ streams" />
      <Cell label="Lapsed sign-offs" value={String(s.lapsed)} tone={s.lapsed ? "text-lapsed" : ""} sub="source doc revised" />
      <Cell label="Stale deliverables" value={`${s.deliverables_stale}/${s.deliverables_total}`} tone={s.deliverables_stale ? "text-signal" : ""} sub="sized on old values" />
    </div>
  );
}
