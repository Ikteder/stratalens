"""Generate the deterministic synthetic checkout fixture."""

from __future__ import annotations

import csv
from pathlib import Path


BLOCKS = [
    ("low_intent", 0, 100, 10),
    ("low_intent", 1, 600, 90),
    ("medium_intent", 0, 300, 90),
    ("medium_intent", 1, 300, 105),
    ("high_intent", 0, 600, 360),
    ("high_intent", 1, 100, 65),
]


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "examples" / "checkout_demo.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["stratum", "treatment", "outcome"])
        for stratum, treatment, count, successes in BLOCKS:
            for index in range(count):
                writer.writerow([stratum, treatment, 1 if index < successes else 0])
    print(f"wrote {target} with {sum(block[2] for block in BLOCKS)} rows")


if __name__ == "__main__":
    main()
