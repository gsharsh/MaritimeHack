#!/usr/bin/env python3
"""
Run two separate tests and compare:

1. CBC MILP only (no min-max): standard single-scenario fleet selection.
2. Min-max MILP: robust fleet selection across stress scenarios.

For each test:
- Run main pipeline (run.py) with sweep, pareto, carbon-sweep; save charts with distinct names.
- Run sensitivity analysis; save sensitivity results and plots with distinct names.
- Outputs: outputs/test_milp/ and outputs/test_minmax/.

Finally writes a markdown summary comparing the two (outputs/MILP_vs_MinMax_Comparison.md).

Requires: run from project root with dependencies installed (pip install -r requirements.txt).
Charts also require matplotlib and seaborn.
"""

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent


def run_cmd(args: list[str], description: str) -> bool:
    """Run a command; return True on success."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"  Command: {' '.join(args)}")
    print('='*60)
    mplconfig = ROOT / "outputs" / ".mplconfig"
    mplconfig.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "MPLBACKEND": "Agg", "MPLCONFIGDIR": str(mplconfig)}
    result = subprocess.run(args, cwd=ROOT, env=env)
    if result.returncode != 0:
        print(f"FAILED: {description} (exit code {result.returncode})", file=sys.stderr)
        return False
    return True


def _df_to_md(df: pd.DataFrame) -> str:
    """Simple markdown table from DataFrame."""
    headers = list(df.columns)
    rows = [headers, ["---"] * len(headers)]
    for _, r in df.iterrows():
        rows.append([str(r[c]) if pd.notna(r[c]) else "" for c in headers])
    return "\n".join("| " + " | ".join(row) + " |" for row in rows)


def load_config() -> dict:
    config_path = ROOT / "config" / "params.yaml"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    print("MILP vs Min-Max comparison — running two tests")
    print("Root:", ROOT)

    # --- Test 1: CBC MILP only (no robust) ---
    chart_dir_milp = ROOT / "outputs" / "test_milp" / "charts"
    chart_dir_milp.mkdir(parents=True, exist_ok=True)

    if not run_cmd(
        [
            sys.executable,
            "run.py",
            "--sweep",
            "--pareto",
            "--carbon-sweep",
            "--chart-dir", str(chart_dir_milp),
            "--chart-suffix", "_milp",
        ],
        "Test 1: CBC MILP (no min-max) — main run with charts",
    ):
        return 1

    sens_dir_milp = ROOT / "outputs" / "test_milp" / "sensitivity"
    if not run_cmd(
        [
            sys.executable,
            "run_sensitivity_analysis.py",
            "--out-dir", str(sens_dir_milp),
            "--suffix", "_milp",
        ],
        "Test 1: Sensitivity analysis (MILP base fleet)",
    ):
        return 1

    # --- Test 2: Min-max MILP ---
    chart_dir_minmax = ROOT / "outputs" / "test_minmax" / "charts"
    chart_dir_minmax.mkdir(parents=True, exist_ok=True)

    if not run_cmd(
        [
            sys.executable,
            "run.py",
            "--robust",
            "--sweep",
            "--pareto",
            "--carbon-sweep",
            "--chart-dir", str(chart_dir_minmax),
            "--chart-suffix", "_minmax",
        ],
        "Test 2: Min-max MILP — main run with charts",
    ):
        return 1

    sens_dir_minmax = ROOT / "outputs" / "test_minmax" / "sensitivity"
    if not run_cmd(
        [
            sys.executable,
            "run_sensitivity_analysis.py",
            "--use-minmax",
            "--out-dir", str(sens_dir_minmax),
            "--suffix", "_minmax",
        ],
        "Test 2: Sensitivity analysis (min-max robust base fleet)",
    ):
        return 1

    # --- Write markdown comparison ---
    out_md = ROOT / "outputs" / "MILP_vs_MinMax_Comparison.md"
    write_comparison_md(
        base_case_milp_path=sens_dir_milp / "base_case.csv",
        base_case_minmax_path=sens_dir_minmax / "base_case.csv",
        carbon_milp_path=sens_dir_milp / "carbon_price_sensitivity.csv",
        carbon_minmax_path=sens_dir_minmax / "carbon_price_sensitivity.csv",
        safety_milp_path=sens_dir_milp / "safety_sensitivity.csv",
        safety_minmax_path=sens_dir_minmax / "safety_sensitivity.csv",
        chart_dir_milp=chart_dir_milp,
        chart_dir_minmax=chart_dir_minmax,
        output_path=out_md,
    )
    print(f"\nComparison summary written to: {out_md}")

    return 0


def write_comparison_md(
    base_case_milp_path: Path,
    base_case_minmax_path: Path,
    carbon_milp_path: Path,
    carbon_minmax_path: Path,
    safety_milp_path: Path,
    safety_minmax_path: Path,
    chart_dir_milp: Path,
    chart_dir_minmax: Path,
    output_path: Path,
) -> None:
    """Build markdown comparing MILP vs min-max results."""
    lines = [
        "# MILP vs Min-Max Robust Fleet — Comparison Summary",
        "",
        "This document compares two optimization runs:",
        "- **CBC MILP (no min-max)**: Single-scenario cost minimization at base carbon price and safety threshold.",
        "- **Min-Max MILP**: Robust optimization minimizing worst-case cost across multiple stress scenarios (base, safety stress, carbon stress, joint stress).",
        "",
        "---",
        "",
        "## 1. Base case fleet metrics",
        "",
        "| Metric | CBC MILP | Min-Max MILP |",
        "|--------|----------|--------------|",
    ]

    def load_base(path: Path) -> dict | None:
        if not path.exists():
            return None
        df = pd.read_csv(path)
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    base_milp = load_base(base_case_milp_path)
    base_minmax = load_base(base_case_minmax_path)

    metrics = [
        ("Fleet size", "fleet_size", "{:.0f}"),
        ("Total cost (USD)", "total_cost_usd", "${:,.0f}"),
        ("Total DWT", "total_dwt", "{:,.0f}"),
        ("Avg safety score", "avg_safety_score", "{:.2f}"),
        ("Total CO2eq (tonnes)", "total_co2e_tonnes", "{:,.0f}"),
        ("Total fuel (tonnes)", "total_fuel_tonnes", "{:,.0f}"),
    ]
    for label, key, fmt in metrics:
        v_milp = base_milp.get(key) if base_milp else None
        v_minmax = base_minmax.get(key) if base_minmax else None
        s_milp = fmt.format(v_milp) if v_milp is not None else "—"
        s_minmax = fmt.format(v_minmax) if v_minmax is not None else "—"
        lines.append(f"| {label} | {s_milp} | {s_minmax} |")

    lines.extend([
        "",
        "**Note:** Min-max selects a fleet that minimizes the worst-case cost across scenarios; base-scenario cost may be higher than the pure MILP base-case fleet, but the fleet is more resilient to stress scenarios.",
        "",
        "---",
        "",
        "## 2. Carbon price sensitivity (fixed fleet)",
        "",
        "Sensitivity evaluates the **same** selected fleet at different carbon prices ($80, $120, $160, $200/tCO2eq).",
        "",
    ])

    for name, path in [("CBC MILP", carbon_milp_path), ("Min-Max MILP", carbon_minmax_path)]:
        if path.exists():
            df = pd.read_csv(path)
            if not df.empty and "carbon_price_usd_per_tco2e" in df.columns:
                lines.append(f"### {name}")
                lines.append("")
                sub = df[["carbon_price_usd_per_tco2e", "total_cost_usd", "total_co2e_tonnes", "fleet_size"]]
                sub.columns = ["Carbon price ($/t)", "Total cost (USD)", "CO2eq (t)", "Fleet size"]
                lines.append(_df_to_md(sub))
                lines.append("")
        else:
            lines.append(f"*No data for {name}*")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Safety threshold sensitivity (fixed fleet)",
        "",
        "Sensitivity evaluates the **same** selected fleet at different minimum safety thresholds.",
        "",
    ])

    for name, path in [("CBC MILP", safety_milp_path), ("Min-Max MILP", safety_minmax_path)]:
        if path.exists():
            df = pd.read_csv(path)
            if not df.empty and "safety_threshold" in df.columns:
                lines.append(f"### {name}")
                lines.append("")
                cols = ["safety_threshold", "total_cost_usd", "total_co2e_tonnes", "fleet_size", "avg_safety_score"]
                cols = [c for c in cols if c in df.columns]
                sub = df[cols]
                lines.append(_df_to_md(sub))
                lines.append("")
        else:
            lines.append(f"*No data for {name}*")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Charts generated",
        "",
        "### CBC MILP (test 1)",
        "",
        f"- Main charts: `{chart_dir_milp}`",
        "  - `carbon_price_sweep_milp.png`",
        "  - `fleet_composition_milp.png`",
        "  - `macc_milp.png`, `macc_full_range_milp.png`",
        "  - `pareto_frontier_milp.png`",
        "  - `safety_comparison_milp.png`",
        f"- Sensitivity plots: `{chart_dir_milp.parent / 'sensitivity' / 'plots'}` (e.g. `carbon_price_sensitivity_milp.png`, `macc_milp.png`, `tornado_analysis_milp.png`, etc.)",
        "",
        "### Min-Max MILP (test 2)",
        "",
        f"- Main charts: `{chart_dir_minmax}`",
        "  - `carbon_price_sweep_minmax.png`",
        "  - `fleet_composition_minmax.png`",
        "  - `macc_minmax.png`, `macc_full_range_minmax.png`",
        "  - `pareto_frontier_minmax.png`",
        "  - `safety_comparison_minmax.png`",
        f"- Sensitivity plots: `{chart_dir_minmax.parent / 'sensitivity' / 'plots'}` (e.g. `carbon_price_sensitivity_minmax.png`, `macc_minmax.png`, `tornado_analysis_minmax.png`, etc.)",
        "",
        "---",
        "",
        "## 5. Summary",
        "",
        "- **CBC MILP** minimizes cost for the base scenario only; the fleet is optimal for current assumptions but may perform worse under higher carbon prices or stricter safety.",
        "- **Min-Max MILP** chooses a fleet that limits the worst-case cost across several stress scenarios, at the cost of potentially higher base-scenario cost.",
        "- Sensitivity analysis (carbon price sweep, safety sweep) shows how each chosen fleet behaves when assumptions change, without re-optimizing.",
        "",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
