"""Run every contract check on every tie-point row and roll the results into one report."""

from __future__ import annotations

from pydantic import BaseModel

from .attest import AttestationResult, check_attestation
from .identity import IdentityResult, check_identity
from .impact import ImpactItem, resolve_line, trace_impact
from .models import Project, Status
from .reconcile import AttributeCheck, reconcile


class TiePointResult(BaseModel):
    id: str
    stream_tag: str
    description: str
    status: Status
    headline: str
    identity: IdentityResult
    conditions: list[AttributeCheck]
    attestation: AttestationResult
    attested_on_paper: bool


class Summary(BaseModel):
    total: int
    current: int
    drift: int
    orphaned: int
    ambiguous: int
    lapsed: int
    pending: int
    attested_on_paper: int
    deliverables_total: int
    deliverables_stale: int
    deliverables_unverifiable: int


class Report(BaseModel):
    project: str
    revision: str
    tie_points: list[TiePointResult]
    impacts: list[ImpactItem]
    summary: Summary


def _fmt(v: float | str | None) -> str:
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def _headline(identity: IdentityResult, conditions: list[AttributeCheck], att: AttestationResult) -> tuple[Status, str]:
    if identity.status in (Status.ORPHANED, Status.AMBIGUOUS):
        return identity.status, identity.reason
    drifted = [c for c in conditions if c.status == Status.DRIFT]
    if drifted:
        parts = []
        for c in drifted:
            label = c.attribute.replace("_", " ")
            if c.delta is not None:
                parts.append(f"{label} {_fmt(c.stated)} → {_fmt(c.current)} {c.unit}".strip() + f" (band ±{c.band:g})")
            else:
                parts.append(f"{label} {_fmt(c.stated)} → {_fmt(c.current)}")
        return Status.DRIFT, "; ".join(parts)
    if att.status == Status.LAPSED:
        revs = [f"{p.doc} Rev {p.attested_rev} → {p.current_rev}" for p in att.parties if p.status == Status.LAPSED]
        return Status.LAPSED, "conditions hold, but the attestation predates " + ", ".join(revs)
    if att.status == Status.PENDING:
        missing = [p.party for p in att.parties if p.status == Status.PENDING]
        return Status.PENDING, "waiting on " + " and ".join(missing) + " attestation"
    return Status.CURRENT, "matches the line list and both owners attested the current revisions"


def run_checks(project: Project) -> Report:
    results: list[TiePointResult] = []
    for tp in project.tie_points:
        identity = check_identity(tp, project.streams)
        line = resolve_line(tp, project)
        conditions = reconcile(tp, line)
        att = check_attestation(tp, project)
        status, headline = _headline(identity, conditions, att)
        results.append(
            TiePointResult(
                id=tp.id,
                stream_tag=tp.stream_tag,
                description=tp.description,
                status=status,
                headline=headline,
                identity=identity,
                conditions=conditions,
                attestation=att,
                attested_on_paper={a.party for a in tp.attestations} == {"upstream", "downstream"},
            )
        )
    impacts = trace_impact(project)
    count = lambda s: sum(1 for r in results if r.status == s)  # noqa: E731
    summary = Summary(
        total=len(results),
        current=count(Status.CURRENT),
        drift=count(Status.DRIFT),
        orphaned=count(Status.ORPHANED),
        ambiguous=count(Status.AMBIGUOUS),
        lapsed=sum(1 for r in results if r.attestation.status == Status.LAPSED),
        pending=sum(1 for r in results if r.attestation.status == Status.PENDING),
        attested_on_paper=sum(1 for r in results if r.attested_on_paper),
        deliverables_total=len(impacts),
        deliverables_stale=sum(1 for i in impacts if i.status == "stale"),
        deliverables_unverifiable=sum(1 for i in impacts if i.status == "unverifiable"),
    )
    return Report(project=project.name, revision=project.revision_label, tie_points=results, impacts=impacts, summary=summary)
