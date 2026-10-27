# Research question and hypotheses — draft for supervisor review

## Primary question

On selected binary Polymarket events, does a retrieval-grounded, verified multi-agent signal improve
event-balanced Brier score over a contemporaneous market-only recalibration model, under strict temporal
information constraints and an untouched chronological test cohort?

## Primary estimand

Mean paired Brier-loss difference `hybrid_verified - market_calibrated`, equally weighting underlying event
groups and then contracts within each event. Negative values favor the AI hybrid. The question concerns
predictive performance, not causal market efficiency or trading profitability.

## Hypotheses

- H1: the verified hybrid has lower expected Brier score than calibrated market prices.
- H2, secondary: verification improves on an unverified ensemble.
- H3, secondary: specialized multi-agent forecasts improve on a repeated single-agent baseline with comparable resources.
- H4, secondary: removing social evidence worsens performance in the cohort with social coverage.
- H5, secondary: retrieval improves on question-only inference, conditional on adequate evidence coverage.

H4 is not testable if the social source is unavailable or returns no eligible content. Report that limitation
instead of describing identical-input runs as proof that social information has no value. H5 changes both the
retrieval context and the tailored prompt in this implementation; interpret it as the configured system
comparison, not a pure causal effect of retrieval. A same-prompt ablation can be added as a separately specified experiment.

## Scope proposed for the pilot

Start with binary, clearly worded contracts with sufficient liquidity and a resolvable near-term deadline.
Audit 20–30 candidates across one or two news-rich categories before fixing categories. Avoid minute-scale
crypto up/down markets, open-ended deadlines and ambiguous resolution rules. Do not pick only cases the
AI appears likely to win. Record the full selection/exclusion ledger.

Category choices and split dates remain deliberately unset in the production config: they must reflect
the markets and collection window actually available, not invented empirical assumptions. The current
all-category config is a discovery pilot, not a finalized research scope.

## Success criteria

Engineering: a reproducible run reconstructs every forecast's rules, price, evidence, prompt, model and output.
Scientific: a transparent comparison estimates the effect with uncertainty and tests plausible alternatives.
A statistically inconclusive or negative result can meet the scientific criteria. No grade is promised.

## Novelty boundary

Do not claim to invent retrieval-augmented forecasting, forecast aggregation, or dynamic forecasting
benchmarks. The contribution is the selected auditable experimental comparison and its empirical findings.
Review the related work matrix in `references.md` before finalizing the dissertation introduction.
