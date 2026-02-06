#!/usr/bin/env python3
"""
Run comprehensive sensitivity analysis including:
- Safety threshold sweep
- Carbon price sensitivity
- 2024 route-specific scenarios (CII, congestion, fuel price)

Outputs results to outputs/sensitivity/
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_loader import load_config, load_global_params, load_ships
from src.cost_model import ship_total_cost_usd
from src.sensitivity_2024 import (
    run_comprehensive_sensitivity,
    format_sensitivity_summary,
)
from src.utils import data_path, outputs_path, voyage_hours_from_nm_and_speed, SINGAPORE_TO_AU_WEST_NM


def save_results_to_csv(results: dict, output_dir: Path) -> None:
    """Save sensitivity results to CSV files for analysis."""

    # Safety sensitivity
    if results['safety_sensitivity']:
        safety_data = []
        for r in results['safety_sensitivity']:
            if r.get('metrics'):
                row = {
                    'safety_threshold': r['threshold'],
                    **r['metrics']
                }
                safety_data.append(row)

        if safety_data:
            df_safety = pd.DataFrame(safety_data)
            df_safety.to_csv(output_dir / 'safety_sensitivity.csv', index=False)
            print(f"Saved safety sensitivity results to {output_dir / 'safety_sensitivity.csv'}")

    # Carbon price sensitivity
    if results['carbon_price_sensitivity']:
        carbon_data = []
        for r in results['carbon_price_sensitivity']:
            if r.get('metrics'):
                row = {
                    'carbon_price_usd_per_tco2e': r['carbon_price'],
                    **r['metrics']
                }
                carbon_data.append(row)

        if carbon_data:
            df_carbon = pd.DataFrame(carbon_data)
            df_carbon.to_csv(output_dir / 'carbon_price_sensitivity.csv', index=False)
            print(f"Saved carbon price sensitivity results to {output_dir / 'carbon_price_sensitivity.csv'}")

    # 2024 scenarios
    if results['scenarios_2024']:
        scenario_data = []
        for r in results['scenarios_2024']:
            if r.get('metrics'):
                row = {
                    'scenario_name': r['scenario_name'],
                    **r['metrics']
                }
                # Flatten scenario_config
                if 'scenario_config' in row:
                    config = row.pop('scenario_config')
                    for k, v in config.items():
                        if k != 'name':
                            row[f'config_{k}'] = v
                scenario_data.append(row)

        if scenario_data:
            df_scenarios = pd.DataFrame(scenario_data)
            df_scenarios.to_csv(output_dir / '2024_scenarios.csv', index=False)
            print(f"Saved 2024 scenario results to {output_dir / '2024_scenarios.csv'}")

    # Base case
    if results.get('base_case') and 'metrics' in results['base_case']:
        base_df = pd.DataFrame([results['base_case']['metrics']])
        base_df.to_csv(output_dir / 'base_case.csv', index=False)
        print(f"Saved base case results to {output_dir / 'base_case.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run comprehensive sensitivity analysis for Maritime Hackathon 2026"
    )
    parser.add_argument("--ships", type=str, default=None, help="Path to ships CSV")
    parser.add_argument("--config", type=str, default="config/params.yaml", help="Path to config YAML")
    parser.add_argument("--out-dir", type=str, default="outputs/sensitivity", help="Output directory")
    parser.add_argument("--skip-safety", action="store_true", help="Skip safety threshold sensitivity")
    parser.add_argument("--skip-carbon", action="store_true", help="Skip carbon price sensitivity")
    parser.add_argument("--skip-2024", action="store_true", help="Skip 2024 scenarios")
    args = parser.parse_args()

    print("=" * 80)
    print("COMPREHENSIVE SENSITIVITY ANALYSIS - Maritime Hackathon 2026")
    print("=" * 80)
    print()

    # Load configuration
    root = Path(__file__).resolve().parent
    config_path = root / args.config
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    cargo_demand = config.get("cargo_demand_tonnes", 4_576_667)  # Updated from methodology
    min_safety = config["constraints"].get("min_avg_safety_score", 3.0)
    require_all_fuel = config["constraints"].get("require_all_fuel_types", True)

    print(f"Configuration:")
    print(f"  Cargo demand: {cargo_demand:,.0f} tonnes")
    print(f"  Base min safety: {min_safety}")
    print(f"  Require all fuel types: {require_all_fuel}")
    print()

    # Load ships data
    given_data_ships = root / "given_data" / "vessel_movements_dataset.csv"
    ships_path = args.ships or (str(given_data_ships) if given_data_ships.exists() else str(data_path("raw", "ships.csv")))

    if not Path(ships_path).exists():
        print(f"Ships file not found: {ships_path}")
        sys.exit(1)

    print(f"Loading ships from: {ships_path}")
    df = load_ships(ships_path)
    print(f"Loaded {len(df)} vessels")
    print()

    # Load global parameters
    global_params_path = str(data_path("global_params", "global_params.yaml"))
    global_params = {}
    if Path(global_params_path).exists():
        global_params = load_global_params(global_params_path)
        print(f"Loaded global parameters from {global_params_path}")
    else:
        print("Warning: Global params not found, using defaults")

    # Calculate voyage hours
    voyage_nm = global_params.get("voyage_nm", SINGAPORE_TO_AU_WEST_NM)
    df["voyage_hours"] = df.apply(
        lambda r: voyage_hours_from_nm_and_speed(voyage_nm, r.get("vref", 12)),
        axis=1,
    )

    carbon_price = config.get("carbon_price_usd_per_tco2e", 80)
    global_params.setdefault("carbon_price_usd_per_tco2e", carbon_price)

    # Compute cost columns per ship
    print("Computing costs for all vessels...")
    rows = []
    for _, row in df.iterrows():
        costs = ship_total_cost_usd(row, global_params, row["voyage_hours"])
        rows.append({**row.to_dict(), **costs})
    df = pd.DataFrame(rows)
    print(f"Computed costs for {len(df)} vessels")
    print()

    # Run comprehensive sensitivity analysis
    print("Running comprehensive sensitivity analysis...")
    print("This may take several minutes...")
    print()

    try:
        results = run_comprehensive_sensitivity(
            df,
            cargo_demand_tonnes=cargo_demand,
            base_min_safety=min_safety,
            require_all_fuel_types=require_all_fuel,
        )

        # Generate summary
        summary = format_sensitivity_summary(results)
        print(summary)

        # Save results
        output_dir = root / args.out_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save text summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = output_dir / f"sensitivity_summary_{timestamp}.txt"
        summary_file.write_text(summary)
        print(f"\nSaved summary to {summary_file}")

        # Save CSV results
        save_results_to_csv(results, output_dir)

        # Save full results as JSON
        json_file = output_dir / f"sensitivity_results_{timestamp}.json"
        # Remove vessel_ids from JSON (can be large)
        results_for_json = {
            'base_case': {k: v for k, v in results['base_case'].items() if k != 'selected_vessel_ids'} if results['base_case'] else None,
            'safety_sensitivity': [
                {k: v for k, v in r.items() if k != 'selected_vessel_ids'}
                for r in results['safety_sensitivity']
            ],
            'carbon_price_sensitivity': [
                {k: v for k, v in r.items() if k != 'selected_vessel_ids'}
                for r in results['carbon_price_sensitivity']
            ],
            'scenarios_2024': [
                {k: v for k, v in r.items() if k != 'selected_vessel_ids'}
                for r in results['scenarios_2024']
            ],
        }

        with open(json_file, 'w') as f:
            json.dump(results_for_json, f, indent=2, default=str)
        print(f"Saved full results to {json_file}")

        print()
        print("=" * 80)
        print("SENSITIVITY ANALYSIS COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: Sensitivity analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
