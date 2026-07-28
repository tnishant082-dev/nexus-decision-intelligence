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
    files = []
    for p in sorted(source.glob("*.parquet")):
        target = dest / p.name
        shutil.copy2(p, target)
        files.append({
            "name": p.name,
            "bytes": target.stat().st_size,
            "sha256": _sha256(target),
        })
    manifest = {
        "landed_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source),
        "file_count": len(files),
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
