"""Repository for the mutable contract state (tie-point rows, deliverables) over the seeded documents."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from .impact import resolve_line
from .identity import check_identity
from .models import Attestation, Deliverable, Party, Project, Status, TiePoint
from .seed import DOWN_PROCESS, UP_PROCESS, UP_UTIL, build_project


class NotFound(KeyError):
    pass


class Conflict(ValueError):
    pass


class Repository(Protocol):
    def project(self, rev: str) -> Project: ...
    def accept(self, tp_id: str, rev: str, stream_tag: str | None = None) -> TiePoint: ...
    def attest(self, tp_id: str, party: Party, rev: str, by: str | None = None) -> TiePoint: ...
    def redraft(self, number: str, rev: str) -> Deliverable: ...
    def reset(self) -> None: ...


class InMemoryRepository:
    """Holds one tie-point table shared by both revisions; documents/streams/lines come from the seed."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        base = build_project("B")
        self._tie_points = [t.model_copy(deep=True) for t in base.tie_points]
        self._deliverables = [d.model_copy(deep=True) for d in base.deliverables]

    def project(self, rev: str) -> Project:
        p = build_project(rev)
        p.tie_points = [t.model_copy(deep=True) for t in self._tie_points]
        p.deliverables = [d.model_copy(deep=True) for d in self._deliverables]
        return p

    def _tp(self, tp_id: str) -> TiePoint:
        tp = next((t for t in self._tie_points if t.id == tp_id), None)
        if tp is None:
            raise NotFound(tp_id)
        return tp

    def accept(self, tp_id: str, rev: str, stream_tag: str | None = None) -> TiePoint:
        """Adopt the current line-list conditions; both attestations reset to pending."""
        tp = self._tp(tp_id)
        project = self.project(rev)
        ident = check_identity(tp, project.streams)
        if stream_tag is not None:
            if stream_tag not in ([ident.matched_tag] if ident.matched_tag else []) + ident.candidates:
                raise Conflict(f"{stream_tag} is not a candidate for {tp_id}")
            tag = stream_tag
        elif ident.status == Status.AMBIGUOUS:
            raise Conflict(f"{tp_id} is ambiguous; choose one of {', '.join(ident.candidates)}")
        else:
            tag = ident.matched_tag or ident.suggestion
        line = next((ln for ln in project.lines if ln.stream_tag == tag), None) if tag else resolve_line(tp, project)
        if line is None:
            raise Conflict(f"{tp_id} has no current stream to accept")
        tp.stream_tag = line.stream_tag
        tp.pressure_psig = line.pressure_psig
        tp.temperature_f = line.temperature_f
        tp.phase = line.phase
        tp.vapor_fraction = line.vapor_fraction
        tp.attestations = []
        return tp.model_copy(deep=True)

    def attest(self, tp_id: str, party: Party, rev: str, by: str | None = None) -> TiePoint:
        tp = self._tp(tp_id)
        project = self.project(rev)
        doc_no = tp.upstream_doc if party == "upstream" else tp.downstream_doc
        doc = project.doc(doc_no)
        if doc is None:
            raise NotFound(doc_no)
        default_by = (UP_UTIL if doc_no == "UT-400" else UP_PROCESS) if party == "upstream" else DOWN_PROCESS
        tp.attestations = [a for a in tp.attestations if a.party != party]
        tp.attestations.append(Attestation(party=party, by=by or default_by, doc=doc_no, rev=doc.rev, on=date.today().isoformat()))
        return tp.model_copy(deep=True)

    def redraft(self, number: str, rev: str) -> Deliverable:
        """Mark a deliverable as redrafted on the current value of its tie-point attribute."""
        d = next((x for x in self._deliverables if x.number == number), None)
        if d is None:
            raise NotFound(number)
        project = self.project(rev)
        tp = next(t for t in project.tie_points if t.id == d.tie_point)
        line = resolve_line(tp, project)
        if line is None:
            raise Conflict(f"{d.tie_point} has no single current stream; resolve it first")
        d.sized_on = {
            "pressure": line.pressure_psig,
            "temperature": line.temperature_f,
            "phase": line.phase,
            "vapor_fraction": line.vapor_fraction,
        }[d.attribute]
        return d.model_copy(deep=True)
