"""
Data adapter for per_vessel.csv — the interface between teammate cost-model
outputs and the MILP optimizer.

Loads per_vessel.csv from data/processed/ or falls back to test fixtures.
Can also aggregate df_active.csv (row-level data) into per_vessel.csv
when teammates provide intermediate outputs (Steps 5c–6f).
Validates column contract, NaN checks, and value constraints.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.constants import (
    CARBON_PRICE,
    FUEL_PRICE_USD_PER_TONNE,
    FUEL_TYPE_MAP,
    GWP,
    SAFETY_ADJUSTMENT_RATES,
    get_monthly_capex,
)
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


def aggregate_df_active(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Aggregate df_active.csv (per-row data) into per_vessel.csv (per-vessel summary).

    Implements SOP Steps 5c through 6f:
      5c: Aggregate emissions per vessel, compute CO2eq
      6a: Fuel cost (ME at ME fuel price, AE/AB at Distillate price)
      6b: Carbon cost (CO2eq * 80)
      6c: Monthly CAPEX
      6d: Total monthly cost
      6e: Risk premium
      6f: Final cost

    Parameters
    ----------
    input_path : str | Path | None
        Path to df_active.csv. Defaults to data/processed/df_active.csv.
    output_path : str | Path | None
        Where to write per_vessel.csv. Defaults to data/processed/per_vessel.csv.

    Returns
    -------
    pd.DataFrame
        The per-vessel summary (also written to output_path).
    """
    if input_path is None:
        input_path = data_path("processed", "df_active.csv")
    input_path = Path(input_path)

    if output_path is None:
        output_path = data_path("processed", "per_vessel.csv")
    output_path = Path(output_path)

    df = pd.read_csv(input_path)

    # --- Step 5c: Aggregate per vessel ---
    agg = df.groupby("vessel_id").agg(
        FC_me_total=("FC_me", "sum"),
        FC_ae_total=("FC_ae", "sum"),
        FC_ab_total=("FC_ab", "sum"),
        E_CO2_total=("E_CO2_total", "sum"),
        E_CH4_total=("E_CH4_total", "sum"),
        E_N2O_total=("E_N2O_total", "sum"),
    ).reset_index()

    agg["FC_total"] = agg["FC_me_total"] + agg["FC_ae_total"] + agg["FC_ab_total"]
    agg["CO2eq"] = (
        1 * agg["E_CO2_total"]
        + GWP["CH4"] * agg["E_CH4_total"]
        + GWP["N2O"] * agg["E_N2O_total"]
    )

    # --- Merge static vessel info ---
    static_cols = ["vessel_id", "dwt", "safety_score", "main_engine_fuel_type"]
    vessel_static = df[static_cols].drop_duplicates("vessel_id")
    pv = agg.merge(vessel_static, on="vessel_id")

    # --- Step 6a: Fuel cost ---
    # ME fuel priced at ME fuel type; AE/AB always Distillate
    price_distillate = FUEL_PRICE_USD_PER_TONNE["Distillate fuel"]
    pv["price_me"] = pv["main_engine_fuel_type"].map(
        lambda ft: FUEL_PRICE_USD_PER_TONNE[FUEL_TYPE_MAP.get(ft, ft)]
    )
    pv["fuel_cost"] = (
        pv["FC_me_total"] * pv["price_me"]
        + (pv["FC_ae_total"] + pv["FC_ab_total"]) * price_distillate
    )

    # --- Step 6b: Carbon cost ---
    pv["carbon_cost"] = pv["CO2eq"] * CARBON_PRICE

    # --- Step 6c: Monthly CAPEX ---
    pv["monthly_capex"] = pv.apply(
        lambda r: get_monthly_capex(r["dwt"], r["main_engine_fuel_type"]),
        axis=1,
    )

    # --- Step 6d: Total monthly cost ---
    pv["total_monthly"] = pv["fuel_cost"] + pv["carbon_cost"] + pv["monthly_capex"]

    # --- Step 6e: Risk premium ---
    pv["adj_rate"] = pv["safety_score"].map(SAFETY_ADJUSTMENT_RATES)
    pv["risk_premium"] = pv["total_monthly"] * pv["adj_rate"]

    # --- Step 6f: Final cost ---
    pv["final_cost"] = pv["total_monthly"] + pv["risk_premium"]

    # --- Select and order output columns ---
    out_cols = REQUIRED_COLUMNS
    pv = pv[out_cols]

    # --- Write ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pv.to_csv(output_path, index=False)
    print(f"Wrote {len(pv)} vessels to {output_path}")

    return pv


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
