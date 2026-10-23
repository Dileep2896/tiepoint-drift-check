import { bandGeometry } from "../src/lib/band";
import { fmtDelta, fmtValue, percent, statusTone } from "../src/lib/format";

describe("bandGeometry", () => {
  it("centres a zero delta inside the band", () => {
    const g = bandGeometry(0, 15);
    expect(g.marker).toBe(50);
    expect(g.inside).toBe(true);
    expect(g.bandLeft + g.bandWidth / 2).toBeCloseTo(50);
  });

  it("treats the band edge as inside", () => {
    expect(bandGeometry(15, 15).inside).toBe(true);
    expect(bandGeometry(15.01, 15).inside).toBe(false);
  });

  it("rescales so a large drift stays on the track", () => {
    const g = bandGeometry(75, 15);
    expect(g.inside).toBe(false);
    expect(g.marker).toBeGreaterThan(50);
    expect(g.marker).toBeLessThanOrEqual(100);
    expect(g.clipped).toBe(false);
  });

  it("handles a zero-width band", () => {
    const g = bandGeometry(0.09, 0);
    expect(g.inside).toBe(false);
    expect(g.bandWidth).toBeCloseTo(0);
  });
});

describe("format", () => {
  it("formats values and deltas", () => {
    expect(fmtValue(1025, "psig")).toBe("1,025 psig");
    expect(fmtValue(0.11)).toBe("0.11");
    expect(fmtValue(null)).toBe("n/a");
    expect(fmtDelta(75)).toBe("+75");
    expect(fmtDelta(-5)).toBe("−5");
    expect(fmtDelta(0.09)).toBe("+0.09");
  });

  it("maps statuses to tones", () => {
    expect(statusTone("current")).toBe("good");
    expect(statusTone("drift")).toBe("bad");
    expect(statusTone("ambiguous")).toBe("odd");
    expect(statusTone("lapsed")).toBe("warn");
  });

  it("computes percentages safely", () => {
    expect(percent(4, 10)).toBe(40);
    expect(percent(1, 0)).toBe(0);
  });
});
