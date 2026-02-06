# Coding Conventions

**Analysis Date:** 2026-02-06

## Naming Patterns

**Files:**
- snake_case.py for all modules (`cost_model.py`, `data_loader.py`)
- test_module_name.py for tests (`test_cost_model.py`)

**Functions:**
- snake_case for all functions (`fuel_consumption_tonnes`, `select_fleet_greedy`)
- Verb-driven prefixes: `load_`, `compute_`, `select_`, `validate_`, `format_`, `run_`
- Unit suffixes where applicable: `_usd`, `_tonnes`, `_hours`

**Variables:**
- snake_case for variables (`cargo_demand_tonnes`, `cost_per_dwt`)
- UPPER_SNAKE_CASE for constants (`SINGAPORE_TO_AU_WEST_NM`, `REQUIRED_SHIP_COLUMNS`)
- Domain abbreviations accepted: `dwt`, `sfc`, `me`/`ae`/`ab`, `co2e`, `lcv`, `capex`, `crf`

**Types:**
- No classes used - functional/procedural style throughout
- Type hints use modern syntax: `dict[str, float]`, `list[str | int]`, `str | Path`

## Code Style

**Formatting:**
- No formatter configured (no black, no autopep8)
- 4-space indentation (Python standard)
- Lines under ~100 characters typical
- Double quotes for all strings

**Linting:**
- No linter configured (no flake8, pylint, ruff)
- No pre-commit hooks
- No mypy for type checking

## Import Organization

**Order:**
1. Standard library (`from pathlib import Path`, `from typing import Any`)
2. Third-party packages (`import pandas as pd`, `import yaml`)
3. Local imports (`from .optimization import ...`)

**Grouping:**
- No blank lines between groups (compact style)
- No explicit sorting enforced

**Path Aliases:**
- None - direct relative imports within `src/` package

## Error Handling

**Patterns:**
- Silent fallbacks: `.get()` with default values for missing config
- Print warnings for missing files, continue with empty defaults
- No try/catch in calculation pipeline
- Validation via dedicated `validate_fleet()` returning `(bool, list[str])`

**Error Types:**
- No custom error classes
- KeyError if required DataFrame columns missing (implicit)
- ValueError for type mismatches (implicit)

## Logging

**Framework:**
- `print()` statements only
- No structured logging framework

**Patterns:**
- Status messages: `print(f"Loaded {len(df)} ships")`
- Warning messages: `print(f"Warning: ...")`
- No log levels

## Comments

**When to Comment:**
- Unit conversion explanations: `# tonnes * 1000 kg * lcv MJ/kg = MJ; MJ/1000 = GJ`
- Domain references: `# GWP approx`
- Configuration notes: `# Adjust with actual route data if provided`

**Docstrings:**
- Triple-quoted strings at module and function level
- Plain English descriptions (no @param/@return tags)
- Return types documented via type hints in function signatures

**TODO Comments:**
- Not observed in current codebase

## Function Design

**Size:**
- Functions are concise (typically 5-20 lines)
- Largest functions ~40 lines (`select_fleet_greedy`)

**Parameters:**
- DataFrame rows as `pd.Series` for cost functions
- Config as `dict[str, Any]` for parameter lookups
- Paths as `str | Path` for file loading

**Return Values:**
- Explicit returns with type hints
- Tuples for validation: `(bool, list[str])`
- Dicts for metrics aggregation

## Module Design

**Exports:**
- No `__all__` defined - all public functions importable
- No barrel files or re-exports

**Organization:**
- One responsibility per module
- No classes - all modules are collections of functions
- Constants at module top level

---

*Convention analysis: 2026-02-06*
*Update when patterns change*
