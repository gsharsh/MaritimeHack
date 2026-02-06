"""
Sensitivity analysis: re-run fleet selection for different average safety score
constraints (e.g. min_avg_safety 3 vs 4) and compare costs and fleet composition.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from .optimization import (
    format_outputs,
    select_fleet_greedy,
    total_cost_and_metrics,
    validate_fleet,
)


def run_sensitivity(
    df: pd.DataFrame,
    cargo_demand_tonnes: float,
    safety_scores_to_try: list[float],
    require_all_fuel_types: bool = True,
    cost_col: str = "total_cost_usd",
) -> list[dict[str, Any]]:
    """
    For each min_avg_safety in safety_scores_to_try, select fleet and record
    metrics. Return list of result dicts (one per run).
    """
    results = []
    for min_safety in safety_scores_to_try:
        selected = select_fleet_greedy(
            df,
            cargo_demand_tonnes=cargo_demand_tonnes,
            min_avg_safety=min_safety,
            require_all_fuel_types=require_all_fuel_types,
            cost_col=cost_col,
        )
        ok, errs = validate_fleet(
            df, selected, cargo_demand_tonnes, min_safety, require_all_fuel_types
        )
        if not ok:
            results.append({
                "min_avg_safety": min_safety,
                "error": "; ".join(errs),
                "metrics": None,
            })
            continue
        metrics = total_cost_and_metrics(df, selected, cost_col=cost_col)
        metrics["min_avg_safety_constraint"] = min_safety
        metrics["selected_vessel_ids"] = selected
        results.append({
            "min_avg_safety": min_safety,
            "error": None,
            "metrics": metrics,
        })
    return results


def sensitivity_summary_for_report(results: list[dict[str, Any]]) -> str:
    """Produce a short text summary for the case paper report."""
    lines = ["Sensitivity analysis: fleet selection under different safety constraints.", ""]
    for r in results:
        s = r["min_avg_safety"]
        if r["error"]:
            lines.append(f"  Min safety {s}: Failed - {r['error']}")
            continue
        m = r["metrics"]
        lines.append(f"  Min safety {s}: Fleet size {m['fleet_size']}, "
                     f"Total cost USD {m['total_cost_usd']:.0f}, "
                     f"Avg safety {m['avg_safety_score']:.2f}, "
                     f"CO2e tonnes {m['total_co2e_tonnes']:.0f}.")
    return "\n".join(lines)
