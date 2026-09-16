# StrataLens Design Specification

Date: 2026-09-16
Status: Approved for implementation
Selection seed: `20260916`
Focused lane: Data science

## Problem

An aggregate treatment or exposure difference can point in the opposite direction from the differences inside relevant strata when group composition is imbalanced. Analysts need a small, reproducible audit that exposes that disagreement without presenting an observational comparison as a causal conclusion.

## Intended user

Data analysts, experiment reviewers, students, and decision teams checking a binary outcome comparison before publishing an aggregate claim.

## Product boundary

StrataLens accepts row-level CSV data containing a stratum, binary treatment, binary outcome, and optional positive weight. It produces a terminal summary, schema-versioned JSON, a standalone HTML report, and a repository-owned SVG overview generated from the same verified result.

It does not infer causality, select confounders, repair sampling bias, fit a predictive model, or certify that a stratification set is sufficient. Results are descriptive and conditional on the supplied rows, strata, labels, and weights.

## Core calculations

1. Validate the complete CSV before analysis.
2. Compute weighted aggregate outcome rates for treated and control rows.
3. Identify strata containing both groups.
4. Compute within-stratum group rates and treated-minus-control differences.
5. Standardize both group rates to the pooled weight distribution over comparable strata.
6. Report the aggregate effect, standardized effect, and composition gap: aggregate minus standardized.
7. Classify a strong reversal only when the aggregate and standardized effects have opposite nonzero signs and every nonzero comparable stratum effect agrees with the standardized sign.
8. Run a deterministic row bootstrap and report percentile intervals for the aggregate effect, standardized effect, and composition gap. Replicates that lack overlap are counted and excluded transparently.
9. Report group effective sample size under weights and the largest stratum-share imbalance.

## Interface

Command:

```text
python -m stratalens analyze INPUT.csv --out OUTPUT_DIR --seed 20260916 --bootstrap 1000
```

Required columns default to `stratum`, `treatment`, and `outcome`. An optional `weight` column defaults to one when absent. Treatment and outcome values must be exactly `0` or `1`; weights must be finite and positive; strata must be non-empty.

## Report design

The report uses a calm dark-blue and warm-coral palette. It leads with the aggregate and standardized effects, explains whether their signs disagree, compares group composition, and lists each comparable stratum with both rates and its difference. Wide tables scroll within their containers. The report remains useful without network access or JavaScript.

## Verification plan

- Unit tests for validation, weighted rates, standardization, strong and mixed reversals, deterministic bootstrap output, incomplete overlap, and safe HTML embedding.
- A deterministic synthetic checkout fixture with three intent strata. Treatment improves outcomes by five percentage points inside every stratum but is concentrated in the lowest-intent stratum, producing a negative aggregate effect and positive standardized effect.
- CLI contract checks for successful analysis and invalid input.
- Python compilation, package build, install, and dependency checks.
- HTML structure and narrow-layout checks, plus browser rendering when available.
- README visual provenance, no-em-dash check, and GitHub rendering check after publication.

## Documentation

The repository will include a portfolio-ready README, this specification, a calculation decision record, a synthetic dataset card, a model non-use card, dated implementation notes, an experiment/verification record, visual provenance, an MIT license, and CI.

## Known limitations to preserve

- Standardization only addresses measured supplied strata.
- Sparse strata can make rates and bootstrap intervals unstable.
- The row bootstrap assumes rows are the sampling units and does not model clusters or repeated subjects.
- Positive input weights are treated as analysis weights; they are not automatically survey-design weights.
- Percentile intervals are descriptive and do not replace a design-aware inferential analysis.
- Binary outcomes and treatments only in version 0.1.
