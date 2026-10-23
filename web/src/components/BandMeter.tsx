// Tolerance band meter: the declared ± band as a shaded zone and the measured delta as a marker.
import { bandGeometry } from "../lib/band";
import { fmtDelta } from "../lib/format";

export default function BandMeter({ delta, band, unit }: { delta: number; band: number; unit: string }) {
  const g = bandGeometry(delta, band);
  return (
    <div className="w-full" aria-label={`delta ${fmtDelta(delta)} against band ±${band}`}>
      <div className="relative h-5 rounded bg-paper ring-1 ring-rule overflow-hidden">
        <div className="absolute inset-y-0 left-1/2 w-px bg-graphite/40" />
        <div className="absolute inset-y-0 bg-good/15 border-x border-good/50" style={{ left: `${g.bandLeft}%`, width: `${g.bandWidth}%` }} />
        <div
          className={`absolute top-0.5 bottom-0.5 w-1.5 -ml-[3px] rounded-sm ${g.inside ? "bg-good" : "bg-signal"}`}
          style={{ left: `${g.marker}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between font-mono text-[11px] text-graphite tabular">
        <span>band ±{band} {unit}</span>
        <span className={g.inside ? "text-good" : "text-signal font-semibold"}>
          {fmtDelta(delta)} {unit}
        </span>
      </div>
    </div>
  );
}
