"""Validate YAML data contracts against DuckDB tables."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
DB = ROOT / "warehouse" / "nexus.duckdb"
OUT = ROOT / "validation" / "contract_report.json"


def _load_contracts() -> list[dict[str, Any]]:
    items = []
    for path in sorted(CONTRACTS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["_file"] = path.name
        items.append(data)
    return items


def validate_contracts(db_path: Path = DB) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    results = []
    passed = 0
    total = 0
    for spec in _load_contracts():
        table = spec.get("table")
        checks = []
        total += 1
        if table not in tables:
            checks.append({"check": "table_exists", "passed": False, "detail": table})
            results.append({"contract": spec["_file"], "table": table, "passed": False, "checks": checks})
            continue
        cols = {c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()}
        missing = [c for c in spec.get("required_columns", []) if c not in cols]
        checks.append({"check": "required_columns", "passed": not missing, "missing": missing})
        pk = spec.get("primary_key")
        if pk and pk in cols:
            n_dup = con.execute(
                f"SELECT COUNT(*) - COUNT(DISTINCT {pk}) FROM {table}"
            ).fetchone()[0]
            checks.append({"check": "primary_key_unique", "passed": n_dup == 0, "duplicate_extra": int(n_dup)})
        for flag in spec.get("flag_columns", []):
            if flag not in cols:
                checks.append({"check": f"flag_{flag}", "passed": False, "detail": "missing"})
                continue
            mn, mx = con.execute(f"SELECT MIN({flag}), MAX({flag}) FROM {table}").fetchone()
            ok = mn in (0, 1, None) and mx in (0, 1, None)
            checks.append({"check": f"flag_{flag}_01", "passed": ok, "min": mn, "max": mx})
        for fk in spec.get("foreign_keys", []):
            ref = fk["ref_table"]
            if ref not in tables:
                checks.append({"check": f"fk_{fk['column']}", "passed": False, "detail": "ref missing"})
                continue
            orphans = con.execute(
                f"""
                SELECT COUNT(*) FROM {table} t
                LEFT JOIN {ref} r ON t.{fk['column']} = r.{fk['ref_column']}
                WHERE r.{fk['ref_column']} IS NULL AND t.{fk['column']} IS NOT NULL
                """
            ).fetchone()[0]
            checks.append({"check": f"fk_{fk['column']}", "passed": orphans == 0, "orphans": int(orphans)})
        ok = all(c["passed"] for c in checks)
        passed += int(ok)
        results.append({"contract": spec["_file"], "table": table, "passed": ok, "checks": checks})
    con.close()
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "total": total,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(validate_contracts(), indent=2)[:2000])
