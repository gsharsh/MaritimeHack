"""
Chart generation for fleet optimization analysis.
"""

import os
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be set before importing pyplot

import matplotlib.pyplot as plt
import numpy as np


def plot_pareto_frontier(
    pareto_results: list[dict[str, Any]],
    output_path: str = "outputs/charts/pareto_frontier.png",
) -> str:
    """
    Plot cost-emissions Pareto frontier and save to PNG.

    Parameters
    ----------
    pareto_results : list[dict]
        Output from run_pareto_sweep(). Each dict has keys:
        feasible, total_co2e_tonnes, total_cost_usd, etc.
    output_path : str
        File path for the saved PNG.

    Returns
    -------
    str
        The path to the saved chart file.
    """
    # Filter to feasible points only
    feasible = [r for r in pareto_results if r["feasible"]]

    if not feasible:
        print("WARNING: No feasible Pareto points to plot.")
        return output_path

    co2_values = [r["total_co2e_tonnes"] for r in feasible]
    cost_values = [r["total_cost_usd"] for r in feasible]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Line + scatter plot
    ax.plot(co2_values, cost_values, "o-", color="#2563eb", markersize=6, linewidth=2)

    # Axes labels
    ax.set_xlabel("Total CO2eq (tonnes)", fontsize=12)
    ax.set_ylabel("Total Fleet Cost (USD)", fontsize=12)

    # Title
    ax.set_title("Cost-Emissions Pareto Frontier", fontsize=14, fontweight="bold")

    # Grid lines
    ax.grid(True, alpha=0.3, linestyle="--")

    # Annotate base case (first point = min cost / max emissions)
    ax.annotate(
        f"Min Cost\n${cost_values[0]:,.0f}",
        xy=(co2_values[0], cost_values[0]),
        xytext=(15, -25),
        textcoords="offset points",
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="gray"),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray"),
    )

    # Annotate min-emissions point (last point)
    if len(feasible) > 1:
        ax.annotate(
            f"Min Emissions\n{co2_values[-1]:,.0f} t",
            xy=(co2_values[-1], cost_values[-1]),
            xytext=(-15, 25),
            textcoords="offset points",
            fontsize=9,
            arrowprops=dict(arrowstyle="->", color="gray"),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", edgecolor="gray"),
        )

    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path


def plot_fleet_composition(
    sweep_results: list[dict[str, Any]],
    output_path: str = "outputs/charts/fleet_composition.png",
) -> str:
    """
    Plot stacked bar chart of fleet composition by fuel type across safety thresholds.

    Parameters
    ----------
    sweep_results : list[dict]
        Output from run_safety_sweep(). Each dict has keys:
        threshold, feasible, fuel_type_counts, etc.
    output_path : str
        File path for the saved PNG.

    Returns
    -------
    str
        The path to the saved chart file.
    """
    # Filter to feasible thresholds
    feasible = [r for r in sweep_results if r["feasible"]]

    if not feasible:
        print("WARNING: No feasible sweep points to plot fleet composition.")
        return output_path

    # Collect all fuel types across all thresholds
    all_fuel_types: set[str] = set()
    for r in feasible:
        all_fuel_types.update(r["fuel_type_counts"].keys())
    fuel_types_sorted = sorted(all_fuel_types)

    # Build data arrays
    thresholds = [str(r["threshold"]) for r in feasible]
    x = np.arange(len(thresholds))

    # Use tab10 colormap for distinct colors
    cmap = plt.cm.get_cmap("tab10")
    colors = [cmap(i) for i in range(len(fuel_types_sorted))]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Build stacked bars
    bottom = np.zeros(len(thresholds))
    for i, ft in enumerate(fuel_types_sorted):
        counts = [r["fuel_type_counts"].get(ft, 0) for r in feasible]
        ax.bar(x, counts, bottom=bottom, label=ft, color=colors[i], width=0.6)
        bottom += np.array(counts)

    # Mark infeasible thresholds on x-axis
    infeasible = [r for r in sweep_results if not r["feasible"]]
    if infeasible:
        inf_labels = [str(r["threshold"]) for r in infeasible]
        inf_x = np.arange(len(thresholds), len(thresholds) + len(inf_labels))
        all_x = np.concatenate([x, inf_x])
        all_labels = thresholds + inf_labels
        for ix in inf_x:
            ax.text(ix, 0.5, "INFEASIBLE", ha="center", va="bottom",
                    fontsize=9, color="red", fontweight="bold", rotation=90)
        ax.set_xticks(all_x)
        ax.set_xticklabels(all_labels)
    else:
        ax.set_xticks(x)
        ax.set_xticklabels(thresholds)

    ax.set_xlabel("Safety Threshold", fontsize=12)
    ax.set_ylabel("Number of Vessels", fontsize=12)
    ax.set_title("Fleet Composition by Safety Threshold", fontsize=14, fontweight="bold")

    # Legend outside plot area below
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=4,
        fontsize=9,
        frameon=True,
    )

    ax.grid(True, alpha=0.3, linestyle="--", axis="y")

    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path
