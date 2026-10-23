"""Unit tests for the three typed-contract checks and the impact trace."""

from tiepoint.attest import check_attestation
from tiepoint.identity import check_identity
from tiepoint.impact import trace_impact
from tiepoint.models import Attestation, Deliverable, LineEntry, Status, Stream, Tolerance
from tiepoint.reconcile import reconcile
from tiepoint.seed import build_project


def tp(project, tp_id):
    return next(t for t in project.tie_points if t.id == tp_id)


# ---------- stream identity ----------

def test_identity_passes_when_tag_exists_once():
    p = build_project("B")
    r = check_identity(tp(p, "TP-01"), p.streams)
    assert r.status == Status.PASS
    assert r.matched_tag == "S-101"


def test_identity_orphaned_with_renumber_suggestion():
    p = build_project("C")
    r = check_identity(tp(p, "TP-03"), p.streams)
    assert r.status == Status.ORPHANED
    assert r.suggestion == "S-103A"
    assert "renumbered" in r.reason


def test_identity_ambiguous_when_route_split():
    p = build_project("C")
    r = check_identity(tp(p, "TP-04"), p.streams)
    assert r.status == Status.AMBIGUOUS
    assert r.candidates == ["S-104A", "S-104B"]
    assert r.suggestion is None


def test_identity_orphaned_without_suggestion_when_route_gone():
    p = build_project("B")
    row = tp(p, "TP-01")
    r = check_identity(row, [s for s in p.streams if s.tag != "S-101"])
    assert r.status == Status.ORPHANED
    assert r.suggestion is None and r.candidates == []


def test_identity_ambiguous_on_duplicate_tag():
    p = build_project("B")
    dup = p.streams + [Stream(tag="S-101", description="dup", from_node="X", to_node="Y")]
    assert check_identity(tp(p, "TP-01"), dup).status == Status.AMBIGUOUS


# ---------- condition reconciliation ----------

def line(**kw):
    base = dict(line_number="L", stream_tag="S-101", pressure_psig=950, temperature_f=120, phase="V", vapor_fraction=1.0)
    base.update(kw)
    return LineEntry(**base)


def test_reconcile_all_pass_at_rev_b():
    p = build_project("B")
    for row in p.tie_points:
        ln = next(l for l in p.lines if l.stream_tag == row.stream_tag)
        assert all(c.status == Status.PASS for c in reconcile(row, ln))


def test_reconcile_pressure_drift_reports_delta_and_band():
    p = build_project("C")
    row = tp(p, "TP-01")
    checks = {c.attribute: c for c in reconcile(row, line(pressure_psig=1025, temperature_f=128))}
    assert checks["pressure"].status == Status.DRIFT
    assert checks["pressure"].delta == 75
    assert checks["pressure"].band == 15
    # +8 F is inside the 10 F band
    assert checks["temperature"].status == Status.PASS


def test_reconcile_band_edge_is_inclusive():
    p = build_project("B")
    row = tp(p, "TP-01")
    checks = {c.attribute: c for c in reconcile(row, line(pressure_psig=965))}
    assert checks["pressure"].status == Status.PASS
    checks = {c.attribute: c for c in reconcile(row, line(pressure_psig=965.5))}
    assert checks["pressure"].status == Status.DRIFT


def test_reconcile_phase_change_is_drift():
    p = build_project("C")
    row = tp(p, "TP-07")
    ln = next(l for l in p.lines if l.stream_tag == "S-107")
    checks = {c.attribute: c for c in reconcile(row, ln)}
    assert checks["phase"].status == Status.DRIFT
    assert checks["phase"].current == "2P"
    assert checks["vapor_fraction"].status == Status.DRIFT
    assert round(checks["vapor_fraction"].delta, 2) == 0.09


def test_reconcile_without_line_entry_reports_missing():
    p = build_project("B")
    checks = reconcile(tp(p, "TP-01"), None)
    assert all(c.status == Status.ORPHANED and c.current is None for c in checks)


# ---------- owner attestation ----------

def test_attestation_current_at_rev_b():
    p = build_project("B")
    assert all(check_attestation(t, p).status == Status.CURRENT for t in p.tie_points)


def test_attestation_lapses_when_upstream_doc_revs():
    p = build_project("C")
    r = check_attestation(tp(p, "TP-01"), p)
    assert r.status == Status.LAPSED
    up = next(x for x in r.parties if x.party == "upstream")
    assert (up.attested_rev, up.current_rev, up.status) == ("B", "C", Status.LAPSED)
    down = next(x for x in r.parties if x.party == "downstream")
    assert down.status == Status.CURRENT


def test_attestation_unaffected_when_its_docs_did_not_rev():
    p = build_project("C")
    assert check_attestation(tp(p, "TP-02"), p).status == Status.CURRENT


def test_attestation_lapses_when_downstream_doc_revs():
    p = build_project("B")
    p.documents = [d.model_copy(update={"rev": "B"}) if d.number == "ATU-300" else d for d in p.documents]
    r = check_attestation(tp(p, "TP-02"), p)
    assert r.status == Status.LAPSED


def test_attestation_pending_when_a_party_missing():
    p = build_project("B")
    row = tp(p, "TP-02")
    row.attestations = [a for a in row.attestations if a.party == "upstream"]
    r = check_attestation(row, p)
    assert r.status == Status.PENDING
    assert next(x for x in r.parties if x.party == "downstream").status == Status.PENDING


def test_attestation_on_wrong_document_does_not_count():
    p = build_project("B")
    row = tp(p, "TP-02")
    row.attestations[0] = Attestation(party="upstream", by="x", doc="LL-200", rev="B", on="2026-06-12")
    assert check_attestation(row, p).status == Status.PENDING


# ---------- impact ----------

def test_impact_flags_only_deliverables_on_drifted_values():
    p = build_project("C")
    items = {i.deliverable.number: i for i in trace_impact(p)}
    stale = sorted(n for n, i in items.items() if i.status == "stale")
    assert stale == ["DS-121", "DS-301", "DS-330", "PSV-305"]
    assert items["DS-301"].current == 1025
    # temperature moved 8 F, inside the band, so the temperature basis is still fine
    assert items["DS-301T"].status == "ok"
    assert items["DS-305"].status == "ok"


def test_impact_clean_at_rev_b():
    assert all(i.status == "ok" for i in trace_impact(build_project("B")))


def test_impact_unverifiable_when_stream_missing():
    p = build_project("C")
    p.deliverables.append(
        Deliverable(number="X-1", title="flash gas KO drum", tie_point="TP-04", attribute="pressure", sized_on=12, discipline="Process")
    )
    items = {i.deliverable.number: i for i in trace_impact(p)}
    assert items["X-1"].status == "unverifiable"


def test_tolerance_model_rejects_negative():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Tolerance(pressure_psi=-1, temperature_f=1, vapor_fraction=0)
