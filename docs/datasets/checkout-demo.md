# Dataset card: synthetic checkout composition reversal

Date created: 2026-09-16
Generator: `scripts/generate_demo.py`
License: MIT with the repository

## Purpose

This fixture verifies a known composition reversal. It is entirely synthetic and makes no claim about a real experiment, customer population, or product.

## Schema

| Column | Type | Meaning |
|---|---|---|
| `stratum` | string | Synthetic visitor intent: low, medium, or high |
| `treatment` | binary integer | 0 for control, 1 for treatment |
| `outcome` | binary integer | Synthetic conversion indicator |

## Construction

| Intent | Control rows | Control rate | Treated rows | Treated rate |
|---|---:|---:|---:|---:|
| Low | 100 | 10% | 600 | 15% |
| Medium | 300 | 30% | 300 | 35% |
| High | 600 | 60% | 100 | 65% |

Every stratum has a +5 percentage point treated-minus-control difference. Composition is deliberately reversed between low and high intent, causing the raw aggregate difference to be -20 percentage points.

## Quality and exclusions

The generator writes exactly 2,000 complete rows. There are no missing values, duplicates with identity semantics, sampling clusters, dates, or personally identifying fields. Outcome order within each block is deterministic and must not be interpreted as temporal order.
