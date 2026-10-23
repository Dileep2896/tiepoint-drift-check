// Geometry for the tolerance band meter: where the band sits and where the measured delta lands.
export interface BandGeometry {
  bandLeft: number; // % from left where the band starts
  bandWidth: number; // % width of the band
  marker: number; // % position of the delta marker, clamped to the track
  inside: boolean;
  clipped: boolean; // true when the delta is off the visible scale
}

/** Scale shows ±(3 x band), or ±(1.25 x |delta|) when the delta is further out, so the marker stays visible. */
export function bandGeometry(delta: number, band: number): BandGeometry {
  const half = Math.max(band * 3, Math.abs(delta) * 1.25, 1e-6);
  const toPct = (x: number) => ((x + half) / (2 * half)) * 100;
  const raw = toPct(delta);
  const marker = Math.min(100, Math.max(0, raw));
  return {
    bandLeft: toPct(-band),
    bandWidth: toPct(band) - toPct(-band),
    marker,
    inside: Math.abs(delta) <= band + 1e-9,
    clipped: raw !== marker,
  };
}
