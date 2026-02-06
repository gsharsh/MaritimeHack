"""
Enhanced sensitivity analysis including:
1. Safety threshold sweep (baseline)
2. Carbon price sensitivity
3. 2024 route-specific adjustments (CII, port congestion, fuel price volatility)

Based on Methodology_Report.md Section 4.4 and Methodology_SOP.md Section 8.3
"""

from pathlib import Path
from typing import Any
import pandas as pd
import numpy as np

from .optimization import (
    select_fleet_greedy,
    total_cost_and_metrics,
    validate_fleet,
)


# IMO CII calculation and rating
ROUTE_DISTANCE_NM = 1762  # Singapore to West Australia


def calculate_cii(co2_tonnes: float, dwt: float, distance_nm: float = ROUTE_DISTANCE_NM) -> float:
    """
    Calculate Carbon Intensity Indicator (CII) in g CO2 / tonne·NM.

    CII = (CO2_total × 10^6) / (DWT × distance_nm)

    Args:
        co2_tonnes: Total CO2 emissions in tonnes (not CO2eq - use CO2 only)
        dwt: Deadweight tonnage
        distance_nm: Voyage distance in nautical miles

    Returns:
        CII value in g CO2 / tonne·NM
    """
    if dwt <= 0 or distance_nm <= 0:
        return 0.0
    return (co2_tonnes * 1_000_000) / (dwt * distance_nm)


def get_cii_rating(cii_value: float) -> str:
    """
    Assign IMO CII rating band (A-E) based on CII value.

    Simplified thresholds for chemical/products tankers.
    Real IMO thresholds are vessel-size and type-specific.

    Args:
        cii_value: CII in g CO2 / tonne·NM

    Returns:
        Rating: 'A' (best) to 'E' (worst)
    """
    if cii_value <= 3.5:
        return 'A'  # Superior
    elif cii_value <= 4.5:
        return 'B'  # Good
    elif cii_value <= 5.5:
        return 'C'  # Acceptable
    elif cii_value <= 6.5:
        return 'D'  # Needs improvement
    else:
        return 'E'  # Poor


def get_cii_penalty_multiplier(rating: str) -> float:
    """
    Get cost multiplier for CII rating.

    Args:
        rating: CII rating 'A' through 'E'

    Returns:
        Multiplier: < 1.0 = discount, > 1.0 = penalty
    """
    CII_PENALTY_MAP = {
        'A': 0.95,  # 5% discount
        'B': 0.98,  # 2% discount
        'C': 1.00,  # No change
        'D': 1.05,  # 5% penalty
        'E': 1.10,  # 10% penalty
    }
    return CII_PENALTY_MAP.get(rating, 1.0)


def apply_cii_penalties(df: pd.DataFrame, co2_col: str = "co2e_tonnes") -> pd.DataFrame:
    """
    Calculate CII and apply penalty multipliers to vessel costs.

    Adds columns: 'CII', 'CII_rating', 'CII_penalty_multiplier'
    Does NOT modify total_cost_usd - caller should apply multiplier.

    Args:
        df: DataFrame with vessel data
        co2_col: Column name for CO2 emissions

    Returns:
        DataFrame with CII columns added
    """
    df = df.copy()

    # Calculate CII per vessel
    df['CII'] = df.apply(
        lambda row: calculate_cii(row[co2_col], row['dwt']),
        axis=1
    )

    # Assign ratings
    df['CII_rating'] = df['CII'].apply(get_cii_rating)

    # Get penalty multipliers
    df['CII_penalty_multiplier'] = df['CII_rating'].apply(get_cii_penalty_multiplier)

    return df


def apply_fuel_price_multiplier(df: pd.DataFrame, multiplier: float, cost_col: str = "fuel_cost_usd") -> pd.DataFrame:
    """
    Apply fuel price volatility multiplier (e.g., 1.05 for +5%).

    Note: Recalculates total_cost_usd based on adjusted fuel cost.

    Args:
        df: DataFrame with cost columns
        multiplier: Price multiplier (e.g., 1.05 = +5%)
        cost_col: Fuel cost column name

    Returns:
        DataFrame with adjusted costs
    """
    df = df.copy()

    # Store original fuel cost
    df['fuel_cost_usd_original'] = df[cost_col]

    # Apply multiplier
    df[cost_col] = df[cost_col] * multiplier

    # Recalculate total cost
    # total_cost = fuel + carbon + ownership + risk_premium
    # risk_premium is based on (fuel + carbon + ownership), so need to recalc
    fuel_delta = df[cost_col] - df['fuel_cost_usd_original']
    df['total_cost_usd'] = df['total_cost_usd'] + fuel_delta

    # Recalculate risk premium with new base
    # risk_premium = (fuel + carbon + ownership) * adj_rate
    # New base = original_base + fuel_delta
    # This is approximate - for exact, would need to store safety_adj_rate

    return df


def add_port_congestion_fuel(
    df: pd.DataFrame,
    congestion_hours: float = 48,
    aux_load_factor: float = 0.5,
    fuel_col: str = "fuel_tonnes",
    co2_col: str = "co2e_tonnes",
) -> pd.DataFrame:
    """
    Add fuel consumption from port congestion delays.

    During anchorage, auxiliary engines and boilers continue running.
    This adds fuel consumption without changing voyage distance.

    Args:
        df: DataFrame with vessel data
        congestion_hours: Hours of delay (default 48 = 2 days)
        aux_load_factor: Auxiliary engine load factor during waiting
        fuel_col: Total fuel column to update
        co2_col: Total CO2 column to update

    Returns:
        DataFrame with increased fuel and emissions
    """
    df = df.copy()

    # Calculate additional auxiliary fuel consumption
    # FC_ae = (ael × sfc_ae × hours) / 1,000,000
    # FC_ab = (abl × sfc_ab × hours) / 1,000,000

    df['congestion_fuel_ae'] = (df['ael'] * df['sfc_ae'] * congestion_hours * aux_load_factor) / 1_000_000
    df['congestion_fuel_ab'] = (df['abl'] * df['sfc_ab'] * congestion_hours * aux_load_factor) / 1_000_000
    df['congestion_fuel_total'] = df['congestion_fuel_ae'] + df['congestion_fuel_ab']

    # Add to total fuel
    df[fuel_col] = df[fuel_col] + df['congestion_fuel_total']

    # Add emissions from congestion fuel (assume Distillate)
    # AE and AB always burn Distillate: Cf_CO2 = 3.206
    DISTILLATE_CF_CO2 = 3.206
    df['congestion_co2'] = df['congestion_fuel_total'] * DISTILLATE_CF_CO2
    df[co2_col] = df[co2_col] + df['congestion_co2']

    return df


def run_carbon_price_sensitivity(
    df: pd.DataFrame,
    cargo_demand_tonnes: float,
    min_safety: float,
    carbon_prices: list[float],
    require_all_fuel_types: bool = True,
) -> list[dict[str, Any]]:
    """
    Re-run fleet selection at different carbon prices.

    Args:
        df: DataFrame with vessel data (must have carbon costs already calculated)
        cargo_demand_tonnes: Monthly demand
        min_safety: Minimum average safety score
        carbon_prices: List of carbon prices to test (USD/tonne CO2eq)
        require_all_fuel_types: Require all 8 fuel types

    Returns:
        List of result dicts with metrics for each carbon price
    """
    results = []

    # Store original carbon cost and total cost
    df_orig = df.copy()
    original_carbon_price = df_orig['carbon_cost_usd'].iloc[0] / max(df_orig['co2e_tonnes'].iloc[0], 0.001) if len(df_orig) > 0 else 80

    for carbon_price in carbon_prices:
        df_test = df_orig.copy()

        # Recalculate carbon cost
        df_test['carbon_cost_usd'] = df_test['co2e_tonnes'] * carbon_price

        # Recalculate total cost
        # total = fuel + carbon + ownership + risk_premium
        # risk_premium = (fuel + carbon + ownership) * adj_rate
        # Need to recalculate properly

        base_cost = df_test['fuel_cost_usd'] + df_test['carbon_cost_usd'] + df_test['ownership_cost_usd']

        # Approximate risk premium recalculation
        # Assuming safety adjustment rates are stored or can be inferred
        # For simplicity, recalculate as proportion of new base
        original_base = df_orig['fuel_cost_usd'] + df_orig['carbon_cost_usd'] + df_orig['ownership_cost_usd']
        risk_premium_ratio = df_orig['risk_premium_usd'] / original_base.clip(lower=1)
        df_test['risk_premium_usd'] = base_cost * risk_premium_ratio

        df_test['total_cost_usd'] = base_cost + df_test['risk_premium_usd']

        # Select fleet
        try:
            selected = select_fleet_greedy(
                df_test,
                cargo_demand_tonnes=cargo_demand_tonnes,
                min_avg_safety=min_safety,
                require_all_fuel_types=require_all_fuel_types,
                cost_col='total_cost_usd',
            )

            metrics = total_cost_and_metrics(df_test, selected, cost_col='total_cost_usd')
            metrics['carbon_price_usd_per_tco2e'] = carbon_price

            results.append({
                'carbon_price': carbon_price,
                'error': None,
                'metrics': metrics,
                'selected_vessel_ids': selected,
            })
        except Exception as e:
            results.append({
                'carbon_price': carbon_price,
                'error': str(e),
                'metrics': None,
                'selected_vessel_ids': [],
            })

    return results


def run_2024_scenario(
    df: pd.DataFrame,
    cargo_demand_tonnes: float,
    min_safety: float,
    scenario_config: dict[str, Any],
    require_all_fuel_types: bool = True,
) -> dict[str, Any]:
    """
    Run single 2024 scenario with specified adjustments.

    Scenario config should contain:
    - fuel_price_multiplier: float (e.g., 1.05)
    - congestion_hours: float (e.g., 48)
    - cii_enforcement: bool

    Args:
        df: DataFrame with vessel data
        cargo_demand_tonnes: Monthly demand
        min_safety: Minimum safety score
        scenario_config: Dict with scenario parameters
        require_all_fuel_types: Require all 8 fuel types

    Returns:
        Dict with metrics and selected vessels
    """
    df_scenario = df.copy()

    # Apply adjustments
    if scenario_config.get('congestion_hours', 0) > 0:
        df_scenario = add_port_congestion_fuel(
            df_scenario,
            congestion_hours=scenario_config['congestion_hours']
        )
        # Recalculate fuel and carbon costs
        # (simplified - in real implementation would recalc from fuel tonnes)

    if scenario_config.get('fuel_price_multiplier', 1.0) != 1.0:
        df_scenario = apply_fuel_price_multiplier(
            df_scenario,
            multiplier=scenario_config['fuel_price_multiplier']
        )

    if scenario_config.get('cii_enforcement', False):
        df_scenario = apply_cii_penalties(df_scenario)
        # Apply CII penalty to total cost
        df_scenario['total_cost_usd_pre_cii'] = df_scenario['total_cost_usd']
        df_scenario['total_cost_usd'] = df_scenario['total_cost_usd'] * df_scenario['CII_penalty_multiplier']

    # Select fleet
    try:
        selected = select_fleet_greedy(
            df_scenario,
            cargo_demand_tonnes=cargo_demand_tonnes,
            min_avg_safety=min_safety,
            require_all_fuel_types=require_all_fuel_types,
            cost_col='total_cost_usd',
        )

        metrics = total_cost_and_metrics(df_scenario, selected, cost_col='total_cost_usd')
        metrics['scenario_config'] = scenario_config

        # Add CII statistics if enforcement enabled
        if scenario_config.get('cii_enforcement', False):
            selected_df = df_scenario[df_scenario['vessel_id'].isin(selected)]
            metrics['avg_cii'] = selected_df['CII'].mean()
            metrics['cii_rating_distribution'] = selected_df['CII_rating'].value_counts().to_dict()

        return {
            'scenario_name': scenario_config.get('name', 'Unnamed'),
            'error': None,
            'metrics': metrics,
            'selected_vessel_ids': selected,
        }
    except Exception as e:
        return {
            'scenario_name': scenario_config.get('name', 'Unnamed'),
            'error': str(e),
            'metrics': None,
            'selected_vessel_ids': [],
        }


def run_comprehensive_sensitivity(
    df: pd.DataFrame,
    cargo_demand_tonnes: float,
    base_min_safety: float = 3.0,
    require_all_fuel_types: bool = True,
) -> dict[str, Any]:
    """
    Run all sensitivity analyses from methodology.

    Returns comprehensive results structure:
    {
        'base_case': {...},
        'safety_sensitivity': [...],
        'carbon_price_sensitivity': [...],
        'scenarios_2024': [...]
    }

    Args:
        df: DataFrame with vessel data
        cargo_demand_tonnes: Monthly demand
        base_min_safety: Base case minimum safety score
        require_all_fuel_types: Require all 8 fuel types

    Returns:
        Dict with all sensitivity results
    """
    results = {
        'base_case': None,
        'safety_sensitivity': [],
        'carbon_price_sensitivity': [],
        'scenarios_2024': [],
    }

    # 1. Base case
    try:
        selected_base = select_fleet_greedy(
            df,
            cargo_demand_tonnes=cargo_demand_tonnes,
            min_avg_safety=base_min_safety,
            require_all_fuel_types=require_all_fuel_types,
        )
        results['base_case'] = {
            'metrics': total_cost_and_metrics(df, selected_base),
            'selected_vessel_ids': selected_base,
        }
    except Exception as e:
        results['base_case'] = {'error': str(e)}

    # 2. Safety threshold sensitivity
    safety_thresholds = [2.5, 3.0, 3.5, 4.0, 4.5]
    for threshold in safety_thresholds:
        try:
            selected = select_fleet_greedy(
                df,
                cargo_demand_tonnes=cargo_demand_tonnes,
                min_avg_safety=threshold,
                require_all_fuel_types=require_all_fuel_types,
            )
            metrics = total_cost_and_metrics(df, selected)
            results['safety_sensitivity'].append({
                'threshold': threshold,
                'metrics': metrics,
                'selected_vessel_ids': selected,
                'error': None,
            })
        except Exception as e:
            results['safety_sensitivity'].append({
                'threshold': threshold,
                'error': str(e),
                'metrics': None,
            })

    # 3. Carbon price sensitivity
    carbon_prices = [80, 120, 160, 200]
    results['carbon_price_sensitivity'] = run_carbon_price_sensitivity(
        df,
        cargo_demand_tonnes,
        base_min_safety,
        carbon_prices,
        require_all_fuel_types,
    )

    # 4. 2024 scenarios
    scenarios_2024 = [
        {
            'name': 'Base (Idealised)',
            'fuel_price_multiplier': 1.00,
            'congestion_hours': 0,
            'cii_enforcement': False,
        },
        {
            'name': '2024 Typical',
            'fuel_price_multiplier': 1.05,
            'congestion_hours': 48,
            'cii_enforcement': True,
        },
        {
            'name': '2024 Stress',
            'fuel_price_multiplier': 1.10,
            'congestion_hours': 72,
            'cii_enforcement': True,
        },
    ]

    for scenario_config in scenarios_2024:
        result = run_2024_scenario(
            df,
            cargo_demand_tonnes,
            base_min_safety,
            scenario_config,
            require_all_fuel_types,
        )
        results['scenarios_2024'].append(result)

    return results


def format_sensitivity_summary(results: dict[str, Any]) -> str:
    """
    Generate text summary of all sensitivity analyses.

    Args:
        results: Output from run_comprehensive_sensitivity

    Returns:
        Formatted text summary
    """
    lines = ["=" * 80]
    lines.append("COMPREHENSIVE SENSITIVITY ANALYSIS RESULTS")
    lines.append("=" * 80)
    lines.append("")

    # Base case
    if results['base_case'] and 'metrics' in results['base_case']:
        m = results['base_case']['metrics']
        lines.append("BASE CASE:")
        lines.append(f"  Fleet size: {m['fleet_size']}")
        lines.append(f"  Total cost: ${m['total_cost_usd']:,.0f}")
        lines.append(f"  Avg safety: {m['avg_safety_score']:.2f}")
        lines.append(f"  Total CO2eq: {m['total_co2e_tonnes']:,.0f} tonnes")
        lines.append("")

    # Safety sensitivity
    lines.append("SAFETY THRESHOLD SENSITIVITY:")
    for r in results['safety_sensitivity']:
        if r.get('error'):
            lines.append(f"  Safety ≥ {r['threshold']}: INFEASIBLE - {r['error']}")
        else:
            m = r['metrics']
            lines.append(f"  Safety ≥ {r['threshold']}: "
                        f"Fleet {m['fleet_size']}, "
                        f"Cost ${m['total_cost_usd']:,.0f}, "
                        f"CO2eq {m['total_co2e_tonnes']:,.0f}t")
    lines.append("")

    # Carbon price sensitivity
    lines.append("CARBON PRICE SENSITIVITY:")
    for r in results['carbon_price_sensitivity']:
        if r.get('error'):
            lines.append(f"  ${r['carbon_price']}/tCO2eq: FAILED - {r['error']}")
        else:
            m = r['metrics']
            lines.append(f"  ${r['carbon_price']}/tCO2eq: "
                        f"Fleet {m['fleet_size']}, "
                        f"Cost ${m['total_cost_usd']:,.0f}, "
                        f"CO2eq {m['total_co2e_tonnes']:,.0f}t")
    lines.append("")

    # 2024 scenarios
    lines.append("2024 ROUTE-SPECIFIC SCENARIOS:")
    for r in results['scenarios_2024']:
        if r.get('error'):
            lines.append(f"  {r['scenario_name']}: FAILED - {r['error']}")
        else:
            m = r['metrics']
            lines.append(f"  {r['scenario_name']}:")
            lines.append(f"    Fleet size: {m['fleet_size']}, Cost: ${m['total_cost_usd']:,.0f}")
            lines.append(f"    CO2eq: {m['total_co2e_tonnes']:,.0f}t, Avg safety: {m['avg_safety_score']:.2f}")
            if 'avg_cii' in m:
                lines.append(f"    Avg CII: {m['avg_cii']:.1f} g CO2/tonne·NM")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)
