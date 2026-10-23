"""Seed project: an amine treating unit tied into a gas plant's inlet and compression scope.

Rev B is the FEL2 freeze: the tie-point table was written and both owners attested against it.
Rev C is the same project after an upstream process change (higher compressor discharge pressure,
a renumbered flash-gas stream, a split acid-gas line, wetter scrubber liquids, a higher LP steam header).
The tie-point table itself was not touched between the two revisions, which is exactly the failure.
"""

from __future__ import annotations

from .models import Attestation, Deliverable, DocRef, LineEntry, Project, Stream, TiePoint, Tolerance

UP = "Inlet & Compression (owner)"
DOWN = "Amine Treating Unit (EPC)"

UP_PROCESS = "J. Okafor, process lead (owner)"
DOWN_PROCESS = "M. Brandt, process lead (EPC)"
UP_UTIL = "R. Haines, utilities lead (owner)"


def _docs(rev: str) -> list[DocRef]:
    process_rev = "B" if rev == "B" else "C"
    return [
        DocRef(number="PFD-100", title="Inlet & Compression PFD", rev=process_rev, scope=UP),
        DocRef(number="LL-200", title="Inlet & Compression line list", rev=process_rev, scope=UP),
        DocRef(number="UT-400", title="Utilities line list", rev="A", scope=UP),
        DocRef(number="ATU-300", title="Amine Treating Unit PFD + line list", rev="A", scope=DOWN),
    ]


_BASE_STREAMS = [
    ("S-101", "Sour gas to amine contactor", "K-101", "C-301"),
    ("S-102", "Makeup water to amine sump", "WTR-1", "TK-305"),
    ("S-103", "Rich amine flash gas to fuel gas", "V-310", "FG-101"),
    ("S-104", "Acid gas to flare header", "C-320", "FL-101"),
    ("S-105", "Sweet gas to dehydration", "C-301", "D-110"),
    ("S-106", "Instrument air supply", "IA-100", "ATU-IA"),
    ("S-107", "Contactor inlet scrubber liquids to slop", "V-300", "TK-120"),
    ("S-108", "Cooling water supply", "CW-100", "E-315"),
    ("S-109", "Cooling water return", "E-315", "CW-101"),
    ("S-110", "LP steam to amine reboiler", "STM-100", "E-330"),
]

# stream tag -> (line number, P psig, T degF, phase, vapor fraction) at Rev B
_BASE_LINES = {
    "S-101": ("8\"-PG-1011-A1", 950, 120, "V", 1.0),
    "S-102": ("2\"-WM-1021-B1", 65, 80, "L", 0.0),
    "S-103": ("3\"-FG-1031-A1", 80, 110, "V", 1.0),
    "S-104": ("6\"-AG-1041-C1", 12, 120, "V", 1.0),
    "S-105": ("8\"-PG-1051-A1", 940, 105, "V", 1.0),
    "S-106": ("1\"-IA-1061-B1", 100, 90, "V", 1.0),
    "S-107": ("2\"-HC-1071-A1", 60, 110, "L", 0.02),
    "S-108": ("6\"-CWS-1081-B1", 65, 85, "L", 0.0),
    "S-109": ("6\"-CWR-1091-B1", 45, 105, "L", 0.0),
    "S-110": ("4\"-LS-1101-A2", 50, 298, "V", 1.0),
}

_UTILITY = {"S-102", "S-106", "S-108", "S-109"}


def _streams(rev: str) -> list[Stream]:
    streams = [Stream(tag=t, description=d, from_node=f, to_node=to) for t, d, f, to in _BASE_STREAMS]
    if rev == "B":
        return streams
    out: list[Stream] = []
    for s in streams:
        if s.tag == "S-103":  # renumbered in PFD-100 Rev C, same route
            out.append(s.model_copy(update={"tag": "S-103A"}))
        elif s.tag == "S-104":  # split into two parallel lines to the same header
            out.append(s.model_copy(update={"tag": "S-104A", "description": "Acid gas to flare header (train A)"}))
            out.append(s.model_copy(update={"tag": "S-104B", "description": "Acid gas to flare header (train B)"}))
        else:
            out.append(s)
    return out


def _lines(rev: str) -> list[LineEntry]:
    rows = dict(_BASE_LINES)
    if rev == "C":
        rows["S-101"] = ("8\"-PG-1011-A1", 1025, 128, "V", 1.0)  # compressor discharge raised
        rows["S-105"] = ("8\"-PG-1051-A1", 1015, 106, "V", 1.0)
        rows["S-107"] = ("2\"-HC-1071-A1", 60, 112, "2P", 0.11)  # wetter inlet, flashing liquids
        rows["S-110"] = ("4\"-LS-1101-A2", 65, 312, "V", 1.0)  # LP header moved up
        rows["S-103A"] = rows.pop("S-103")
        line, p, t, ph, vf = rows.pop("S-104")
        rows["S-104A"] = ("6\"-AG-1041A-C1", p, t, ph, vf)
        rows["S-104B"] = ("6\"-AG-1041B-C1", p, t, ph, vf)
    return [
        LineEntry(line_number=ln, stream_tag=tag, pressure_psig=p, temperature_f=t, phase=ph, vapor_fraction=vf)
        for tag, (ln, p, t, ph, vf) in rows.items()
    ]


def _tie_points() -> list[TiePoint]:
    """The tie-point table as frozen at FEL2 (Rev B). Unchanged in Rev C."""
    out: list[TiePoint] = []
    tol_default = Tolerance(pressure_psi=15, temperature_f=10, vapor_fraction=0.05)
    tight = {
        "S-102": Tolerance(pressure_psi=5, temperature_f=10, vapor_fraction=0.0),
        "S-104": Tolerance(pressure_psi=3, temperature_f=10, vapor_fraction=0.0),
        "S-107": Tolerance(pressure_psi=5, temperature_f=10, vapor_fraction=0.03),
        "S-108": Tolerance(pressure_psi=5, temperature_f=5, vapor_fraction=0.0),
        "S-109": Tolerance(pressure_psi=5, temperature_f=5, vapor_fraction=0.0),
        "S-110": Tolerance(pressure_psi=5, temperature_f=10, vapor_fraction=0.0),
    }
    for i, (tag, desc, frm, to) in enumerate(_BASE_STREAMS, start=1):
        _ln, p, t, ph, vf = _BASE_LINES[tag]
        util = tag in _UTILITY
        up_doc = "UT-400" if util else "LL-200"
        up_rev = "A" if util else "B"
        out.append(
            TiePoint(
                id=f"TP-{i:02d}",
                stream_tag=tag,
                description=desc,
                from_node=frm,
                to_node=to,
                upstream_owner=UP,
                downstream_owner=DOWN,
                upstream_doc=up_doc,
                downstream_doc="ATU-300",
                pressure_psig=p,
                temperature_f=t,
                phase=ph,
                vapor_fraction=vf,
                tolerance=tight.get(tag, tol_default),
                attestations=[
                    Attestation(party="upstream", by=UP_UTIL if util else UP_PROCESS, doc=up_doc, rev=up_rev, on="2026-06-12"),
                    Attestation(party="downstream", by=DOWN_PROCESS, doc="ATU-300", rev="A", on="2026-06-14"),
                ],
            )
        )
    return out


def _deliverables() -> list[Deliverable]:
    return [
        Deliverable(number="DS-301", title="Amine contactor C-301 datasheet", tie_point="TP-01", attribute="pressure", sized_on=950, discipline="Mechanical"),
        Deliverable(number="DS-301T", title="Contactor C-301 feed temperature basis", tie_point="TP-01", attribute="temperature", sized_on=120, discipline="Process"),
        Deliverable(number="DS-305", title="Makeup water pump P-305 datasheet", tie_point="TP-02", attribute="pressure", sized_on=65, discipline="Mechanical"),
        Deliverable(number="PSV-305", title="Sweet gas outlet relief calc PSV-305", tie_point="TP-05", attribute="pressure", sized_on=940, discipline="Process"),
        Deliverable(number="DS-121", title="Slop pump P-121 datasheet", tie_point="TP-07", attribute="vapor_fraction", sized_on=0.02, discipline="Mechanical"),
        Deliverable(number="DS-330", title="Amine reboiler E-330 datasheet", tie_point="TP-10", attribute="pressure", sized_on=50, discipline="Mechanical"),
    ]


def build_project(rev: str = "C") -> Project:
    if rev not in ("B", "C"):
        raise ValueError(f"unknown revision {rev!r}")
    return Project(
        name="Gas plant expansion: amine treating unit tie-in (FEL2 to FEL3)",
        revision_label=f"Rev {rev}",
        documents=_docs(rev),
        streams=_streams(rev),
        lines=_lines(rev),
        tie_points=_tie_points(),
        deliverables=_deliverables(),
    )


SAMPLE_TABLE_TEXT = """TIE-POINT SCHEDULE  ATU-300 APPENDIX C   REV A   (FEL2)
TP     STREAM   SERVICE                               P(psig)  T(F)  PHASE  VF
TP-01  S-101    Sour gas to amine contactor           950      120   V      1.00
TP-02  S-102    Makeup water to amine sump            65       80    L      0.00
TP-03  S-103    Rich amine flash gas to fuel gas      80       110   V      1.00
TP-04  S-104    Acid gas to flare header              12       120   V      1.00
       -- page 2 --
TP-05  S-105    Sweet gas to dehydration              940      105   V      1.00
TP-06  S-106    Instrument air supply                 100      90    V      1.00
TP-07  S-107    Contactor inlet scrubber liquids      60       110   L      0.02
TP-08  S-108    Cooling water supply                  65       85    L      0.00
TP-09  S-109    Cooling water return                  45       105   LIQ    0.00
TP-10  S-110    LP steam to amine reboiler            fifty    298   V      1.00
NOTES: 1. CONDITIONS AT BATTERY LIMIT.  2. TOLERANCES PER INTERFACE AGREEMENT IA-07.
"""
