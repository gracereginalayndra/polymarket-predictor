# Week 1–7 completion matrix and recovery plan

**Status: implementation delivered; real empirical Week 7 completion is not claimed.**
The original plan has seven weeks of work, not seven folders. This document keeps code, validation and
research evidence separate so you can give your supervisor an accurate progress update.

| Planned week | Delivered implementation/documentation | Verification | Remaining empirical/academic dependency |
|---|---|---|---|
| 1: literature, RQ, scope | RQ, hypotheses, critical framework, initial primary-source matrix | Report reviewed; primary documentation consulted | Full-paper synthesis, final scope and supervisor agreement |
| 2: APIs, markets, database | Gamma/CLOB/Data v2 adapters, RSS/GDELT/Reddit/import paths, SQL schema, data specification | Contract tests and a small live pilot | Confirm domain coverage, provider access, category choice and event grouping |
| 3: historical collection | Raw-response archives, pagination, explicit history adapters and audited imports | Live ingestion and offline contract tests | A sufficiently large verified point-in-time historical dataset; history availability does not imply valid past metadata/news |
| 4: cleaning, horizons, splits | Versioned as-of snapshots, stale/settlement rejection, fixed horizons, chronological/group-purged splits, label-maturity rules | Automated leakage tests and full synthetic integration | Audit real evidence/labels, choose dates, acquire enough independent events |
| 5: baselines | Raw market, constant 50%, market recalibration, market-feature logistic, no-retrieval LLM, RAG and repeated-call controls | Metric/model tests; synthetic fitted models; raw live baselines when quotes available | Real fitted/evaluated baselines need mature labels and, for LLM baselines, credentials |
| 6: agents | News/reference-class agents, verifier, orchestrator, schema validation, prompt versions, caching and request budgets | Synthetic end-to-end run and real-adapter response fixture | Real provider access, citation/relevance audit and recorded real forecasts |
| 7: Bayesian/logistic aggregation | Six logistic models plus Bayesian logistic correction, validation tuning, fit manifests and saved parameters | Seven models fitted on synthetic data | Fit on legitimate real forecast/outcome pairs; document the actual sample and uncertainty |

## Evidence delivered

- `examples/test_results.txt`: executed test output, including an integration test.
- `examples/synthetic_demo_summary.json`: counts and explicit synthetic-only status.
- `examples/synthetic_evaluation.json` and calibration image: software demonstration only.
- `examples/live_pilot_status.json`: actual API/data status from this environment.
- `examples/build_verification.json`: package/runtime/test summary.

Generated synthetic scores must never be copied into a dissertation table as real forecasting performance.
Likewise, a provider response fixture tests an adapter, not a live paid LLM experiment.

## What blocks genuine real-data completion

1. No LLM credentials/model choice were supplied. A valid model call cannot be fabricated.
2. Historical market/news versions and model-weight contamination need a defensible plan.
3. Enough independent event groups must resolve before training/tuning boundaries.
4. Actual category, time window, resource budget and final protocol require informed project decisions.

The code is structured to expose these blockers rather than silently filling them with synthetic results.

## Recovery sequence

**First session:** install, run tests/demo, inspect schema and a real evidence packet; confirm the server can
reach the chosen data sources and LLM provider. Bring the scope/timing risks to your supervisor promptly.

**Next working session:** select the first market category using the access audit, agree a forecast horizon,
inspect approximately 20–30 candidate markets, choose model/budget, and start a three-snapshot paid pilot.
Check question interpretation, citations, latency and cost before increasing volume.

**Following sessions:** collect prospective data on a regular schedule; obtain reviewed archival data if
available; freeze the protocol and prompts after the pilot; run raw/statistical baselines as labels mature.
Measure independent event counts, missing evidence and paired-loss variance. A small pilot is not a final study.

**After sufficient labels mature:** fit the aggregation models; keep future test outcomes untouched; run
the held-out comparisons, ablations and confidence intervals. Write the methods and limitations alongside
the experiment rather than waiting until the final week.

Calendar time to resolution cannot be compressed by more code. If the remaining project deadline is too
short for a credible prospective sample, agree a smaller replication/archival study with explicitly bounded
claims. The grade-oriented choice is a defensible completed study, not a claim that every original ambition
has been achieved regardless of evidence.
