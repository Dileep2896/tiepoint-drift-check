// Extraction: paste a tie-point schedule (PDF text) and get typed rows with a source line per value.
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtValue } from "../lib/format";
import type { ExtractionResult } from "../lib/types";

export default function Extract() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    api.sample().then(setText).catch(() => undefined);
  }, []);

  const run = async () => {
    setBusy(true);
    try {
      setResult(await api.extract(text));
    } finally {
      setBusy(false);
    }
  };

  const lines = text.split("\n");
  return (
    <main className="mx-auto max-w-7xl px-4 sm:px-6 py-6 grid lg:grid-cols-2 gap-5 items-start">
      <section className="rounded-sheet bg-sheet ring-1 ring-rule p-4">
        <div className="flex items-center gap-2 mb-2">
          <h1 className="font-semibold">Tie-point schedule (pasted from PDF)</h1>
          <button onClick={run} disabled={busy || !text.trim()} className="ml-auto text-sm font-semibold px-3 py-1.5 rounded-sheet bg-ink text-sheet hover:bg-blueprint disabled:opacity-40">
            {busy ? "Extracting…" : "Extract rows"}
          </button>
        </div>
        {result ? (
          <ol className="font-mono text-[12px] leading-5 bg-paper rounded p-2 overflow-x-auto">
            {lines.map((l, i) => {
              const n = i + 1;
              const isErr = result.errors.some((e) => e.source_line === n);
              const isRow = result.rows.some((r) => r.source_line === n);
              return (
                <li key={n} className={`whitespace-pre flex ${hover === n ? "bg-blueprint/10" : ""} ${isErr ? "bg-signal/10" : ""}`}>
                  <span className="w-7 shrink-0 text-right pr-2 text-graphite/70 select-none">{n}</span>
                  <span className={isRow || isErr ? "" : "text-graphite/60"}>{l || " "}</span>
                </li>
              );
            })}
          </ol>
        ) : (
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={16} className="w-full font-mono text-[12px] leading-5 bg-paper rounded p-2 ring-1 ring-rule" />
        )}
        {result && (
          <button onClick={() => setResult(null)} className="mt-2 text-xs text-graphite hover:text-ink">Edit text</button>
        )}
      </section>

      <section className="rounded-sheet bg-sheet ring-1 ring-rule p-4 min-w-0">
        <h2 className="font-semibold">Typed rows</h2>
        {!result ? (
          <p className="text-sm text-graphite mt-1">Each extracted value keeps the line it came from. Rows that fail validation are listed, never dropped.</p>
        ) : (
          <>
            <p className="text-xs text-graphite mt-0.5">
              {result.rows.length} rows · {result.errors.length} rejected · {result.lines_scanned} lines scanned · engine: {result.engine === "llm" ? "LLM + validator" : "rule parser + validator"}
            </p>
            <div className="overflow-x-auto mt-2">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wider text-graphite border-b border-rule">
                    <th className="py-1.5 pr-2 font-medium">Line</th>
                    <th className="py-1.5 pr-2 font-medium">TP</th>
                    <th className="py-1.5 pr-2 font-medium">Stream</th>
                    <th className="py-1.5 pr-2 font-medium text-right">P</th>
                    <th className="py-1.5 pr-2 font-medium text-right">T</th>
                    <th className="py-1.5 pr-2 font-medium">Ph</th>
                    <th className="py-1.5 font-medium text-right">VF</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((r) => (
                    <tr key={r.id} onMouseEnter={() => setHover(r.source_line)} onMouseLeave={() => setHover(null)} className="border-b border-rule/60 font-mono text-xs tabular">
                      <td className="py-1.5 pr-2 text-graphite">L{r.source_line}</td>
                      <td className="py-1.5 pr-2 font-semibold">{r.id}</td>
                      <td className="py-1.5 pr-2">{r.stream_tag}</td>
                      <td className="py-1.5 pr-2 text-right">{fmtValue(r.pressure_psig)}</td>
                      <td className="py-1.5 pr-2 text-right">{fmtValue(r.temperature_f)}</td>
                      <td className="py-1.5 pr-2">{r.phase}</td>
                      <td className="py-1.5 text-right">{r.vapor_fraction.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {result.errors.map((e) => (
              <div key={e.source_line} className="mt-3 rounded bg-signal/10 ring-1 ring-signal/30 px-3 py-2 text-sm" onMouseEnter={() => setHover(e.source_line)} onMouseLeave={() => setHover(null)}>
                <span className="font-mono text-xs font-semibold text-signal">L{e.source_line} rejected</span> <span className="text-signal">{e.reason}</span>
                <div className="font-mono text-[11px] text-graphite truncate">{e.text}</div>
              </div>
            ))}
          </>
        )}
      </section>
    </main>
  );
}
