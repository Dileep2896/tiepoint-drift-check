"""Owner attestation: valid only while each owner's attested revision is still the current revision."""

from __future__ import annotations

from pydantic import BaseModel

from .models import Party, Project, Status, TiePoint


class PartyAttestation(BaseModel):
    party: Party
    doc: str
    by: str | None
    attested_rev: str | None
    current_rev: str | None
    status: Status


class AttestationResult(BaseModel):
    status: Status
    parties: list[PartyAttestation]


def check_attestation(tp: TiePoint, project: Project) -> AttestationResult:
    parties: list[PartyAttestation] = []
    for party, doc_no in (("upstream", tp.upstream_doc), ("downstream", tp.downstream_doc)):
        doc = project.doc(doc_no)
        current_rev = doc.rev if doc else None
        att = next((a for a in tp.attestations if a.party == party and a.doc == doc_no), None)
        if att is None:
            status = Status.PENDING
        elif att.rev == current_rev:
            status = Status.CURRENT
        else:
            status = Status.LAPSED
        parties.append(
            PartyAttestation(
                party=party,
                doc=doc_no,
                by=att.by if att else None,
                attested_rev=att.rev if att else None,
                current_rev=current_rev,
                status=status,
            )
        )
    statuses = {p.status for p in parties}
    if Status.LAPSED in statuses:
        overall = Status.LAPSED
    elif Status.PENDING in statuses:
        overall = Status.PENDING
    else:
        overall = Status.CURRENT
    return AttestationResult(status=overall, parties=parties)
