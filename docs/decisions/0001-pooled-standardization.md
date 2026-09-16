# Decision 0001: Standardize to the pooled comparable-stratum distribution

Date: 2026-09-16
Status: Accepted

## Context

Raw group rates can differ because outcome rates differ within strata, because the groups contain different stratum shares, or both. A common target distribution is required to compare observed stratum-specific rates on the same mix.

## Decision

Use each comparable stratum's share of pooled analysis weight as the target distribution. Apply those shares to both groups. Exclude strata missing either group from this standardized contrast, report them visibly, and report the share of total pooled weight retained.

## Why

The pooled target is symmetric between treated and control groups, can be explained without a reference population, and is deterministic. It avoids silently choosing either group's composition as the standard.

## Tradeoffs

The target is sample-dependent and may not match a policy population. Excluding non-overlap changes the population represented by the standardized result. The report therefore names the target and reports comparable coverage rather than presenting the result as universal.
