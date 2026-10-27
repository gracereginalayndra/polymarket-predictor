"""Shared serialization, configuration and UTC contracts. No network side effects."""
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def utcnow():
    return int(datetime.now(timezone.utc).timestamp())


def timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value) or value < 0 or value > 1e11:
            raise ValueError("Expected finite epoch SECONDS, not milliseconds")
        return int(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing timestamp")
    if value.isdigit():
        return timestamp(int(value))
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone required: use UTC Z or explicit offset")
    return int(dt.timestamp())


def iso(value):
    return datetime.fromtimestamp(int(value), timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        for n, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError as exc:
                    raise ValueError(f"Invalid JSON at line {n}") from exc


def load_config(path="configs/config.yaml"):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key in ("database", "data_dir", "artifact_dir", "market_filters"):
        value = Path(cfg[key])
        cfg[key] = str(value if value.is_absolute() else ROOT / value)
    cfg["llm"]["prompt_dir"] = str(ROOT / cfg["llm"]["prompt_dir"])
    cfg["config_path"] = str(path)
    return cfg


def load_env(path=None):
    """Small .env reader: no shell evaluation, interpolation or overwriting env."""
    path = Path(path or ROOT / ".env")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def probability(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a probability")
    p = float(value)
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Probability must be finite in [0, 1]")
    return p


def source_fingerprint():
    return digest({str(p.relative_to(ROOT)): p.read_text(encoding='utf-8')
                   for folder in ('src', 'scripts') for p in sorted((ROOT/folder).rglob('*.py'))})


def runtime_info():
    import importlib.metadata
    import platform
    return {'python': platform.python_version(), 'platform': platform.platform(),
            'packages': {name: importlib.metadata.version(name) for name in
                         ('numpy','scipy','pandas','scikit-learn','PyYAML','joblib','matplotlib')}}
