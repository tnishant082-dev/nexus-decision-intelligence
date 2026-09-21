"""Load the metric dictionary."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PATH = Path(__file__).resolve().parent / "dictionary.yaml"


def load_dictionary() -> dict[str, Any]:
    return yaml.safe_load(PATH.read_text(encoding="utf-8"))


def metric_names() -> list[str]:
    return list(load_dictionary()["metrics"].keys())
