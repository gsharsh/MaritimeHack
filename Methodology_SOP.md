# Maritime Hackathon 2026 — Calculation SOP

## Standard Operating Procedure: From Raw AIS Data to Optimal Fleet Selection

**Purpose:** This document is a step-by-step instruction manual. Follow every step in order. Every formula, column name, file reference, and lookup value is specified exactly. Two worked examples are threaded through so you can verify your calculations at each stage.

---

## FILES YOU NEED

| File | What It Contains |
|---|---|
| `vessel_movements_dataset.csv` | 13,216 AIS rows across 108 vessels (23 columns) |
| `calculation_factors.xlsx` | 5 sheets: `Cf`, `Fuel cost`, `Cost of Carbon`, `Cost of ship`, `Safety score adjustment` |
| `llaf_table.csv` | Low Load Adjustment Factor lookup (19 rows × 9 columns) |

---

## COLUMN REFERENCE — vessel_movements_dataset.csv

| # | Column Name | Type | Description |
|---|---|---|---|
| 1 | `vessel_id` | int | Unique vessel identifier |
| 2 | `vessel_type_new` | str | Always "Chemical/Products Tanker" |
| 3 | `timestamp` | str | UTC datetime string, format `YYYY/MM/DD HH:MM:SS+00` |
| 4 | `timestamp_epoch` | int | Unix epoch seconds — **USE THIS for time calculations** |
| 5 | `latitude` | float | Decimal degrees |
| 6 | `longitude` | float | Decimal degrees |
| 7 | `speed_knots` | float | GPS-derived speed in knots |
| 8 | `in_anchorage` | str/NaN | Either `"anchorage"` or NaN (empty) |
| 9 | `in_port_boundary` | str/NaN | Either `"Singapore"`, `"Port Hedland"`, or NaN (empty) |
| 10 | `safety_score` | int | 1–5 (1 = riskiest, 5 = safest) |
| 11 | `dwt` | int | Deadweight tonnage |
| 12 | `fuel_category` | int | Always 2 in this dataset (ignore) |
| 13 | `main_engine_fuel_type` | str | One of 8 fuel types (see below) |
| 14 | `aux_engine_fuel_type` | str | **Always "DISTILLATE FUEL"** |
| 15 | `boil_engine_fuel_type` | str | **Always "DISTILLATE FUEL"** |
| 16 | `engine_type` | str | "SSD" or "LNG-Diesel" (not used in calculations) |
| 17 | `mep` | int | Main Engine Power in **kW** |
| 18 | `vref` | float | Reference/design speed in **knots** |
| 19 | `sfc_me` | float | Main Engine Specific Fuel Consumption in **g/kWh** (Distillate baseline) |
| 20 | `sfc_ae` | float | Aux Engine SFC in **g/kWh** |
| 21 | `sfc_ab` | float | Aux Boiler SFC in **g/kWh** |
| 22 | `ael` | int | Aux Engine Load in **kW** |
| 23 | `abl` | int | Aux Boiler Load in **kW** (can be 0) |

**Note:** Columns 10–23 are static per vessel (same value in every row for a given `vessel_id`). Columns 1–9 vary per AIS timestamp.

---

## TABLE REFERENCE — calculation_factors.xlsx

### Sheet: "Cf" — Emission Factors & Lower Calorific Values

| Fuel Type | LCV (MJ/kg) | Cf_CO2 | Cf_CH4 | Cf_N2O |
|---|---|---|---|---|
| Distillate fuel | 42.7 | 3.206 | 0.00005 | 0.00018 |
| Light Fuel Oil | 41.2 | 3.151 | 0.00005 | 0.00018 |
| Heavy Fuel Oil | 40.2 | 3.114 | 0.00005 | 0.00018 |
| LPG (Propane) | 46.3 | 3.000 | 0.00005 | 0.00018 |
| LPG (Butane) | 45.7 | 3.030 | 0.00005 | 0.00018 |
| LNG | 48.0 | 2.750 | 0.00000 | 0.00011 |
| Methanol | 19.9 | 1.375 | 0.00005 | 0.00018 |
| Ethanol | 26.8 | 1.913 | 0.00005 | 0.00018 |
| Ammonia | 18.6 | 0.000 | 0.00005 | 0.00018 |
| Hydrogen | 120.0 | 0.000 | 0.00000 | 0.00000 |

**How to use this sheet:** You will look up values by matching the `main_engine_fuel_type` (or `aux_engine_fuel_type` / `boil_engine_fuel_type`) column from the CSV against the "Fuel Type" column here. Match must be exact string (e.g., the CSV says `"DISTILLATE FUEL"` in uppercase — map this to `"Distillate fuel"` in this sheet).

**String mapping needed:**

| CSV value | Cf sheet value |
|---|---|
| `DISTILLATE FUEL` | `Distillate fuel` |
| `LNG` | `LNG` |
| `Methanol` | `Methanol` |
| `Ethanol` | `Ethanol` |
| `Ammonia` | `Ammonia` |
| `Hydrogen` | `Hydrogen` |
| `LPG (Propane)` | `LPG (Propane)` |
| `LPG (Butane)` | `LPG (Butane)` |

### Sheet: "Fuel cost" — Fuel Prices

| Fuel Type | Cost per GJ (USD) | LCV (MJ/kg) |
|---|---|---|
| Distillate fuel | 13 | 42.7 |
| LPG (Propane) | 15 | 46.3 |
| LPG (Butane) | 15 | 45.7 |
| LNG | 15 | 48 |
| Methanol | 54 | 19.9 |
| Ethanol | 54 | 26.8 |
| Ammonia | 40 | 18.6 |
| Hydrogen | 50 | 120 |

### Sheet: "Cost of Carbon"

| | Carbon cost per ton (USD) |
|---|---|
| (As of 2024) | **80** |

### Sheet: "Cost of ship" — CAPEX by DWT Bracket

**Base costs (Distillate fuel, in million USD):**

| DWT Bracket | Condition | Cost ($M) |
|---|---|---|
| 10–40k DWT | 10,000 ≤ DWT ≤ 40,000 | 35 |
| 40–55k DWT | 40,000 < DWT ≤ 55,000 | 53 |
| 55–80k DWT | 55,000 < DWT ≤ 80,000 | 80 |
| 80–120k DWT | 80,000 < DWT ≤ 120,000 | 78 |
| >120k DWT | DWT > 120,000 | 90 |

**⚠️ Bracket boundaries:** The hint in the methodology doc says "40-55k DWT means: 40,000 < DWT ≤ 55,000". The lower bound is **exclusive**, the upper bound is **inclusive**. Apply this pattern to all brackets.

**Multiplier factors (M) by fuel type:** Applied uniformly across all DWT brackets.

| Fuel Type | M |
|---|---|
| Distillate fuel | 1.0 (use base cost directly) |
| LPG (Propane) | 1.3 |
| LPG (Butane) | 1.35 |
| LNG | 1.4 |
| Methanol | 1.3 |
| Ethanol | 1.2 |
| Ammonia | 1.4 |
| Hydrogen | 1.1 |

### Sheet: "Safety score adjustment"

| Safety Score | Adjustment Rate |
|---|---|
| 1 | +10% (riskier → increased cost) |
| 2 | +5% |
| 3 | 0% |
| 4 | −2% (safer → reduced cost) |
| 5 | −5% |

---

## TABLE REFERENCE — llaf_table.csv

The LLAF table has columns: `Load`, `NOx`, `HC`, `CO`, `PM`, `SO2`, `CO2`, `N2O`, `CH4`.

**You only need columns: `Load`, `CO2`, `N2O`, `CH4`.**

| Load (%) | CO2 | N2O | CH4 |
|---|---|---|---|
| 2% | 3.28 | 4.63 | 21.18 |
| 3% | 2.44 | 2.92 | 11.68 |
| 4% | 2.01 | 2.21 | 7.71 |
| 5% | 1.76 | 1.83 | 5.61 |
| 6% | 1.59 | 1.60 | 4.35 |
| 7% | 1.47 | 1.45 | 3.52 |
| 8% | 1.38 | 1.35 | 2.95 |
| 9% | 1.31 | 1.27 | 2.52 |
| 10% | 1.25 | 1.22 | 2.20 |
| 11% | 1.21 | 1.17 | 1.96 |
| 12% | 1.17 | 1.14 | 1.76 |
| 13% | 1.14 | 1.11 | 1.60 |
| 14% | 1.11 | 1.08 | 1.47 |
| 15% | 1.08 | 1.06 | 1.36 |
| 16% | 1.06 | 1.05 | 1.26 |
| 17% | 1.04 | 1.03 | 1.18 |
| 18% | 1.03 | 1.02 | 1.11 |
| 19% | 1.01 | 1.01 | 1.05 |
| ≥20% | 1.00 | 1.00 | 1.00 |

---

## WORKED EXAMPLES — Two Ships We'll Track Through Every Step

We will compute values for two vessels at every stage so you can verify your code.

| | Ship A (Distillate) | Ship B (Ammonia) |
|---|---|---|
| `vessel_id` | 10102950 | 10657280 |
| `dwt` | 175,108 | 206,331 |
| `safety_score` | 1 | 3 |
| `main_engine_fuel_type` | DISTILLATE FUEL | Ammonia |
| `aux_engine_fuel_type` | DISTILLATE FUEL | DISTILLATE FUEL |
| `boil_engine_fuel_type` | DISTILLATE FUEL | DISTILLATE FUEL |
| `mep` | 16,860 kW | 18,630 kW |
| `vref` | 14.62 kn | 14.97 kn |
| `sfc_me` | 171.4 g/kWh | 169.1 g/kWh |
| `sfc_ae` | 199.3 g/kWh | 200.5 g/kWh |
| `sfc_ab` | 300 g/kWh | 300 g/kWh |
| `ael` | 1,029 kW | 1,094 kW |
| `abl` | 165 kW | 175 kW |

---

## STEP 0: LOAD AND CLEAN DATA

### 0.1 Read the CSV

```python
import pandas as pd

df = pd.read_csv('vessel_movements_dataset.csv')
# Drop empty trailing columns (the CSV has trailing commas)
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
```

### 0.2 Sort by vessel then time

```python
df = df.sort_values(['vessel_id', 'timestamp_epoch']).reset_index(drop=True)
```

You should have **13,216 rows** and **23 columns** and **108 unique vessel_ids**.

---

## STEP 1: CLASSIFY OPERATING MODE

**For each row**, assign a mode based on these exact rules, evaluated in this order:

```
IF   in_anchorage == "anchorage"  AND  speed_knots < 1    →  "Anchorage"
ELIF in_port_boundary is not NaN  AND  speed_knots > 1    →  "Maneuver"
ELIF in_port_boundary is NaN      AND  speed_knots >= 1   →  "Transit"
ELSE                                                       →  "Drifting"
```

**Where to find the values:**
- `in_anchorage` → column 8 (string `"anchorage"` or NaN)
- `in_port_boundary` → column 9 (string `"Singapore"` or `"Port Hedland"` or NaN)
- `speed_knots` → column 7

**Python implementation:**

```python
def classify_mode(row):
    if row['in_anchorage'] == 'anchorage' and row['speed_knots'] < 1:
        return 'Anchorage'
    elif pd.notna(row['in_port_boundary']) and row['speed_knots'] > 1:
        return 'Maneuver'
    elif pd.isna(row['in_port_boundary']) and row['speed_knots'] >= 1:
        return 'Transit'
    else:
        return 'Drifting'

df['mode'] = df.apply(classify_mode, axis=1)
```

**Expected counts (approximate):**
- Transit: ~12,178 rows
- Maneuver: ~562 rows
- Anchorage: ~377 rows
- Drifting: ~99 rows

**⚠️ IMPORTANT: Only Transit and Maneuver rows are used in fuel & emission calculations. Filter to these two modes for all subsequent steps.**

```python
df_active = df[df['mode'].isin(['Transit', 'Maneuver'])].copy()
```

---

## STEP 2: CALCULATE ACTIVITY HOURS (A)

**Definition:** For each row, A is the time difference (in hours) between this row's timestamp and the **next** row's timestamp for the **same vessel**.

**Where to find the values:**
- `timestamp_epoch` → column 4 (Unix epoch in seconds)
- `vessel_id` → column 1

**Formula:**

```
A_hours = (timestamp_epoch_next_row − timestamp_epoch_this_row) / 3600
```

**Python implementation:**

```python
df_active['A_hours'] = df_active.groupby('vessel_id')['timestamp_epoch'].diff(-1).abs() / 3600
```

**Edge cases:**
1. **Last row per vessel:** `diff(-1)` produces NaN for the last row. Set `A_hours = 0` for these.
2. **Gap cap:** If `A_hours > 6.0`, cap it to `6.0`. This handles data gaps where AIS transmission was lost.

```python
df_active['A_hours'] = df_active['A_hours'].fillna(0)
df_active['A_hours'] = df_active['A_hours'].clip(upper=6.0)
```

**Worked example — Ship A (10102950):**

First transit row has `timestamp_epoch` = 1736791265, next row = 1736794865.
```
A = (1736794865 − 1736791265) / 3600 = 3600 / 3600 = 1.0 hours ✓
```

**Expected totals per vessel (approximate):**
- Ship A (10102950): Transit hours ≈ 194.5, Maneuver hours ≈ 14.0
- Ship B (10657280): Transit hours ≈ 132.9, Maneuver hours ≈ 6.0

---

## STEP 3a: CALCULATE MAXIMUM SPEED (MS)

**Formula:**

```
MS = 1.066 × vref
```

**Where to find the values:**
- `vref` → column 18 of the CSV (knots)
- `1.066` → this is a constant from the methodology document (MS/Vref ratio)

This is a **per-vessel constant** (same for every row of the same vessel).

**Worked examples:**
- Ship A: MS = 1.066 × 14.62 = **15.58 knots**
- Ship B: MS = 1.066 × 14.97 = **15.96 knots**

---

## STEP 3b: CALCULATE ENGINE LOAD FACTOR (LF)

**Formula:**

```
LF = round( min( (speed_knots / MS)³, 1.0 ), 2)
```

**Where to find the values:**
- `speed_knots` → column 7 (varies per row)
- `MS` → computed in Step 3a

**Rules:**
1. Compute raw LF = (speed_knots / MS)³
2. Cap at 1.0: if LF > 1.0, set LF = 1.0
3. Round to 2 decimal places (standard rounding: 0.005 → 0.01)
4. Floor at 0.02 for active modes: if LF < 0.02 AND mode is Transit or Maneuver, set LF = 0.02

**Python implementation:**

```python
df_active['MS'] = 1.066 * df_active['vref']
df_active['LF'] = ((df_active['speed_knots'] / df_active['MS']) ** 3).clip(upper=1.0).round(2)
df_active.loc[df_active['LF'] < 0.02, 'LF'] = 0.02
```

**Worked example — Ship A, a transit row with speed_knots = 8.87:**
```
MS = 15.58
LF = (8.87 / 15.58)³ = (0.5693)³ = 0.1845
LF rounded = 0.18
LF ≥ 0.02, so no floor applied → LF = 0.18
```

**Worked example — Ship B, a transit row with speed_knots = 11.19:**
```
MS = 15.96
LF = (11.19 / 15.96)³ = (0.7011)³ = 0.3447
LF rounded = 0.34
→ LF = 0.34
```

**Expected fleet-wide range:** LF from 0.02 to 1.00, median around 0.50 for transit rows.

---

## STEP 4a: CALCULATE ADJUSTED SFC FOR EACH MACHINERY

**Formula (applied per machinery):**

```
sfc_adjusted_xy = sfc_xy × (42.7 / LCV_of_fuel_burned_by_xy)
```

**Where to find the values:**
- `sfc_me` → column 19 of CSV
- `sfc_ae` → column 20 of CSV
- `sfc_ab` → column 21 of CSV
- LCV → look up from `calculation_factors.xlsx`, sheet `"Cf"`, column `"LCV (MJ/kg)"`
- Match using: `main_engine_fuel_type` (column 13) for ME; `aux_engine_fuel_type` (column 14) for AE; `boil_engine_fuel_type` (column 15) for AB
- `42.7` → this is the Distillate LCV (the baseline fuel the dataset SFC values are calibrated to)

**Critical insight:** Since `aux_engine_fuel_type` and `boil_engine_fuel_type` are ALWAYS `"DISTILLATE FUEL"` in this dataset, their LCV is always 42.7, so:
- `sfc_adjusted_ae = sfc_ae × (42.7 / 42.7) = sfc_ae` → **NO CHANGE**
- `sfc_adjusted_ab = sfc_ab × (42.7 / 42.7) = sfc_ab` → **NO CHANGE**
- Only `sfc_adjusted_me` changes for non-Distillate ships.

**Pre-computed adjustment ratios (42.7 / LCV):**

| main_engine_fuel_type | LCV | 42.7 / LCV | What happens to sfc_me |
|---|---|---|---|
| DISTILLATE FUEL | 42.7 | 1.000 | No change |
| LNG | 48.0 | 0.890 | Decreases 11% |
| LPG (Propane) | 46.3 | 0.922 | Decreases 8% |
| LPG (Butane) | 45.7 | 0.934 | Decreases 7% |
| Ethanol | 26.8 | 1.593 | Increases 59% |
| Methanol | 19.9 | 2.146 | Increases 115% |
| Ammonia | 18.6 | 2.296 | Increases 130% |
| Hydrogen | 120.0 | 0.356 | Decreases 64% |

**Worked example — Ship A (Distillate):**
```
LCV_ME = 42.7 (Distillate)
sfc_adjusted_me = 171.4 × (42.7 / 42.7) = 171.4 g/kWh  (no change)
sfc_adjusted_ae = 199.3 × (42.7 / 42.7) = 199.3 g/kWh  (no change)
sfc_adjusted_ab = 300.0 × (42.7 / 42.7) = 300.0 g/kWh  (no change)
```

**Worked example — Ship B (Ammonia):**
```
LCV_ME = 18.6 (Ammonia, from Cf sheet)
sfc_adjusted_me = 169.1 × (42.7 / 18.6) = 169.1 × 2.2957 = 388.2 g/kWh  ← BIG INCREASE
sfc_adjusted_ae = 200.5 × (42.7 / 42.7) = 200.5 g/kWh  (no change — AE burns Distillate)
sfc_adjusted_ab = 300.0 × (42.7 / 42.7) = 300.0 g/kWh  (no change — AB burns Distillate)
```

**Python implementation:**

```python
# Build LCV lookup from Cf sheet
lcv_map = {
    'DISTILLATE FUEL': 42.7, 'LNG': 48.0, 'Methanol': 19.9,
    'Ethanol': 26.8, 'Ammonia': 18.6, 'Hydrogen': 120.0,
    'LPG (Propane)': 46.3, 'LPG (Butane)': 45.7
}

df_active['lcv_me'] = df_active['main_engine_fuel_type'].map(lcv_map)
df_active['sfc_adjusted_me'] = df_active['sfc_me'] * (42.7 / df_active['lcv_me'])
df_active['sfc_adjusted_ae'] = df_active['sfc_ae']   # Always Distillate → no change
df_active['sfc_adjusted_ab'] = df_active['sfc_ab']   # Always Distillate → no change
```

---

## STEP 4b: CALCULATE FUEL CONSUMPTION (tonnes) PER ROW

**Formulas:**

```
FC_me = (LF × mep × sfc_adjusted_me × A_hours) / 1,000,000
FC_ae = (ael × sfc_adjusted_ae × A_hours)        / 1,000,000
FC_ab = (abl × sfc_adjusted_ab × A_hours)        / 1,000,000
```

**Where to find the values:**
- `LF` → computed in Step 3b (dimensionless, per row)
- `mep` → column 17 (kW, static per vessel)
- `sfc_adjusted_me/ae/ab` → computed in Step 4a (g/kWh)
- `A_hours` → computed in Step 2 (hours, per row)
- `ael` → column 22 (kW, static per vessel)
- `abl` → column 23 (kW, static per vessel — can be 0)
- `1,000,000` → unit conversion: kW × g/kWh × hours = grams → divide by 10⁶ to get tonnes

**Key difference:** ME consumption depends on `LF` (speed-dependent). AE and AB are constant-load (they run at a fixed power output regardless of ship speed).

**Worked example — Ship B (Ammonia), one transit row where speed=11.19, LF=0.34, A=0.95 hrs:**
```
FC_me = (0.34 × 18630 × 388.2 × 0.95) / 1,000,000
      = (0.34 × 18630 × 388.2 × 0.95) / 1,000,000
      = (2,337,009.6) / 1,000,000
      ≈ 2.337 tonnes

FC_ae = (1094 × 200.5 × 0.95) / 1,000,000
      = (208,231.3) / 1,000,000
      ≈ 0.208 tonnes

FC_ab = (175 × 300 × 0.95) / 1,000,000
      = (49,875) / 1,000,000
      ≈ 0.050 tonnes
```

**Python implementation:**

```python
df_active['FC_me'] = (df_active['LF'] * df_active['mep'] * df_active['sfc_adjusted_me'] * df_active['A_hours']) / 1_000_000
df_active['FC_ae'] = (df_active['ael'] * df_active['sfc_adjusted_ae'] * df_active['A_hours']) / 1_000_000
df_active['FC_ab'] = (df_active['abl'] * df_active['sfc_adjusted_ab'] * df_active['A_hours']) / 1_000_000
```

**Expected per-vessel totals (sum across all rows for one vessel):**

| | Ship A (10102950) | Ship B (10657280) |
|---|---|---|
| FC_me total | ≈ 118.20 tonnes | ≈ 409.13 tonnes |
| FC_ae total | ≈ 42.76 tonnes | ≈ 30.46 tonnes |
| FC_ab total | ≈ 10.32 tonnes | ≈ 7.29 tonnes |
| FC_total | ≈ 171.28 tonnes | ≈ 446.88 tonnes |

Ship B burns far more ME fuel because Ammonia's low LCV means the SFC adjustment is 2.3×.

---

## STEP 5a: LOOK UP LOW LOAD ADJUSTMENT FACTOR (LLAF)

**Purpose:** LLAF inflates emissions at low engine loads where combustion is incomplete. It is a **per-row multiplier** with separate values for CO₂, N₂O, and CH₄.

**Procedure for each row:**

1. Take the `LF` value from Step 3b
2. Convert to percentage: `pct_LF = LF × 100`
3. Round `pct_LF` to nearest integer (standard rounding: 0.5 rounds up)
4. If `pct_LF < 2` AND mode is Transit or Maneuver → set `pct_LF = 2`
5. If `pct_LF >= 20` → LLAF_CO2 = 1.0, LLAF_N2O = 1.0, LLAF_CH4 = 1.0
6. Otherwise → look up the `llaf_table.csv` at the row matching `pct_LF`, read columns `CO2`, `N2O`, `CH4`

**Where to find the values:**
- `LF` → from Step 3b
- LLAF table → `llaf_table.csv`, columns `Load` (match on integer), `CO2`, `N2O`, `CH4`

**⚠️ LLAF is applied ONLY to Main Engine emissions.** AE and AB operate at constant load and don't need LLAF adjustment. (We apply LLAF = 1.0 to AE and AB, which means no effect.)

**Worked example — LF = 0.18 (Ship A):**
```
pct_LF = 0.18 × 100 = 18
Round to integer = 18
18 < 20, so look up row "18%" in LLAF table:
→ LLAF_CO2 = 1.03, LLAF_N2O = 1.02, LLAF_CH4 = 1.11
```

**Worked example — LF = 0.34 (Ship B):**
```
pct_LF = 0.34 × 100 = 34
Round to integer = 34
34 ≥ 20, so:
→ LLAF_CO2 = 1.00, LLAF_N2O = 1.00, LLAF_CH4 = 1.00
```

**Python implementation:**

```python
import numpy as np

# Load LLAF table
llaf = pd.read_csv('llaf_table.csv')
llaf['Load_int'] = llaf['Load'].str.replace('%', '').astype(int)

# Compute percentage load factor
df_active['pct_LF'] = (df_active['LF'] * 100).round(0).astype(int)
df_active.loc[df_active['pct_LF'] < 2, 'pct_LF'] = 2

# Merge LLAF values (for pct_LF < 20 only)
df_active = df_active.merge(
    llaf[['Load_int', 'CO2', 'N2O', 'CH4']].rename(
        columns={'Load_int': 'pct_LF', 'CO2': 'LLAF_CO2', 'N2O': 'LLAF_N2O', 'CH4': 'LLAF_CH4'}
    ), on='pct_LF', how='left'
)

# For pct_LF >= 20, set LLAF = 1.0
df_active['LLAF_CO2'] = df_active['LLAF_CO2'].fillna(1.0)
df_active['LLAF_N2O'] = df_active['LLAF_N2O'].fillna(1.0)
df_active['LLAF_CH4'] = df_active['LLAF_CH4'].fillna(1.0)
```

---

## STEP 5b: CALCULATE EMISSIONS PER ROW PER MACHINERY

**Formula (for each row, each machinery, each gas):**

```
Emission_gas_xy = LLAF_gas × Cf_gas × FC_xy
```

**Where:**
- `gas` = CO2, CH4, or N2O
- `xy` = ME, AE, or AB
- `LLAF_gas` = from Step 5a (only applied to ME; use 1.0 for AE and AB)
- `Cf_gas` = emission factor from `calculation_factors.xlsx`, sheet `"Cf"`, matched to **the fuel type that machinery burns**
- `FC_xy` = fuel consumption from Step 4b (tonnes)

### ⚠️ CRITICAL: WHICH Cf VALUES TO USE FOR EACH MACHINERY

| Machinery | Fuel it burns | Where to find fuel type | Which Cf row to look up |
|---|---|---|---|
| Main Engine (ME) | Ship's primary fuel | column `main_engine_fuel_type` (col 13) | Match ME fuel type → Cf sheet |
| Aux Engine (AE) | ALWAYS Distillate | column `aux_engine_fuel_type` (col 14) | **Always use "Distillate fuel" row** |
| Aux Boiler (AB) | ALWAYS Distillate | column `boil_engine_fuel_type` (col 15) | **Always use "Distillate fuel" row** |

**This means:**
- For AE and AB, Cf_CO2 = **3.206**, Cf_CH4 = **0.00005**, Cf_N2O = **0.00018** — ALWAYS, regardless of main engine fuel type.
- For ME, Cf values depend on the ship's main_engine_fuel_type.

**Pre-computed Cf lookup for ME:**

| main_engine_fuel_type | Cf_CO2 | Cf_CH4 | Cf_N2O |
|---|---|---|---|
| DISTILLATE FUEL | 3.206 | 0.00005 | 0.00018 |
| LNG | 2.750 | 0.00000 | 0.00011 |
| LPG (Propane) | 3.000 | 0.00005 | 0.00018 |
| LPG (Butane) | 3.030 | 0.00005 | 0.00018 |
| Methanol | 1.375 | 0.00005 | 0.00018 |
| Ethanol | 1.913 | 0.00005 | 0.00018 |
| Ammonia | **0.000** | 0.00005 | 0.00018 |
| Hydrogen | **0.000** | **0.00000** | **0.00000** |

**Expanded formulas for all 9 emission components (per row):**

```
# Main Engine emissions (uses ME fuel Cf, and LLAF from Step 5a)
E_CO2_me = LLAF_CO2 × Cf_CO2_ME_fuel × FC_me
E_CH4_me = LLAF_CH4 × Cf_CH4_ME_fuel × FC_me
E_N2O_me = LLAF_N2O × Cf_N2O_ME_fuel × FC_me

# Aux Engine emissions (uses DISTILLATE Cf, LLAF = 1.0)
E_CO2_ae = 1.0 × 3.206 × FC_ae
E_CH4_ae = 1.0 × 0.00005 × FC_ae
E_N2O_ae = 1.0 × 0.00018 × FC_ae

# Aux Boiler emissions (uses DISTILLATE Cf, LLAF = 1.0)
E_CO2_ab = 1.0 × 3.206 × FC_ab
E_CH4_ab = 1.0 × 0.00005 × FC_ab
E_N2O_ab = 1.0 × 0.00018 × FC_ab
```

**Worked example — Ship B (Ammonia), one row with FC_me=2.337t, FC_ae=0.208t, FC_ab=0.050t, LLAF=1.0:**

```
ME emissions (Ammonia: Cf_CO2=0.000, Cf_CH4=0.00005, Cf_N2O=0.00018):
  E_CO2_me = 1.0 × 0.000   × 2.337 = 0.000 tonnes     ← ZERO CO₂ from ammonia!
  E_CH4_me = 1.0 × 0.00005 × 2.337 = 0.000117 tonnes
  E_N2O_me = 1.0 × 0.00018 × 2.337 = 0.000421 tonnes

AE emissions (ALWAYS Distillate: Cf_CO2=3.206):
  E_CO2_ae = 1.0 × 3.206 × 0.208 = 0.667 tonnes        ← NONZERO CO₂ from Distillate!
  E_CH4_ae = 1.0 × 0.00005 × 0.208 = 0.0000104 tonnes
  E_N2O_ae = 1.0 × 0.00018 × 0.208 = 0.0000374 tonnes

AB emissions (ALWAYS Distillate):
  E_CO2_ab = 1.0 × 3.206 × 0.050 = 0.160 tonnes        ← NONZERO CO₂ from Distillate!
  E_CH4_ab = 1.0 × 0.00005 × 0.050 = 0.0000025 tonnes
  E_N2O_ab = 1.0 × 0.00018 × 0.050 = 0.0000090 tonnes

Row total CO₂ = 0.000 + 0.667 + 0.160 = 0.827 tonnes  (ALL from AE + AB!)
```

**⚠️ KEY POINT:** Even though this is an Ammonia ship with zero ME CO₂, the AE and AB still emit CO₂ from burning Distillate. If you mistakenly apply Ammonia's Cf_CO2=0 to all machineries, you get zero total CO₂ — which is physically wrong.

**Python implementation:**

```python
# Build Cf lookup dictionaries
cf_co2_map = {'DISTILLATE FUEL': 3.206, 'LNG': 2.750, 'Methanol': 1.375,
              'Ethanol': 1.913, 'Ammonia': 0.000, 'Hydrogen': 0.000,
              'LPG (Propane)': 3.000, 'LPG (Butane)': 3.030}
cf_ch4_map = {'DISTILLATE FUEL': 0.00005, 'LNG': 0.00000, 'Methanol': 0.00005,
              'Ethanol': 0.00005, 'Ammonia': 0.00005, 'Hydrogen': 0.00000,
              'LPG (Propane)': 0.00005, 'LPG (Butane)': 0.00005}
cf_n2o_map = {'DISTILLATE FUEL': 0.00018, 'LNG': 0.00011, 'Methanol': 0.00018,
              'Ethanol': 0.00018, 'Ammonia': 0.00018, 'Hydrogen': 0.00000,
              'LPG (Propane)': 0.00018, 'LPG (Butane)': 0.00018}

# ME Cf (varies by ship)
df_active['Cf_CO2_me'] = df_active['main_engine_fuel_type'].map(cf_co2_map)
df_active['Cf_CH4_me'] = df_active['main_engine_fuel_type'].map(cf_ch4_map)
df_active['Cf_N2O_me'] = df_active['main_engine_fuel_type'].map(cf_n2o_map)

# AE and AB Cf (ALWAYS Distillate)
Cf_CO2_dist = 3.206
Cf_CH4_dist = 0.00005
Cf_N2O_dist = 0.00018

# ME emissions (with LLAF)
df_active['E_CO2_me'] = df_active['LLAF_CO2'] * df_active['Cf_CO2_me'] * df_active['FC_me']
df_active['E_CH4_me'] = df_active['LLAF_CH4'] * df_active['Cf_CH4_me'] * df_active['FC_me']
df_active['E_N2O_me'] = df_active['LLAF_N2O'] * df_active['Cf_N2O_me'] * df_active['FC_me']

# AE emissions (LLAF = 1.0, Distillate Cf)
df_active['E_CO2_ae'] = Cf_CO2_dist * df_active['FC_ae']
df_active['E_CH4_ae'] = Cf_CH4_dist * df_active['FC_ae']
df_active['E_N2O_ae'] = Cf_N2O_dist * df_active['FC_ae']

# AB emissions (LLAF = 1.0, Distillate Cf)
df_active['E_CO2_ab'] = Cf_CO2_dist * df_active['FC_ab']
df_active['E_CH4_ab'] = Cf_CH4_dist * df_active['FC_ab']
df_active['E_N2O_ab'] = Cf_N2O_dist * df_active['FC_ab']
```

---

## STEP 5c: AGGREGATE EMISSIONS PER VESSEL AND COMPUTE CO₂ EQUIVALENT

**Sum across all rows for each vessel, then across all machineries:**

```
Total_CO2_vessel  = Σ(E_CO2_me) + Σ(E_CO2_ae) + Σ(E_CO2_ab)
Total_CH4_vessel  = Σ(E_CH4_me) + Σ(E_CH4_ae) + Σ(E_CH4_ab)
Total_N2O_vessel  = Σ(E_N2O_me) + Σ(E_N2O_ae) + Σ(E_N2O_ab)
```

**Then convert to CO₂ equivalent using GWP values:**

```
CO2eq = (1 × Total_CO2) + (28 × Total_CH4) + (265 × Total_N2O)
```

**Where to find GWP values:** These are IPCC AR5 constants given in the methodology document:
- GWP_CO2 = 1
- GWP_CH4 = 28
- GWP_N2O = 265

**Python implementation:**

```python
vessel_emissions = df_active.groupby('vessel_id').agg(
    CO2_total = ('E_CO2_me', 'sum'),  # We'll add AE/AB below
    # ... etc
).reset_index()

# Easier approach: sum all emission columns per vessel
emission_cols_co2 = ['E_CO2_me', 'E_CO2_ae', 'E_CO2_ab']
emission_cols_ch4 = ['E_CH4_me', 'E_CH4_ae', 'E_CH4_ab']
emission_cols_n2o = ['E_N2O_me', 'E_N2O_ae', 'E_N2O_ab']

df_active['E_CO2_total'] = df_active[emission_cols_co2].sum(axis=1)
df_active['E_CH4_total'] = df_active[emission_cols_ch4].sum(axis=1)
df_active['E_N2O_total'] = df_active[emission_cols_n2o].sum(axis=1)

per_vessel = df_active.groupby('vessel_id').agg(
    FC_me_total   = ('FC_me', 'sum'),
    FC_ae_total   = ('FC_ae', 'sum'),
    FC_ab_total   = ('FC_ab', 'sum'),
    CO2_total     = ('E_CO2_total', 'sum'),
    CH4_total     = ('E_CH4_total', 'sum'),
    N2O_total     = ('E_N2O_total', 'sum'),
).reset_index()

per_vessel['FC_total'] = per_vessel['FC_me_total'] + per_vessel['FC_ae_total'] + per_vessel['FC_ab_total']
per_vessel['CO2eq'] = (1 * per_vessel['CO2_total']) + (28 * per_vessel['CH4_total']) + (265 * per_vessel['N2O_total'])
```

**Expected results:**

| | Ship A (10102950, Distillate) | Ship B (10657280, Ammonia) |
|---|---|---|
| Total CO₂ | ≈ 565.78 tonnes | ≈ 121.04 tonnes |
| Total CH₄ | ≈ 0.009 tonnes | ≈ 0.024 tonnes |
| Total N₂O | ≈ 0.033 tonnes | ≈ 0.083 tonnes |
| **CO₂eq** | **≈ 574.53 tonnes** | **≈ 143.08 tonnes** |

**Ship B verification:** 121.04 CO₂ comes entirely from AE + AB burning Distillate. The ME (Ammonia) produces 0 CO₂. This is correct.

---

## STEP 6a: CALCULATE FUEL COST

**Formula:**

```
Fuel_cost = (FC_me_total × Price_per_tonne_ME) + ((FC_ae_total + FC_ab_total) × Price_per_tonne_Distillate)
```

**Where to find Price_per_tonne:**

From `calculation_factors.xlsx`, sheet `"Fuel cost"`:

```
Price_per_tonne = Cost_per_GJ × LCV
```

**Pre-computed prices (USD per tonne):**

| Fuel Type | Cost/GJ | LCV | Price/tonne (USD) |
|---|---|---|---|
| DISTILLATE FUEL | 13 | 42.7 | **555.10** |
| LPG (Propane) | 15 | 46.3 | **694.50** |
| LPG (Butane) | 15 | 45.7 | **685.50** |
| LNG | 15 | 48.0 | **720.00** |
| Methanol | 54 | 19.9 | **1,074.60** |
| Ethanol | 54 | 26.8 | **1,447.20** |
| Ammonia | 40 | 18.6 | **744.00** |
| Hydrogen | 50 | 120.0 | **6,000.00** |

**⚠️ WHY SEPARATE PRICING MATTERS:**
AE and AB always burn Distillate at $555.10/tonne. If you accidentally price all fuel at the ME rate, the error is:
- For Hydrogen ships: AE/AB fuel (~32t) priced at $6,000/t instead of $555/t → **+$173,000 phantom cost** (+38%)
- For Ammonia ships: mild ~+2% error
- For Distillate ships: no error (same rate)

**Worked example — Ship A (Distillate):**
```
ME price = 13 × 42.7 = $555.10/tonne
AE/AB price = $555.10/tonne (same fuel)

Fuel_cost = (118.20 × 555.10) + ((42.76 + 10.32) × 555.10)
          = 65,612.82 + 29,465.51
          = $95,078
```

**Worked example — Ship B (Ammonia):**
```
ME price = 40 × 18.6 = $744.00/tonne
AE/AB price = $555.10/tonne (Distillate)

Fuel_cost = (409.13 × 744.00) + ((30.46 + 7.29) × 555.10)
          = 304,392.72 + 20,958.27
          = $325,351
```

**Python implementation:**

```python
price_map = {
    'DISTILLATE FUEL': 13 * 42.7, 'LNG': 15 * 48.0,
    'Methanol': 54 * 19.9, 'Ethanol': 54 * 26.8,
    'Ammonia': 40 * 18.6, 'Hydrogen': 50 * 120.0,
    'LPG (Propane)': 15 * 46.3, 'LPG (Butane)': 15 * 45.7
}
price_distillate = 13 * 42.7  # = 555.10

# Merge vessel static data
vessel_static = df[['vessel_id', 'main_engine_fuel_type', 'dwt', 'safety_score']].drop_duplicates('vessel_id')
per_vessel = per_vessel.merge(vessel_static, on='vessel_id')

per_vessel['price_me'] = per_vessel['main_engine_fuel_type'].map(price_map)
per_vessel['fuel_cost'] = (per_vessel['FC_me_total'] * per_vessel['price_me']) + \
                          ((per_vessel['FC_ae_total'] + per_vessel['FC_ab_total']) * price_distillate)
```

---

## STEP 6b: CALCULATE CARBON COST

**Formula:**

```
Carbon_cost = CO2eq × 80
```

**Where to find the values:**
- `CO2eq` → from Step 5c (tonnes)
- `80` → from `calculation_factors.xlsx`, sheet `"Cost of Carbon"`, cell B2

**Worked examples:**
```
Ship A: Carbon_cost = 574.53 × 80 = $45,962
Ship B: Carbon_cost = 143.08 × 80 = $11,446
```

**Note:** Ship B has much lower carbon cost because Ammonia produces 0 ME CO₂. Its 143.08 tonnes CO₂eq comes almost entirely from AE/AB Distillate emissions.

```python
per_vessel['carbon_cost'] = per_vessel['CO2eq'] * 80
```

---

## STEP 6c: CALCULATE MONTHLY SHIP OWNERSHIP COST (CAPEX)

This is a multi-step calculation. Follow each sub-step carefully.

### Sub-step 6c.1: Look up base Distillate ship cost

**Where to find:** `calculation_factors.xlsx`, sheet `"Cost of ship"`, row "Distillate fuel"

Match the vessel's `dwt` (column 11 of CSV) to the correct bracket:

```python
def get_base_cost(dwt):
    if dwt <= 40000:
        return 35    # million USD
    elif dwt <= 55000:
        return 53
    elif dwt <= 80000:
        return 80
    elif dwt <= 120000:
        return 78
    else:
        return 90
```

**⚠️ Bracket boundaries:** `40-55k` means `40,000 < DWT ≤ 55,000` (lower bound exclusive, upper inclusive).

### Sub-step 6c.2: Apply fuel type multiplier

**Where to find:** `calculation_factors.xlsx`, sheet `"Cost of ship"`, rows below "Multiplier factor (M)"

```
Ship_cost = Base_cost × M × 1,000,000      (convert from millions to USD)
```

```python
multiplier_map = {
    'DISTILLATE FUEL': 1.0, 'LNG': 1.4, 'Methanol': 1.3,
    'Ethanol': 1.2, 'Ammonia': 1.4, 'Hydrogen': 1.1,
    'LPG (Propane)': 1.3, 'LPG (Butane)': 1.35
}
```

### Sub-step 6c.3: Calculate salvage value

```
S = 0.10 × Ship_cost
```

(10% of ship cost, from the methodology document)

### Sub-step 6c.4: Calculate Capital Recovery Factor (CRF)

```
r = 0.08
N = 30
CRF = r × (1 + r)^N / ((1 + r)^N − 1)
```

**Pre-computed:** (1.08)^30 = 10.06266. So:

```
CRF = 0.08 × 10.06266 / (10.06266 − 1) = 0.80501 / 9.06266 = 0.088827
```

**CRF = 0.088827** (use this constant).

### Sub-step 6c.5: Calculate amortised annual ownership cost

```
Annual_cost = ((Ship_cost − S) × CRF) + (r × S)
```

**This is:**
- `(Ship_cost − S) × CRF` = annual recovery of depreciated value
- `r × S` = annual return on salvage value (opportunity cost)

### Sub-step 6c.6: Convert to monthly

```
Monthly_CAPEX = Annual_cost / 12
```

### Full worked example — Ship A (Distillate, DWT=175,108):

```
Step 6c.1: DWT = 175,108 > 120,000 → Base_cost = $90M
Step 6c.2: Fuel = DISTILLATE FUEL → M = 1.0
           Ship_cost = 90 × 1.0 × 1,000,000 = $90,000,000
Step 6c.3: S = 0.10 × 90,000,000 = $9,000,000
Step 6c.4: CRF = 0.088827
Step 6c.5: Annual = ((90,000,000 − 9,000,000) × 0.088827) + (0.08 × 9,000,000)
                   = (81,000,000 × 0.088827) + 720,000
                   = 7,194,987 + 720,000
                   = $7,914,987 / year
Step 6c.6: Monthly = 7,914,987 / 12 = $659,582 ≈ $659,585/month
```

### Full worked example — Ship B (Ammonia, DWT=206,331):

```
Step 6c.1: DWT = 206,331 > 120,000 → Base_cost = $90M
Step 6c.2: Fuel = Ammonia → M = 1.4
           Ship_cost = 90 × 1.4 × 1,000,000 = $126,000,000
Step 6c.3: S = 0.10 × 126,000,000 = $12,600,000
Step 6c.5: Annual = ((126,000,000 − 12,600,000) × 0.088827) + (0.08 × 12,600,000)
                   = (113,400,000 × 0.088827) + 1,008,000
                   = 10,073,021 + 1,008,000
                   = $11,081,021 / year
Step 6c.6: Monthly = 11,081,021 / 12 = $923,418 ≈ $923,419/month
```

**Python implementation:**

```python
per_vessel['base_cost_M'] = per_vessel['dwt'].apply(get_base_cost)  # in millions
per_vessel['multiplier'] = per_vessel['main_engine_fuel_type'].map(multiplier_map)
per_vessel['ship_cost'] = per_vessel['base_cost_M'] * per_vessel['multiplier'] * 1_000_000

S = 0.10 * per_vessel['ship_cost']
CRF = 0.088827
r = 0.08
annual_cost = ((per_vessel['ship_cost'] - S) * CRF) + (r * S)
per_vessel['monthly_capex'] = annual_cost / 12
```

---

## STEP 6d: TOTAL MONTHLY SHIP COST (before risk adjustment)

**Formula:**

```
Total_monthly_cost = fuel_cost + carbon_cost + monthly_capex
```

**Worked examples:**

```
Ship A: 95,078 + 45,962 + 659,585 = $800,625
Ship B: 325,351 + 11,446 + 923,419 = $1,260,216
```

```python
per_vessel['total_monthly'] = per_vessel['fuel_cost'] + per_vessel['carbon_cost'] + per_vessel['monthly_capex']
```

---

## STEP 6e: CALCULATE RISK PREMIUM

**Formula:**

```
Risk_premium = Total_monthly_cost × adjustment_rate
```

**Where to find adjustment_rate:** `calculation_factors.xlsx`, sheet `"Safety score adjustment"`, match on `safety_score` (column 10 of CSV):

| safety_score | adjustment_rate (as decimal) |
|---|---|
| 1 | +0.10 |
| 2 | +0.05 |
| 3 | 0.00 |
| 4 | −0.02 |
| 5 | −0.05 |

**Worked examples:**

```
Ship A (safety_score=1): Risk_premium = 800,625 × (+0.10) = +$80,063
Ship B (safety_score=3): Risk_premium = 1,260,216 × (0.00) = $0
```

```python
adj_map = {1: 0.10, 2: 0.05, 3: 0.00, 4: -0.02, 5: -0.05}
per_vessel['adj_rate'] = per_vessel['safety_score'].map(adj_map)
per_vessel['risk_premium'] = per_vessel['total_monthly'] * per_vessel['adj_rate']
```

---

## STEP 6f: FINAL RISK-ADJUSTED SHIP COST

**Formula:**

```
Final_cost = Total_monthly_cost + Risk_premium
```

**Equivalently:**

```
Final_cost = Total_monthly_cost × (1 + adjustment_rate)
```

**Worked examples:**

```
Ship A: 800,625 + 80,063 = $880,688  (or 800,625 × 1.10)
Ship B: 1,260,216 + 0 = $1,260,216   (or 1,260,216 × 1.00)
```

**Cost per DWT (useful metric for judging ship efficiency):**
```
Ship A: $880,688 / 175,108 = $5.03/DWT
Ship B: $1,260,216 / 206,331 = $6.11/DWT
```

```python
per_vessel['final_cost'] = per_vessel['total_monthly'] + per_vessel['risk_premium']
per_vessel['cost_per_dwt'] = per_vessel['final_cost'] / per_vessel['dwt']
```

---

## STEP 7: FLEET OPTIMISATION (MILP)

You now have a table with 108 rows, one per vessel, with columns: `vessel_id`, `dwt`, `safety_score`, `main_engine_fuel_type`, `final_cost`, `FC_total`, `CO2eq`.

### 7.1 Constants

```python
MONTHLY_DEMAND = 4_576_667  # tonnes DWT (= 54,920,000 / 12)
SAFETY_THRESHOLD = 3.0
FUEL_TYPES = ['DISTILLATE FUEL', 'LNG', 'Methanol', 'Ethanol',
              'Ammonia', 'Hydrogen', 'LPG (Propane)', 'LPG (Butane)']
```

**Where MONTHLY_DEMAND comes from:** MPA Annual Report 2024 (file `mpa-ar24-full-book_fa.pdf`), Page 10: "Bunker Sales Volume 2024 = 54.92 million tonnes". Divide by 12 months = 4,576,667 tonnes/month.

### 7.2 Formulation

```python
from pulp import *

prob = LpProblem("FleetSelection", LpMinimize)

# Decision variable: 1 = select ship, 0 = don't
ships = per_vessel.to_dict('records')
x = {s['vessel_id']: LpVariable(f"x_{s['vessel_id']}", cat='Binary') for s in ships}

# OBJECTIVE: minimise total fleet cost
prob += lpSum(x[s['vessel_id']] * s['final_cost'] for s in ships)

# CONSTRAINT 1: Total DWT >= monthly demand
prob += lpSum(x[s['vessel_id']] * s['dwt'] for s in ships) >= MONTHLY_DEMAND

# CONSTRAINT 2: Average safety >= 3.0 (linearised)
# Σ x_i × (safety_i - 3.0) >= 0
prob += lpSum(x[s['vessel_id']] * (s['safety_score'] - SAFETY_THRESHOLD) for s in ships) >= 0

# CONSTRAINT 3: At least one ship per fuel type
for ft in FUEL_TYPES:
    ft_ships = [s for s in ships if s['main_engine_fuel_type'] == ft]
    prob += lpSum(x[s['vessel_id']] for s in ft_ships) >= 1

# SOLVE
prob.solve(PULP_CBC_CMD(msg=0))
```

### 7.3 Extract results

```python
selected = [s for s in ships if x[s['vessel_id']].value() == 1]

total_dwt = sum(s['dwt'] for s in selected)
total_cost = sum(s['final_cost'] for s in selected)
avg_safety = sum(s['safety_score'] for s in selected) / len(selected)
total_co2eq = sum(s['CO2eq'] for s in selected)
total_fuel = sum(s['FC_total'] for s in selected)
fuel_types_count = len(set(s['main_engine_fuel_type'] for s in selected))
fleet_size = len(selected)
```

### 7.4 Expected ranges for base case (safety ≥ 3.0)

| Metric | Sanity check range |
|---|---|
| Fleet size | 25 – 40 ships |
| Total DWT | 4,577,000 – 5,500,000 tonnes |
| Total cost | $25M – $40M |
| Avg safety score | 3.00 – 3.50 |
| Total CO₂eq | 10,000 – 25,000 tonnes |
| Total fuel | 4,000 – 10,000 tonnes |
| Fuel types | 8 (must be all 8) |

---

## STEP 8: SENSITIVITY ANALYSIS

### 8.1 Safety threshold sweep

Re-run Step 7 with `SAFETY_THRESHOLD` set to 3.0, 3.5, 4.0, and 4.5. Record all outputs for each run.

```python
results = []
for threshold in [3.0, 3.5, 4.0, 4.5]:
    # rebuild constraint 2 with new threshold
    # ... (re-run MILP)
    results.append({'threshold': threshold, 'cost': total_cost, 'safety': avg_safety, ...})
```

### 8.2 Carbon price sweep

Re-run the full pipeline (Steps 6b onward) with carbon price set to $80, $120, $160, $200. You must recompute `carbon_cost`, `total_monthly`, `risk_premium`, and `final_cost` for each ship before re-running the MILP.

---

## STEP 9: FILL SUBMISSION CSV

**File:** `submission_template.csv`

| Field | Where to get value |
|---|---|
| team_name | Your team name (string) |
| category | Your category: "A" or "B" |
| report_file_name | "MaritimeHackathon2026_CasePaper_teamname.pdf" |
| sum_of_fleet_deadweight | `total_dwt` from Step 7.3 |
| total_cost_of_fleet | `total_cost` from Step 7.3 |
| average_fleet_safety_score | `avg_safety` from Step 7.3 |
| no_of_unique_main_engine_fuel_types_in_fleet | `fuel_types_count` from Step 7.3 (should be 8) |
| sensitivity_analysis_performance | "Yes" |
| size_of_fleet_count | `fleet_size` from Step 7.3 |
| total_emission_CO2_eq | `total_co2eq` from Step 7.3 |
| total_fuel_consumption | `total_fuel` from Step 7.3 |

---

## COMPLETE VERIFICATION CHECKPOINT

Use these five checkpoint vessels to verify your entire pipeline. If your numbers don't match (within ±2%), you have a bug.

### Checkpoint 1: Vessel 10102950 (DISTILLATE FUEL)

| Stage | Expected Value |
|---|---|
| DWT | 175,108 |
| Safety score | 1 |
| MS = 1.066 × 14.62 | 15.58 kn |
| SFC_ME adjusted = 171.4 × (42.7/42.7) | 171.4 g/kWh |
| SFC_AE adjusted | 199.3 g/kWh (no change) |
| SFC_AB adjusted | 300.0 g/kWh (no change) |
| Transit hours | ≈ 194.5 |
| Maneuver hours | ≈ 14.0 |
| Mean LF (transit) | ≈ 0.186 |
| FC_ME total | ≈ 118.20 tonnes |
| FC_AE total | ≈ 42.76 tonnes |
| FC_AB total | ≈ 10.32 tonnes |
| FC_total | ≈ 171.28 tonnes |
| CO₂ total | ≈ 565.78 tonnes |
| CO₂eq | ≈ 574.53 tonnes |
| Fuel cost | ≈ $95,078 |
| Carbon cost = 574.53 × 80 | ≈ $45,962 |
| Monthly CAPEX | ≈ $659,585 |
| Total monthly | ≈ $800,625 |
| Risk premium = 800,625 × 0.10 | ≈ +$80,063 |
| **Final cost** | **≈ $880,688** |
| $/DWT | ≈ $5.03 |

### Checkpoint 2: Vessel 10657280 (Ammonia)

| Stage | Expected Value |
|---|---|
| DWT | 206,331 |
| Safety score | 3 |
| MS = 1.066 × 14.97 | 15.96 kn |
| SFC_ME adjusted = 169.1 × (42.7/18.6) | 388.2 g/kWh |
| SFC_AE adjusted | 200.5 g/kWh (no change) |
| Transit hours | ≈ 132.9 |
| Maneuver hours | ≈ 6.0 |
| Mean LF (transit) | ≈ 0.420 |
| FC_ME total | ≈ 409.13 tonnes |
| FC_AE total | ≈ 30.46 tonnes |
| FC_AB total | ≈ 7.29 tonnes |
| CO₂ total | ≈ 121.04 tonnes **(NOT ZERO — AE/AB emit CO₂!)** |
| CO₂eq | ≈ 143.08 tonnes |
| Fuel cost (ME @ $744 + AE/AB @ $555.10) | ≈ $325,351 |
| Carbon cost | ≈ $11,446 |
| Monthly CAPEX | ≈ $923,419 |
| Risk premium | $0 (safety = 3) |
| **Final cost** | **≈ $1,260,216** |
| $/DWT | ≈ $6.11 |

### Checkpoint 3: Vessel 10791900 (LNG)

| Stage | Expected Value |
|---|---|
| DWT | 179,700 |
| Safety score | 5 |
| MS = 1.066 × 14.45 | 15.40 kn |
| SFC_ME adjusted = sfc × (42.7/48.0) | 154.3 g/kWh |
| FC_ME total | ≈ 154.81 tonnes |
| CO₂eq | ≈ 548.51 tonnes |
| Fuel cost | ≈ $131,611 |
| Monthly CAPEX | ≈ $923,419 |
| Risk premium = total × (−0.05) | ≈ −$54,946 |
| **Final cost** | **≈ $1,043,965** |
| $/DWT | ≈ $5.81 |

### Checkpoint 4: Vessel 10522650 (Methanol)

| Stage | Expected Value |
|---|---|
| DWT | 115,444 |
| Safety score | 3 |
| SFC_ME adjusted = sfc × (42.7/19.9) | 370.6 g/kWh |
| FC_ME total | ≈ 331.37 tonnes |
| CO₂eq | ≈ 548.38 tonnes |
| Fuel cost | ≈ $369,132 |
| Monthly CAPEX | ≈ $743,133 |
| **Final cost** | **≈ $1,156,134** |
| $/DWT | ≈ $10.01 |

### Checkpoint 5: Vessel 10673120 (Hydrogen)

| Stage | Expected Value |
|---|---|
| DWT | 178,838 |
| Safety score | 3 |
| SFC_ME adjusted = sfc × (42.7/120.0) | 60.4 g/kWh |
| FC_ME total | ≈ 72.34 tonnes |
| CO₂ total | ≈ 102.10 tonnes **(NOT ZERO — AE/AB emit!)** |
| CO₂eq | ≈ 103.67 tonnes |
| Fuel cost (ME @ $6,000 + AE/AB @ $555.10) | ≈ $451,703 |
| Monthly CAPEX | ≈ $725,544 |
| **Final cost** | **≈ $1,185,540** |
| $/DWT | ≈ $6.63 |

---

## COMMON MISTAKES TO WATCH FOR

| # | Mistake | How to detect | Impact |
|---|---|---|---|
| 1 | Pricing all fuel at ME rate | Hydrogen ships show fuel cost ≈ $625k instead of ≈ $452k | +38% for Hydrogen |
| 2 | Applying ME emission factors to AE/AB | Ammonia/Hydrogen ships show CO₂ = 0 | Missing ~$8–10k carbon cost per ship |
| 3 | Applying SFC adjustment to AE/AB | AE fuel consumption doubles for Methanol ships | Large overcount |
| 4 | Applying LLAF to AE/AB | Small overcount on emissions during maneuvering | Minor (~1%) |
| 5 | Forgetting to cap activity hours at 6h | Two vessels get absurd fuel costs | Very large |
| 6 | Not capping LF at 1.0 | Some rows show LF > 1.0 → impossible engine load | Moderate |
| 7 | Using wrong DWT bracket boundary | e.g., DWT=40,000 goes to 10–40k (correct) not 40–55k | Affects CAPEX |
| 8 | Forgetting to divide annual CAPEX by 12 | CAPEX 12× too high | Fatal |
| 9 | Not converting CAPEX from millions | $90 instead of $90,000,000 | Fatal |
| 10 | Using `in_port_boundary == "Singapore"` for anchorage instead of `in_anchorage == "anchorage"` | Wrong mode classification | Moderate |

---

## QUICK REFERENCE: THE FULL FORMULA CHAIN IN ONE PLACE

```
FOR EACH AIS ROW WHERE MODE ∈ {Transit, Maneuver}:

  A = min((epoch_next − epoch_current) / 3600, 6.0)
  MS = 1.066 × vref
  LF = max(0.02, min(round((speed / MS)³, 2), 1.0))

  sfc_adj_me = sfc_me × (42.7 / LCV[main_engine_fuel_type])
  sfc_adj_ae = sfc_ae                    # always Distillate
  sfc_adj_ab = sfc_ab                    # always Distillate

  FC_me = LF × mep × sfc_adj_me × A / 1e6
  FC_ae = ael × sfc_adj_ae × A / 1e6
  FC_ab = abl × sfc_adj_ab × A / 1e6

  pct_LF = max(2, round(LF × 100))
  LLAF_CO2, LLAF_N2O, LLAF_CH4 = lookup(pct_LF) if pct_LF < 20 else (1,1,1)

  E_CO2 = LLAF_CO2 × Cf_CO2[ME_fuel] × FC_me + 3.206 × FC_ae + 3.206 × FC_ab
  E_CH4 = LLAF_CH4 × Cf_CH4[ME_fuel] × FC_me + 0.00005 × FC_ae + 0.00005 × FC_ab
  E_N2O = LLAF_N2O × Cf_N2O[ME_fuel] × FC_me + 0.00018 × FC_ae + 0.00018 × FC_ab

PER VESSEL (sum across rows):

  FC_total = Σ FC_me + Σ FC_ae + Σ FC_ab
  CO2eq = Σ E_CO2 + 28 × Σ E_CH4 + 265 × Σ E_N2O

  Fuel_cost = Σ FC_me × (Cost_GJ[ME_fuel] × LCV[ME_fuel]) +
              (Σ FC_ae + Σ FC_ab) × 555.10

  Carbon_cost = CO2eq × 80
  Ship_cost = Base[DWT_bracket] × M[ME_fuel] × 1e6
  Monthly_CAPEX = (((Ship_cost − 0.1×Ship_cost) × 0.088827) + (0.08 × 0.1×Ship_cost)) / 12
  Total_monthly = Fuel_cost + Carbon_cost + Monthly_CAPEX
  Final_cost = Total_monthly × (1 + adj_rate[safety_score])

FLEET OPTIMISATION:

  min  Σ x_i × Final_cost_i
  s.t. Σ x_i × DWT_i ≥ 4,576,667
       Σ x_i × (safety_i − 3) ≥ 0
       ∀ fuel_type: Σ x_i[fuel_type] ≥ 1
       x_i ∈ {0, 1}
```
