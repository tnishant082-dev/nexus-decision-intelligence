"""Land star-schema parquet extracts into landing zone (copy + manifest)."""
from __future__ import annotations
import hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data"
LANDING = Path(__file__).resolve().parents[1] / "landing"

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def land(source: Path = SRC, dest: Path = LANDING) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    prev_manifest = {}
    manifest_path = dest / "manifest.json"
    if manifest_path.exists():
        try:
            prev_manifest = {f["name"]: f.get("sha256") for f in json.loads(manifest_path.read_text()).get("files", [])}
        except (json.JSONDecodeError, TypeError):
            prev_manifest = {}
    files = []
    copied = 0
    skipped = 0
    for p in sorted(source.glob("*.parquet")):
        target = dest / p.name
        digest = _sha256(p)
        if target.exists() and prev_manifest.get(p.name) == digest:
            skipped += 1
            files.append({
                "name": p.name,
                "bytes": target.stat().st_size,
                "sha256": digest,
                "skipped": True,
            })
            continue
        shutil.copy2(p, target)
        copied += 1
        files.append({
            "name": p.name,
            "bytes": target.stat().st_size,
            "sha256": digest,
            "skipped": False,
        })
    manifest = {
        "landed_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source),
        "file_count": len(files),
        "copied": copied,
        "skipped_unchanged": skipped,
        "incremental": True,
        "files": files,
        "sources_cited": [
            "DataCo Smart Supply Chain (Kaggle / public extract) — primary OMS/TMS/WMS grain",
            "Online Retail II (UCI / public) — customer/retail enrichment tokenized in dim_customer",
        ],
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest

if __name__ == "__main__":
    print(json.dumps(land(), indent=2)[:800])
