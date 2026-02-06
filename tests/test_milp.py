"""Tests for select_fleet_milp() — the binary MILP fleet selector."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimization import select_fleet_milp


@pytest.fixture
def vessels():
    """Load the 5 checkpoint vessels from test fixtures."""
    csv_path = Path(__file__).parent / "fixtures" / "checkpoint_vessels.csv"
    return pd.read_csv(csv_path)


# Vessel reference:
#   10102950: 175108 DWT, safety=1, DISTILLATE FUEL, $880,688
#   10657280: 206331 DWT, safety=3, Ammonia,         $1,260,216
#   10791900: 179700 DWT, safety=5, LNG,             $1,043,965
#   10522650: 115444 DWT, safety=3, Methanol,        $1,156,134
#   10673120: 178838 DWT, safety=3, Hydrogen,        $1,185,540
#   Total DWT: 855,421  |  Total cost: $5,526,543

ALL_IDS = sorted([10102950, 10657280, 10791900, 10522650, 10673120])


class TestAllVesselsWhenDemandRequiresIt:
    def test_selects_all_five_when_demand_equals_total_dwt(self, vessels):
        """With demand=855421 (total DWT), all 5 must be selected."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=855_421,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        assert sorted(result) == ALL_IDS

    def test_total_cost_is_sum_of_all(self, vessels):
        """When all 5 selected, total cost = 5,526,543."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=855_421,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        selected = vessels[vessels["vessel_id"].isin(result)]
        assert selected["final_cost"].sum() == 5_526_543


class TestDWTConstraint:
    def test_drops_methanol_to_minimize_cost(self, vessels):
        """With demand=700000, optimal is to drop Methanol (cheapest removable)."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=700_000,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        expected = sorted([10102950, 10657280, 10791900, 10673120])
        assert sorted(result) == expected

    def test_cost_without_methanol(self, vessels):
        """Dropping Methanol gives cost = 4,370,409."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=700_000,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        selected = vessels[vessels["vessel_id"].isin(result)]
        assert selected["final_cost"].sum() == 4_370_409


class TestSafetyConstraint:
    def test_cheapest_combo_meeting_safety(self, vessels):
        """With demand=500000, safety>=3.0: cheapest is {Distillate, Ammonia, LNG}."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=3.0,
            require_all_fuel_types=False,
        )
        expected = sorted([10102950, 10657280, 10791900])
        assert sorted(result) == expected

    def test_safety_combo_cost(self, vessels):
        """Cheapest safety-valid combo costs $3,184,869."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=3.0,
            require_all_fuel_types=False,
        )
        selected = vessels[vessels["vessel_id"].isin(result)]
        assert selected["final_cost"].sum() == 3_184_869


class TestFuelDiversityConstraint:
    def test_all_fuel_types_forces_all_selected(self, vessels):
        """With require_all_fuel_types=True, must include all 5 fuel types → all 5 vessels."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=1.0,
            require_all_fuel_types=True,
        )
        assert sorted(result) == ALL_IDS


class TestInfeasible:
    def test_returns_empty_on_impossible_demand(self, vessels):
        """Demand=999,999,999 is impossible → empty list."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=999_999_999,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        assert result == []


class TestDeterminism:
    def test_returns_sorted_ids(self, vessels):
        """Output vessel IDs should be sorted for deterministic output."""
        result = select_fleet_milp(
            vessels,
            cargo_demand=500_000,
            min_avg_safety=1.0,
            require_all_fuel_types=False,
        )
        assert result == sorted(result)
