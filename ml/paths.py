from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"
EXPERIMENTS = Path(__file__).resolve().parent / "experiments"
REGISTRY = Path(__file__).resolve().parent / "registry"
MODELS = Path(__file__).resolve().parent / "models"
