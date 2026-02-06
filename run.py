#!/usr/bin/env python3
"""
Run fleet selection: load data, compute costs, optimize, optionally run sensitivity.
Outputs results and submission-ready metrics.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_loader import load_config, load_global_params, load_ships
from src.cost_model import ship_total_cost_usd
from src.optimization import (
    format_outputs,
    select_fleet_greedy,
    total_cost_and_metrics,
)
from src.sensitivity import run_sensitivity, sensitivity_summary_for_report
from src.utils import data_path, outputs_path, voyage_hours_from_nm_and_speed, SINGAPORE_TO_AU_WEST_NM


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Fleet Selection - Maritime Hackathon 2026")
    parser.add_argument("--ships", type=str, default=None, help="Path to ships CSV")
    parser.add_argument("--global-params", type=str, default=None, help="Path to global params YAML/JSON")
    parser.add_argument("--config", type=str, default="config/params.yaml", help="Path to config YAML")
    parser.add_argument("--sensitivity", action="store_true", help="Run sensitivity analysis")
    parser.add_argument("--out-dir", type=str, default="outputs/results", help="Output directory")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    config_path = root / args.config
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)
    config = load_config(config_path)
    cargo_demand = config.get("cargo_demand_tonnes", 4_150_000)
    min_safety = config["constraints"].get("min_avg_safety_score", 3.0)
    require_all_fuel = config["constraints"].get("require_all_fuel_types", True)

    given_data_ships = root / "given_data" / "vessel_movements_dataset.csv"
    ships_path = args.ships or (str(given_data_ships) if given_data_ships.exists() else str(data_path("raw", "ships.csv")))
    global_params_path = args.global_params or str(data_path("global_params", "global_params.yaml"))

    if not Path(ships_path).exists():
        print(f"Ships file not found: {ships_path}. Use given_data/vessel_movements_dataset.csv or add data/raw/ships.csv.")
        sys.exit(1)

    df = load_ships(ships_path)
    global_params = {}
    if Path(global_params_path).exists():
        global_params = load_global_params(global_params_path)
    else:
        print("Global params not found; using defaults. Add data/global_params/global_params.yaml for real costs.")

    # Default voyage hours from Vref if no route data
    voyage_nm = global_params.get("voyage_nm", SINGAPORE_TO_AU_WEST_NM)
    df["voyage_hours"] = df.apply(
        lambda r: voyage_hours_from_nm_and_speed(voyage_nm, r.get("vref", 12)),
        axis=1,
    )
    carbon_price = config.get("carbon_price_usd_per_tco2e", 80)
    global_params.setdefault("carbon_price_usd_per_tco2e", carbon_price)

    # Compute cost columns per ship
    rows = []
    for _, row in df.iterrows():
        costs = ship_total_cost_usd(row, global_params, row["voyage_hours"])
        rows.append({**row.to_dict(), **costs})
    df = pd.DataFrame(rows)

    selected = select_fleet_greedy(
        df,
        cargo_demand_tonnes=cargo_demand,
        min_avg_safety=min_safety,
        require_all_fuel_types=require_all_fuel,
    )
    metrics = total_cost_and_metrics(df, selected)
    out = format_outputs(metrics, sensitivity_done=False)

    if args.sensitivity:
        sens_config = config.get("sensitivity", {})
        scores = sens_config.get("safety_scores_to_try", [3.0, 4.0])
        sens_results = run_sensitivity(
            df, cargo_demand, scores, require_all_fuel, "total_cost_usd"
        )
        out["Sensitivity analysis performed"] = "Yes"
        summary = sensitivity_summary_for_report(sens_results)
        out_dir = root / args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "sensitivity_summary.txt").write_text(summary)
        print("Sensitivity summary:\n", summary)

    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    for k, v in out.items():
        print(f"  {k}: {v}")
    return


if __name__ == "__main__":
    main()
