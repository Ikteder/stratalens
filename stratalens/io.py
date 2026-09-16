"""Strict CSV loading for StrataLens."""

from __future__ import annotations

import csv
import math
from pathlib import Path


class InputError(ValueError):
    """Raised when an input file violates the public schema."""


def load_rows(
    path: str | Path,
    *,
    stratum_column: str = "stratum",
    treatment_column: str = "treatment",
    outcome_column: str = "outcome",
    weight_column: str = "weight",
) -> list[dict[str, object]]:
    source = Path(path)
    try:
        handle = source.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise InputError(f"cannot open input: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise InputError("input must contain a header row")
        required = {stratum_column, treatment_column, outcome_column}
        missing = sorted(required.difference(reader.fieldnames))
        if missing:
            raise InputError(f"missing required columns: {', '.join(missing)}")
        has_weight = weight_column in reader.fieldnames
        rows: list[dict[str, object]] = []
        for line_number, raw in enumerate(reader, start=2):
            stratum = (raw.get(stratum_column) or "").strip()
            if not stratum:
                raise InputError(f"line {line_number}: stratum must not be empty")
            treatment = _binary(raw.get(treatment_column), treatment_column, line_number)
            outcome = _binary(raw.get(outcome_column), outcome_column, line_number)
            weight = 1.0
            if has_weight:
                text = (raw.get(weight_column) or "").strip()
                if not text:
                    raise InputError(f"line {line_number}: weight must not be empty")
                try:
                    weight = float(text)
                except ValueError as exc:
                    raise InputError(f"line {line_number}: weight must be numeric") from exc
                if not math.isfinite(weight) or weight <= 0:
                    raise InputError(f"line {line_number}: weight must be finite and positive")
            rows.append(
                {
                    "stratum": stratum,
                    "treatment": treatment,
                    "outcome": outcome,
                    "weight": weight,
                }
            )
    if not rows:
        raise InputError("input must contain at least one data row")
    return rows


def _binary(value: str | None, name: str, line_number: int) -> int:
    text = (value or "").strip()
    if text not in {"0", "1"}:
        raise InputError(f"line {line_number}: {name} must be exactly 0 or 1")
    return int(text)
