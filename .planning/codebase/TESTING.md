# Testing Patterns

**Analysis Date:** 2026-02-06

## Test Framework

**Runner:**
- pytest >=7.0.0
- No pytest.ini or pyproject.toml config

**Assertion Library:**
- Built-in `assert` statements
- `pytest.approx()` for floating-point comparisons

**Run Commands:**
```bash
pytest                                    # Run all tests
pytest tests/test_cost_model.py          # Single file
pytest -v                                 # Verbose output
```

## Test File Organization

**Location:**
- `tests/` directory at project root (separate from source)
- Not co-located with source files

**Naming:**
- `test_module_name.py` following pytest conventions

**Structure:**
```
tests/
├── __init__.py
├── test_cost_model.py       # Tests for src/cost_model.py (32 lines)
└── test_optimization.py     # Tests for src/optimization.py (46 lines)
```

## Test Structure

**Suite Organization:**
```python
import pytest
import pandas as pd
from src.cost_model import fuel_consumption_tonnes

def test_fuel_consumption_tonnes():
    row = pd.Series({...})
    result = fuel_consumption_tonnes(row, voyage_hours=48.0)
    assert result == pytest.approx(expected, rel=1e-3)
```

**Patterns:**
- Direct function calls with simple test data
- `pytest.approx()` for floating-point comparisons
- Fixtures via `@pytest.fixture` for shared test data
- No arrange/act/assert comments (compact style)
- One assertion focus per test

## Mocking

**Framework:**
- No mocking used
- Direct function calls with inline test data

**What to Mock (if needed):**
- File system operations (CSV/YAML loading)
- Not currently mocked - tests use hardcoded data

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def sample_ships():
    return pd.DataFrame({
        "vessel_id": ["A", "B", "C"],
        "dwt": [50000, 60000, 40000],
        "total_cost_usd": [100000, 120000, 80000],
        "safety_score": [4, 3, 5],
        "main_engine_fuel_type": ["LNG", "Methanol", "Diesel"],
        # ... additional columns
    })
```

**Location:**
- Fixtures defined in test files (`tests/test_optimization.py`)
- Inline test data in individual test functions (`tests/test_cost_model.py`)
- No shared fixtures directory

## Coverage

**Requirements:**
- No formal coverage target
- No coverage tool configured (no pytest-cov)

**Current State:**
- Cost model: 3 functions tested (fuel_consumption, amortized_ownership, risk_premium)
- Optimization: 4 functions tested (validate_fleet x2, total_cost_and_metrics, format_outputs)
- Missing: `ship_total_cost_usd()`, `select_fleet_greedy()`, all data_loader functions, sensitivity, utils

## Test Types

**Unit Tests:**
- Test individual functions in isolation
- Use hardcoded/fixture data (no real files)
- 7 test functions total

**Integration Tests:**
- None

**E2E Tests:**
- None

## Common Patterns

**Numeric Testing:**
```python
def test_fuel_consumption_tonnes():
    row = pd.Series({"P": 10000, "ael": 500, "abl": 200, ...})
    result = fuel_consumption_tonnes(row, voyage_hours=48.0)
    assert result == pytest.approx(expected_value, rel=1e-3)
```

**Validation Testing:**
```python
def test_validate_fleet_demand():
    ok, msgs = validate_fleet(fleet_df, cargo_demand=200000, constraints={})
    assert not ok
    assert any("DWT" in m for m in msgs)
```

**Fixture Reuse:**
```python
def test_total_cost_and_metrics(sample_ships):
    metrics = total_cost_and_metrics(sample_ships)
    assert metrics["fleet_size"] == 3
```

---

*Testing analysis: 2026-02-06*
*Update when test patterns change*
