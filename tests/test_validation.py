"""Validation tests for checkpoint vessel costs and MILP solution quality.

Verifies:
- Per-vessel costs from checkpoint_vessels.csv match SOP expected values
- MILP solver produces correct fleet selections on known fixtures
- Aggregated metrics are consistent across all functions
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimization import select_fleet_milp, validate_fleet, total_cost_and_metrics


@pytest.fixture
def vessels():
    """Load the 5 checkpoint vessels from test fixtures."""
    csv_path = Path(__file__).parent / "fixtures" / "checkpoint_vessels.csv"
    return pd.read_csv(csv_path)


# Expected per-vessel values from SOP checkpoints
EXPECTED_VESSELS = {
    10102950: {"final_cost": 880688, "CO2eq": 574.53, "fuel_type": "DISTILLATE FUEL", "dwt": 175108},
    10657280: {"final_cost": 1260216, "CO2eq": 143.08, "fuel_type": "Ammonia", "dwt": 206331},
    10791900: {"final_cost": 1043965, "CO2eq": 548.51, "fuel_type": "LNG", "dwt": 179700},
    10522650: {"final_cost": 1156134, "CO2eq": 548.38, "fuel_type": "Methanol", "dwt": 115444},
    10673120: {"final_cost": 1185540, "CO2eq": 103.67, "fuel_type": "Hydrogen", "dwt": 178838},
}

ALL_IDS = sorted(EXPECTED_VESSELS.keys())
TOTAL_DWT = 855421
TOTAL_COST = 5526543
TOTAL_CO2E = 574.53 + 143.08 + 548.51 + 548.38 + 103.67


class TestCheckpointVesselValues:
    """Verify each checkpoint vessel's final_cost and CO2eq match SOP expected values."""

    def test_vessel_10102950_final_cost(self, vessels):
        row = vessels[vessels["vessel_id"] == 10102950].iloc[0]
        assert int(row["final_cost"]) == 880688

    def test_vessel_10102950_co2eq(self, vessels):
        row = vessels[vessels["vessel_id"] == 10102950].iloc[0]
        assert row["CO2eq"] == pytest.approx(574.53, rel=1e-3)

    def test_vessel_10657280_final_cost(self, vessels):
        row = vessels[vessels["vessel_id"] == 10657280].iloc[0]
        assert int(row["final_cost"]) == 1260216

    def test_vessel_10657280_co2eq(self, vessels):
        row = vessels[vessels["vessel_id"] == 10657280].iloc[0]
        assert row["CO2eq"] == pytest.approx(143.08, rel=1e-3)

    def test_vessel_10791900_final_cost(self, vessels):
        row = vessels[vessels["vessel_id"] == 10791900].iloc[0]
        assert int(row["final_cost"]) == 1043965

    def test_vessel_10791900_co2eq(self, vessels):
        row = vessels[vessels["vessel_id"] == 10791900].iloc[0]
        assert row["CO2eq"] == pytest.approx(548.51, rel=1e-3)

    def test_vessel_10522650_final_cost(self, vessels):
        row = vessels[vessels["vessel_id"] == 10522650].iloc[0]
        assert int(row["final_cost"]) == 1156134

    def test_vessel_10522650_co2eq(self, vessels):
        row = vessels[vessels["vessel_id"] == 10522650].iloc[0]
        assert row["CO2eq"] == pytest.approx(548.38, rel=1e-3)

    def test_vessel_10673120_final_cost(self, vessels):
        row = vessels[vessels["vessel_id"] == 10673120].iloc[0]
        assert int(row["final_cost"]) == 1185540

    def test_vessel_10673120_co2eq(self, vessels):
        row = vessels[vessels["vessel_id"] == 10673120].iloc[0]
        assert row["CO2eq"] == pytest.approx(103.67, rel=1e-3)


class TestMILPOnFixtures:
    """Run select_fleet_milp() on the 5 checkpoint fixtures and verify results."""

    def test_all_selected_when_demand_equals_total_dwt(self, vessels):
        """With demand=855421 (total DWT), safety>=1.0, no fuel diversity: all 5 selected."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=855_421,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        assert sorted(result) == ALL_IDS

    def test_all_selected_total_cost(self, vessels):
        """When all 5 selected, total cost = 5,526,543."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=855_421,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        selected = vessels[vessels["vessel_id"].isin(result)]
        assert selected["final_cost"].sum() == TOTAL_COST

    def test_safety_constrained_selects_three(self, vessels):
        """With demand=500000, safety>=3.0, no fuel diversity: 3 vessels selected."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=3.0,
            require_all_fuel_types=False,
        )
        assert len(result) == 3

    def test_safety_constrained_cost(self, vessels):
        """With demand=500000, safety>=3.0: cost = 3,110,193."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=3.0,
            require_all_fuel_types=False,
        )
        selected = vessels[vessels["vessel_id"].isin(result)]
        assert selected["final_cost"].sum() == 3_110_193

    def test_validate_fleet_all_selected(self, vessels):
        """validate_fleet() returns ok=True for the all-5 selection."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=855_421,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        ok, errors = validate_fleet(
            vessels, result, cargo_demand_tonnes=855_421,
            min_avg_safety=1.0, require_all_fuel_types=False,
        )
        assert ok is True
        assert errors == []

    def test_validate_fleet_safety_constrained(self, vessels):
        """validate_fleet() returns ok=True for the safety-constrained selection."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=3.0,
            require_all_fuel_types=False,
        )
        ok, errors = validate_fleet(
            vessels, result, cargo_demand_tonnes=500_000,
            min_avg_safety=3.0, require_all_fuel_types=False,
        )
        assert ok is True
        assert errors == []

    def test_metrics_all_selected(self, vessels):
        """total_cost_and_metrics for all-5: dwt >= demand, safety >= threshold, fleet_size matches."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=855_421,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        metrics = total_cost_and_metrics(vessels, result)
        assert metrics["total_dwt"] >= 855_421
        assert metrics["avg_safety_score"] >= 1.0
        assert metrics["fleet_size"] == len(result)

    def test_metrics_safety_constrained(self, vessels):
        """total_cost_and_metrics for safety-constrained: dwt >= demand, safety >= threshold."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=3.0,
            require_all_fuel_types=False,
        )
        metrics = total_cost_and_metrics(vessels, result)
        assert metrics["total_dwt"] >= 500_000
        assert metrics["avg_safety_score"] >= 3.0
        assert metrics["fleet_size"] == len(result)


class TestMetricsConsistency:
    """Verify total_cost_and_metrics aggregates are consistent for the all-5 selection."""

    @pytest.fixture
    def all_five_metrics(self, vessels):
        """Run total_cost_and_metrics on all 5 checkpoint vessels."""
        return total_cost_and_metrics(vessels, ALL_IDS)

    def test_total_dwt(self, all_five_metrics):
        assert all_five_metrics["total_dwt"] == TOTAL_DWT

    def test_total_cost_usd(self, all_five_metrics):
        assert all_five_metrics["total_cost_usd"] == TOTAL_COST

    def test_fleet_size(self, all_five_metrics):
        assert all_five_metrics["fleet_size"] == 5

    def test_num_unique_fuel_types(self, all_five_metrics):
        assert all_five_metrics["num_unique_main_engine_fuel_types"] == 5

    def test_avg_safety_score(self, all_five_metrics):
        # Mean of [1, 3, 5, 3, 3] = 15/5 = 3.0
        assert all_five_metrics["avg_safety_score"] == 3.0

    def test_total_co2e_tonnes(self, all_five_metrics):
        assert all_five_metrics["total_co2e_tonnes"] == pytest.approx(TOTAL_CO2E, rel=1e-3)
