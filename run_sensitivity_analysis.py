#!/usr/bin/env python3
"""
Run comprehensive sensitivity analysis using the same optimization as run.py (MILP).

Uses data/processed/per_vessel.csv and src.sensitivity (safety sweep, carbon price sweep).
Outputs results to outputs/sensitivity/ and generates charts including sensitivity matrix.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import yaml

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_adapter import load_per_vessel
from src.optimization import select_fleet_milp, total_cost_and_metrics
from src.sensitivity import (
    run_safety_sweep_fixed_fleet,
    run_carbon_price_sweep_fixed_fleet,
)
from src.visualize_sensitivity import generate_all_visualizations


def load_config(config_path: Path) -> dict:
    """Load YAML config (cargo_demand_tonnes, constraints, etc.)."""
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def run_sensitivity_using_milp(
    df: pd.DataFrame,
    cargo_demand: float,
    min_safety: float,
    skip_safety: bool = False,
    skip_carbon: bool = False,
) -> dict:
    """
    Run sensitivity analysis using MILP (same as run.py).

    Returns dict: base_case, safety_sensitivity, carbon_price_sensitivity, scenarios_2024.
    scenarios_2024 is left empty so visualizer skips that chart; can be extended later.
    """
    results = {
        "base_case": None,
        "safety_sensitivity": [],
        "carbon_price_sensitivity": [],
        "scenarios_2024": [],
    }

    # 1. Base case
    selected_base = select_fleet_milp(
        df,
        cargo_demand=cargo_demand,
        min_avg_safety=min_safety,
    )
    if selected_base:
        results["base_case"] = {
            "metrics": total_cost_and_metrics(df, selected_base),
            "selected_vessel_ids": selected_base,
        }
    else:
        results["base_case"] = {"error": "Infeasible"}

    # 2. Safety threshold sensitivity (fixed fleet: evaluate base fleet at each threshold)
    if not skip_safety and selected_base:
        safety_results = run_safety_sweep_fixed_fleet(
            df,
            selected_ids=selected_base,
            thresholds=[2.5, 3.0, 3.5, 4.0, 4.5],
        )
        for r in safety_results:
            if r.get("total_cost_usd") is not None:
                metrics = {
                    "total_cost_usd": r["total_cost_usd"],
                    "total_co2e_tonnes": r["total_co2e_tonnes"],
                    "fleet_size": r["fleet_size"],
                    "avg_safety_score": r["avg_safety_score"],
                    "total_dwt": r["total_dwt"],
                    "total_fuel_tonnes": r.get("total_fuel_tonnes"),
                    "total_fuel_cost": r.get("total_fuel_cost"),
                    "total_carbon_cost": r.get("total_carbon_cost"),
                    "total_capex": r.get("total_capex"),
                    "total_risk_premium": r.get("total_risk_premium"),
                }
                results["safety_sensitivity"].append({
                    "threshold": r["threshold"],
                    "metrics": metrics,
                    "error": None if r.get("feasible", True) else "Constraint not met",
                })
            else:
                results["safety_sensitivity"].append({
                    "threshold": r["threshold"],
                    "metrics": None,
                    "error": "Infeasible",
                })

    # 3. Carbon price sensitivity (fixed fleet: same fleet, cost/CO2eq at each price)
    if not skip_carbon and selected_base:
        carbon_results = run_carbon_price_sweep_fixed_fleet(
            df,
            selected_ids=selected_base,
            carbon_prices=[80, 120, 160, 200],
        )
        for r in carbon_results:
            if r.get("feasible") and r.get("total_cost_usd") is not None:
                metrics = {
                    "total_cost_usd": r["total_cost_usd"],
                    "total_co2e_tonnes": r["total_co2e_tonnes"],
                    "fleet_size": r["fleet_size"],
                    "avg_safety_score": r["avg_safety_score"],
                    "total_dwt": r["total_dwt"],
                    "total_fuel_tonnes": r.get("total_fuel_tonnes"),
                    "total_fuel_cost": r.get("total_fuel_cost"),
                    "total_carbon_cost": r.get("total_carbon_cost"),
                    "total_capex": r.get("total_capex"),
                    "total_risk_premium": r.get("total_risk_premium"),
                }
                # Flatten dwt_by_fuel for CSV (dwt_Ammonia, dwt_LNG, ...)
                for ft, dwt in r.get("dwt_by_fuel", {}).items():
                    metrics[f"dwt_{ft}"] = dwt
                results["carbon_price_sensitivity"].append({
                    "carbon_price": r["carbon_price"],
                    "metrics": metrics,
                    "error": None,
                })
            else:
                results["carbon_price_sensitivity"].append({
                    "carbon_price": r["carbon_price"],
                    "metrics": None,
                    "error": "Infeasible",
                })

    # 4. 2024 scenarios: not implemented with MILP pipeline; leave empty
    # (visualize_sensitivity skips 2024 chart when scenarios_2024 is empty)
    results["scenarios_2024"] = []

    return results


def format_sensitivity_summary(results: dict) -> str:
    """Generate text summary of sensitivity results."""
    lines = ["=" * 80]
    lines.append("COMPREHENSIVE SENSITIVITY ANALYSIS (fixed base fleet)")
    lines.append("=" * 80)
    lines.append("")

    if results["base_case"] and "metrics" in results["base_case"]:
        m = results["base_case"]["metrics"]
        lines.append("BASE CASE:")
        lines.append(f"  Fleet size: {m['fleet_size']}")
        lines.append(f"  Total cost: ${m['total_cost_usd']:,.0f}")
        lines.append(f"  Avg safety: {m['avg_safety_score']:.2f}")
        lines.append(f"  Total CO2eq: {m['total_co2e_tonnes']:,.0f} tonnes")
        lines.append("")
    elif results["base_case"] and results["base_case"].get("error"):
        lines.append("BASE CASE: INFEASIBLE")
        lines.append("")

    lines.append("SAFETY THRESHOLD SENSITIVITY (fixed base fleet):")
    for r in results["safety_sensitivity"]:
        if r.get("error") or not r.get("metrics"):
            lines.append(f"  Safety ≥ {r['threshold']}: constraint not met")
        else:
            m = r["metrics"]
            lines.append(
                f"  Safety ≥ {r['threshold']}: "
                f"Fleet {m['fleet_size']}, "
                f"Cost ${m['total_cost_usd']:,.0f}, "
                f"CO2eq {m['total_co2e_tonnes']:,.0f}t"
            )
    lines.append("")

    lines.append("CARBON PRICE SENSITIVITY (fixed base fleet):")
    for r in results["carbon_price_sensitivity"]:
        if r.get("error") or not r.get("metrics"):
            lines.append(f"  ${r['carbon_price']}/tCO2eq: INFEASIBLE")
        else:
            m = r["metrics"]
            lines.append(
                f"  ${r['carbon_price']}/tCO2eq: "
                f"Fleet {m['fleet_size']}, "
                f"Cost ${m['total_cost_usd']:,.0f}, "
                f"CO2eq {m['total_co2e_tonnes']:,.0f}t"
            )
    lines.append("")

    return "\n".join(lines)


def save_results_to_csv(results: dict, output_dir: Path) -> None:
    """Save sensitivity results to CSV files for analysis."""
    if results["safety_sensitivity"]:
        safety_data = []
        for r in results["safety_sensitivity"]:
            if r.get("metrics"):
                row = {"safety_threshold": r["threshold"], **r["metrics"]}
                safety_data.append(row)
        if safety_data:
            pd.DataFrame(safety_data).to_csv(
                output_dir / "safety_sensitivity.csv", index=False
            )
            print(f"Saved safety sensitivity to {output_dir / 'safety_sensitivity.csv'}")

    if results["carbon_price_sensitivity"]:
        carbon_data = []
        for r in results["carbon_price_sensitivity"]:
            if r.get("metrics"):
                row = {
                    "carbon_price_usd_per_tco2e": r["carbon_price"],
                    **r["metrics"],
                }
                carbon_data.append(row)
        if carbon_data:
            pd.DataFrame(carbon_data).to_csv(
                output_dir / "carbon_price_sensitivity.csv", index=False
            )
            print(
                f"Saved carbon price sensitivity to {output_dir / 'carbon_price_sensitivity.csv'}"
            )

    if results.get("base_case") and "metrics" in results["base_case"]:
        pd.DataFrame([results["base_case"]["metrics"]]).to_csv(
            output_dir / "base_case.csv", index=False
        )
        print(f"Saved base case to {output_dir / 'base_case.csv'}")

    # Write empty 2024 scenarios when not run so old file doesn't pollute matrix/dashboard
    if not results["scenarios_2024"]:
        pd.DataFrame(columns=["scenario_name", "total_cost_usd", "total_co2e_tonnes", "fleet_size", "avg_safety_score"]).to_csv(
            output_dir / "2024_scenarios.csv", index=False
        )

    if results["scenarios_2024"]:
        scenario_data = []
        for r in results["scenarios_2024"]:
            if r.get("metrics"):
                row = {"scenario_name": r.get("scenario_name", ""), **r["metrics"]}
                scenario_data.append(row)
        if scenario_data:
            pd.DataFrame(scenario_data).to_csv(
                output_dir / "2024_scenarios.csv", index=False
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis (MILP) - same data & optimizer as run.py"
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to per_vessel.csv (default: data/processed/per_vessel.csv)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/params.yaml",
        help="Path to config YAML",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs/sensitivity",
        help="Output directory",
    )
    parser.add_argument("--skip-safety", action="store_true", help="Skip safety sweep")
    parser.add_argument("--skip-carbon", action="store_true", help="Skip carbon price sweep")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    print("=" * 80)
    print("SENSITIVITY ANALYSIS (MILP) - Maritime Hackathon 2026")
    print("=" * 80)
    print()

    # Config
    config_path = root / args.config
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)
    config = load_config(config_path)
    cargo_demand = config.get("cargo_demand_tonnes", 4_576_667)
    min_safety = config["constraints"].get("min_avg_safety_score", 3.0)
    print(f"Config: cargo_demand={cargo_demand:,.0f}, min_safety={min_safety}")

    # Load same data as run.py (processed per_vessel)
    df = load_per_vessel(args.data)
    print(f"Loaded {len(df)} vessels from per_vessel data")
    print()

    try:
        results = run_sensitivity_using_milp(
            df,
            cargo_demand=cargo_demand,
            min_safety=min_safety,
            skip_safety=args.skip_safety,
            skip_carbon=args.skip_carbon,
        )

        summary = format_sensitivity_summary(results)
        print(summary)

        output_dir = root / args.out_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        summary_file = output_dir / f"sensitivity_summary_{timestamp}.txt"
        summary_file.write_text(summary)
        print(f"\nSaved summary to {summary_file}")

        save_results_to_csv(results, output_dir)

        print("\nGenerating sensitivity charts (including tornado analysis)...")
        generate_all_visualizations(
            results_dir=str(output_dir),
            output_dir=str(output_dir / "plots"),
        )

        json_file = output_dir / f"sensitivity_results_{timestamp}.json"
        results_for_json = {
            "base_case": (
                {k: v for k, v in results["base_case"].items() if k != "selected_vessel_ids"}
                if results["base_case"]
                else None
            ),
            "safety_sensitivity": [
                {k: v for k, v in r.items() if k != "selected_vessel_ids"}
                for r in results["safety_sensitivity"]
            ],
            "carbon_price_sensitivity": [
                {k: v for k, v in r.items() if k != "selected_vessel_ids"}
                for r in results["carbon_price_sensitivity"]
            ],
            "scenarios_2024": results["scenarios_2024"],
        }
        with open(json_file, "w") as f:
            json.dump(results_for_json, f, indent=2, default=str)
        print(f"Saved results to {json_file}")

        print()
        print("=" * 80)
        print("SENSITIVITY ANALYSIS COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
