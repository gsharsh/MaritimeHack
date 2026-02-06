"""
Cost model per ship (single A→B voyage, one month scope).
1. Fuel cost (main + auxiliary engine + boiler)
2. Carbon cost (emissions from fuel consumption)
3. Amortized ownership cost per month
4. Risk premium (safety score adjustment)
"""

from typing import Any

import pandas as pd


def fuel_consumption_tonnes(
    row: pd.Series,
    voyage_hours: float,
    load_factors: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Compute fuel consumption (tonnes) for main engine, auxiliary engine, auxiliary boiler.
    Assumes power in kW, sfc in g/kWh, voyage_hours for trip duration.
    """
    if load_factors is None:
        load_factors = {"me": 0.8, "ae": 0.5, "ab": 0.3}
    me = (row["P"] * load_factors["me"] * voyage_hours * row["sfc_me"]) / 1e6  # g -> tonnes
    ae = (row["ael"] * load_factors["ae"] * voyage_hours * row["sfc_ae"]) / 1e6
    ab = (row["abl"] * load_factors["ab"] * voyage_hours * row["sfc_ab"]) / 1e6
    return {"fuel_me_tonnes": me, "fuel_ae_tonnes": ae, "fuel_ab_tonnes": ab}


def co2e_tonnes(
    fuel_tonnes: dict[str, float],
    emission_factors: dict[str, dict[str, float]],
    fuel_types: dict[str, str],
) -> float:
    """CO2 equivalent (tonnes) from fuel burn and emission factors (CO2, CH4, N2O)."""
    total = 0.0
    for key, tonnes in fuel_tonnes.items():
        if tonnes <= 0:
            continue
        ft = fuel_types.get(key, "default")
        cf = emission_factors.get(ft, emission_factors.get("default", {}))
        total += tonnes * (
            cf.get("CO2", 0) + cf.get("CH4", 0) * 25 + cf.get("N2O", 0) * 298
        )  # GWP approx
    return total


def fuel_cost_usd(
    fuel_tonnes: dict[str, float],
    fuel_types: dict[str, str],
    lcv_mj_per_kg: dict[str, float],
    price_usd_per_gj: dict[str, float],
) -> float:
    """Fuel cost in USD using LCV (MJ/kg) and price in USD/GJ."""
    cost = 0.0
    for key, tonnes in fuel_tonnes.items():
        if tonnes <= 0:
            continue
        ft = fuel_types.get(key, "default")
        lcv = lcv_mj_per_kg.get(ft, 40)  # MJ/kg
        price = price_usd_per_gj.get(ft, 0)
        # tonnes * 1000 kg * lcv MJ/kg = MJ; MJ/1000 = GJ
        gj = tonnes * 1000 * lcv / 1000
        cost += gj * price
    return cost


def amortized_ownership_per_month_usd(
    capex_usd: float,
    crf: float,
    n_years: int = 30,
) -> float:
    """Monthly amortized ownership (CAPEX * CRF / 12)."""
    return capex_usd * crf / 12


def risk_premium_usd(base_cost_component: float, safety_score: int, adjustment_rates: dict[int, float]) -> float:
    """Risk premium: positive = penalty (riskier), negative = reward (safer). Rate as decimal e.g. 0.05 = 5%."""
    rate = adjustment_rates.get(safety_score, 0.0)
    return base_cost_component * rate


def ship_total_cost_usd(
    row: pd.Series,
    global_params: dict[str, Any],
    voyage_hours: float,
) -> dict[str, float]:
    """
    Total cost for one ship for one A→B voyage (one month scope).
    Returns dict with fuel_cost, carbon_cost, ownership_cost, risk_premium, total.
    """
    fuel_tonnes = fuel_consumption_tonnes(row, voyage_hours)
    total_fuel_tonnes = sum(fuel_tonnes.values())

    fuel_types = {
        "fuel_me_tonnes": row.get("main_engine_fuel_type", "default"),
        "fuel_ae_tonnes": row.get("aux_engine_fuel_type", "default"),
        "fuel_ab_tonnes": row.get("aux_boiler_fuel_type", "default"),
    }
    fuel_cost = fuel_cost_usd(
        fuel_tonnes,
        fuel_types,
        global_params.get("lcv_mj_per_kg", {}),
        global_params.get("price_usd_per_gj", {}),
    )
    # If emission_factors is empty (e.g. global_params not loaded for seed data),
    # co2e_tonnes() returns 0 because cf.get("CO2", 0) etc. are all 0. Load
    # data/seed/seed_global_params.json when using seed ships to get non-zero CO2e.
    co2e = co2e_tonnes(
        fuel_tonnes,
        global_params.get("emission_factors", {}),
        fuel_types,
    )
    carbon_cost = co2e * global_params.get("carbon_price_usd_per_tco2e", 80)

    capex = global_params.get("ship_capex_usd", {}).get(str(row.get("vessel_id")), row.get("capex_usd", 0))
    crf = global_params.get("crf", 0.05)
    ownership = amortized_ownership_per_month_usd(capex, crf)

    base_for_risk = fuel_cost + carbon_cost + ownership
    safety = int(row.get("safety_score", 3))
    adjustment = global_params.get("safety_score_adjustment_rates", {}).get(safety, 0)
    risk_premium = base_for_risk * adjustment

    total = fuel_cost + carbon_cost + ownership + risk_premium
    return {
        "fuel_cost_usd": fuel_cost,
        "carbon_cost_usd": carbon_cost,
        "ownership_cost_usd": ownership,
        "risk_premium_usd": risk_premium,
        "total_cost_usd": total,
        "fuel_tonnes": total_fuel_tonnes,
        "co2e_tonnes": co2e,
    }
