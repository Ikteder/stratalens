# Model card: no trained model

Date: 2026-09-16

StrataLens does not train, load, or call a machine-learning model. It performs deterministic weighted summaries, direct standardization, rule-based classification, and a seeded nonparametric row bootstrap.

There is no learned parameter set, train/validation/test split, inference service, accuracy claim, or model artifact. The main risks come from study design, supplied strata, overlap, weights, row dependence, and interpretation rather than predictive-model error.
