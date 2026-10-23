// Status pill used across the table, detail panel and story page.
import { STATUS_LABEL, statusTone } from "../lib/format";
import type { Status } from "../lib/types";

const TONE = {
  good: "bg-good/10 text-good ring-good/30",
  bad: "bg-signal/10 text-signal ring-signal/30",
  warn: "bg-lapsed/10 text-lapsed ring-lapsed/30",
  odd: "bg-orphan/10 text-orphan ring-orphan/30",
};

export default function StatusChip({ status, label }: { status: Status; label?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${TONE[statusTone(status)]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" style={{ backgroundColor: "currentColor" }} />
      {label ?? STATUS_LABEL[status]}
    </span>
  );
}
