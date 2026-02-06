"""
Generate realistic seed data for testing sensitivity analysis.

Creates synthetic fleet based on methodology specifications:
- 108 vessels (matching real dataset size)
- 8 main engine fuel types
- DWT ranges from methodology (10k-260k tonnes)
- Safety scores 1-5 distribution
- Realistic cost structures
"""

import numpy as np
import pandas as pd
from typing import Any


# Fuel type distribution from methodology (Section 2.2)
FUEL_TYPES_DISTRIBUTION = {
    'DISTILLATE FUEL': 54,
    'LNG': 22,
    'Methanol': 11,
    'Ammonia': 8,
    'Ethanol': 5,
    'LPG (Butane)': 3,
    'LPG (Propane)': 3,
    'Hydrogen': 2,
}

# DWT ranges per fuel type (approximate from methodology)
DWT_RANGES = {
    'DISTILLATE FUEL': (14_226, 262_781),
    'LNG': (25_035, 261_089),
    'Methanol': (37_520, 210_102),
    'Ammonia': (106_507, 210_909),
    'Ethanol': (174_802, 207_939),
    'LPG (Butane)': (49_861, 210_909),
    'LPG (Propane)': (39_781, 206_118),
    'Hydrogen': (114_563, 178_838),
}

# Safety score distribution (from methodology Section 2.2)
SAFETY_DISTRIBUTION = {
    1: 17,
    2: 14,
    3: 31,
    4: 29,
    5: 17,
}

# Average safety by fuel type (from methodology Section 5.2)
# Boosted slightly to ensure feasible solutions
FUEL_SAFETY_MEANS = {
    'DISTILLATE FUEL': 3.0,  # Boosted from 2.6 for testing
    'LNG': 3.8,
    'Methanol': 3.4,  # Boosted from 3.2
    'Ammonia': 3.6,  # Boosted from 3.5
    'Ethanol': 3.6,  # Boosted from 3.4
    'LPG (Butane)': 4.5,
    'LPG (Propane)': 4.7,
    'Hydrogen': 4.0,  # Boosted from 3.8
}

# Emission factors from methodology Appendix A.1
EMISSION_FACTORS = {
    'DISTILLATE FUEL': {'CO2': 3.206, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 42.7},
    'Light Fuel Oil': {'CO2': 3.151, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 41.2},
    'Heavy Fuel Oil': {'CO2': 3.114, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 40.2},
    'LPG (Propane)': {'CO2': 3.000, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 46.3},
    'LPG (Butane)': {'CO2': 3.030, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 45.7},
    'LNG': {'CO2': 2.750, 'CH4': 0.00000, 'N2O': 0.00011, 'LCV': 48.0},
    'Methanol': {'CO2': 1.375, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 19.9},
    'Ethanol': {'CO2': 1.913, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 26.8},
    'Ammonia': {'CO2': 0.000, 'CH4': 0.00005, 'N2O': 0.00018, 'LCV': 18.6},
    'Hydrogen': {'CO2': 0.000, 'CH4': 0.00000, 'N2O': 0.00000, 'LCV': 120.0},
}

# Fuel prices from methodology Appendix A.2
FUEL_PRICES = {
    'DISTILLATE FUEL': 13,  # USD/GJ
    'LPG (Propane)': 15,
    'LPG (Butane)': 15,
    'LNG': 15,
    'Methanol': 54,
    'Ethanol': 54,
    'Ammonia': 40,
    'Hydrogen': 50,
}

# CAPEX base costs and multipliers (Methodology Appendix A.2)
CAPEX_BASE = {
    # DWT bracket: (min, max, cost_M)
    'brackets': [
        (10_000, 40_000, 35),
        (40_001, 55_000, 53),
        (55_001, 80_000, 80),
        (80_001, 120_000, 78),
        (120_001, 300_000, 90),
    ]
}

CAPEX_MULTIPLIERS = {
    'DISTILLATE FUEL': 1.0,
    'LPG (Propane)': 1.3,
    'LPG (Butane)': 1.35,
    'LNG': 1.4,
    'Methanol': 1.3,
    'Ethanol': 1.2,
    'Ammonia': 1.4,
    'Hydrogen': 1.1,
}

# Safety score adjustment rates (Methodology Appendix A.3)
SAFETY_ADJUSTMENT_RATES = {
    1: 0.10,   # +10%
    2: 0.05,   # +5%
    3: 0.00,   # 0%
    4: -0.02,  # -2%
    5: -0.05,  # -5%
}


def get_capex_base(dwt: float) -> float:
    """Get base CAPEX in millions USD based on DWT bracket."""
    for min_dwt, max_dwt, cost in CAPEX_BASE['brackets']:
        if min_dwt <= dwt <= max_dwt:
            return cost
    return 90  # Default for >120k


def generate_vessel_id(idx: int) -> int:
    """Generate realistic vessel ID (8 digits)."""
    return 10000000 + idx * 1000 + np.random.randint(0, 1000)


def generate_seed_fleet(n_vessels: int = 108, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic seed fleet data for testing.

    Args:
        n_vessels: Number of vessels (default 108 from methodology)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with vessel data ready for cost model
    """
    np.random.seed(seed)

    vessels = []

    # Distribute vessels by fuel type
    vessel_idx = 0
    for fuel_type, count in FUEL_TYPES_DISTRIBUTION.items():
        for _ in range(count):
            # Generate DWT within realistic range for fuel type
            dwt_min, dwt_max = DWT_RANGES[fuel_type]
            dwt = np.random.uniform(dwt_min, dwt_max)

            # Safety score with fuel-type bias
            mean_safety = FUEL_SAFETY_MEANS[fuel_type]
            # Use wider distribution to get more high-safety vessels
            safety_raw = np.random.normal(mean_safety, 1.2)
            safety = int(np.clip(np.round(safety_raw), 1, 5))

            # Main engine power (MEP) scales with DWT
            # Approximate: 10-20 kW per tonne DWT
            mep = dwt * np.random.uniform(10, 20) * 0.08  # 80% of max power

            # Reference speed (Vref) - typical 12-16 knots
            vref = np.random.uniform(12.5, 15.5)

            # Auxiliary engine load (AEL) - typically 5-10% of MEP
            ael = mep * np.random.uniform(0.05, 0.10)

            # Auxiliary boiler load (ABL) - typically 1-2% of MEP
            abl = mep * np.random.uniform(0.01, 0.02)

            # Specific Fuel Consumption (SFC) - g/kWh
            # ME: 165-180 g/kWh typical for modern engines
            sfc_me = np.random.uniform(165, 180)
            sfc_ae = np.random.uniform(195, 210)
            sfc_ab = np.random.uniform(290, 310)

            # CAPEX calculation
            base_capex = get_capex_base(dwt) * 1_000_000
            capex = base_capex * CAPEX_MULTIPLIERS[fuel_type]

            vessel = {
                'vessel_id': generate_vessel_id(vessel_idx),
                'vessel_name': f'VESSEL_{vessel_idx:03d}',
                'vessel_type': 'Chemical/Products Tanker',
                'dwt': int(dwt),
                'main_engine_fuel_type': fuel_type,
                'aux_engine_fuel_type': 'DISTILLATE FUEL',  # Always distillate
                'aux_boiler_fuel_type': 'DISTILLATE FUEL',  # Always distillate
                'safety_score': safety,
                'P': int(mep),  # Main engine power
                'vref': round(vref, 2),
                'ael': int(ael),
                'abl': int(abl),
                'sfc_me': round(sfc_me, 1),
                'sfc_ae': round(sfc_ae, 1),
                'sfc_ab': round(sfc_ab, 1),
                'capex_usd': capex,
            }

            vessels.append(vessel)
            vessel_idx += 1

    df = pd.DataFrame(vessels)

    # Calculate estimated voyage parameters (simplified)
    # Voyage distance: Singapore to West Australia ≈ 1762 NM
    # Voyage time at Vref: 1762 / Vref hours
    df['voyage_hours'] = 1762 / df['vref']

    return df


def generate_global_params() -> dict[str, Any]:
    """Generate global parameters for cost model."""
    return {
        'emission_factors': EMISSION_FACTORS,
        'price_usd_per_gj': FUEL_PRICES,
        'lcv_mj_per_kg': {k: v['LCV'] for k, v in EMISSION_FACTORS.items()},
        'carbon_price_usd_per_tco2e': 80,
        'crf': 0.088827,  # Capital Recovery Factor from methodology
        'safety_score_adjustment_rates': SAFETY_ADJUSTMENT_RATES,
        'voyage_nm': 1762,
        'ship_capex_usd': {},  # Will be filled from vessel data
    }


def compute_estimated_costs(df: pd.DataFrame, global_params: dict[str, Any]) -> pd.DataFrame:
    """
    Compute estimated costs using simplified model (matching cost_model.py logic).

    Args:
        df: Vessel dataframe
        global_params: Global parameters

    Returns:
        DataFrame with cost columns added
    """
    df = df.copy()

    # Load factors (simplified - from cost_model.py defaults)
    LF_ME = 0.8
    LF_AE = 0.5
    LF_AB = 0.3

    rows = []
    for _, row in df.iterrows():
        # Fuel consumption (tonnes)
        voyage_hours = row['voyage_hours']
        fuel_me = (row['P'] * LF_ME * voyage_hours * row['sfc_me']) / 1e6
        fuel_ae = (row['ael'] * LF_AE * voyage_hours * row['sfc_ae']) / 1e6
        fuel_ab = (row['abl'] * LF_AB * voyage_hours * row['sfc_ab']) / 1e6

        # Fuel cost (USD)
        me_fuel_type = row['main_engine_fuel_type']
        lcv_me = EMISSION_FACTORS[me_fuel_type]['LCV']
        price_me = FUEL_PRICES[me_fuel_type]
        lcv_dist = EMISSION_FACTORS['DISTILLATE FUEL']['LCV']
        price_dist = FUEL_PRICES['DISTILLATE FUEL']

        fuel_cost_me = (fuel_me * 1000 * lcv_me / 1000) * price_me
        fuel_cost_ae = (fuel_ae * 1000 * lcv_dist / 1000) * price_dist
        fuel_cost_ab = (fuel_ab * 1000 * lcv_dist / 1000) * price_dist
        fuel_cost_total = fuel_cost_me + fuel_cost_ae + fuel_cost_ab

        # Emissions (tonnes CO2eq)
        cf_me = EMISSION_FACTORS[me_fuel_type]
        cf_dist = EMISSION_FACTORS['DISTILLATE FUEL']

        # CO2eq using GWP: CO2 + 28*CH4 + 265*N2O (from methodology)
        co2eq_me = fuel_me * (cf_me['CO2'] + 28 * cf_me['CH4'] + 265 * cf_me['N2O'])
        co2eq_ae = fuel_ae * (cf_dist['CO2'] + 28 * cf_dist['CH4'] + 265 * cf_dist['N2O'])
        co2eq_ab = fuel_ab * (cf_dist['CO2'] + 28 * cf_dist['CH4'] + 265 * cf_dist['N2O'])
        co2eq_total = co2eq_me + co2eq_ae + co2eq_ab

        # Carbon cost
        carbon_cost = co2eq_total * global_params['carbon_price_usd_per_tco2e']

        # Ownership cost (monthly amortized)
        capex = row['capex_usd']
        crf = global_params['crf']
        ownership_cost = (capex * crf) / 12

        # Risk premium
        base_cost = fuel_cost_total + carbon_cost + ownership_cost
        safety_adj = SAFETY_ADJUSTMENT_RATES[row['safety_score']]
        risk_premium = base_cost * safety_adj

        # Total cost
        total_cost = base_cost + risk_premium

        row_dict = row.to_dict()
        row_dict.update({
            'fuel_me_tonnes': fuel_me,
            'fuel_ae_tonnes': fuel_ae,
            'fuel_ab_tonnes': fuel_ab,
            'fuel_tonnes': fuel_me + fuel_ae + fuel_ab,
            'fuel_cost_usd': fuel_cost_total,
            'co2e_tonnes': co2eq_total,
            'carbon_cost_usd': carbon_cost,
            'ownership_cost_usd': ownership_cost,
            'risk_premium_usd': risk_premium,
            'total_cost_usd': total_cost,
        })
        rows.append(row_dict)

    return pd.DataFrame(rows)


def save_seed_data(output_dir: str = 'data/seed') -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Generate and save seed data for testing.

    Args:
        output_dir: Directory to save seed data

    Returns:
        Tuple of (vessels dataframe, global_params dict)
    """
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate data
    df_vessels = generate_seed_fleet()
    global_params = generate_global_params()

    # Compute costs
    df_vessels = compute_estimated_costs(df_vessels, global_params)

    # Save
    df_vessels.to_csv(output_path / 'seed_vessels.csv', index=False)

    import json
    with open(output_path / 'seed_global_params.json', 'w') as f:
        json.dump(global_params, f, indent=2)

    print(f"Seed data saved to {output_path}")
    print(f"  Vessels: {len(df_vessels)}")
    print(f"  Total DWT: {df_vessels['dwt'].sum():,.0f} tonnes")
    print(f"  Fuel types: {df_vessels['main_engine_fuel_type'].nunique()}")
    print(f"  Safety scores: {sorted(df_vessels['safety_score'].unique())}")

    return df_vessels, global_params


if __name__ == '__main__':
    df, params = save_seed_data()
    print("\nSample vessels:")
    print(df[['vessel_id', 'dwt', 'main_engine_fuel_type', 'safety_score', 'total_cost_usd']].head(10))
