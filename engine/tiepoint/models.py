"""Typed records for a tie-point contract between two engineering scopes.

The PFD stream list and the line list act as the type system; the tie-point table is the contract that
both scopes sign. Every value keeps the document and revision it came from.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

Phase = Literal["V", "L", "2P"]
Party = Literal["upstream", "downstream"]
Attribute = Literal["pressure", "temperature", "phase", "vapor_fraction"]


class DocRef(BaseModel):
    """A controlled document and its current revision, e.g. LL-200 Rev C."""

    number: str
    title: str
    rev: str
    scope: str


class Stream(BaseModel):
    """One PFD stream. from/to are equipment or battery-limit nodes."""

    tag: str
    description: str
    from_node: str
    to_node: str


class LineEntry(BaseModel):
    """Line-list operating conditions for a stream (the current source of truth)."""

    line_number: str
    stream_tag: str
    pressure_psig: float
    temperature_f: float
    phase: Phase
    vapor_fraction: float = Field(ge=0, le=1)


class Tolerance(BaseModel):
    """Per-tie-point tolerance band declared by both scopes."""

    pressure_psi: float = Field(ge=0)
    temperature_f: float = Field(ge=0)
    vapor_fraction: float = Field(ge=0, le=1)


class Attestation(BaseModel):
    """One owner's sign-off, pinned to the revision of their source document they reviewed."""

    party: Party
    by: str
    doc: str
    rev: str
    on: str


class TiePoint(BaseModel):
    id: str
    stream_tag: str
    description: str
    from_node: str
    to_node: str
    upstream_owner: str
    downstream_owner: str
    upstream_doc: str
    downstream_doc: str
    pressure_psig: float
    temperature_f: float
    phase: Phase
    vapor_fraction: float = Field(ge=0, le=1)
    tolerance: Tolerance
    attestations: list[Attestation] = []


class Deliverable(BaseModel):
    """A downstream document sized against tie-point values (datasheet, calc)."""

    number: str
    title: str
    tie_point: str
    attribute: Attribute
    sized_on: float | str
    discipline: str


class Project(BaseModel):
    name: str
    revision_label: str
    documents: list[DocRef]
    streams: list[Stream]
    lines: list[LineEntry]
    tie_points: list[TiePoint]
    deliverables: list[Deliverable]

    def doc(self, number: str) -> DocRef | None:
        return next((d for d in self.documents if d.number == number), None)


class Status(str, Enum):
    PASS = "pass"
    DRIFT = "drift"
    ORPHANED = "orphaned"
    AMBIGUOUS = "ambiguous"
    LAPSED = "lapsed"
    PENDING = "pending"
    CURRENT = "current"
