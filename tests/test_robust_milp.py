"""Tests for select_fleet_minmax_milp() — min-max robust fleet selector."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimization import (
    DEFAULT_ROBUST_SCENARIOS,
    build_scenario_cost_matrix,
    fleet_costs_by_scenario,
    select_fleet_minmax_milp,
    validate_fleet,
)


@pytest.fixture
def vessels():
    """Load the 5 checkpoint vessels from test fixtures."""
    csv_path = Path(__file__).parent / "fixtures" / "checkpoint_vessels.csv"
    return pd.read_csv(csv_path)


# Scenario set feasible with 5-vessel fixture: max safety 1.0 so all 5 can be selected
FEASIBLE_SCENARIOS = {
    "base": {"carbon_price": 80, "min_avg_safety": 1.0},
    "high_carbon": {"carbon_price": 160, "min_avg_safety": 1.0},
}


class TestSelectFleetMinmaxMilp:
    def test_returns_non_empty_sorted_ids_when_feasible(self, vessels):
        """With feasible scenarios and demand <= total DWT, returns non-empty sorted list."""
        selected, z_value = select_fleet_minmax_milp(
            vessels,
            scenarios=FEASIBLE_SCENARIOS,
            cargo_demand=855_421,
            require_all_fuel_types=True,
        )
        assert len(selected) > 0
        assert selected == sorted(selected)

    def test_validate_fleet_passes_for_strictest_scenario(self, vessels):
        """Returned fleet satisfies constraints under the strictest scenario."""
        selected, z_value = select_fleet_minmax_milp(
            vessels,
            scenarios=FEASIBLE_SCENARIOS,
            cargo_demand=855_421,
            require_all_fuel_types=True,
        )
        assert len(selected) > 0
        min_avg_safety_robust = max(
            s["min_avg_safety"] for s in FEASIBLE_SCENARIOS.values()
        )
        ok, errors = validate_fleet(
            vessels,
            selected,
            cargo_demand_tonnes=855_421,
            min_avg_safety=min_avg_safety_robust,
            require_all_fuel_types=True,
        )
        assert ok, errors

    def test_worst_case_cost_equals_z(self, vessels):
        """Max cost over scenarios equals (or is very close to) optimal Z."""
        selected, z_value = select_fleet_minmax_milp(
            vessels,
            scenarios=FEASIBLE_SCENARIOS,
            cargo_demand=855_421,
            require_all_fuel_types=True,
        )
        assert len(selected) > 0
        assert z_value is not None
        cost_by_scenario = fleet_costs_by_scenario(
            vessels, FEASIBLE_SCENARIOS, selected
        )
        worst_cost = max(cost_by_scenario.values())
        assert abs(worst_cost - z_value) < 1.0

    def test_returns_empty_and_none_when_infeasible(self, vessels):
        """When demand exceeds total DWT, returns ([], None)."""
        selected, z_value = select_fleet_minmax_milp(
            vessels,
            scenarios=FEASIBLE_SCENARIOS,
            cargo_demand=999_999_999,
            require_all_fuel_types=False,
        )
        assert selected == []
        assert z_value is None


class TestBuildScenarioCostMatrix:
    def test_shape_matches_df_and_scenarios(self, vessels):
        """Cost matrix has index = df.index, columns = scenario names."""
        matrix = build_scenario_cost_matrix(vessels, FEASIBLE_SCENARIOS)
        assert matrix.index.tolist() == vessels.index.tolist()
        assert list(matrix.columns) == list(FEASIBLE_SCENARIOS.keys())

    def test_base_scenario_close_to_final_cost(self, vessels):
        """With carbon_price 80 (default), base scenario cost close to final_cost."""
        scenarios_80 = {"base": {"carbon_price": 80, "min_avg_safety": 1.0}}
        matrix = build_scenario_cost_matrix(vessels, scenarios_80)
        diff = (matrix["base"] - vessels["final_cost"]).abs()
        assert (diff < 1.0).all()


class TestFleetCostsByScenario:
    def test_matches_sum_of_cost_matrix_rows(self, vessels):
        """Total cost by scenario equals sum of cost matrix for selected vessels."""
        selected, _ = select_fleet_minmax_milp(
            vessels,
            scenarios=FEASIBLE_SCENARIOS,
            cargo_demand=500_000,
            require_all_fuel_types=False,
        )
        if not selected:
            pytest.skip("infeasible with demand 500k")
        cost_by_scenario = fleet_costs_by_scenario(
            vessels, FEASIBLE_SCENARIOS, selected
        )
        matrix = build_scenario_cost_matrix(vessels, FEASIBLE_SCENARIOS)
        mask = vessels["vessel_id"].isin(selected)
        for sname, total in cost_by_scenario.items():
            expected = matrix.loc[mask, sname].sum()
            assert abs(total - expected) < 1.0
