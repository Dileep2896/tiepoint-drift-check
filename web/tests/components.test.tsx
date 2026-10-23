import { fireEvent, render, screen } from "@testing-library/react";
import DetailPanel from "../src/components/DetailPanel";
import SummaryStrip from "../src/components/SummaryStrip";
import TiePointTable from "../src/components/TiePointTable";
import type { Summary, TiePointResult } from "../src/lib/types";

const summary: Summary = {
  total: 10, current: 4, drift: 4, orphaned: 1, ambiguous: 1, lapsed: 6, pending: 0,
  attested_on_paper: 10, deliverables_total: 6, deliverables_stale: 4, deliverables_unverifiable: 0,
};

function row(over: Partial<TiePointResult> = {}): TiePointResult {
  return {
    id: "TP-01", stream_tag: "S-101", description: "Sour gas to amine contactor", status: "drift",
    headline: "pressure 950 -> 1025 psig (band ±15)",
    identity: { status: "pass", matched_tag: "S-101", suggestion: null, candidates: [], reason: "S-101 found once in the current PFD" },
    conditions: [
      { attribute: "pressure", stated: 950, current: 1025, delta: 75, band: 15, unit: "psig", status: "drift" },
      { attribute: "temperature", stated: 120, current: 128, delta: 8, band: 10, unit: "°F", status: "pass" },
      { attribute: "phase", stated: "V", current: "V", delta: null, band: null, unit: "", status: "pass" },
      { attribute: "vapor_fraction", stated: 1, current: 1, delta: 0, band: 0.05, unit: "", status: "pass" },
    ],
    attestation: {
      status: "lapsed",
      parties: [
        { party: "upstream", doc: "LL-200", by: "J. Okafor", attested_rev: "B", current_rev: "C", status: "lapsed" },
        { party: "downstream", doc: "ATU-300", by: "M. Brandt", attested_rev: "A", current_rev: "A", status: "current" },
      ],
    },
    attested_on_paper: true,
    ...over,
  };
}

describe("SummaryStrip", () => {
  it("shows paper vs actual", () => {
    render(<SummaryStrip s={summary} />);
    expect(screen.getByText("10/10")).toBeInTheDocument();
    expect(screen.getByText("4/10")).toBeInTheDocument();
    expect(screen.getByText("4/6")).toBeInTheDocument();
  });
});

describe("TiePointTable", () => {
  it("renders rows and selects on click", () => {
    const onSelect = vi.fn();
    render(<TiePointTable rows={[row(), row({ id: "TP-02", status: "current", headline: "ok" })]} selected={null} onSelect={onSelect} />);
    expect(screen.getByText("Drift")).toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    fireEvent.click(screen.getByText("TP-02"));
    expect(onSelect).toHaveBeenCalledWith("TP-02");
  });
});

describe("DetailPanel", () => {
  const noop = () => undefined;

  it("offers accept on drift and shows the lapsed revision", () => {
    const onAccept = vi.fn();
    render(<DetailPanel row={row()} impacts={[]} busy={false} onAccept={onAccept} onAttest={noop} onRedraft={noop} />);
    expect(screen.getByText("current Rev C")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Accept current line-list values"));
    expect(onAccept).toHaveBeenCalledWith(undefined);
  });

  it("requires a stream choice when ambiguous", () => {
    const onAccept = vi.fn();
    const amb = row({
      status: "ambiguous",
      identity: { status: "ambiguous", matched_tag: null, suggestion: null, candidates: ["S-104A", "S-104B"], reason: "split" },
    });
    render(<DetailPanel row={amb} impacts={[]} busy={false} onAccept={onAccept} onAttest={noop} onRedraft={noop} />);
    const btn = screen.getByText("Accept current line-list values");
    expect(btn).toBeDisabled();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "S-104B" } });
    fireEvent.click(btn);
    expect(onAccept).toHaveBeenCalledWith("S-104B");
  });

  it("offers re-attest only once conditions pass", () => {
    const onAttest = vi.fn();
    const lapsed = row({
      status: "lapsed",
      conditions: row().conditions.map((c) => ({ ...c, status: "pass" as const })),
    });
    render(<DetailPanel row={lapsed} impacts={[]} busy={false} onAccept={noop} onAttest={onAttest} onRedraft={noop} />);
    fireEvent.click(screen.getByText("Attest Rev C"));
    expect(onAttest).toHaveBeenCalledWith("upstream");
    expect(screen.queryByText("Accept current line-list values")).toBeNull();
  });
});
