---
name: test-guide
description: Test-writing guide for Backend.AI — propose success/exception/edge scenarios first, refine them with the user, then implement while reporting per-scenario verification status. Covers fixtures, with_tables, mock repositories, pants test, optional TDD cadence.
tags:
  - testing
  - test-scenarios
  - pytest
  - fixtures
  - tdd
---

# Test Guide

Write tests by agreeing on scenarios first, then verifying each one as you implement. The center of gravity is the **scenario list and its verification status** — not a fixed Red-Green-Refactor cadence (that is one valid way to write the tests; see §3).

## 1. Propose scenarios first

Before writing code or tests, draft the scenarios and get the user's input:

1. **Draft** success / exception / edge scenarios from the requirement.
2. **Present them to the user** for review — they add missing cases and correct expectations.
3. **Confirm** the merged list. It is the contract for what "done" means.

```markdown
## Test Target: {Feature}

### Success
1. {primary case} -> {expected}
2. {edge case that should succeed} -> {expected}

### Exception
1. {invalid input} -> raises {ErrorType}
2. {not found} -> raises {ErrorType}
3. {boundary} -> {empty/default behavior}
```

### How to derive scenarios

Walk these axes — every one that applies to the feature becomes one or more scenarios:

| Axis | Ask | Example scenario |
|------|-----|------------------|
| Happy path | What is the primary success? | valid input -> entity created |
| Variations | Other valid inputs/states? | optional field omitted -> default applied |
| Not found | A referenced entity is missing? | unknown id -> raises `XxxNotFound` |
| Validation | Invalid/malformed input? | negative quantity -> raises `InvalidArgument` |
| Conflict / state | Duplicate, or wrong current state? | create existing name -> raises `XxxConflict` |
| Permission | Caller lacks rights? | non-admin -> 403 / raises `Forbidden` |
| Boundary | Empty, zero, max, end-of-page? | offset past total -> empty list |
| Idempotency / concurrency | Repeat or parallel calls? | re-run -> no duplicate side effect |

Pull exception scenarios straight from the domain rules and the `BackendAIError` subclasses the code can raise (see `manager/errors/AGENTS.md`). Every scenario must name a concrete expected outcome or error type — "should fail" is not specific enough to test.

Propose first because the user catches missing cases far faster than reverse-engineering them from code, and the agreed list prevents scope drift.

## 2. Verify scenarios collaboratively

As you implement, report each scenario's status back to the user and keep it visible:

| Scenario | Test | Status |
|----------|------|--------|
| returns record when present | `test_returns_record` | ✅ pass |
| raises NotFound when missing | `test_missing_raises` | ✅ pass |
| pagination past end | — | ⬜ not covered yet |

- Surface gaps (`not covered`) explicitly — never silently skip a scenario.
- When the user adds a scenario mid-work, append it to the list and the table.
- A scenario is done only when its test exists and passes.

## 3. Writing tests

One scenario = one test. Arrange (fixtures) → Act (call) → Assert.

```python
class TestFeature:
    @pytest.fixture
    async def scenario_data(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DataRow, None]:
        # setup with with_tables — see tests/AGENTS.md
        yield data

    async def test_returns_record_when_present(
        self, repository: FeatureRepository, scenario_data: DataRow
    ) -> None:
        result = await repository.method(scenario_data.id)
        assert result.field == expected
```

- **Fixtures**: name by scenario (`domain_with_record`), return complete data, type as `AsyncGenerator[T, None]`.
- **Repositories / models**: real DB via `with_tables`; include FK deps, clean up child → parent. See `tests/AGENTS.md`.
- **Services / handlers**: unit tests with mocked repositories — isolate business logic.
- **Types**: annotate everything; test functions return `-> None`.
- **TDD (optional cadence)**: write the failing test first (confirm it fails for the right reason — `ImportError`/`AttributeError`), implement the minimum, then refactor while green.

## 4. Run and verify

Verify against the tests you added or changed — not a transitive sweep.

```bash
# the specific test(s) for the scenarios you implemented
pants test tests/manager/repositories/test_feature.py
pants test tests/.../test_feature.py::TestFeature::test_case

# quality, scoped to your change
pants fmt --changed-since=HEAD~1
pants fix --changed-since=HEAD~1
pants lint --changed-since=HEAD~1
pants check --changed-since=HEAD~1
pants test --changed-since=HEAD~1
```

- Add a BUILD file with `python_tests()` to new test directories.
- Fix all lint/type/test errors — never `# noqa` / `# type: ignore` / skip. See `BUILDING.md`.

## Cross-References

- `tests/AGENTS.md` — testing guidelines, `with_tables`, strategies
- `/repository-guide`, `/service-guide`, `/api-guide` — layer patterns under test
- `BUILDING.md` — quality enforcement
