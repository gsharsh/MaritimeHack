"""
SOP constants, lookup tables, and helper functions.

Single source of truth for all values from the SOP (Nickolas.md) and
calculation_factors.xlsx. Every constant references its SOP section.
"""

# ---------------------------------------------------------------------------
# 1. Monthly cargo demand (SOP Step 7.1)
#    54,920,000 tonnes annual / 12 months
# ---------------------------------------------------------------------------
MONTHLY_DEMAND: int = 4_576_667

# ---------------------------------------------------------------------------
# 2. Minimum average fleet safety score constraint (SOP Step 7)
# ---------------------------------------------------------------------------
SAFETY_THRESHOLD: float = 3.0

# ---------------------------------------------------------------------------
# 3. Carbon price USD per tonne CO2-equivalent (SOP Step 5)
# ---------------------------------------------------------------------------
CARBON_PRICE: int = 80

# ---------------------------------------------------------------------------
# 4. Capital Recovery Factor (SOP Step 6c.4)
#    CRF = i(1+i)^n / ((1+i)^n - 1), i=0.05, n=15 => 0.088827
# ---------------------------------------------------------------------------
CRF: float = 0.088827

# ---------------------------------------------------------------------------
# 5. Salvage rate (SOP Step 6c)
#    S = 10% of ship cost
# ---------------------------------------------------------------------------
SALVAGE_RATE: float = 0.10

# ---------------------------------------------------------------------------
# 6. Discount rate / required return on salvage (SOP Step 6c)
#    r = 8%
# ---------------------------------------------------------------------------
DISCOUNT_RATE: float = 0.08

# ---------------------------------------------------------------------------
# 7. Fuel types as they appear in the CSV (SOP Step 2)
# ---------------------------------------------------------------------------
FUEL_TYPES: list[str] = [
    "DISTILLATE FUEL",
    "LNG",
    "Methanol",
    "Ethanol",
    "Ammonia",
    "Hydrogen",
    "LPG (Propane)",
    "LPG (Butane)",
]

# ---------------------------------------------------------------------------
# 8. Mapping from CSV fuel-type strings to Cf-sheet / lookup-table keys
#    (SOP Step 2)
# ---------------------------------------------------------------------------
FUEL_TYPE_MAP: dict[str, str] = {
    "DISTILLATE FUEL": "Distillate fuel",
    "LNG": "LNG",
    "Methanol": "Methanol",
    "Ethanol": "Ethanol",
    "Ammonia": "Ammonia",
    "Hydrogen": "Hydrogen",
    "LPG (Propane)": "LPG (Propane)",
    "LPG (Butane)": "LPG (Butane)",
}

# ---------------------------------------------------------------------------
# 9. Cf emission factors from calculation_factors.xlsx "Cf" sheet
#    Keys: CO2 (g CO2 / g fuel), CH4, N2O, LCV (MJ/kg)
#    (SOP Step 5a-5b)
# ---------------------------------------------------------------------------
CF_EMISSION_FACTORS: dict[str, dict[str, float]] = {
    "Distillate fuel": {"CO2": 3.206, "CH4": 0.00005, "N2O": 0.00018, "LCV": 42.7},
    "Light Fuel Oil":  {"CO2": 3.151, "CH4": 0.00005, "N2O": 0.00018, "LCV": 41.2},
    "Heavy Fuel Oil":  {"CO2": 3.114, "CH4": 0.00005, "N2O": 0.00018, "LCV": 40.2},
    "LPG (Propane)":   {"CO2": 3.000, "CH4": 0.00005, "N2O": 0.00018, "LCV": 46.3},
    "LPG (Butane)":    {"CO2": 3.030, "CH4": 0.00005, "N2O": 0.00018, "LCV": 45.7},
    "LNG":             {"CO2": 2.750, "CH4": 0.00000, "N2O": 0.00011, "LCV": 48.0},
    "Methanol":        {"CO2": 1.375, "CH4": 0.00005, "N2O": 0.00018, "LCV": 19.9},
    "Ethanol":         {"CO2": 1.913, "CH4": 0.00005, "N2O": 0.00018, "LCV": 26.8},
    "Ammonia":         {"CO2": 0.000, "CH4": 0.00005, "N2O": 0.00018, "LCV": 18.6},
    "Hydrogen":        {"CO2": 0.000, "CH4": 0.00000, "N2O": 0.00000, "LCV": 120.0},
}

# ---------------------------------------------------------------------------
# 10. Lower Calorific Value (MJ/kg) — derived from CF_EMISSION_FACTORS
#     (SOP Step 4)
# ---------------------------------------------------------------------------
LCV_MJ_PER_KG: dict[str, float] = {
    fuel: vals["LCV"] for fuel, vals in CF_EMISSION_FACTORS.items()
}

# ---------------------------------------------------------------------------
# 11. Fuel price in USD per GJ (SOP Step 4)
# ---------------------------------------------------------------------------
FUEL_PRICE_USD_PER_GJ: dict[str, float] = {
    "Distillate fuel": 13,
    "LPG (Propane)": 15,
    "LPG (Butane)": 15,
    "LNG": 15,
    "Methanol": 54,
    "Ethanol": 54,
    "Ammonia": 40,
    "Hydrogen": 50,
}

# ---------------------------------------------------------------------------
# 12. Fuel price in USD per tonne — precomputed: price_per_gj * LCV
#     (SOP Step 4, e.g. Distillate = 13 * 42.7 = 555.10)
# ---------------------------------------------------------------------------
FUEL_PRICE_USD_PER_TONNE: dict[str, float] = {
    fuel: FUEL_PRICE_USD_PER_GJ[fuel] * LCV_MJ_PER_KG[fuel]
    for fuel in FUEL_PRICE_USD_PER_GJ
}

# ---------------------------------------------------------------------------
# 13. CAPEX base cost brackets (millions USD) by DWT range
#     (SOP Step 6c.1)
#     Tuple: (lower_dwt, upper_dwt, base_cost_millions)
#     First bracket: 10,000 <= DWT <= 40,000 (inclusive both ends)
#     Others: lower < DWT <= upper
#     Last bracket: DWT > 120,000
# ---------------------------------------------------------------------------
CAPEX_BASE_COST_M: list[tuple[int, float, int]] = [
    (10_000,  40_000,        35),
    (40_000,  55_000,        53),
    (55_000,  80_000,        80),
    (80_000,  120_000,       78),
    (120_000, float("inf"),  90),
]

# ---------------------------------------------------------------------------
# 14. CAPEX fuel-type multiplier (SOP Step 6c.2)
# ---------------------------------------------------------------------------
CAPEX_FUEL_MULTIPLIER: dict[str, float] = {
    "Distillate fuel": 1.0,
    "LPG (Propane)": 1.3,
    "LPG (Butane)": 1.35,
    "LNG": 1.4,
    "Methanol": 1.3,
    "Ethanol": 1.2,
    "Ammonia": 1.4,
    "Hydrogen": 1.1,
}

# ---------------------------------------------------------------------------
# 15. Safety score adjustment rates (SOP Step 6d)
#     Positive = surcharge (riskier), negative = discount (safer)
# ---------------------------------------------------------------------------
SAFETY_ADJUSTMENT_RATES: dict[int, float] = {
    1:  0.10,
    2:  0.05,
    3:  0.00,
    4: -0.02,
    5: -0.05,
}

# ---------------------------------------------------------------------------
# 16. Global Warming Potentials (SOP Step 5c)
#     CH4 = 28 (NOT 25), N2O = 265 (NOT 298)
# ---------------------------------------------------------------------------
GWP: dict[str, int] = {
    "CH4": 28,
    "N2O": 265,
}

# ---------------------------------------------------------------------------
# 17. Low-Load Adjustment Factor table (SOP Step 5d)
#     Keyed by integer engine load percent (2-19).
#     Load >= 20% => all factors = 1.0
# ---------------------------------------------------------------------------
LLAF_TABLE: dict[int, dict[str, float]] = {
    2:  {"CO2": 3.28, "N2O": 4.63, "CH4": 21.18},
    3:  {"CO2": 2.44, "N2O": 2.92, "CH4": 11.68},
    4:  {"CO2": 2.01, "N2O": 2.21, "CH4": 7.71},
    5:  {"CO2": 1.76, "N2O": 1.83, "CH4": 5.61},
    6:  {"CO2": 1.59, "N2O": 1.60, "CH4": 4.35},
    7:  {"CO2": 1.47, "N2O": 1.45, "CH4": 3.52},
    8:  {"CO2": 1.38, "N2O": 1.35, "CH4": 2.95},
    9:  {"CO2": 1.31, "N2O": 1.27, "CH4": 2.52},
    10: {"CO2": 1.25, "N2O": 1.22, "CH4": 2.20},
    11: {"CO2": 1.21, "N2O": 1.17, "CH4": 1.96},
    12: {"CO2": 1.17, "N2O": 1.14, "CH4": 1.76},
    13: {"CO2": 1.14, "N2O": 1.11, "CH4": 1.60},
    14: {"CO2": 1.11, "N2O": 1.08, "CH4": 1.47},
    15: {"CO2": 1.08, "N2O": 1.06, "CH4": 1.36},
    16: {"CO2": 1.06, "N2O": 1.05, "CH4": 1.26},
    17: {"CO2": 1.04, "N2O": 1.03, "CH4": 1.18},
    18: {"CO2": 1.03, "N2O": 1.02, "CH4": 1.11},
    19: {"CO2": 1.01, "N2O": 1.01, "CH4": 1.05},
}


# ============================= Helper functions ============================


def get_base_capex_millions(dwt: int) -> float:
    """
    Look up base CAPEX (millions USD) by DWT bracket (SOP Step 6c.1).

    First bracket: 10,000 <= DWT <= 40,000 (inclusive both ends).
    Others: lower < DWT <= upper.
    Last bracket: DWT > 120,000.
    """
    for i, (lower, upper, cost) in enumerate(CAPEX_BASE_COST_M):
        if i == 0:
            # First bracket: inclusive both ends
            if lower <= dwt <= upper:
                return float(cost)
        else:
            if lower < dwt <= upper:
                return float(cost)
    raise ValueError(f"DWT {dwt} out of range for CAPEX brackets")


def get_capex_multiplier(fuel_type_csv: str) -> float:
    """
    Get CAPEX fuel-type multiplier (SOP Step 6c.2).

    Maps the CSV fuel-type string (e.g. 'DISTILLATE FUEL') through
    FUEL_TYPE_MAP to the Cf-sheet key, then looks up CAPEX_FUEL_MULTIPLIER.
    """
    cf_key = FUEL_TYPE_MAP.get(fuel_type_csv, fuel_type_csv)
    return CAPEX_FUEL_MULTIPLIER[cf_key]


def get_monthly_capex(dwt: int, fuel_type_csv: str) -> float:
    """
    Full monthly CAPEX calculation (SOP Step 6c).

    ship_cost = base_capex_millions * fuel_multiplier * 1,000,000
    S = SALVAGE_RATE * ship_cost
    annual = ((ship_cost - S) * CRF) + (DISCOUNT_RATE * S)
    monthly = annual / 12
    """
    ship_cost = get_base_capex_millions(dwt) * get_capex_multiplier(fuel_type_csv) * 1_000_000
    s = SALVAGE_RATE * ship_cost
    annual = ((ship_cost - s) * CRF) + (DISCOUNT_RATE * s)
    return annual / 12
