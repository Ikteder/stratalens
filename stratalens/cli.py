"""Command-line interface for StrataLens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analysis import analyze_rows
from .io import InputError, load_rows
from .report import render_html, render_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stratalens", description="Audit aggregate versus stratified binary comparisons.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="analyze a row-level CSV file")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--out", type=Path, required=True)
    analyze.add_argument("--seed", type=int, default=20260916)
    analyze.add_argument("--bootstrap", type=int, default=1000)
    analyze.add_argument("--title", default="StrataLens audit")
    analyze.add_argument("--stratum-column", default="stratum")
    analyze.add_argument("--treatment-column", default="treatment")
    analyze.add_argument("--outcome-column", default="outcome")
    analyze.add_argument("--weight-column", default="weight")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = load_rows(
            args.input,
            stratum_column=args.stratum_column,
            treatment_column=args.treatment_column,
            outcome_column=args.outcome_column,
            weight_column=args.weight_column,
        )
        result = analyze_rows(rows, seed=args.seed, bootstrap=args.bootstrap)
    except (InputError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.out / "report.html").write_text(render_html(result, title=args.title), encoding="utf-8")
    (args.out / "overview.svg").write_text(render_svg(result), encoding="utf-8")
    aggregate = float(result["aggregate"]["effect"])
    standardized = float(result["standardized"]["effect"])
    print(f"classification: {result['classification']['label']}")
    print(f"aggregate effect: {aggregate:+.6f}")
    print(f"standardized effect: {standardized:+.6f}")
    print(f"composition gap: {float(result['composition_gap']):+.6f}")
    print(f"wrote: {args.out.resolve()}")
    return 0
