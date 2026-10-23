// Detail for one tie-point: the three checks side by side, plus the resolve actions.
import { useState } from "react";
import { ATTRIBUTE_LABEL, fmtValue } from "../lib/format";
import type { ImpactItem, Party, TiePointResult } from "../lib/types";
import BandMeter from "./BandMeter";
import ImpactList from "./ImpactList";
import StatusChip from "./StatusChip";

interface Props {
  row: TiePointResult;
  impacts: ImpactItem[];
  busy: boolean;
  onAccept: (streamTag?: string) => void;
  onAttest: (party: Party) => void;
  onRedraft: (number: string) => void;
}

function Section({ n, title, status, children }: { n: number; title: string; status: TiePointResult["status"]; children: React.ReactNode }) {
  return (
    <section className="py-4 border-b border-rule last:border-b-0">
      <div className="flex items-center gap-2 mb-2.5">
        <span className="font-mono text-[11px] text-graphite">CHECK {n}</span>
        <h3 className="font-semibold text-sm">{title}</h3>
        <span className="ml-auto"><StatusChip status={status} /></span>
      </div>
      {children}
    </section>
  );
}

export default function DetailPanel({ row, impacts, busy, onAccept, onAttest, onRedraft }: Props) {
  const [choice, setChoice] = useState<string>("");
  const conditionStatus = row.conditions.some((c) => c.status === "drift")
    ? "drift"
    : row.conditions.some((c) => c.status === "orphaned")
      ? "orphaned"
      : "pass";
  const needsChoice = row.identity.status === "ambiguous";
  const canAccept = row.status !== "current" && row.status !== "lapsed" && row.status !== "pending";
  return (
    <aside className="rounded-sheet bg-sheet ring-1 ring-rule p-5" data-testid="detail">
      <div className="flex items-baseline gap-3">
        <h2 className="font-mono text-lg font-semibold">{row.id}</h2>
        <span className="font-mono text-sm text-graphite">{row.stream_tag}</span>
        <span className="ml-auto"><StatusChip status={row.status} /></span>
      </div>
      <p className="text-sm mt-0.5">{row.description}</p>
      <p className="text-xs text-graphite mt-2">{row.headline}</p>

      <Section n={1} title="Stream identity" status={row.identity.status}>
        <p className="text-sm text-graphite">{row.identity.reason}</p>
      </Section>

      <Section n={2} title="Condition reconciliation" status={conditionStatus}>
        <div className="space-y-3">
          {row.conditions.map((c) => (
            <div key={c.attribute} className="grid grid-cols-[110px_1fr] gap-3 items-center">
              <div>
                <div className="text-xs font-medium">{ATTRIBUTE_LABEL[c.attribute]}</div>
                <div className="font-mono text-[11px] text-graphite tabular">
                  {fmtValue(c.stated)} → <span className={c.status === "drift" ? "text-signal font-semibold" : ""}>{fmtValue(c.current)}</span>
                </div>
              </div>
              {c.delta !== null && c.band !== null ? (
                <BandMeter delta={c.delta} band={c.band} unit={c.unit} />
              ) : (
                <div className={`text-xs font-mono ${c.status === "drift" ? "text-signal font-semibold" : "text-graphite"}`}>
                  {c.status === "drift" ? `changed: ${c.stated} → ${c.current}` : c.status === "orphaned" ? "no current line-list entry" : "matches"}
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      <Section n={3} title="Owner attestation" status={row.attestation.status}>
        <div className="space-y-2">
          {row.attestation.parties.map((p) => (
            <div key={p.party} className="flex items-center gap-3 text-sm">
              <div className="min-w-0 flex-1">
                <div className="font-medium capitalize">{p.party}</div>
                <div className="text-xs text-graphite truncate">{p.by ?? "not attested"}</div>
              </div>
              <div className="font-mono text-xs tabular text-right">
                {p.doc} attested Rev {p.attested_rev ?? "–"}
                <br />
                <span className={p.status === "lapsed" ? "text-lapsed font-semibold" : "text-graphite"}>current Rev {p.current_rev}</span>
              </div>
              {p.status !== "current" && row.identity.status === "pass" && conditionStatus === "pass" && (
                <button disabled={busy} onClick={() => onAttest(p.party)} className="text-xs font-semibold px-2.5 py-1 rounded-sheet ring-1 ring-ink hover:bg-ink hover:text-sheet disabled:opacity-40">
                  Attest Rev {p.current_rev}
                </button>
              )}
            </div>
          ))}
        </div>
      </Section>

      {canAccept && (
        <div className="pt-4 flex flex-wrap items-center gap-2">
          {needsChoice && (
            <select value={choice} onChange={(e) => setChoice(e.target.value)} className="text-sm font-mono rounded-sheet ring-1 ring-rule bg-sheet px-2 py-1.5">
              <option value="">choose stream…</option>
              {row.identity.candidates.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          )}
          <button
            disabled={busy || (needsChoice && !choice)}
            onClick={() => onAccept(needsChoice ? choice : undefined)}
            className="text-sm font-semibold px-3 py-1.5 rounded-sheet bg-ink text-sheet hover:bg-blueprint disabled:opacity-40"
          >
            {row.identity.suggestion ? `Re-point to ${row.identity.suggestion} and accept` : "Accept current line-list values"}
          </button>
          <span className="text-xs text-graphite">Both sign-offs reset; owners re-attest.</span>
        </div>
      )}

      {impacts.length > 0 && (
        <div className="pt-4">
          <h3 className="text-[11px] uppercase tracking-wider text-graphite font-medium mb-1">Downstream deliverables</h3>
          <ImpactList items={impacts} onRedraft={onRedraft} busy={busy} />
        </div>
      )}
    </aside>
  );
}
