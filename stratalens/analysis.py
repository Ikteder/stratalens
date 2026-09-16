"""Transparent aggregate and standardized comparison calculations."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Iterable


SCHEMA_VERSION = 1
EPSILON = 1e-12


def analyze_rows(
    rows: Iterable[dict[str, object]], *, seed: int = 20260916, bootstrap: int = 1000
) -> dict[str, object]:
    materialized = list(rows)
    if not materialized:
        raise ValueError("analysis requires at least one row")
    if bootstrap < 0:
        raise ValueError("bootstrap must be non-negative")

    core = _core(materialized)
    intervals = _bootstrap(materialized, seed=seed, repetitions=bootstrap)
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_type": "descriptive_stratified_binary_comparison",
        "seed": seed,
        "row_count": len(materialized),
        **core,
        "bootstrap": intervals,
        "interpretation": {
            "causal_claim": False,
            "statement": (
                "This is a descriptive comparison conditional on the supplied rows, "
                "strata, labels, and weights. It does not establish a causal effect."
            ),
        },
    }


def _core(rows: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, dict[int, list[dict[str, object]]]] = defaultdict(
        lambda: {0: [], 1: []}
    )
    by_group = {0: [], 1: []}
    for row in rows:
        group = int(row["treatment"])
        if group not in (0, 1):
            raise ValueError("treatment values must be binary")
        by_group[group].append(row)
        grouped[str(row["stratum"])][group].append(row)
    if not by_group[0] or not by_group[1]:
        raise ValueError("analysis requires at least one row in each treatment group")

    group_summary = {str(group): _summary(values) for group, values in by_group.items()}
    aggregate_effect = group_summary["1"]["rate"] - group_summary["0"]["rate"]

    strata: list[dict[str, object]] = []
    comparable: list[dict[str, object]] = []
    total_weight = sum(float(row["weight"]) for row in rows)
    comparable_weight = 0.0
    for name in sorted(grouped, key=str.casefold):
        control_rows = grouped[name][0]
        treated_rows = grouped[name][1]
        control = _summary(control_rows) if control_rows else None
        treated = _summary(treated_rows) if treated_rows else None
        pooled_weight = sum(float(row["weight"]) for row in control_rows + treated_rows)
        item: dict[str, object] = {
            "name": name,
            "pooled_weight": pooled_weight,
            "control": control,
            "treated": treated,
            "comparable": bool(control and treated),
        }
        if control and treated:
            item["difference"] = treated["rate"] - control["rate"]
            comparable.append(item)
            comparable_weight += pooled_weight
        else:
            item["difference"] = None
        strata.append(item)
    if not comparable:
        raise ValueError("analysis requires at least one stratum containing both groups")

    standardized_treated = sum(
        float(item["pooled_weight"]) * float(item["treated"]["rate"])
        for item in comparable
    ) / comparable_weight
    standardized_control = sum(
        float(item["pooled_weight"]) * float(item["control"]["rate"])
        for item in comparable
    ) / comparable_weight
    standardized_effect = standardized_treated - standardized_control
    composition_gap = aggregate_effect - standardized_effect

    for item in strata:
        item["pooled_share"] = float(item["pooled_weight"]) / total_weight
        if item["comparable"]:
            item["standardization_share"] = float(item["pooled_weight"]) / comparable_weight
        else:
            item["standardization_share"] = None
        for group, label in ((0, "control"), (1, "treated")):
            summary = item[label]
            if summary:
                summary["group_share"] = summary["weight"] / group_summary[str(group)]["weight"]

    share_gaps = []
    for item in comparable:
        share_gaps.append(
            abs(item["treated"]["group_share"] - item["control"]["group_share"])
        )
    effects = [float(item["difference"]) for item in comparable]
    classification = _classification(aggregate_effect, standardized_effect, effects)
    return {
        "aggregate": {
            "control_rate": group_summary["0"]["rate"],
            "treated_rate": group_summary["1"]["rate"],
            "effect": aggregate_effect,
        },
        "standardized": {
            "control_rate": standardized_control,
            "treated_rate": standardized_treated,
            "effect": standardized_effect,
            "target": "pooled weight distribution over comparable strata",
        },
        "composition_gap": composition_gap,
        "classification": classification,
        "groups": {"control": group_summary["0"], "treated": group_summary["1"]},
        "strata": strata,
        "diagnostics": {
            "strata_total": len(strata),
            "strata_comparable": len(comparable),
            "comparable_weight_share": comparable_weight / total_weight,
            "maximum_group_share_gap": max(share_gaps) if share_gaps else 0.0,
        },
    }


def _summary(rows: list[dict[str, object]]) -> dict[str, float | int]:
    weight = sum(float(row["weight"]) for row in rows)
    successes = sum(float(row["weight"]) * int(row["outcome"]) for row in rows)
    squared = sum(float(row["weight"]) ** 2 for row in rows)
    return {
        "rows": len(rows),
        "weight": weight,
        "success_weight": successes,
        "rate": successes / weight,
        "effective_sample_size": weight * weight / squared,
    }


def _sign(value: float) -> int:
    if value > EPSILON:
        return 1
    if value < -EPSILON:
        return -1
    return 0


def _classification(aggregate: float, standardized: float, effects: list[float]) -> dict[str, object]:
    aggregate_sign = _sign(aggregate)
    standardized_sign = _sign(standardized)
    nonzero = [_sign(effect) for effect in effects if _sign(effect) != 0]
    signs_disagree = aggregate_sign * standardized_sign == -1
    unanimous = bool(nonzero) and all(sign == standardized_sign for sign in nonzero)
    if signs_disagree and unanimous:
        label = "strong_reversal"
        message = "Aggregate and standardized effects point in opposite directions, and every nonzero comparable stratum agrees with the standardized direction."
    elif signs_disagree:
        label = "mixed_reversal"
        message = "Aggregate and standardized effects point in opposite directions, but comparable strata do not all agree."
    elif aggregate_sign == 0 or standardized_sign == 0:
        label = "tie_or_near_zero"
        message = "At least one headline effect is zero or numerically near zero."
    else:
        label = "no_reversal"
        message = "Aggregate and standardized effects point in the same direction."
    return {
        "label": label,
        "message": message,
        "aggregate_sign": aggregate_sign,
        "standardized_sign": standardized_sign,
        "within_strata_unanimous": unanimous,
    }


def _bootstrap(rows: list[dict[str, object]], *, seed: int, repetitions: int) -> dict[str, object]:
    if repetitions == 0:
        return {"requested": 0, "valid": 0, "skipped": 0, "intervals": {}}
    rng = random.Random(seed)
    n = len(rows)
    values = {"aggregate_effect": [], "standardized_effect": [], "composition_gap": []}
    skipped = 0
    for _ in range(repetitions):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        try:
            result = _core(sample)
        except ValueError:
            skipped += 1
            continue
        values["aggregate_effect"].append(float(result["aggregate"]["effect"]))
        values["standardized_effect"].append(float(result["standardized"]["effect"]))
        values["composition_gap"].append(float(result["composition_gap"]))
    intervals = {
        name: {"lower": _percentile(series, 0.025), "upper": _percentile(series, 0.975)}
        for name, series in values.items()
        if series
    }
    return {
        "requested": repetitions,
        "valid": repetitions - skipped,
        "skipped": skipped,
        "method": "row bootstrap percentile interval",
        "confidence_level": 0.95,
        "intervals": intervals,
    }


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction
