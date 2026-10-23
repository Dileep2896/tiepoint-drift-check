// Types mirroring the engine's Pydantic report models.
export type Status = "pass" | "drift" | "orphaned" | "ambiguous" | "lapsed" | "pending" | "current";
export type Rev = "B" | "C";
export type Party = "upstream" | "downstream";

export interface AttributeCheck {
  attribute: "pressure" | "temperature" | "phase" | "vapor_fraction";
  stated: number | string;
  current: number | string | null;
  delta: number | null;
  band: number | null;
  unit: string;
  status: Status;
}

export interface PartyAttestation {
  party: Party;
  doc: string;
  by: string | null;
  attested_rev: string | null;
  current_rev: string | null;
  status: Status;
}

export interface TiePointResult {
  id: string;
  stream_tag: string;
  description: string;
  status: Status;
  headline: string;
  identity: { status: Status; matched_tag: string | null; suggestion: string | null; candidates: string[]; reason: string };
  conditions: AttributeCheck[];
  attestation: { status: Status; parties: PartyAttestation[] };
  attested_on_paper: boolean;
}

export interface Deliverable {
  number: string;
  title: string;
  tie_point: string;
  attribute: AttributeCheck["attribute"];
  sized_on: number | string;
  discipline: string;
}

export interface ImpactItem {
  deliverable: Deliverable;
  current: number | string | null;
  status: "ok" | "stale" | "unverifiable";
  reason: string;
}

export interface Summary {
  total: number;
  current: number;
  drift: number;
  orphaned: number;
  ambiguous: number;
  lapsed: number;
  pending: number;
  attested_on_paper: number;
  deliverables_total: number;
  deliverables_stale: number;
  deliverables_unverifiable: number;
}

export interface Report {
  project: string;
  revision: string;
  tie_points: TiePointResult[];
  impacts: ImpactItem[];
  summary: Summary;
}

export interface DocRef {
  number: string;
  title: string;
  rev: string;
  scope: string;
}

export interface ExtractedRow {
  id: string;
  stream_tag: string;
  description: string;
  pressure_psig: number;
  temperature_f: number;
  phase: string;
  vapor_fraction: number;
  source_line: number;
}

export interface ExtractionResult {
  engine: "rules" | "llm";
  rows: ExtractedRow[];
  errors: { source_line: number; text: string; reason: string }[];
  lines_scanned: number;
}
