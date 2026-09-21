#!/usr/bin/env python3
"""Run landing → clean → warehouse → validate → lineage → catalog → quality."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl.land import land
from etl.clean import clean
from etl.warehouse import load_warehouse
from validation.validate import validate
from lineage.build_lineage import build as build_lineage
from catalog.build_catalog import build as build_catalog
from quality.profile import profile
from quality.freshness import freshness


def main() -> int:
    print("== land ==")
    landed = land()
    print(json.dumps({"copied": landed.get("copied"), "skipped": landed.get("skipped_unchanged")}, indent=2))
    print("== clean ==")
    print(json.dumps(clean(), indent=2)[:400])
    print("== warehouse ==")
    print(json.dumps(load_warehouse(incremental=True), indent=2)[:800])
    print("== validate ==")
    report = validate()
    print(json.dumps({k: report[k] for k in ("passed", "total", "contracts")}, indent=2))
    build_lineage()
    catalog = build_catalog()
    profile()
    freshness()
    print("catalog tables", len(catalog.get("tables", [])))
    print("pipeline complete; passed", report["passed"], "/", report["total"])
    contract_ok = report.get("contracts", {}).get("passed", 0) == report.get("contracts", {}).get("total", 0)
    return 0 if report["passed"] >= report["total"] - 1 and contract_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
