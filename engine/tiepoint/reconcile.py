"""Condition reconciliation: tie-point conditions vs the current line list, within declared tolerance bands."""

from __future__ import annotations

from pydantic import BaseModel

from .models import Attribute, LineEntry, Status, TiePoint

EPS = 1e-9


class AttributeCheck(BaseModel):
    attribute: Attribute
    stated: float | str
    current: float | str | None
    delta: float | None = None
    band: float | None = None
    unit: str
    status: Status


def _numeric(attr: Attribute, stated: float, current: float, band: float, unit: str) -> AttributeCheck:
    delta = round(current - stated, 6)
    status = Status.PASS if abs(delta) <= band + EPS else Status.DRIFT
    return AttributeCheck(attribute=attr, stated=stated, current=current, delta=delta, band=band, unit=unit, status=status)


def reconcile(tp: TiePoint, line: LineEntry | None) -> list[AttributeCheck]:
    if line is None:
        return [
            AttributeCheck(attribute=a, stated=s, current=None, unit=u, status=Status.ORPHANED)
            for a, s, u in (
                ("pressure", tp.pressure_psig, "psig"),
                ("temperature", tp.temperature_f, "°F"),
                ("phase", tp.phase, ""),
                ("vapor_fraction", tp.vapor_fraction, ""),
            )
        ]
    tol = tp.tolerance
    return [
        _numeric("pressure", tp.pressure_psig, line.pressure_psig, tol.pressure_psi, "psig"),
        _numeric("temperature", tp.temperature_f, line.temperature_f, tol.temperature_f, "°F"),
        AttributeCheck(
            attribute="phase",
            stated=tp.phase,
            current=line.phase,
            unit="",
            status=Status.PASS if tp.phase == line.phase else Status.DRIFT,
        ),
        _numeric("vapor_fraction", tp.vapor_fraction, line.vapor_fraction, tol.vapor_fraction, ""),
    ]
