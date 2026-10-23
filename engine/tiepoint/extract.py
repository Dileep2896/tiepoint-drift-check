"""Extraction: messy tie-point schedule text (PDF copy-paste) -> typed rows, each value with its source line.

Two extractors share one contract and one validator. The rule parser is deterministic and always
available. The LLM extractor is used only when an API key is configured; its output is validated by
the same Pydantic model, so a hallucinated or malformed row is reported, never written.
"""

from __future__ import annotations

import json
import os
import re
from typing import Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from .models import Phase

_PHASES: dict[str, Phase] = {
    "V": "V", "VAP": "V", "VAPOR": "V", "VAPOUR": "V", "GAS": "V",
    "L": "L", "LIQ": "L", "LIQUID": "L",
    "2P": "2P", "TWO-PHASE": "2P", "2-PHASE": "2P", "MIXED": "2P",
}
_ROW = re.compile(r"^\s*(TP-\d+)\s+(\S+)\s+(.*)$")


class ExtractedRow(BaseModel):
    id: str = Field(pattern=r"^TP-\d+$")
    stream_tag: str
    description: str
    pressure_psig: float
    temperature_f: float
    phase: Phase
    vapor_fraction: float = Field(ge=0, le=1)
    source_line: int = Field(ge=1)


class RowError(BaseModel):
    source_line: int
    text: str
    reason: str


class ExtractionResult(BaseModel):
    engine: Literal["rules", "llm"]
    rows: list[ExtractedRow]
    errors: list[RowError]
    lines_scanned: int


class Extractor(Protocol):
    def extract(self, text: str) -> ExtractionResult: ...


def normalize_phase(raw: str) -> Phase | None:
    return _PHASES.get(raw.strip().upper())


def _num(raw: str, label: str) -> float:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        raise ValueError(f"{label} {raw!r} is not a number") from None


class RuleExtractor:
    """Parses rows that start with a TP-nn id; the last four tokens are P, T, phase, vapor fraction."""

    def extract(self, text: str) -> ExtractionResult:
        rows: list[ExtractedRow] = []
        errors: list[RowError] = []
        lines = text.splitlines()
        for n, raw in enumerate(lines, start=1):
            m = _ROW.match(raw)
            if not m:
                continue
            tp_id, tag, rest = m.groups()
            tokens = rest.split()
            if len(tokens) < 5:
                errors.append(RowError(source_line=n, text=raw.strip(), reason="expected service, P, T, phase and VF"))
                continue
            p_raw, t_raw, ph_raw, vf_raw = tokens[-4:]
            try:
                phase = normalize_phase(ph_raw)
                if phase is None:
                    raise ValueError(f"phase {ph_raw!r} is not V, L or 2P")
                rows.append(
                    ExtractedRow(
                        id=tp_id,
                        stream_tag=tag,
                        description=" ".join(tokens[:-4]),
                        pressure_psig=_num(p_raw, "pressure"),
                        temperature_f=_num(t_raw, "temperature"),
                        phase=phase,
                        vapor_fraction=_num(vf_raw, "vapor fraction"),
                        source_line=n,
                    )
                )
            except (ValueError, ValidationError) as e:
                reason = e.errors()[0]["msg"] if isinstance(e, ValidationError) else str(e)
                errors.append(RowError(source_line=n, text=raw.strip(), reason=reason))
        return ExtractionResult(engine="rules", rows=rows, errors=errors, lines_scanned=len(lines))


SYSTEM_PROMPT = (
    "You extract tie-point schedules from engineering documents. Return only a JSON array. "
    "Each element: {id, stream_tag, description, pressure_psig, temperature_f, phase, vapor_fraction, source_line}. "
    "phase is one of V, L, 2P. source_line is the 1-based line number the row came from. "
    "Copy values exactly; if a value is unreadable, still return the row with that field set to null."
)


def validate_rows(items: list[dict], lines: list[str]) -> tuple[list[ExtractedRow], list[RowError]]:
    """Validate model output with the same schema as the rule parser; bad rows become errors."""
    rows: list[ExtractedRow] = []
    errors: list[RowError] = []
    for item in items:
        line_no = item.get("source_line") if isinstance(item.get("source_line"), int) else 0
        text = lines[line_no - 1].strip() if 1 <= line_no <= len(lines) else str(item)
        if isinstance(item.get("phase"), str):
            item = {**item, "phase": normalize_phase(item["phase"]) or item["phase"]}
        try:
            row = ExtractedRow(**item)
        except ValidationError as e:
            errors.append(RowError(source_line=max(line_no, 1), text=text, reason=e.errors()[0]["msg"]))
            continue
        if row.id not in text:
            errors.append(RowError(source_line=row.source_line, text=text, reason=f"{row.id} not found on its cited source line"))
            continue
        rows.append(row)
    return rows, errors


class LLMExtractor:
    """Claude-backed extractor. Requires the `anthropic` package and ANTHROPIC_API_KEY."""

    def __init__(self, model: str | None = None) -> None:
        import anthropic  # optional dependency

        self._client = anthropic.Anthropic()
        self._model = model or os.environ.get("EXTRACT_MODEL", "claude-opus-5-5")

    def extract(self, text: str) -> ExtractionResult:
        lines = text.splitlines()
        numbered = "\n".join(f"{i}: {ln}" for i, ln in enumerate(lines, start=1))
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": numbered}],
        )
        body = "".join(b.text for b in msg.content if b.type == "text").strip()
        body = body[body.find("[") : body.rfind("]") + 1] if "[" in body else "[]"
        rows, errors = validate_rows(json.loads(body), lines)
        return ExtractionResult(engine="llm", rows=rows, errors=errors, lines_scanned=len(lines))


def default_extractor() -> Extractor:
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return LLMExtractor()
        except ImportError:
            pass
    return RuleExtractor()
