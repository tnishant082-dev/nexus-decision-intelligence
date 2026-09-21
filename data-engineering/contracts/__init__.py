"""Load YAML data contracts from data-engineering/contracts/."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONTRACTS_DIR = Path(__file__).resolve().parent


def load_contracts(directory: Path = CONTRACTS_DIR) -> list[dict[str, Any]]:
    contracts = []
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["_path"] = str(path)
        contracts.append(data)
    return contracts
