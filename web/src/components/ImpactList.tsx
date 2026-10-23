// Downstream deliverables and whether the value they were sized on still holds.
import { fmtValue } from "../lib/format";
import type { ImpactItem } from "../lib/types";
import StatusChip from "./StatusChip";

export default function ImpactList({
  items,
  onRedraft,
  busy,
}: {
  items: ImpactItem[];
  onRedraft?: (number: string) => void;
  busy?: boolean;
}) {
  return (
    <ul className="divide-y divide-rule/70">
      {items.map((i) => (
        <li key={i.deliverable.number} className="py-2.5 flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold">{i.deliverable.number}</span>
              <span className="text-[11px] text-graphite">{i.deliverable.discipline} · {i.deliverable.tie_point}</span>
            </div>
            <div className="text-sm">{i.deliverable.title}</div>
            <div className="text-xs text-graphite font-mono tabular">
              sized on {fmtValue(i.deliverable.sized_on)} · now {fmtValue(i.current)}
            </div>
          </div>
          {i.status === "stale" ? (
            <div className="flex flex-col items-end gap-1.5">
              <StatusChip status="drift" label="Stale" />
              {onRedraft && (
                <button disabled={busy} onClick={() => onRedraft(i.deliverable.number)} className="text-xs font-medium text-blueprint hover:underline disabled:opacity-40">
                  Mark redrafted
                </button>
              )}
            </div>
          ) : i.status === "unverifiable" ? (
            <StatusChip status="ambiguous" label="Unverifiable" />
          ) : (
            <StatusChip status="pass" label="Holds" />
          )}
        </li>
      ))}
    </ul>
  );
}
