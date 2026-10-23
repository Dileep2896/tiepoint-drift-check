"""Checker summary on the seed revisions and the resolve loop in the repository."""

import pytest

from tiepoint.checker import run_checks
from tiepoint.models import Status
from tiepoint.seed import build_project
from tiepoint.store import Conflict, InMemoryRepository, NotFound


def by_id(report):
    return {r.id: r for r in report.tie_points}


def test_rev_b_is_fully_current():
    s = run_checks(build_project("B")).summary
    assert (s.total, s.current, s.drift, s.orphaned, s.ambiguous, s.lapsed) == (10, 10, 0, 0, 0, 0)
    assert s.deliverables_stale == 0


def test_rev_c_summary_counts():
    s = run_checks(build_project("C")).summary
    assert s.total == 10
    assert s.attested_on_paper == 10
    assert s.current == 4
    assert s.drift == 4
    assert s.orphaned == 1
    assert s.ambiguous == 1
    assert s.lapsed == 6
    assert (s.deliverables_total, s.deliverables_stale, s.deliverables_unverifiable) == (6, 4, 0)


def test_rev_c_statuses_and_headlines():
    rows = by_id(run_checks(build_project("C")))
    assert rows["TP-01"].status == Status.DRIFT
    assert rows["TP-01"].headline == "pressure 950 → 1025 psig (band ±15)"
    assert rows["TP-03"].status == Status.ORPHANED
    assert rows["TP-04"].status == Status.AMBIGUOUS
    assert rows["TP-07"].status == Status.DRIFT and "phase" in rows["TP-07"].headline
    assert rows["TP-02"].status == Status.CURRENT


def test_identity_failure_outranks_drift():
    rows = by_id(run_checks(build_project("C")))
    # TP-03's renumbered stream carries identical conditions, but the row still fails identity
    assert all(c.status == Status.PASS for c in rows["TP-03"].conditions)
    assert rows["TP-03"].status == Status.ORPHANED


def test_lapsed_only_row_reports_rev_change():
    p = build_project("C")
    # put TP-01 back inside its band: only the lapsed attestation remains
    for ln in p.lines:
        if ln.stream_tag == "S-101":
            ln.pressure_psig = 955
    rows = by_id(run_checks(p))
    assert rows["TP-01"].status == Status.LAPSED
    assert "LL-200 Rev B → C" in rows["TP-01"].headline


def test_accept_then_attest_restores_current():
    repo = InMemoryRepository()
    tp = repo.accept("TP-01", "C")
    assert tp.pressure_psig == 1025 and tp.attestations == []
    row = by_id(run_checks(repo.project("C")))["TP-01"]
    assert row.status == Status.PENDING
    repo.attest("TP-01", "upstream", "C")
    repo.attest("TP-01", "downstream", "C")
    row = by_id(run_checks(repo.project("C")))["TP-01"]
    assert row.status == Status.CURRENT
    up = next(a for a in repo.project("C").tie_points[0].attestations if a.party == "upstream")
    assert up.rev == "C" and up.doc == "LL-200"


def test_accept_renumber_takes_suggestion():
    repo = InMemoryRepository()
    assert repo.accept("TP-03", "C").stream_tag == "S-103A"


def test_accept_ambiguous_requires_choice():
    repo = InMemoryRepository()
    with pytest.raises(Conflict):
        repo.accept("TP-04", "C")
    with pytest.raises(Conflict):
        repo.accept("TP-04", "C", stream_tag="S-999")
    assert repo.accept("TP-04", "C", stream_tag="S-104B").stream_tag == "S-104B"


def test_redraft_clears_stale_deliverable():
    repo = InMemoryRepository()
    d = repo.redraft("DS-301", "C")
    assert d.sized_on == 1025
    s = run_checks(repo.project("C")).summary
    assert s.deliverables_stale == 3


def test_redraft_unresolved_ambiguous_conflicts():
    from tiepoint.models import Deliverable

    repo = InMemoryRepository()
    repo._deliverables.append(Deliverable(number="X", title="x", tie_point="TP-04", attribute="pressure", sized_on=12, discipline="P"))
    with pytest.raises(Conflict):
        repo.redraft("X", "C")


def test_full_resolution_reaches_all_current():
    repo = InMemoryRepository()
    for tp_id, tag in [("TP-01", None), ("TP-03", None), ("TP-04", "S-104A"), ("TP-05", None), ("TP-07", None), ("TP-10", None)]:
        repo.accept(tp_id, "C", tag)
        repo.attest(tp_id, "upstream", "C")
        repo.attest(tp_id, "downstream", "C")
    for n in ["DS-301", "PSV-305", "DS-121", "DS-330"]:
        repo.redraft(n, "C")
    s = run_checks(repo.project("C")).summary
    assert (s.current, s.deliverables_stale) == (10, 0)


def test_unknown_ids_raise_not_found():
    repo = InMemoryRepository()
    with pytest.raises(NotFound):
        repo.accept("TP-99", "C")
    with pytest.raises(NotFound):
        repo.redraft("NOPE", "C")


def test_reset_restores_seed():
    repo = InMemoryRepository()
    repo.accept("TP-01", "C")
    repo.reset()
    assert run_checks(repo.project("C")).summary.drift == 4


def test_unknown_revision_rejected():
    with pytest.raises(ValueError):
        build_project("Z")
