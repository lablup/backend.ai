---
name: test-guide
description: Test-writing guide for Backend.AI: propose success/exception/edge scenarios first, refine them with the user, then implement while reporting per-scenario verification status. Covers fixtures, with_tables, mock repositories, pants test, optional TDD cadence.
tags:
  - testing
  - test-scenarios
  - pytest
  - fixtures
  - tdd
---

# Test guide

Write tests by agreeing on scenarios first, then verifying each one as you implement. The center of gravity is the **scenario list and its verification status**, not a fixed Red-Green-Refactor cadence. That cadence is one valid way to write the tests; see Writing tests.

## Propose scenarios first

Before writing code or tests, draft the scenarios and get the user's input:

1. **Draft** success, exception and edge scenarios from the requirement.
2. **Present them to the user** for review. The user adds missing cases and corrects expectations.
3. **Confirm** the merged list. It is the contract for what "done" means.

```markdown
## Test Target: {Feature}

### Success
1. {primary case} → {expected}
2. {edge case that should succeed} → {expected}

### Exception
1. {invalid input} → raises {ErrorType}
2. {not found} → raises {ErrorType}
3. {boundary} → {empty/default behavior}
```

### How to derive scenarios

Walk these axes. Every one that applies to the feature becomes one or more scenarios.

| Axis | Ask | Example scenario |
|---|---|---|
| Happy path | What is the primary success? | valid input → entity created |
| Variations | Other valid inputs or states? | optional field omitted → default applied |
| Not found | A referenced entity is missing? | unknown id → raises `XxxNotFound` |
| Validation | Invalid or malformed input? | negative quantity → raises `InvalidArgument` |
| Conflict or state | Duplicate, or wrong current state? | create existing name → raises `XxxConflict` |
| Permission | Caller lacks rights? | non-admin → 403 or raises `Forbidden` |
| Boundary | Empty, zero, max, end of page? | offset past total → empty list |
| Idempotency or concurrency | Repeated or parallel calls? | re-run → no duplicate side effect |

Pull exception scenarios from the domain rules and the `BackendAIError` subclasses the code can raise. See `manager/errors/AGENTS.md`. Every scenario names a concrete expected outcome or error type. "Should fail" is not specific enough to test.

Propose first, because the user catches missing cases far faster than you can reverse-engineer them from code. The agreed list also prevents scope drift.

## Verify scenarios collaboratively

As you implement, report the status of each scenario back to the user and keep it visible:

| Scenario | Test | Status |
|---|---|---|
| returns record when present | `test_returns_record` | ✅ pass |
| raises NotFound when missing | `test_missing_raises` | ✅ pass |
| pagination past end | none | ⬜ not covered yet |

- Surface gaps (`not covered`) explicitly. Do not silently skip a scenario.
- When the user adds a scenario mid-work, append it to the list and the table.
- A scenario is done only when its test exists and passes.

## Writing tests

One scenario is one test. Arrange (fixtures), act (call), assert.

```python
class TestFeature:
    @pytest.fixture
    async def scenario_data(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DataRow, None]:
        # setup with with_tables: see tests/AGENTS.md
        yield data

    async def test_returns_record_when_present(
        self, repository: FeatureRepository, scenario_data: DataRow
    ) -> None:
        result = await repository.method(scenario_data.id)
        assert result.field == expected
```

- **Fixtures** - name by scenario (`domain_with_record`), return complete data, and type as `AsyncGenerator[T, None]`.
- **Repositories and models** - use a real DB via `with_tables`. Include FK dependencies and clean up child before parent. See `tests/AGENTS.md`.
- **Services and handlers** - unit tests with mocked repositories, to isolate business logic.
- **Types** - annotate everything. Test functions return `-> None`.
- **TDD (optional cadence)** - write the failing test first, confirm it fails for the right reason (`ImportError` or `AttributeError`), implement the minimum, then refactor while green.

## Run and verify

Verify against the tests you added or changed, not a transitive sweep.

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
- Fix all lint, type and test errors. Do not use `# noqa`, `# type: ignore` or skip. See `BUILDING.md`.

## Related documents

- `tests/AGENTS.md` - Testing guidelines, `with_tables`, strategies
- `/repository-guide`, `/service-guide`, `/api-guide` - Layer patterns under test
- `BUILDING.md` - Quality enforcement
