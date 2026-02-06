#!/usr/bin/env python3
"""
Run fleet selection: load per-vessel data, print fleet summary.
Phase 1 staging script — MILP optimization will be added in Phase 2.
"""

import argparse
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_adapter import load_per_vessel, validate_per_vessel
from src.constants import MONTHLY_DEMAND, SAFETY_THRESHOLD, FUEL_TYPES, CARBON_PRICE


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smart Fleet Selection - Maritime Hackathon 2026"
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to per_vessel.csv (default: data/processed/per_vessel.csv or fixtures)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs/results",
        help="Output directory",
    )
    args = parser.parse_args()

    # --- Load data -----------------------------------------------------------
    print("=" * 60)
    print("Smart Fleet Selection - Maritime Hackathon 2026")
    print("=" * 60)

    df = load_per_vessel(args.data)
    print(f"\nLoaded {len(df)} vessels")

    # --- Data summary --------------------------------------------------------
    fuel_types_found = sorted(df["main_engine_fuel_type"].unique())
    print(f"Fuel types found ({len(fuel_types_found)}): {fuel_types_found}")
    print(f"Total DWT: {df['dwt'].sum():,.0f}")
    print(f"Total final_cost: ${df['final_cost'].sum():,.2f}")
    print(f"Average safety score: {df['safety_score'].mean():.2f}")

    # Count by fuel type
    print("\nVessels by fuel type:")
    for ft, count in df["main_engine_fuel_type"].value_counts().items():
        print(f"  {ft}: {count}")

    # --- Validate (production checks) ----------------------------------------
    ok, errors = validate_per_vessel(df)
    print(f"\nProduction validation: {'PASS' if ok else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"  - {err}")

    # --- Constants summary ---------------------------------------------------
    print(f"\nConstants from SOP:")
    print(f"  MONTHLY_DEMAND = {MONTHLY_DEMAND:,}")
    print(f"  SAFETY_THRESHOLD = {SAFETY_THRESHOLD}")
    print(f"  CARBON_PRICE = ${CARBON_PRICE}/tCO2e")
    print(f"  FUEL_TYPES = {len(FUEL_TYPES)} types")

    # --- Ready for Phase 2 ---------------------------------------------------
    print(f"\nReady for Phase 2: MILP optimization")
    print("=" * 60)


if __name__ == "__main__":
    main()
