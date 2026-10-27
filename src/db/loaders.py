"""Append-only records; conflicting identities fail instead of overwriting history."""
import sqlite3
from pathlib import Path

from src.common import canonical, digest, utcnow

TABLES = {'markets', 'market_versions', 'prices', 'documents', 'resolutions',
          'snapshots', 'forecast_runs', 'forecasts'}


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(Path(__file__).with_name("schema.sql").read_text())
    return con


def insert(con, table, record):
    if table not in TABLES:
        raise ValueError("Unknown table")
    allowed = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
    if not set(record).issubset(allowed):
        raise ValueError(f"Unknown fields for {table}: {set(record)-allowed}")
    fields = list(record)
    key = next(r[1] for r in con.execute(f"PRAGMA table_info({table})") if r[5])
    old = con.execute(f"SELECT * FROM {table} WHERE {key}=?", (record[key],)).fetchone()
    if old:
        if any(old[k] != v for k, v in record.items()):
            raise ValueError(f"Immutable record conflict: {table}/{record[key]}")
        return False
    sql = f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})"
    with con:
        con.execute(sql, tuple(record[k] for k in fields))
    return True


def rows(con, sql, params=()):
    return [dict(r) for r in con.execute(sql, params)]


def event(con, stage, status, details):
    with con:
        con.execute("INSERT INTO pipeline_events(created_at,stage,status,detail_json) VALUES(?,?,?,?)",
                    (utcnow(), stage, status, canonical(details)))


def add_document(con, record):
    record = dict(record)
    if record['available_at'] < record['published_at']:
        raise ValueError("Document available before publication")
    if record['provenance'] == 'prospective' and record['available_at'] < record['observed_at']:
        raise ValueError("Prospective availability must be observation time or later")
    if record['provenance'] not in ('prospective', 'archive_verified', 'synthetic'):
        raise ValueError("Unverified document provenance")
    if record['provenance'] == 'archive_verified' and not record['raw_ref']:
        raise ValueError("Archive provenance requires a reference")
    record['content_hash'] = digest([record['title'], record['body']])
    record['document_id'] = digest([record['url'], record['content_hash']])
    # An unchanged page seen again retains its first observed availability.
    old = con.execute("SELECT document_id FROM documents WHERE document_id=?", (record['document_id'],)).fetchone()
    return False if old else insert(con, 'documents', record)
