"""
Tests for src/data_adapter.py — per_vessel.csv loading and validation.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.data_adapter import REQUIRED_COLUMNS, load_per_vessel, validate_per_vessel
from src.utils import project_root


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
FIXTURE_PATH = project_root() / "tests" / "fixtures" / "checkpoint_vessels.csv"


@pytest.fixture
def fixture_df() -> pd.DataFrame:
    """Load the checkpoint vessels fixture directly."""
    return pd.read_csv(FIXTURE_PATH)


# ---------------------------------------------------------------------------
# Tests for load_per_vessel
# ---------------------------------------------------------------------------


def test_load_falls_back_to_fixtures():
    """load_per_vessel() returns fixture data when per_vessel.csv is absent."""
    df = load_per_vessel()  # data/processed/per_vessel.csv should not exist
    assert len(df) == 5
    assert df["vessel_id"].iloc[0] == 10102950


def test_loaded_df_has_all_required_columns():
    """Loaded DataFrame contains every column in the contract."""
    df = load_per_vessel()
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing column: {col}"


def test_checkpoint_vessel_final_cost():
    """Vessel 10102950 (DISTILLATE FUEL) has final_cost close to $880,688."""
    df = load_per_vessel()
    row = df.loc[df["vessel_id"] == 10102950].iloc[0]
    assert abs(row["final_cost"] - 880688) < 100


# ---------------------------------------------------------------------------
# Tests for validate_per_vessel
# ---------------------------------------------------------------------------


def test_validate_fixture_returns_expected_errors(fixture_df):
    """5-row fixture should fail production checks (108 rows, 8 fuels, DWT)."""
    ok, errors = validate_per_vessel(fixture_df)
    assert not ok, "5-row fixture should not pass production validation"
    # Must flag row count
    assert any("108" in e for e in errors), f"Expected row-count error, got: {errors}"
    # Must flag fuel type count
    assert any("fuel type" in e.lower() for e in errors), f"Expected fuel-type error, got: {errors}"
    # Must flag DWT sum
    assert any("DWT" in e for e in errors), f"Expected DWT error, got: {errors}"


# ---------------------------------------------------------------------------
# Tests for error handling
# ---------------------------------------------------------------------------


def test_load_raises_on_missing_columns():
    """load_per_vessel raises ValueError when required columns are absent."""
    # Create a CSV missing most columns
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as tmp:
        tmp.write("vessel_id,dwt\n")
        tmp.write("123,50000\n")
        tmp_path = tmp.name

    with pytest.raises(ValueError, match="Missing required columns"):
        load_per_vessel(path=tmp_path)

    Path(tmp_path).unlink(missing_ok=True)
