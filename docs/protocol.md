# Evaluation protocol — must be finalized and frozen before the final test period

Status: proposed protocol, NOT an already completed preregistration.

1. Population: explicitly mapped binary Yes/No contracts selected using information available at the cutoff.
   Resolve category filters after the pilot, then freeze them. Record every exclusion.
2. Outcome: final official binary settlement, excluding disputed/unsettled/voided/split outcomes from binary
   scoring. Keep unresolved and excluded cases in coverage accounting. Do not infer labels from a price near 1.
3. Forecast unit: market at a configured 24-hour or 168-hour horizon before its scheduled deadline as known then.
   The `--at now` path is for pilots and is not pooled into the primary fixed-horizon result without amendment.
4. Price benchmark: current two-sided midpoint captured prospectively. Retrospective history has separate
   provenance and may have different semantics; do not combine it uncritically with midpoint benchmarks.
5. Evidence: publication and availability must not exceed the cutoff. Prospective records must also have been
   locally observed by then. Archived content versions need verifiable archival provenance.
6. Model: record provider, exact model/checkpoint, freeze date where relevant, prompt hashes, temperature,
   token limits and retrieval rules. Verify model access with a tiny pilot. No hidden built-in web search.
7. Independent agent contexts omit market probabilities. The verifier receives only the same eligible evidence
   and initial outputs. All probabilities are schema-checked; invented citation IDs invalidate a response.
8. Systems: raw market, constant 50%, recalibrated market, market-feature logistic, no-retrieval LLM,
   single RAG, repeated single RAG, unverified ensemble, verified ensemble, no-social ensemble, and the
   corresponding fitted hybrids. Bayesian correction is a sensitivity model.
9. Split: fixed UTC train_end and validation_end; test begins at validation_end. Purge groups spanning
   boundaries. Training/tuning outcomes must be known by the corresponding fit boundary.
10. Fit: common complete training/validation rows, event-balanced weights, training-only preprocessing.
    Choose regularization by validation Brier score; refit train+validation once; do not tune on test.
11. Primary contrast: verified hybrid versus recalibrated market; event-balanced paired Brier difference.
12. Secondary: raw-market and market-feature comparisons, verifier/retrieval/social/resource-matched ablations,
    log loss, calibration, coverage, source relevance, token cost and latency. Treat these as exploratory unless
    a multiplicity plan is agreed before testing. A positive subgroup finding is not a global result.
13. Uncertainty: event-cluster paired percentile bootstrap with fixed seed and configured draws. Review
    grouping manually; cross-event dependence and small-sample uncertainty remain limitations.
14. Missing predictions: log failures; give common-cohort comparisons plus full resolved-cohort market-fallback
    performance. No silent deletion or replacement of failed AI outputs by fabricated forecasts.
15. Test access: no manual inspection of test outcomes for prompt/model selection. A changed design starts a
    new experiment. Local hashing does not prevent human test peeking; commit a protocol timestamp externally.
16. Contamination: prefer prospective collection. A replay with a later-trained model is exploratory and cannot
    support a clean foresight claim, even when all retrieved documents predate the target cutoff.
17. Timing: save forecast generation time. For prospective runs, enforce a short cutoff-to-generation delay;
    report actual delay and ensure the event was not already known. Compare prices at the same declared cutoff.
18. Final reporting: include cohort construction, source coverage, label delays, model/version changes,
    exclusions, all prespecified systems, uncertainty, compute/cost and failure examples.

## Freeze checklist

Set model, category rules, event-group corrections, source list, split dates, budgets and collection schedule.
Inspect at least a small labelled audit sample of evidence relevance and resolution-rule interpretation.
Run `python -m scripts.freeze_protocol`; retain `protocol_lock.json` with the dissertation experiment record.
The real evaluation command rejects a missing/late/mismatched freeze unless explicitly marked exploratory.

The first demo is synthetic and exempt from real-experiment freeze requirements; its outputs stay labelled synthetic.
