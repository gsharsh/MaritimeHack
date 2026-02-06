# Codebase Concerns

**Analysis Date:** 2026-02-06

## Tech Debt

**Silent fallbacks on missing configuration:**
- Issue: If `global_params.yaml` is missing, code continues with empty dict `{}`, producing silently wrong results (zero ownership cost, default fuel prices)
- Files: `run.py` (lines 56-59), `src/data_loader.py` (lines 86-93)
- Why: Graceful degradation for rapid development
- Impact: Users get incorrect optimization results without any error
- Fix approach: Raise error or require explicit `--no-params` flag to run without global parameters

**Hardcoded load factors and constants:**
- Issue: Load factors hardcoded as `{"me": 0.8, "ae": 0.5, "ab": 0.3}` without documentation or configurability
- Files: `src/cost_model.py` (line 24), GWP multipliers at lines 44-45
- Why: Quick implementation for hackathon
- Impact: Cannot tune load factors without code changes
- Fix approach: Move to `config/params.yaml` or `global_params.yaml`

**Missing global_params.yaml:**
- Issue: Only `.example` template exists at `data/global_params/global_params.yaml.example`, no actual config
- Files: `data/global_params/`
- Why: Template provided but actual values not committed
- Impact: New users/runs produce incorrect results without setup
- Fix approach: Create actual `global_params.yaml` with values from `given_data/calculation_factors.xlsx`

## Known Bugs

**Potential type mismatch in greedy safety loop:**
- Symptoms: Possible ValueError in `.remove()` call if vessel_id types differ (numpy int64 vs Python int)
- Trigger: When safety constraint causes ship removal during `select_fleet_greedy()`
- File: `src/optimization.py` (lines 105-114)
- Workaround: Not observed in current dataset but possible with different data
- Root cause: No type normalization on vessel_id column

## Security Considerations

**No significant security risks detected:**
- No hardcoded secrets or credentials in codebase
- No network/API calls
- No user input beyond CLI arguments and file paths
- `.env` in `.gitignore` (good practice even though not used)

## Performance Bottlenecks

**iterrows() in main pipeline:**
- Problem: Uses `for _, row in df.iterrows()` to compute per-ship costs
- Files: `run.py` (line 72), `src/optimization.py` (line 98)
- Measurement: Not profiled, but `vessel_movements_dataset.csv` has 13,000+ records
- Cause: iterrows() is slow; pandas recommends vectorized operations or itertuples()
- Improvement path: Vectorize cost calculations using DataFrame operations instead of row-by-row iteration

## Fragile Areas

**Cost model silent defaults:**
- File: `src/cost_model.py` (lines 104-105)
- Why fragile: Falls back to "default" fuel type if key missing from emission factors dict, producing wrong costs silently
- Common failures: Wrong fuel type name in data → incorrect emission/cost calculation
- Safe modification: Add validation that fuel types in ship data match keys in global params
- Test coverage: `ship_total_cost_usd()` (the integrating function) is not tested

**Greedy fleet selection safety enforcement:**
- File: `src/optimization.py` (lines 105-114)
- Why fragile: While loop that drops worst-safety ships could create oscillation or skip ships
- Common failures: Ships removed then re-added if DWT drops too low
- Safe modification: Add tests for edge cases before modifying algorithm
- Test coverage: `select_fleet_greedy()` has no unit tests

## Scaling Limits

**Single-process execution:**
- Current capacity: Handles 13,000 AIS records in reasonable time
- Limit: Very large fleets (100k+) would be slow due to iterrows()
- Symptoms at limit: Long execution time, high memory usage
- Scaling path: Vectorize pandas operations, or use optional PuLP/OR-Tools solvers

## Dependencies at Risk

**Minimal dependency risk:**
- pandas and pyyaml are stable, well-maintained packages
- pytest is actively maintained
- DeprecationWarning from dateutil (transitive dependency) about `utcfromtimestamp()` - cosmetic only

## Missing Critical Features

**No actual global_params.yaml:**
- Problem: Template exists but actual values not populated from hackathon data
- Current workaround: Code runs with defaults/zeros
- Blocks: Accurate cost calculations
- Implementation complexity: Low - extract values from `given_data/calculation_factors.xlsx`

## Test Coverage Gaps

**Core optimization algorithm untested:**
- What's not tested: `select_fleet_greedy()` - the main optimization function
- Risk: Algorithm bugs (constraint violations, suboptimal selection) go undetected
- Priority: High
- Difficulty to test: Medium - needs realistic test fixtures

**Ship total cost integration untested:**
- What's not tested: `ship_total_cost_usd()` - combines all cost components
- Risk: Integration errors between cost components
- Priority: High
- Difficulty to test: Low - just needs proper input fixtures

**Data loading completely untested:**
- What's not tested: `load_ships()`, `load_vessel_movements_ships()`, `load_global_params()`
- Risk: Column mapping, type conversion, or validation errors undetected
- Priority: Medium
- Difficulty to test: Medium - needs test CSV/YAML fixtures

**Missing test files:**
- No `tests/test_data_loader.py`
- No `tests/test_sensitivity.py`
- No `tests/test_utils.py`

---

*Concerns audit: 2026-02-06*
*Update as issues are fixed or new ones discovered*
