"""
Visualize sensitivity analysis results.

Creates comprehensive charts:
1. Sensitivity matrix/heatmap
2. Pareto frontier (cost vs safety)
3. Carbon price response curves
4. 2024 scenario comparison
5. Fleet composition breakdown
6. CII distribution
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_sensitivity_results(results_dir: str = 'outputs/sensitivity') -> dict[str, pd.DataFrame]:
    """Load all sensitivity CSV results."""
    results_path = Path(results_dir)

    data = {}
    files = {
        'base_case': 'base_case.csv',
        'safety': 'safety_sensitivity.csv',
        'carbon': 'carbon_price_sensitivity.csv',
        'scenarios_2024': '2024_scenarios.csv',
    }

    for key, filename in files.items():
        filepath = results_path / filename
        if filepath.exists():
            data[key] = pd.read_csv(filepath)
            print(f"Loaded {key}: {len(data[key])} rows")
        else:
            print(f"Warning: {filename} not found")
            data[key] = pd.DataFrame()

    return data


def plot_safety_pareto_frontier(df_safety: pd.DataFrame, output_path: Path) -> None:
    """
    Plot cost vs safety Pareto frontier.

    Shows marginal cost of safety improvements.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Filter valid rows
    df = df_safety[df_safety['total_cost_usd'] > 0].copy()

    if len(df) == 0:
        print("No valid safety data for Pareto plot")
        return

    # Plot 1: Cost vs Safety
    ax1.plot(df['avg_safety_score'], df['total_cost_usd'] / 1e6,
             marker='o', linewidth=2, markersize=10, color='#2E86AB')
    ax1.fill_between(df['avg_safety_score'], 0, df['total_cost_usd'] / 1e6,
                      alpha=0.3, color='#2E86AB')

    ax1.set_xlabel('Average Fleet Safety Score', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Fleet Cost (Million USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Cost-Safety Pareto Frontier', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Annotate points
    for _, row in df.iterrows():
        ax1.annotate(f"≥{row['safety_threshold']:.1f}",
                    xy=(row['avg_safety_score'], row['total_cost_usd'] / 1e6),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=9, alpha=0.7)

    # Plot 2: Fleet size vs Safety
    ax2.plot(df['safety_threshold'], df['fleet_size'],
             marker='s', linewidth=2, markersize=10, color='#A23B72')
    ax2.fill_between(df['safety_threshold'], 0, df['fleet_size'],
                      alpha=0.3, color='#A23B72')

    ax2.set_xlabel('Minimum Safety Threshold', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Fleet Size (Number of Vessels)', fontsize=12, fontweight='bold')
    ax2.set_title('Fleet Size vs Safety Constraint', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'safety_pareto_frontier.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'safety_pareto_frontier.png'}")


def plot_carbon_price_sensitivity(df_carbon: pd.DataFrame, output_path: Path) -> None:
    """
    Plot carbon price sensitivity curves.

    Shows how fleet cost and CO2eq respond to carbon pricing.
    """
    df = df_carbon[df_carbon['total_cost_usd'] > 0].copy()

    if len(df) == 0:
        print("No valid carbon price data")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    carbon_prices = df['carbon_price_usd_per_tco2e']

    # Plot 1: Total cost vs carbon price
    ax1.plot(carbon_prices, df['total_cost_usd'] / 1e6,
             marker='D', linewidth=2, markersize=10, color='#F18F01', label='Total Cost')

    ax1.set_xlabel('Carbon Price (USD/tonne CO₂eq)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Fleet Cost (Million USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Fleet Cost vs Carbon Price', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot 2: Emissions vs carbon price
    ax2.plot(carbon_prices, df['total_co2e_tonnes'] / 1000,
             marker='o', linewidth=2, markersize=10, color='#6A994E', label='CO₂eq Emissions')

    ax2.set_xlabel('Carbon Price (USD/tonne CO₂eq)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Total Fleet Emissions (Thousand tonnes CO₂eq)', fontsize=12, fontweight='bold')
    ax2.set_title('Fleet Emissions vs Carbon Price', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Add elasticity annotation
    if len(df) >= 2:
        cost_change_pct = ((df['total_cost_usd'].iloc[-1] - df['total_cost_usd'].iloc[0]) /
                           df['total_cost_usd'].iloc[0]) * 100
        emis_change_pct = ((df['total_co2e_tonnes'].iloc[-1] - df['total_co2e_tonnes'].iloc[0]) /
                           max(df['total_co2e_tonnes'].iloc[0], 1)) * 100

        ax1.text(0.05, 0.95, f'Cost change: {cost_change_pct:+.1f}%',
                transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax2.text(0.05, 0.95, f'Emissions change: {emis_change_pct:+.1f}%',
                transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path / 'carbon_price_sensitivity.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'carbon_price_sensitivity.png'}")


def plot_2024_scenario_comparison(df_scenarios: pd.DataFrame, output_path: Path) -> None:
    """
    Compare 2024 route-specific scenarios.

    Bar chart comparing key metrics across Base/Typical/Stress scenarios.
    """
    if len(df_scenarios) == 0:
        print("No 2024 scenario data")
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    scenarios = df_scenarios['scenario_name'].tolist()
    colors = ['#4A90E2', '#F39C12', '#E74C3C']

    # Plot 1: Total cost
    ax = axes[0, 0]
    costs = df_scenarios['total_cost_usd'] / 1e6
    bars = ax.bar(scenarios, costs, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Total Fleet Cost (Million USD)', fontsize=11, fontweight='bold')
    ax.set_title('Fleet Cost by Scenario', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${height:.1f}M',
                   ha='center', va='bottom', fontsize=9)

    # Plot 2: Emissions
    ax = axes[0, 1]
    emissions = df_scenarios['total_co2e_tonnes'] / 1000
    bars = ax.bar(scenarios, emissions, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Total Emissions (Thousand tonnes CO₂eq)', fontsize=11, fontweight='bold')
    ax.set_title('Fleet Emissions by Scenario', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}kt',
               ha='center', va='bottom', fontsize=9)

    # Plot 3: Fleet size
    ax = axes[1, 0]
    fleet_sizes = df_scenarios['fleet_size']
    bars = ax.bar(scenarios, fleet_sizes, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Fleet Size (Number of Vessels)', fontsize=11, fontweight='bold')
    ax.set_title('Fleet Size by Scenario', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{int(height)}',
               ha='center', va='bottom', fontsize=9)

    # Plot 4: Average CII (if available)
    ax = axes[1, 1]
    if 'avg_cii' in df_scenarios.columns:
        cii_values = df_scenarios['avg_cii'].fillna(0)
        bars = ax.bar(scenarios, cii_values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_ylabel('Average CII (g CO₂/tonne·NM)', fontsize=11, fontweight='bold')
        ax.set_title('Carbon Intensity by Scenario', fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=9)
    else:
        ax.text(0.5, 0.5, 'CII data not available',
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path / '2024_scenario_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / '2024_scenario_comparison.png'}")


def plot_sensitivity_matrix(data: dict[str, pd.DataFrame], output_path: Path) -> None:
    """
    Create sensitivity matrix heatmap showing how key metrics change.

    Rows: Different sensitivities (Safety, Carbon Price, 2024 Scenarios)
    Columns: Metrics (Cost, Emissions, Fleet Size, Safety)
    """
    # Build matrix data
    matrix_data = []
    row_labels = []

    # Safety sensitivity
    df_safety = data['safety']
    if not df_safety.empty:
        for _, row in df_safety.iterrows():
            if row['total_cost_usd'] > 0:
                matrix_data.append([
                    row['total_cost_usd'] / 1e6,
                    row['total_co2e_tonnes'] / 1000,
                    row['fleet_size'],
                    row['avg_safety_score']
                ])
                row_labels.append(f"Safety≥{row['safety_threshold']:.1f}")

    # Carbon price sensitivity
    df_carbon = data['carbon']
    if not df_carbon.empty:
        for _, row in df_carbon.iterrows():
            if row['total_cost_usd'] > 0:
                matrix_data.append([
                    row['total_cost_usd'] / 1e6,
                    row['total_co2e_tonnes'] / 1000,
                    row['fleet_size'],
                    row['avg_safety_score']
                ])
                row_labels.append(f"C${int(row['carbon_price_usd_per_tco2e'])}")

    # 2024 scenarios
    df_scenarios = data['scenarios_2024']
    if not df_scenarios.empty:
        for _, row in df_scenarios.iterrows():
            if row['total_cost_usd'] > 0:
                matrix_data.append([
                    row['total_cost_usd'] / 1e6,
                    row['total_co2e_tonnes'] / 1000,
                    row['fleet_size'],
                    row['avg_safety_score']
                ])
                row_labels.append(row['scenario_name'][:12])  # Truncate

    if not matrix_data:
        print("No data for sensitivity matrix")
        return

    # Create DataFrame
    df_matrix = pd.DataFrame(matrix_data, columns=[
        'Cost (M$)',
        'Emissions (kt CO₂eq)',
        'Fleet Size',
        'Avg Safety'
    ], index=row_labels)

    # Normalize for heatmap
    df_normalized = (df_matrix - df_matrix.min()) / (df_matrix.max() - df_matrix.min())

    # Plot
    fig, ax = plt.subplots(figsize=(10, max(8, len(row_labels) * 0.4)))
    sns.heatmap(df_normalized, annot=df_matrix.round(1), fmt='g',
                cmap='RdYlGn_r', cbar_kws={'label': 'Normalized Value'},
                linewidths=0.5, ax=ax)

    ax.set_title('Sensitivity Analysis Matrix\n(Cell values show actual metrics, color shows normalized scale)',
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Metrics', fontsize=12, fontweight='bold')
    ax.set_ylabel('Sensitivity Cases', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path / 'sensitivity_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'sensitivity_matrix.png'}")


def plot_combined_summary(data: dict[str, pd.DataFrame], output_path: Path) -> None:
    """
    Create single-page summary dashboard with all key insights.
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('Comprehensive Sensitivity Analysis Summary\nMaritime Hackathon 2026',
                fontsize=18, fontweight='bold', y=0.98)

    # 1. Safety Pareto (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    df_safety = data['safety'][data['safety']['total_cost_usd'] > 0]
    if not df_safety.empty:
        ax1.plot(df_safety['avg_safety_score'], df_safety['total_cost_usd'] / 1e6,
                marker='o', linewidth=2, color='#2E86AB')
        ax1.set_xlabel('Avg Safety Score', fontsize=10)
        ax1.set_ylabel('Cost (M$)', fontsize=10)
        ax1.set_title('Cost vs Safety', fontsize=11, fontweight='bold')
        ax1.grid(True, alpha=0.3)

    # 2. Carbon price response (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    df_carbon = data['carbon'][data['carbon']['total_cost_usd'] > 0]
    if not df_carbon.empty:
        ax2.plot(df_carbon['carbon_price_usd_per_tco2e'], df_carbon['total_co2e_tonnes'] / 1000,
                marker='D', linewidth=2, color='#6A994E')
        ax2.set_xlabel('Carbon Price ($/tCO₂eq)', fontsize=10)
        ax2.set_ylabel('Emissions (kt CO₂eq)', fontsize=10)
        ax2.set_title('Emissions vs Carbon Price', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3)

    # 3. 2024 scenarios cost (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    df_scenarios = data['scenarios_2024']
    if not df_scenarios.empty:
        scenarios = df_scenarios['scenario_name']
        costs = df_scenarios['total_cost_usd'] / 1e6
        ax3.bar(range(len(scenarios)), costs, color=['#4A90E2', '#F39C12', '#E74C3C'], alpha=0.7)
        ax3.set_xticks(range(len(scenarios)))
        ax3.set_xticklabels(scenarios, rotation=15, ha='right', fontsize=9)
        ax3.set_ylabel('Cost (M$)', fontsize=10)
        ax3.set_title('2024 Scenario Costs', fontsize=11, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)

    # 4-9: More detailed panels
    # (Add more visualizations as needed)

    # Add watermark
    fig.text(0.99, 0.01, 'Generated by Maritime Optimization System',
            ha='right', va='bottom', fontsize=8, alpha=0.5)

    plt.savefig(output_path / 'summary_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'summary_dashboard.png'}")


def generate_all_visualizations(results_dir: str = 'outputs/sensitivity',
                                output_dir: Optional[str] = None) -> None:
    """
    Generate all visualization types.

    Args:
        results_dir: Directory containing CSV results
        output_dir: Directory to save plots (defaults to results_dir/plots)
    """
    if output_dir is None:
        output_dir = f"{results_dir}/plots"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Loading sensitivity results...")
    data = load_sensitivity_results(results_dir)

    print("\nGenerating visualizations...")

    # 1. Sensitivity matrix
    plot_sensitivity_matrix(data, output_path)

    # 2. Safety Pareto frontier
    if not data['safety'].empty:
        plot_safety_pareto_frontier(data['safety'], output_path)

    # 3. Carbon price sensitivity
    if not data['carbon'].empty:
        plot_carbon_price_sensitivity(data['carbon'], output_path)

    # 4. 2024 scenarios
    if not data['scenarios_2024'].empty:
        plot_2024_scenario_comparison(data['scenarios_2024'], output_path)

    # 5. Summary dashboard
    plot_combined_summary(data, output_path)

    print(f"\n✓ All visualizations saved to {output_path}")


if __name__ == '__main__':
    import sys

    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'outputs/sensitivity'
    generate_all_visualizations(results_dir)
