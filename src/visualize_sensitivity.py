"""
Visualize sensitivity analysis results.

Creates comprehensive charts:
1. Tornado analysis (replaces sensitivity matrix)
2. Pareto frontier (cost vs safety)
3. Carbon price response curves
4. 2024 scenario comparison
5. Summary dashboard

Tornado analysis: shows how key outputs (cost, emissions) vary across sensitivity
cases (each safety threshold and carbon price). Each case = one horizontal bar;
bars are sorted by impact so the case with the largest value is at the top
(tornado shape). Clarifies which assumptions drive the most change.
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

    Left: cost vs minimum safety threshold (one point per constraint, clear curve).
    Right: fleet size vs minimum safety threshold.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Filter valid rows and sort by threshold so the line connects in order
    df = df_safety[df_safety['total_cost_usd'] > 0].copy()
    if len(df) == 0:
        print("No valid safety data for Pareto plot")
        return
    df = df.sort_values('safety_threshold').reset_index(drop=True)

    # Plot 1: Cost vs minimum safety threshold (x = threshold, so one point per run, no duplicates)
    ax1.plot(df['safety_threshold'], df['total_cost_usd'] / 1e6,
             marker='o', linewidth=2, markersize=10, color='#2E86AB')
    ax1.fill_between(df['safety_threshold'], 0, df['total_cost_usd'] / 1e6,
                      alpha=0.3, color='#2E86AB')

    ax1.set_xlabel('Minimum Safety Threshold', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Fleet Cost (Million USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Cost vs Safety Threshold', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Annotate with threshold (matches x-axis)
    for _, row in df.iterrows():
        ax1.annotate(f"≥{row['safety_threshold']:.1f}",
                    xy=(row['safety_threshold'], row['total_cost_usd'] / 1e6),
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


# --- Mandatory methodology charts (1–5) ---------------------------------------


def plot_cost_vs_safety_threshold(df_safety: pd.DataFrame, output_path: Path) -> None:
    """
    Line chart: Total Fleet Cost vs Safety Threshold.
    Optional second line: Fleet size (or total DWT).
    Shows marginal cost of safety.
    """
    df = df_safety[df_safety['total_cost_usd'] > 0].copy()
    if len(df) == 0:
        return
    df = df.sort_values('safety_threshold').reset_index(drop=True)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(df['safety_threshold'], df['total_cost_usd'] / 1e6, marker='o', linewidth=2,
             markersize=10, color='#2E86AB', label='Total fleet cost (M$)')
    ax1.set_xlabel('Minimum average safety threshold', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total fleet cost (Million USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Total Fleet Cost vs Safety Threshold', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    ax2 = ax1.twinx()
    ax2.plot(df['safety_threshold'], df['fleet_size'], marker='s', linewidth=2,
             markersize=8, color='#A23B72', linestyle='--', label='Fleet size')
    ax2.set_ylabel('Fleet size (number of vessels)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(output_path / 'cost_vs_safety_threshold.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'cost_vs_safety_threshold.png'}")


def plot_cost_breakdown_vs_safety(df_safety: pd.DataFrame, output_path: Path) -> None:
    """
    Stacked bar: Cost breakdown (CAPEX, Fuel, Carbon, Risk premium) vs safety threshold.
    """
    need = ['total_capex', 'total_fuel_cost', 'total_carbon_cost', 'total_risk_premium']
    if not all(c in df_safety.columns for c in need):
        print("Cost breakdown columns missing; skip cost breakdown chart")
        return
    df = df_safety[df_safety['total_cost_usd'] > 0].copy()
    if len(df) == 0:
        return
    df = df.sort_values('safety_threshold').reset_index(drop=True)
    x = df['safety_threshold'].astype(str)
    cap = (df['total_capex'] / 1e6).fillna(0)
    fuel = (df['total_fuel_cost'] / 1e6).fillna(0)
    carbon = (df['total_carbon_cost'] / 1e6).fillna(0)
    risk = (df['total_risk_premium'] / 1e6).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, cap, label='CAPEX', color='#4A90E2', alpha=0.9)
    ax.bar(x, fuel, bottom=cap, label='Fuel cost', color='#F39C12', alpha=0.9)
    ax.bar(x, carbon, bottom=cap + fuel, label='Carbon cost', color='#6A994E', alpha=0.9)
    ax.bar(x, risk, bottom=cap + fuel + carbon, label='Risk premium', color='#E74C3C', alpha=0.9)
    ax.set_xlabel('Minimum average safety threshold', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cost (Million USD)', fontsize=12, fontweight='bold')
    ax.set_title('Cost Breakdown vs Safety Threshold', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path / 'cost_breakdown_vs_safety.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'cost_breakdown_vs_safety.png'}")


def plot_emissions_vs_safety_threshold(df_safety: pd.DataFrame, output_path: Path) -> None:
    """
    Line chart: Fleet emissions (total CO₂eq) vs safety threshold.
    """
    df = df_safety[df_safety['total_cost_usd'] > 0].copy()
    if len(df) == 0:
        return
    df = df.sort_values('safety_threshold').reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['safety_threshold'], df['total_co2e_tonnes'] / 1000, marker='o', linewidth=2,
            markersize=10, color='#6A994E')
    ax.set_xlabel('Minimum average safety threshold', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total fleet CO₂eq (thousand tonnes)', fontsize=12, fontweight='bold')
    ax.set_title('Fleet Emissions vs Safety Threshold', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path / 'emissions_vs_safety_threshold.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'emissions_vs_safety_threshold.png'}")


def plot_fuel_mix_vs_carbon_price(df_carbon: pd.DataFrame, output_path: Path) -> None:
    """
    Stacked bar: Share of fleet by total DWT by fuel type vs carbon price.
    x: Carbon price ($80, $120, $160, $200); y: share of DWT (stacks = fuel types).
    """
    df = df_carbon[df_carbon['total_cost_usd'] > 0].copy()
    if len(df) == 0:
        return
    dwt_cols = [c for c in df.columns if c.startswith('dwt_')]
    if not dwt_cols:
        print("No dwt_* columns; skip fuel mix vs carbon price chart")
        return
    df = df.sort_values('carbon_price_usd_per_tco2e').reset_index(drop=True)
    x_labels = [f"${int(p)}" for p in df['carbon_price_usd_per_tco2e']]
    x_pos = np.arange(len(x_labels))
    total_dwt = df[dwt_cols].sum(axis=1)
    total_dwt = total_dwt.replace(0, np.nan)
    # Stack order: deterministic by column name
    fuel_order = sorted(dwt_cols, key=lambda c: c.replace('dwt_', ''))
    bottom = np.zeros(len(df))
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(fuel_order)))
    for i, col in enumerate(fuel_order):
        share = (df[col].fillna(0) / total_dwt).fillna(0).values
        ax.bar(x_pos, share, bottom=bottom, label=col.replace('dwt_', ''), color=colors[i % len(colors)], alpha=0.9)
        bottom = bottom + share
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel('Carbon price (USD / tCO₂eq)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Share of fleet DWT', fontsize=12, fontweight='bold')
    ax.set_title('Fuel Mix (DWT share) vs Carbon Price', fontsize=14, fontweight='bold')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
    ax.set_ylim(0, 1)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path / 'fuel_mix_vs_carbon_price.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'fuel_mix_vs_carbon_price.png'}")


def plot_macc(data: dict[str, pd.DataFrame], output_path: Path) -> None:
    """
    MACC: Marginal Abatement Cost Curve (formal definition).
    Baseline: min avg safety ≥ 3.0, carbon price = USD 80/tCO₂eq.
    Scenarios: safety tightening only (≥3.5, ≥4.0, ≥4.5). No carbon-price scenarios.
    x-axis: Cumulative CO₂eq abated (tonnes). y-axis: MAC (USD/tCO₂eq).
    Bars contiguous; each bar = one scenario (bar_left, width=abatement, height=MAC).
    Fallback: if abatement volumes are extremely small, plot simple bar chart and skip MACC.
    """
    base = data.get('base_case')
    safety = data.get('safety')
    if base is None or base.empty or safety is None or safety.empty:
        return
    base_row = base.iloc[0]
    baseline_co2 = float(base_row.get('total_co2e_tonnes') or 0)
    baseline_cost = float(base_row.get('total_cost_usd') or 0)
    if baseline_co2 <= 0:
        return

    # One policy axis only: safety tightening. Exclude baseline (3.0) and carbon scenarios.
    rows = []
    for _, row in safety.iterrows():
        t = row.get('safety_threshold')
        if t is None or t <= 3.0:
            continue
        co2_i = row.get('total_co2e_tonnes')
        cost_i = row.get('total_cost_usd')
        if co2_i is None or cost_i is None or cost_i <= 0:
            continue
        abatement = baseline_co2 - float(co2_i)  # tonnes
        if abatement <= 0:
            continue
        delta_cost = float(cost_i) - baseline_cost
        mac = delta_cost / abatement  # USD / tCO₂eq
        rows.append({
            'threshold': t,
            'label': f"≥{t:.1f}",
            'abatement': abatement,
            'delta_cost': delta_cost,
            'mac': mac,
        })
    if not rows:
        return

    df = pd.DataFrame(rows)
    # Sort by increasing MAC (MACC construction rule)
    df = df.sort_values('mac', ascending=True).reset_index(drop=True)
    df['cum_abatement'] = df['abatement'].cumsum()
    df['bar_left'] = df['cum_abatement'] - df['abatement']

    # Fallback: if abatement volumes are extremely small, MACC would be visually misleading.
    total_abate = df['abatement'].sum()
    if total_abate < 1.0 or (df['abatement'].max() / max(total_abate, 1e-9) < 1e-6):
        # Produce simple bar chart instead; state limitation in comment (see docstring).
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(df['label'], df['mac'], color='#2E86AB', alpha=0.85, edgecolor='#1a5276')
        ax.axhline(80, color='gray', linestyle='--', linewidth=1.5, label='Carbon price $80/tCO₂eq')
        ax.set_xlabel('Safety threshold (vs baseline ≥3.0)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Marginal abatement cost (USD / tCO₂eq)', fontsize=12, fontweight='bold')
        ax.set_title('Marginal abatement cost by safety scenario (vs baseline)\n(Abatement volumes too small for contiguous MACC)', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'macc.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path / 'macc.png'} (fallback bar chart)")
        return

    # Proper MACC: x = cumulative abatement (tonnes), y = MAC ($/t). Contiguous bars.
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(df)))
    for i, (_, r) in enumerate(df.iterrows()):
        ax.bar(r['bar_left'], r['mac'], width=r['abatement'], align='edge', color=colors[i], alpha=0.9, edgecolor='#1a5276', linewidth=0.8)
        # Label at bar centre
        ax.text(r['bar_left'] + r['abatement'] / 2, r['mac'] / 2, r['label'], ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.axhline(80, color='red', linestyle='--', linewidth=1.5, label='Carbon price $80/tCO₂eq')
    ax.set_xlabel('Cumulative CO₂eq abated (tonnes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Marginal abatement cost (USD / tCO₂eq)', fontsize=12, fontweight='bold')
    ax.set_title('MACC: Marginal Abatement Cost Curve\n(Baseline: Safety≥3.0, C$80/tCO₂eq. Safety-tightening scenarios only.)', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(output_path / 'macc.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'macc.png'}")


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


def _build_tornado_cases(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build a single DataFrame of sensitivity cases with cost and emissions for tornado charts."""
    rows = []
    # Safety sensitivity
    df_safety = data['safety']
    if not df_safety.empty:
        for _, row in df_safety.iterrows():
            if row['total_cost_usd'] > 0:
                rows.append({
                    'case': f"Safety≥{row['safety_threshold']:.1f}",
                    'cost_m': row['total_cost_usd'] / 1e6,
                    'emissions_kt': row['total_co2e_tonnes'] / 1000,
                    'fleet_size': row['fleet_size'],
                    'avg_safety': row['avg_safety_score'],
                })
    # Carbon price sensitivity
    df_carbon = data['carbon']
    if not df_carbon.empty:
        for _, row in df_carbon.iterrows():
            if row['total_cost_usd'] > 0:
                rows.append({
                    'case': f"C${int(row['carbon_price_usd_per_tco2e'])}",
                    'cost_m': row['total_cost_usd'] / 1e6,
                    'emissions_kt': row['total_co2e_tonnes'] / 1000,
                    'fleet_size': row['fleet_size'],
                    'avg_safety': row['avg_safety_score'],
                })
    # 2024 scenarios (if present)
    df_scenarios = data['scenarios_2024']
    if not df_scenarios.empty:
        for _, row in df_scenarios.iterrows():
            if row['total_cost_usd'] > 0:
                rows.append({
                    'case': (row['scenario_name'][:14] if 'scenario_name' in row else 'Scenario'),
                    'cost_m': row['total_cost_usd'] / 1e6,
                    'emissions_kt': row['total_co2e_tonnes'] / 1000,
                    'fleet_size': row['fleet_size'],
                    'avg_safety': row['avg_safety_score'],
                })
    return pd.DataFrame(rows)


def plot_tornado_analysis(data: dict[str, pd.DataFrame], output_path: Path) -> None:
    """
    Tornado analysis: one horizontal bar per sensitivity case, sorted by impact.

    What it shows:
      - Each bar = one sensitivity case (e.g. Safety≥3.5 or C$120).
      - Bar length = value of the metric (cost or emissions).
      - Cases are sorted by that metric (highest at top) so the "tornado" shape
        makes it clear which assumptions drive the most change.

    Two panels: Total Cost (M$) and Emissions (kt CO₂eq), using the same cases
    (safety thresholds + carbon prices). No base-case reference line; the chart
    compares levels across scenarios.
    """
    df = _build_tornado_cases(data)
    if df.empty:
        print("No data for tornado analysis")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(6, len(df) * 0.45)))

    # Sort by cost descending (tornado: highest impact at top)
    df_cost = df.sort_values('cost_m', ascending=True).reset_index(drop=True)
    y_pos = np.arange(len(df_cost))
    bars1 = ax1.barh(y_pos, df_cost['cost_m'], height=0.7, color='#2E86AB', alpha=0.85, edgecolor='#1a5276')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(df_cost['case'], fontsize=10)
    ax1.set_xlabel('Total Fleet Cost (Million USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Tornado: Cost by sensitivity case', fontsize=13, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    # Sort by emissions descending
    df_emis = df.sort_values('emissions_kt', ascending=True).reset_index(drop=True)
    bars2 = ax2.barh(y_pos, df_emis['emissions_kt'], height=0.7, color='#6A994E', alpha=0.85, edgecolor='#2d5a27')
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_emis['case'], fontsize=10)
    ax2.set_xlabel('Total Emissions (kt CO₂eq)', fontsize=12, fontweight='bold')
    ax2.set_title('Tornado: Emissions by sensitivity case', fontsize=13, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)

    fig.suptitle(
        'Tornado analysis: one bar per sensitivity case (safety threshold or carbon price).\n'
        'Sorted by metric value so the case with largest impact is at the top.',
        fontsize=11, fontweight='normal', y=1.02,
    )
    plt.tight_layout()
    plt.savefig(output_path / 'tornado_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path / 'tornado_analysis.png'}")


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

    # 1. Tornado analysis (replaces sensitivity matrix)
    plot_tornado_analysis(data, output_path)

    # 2. Safety Pareto frontier
    if not data['safety'].empty:
        plot_safety_pareto_frontier(data['safety'], output_path)

    # 3. Mandatory methodology charts (1–5)
    if not data['safety'].empty:
        plot_cost_vs_safety_threshold(data['safety'], output_path)
        plot_cost_breakdown_vs_safety(data['safety'], output_path)
        plot_emissions_vs_safety_threshold(data['safety'], output_path)
    if not data['carbon'].empty:
        plot_carbon_price_sensitivity(data['carbon'], output_path)
        plot_fuel_mix_vs_carbon_price(data['carbon'], output_path)
    plot_macc(data, output_path)

    # 4. 2024 scenarios
    if not data['scenarios_2024'].empty:
        plot_2024_scenario_comparison(data['scenarios_2024'], output_path)

    # 5. Summary dashboard
    plot_combined_summary(data, output_path)

    print(f"\nAll visualizations saved to {output_path}")


if __name__ == '__main__':
    import sys

    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'outputs/sensitivity'
    generate_all_visualizations(results_dir)
