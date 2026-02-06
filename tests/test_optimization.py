"""Tests for optimization constraints and metrics."""

import pandas as pd
import pytest

from src.optimization import (
    validate_fleet,
    total_cost_and_metrics,
    format_outputs,
)


@pytest.fixture
def sample_ships():
    return pd.DataFrame([
        {"vessel_id": 1, "dwt": 10000, "safety_score": 4, "main_engine_fuel_type": "A", "total_cost_usd": 100, "fuel_tonnes": 50, "co2e_tonnes": 160},
        {"vessel_id": 2, "dwt": 15000, "safety_score": 3, "main_engine_fuel_type": "B", "total_cost_usd": 120, "fuel_tonnes": 60, "co2e_tonnes": 190},
        {"vessel_id": 3, "dwt": 20000, "safety_score": 5, "main_engine_fuel_type": "C", "total_cost_usd": 90, "fuel_tonnes": 40, "co2e_tonnes": 130},
    ])


def test_validate_fleet_demand(sample_ships):
    ok, errs = validate_fleet(sample_ships, [1, 2], cargo_demand_tonnes=30000, min_avg_safety=3, require_all_fuel_types=False)
    assert not ok
    assert any("DWT" in e for e in errs)


def test_validate_fleet_ok(sample_ships):
    ok, errs = validate_fleet(sample_ships, [1, 2, 3], cargo_demand_tonnes=30000, min_avg_safety=3, require_all_fuel_types=True)
    assert ok
    assert len(errs) == 0


def test_total_cost_and_metrics(sample_ships):
    m = total_cost_and_metrics(sample_ships, [1, 2, 3])
    assert m["total_dwt"] == 45000
    assert m["total_cost_usd"] == 310
    assert m["fleet_size"] == 3
    assert m["num_unique_main_engine_fuel_types"] == 3


def test_format_outputs(sample_ships):
    m = total_cost_and_metrics(sample_ships, [1, 2, 3])
    out = format_outputs(m, sensitivity_done=True)
    assert "Total cost of selected fleet (USD)" in out
    assert out["Sensitivity analysis performed"] == "Yes"
