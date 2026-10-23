"""Stream identity check: each tie-point row must map to exactly one stream tag in the current PFD."""

from __future__ import annotations

from pydantic import BaseModel

from .models import Status, Stream, TiePoint


class IdentityResult(BaseModel):
    status: Status
    matched_tag: str | None = None
    suggestion: str | None = None
    candidates: list[str] = []
    reason: str


def check_identity(tp: TiePoint, streams: list[Stream]) -> IdentityResult:
    exact = [s for s in streams if s.tag == tp.stream_tag]
    if len(exact) == 1:
        return IdentityResult(status=Status.PASS, matched_tag=tp.stream_tag, reason=f"{tp.stream_tag} found once in the current PFD")
    if len(exact) > 1:
        return IdentityResult(
            status=Status.AMBIGUOUS,
            candidates=[s.tag for s in exact],
            reason=f"{tp.stream_tag} appears {len(exact)} times in the current PFD",
        )
    same_route = sorted(s.tag for s in streams if s.from_node == tp.from_node and s.to_node == tp.to_node)
    route = f"{tp.from_node} to {tp.to_node}"
    if len(same_route) == 1:
        return IdentityResult(
            status=Status.ORPHANED,
            suggestion=same_route[0],
            candidates=same_route,
            reason=f"{tp.stream_tag} no longer exists; {same_route[0]} runs the same route ({route}), likely renumbered",
        )
    if len(same_route) > 1:
        return IdentityResult(
            status=Status.AMBIGUOUS,
            candidates=same_route,
            reason=f"{tp.stream_tag} no longer exists; {len(same_route)} streams now run {route} ({', '.join(same_route)})",
        )
    return IdentityResult(status=Status.ORPHANED, reason=f"{tp.stream_tag} no longer exists and no stream runs {route}")
