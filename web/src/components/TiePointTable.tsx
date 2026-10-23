// The tie-point contract table: one row per interface, status from the three checks.
import { fmtValue } from "../lib/format";
import type { TiePointResult } from "../lib/types";
import StatusChip from "./StatusChip";

export default function TiePointTable({
  rows,
  selected,
  onSelect,
}: {
  rows: TiePointResult[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="rounded-sheet bg-sheet ring-1 ring-rule overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-wider text-graphite border-b border-rule">
            <th className="px-3 py-2 font-medium">Tie-point</th>
            <th className="px-3 py-2 font-medium">Stream</th>
            <th className="px-3 py-2 font-medium">Service</th>
            <th className="px-3 py-2 font-medium text-right">P psig</th>
            <th className="px-3 py-2 font-medium text-right">T °F</th>
            <th className="px-3 py-2 font-medium">Ph</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 font-medium">Finding</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const p = r.conditions.find((c) => c.attribute === "pressure")!;
            const t = r.conditions.find((c) => c.attribute === "temperature")!;
            const ph = r.conditions.find((c) => c.attribute === "phase")!;
            return (
              <tr
                key={r.id}
                onClick={() => onSelect(r.id)}
                className={`border-b last:border-b-0 border-rule/70 cursor-pointer transition-colors ${
                  selected === r.id ? "bg-blueprint/[0.06]" : "hover:bg-paper/70"
                }`}
              >
                <td className="px-3 py-2.5 font-mono font-semibold">{r.id}</td>
                <td className="px-3 py-2.5 font-mono text-graphite">{r.stream_tag}</td>
                <td className="px-3 py-2.5 max-w-[220px] truncate">{r.description}</td>
                <td className={`px-3 py-2.5 text-right font-mono tabular ${p.status === "drift" ? "text-signal font-semibold" : ""}`}>{fmtValue(p.stated)}</td>
                <td className={`px-3 py-2.5 text-right font-mono tabular ${t.status === "drift" ? "text-signal font-semibold" : ""}`}>{fmtValue(t.stated)}</td>
                <td className={`px-3 py-2.5 font-mono ${ph.status === "drift" ? "text-signal font-semibold" : ""}`}>{String(ph.stated)}</td>
                <td className="px-3 py-2.5"><StatusChip status={r.status} /></td>
                <td className="px-3 py-2.5 text-graphite text-xs max-w-[340px]">{r.headline}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
