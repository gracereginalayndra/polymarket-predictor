# Data specification and provenance contracts

## Storage model

`src/db/schema.sql` is the executable schema. SQLite foreign keys and probability constraints are enabled.
Records are immutable by identity: an identical insert is idempotent; a conflicting insert fails. Repeated
unchanged document fetches retain first availability. Revised document content creates a new version/hash.
Use one writer on local disk. Back up with SQLite's backup API or when the process is stopped, not by copying
only the main file while its WAL contains uncheckpointed changes.

| Table | Primary identity | Purpose and main fields |
|---|---|---|
| markets | market_id | condition_id; reviewed event_group; explicit YES/NO token IDs and YES index; real/synthetic source kind |
| market_versions | version_id | Versioned question/rules; scheduled_end; category; open state; liquidity/volume; available_at and observed_at |
| prices | price_id | Market, event timestamp, availability/observation, probability, bid/ask, price kind, resolution grain, provenance |
| documents | document_id | URL, title/body, source/type, content hash/version, publication/availability/observation, content kind and provenance |
| resolutions | market_id | Final binary outcome; resolution time; label availability; source; raw reference |
| snapshots | snapshot_id | Market/version/price references; cutoff; horizon; computed market features; config hash; mode and source kind |
| forecast_runs | run_id | Configuration, prompt hash, provider/model, source kind; accompanying JSON records code hash/runtime |
| forecasts | forecast_id | Run/snapshot/system, probability, generation time, evidence IDs, complete structured agent output |
| pipeline_events | event_id | Dated stage status, failures, exclusions and collection reports |

IDs are strings. No numeric coercion is applied to long token IDs. Outcome order is explicitly mapped;
the first token is not assumed to be YES. Market grouping initially follows the platform event ID.
`polymarket.group_overrides` maps market IDs to broader reviewed groups when necessary. Set it before
collection into a fresh experiment DB; immutable existing market identities are not silently rewritten.

## Timestamp meanings

| Field | Meaning | What it must not be confused with |
|---|---|---|
| published_at | Source-reported publication, or documented discovery time for GDELT headlines | Proof that the current text existed then |
| available_at | Earliest admissible availability of this exact version in this experiment | Market creation or article date alone |
| observed_at | Local collection/ingestion time | Earlier public availability |
| cutoff | Information boundary for one forecast | Actual time the result was generated |
| generated_at | When a forecast was logged | A backdated simulated forecast time |
| scheduled_end | Deadline from the metadata version available then | Actual final settlement time |
| resolved_at | Final outcome settlement time | A pending proposal or a high market price |
| label_available_at | When the training process could legitimately know the final label | The event's scheduled date |

Every timestamp is timezone-aware on input and UTC epoch **seconds** internally. Naive datetimes and
millisecond epoch inputs are rejected. The live CLOB midpoint is timestamped at local observation; source
book timestamps are not treated as earlier admission to the dataset.

## Provenance classes

- `prospective`: the process observed the record; availability cannot precede local observation.
- `archive_verified`: an explicit, manually reviewed archive establishes this exact version's earlier availability.
- `retrospective_unverified`: history fetched now without sufficient as-of provenance; archived but excluded from strict snapshots.
- `synthetic`: generated demonstration only, isolated by config, database and output labels.

The code can enforce declared timestamps and references. It cannot authenticate a falsified archive claim.
Keep the actual archive/capture proof and review log. `--archive-verified` is an attestation, not a way to turn
ineligible records into good evidence merely by changing their timestamp fields.

## Snapshot construction

For market m at cutoff t: select the latest metadata version available by t; verify that its deadline is
after t; select the most recent eligible non-settlement price no later than t; check age and market filters;
compute lag features only from earlier available records. Store exact version and price IDs.

For configured horizons, a candidate is accepted only if the deadline used to generate it matches the
deadline actually visible at the cutoff. Updating a market's end date today cannot create valid old snapshots.
Current cumulative volume/liquidity can filter current snapshots, but cannot filter historical snapshots
unless a historical metadata version exists. This avoids using final trading volume for past selection.

The API history adapters save their original grain; missing fine history is not fabricated by interpolation.
Data v2 settlement rows with `resolution_seconds=0` are excluded. Gamma's final outcomePrices are never labels.

## Evidence import contract

`python -m scripts.import_data --kind documents --file YOUR_FILE.jsonl`

Each JSONL object has these required fields:

| Field | Type | Rule |
|---|---|---|
| url, title, body, source | strings | Actual source and exact eligible content version |
| source_type | string | news, social or external |
| content_kind | string | headline, feed_summary, post, article or release_vintage, as appropriate |
| published_at, available_at, observed_at | ISO strings or epoch seconds | Preserve separate meanings |
| provenance | string | prospective or archive_verified for real evidence |
| raw_ref | string | Capture file/archive reference supporting the version |
| source_kind | string | Must be real on the research import command |

Do not supply document_id/content_hash: they are computed. Missing data fails explicitly.
RSS imports use the feed's title/summary. GDELT does not deliver full text in this implementation.
The code does not fetch arbitrary article URLs or execute instructions in retrieved content.

`--kind releases` accepts CSV columns `series,period,value,units,released_at,source,source_url`.
This preserves the value as imported but marks availability at import time. Historical economic vintages
need the documented archive path; downloading today's revised series is insufficient for past forecasts.

## Reviewed market/price/label imports

`--kind markets`, `market_versions`, `prices` and `resolutions` accept JSONL matching the corresponding
schema columns. Import markets first, then metadata/prices and finally labels. Use `--archive-verified` for
the latter three. Assign stable IDs to distinct archival versions; include source references and correct
available/observed times. See the SQL schema for all required columns. No fabricated example outcome file
is shipped as research data.

For resolutions, require final binary status, an official source/capture, resolved_at <= label_available_at,
and the correct YES mapping. Existing conflicting labels fail and require a review. Public v2 resolution
checks record label availability conservatively at observation time; historical training needs reviewed
archival label-availability evidence or a later fit boundary.

## Dataset exports and splits

The CSV dataset contains one row per snapshot plus labels joined only for model/evaluation use. Agent
contexts are created by an allowlist, not by serializing the full row. `train_manifest.csv`,
`validation_manifest.csv`, `test_manifest.csv` and `purged_manifest.csv` show exact membership.

An entire event group crossing a boundary is purged. A group with an unknown or late label is excluded from
the corresponding training/tuning set. The test manifest retains unresolved rows. Evaluation counts them
but scores only final labels known at evaluation time. Never turn unresolved outcomes into zeros.

## Output lineage

Run ID binds config, provider/model/base URL, prompts and source fingerprint. `run_metadata.json` records
runtime package versions. `training_manifest.json` records hyperparameters, coefficients and trained IDs.
LLM caches include request content, generation time, returned model and usage when the provider supplies it.
Credentials are not cached. Agent probability, short rationale, citations and limitations are stored;
unsupported claims are still subject to manual factual review.
