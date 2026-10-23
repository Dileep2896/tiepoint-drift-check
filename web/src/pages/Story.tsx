// Story page: the problem, the failure, the decision, and the measured before -> after on the seed project.
import { animate, motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import StatusChip from "../components/StatusChip";
import type { Status, Summary } from "../lib/types";

interface StoryData {
  before: Summary;
  after: Summary;
  findings: { id: string; status: Status; headline: string }[];
}

const rise = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
};

function Counter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!inView) return;
    const c = animate(0, to, { duration: 1.2, ease: "easeOut", onUpdate: (x) => setV(Math.round(x)) });
    return () => c.stop();
  }, [inView, to]);
  return (
    <span ref={ref} className="tabular">
      {v}
      {suffix}
    </span>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return <div className="font-mono text-[11px] tracking-[0.18em] uppercase text-signal">{children}</div>;
}

function InterfaceDiagram() {
  // two scope blocks, a battery-limit line, and tie-points crossing it
  const tps = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
  return (
    <svg viewBox="0 0 560 220" className="w-full max-w-xl" role="img" aria-label="Two scopes joined by ten tie-points">
      <motion.rect x="10" y="20" width="220" height="180" rx="8" fill="#FBFAF6" stroke="#16191D" strokeWidth="1.5"
        initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }} />
      <motion.rect x="330" y="20" width="220" height="180" rx="8" fill="#FBFAF6" stroke="#16191D" strokeWidth="1.5"
        initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }} />
      <text x="24" y="44" fontFamily="IBM Plex Mono" fontSize="11" fill="#5C6168">SCOPE A · OWNER</text>
      <text x="24" y="62" fontFamily="IBM Plex Sans" fontSize="14" fontWeight="600" fill="#16191D">Inlet &amp; compression</text>
      <text x="344" y="44" fontFamily="IBM Plex Mono" fontSize="11" fill="#5C6168">SCOPE B · EPC</text>
      <text x="344" y="62" fontFamily="IBM Plex Sans" fontSize="14" fontWeight="600" fill="#16191D">Amine treating unit</text>
      <motion.line x1="280" y1="10" x2="280" y2="210" stroke="#1E3A5F" strokeWidth="1.2" strokeDasharray="5 5"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8, delay: 0.4 }} />
      <text x="286" y="20" fontFamily="IBM Plex Mono" fontSize="9" fill="#1E3A5F">BATTERY LIMIT</text>
      {tps.map((i) => {
        const y = 80 + i * 12;
        const bad = [0, 2, 3, 4, 6, 9].includes(i);
        return (
          <g key={i}>
            <motion.line x1="230" y1={y} x2="330" y2={y} stroke={bad ? "#C2410C" : "#0F766E"} strokeWidth="1.4"
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.4, delay: 0.9 + i * 0.07 }} />
            <motion.circle cx="280" cy={y} r="3.2" fill={bad ? "#C2410C" : "#0F766E"}
              initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 1.2 + i * 0.07 }} />
          </g>
        );
      })}
    </svg>
  );
}

const TIMELINE = [
  { tag: "FEL2 freeze", text: "Tie-point table written. TP-01 sour gas at the battery limit: 950 psig. Both owners sign." },
  { tag: "Line list Rev C", text: "Upstream raises compressor discharge. The line list now says 1,025 psig." },
  { tag: "Table untouched", text: "The tie-point row still reads 950. Both signatures still look valid." },
  { tag: "Downstream sizing", text: "The contactor datasheet is sized against 950 psig, a value that no longer exists." },
  { tag: "Commissioning", text: "The mismatch finally surfaces, months later, in steel." },
];

const CHECKS = [
  { n: "01", title: "Stream identity", body: "Each row maps to exactly one PFD stream tag. Renumbered or split streams fail loudly, with the likely replacement suggested." },
  { n: "02", title: "Condition reconciliation", body: "Pressure, temperature, phase and vapor fraction must match the current line list inside the band both scopes declared for that tie-point." },
  { n: "03", title: "Owner attestation", body: "A row is approved only while both owners' signatures point at the current revision of their source document. Any rev bump lapses it." },
];

export default function Story() {
  const [data, setData] = useState<StoryData | null>(null);
  useEffect(() => {
    fetch("/api/story").then((r) => r.json()).then(setData).catch(() => undefined);
  }, []);
  const a = data?.after;
  const b = data?.before;

  return (
    <main className="mx-auto max-w-6xl px-4 sm:px-6 pb-24">
      {/* 1. hero */}
      <section className="pt-14 pb-16 grid lg:grid-cols-[1.1fr_1fr] gap-10 items-center">
        <div>
          <Eyebrow>Capital projects · interface control</Eyebrow>
          <motion.h1 className="mt-3 text-4xl sm:text-5xl font-semibold tracking-tight leading-[1.05]"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            Two scopes. One tie-point table. Nobody re-checks it.
          </motion.h1>
          <motion.p className="mt-5 text-lg text-graphite max-w-xl" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            When a plant is split between an owner and an EPC, the tie-point table is the contract at the battery limit.
            It gets written at the FEL2 freeze, signed, and then quietly goes stale while the line list keeps moving.
          </motion.p>
        </div>
        <InterfaceDiagram />
      </section>

      {/* 2. the failure */}
      <section className="py-14 border-t border-rule">
        <motion.div {...rise}>
          <Eyebrow>The failure</Eyebrow>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight max-w-2xl">A process condition changes after the freeze. The table doesn't.</h2>
          <p className="mt-3 text-graphite max-w-2xl">
            Engineering briefs on FEL2 tie-points describe the same pattern: the downstream team sizes equipment against an interface
            condition that no longer exists, and the mismatch surfaces during commissioning.
          </p>
        </motion.div>
        <ol className="mt-8 relative border-l-2 border-rule ml-2 space-y-6">
          {TIMELINE.map((t, i) => (
            <motion.li key={t.tag} className="pl-6 relative" {...rise} transition={{ ...rise.transition, delay: i * 0.12 }}>
              <span className={`absolute -left-[7px] top-1.5 h-3 w-3 rounded-full ${i === 0 ? "bg-good" : i >= 2 ? "bg-signal" : "bg-blueprint"}`} />
              <div className="font-mono text-xs text-graphite">{t.tag}</div>
              <div className="text-base">{t.text}</div>
            </motion.li>
          ))}
        </ol>
      </section>

      {/* 3. the decision */}
      <section className="py-14 border-t border-rule">
        <motion.div {...rise}>
          <Eyebrow>The decision</Eyebrow>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight max-w-2xl">Treat the table as a typed contract. The PFD and line list are the type system.</h2>
        </motion.div>
        <div className="mt-8 grid md:grid-cols-3 gap-4">
          {CHECKS.map((c, i) => (
            <motion.div key={c.n} className="rounded-sheet bg-sheet ring-1 ring-rule p-5" {...rise} transition={{ ...rise.transition, delay: i * 0.12 }}>
              <div className="font-mono text-sm text-signal">CHECK {c.n}</div>
              <div className="mt-1 font-semibold">{c.title}</div>
              <p className="mt-2 text-sm text-graphite">{c.body}</p>
            </motion.div>
          ))}
        </div>
        <motion.div className="mt-6 rounded-sheet bg-blueprint text-sheet p-5 grid md:grid-cols-2 gap-5" {...rise}>
          <div>
            <div className="font-mono text-[11px] tracking-widest uppercase opacity-70">Why this feature</div>
            <p className="mt-1 text-sm">
              Every input is project data both scopes already own: a PFD, a line list, a tie-point table. The checks are deterministic,
              and a drift caught at FEL2 is a redraft, not a field change. On top sits an impact trace: every datasheet sized on a stale value is named.
            </p>
          </div>
          <div>
            <div className="font-mono text-[11px] tracking-widest uppercase opacity-70">What I didn't build</div>
            <p className="mt-1 text-sm">
              A piping-code errata checker (does each line still fit its class after a code revision). Real pain, but it depends on licensed
              allowable-stress tables that a public demo can't ship honestly.
            </p>
          </div>
        </motion.div>
      </section>

      {/* 4. before -> after on the real seed */}
      <section className="py-14 border-t border-rule">
        <motion.div {...rise}>
          <Eyebrow>Before → after, on the seed project</Eyebrow>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">What the table says vs what is true.</h2>
        </motion.div>
        {a && (
          <div className="mt-8 grid md:grid-cols-2 gap-5">
            <motion.div className="rounded-sheet bg-sheet ring-1 ring-rule p-6" {...rise}>
              <div className="text-sm text-graphite">Spreadsheet view, Rev C</div>
              <div className="mt-1 text-6xl font-semibold text-good"><Counter to={a.attested_on_paper} />/{a.total}</div>
              <div className="mt-1 text-sm">tie-points show two signatures</div>
            </motion.div>
            <motion.div className="rounded-sheet bg-sheet ring-2 ring-signal p-6" {...rise} transition={{ ...rise.transition, delay: 0.2 }}>
              <div className="text-sm text-graphite">After the three checks, Rev C</div>
              <div className="mt-1 text-6xl font-semibold text-signal"><Counter to={a.current} />/{a.total}</div>
              <div className="mt-1 text-sm">are actually current</div>
            </motion.div>
          </div>
        )}
        {data && (
          <motion.ul className="mt-6 rounded-sheet bg-sheet ring-1 ring-rule divide-y divide-rule/70" {...rise}>
            {data.findings.map((f) => (
              <li key={f.id} className="px-4 py-2.5 flex items-center gap-3 text-sm">
                <span className="font-mono font-semibold w-14">{f.id}</span>
                <StatusChip status={f.status} />
                <span className="text-graphite text-xs">{f.headline}</span>
              </li>
            ))}
          </motion.ul>
        )}
      </section>

      {/* 5. impact */}
      <section className="py-14 border-t border-rule">
        <motion.div {...rise}>
          <Eyebrow>Measured impact</Eyebrow>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">Caught before issue, not at commissioning.</h2>
          <p className="mt-2 text-sm text-graphite">Measured by the engine on the bundled seed project (Rev C vs its own FEL2 baseline). Not customer data.</p>
        </motion.div>
        {a && b && (
          <div className="mt-8 grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: "condition drifts", v: a.drift, base: b.drift },
              { label: "orphaned rows", v: a.orphaned, base: b.orphaned },
              { label: "ambiguous rows", v: a.ambiguous, base: b.ambiguous },
              { label: "lapsed sign-offs", v: a.lapsed, base: b.lapsed },
              { label: `of ${a.deliverables_total} deliverables stale`, v: a.deliverables_stale, base: b.deliverables_stale },
            ].map((m, i) => (
              <motion.div key={m.label} className="rounded-sheet bg-sheet ring-1 ring-rule p-4" {...rise} transition={{ ...rise.transition, delay: i * 0.08 }}>
                <div className="text-4xl font-semibold text-signal"><Counter to={m.v} /></div>
                <div className="text-sm mt-1">{m.label}</div>
                <div className="text-[11px] font-mono text-graphite mt-1">Rev B baseline: {m.base}</div>
              </motion.div>
            ))}
          </div>
        )}
        <motion.div className="mt-10 flex flex-wrap gap-3" {...rise}>
          <Link to="/" className="px-4 py-2 rounded-sheet bg-ink text-sheet font-semibold text-sm hover:bg-blueprint">Open the workspace</Link>
          <Link to="/extract" className="px-4 py-2 rounded-sheet ring-1 ring-ink font-semibold text-sm hover:bg-ink hover:text-sheet">Try extraction</Link>
        </motion.div>
      </section>
    </main>
  );
}
