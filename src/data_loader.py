"""
Load and validate ship dataset and global parameters.
Ship data: vessel ID, name, type; DWT; Vref; P, ael, abl; fuel types; sfc_me, sfc_ae, sfc_ab; safety score.
Global params: emission factors, LCV, fuel price USD/GJ, carbon price, CAPEX, safety adjustment rates.
Supports given_data format: vessel_movements_dataset.csv (AIS rows → one row per vessel).
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

# Column names required for cost model and optimization
REQUIRED_SHIP_COLUMNS = [
    "vessel_id", "vessel_type", "dwt",
    "vref", "P", "ael", "abl",
    "main_engine_fuel_type", "aux_engine_fuel_type", "aux_boiler_fuel_type",
    "sfc_me", "sfc_ae", "sfc_ab",
    "safety_score",
]

# Given data (vessel_movements_dataset.csv) → internal names
GIVEN_DATA_COLUMN_MAP = {
    "mep": "P",
    "boil_engine_fuel_type": "aux_boiler_fuel_type",
    "vessel_type_new": "vessel_type",
}


def load_vessel_movements_ships(path: str | Path) -> pd.DataFrame:
    """
    Load ship-level table from given_data vessel_movements_dataset.csv.
    Takes one row per vessel_id (drops duplicate AIS rows) and maps columns
    to internal names: mep→P, boil_engine_fuel_type→aux_boiler_fuel_type,
    vessel_type_new→vessel_type. Adds vessel_name = vessel_id if missing.
    """
    path = Path(path)
    df = pd.read_csv(path)
    # Drop completely empty columns
    df = df.loc[:, df.columns.notna() & (df.columns != "")]
    df = df.dropna(axis=1, how="all")
    # One row per vessel (ship attributes repeat every AIS row)
    df = df.drop_duplicates(subset=["vessel_id"], keep="first").copy()
    # Rename given_data columns to internal names
    for old_name, new_name in GIVEN_DATA_COLUMN_MAP.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})
    if "vessel_name" not in df.columns:
        df["vessel_name"] = df["vessel_id"].astype(str)
    required = [c for c in REQUIRED_SHIP_COLUMNS if c != "vessel_name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ship dataset missing columns after mapping: {missing}")
    return df


def load_ships(path: str | Path) -> pd.DataFrame:
    """Load ship dataset (CSV). Supports given_data vessel_movements_dataset or pre-built ships CSV."""
    path = Path(path).resolve()
    if not path.suffix:
        path = path / "ships.csv"
    if not path.exists():
        raise FileNotFoundError(f"Ship file not found: {path}")
    # Detect given_data format (AIS movements: mep, vessel_type_new) and convert to ship-level
    df = pd.read_csv(path)
    # If this looks like vessel_movements (has mep, vessel_type_new), convert
    if "mep" in df.columns and "vessel_id" in df.columns:
        df = df.drop_duplicates(subset=["vessel_id"], keep="first").copy()
        for old_name, new_name in GIVEN_DATA_COLUMN_MAP.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        if "vessel_name" not in df.columns:
            df["vessel_name"] = df["vessel_id"].astype(str)
    required = [c for c in REQUIRED_SHIP_COLUMNS if c != "vessel_name"]
    required_with_name = REQUIRED_SHIP_COLUMNS
    missing = [c for c in required_with_name if c not in df.columns]
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
