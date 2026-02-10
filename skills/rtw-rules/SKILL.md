---
description: RTW validation rules engine and testing conventions
globs:
  - "rtw/rules/**"
  - "rtw/validator.py"
  - "tests/**"
---

# RTW Rules Engine & Testing

## Rules Engine Guidelines

- NEVER invent or guess fare rule constraints. All rules derive from IATA Rule 3015.
- Before modifying any rule, read `01-fare-rules.md` (project root) for the authoritative source text.
- For optimization context, see `12-rtw-optimization-guide.md` (project root).
- Each rule is a function in a separate file: `segments.py`, `carriers.py`, `direction.py`, etc.
- Rules return a list of `RuleResult` with severity: `error` (blocks validation) or `warning` (informational).
- The validator (`rtw/validator.py`) builds a `ValidationContext` then calls each rule. Rules do NOT call each other.
- Continent assignments use `rtw/continents.py` overrides (e.g., Egypt = EU_ME, Guam = Asia). Never hardcode continent for an airport.
- Test rule changes with: `uv run pytest tests/test_rules/ -x`

## Testing Conventions

- NEVER use mocks for API responses or domain logic. Tests use real data from `tests/fixtures/`.
- Mocks are ONLY acceptable for: system keyring access, ExpertFlyer HTTP sessions, and external service credentials.
- Test files mirror source structure: `rtw/cost.py` → `tests/test_cost.py`, `rtw/rules/segments.py` → `tests/test_rules/test_segments.py`
- Use `pytest.approx()` for floating-point comparisons (costs, distances, percentages).
- Fixtures live in `tests/fixtures/` as YAML files. Load them with `Path(__file__).parent / "fixtures" / "name.yaml"`.
- Mark slow tests with `@pytest.mark.slow`, integration tests with `@pytest.mark.integration`.
- Run focused: `uv run pytest tests/test_cost.py -x` (one file, stop on first failure).
- Run fast: `uv run pytest -m "not slow and not integration" -x`
- All models are Pydantic v2 — test serialization with `model_dump(mode="json")` and `model_validate(data)`.
