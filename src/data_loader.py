"""
Load and validate ship dataset and global parameters.
Ship data: vessel ID, name, type; DWT; Vref; P, ael, abl; fuel types; sfc_me, sfc_ae, sfc_ab; safety score.
Global params: emission factors, LCV, fuel price USD/GJ, carbon price, CAPEX, safety adjustment rates.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def load_ships(path: str | Path) -> pd.DataFrame:
    """Load ship dataset (CSV expected). Validate required columns."""
    path = Path(path)
    if not path.suffix:
        path = path / "ships.csv"
    df = pd.read_csv(path)
    required = [
        "vessel_id", "vessel_name", "vessel_type", "dwt",
        "vref", "P", "ael", "abl",
        "main_engine_fuel_type", "aux_engine_fuel_type", "aux_boiler_fuel_type",
        "sfc_me", "sfc_ae", "sfc_ab",
        "safety_score",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ship dataset missing columns: {missing}")
    return df


def load_global_params(path: str | Path) -> dict[str, Any]:
    """Load global parameters (YAML or JSON)."""
    path = Path(path)
    if not path.exists():
        path = path / "global_params.yaml"
    with open(path) as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        if path.suffix == ".json":
            import json
            return json.load(f)
    raise ValueError(f"Unsupported config format: {path.suffix}")


def load_config(path: str | Path) -> dict[str, Any]:
    """Load project config (e.g. config/params.yaml)."""
    path = Path(path)
    with open(path) as f:
        return yaml.safe_load(f)
