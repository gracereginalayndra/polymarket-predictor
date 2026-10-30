# US House evidence relevance patch

Scope: conservative lexical filtering for US House-control questions. This is not
an all-topic semantic retriever. Other questions retain the original lexical
behaviour and the inspection report explicitly labels them unprofiled.

Before ranking, the filter requires US House context and an election-related
term in the title or the body excerpt actually sent to agents. Explicit mismatched
headline election years are rejected. For supported questions, rank using the
question rather than resolution boilerplate. Time eligibility is unchanged.

This heuristic can miss relevant documents and can admit mixed-topic documents;
manual evidence review remains necessary. Do not interpret a score as a calibrated
relevance probability. This patch does not add source coverage or full-text scraping.

For profiled snapshots with zero retrieved evidence, the agent run logs
insufficient_relevant_evidence and makes no LLM calls for that snapshot (including
its comparisons). This is a coverage failure, not a generated forecast. The normal
client still requires valid configuration. Audit refusals rather than silently
removing difficult events from evaluation.

Install the provided HX2605_retrieval_fix.py from the project root while no agents
are running. It checks the original two files against their ZIP versions, refuses
unrecognised edits, and backs up affected existing files under backups/. It does
not change databases, credentials, configuration or existing forecasts.

Validate:
python -m unittest tests.test_retrieval_relevance -v
python -m scripts.inspect_retrieval --config configs/live_pilot.yaml

The inspector opens SQLite read-only, performs no network or LLM requests and
prints rejection reasons. The original four reported unrelated headline fixtures
are rejected. Your actual result depends on the stored document bodies; review any
remaining candidates. Zero documents is correct when no relevant evidence exists.

Do not ingest newer evidence as if it existed at an old cutoff. Use new snapshots
for live collection, or explicitly verified archival content for historical work.
Source changes cause new run IDs: old forecast/model bundles remain auditable but
are not compatible with newly generated runs. No need to rerun the synthetic demo
on the slow server just to inspect retrieval.

Local verification: 47 unittest tests passed, including the original full synthetic
integration test and 11 added relevance/coverage tests. Not yet installed on CUHK.
