"""Impact trace: which downstream deliverables were sized on a value the current line list no longer holds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .identity import check_identity
from .models import Deliverable, LineEntry, Project, Status, TiePoint

ImpactStatus = Literal["ok", "stale", "unverifiable"]


class ImpactItem(BaseModel):
    deliverable: Deliverable
    current: float | str | None
    status: ImpactStatus
    reason: str


def resolve_line(tp: TiePoint, project: Project) -> LineEntry | None:
    """Current line-list entry for a row: exact tag, or a single same-route renumber; else None."""
    ident = check_identity(tp, project.streams)
    tag = ident.matched_tag or (ident.suggestion if ident.status == Status.ORPHANED else None)
    if tag is None:
        return None
    return next((ln for ln in project.lines if ln.stream_tag == tag), None)


def _current_value(line: LineEntry, attribute: str) -> float | str:
    return {
        "pressure": line.pressure_psig,
        "temperature": line.temperature_f,
        "phase": line.phase,
        "vapor_fraction": line.vapor_fraction,
    }[attribute]


def _band(tp: TiePoint, attribute: str) -> float:
    return {
        "pressure": tp.tolerance.pressure_psi,
        "temperature": tp.tolerance.temperature_f,
        "vapor_fraction": tp.tolerance.vapor_fraction,
    }.get(attribute, 0.0)


def trace_impact(project: Project) -> list[ImpactItem]:
    rows = {t.id: t for t in project.tie_points}
    items: list[ImpactItem] = []
    for d in project.deliverables:
        tp = rows.get(d.tie_point)
        line = resolve_line(tp, project) if tp else None
        if tp is None or line is None:
            items.append(ImpactItem(deliverable=d, current=None, status="unverifiable", reason=f"{d.tie_point} has no single current stream"))
            continue
        cur = _current_value(line, d.attribute)
        if isinstance(cur, str) or isinstance(d.sized_on, str):
            stale = str(cur) != str(d.sized_on)
        else:
            stale = abs(cur - float(d.sized_on)) > _band(tp, d.attribute) + 1e-9
        label = d.attribute.replace("_", " ")
        reason = (
            f"sized on {label} {d.sized_on}, line list now says {cur}"
            if stale
            else f"{label} {d.sized_on} still within the {d.tie_point} band (now {cur})"
        )
        items.append(ImpactItem(deliverable=d, current=cur, status="stale" if stale else "ok", reason=reason))
    return items
