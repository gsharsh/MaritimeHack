"""
Data adapter for per_vessel.csv — the interface between teammate cost-model
outputs and the MILP optimizer.

Loads per_vessel.csv from data/processed/ or falls back to test fixtures.
Validates column contract, NaN checks, and value constraints.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import data_path, project_root

# ---------------------------------------------------------------------------
# Column contract (must match per_vessel.csv exactly)
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS: list[str] = [
    "vessel_id",
    "dwt",
    "safety_score",
    "main_engine_fuel_type",
    "FC_me_total",
    "FC_ae_total",
    "FC_ab_total",
    "FC_total",
    "CO2eq",
    "fuel_cost",
    "carbon_cost",
    "monthly_capex",
    "total_monthly",
    "adj_rate",
    "risk_premium",
    "final_cost",
]

# Production expectations
_EXPECTED_ROWS = 108
_EXPECTED_FUEL_TYPES = 8
_MIN_DWT_SUM = 4_576_667


def load_per_vessel(path: str | Path | None = None) -> pd.DataFrame:
    """
    Load per_vessel.csv into a validated DataFrame.

    Parameters
    ----------
    path : str | Path | None
        Explicit path to CSV.  If *None*, tries
        ``data/processed/per_vessel.csv`` then falls back to the test
        fixtures at ``tests/fixtures/checkpoint_vessels.csv``.

    Returns
    -------
    pd.DataFrame
        Validated vessel data.

    Raises
    ------
    ValueError
        If required columns are missing, NaN values exist in required
        columns, or critical value constraints are violated.
    FileNotFoundError
        If neither the primary path nor the fixture fallback exists.
    """
    if path is not None:
        csv_path = Path(path)
    else:
        csv_path = data_path("processed", "per_vessel.csv")

    if not csv_path.exists():
        fixture_path = project_root() / "tests" / "fixtures" / "checkpoint_vessels.csv"
        if fixture_path.exists():
            print(
                f"WARNING: {csv_path} not found — falling back to "
                f"test fixtures at {fixture_path}"
            )
            csv_path = fixture_path
        else:
            raise FileNotFoundError(
                f"No per_vessel.csv at {csv_path} and no fixture fallback at {fixture_path}"
            )

    df = pd.read_csv(csv_path)

    # --- Validate columns ---------------------------------------------------
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # --- Validate no NaN in required columns --------------------------------
    nan_cols = [c for c in REQUIRED_COLUMNS if df[c].isna().any()]
    if nan_cols:
        raise ValueError(f"NaN values found in columns: {nan_cols}")

    # --- Validate value constraints -----------------------------------------
    if not (df["final_cost"] > 0).all():
        raise ValueError("All final_cost values must be > 0")

    if not (df["CO2eq"] > 0).all():
        raise ValueError("All CO2eq values must be > 0")

    return df


def validate_per_vessel(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Run full production validation checks on a per_vessel DataFrame.

    These checks are stricter than ``load_per_vessel`` and are meant for
    the final 108-row production dataset.

    Returns
    -------
    tuple[bool, list[str]]
        ``(ok, errors)`` where *ok* is True only when all checks pass
        and *errors* is a list of human-readable messages for each failure.
    """
    errors: list[str] = []

    # 1. Exactly 108 rows
    if len(df) != _EXPECTED_ROWS:
        errors.append(f"Expected {_EXPECTED_ROWS} rows, got {len(df)}")

    # 2. 8 unique fuel types
    n_fuels = df["main_engine_fuel_type"].nunique()
    if n_fuels != _EXPECTED_FUEL_TYPES:
        errors.append(f"Expected {_EXPECTED_FUEL_TYPES} unique fuel types, got {n_fuels}")

    # 3. All final_cost > 0
    bad_cost = (df["final_cost"] <= 0).sum()
    if bad_cost:
        errors.append(f"{bad_cost} vessels have final_cost <= 0")

    # 4. All CO2eq > 0
    bad_co2 = (df["CO2eq"] <= 0).sum()
    if bad_co2:
        errors.append(f"{bad_co2} vessels have CO2eq <= 0")

    # 5. Sum of DWT > monthly demand
    dwt_sum = df["dwt"].sum()
    if dwt_sum <= _MIN_DWT_SUM:
        errors.append(
            f"Total DWT {dwt_sum:,.0f} <= minimum demand {_MIN_DWT_SUM:,}"
        )

    # 6. No NaN in required columns
    nan_cols = [c for c in REQUIRED_COLUMNS if c in df.columns and df[c].isna().any()]
    if nan_cols:
        errors.append(f"NaN values in columns: {nan_cols}")

    return (len(errors) == 0, errors)
