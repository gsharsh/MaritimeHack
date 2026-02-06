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


def plot_safety_comparison(
    sweep_results: list[dict[str, Any]],
    output_path: str = "outputs/charts/safety_comparison.png",
) -> str:
    """
    Plot a table visualization comparing key metrics across safety thresholds.

    Parameters
    ----------
    sweep_results : list[dict]
        Output from run_safety_sweep(). Each dict has keys:
        threshold, feasible, fleet_size, total_cost_usd, avg_safety_score,
        total_co2e_tonnes, total_dwt, etc.
    output_path : str
        File path for the saved PNG.

    Returns
    -------
    str
        The path to the saved chart file.
    """
    if not sweep_results:
        print("WARNING: No sweep results to plot safety comparison.")
        return output_path

    # Build table data
    col_labels = [
        "Threshold",
        "Fleet Size",
        "Total Cost ($M)",
        "Avg Safety",
        "Total CO2eq (kt)",
        "Total DWT (kt)",
    ]

    cell_text = []
    cell_colors = []

    for r in sweep_results:
        if r["feasible"]:
            row = [
                f"{r['threshold']:.1f}",
                str(r["fleet_size"]),
                f"${r['total_cost_usd'] / 1_000_000:.2f}M",
                f"{r['avg_safety_score']:.2f}",
                f"{r['total_co2e_tonnes'] / 1_000:.2f}",
                f"{r['total_dwt'] / 1_000:.1f}",
            ]
            # Color-code: green for base (3.0), yellow/orange for higher
            if r["threshold"] <= 3.0:
                row_color = ["#d4edda"] * len(col_labels)  # light green
            elif r["threshold"] <= 3.5:
                row_color = ["#fff3cd"] * len(col_labels)  # light yellow
            elif r["threshold"] <= 4.0:
                row_color = ["#ffe0b2"] * len(col_labels)  # light orange
            else:
                row_color = ["#ffccbc"] * len(col_labels)  # deeper orange
        else:
            row = [
                f"{r['threshold']:.1f}",
                "-",
                "-",
                "-",
                "-",
                "-",
            ]
            row_color = ["#f8d7da"] * len(col_labels)  # light red

        cell_text.append(row)
        cell_colors.append(row_color)

    fig, ax = plt.subplots(figsize=(10, 2 + 0.5 * len(sweep_results)))
    ax.axis("off")

    ax.set_title(
        "Safety Threshold Comparison",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellColours=cell_colors,
        colColours=["#cce5ff"] * len(col_labels),  # light blue header
        loc="center",
        cellLoc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.8)

    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path
