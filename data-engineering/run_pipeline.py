#!/usr/bin/env python3
"""Run landing → clean → warehouse → validate → lineage → catalog."""
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

def main() -> int:
    print("== land ==")
    print(json.dumps(land(), indent=2)[:400])
    print("== clean ==")
    print(json.dumps(clean(), indent=2)[:400])
    print("== warehouse ==")
    print(json.dumps(load_warehouse(), indent=2)[:600])
    print("== validate ==")
    report = validate()
    print(json.dumps(report, indent=2)[:600])
    build_lineage()
    build_catalog()
    print("pipeline complete; passed", report["passed"], "/", report["total"])
    return 0 if report["passed"] >= report["total"] - 1 else 1

if __name__ == "__main__":
    raise SystemExit(main())
