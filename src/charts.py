"""
Chart generation for fleet optimization analysis.
"""

import os
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be set before importing pyplot

import matplotlib.pyplot as plt


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
