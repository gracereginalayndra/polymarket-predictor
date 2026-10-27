# HX2605 — Incremental Predictive Value of Multi-Agent AI

Research forecasting framework for Grace Regina Layndra and Kent Justin Henly.
Supervisor: XU Hong, Henry. No orders, wallets, private keys, real trades or simulated profit claims.

**This package implements the pipeline through model fitting and includes evaluation infrastructure.
It does not claim that your real-data Week 7 research experiment has been completed.**
The included integration evidence is explicitly synthetic. Real research requires a chosen accessible
LLM, valid point-in-time data, mature outcome labels, a frozen protocol, and sufficient event groups.
Read [the status matrix](docs/week7_status.md) before describing progress to your supervisor.

## Start here

1. [Framework and feasibility](docs/framework.md): architecture, data flow, training, limitations.
2. [File guide](docs/file_guide.md): purpose of every source file and output.
3. [Research question](docs/research_question.md) and [protocol](docs/protocol.md).
4. [Data specification](docs/data_spec.md): schema, timestamps, import contracts.
5. [Runbook](docs/runbook.md): commands, scheduling, failure recovery, GitHub.
6. [Week 7 status and recovery plan](docs/week7_status.md).

## Install — Python 3.10, 3.11 or 3.12

Run commands **inside the extracted `hx2605` directory**. Python 3.12 was tested in the build environment;
the lock pins were chosen to support Python 3.10 as well. Verify on your CUHK server before long runs.

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip check
python -m unittest discover -s tests -v
python -m scripts.run_demo
```

Windows PowerShell (activation is optional; calling the executable avoids execution-policy changes):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scripts.run_demo
```

The offline demo generates **140 synthetic event groups, 280 contracts and 560 forecast snapshots**.
It exercises collection-shaped records, SQLite, temporal retrieval, eight agent/baseline outputs,
seven fitted models, purged splits, Brier/log loss, clustered uncertainty and calibration plotting.
Its fake LLM backend reads noisy synthetic signals, not real outcomes. **Do not cite its scores as FYP findings.**

Look in `artifacts/demo/demo_summary.json`; it identifies the experiment output directory containing
`training_manifest.json`, `models.joblib`, `evaluation.json`, `test_predictions.csv`, and `calibration.png`.

## Real-data path

Copy `.env.example` to `.env`, then set your provider's chat-completions base URL, API key and model ID.
No provider is selected or paid account assumed. Set `configs/config.yaml` before running a paid batch.
The call budget is a request-count guard, not a monetary spending limit.

```bash
python -m scripts.run_ingest --stages markets,quotes,news
python -m scripts.build_dataset --at now
python -m scripts.run_agents --limit 3
```

`--at now` is a pipeline pilot, not the pre-registered fixed-horizon experiment. Begin with three
snapshots to verify output validity, latency, token costs and citations. No `.env` is necessary for
public market/news ingestion. News and social access can fail independently.

For a research experiment: choose categories and split dates, verify a model ID and budget, review the
protocol, freeze it **before the final test period**, and collect prospective data continuously.

```bash
python -m scripts.freeze_protocol
python -m scripts.run_ingest --stages markets,quotes,news,social,resolutions
python -m scripts.build_dataset
python -m scripts.run_agents
python -m scripts.fit_calibrator --run-id YOUR_RUN_ID
python -m scripts.run_eval --run-id YOUR_RUN_ID
```

These commands deliberately fail if prerequisites are missing. A successful installation or synthetic
training run does not unlock real-data fitting. Record the run ID returned by `run_agents`.
Historical records fetched today are archived but **not silently treated as available in the past**.
See the runbook for reviewed archival imports and restrictions on retrospective LLM evaluation.

## Design choices

- SQLite + immutable JSON archives; CSV experiment manifests. One collector/writer process on local disk.
- Stateless sparse text retrieval using hashed unigrams/bigrams, with time filtering **before** ranking.
- Independent news and reference-class agents; one verification step; shared frozen evidence.
- Pretrained LLM inference. No expensive foundation-model training is required.
- Regularized logistic stacking is primary; a Normal-prior, Laplace-approximated logistic correction is a sensitivity model.
- Market recalibration and market-feature baselines distinguish AI value from simple price correction.
- Entire event groups are kept apart across temporal splits; labels must be available before fitting.
- Brier score is primary; log loss, calibration, coverage, latency and cost are complementary.

## Limits and safe failure

The API adapters are version-specific and validate their response shapes. The current Data v2 adapter
and an explicitly selected legacy CLOB adapter are separate: no hidden fallback changes your experiment.
The Gamma adapter supports explicit Yes/No CTF token arrays; unfamiliar protocol/market formats are
quarantined rather than guessed. The Reddit adapter is public-read only and may be blocked; licensed
JSONL imports are supported. Source access and historical coverage are empirical prerequisites.

The local protocol hash is an audit aid, not independent preregistration. Commit or publish it before
test forecasts. API-generated text is not guaranteed bit-identical on rerun, even at temperature zero;
cached requests/responses preserve the original observations. Only load locally generated joblib files.

## Sharing and GitHub

The archive is a source project, not an existing Git checkout. Read `docs/runbook.md` for a safe first
commit. `.env`, databases, API caches, datasets, virtual environments and generated models are ignored.
The `examples/` directory contains compact, clearly labelled verification artifacts, not real experimental conclusions.
Keep copyrighted source content out of public Git; publish identifiers/provenance when redistribution is restricted.

Sources and dated technical decisions are in [references](docs/references.md) and [decision log](docs/decisions_log.md).
