PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS markets (
 market_id TEXT PRIMARY KEY, condition_id TEXT NOT NULL, event_group TEXT NOT NULL,
 yes_token TEXT NOT NULL, no_token TEXT NOT NULL, yes_index INTEGER NOT NULL,
 source_kind TEXT NOT NULL CHECK(source_kind IN ('real','synthetic'))
);
CREATE TABLE IF NOT EXISTS market_versions (
 version_id TEXT PRIMARY KEY, market_id TEXT NOT NULL REFERENCES markets(market_id),
 available_at INTEGER NOT NULL, observed_at INTEGER NOT NULL,
 question TEXT NOT NULL, rules TEXT NOT NULL, scheduled_end INTEGER NOT NULL,
 category TEXT NOT NULL, is_open INTEGER NOT NULL, liquidity REAL, volume REAL,
 provenance TEXT NOT NULL, raw_ref TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS metadata_asof ON market_versions(market_id,available_at);
CREATE TABLE IF NOT EXISTS prices (
 price_id TEXT PRIMARY KEY, market_id TEXT NOT NULL REFERENCES markets(market_id),
 timestamp INTEGER NOT NULL, available_at INTEGER NOT NULL, observed_at INTEGER NOT NULL,
 price REAL NOT NULL CHECK(price >= 0 AND price <= 1),
 price_kind TEXT NOT NULL, resolution_seconds INTEGER NOT NULL,
 bid REAL, ask REAL, provenance TEXT NOT NULL, raw_ref TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS prices_asof ON prices(market_id,timestamp,available_at);
CREATE TABLE IF NOT EXISTS documents (
 document_id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
 source TEXT NOT NULL, source_type TEXT NOT NULL CHECK(source_type IN ('news','social','external')),
 published_at INTEGER NOT NULL, available_at INTEGER NOT NULL, observed_at INTEGER NOT NULL,
 content_hash TEXT NOT NULL, provenance TEXT NOT NULL, raw_ref TEXT NOT NULL,
 source_kind TEXT NOT NULL CHECK(source_kind IN ('real','synthetic')),
 content_kind TEXT NOT NULL, UNIQUE(url,content_hash)
);
CREATE INDEX IF NOT EXISTS documents_asof ON documents(available_at,published_at);
CREATE TABLE IF NOT EXISTS resolutions (
 market_id TEXT PRIMARY KEY REFERENCES markets(market_id),
 outcome INTEGER NOT NULL CHECK(outcome IN (0,1)), resolved_at INTEGER NOT NULL,
 label_available_at INTEGER NOT NULL, observed_at INTEGER NOT NULL,
 source TEXT NOT NULL, status TEXT NOT NULL CHECK(status='final'), raw_ref TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
 snapshot_id TEXT PRIMARY KEY, market_id TEXT NOT NULL REFERENCES markets(market_id),
 version_id TEXT NOT NULL REFERENCES market_versions(version_id),
 cutoff INTEGER NOT NULL, horizon_hours REAL NOT NULL, market_price REAL NOT NULL,
 price_id TEXT NOT NULL REFERENCES prices(price_id), features_json TEXT NOT NULL,
 mode TEXT NOT NULL, source_kind TEXT NOT NULL, config_hash TEXT NOT NULL,
 UNIQUE(market_id,cutoff,config_hash)
);
CREATE TABLE IF NOT EXISTS forecast_runs (
 run_id TEXT PRIMARY KEY, created_at INTEGER NOT NULL, config_json TEXT NOT NULL,
 config_hash TEXT NOT NULL, model TEXT NOT NULL, provider TEXT NOT NULL,
 prompt_hash TEXT NOT NULL, source_kind TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS forecasts (
 forecast_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES forecast_runs(run_id),
 snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id), system TEXT NOT NULL,
 probability REAL CHECK(probability >= 0 AND probability <= 1),
 status TEXT NOT NULL, result_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
 generated_at INTEGER NOT NULL, UNIQUE(run_id,snapshot_id,system)
);
CREATE TABLE IF NOT EXISTS pipeline_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at INTEGER NOT NULL,
 stage TEXT NOT NULL, status TEXT NOT NULL, detail_json TEXT NOT NULL
);
