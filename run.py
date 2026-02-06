#!/usr/bin/env python3
"""
Run fleet selection: load per-vessel data, run MILP optimizer, print results.
"""

import argparse
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_adapter import load_per_vessel, validate_per_vessel
from src.constants import MONTHLY_DEMAND, SAFETY_THRESHOLD, FUEL_TYPES, CARBON_PRICE
from src.optimization import (
    select_fleet_milp,
    validate_fleet,
    total_cost_and_metrics,
    format_outputs,
)
from src.sensitivity import (
    run_safety_sweep,
    format_sweep_table,
    run_pareto_sweep,
    format_pareto_table,
    run_carbon_price_sweep,
    format_carbon_sweep_table,
)


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
    parser.add_argument(
        "--cargo-demand",
        type=float,
        default=MONTHLY_DEMAND,
        help=f"Cargo demand in tonnes (default: {MONTHLY_DEMAND:,})",
    )
    parser.add_argument(
        "--safety-threshold",
        type=float,
        default=SAFETY_THRESHOLD,
        help=f"Minimum average safety score (default: {SAFETY_THRESHOLD})",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        default=False,
        help="Run safety threshold sweep at 3.0, 3.5, 4.0, 4.5",
    )
    parser.add_argument(
        "--pareto",
        action="store_true",
        default=False,
        help="Run cost-emissions Pareto frontier (epsilon-constraint, 15 points)",
    )
    parser.add_argument(
        "--carbon-sweep",
        action="store_true",
        default=False,
        help="Run carbon price sweep at $80/$120/$160/$200",
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

    # --- MILP optimization ---------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"MILP Fleet Optimization")
    print(f"  Cargo demand: {args.cargo_demand:,.0f} tonnes")
    print(f"  Safety threshold: {args.safety_threshold}")
    print(f"{'=' * 60}")

    selected_ids = select_fleet_milp(
        df,
        cargo_demand=args.cargo_demand,
        min_avg_safety=args.safety_threshold,
    )

    if not selected_ids:
        print("\nINFEASIBLE: No fleet satisfies all constraints.")
        print(f"  Total available DWT: {df['dwt'].sum():,.0f}")
        print(f"  Required DWT: {args.cargo_demand:,.0f}")
        if df["dwt"].sum() < args.cargo_demand:
            print("  (Not enough total DWT in vessel pool)")
        sys.exit(1)

    # --- Validate fleet ------------------------------------------------------
    ok, errors = validate_fleet(
        df, selected_ids, args.cargo_demand, args.safety_threshold, True
    )
    print(f"\nFleet validation: {'PASS' if ok else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"  - {err}")

    # --- Metrics and output --------------------------------------------------
    metrics = total_cost_and_metrics(df, selected_ids)
    formatted = format_outputs(metrics)

    print(f"\nFleet Selection Results:")
    for key, val in formatted.items():
        print(f"  {key}: {val}")

    print(f"\nSelected vessel IDs ({len(selected_ids)}):")
    print(f"  {selected_ids}")
    print("=" * 60)

    # --- Safety threshold sweep ----------------------------------------------
    if args.sweep:
        print(f"\n{'=' * 60}")
        print("Safety Threshold Sweep")
        print(f"{'=' * 60}")

        results = run_safety_sweep(
            df, thresholds=[3.0, 3.5, 4.0, 4.5], cargo_demand=args.cargo_demand
        )
        table = format_sweep_table(results)
        print(f"\n{table.to_string(index=False)}")

        print(f"\nFuel type composition by threshold:")
        for r in results:
            if r["feasible"]:
                counts = r["fuel_type_counts"]
                composition = ", ".join(f"{ft}: {n}" for ft, n in counts.items())
                print(f"  Threshold {r['threshold']}: {len(counts)} types — {composition}")
            else:
                print(f"  Threshold {r['threshold']}: INFEASIBLE")

        print("=" * 60)

    # --- Pareto frontier -----------------------------------------------------
    if args.pareto:
        print(f"\n{'=' * 60}")
        print("Cost-Emissions Pareto Frontier")
        print(f"{'=' * 60}")

        pareto_results = run_pareto_sweep(df, cargo_demand=args.cargo_demand)
        table = format_pareto_table(pareto_results)
        print(f"\n{table.to_string(index=False)}")

        feasible_count = sum(1 for r in pareto_results if r["feasible"])
        print(f"\nPareto points: {feasible_count} feasible out of {len(pareto_results)}")

        print("=" * 60)

    # --- Carbon price sweep --------------------------------------------------
    if args.carbon_sweep:
        print(f"\n{'=' * 60}")
        print("Carbon Price Sweep")
        print(f"{'=' * 60}")

        carbon_results = run_carbon_price_sweep(
            df,
            cargo_demand=args.cargo_demand,
            safety_threshold=args.safety_threshold,
        )
        table = format_carbon_sweep_table(carbon_results)
        print(f"\n{table.to_string(index=False)}")

        print(f"\nFuel type composition by carbon price:")
        for r in carbon_results:
            if r["feasible"]:
                counts = r["fuel_type_counts"]
                composition = ", ".join(f"{ft}: {n}" for ft, n in counts.items())
                print(f"  ${r['carbon_price']}/t: {len(counts)} types — {composition}")
            else:
                print(f"  ${r['carbon_price']}/t: INFEASIBLE")

        print("=" * 60)


if __name__ == "__main__":
    main()
