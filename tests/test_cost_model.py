"""Tests for cost_model."""

import pandas as pd
import pytest

from src.cost_model import (
    fuel_consumption_tonnes,
    fuel_cost_usd,
    co2e_tonnes,
    amortized_ownership_per_month_usd,
    risk_premium_usd,
)


def test_fuel_consumption_tonnes():
    # P=5000 kW, sfc_me=180 g/kWh, 100 h -> 5000*0.8*100*180/1e6 = 72 tonnes
    row = pd.Series({"P": 5000, "ael": 500, "abl": 200, "sfc_me": 180, "sfc_ae": 220, "sfc_ab": 80})
    out = fuel_consumption_tonnes(row, voyage_hours=100)
    assert out["fuel_me_tonnes"] == pytest.approx(72.0)
    assert out["fuel_ae_tonnes"] > 0
    assert out["fuel_ab_tonnes"] > 0


def test_amortized_ownership():
    x = amortized_ownership_per_month_usd(1_000_000, crf=0.065, n_years=30)
    assert x == pytest.approx(1_000_000 * 0.065 / 12)


def test_risk_premium():
    assert risk_premium_usd(1000, 3, {3: 0}) == 0
    assert risk_premium_usd(1000, 1, {1: 0.10}) == 100
    assert risk_premium_usd(1000, 5, {5: -0.05}) == -50
