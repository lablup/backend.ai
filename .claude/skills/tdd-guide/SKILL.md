---
name: tdd-guide
description: Test-Driven Development workflow guide for Backend.AI (Red-Green-Refactor cycle, scenario definition, pytest fixtures, with_tables, mock repositories, pants test)
invoke_method: automatic
auto_execute: false
enabled: true
---

# TDD Workflow Guide

This skill guides you through Test-Driven Development (TDD) workflow for Backend.AI.

## Purpose

When implementing new features or fixing bugs:
1. Define test scenarios (success + exception cases)
2. Write failing tests first
3. Implement minimum code to pass tests
4. Refactor with confidence

## Parameters

This skill takes no parameters. It guides you through the TDD cycle.

## TDD Cycle Overview

```
1. Define Scenarios → 2. Write Tests → 3. Verify Failure → 4. Implement → 5. Pass → 6. Refactor
                                                                            ↑______________|
```

**Key Principle: Red → Green → Refactor**
- Red: Write a failing test
- Green: Make it pass with minimum code
- Refactor: Improve code while keeping tests green

## Step 1: Define Test Scenarios

**Before writing any code, document:**
1. Success scenarios (expected behavior)
2. Exception scenarios (error cases, edge cases)

### Scenario Template

```markdown
## Test Target: {Feature/Component Name}

### Success Scenarios
1. {Primary success case}
2. {Secondary success case}
3. {Edge case that should succeed}

### Exception Scenarios
1. {Invalid input} → Expected error: {ErrorType}
2. {Constraint violation} → Expected error: {ErrorType}
3. {Resource not found} → Expected error: {ErrorType}
4. {Boundary condition} → Expected behavior: {empty result/default value}
```

### Example: Domain Fair Share Query

```markdown
## Test Target: DomainFairShare Entity Retrieval

### Success Scenarios
1. Domain with fair share record → Return domain with details populated
2. Domain without fair share record → Return domain with details=None
3. Mixed domains (some with/without records) → Return all with correct details

### Exception Scenarios
1. Non-existent resource_group → Raise ResourceGroupNotFound
2. Resource group with no domains → Raise NoDomainsInResourceGroup
3. Pagination offset > total_count → Return empty list (total_count indicates end)
```

## Step 2: Write Failing Tests

**Write tests BEFORE implementation.**

### Test Structure Pattern

**Test Class:**
```python
import pytest

class TestFeature:
    """Tests for Feature component."""

    @pytest.fixture
    async def scenario_data(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[DataRow, None]:
        """Fixture describing scenario."""
        # Setup with with_tables - see tests/CLAUDE.md
        yield data
        # Cleanup

    async def test_expected_behavior(
        self,
        repository: FeatureRepository,
        scenario_data: DataRow,
    ) -> None:
        """Test success: Expected behavior description."""
        result = await repository.method(scenario_data.id)
        assert result.field == expected_value
```

**See `tests/CLAUDE.md` for:**
- `with_tables` usage patterns
- Fixture setup examples
- Database test guidelines

### Test Guidelines

**Fixtures:**
- Name describes scenario: `domain_with_record`, `mock_provisioner_failure`
- Return complete data, not factory functions
- Use `AsyncGenerator[ReturnType, None]` for async fixtures

**Test Functions:**
- Name describes expected behavior: `test_returns_domain_with_record`
- Focus on: Arrange (fixtures) → Act (call) → Assert (verify)
- One test = one scenario

**Type Hints:**
- All fixtures, parameters, returns annotated
- Test functions return `-> None`

**Database Tests:**
- Use `with_tables` for repositories/models (see `tests/CLAUDE.md` for detailed usage)
- Include all FK dependencies in proper order
- Clean up in reverse order (child → parent)

## Step 3: Verify Test Failure

**Run tests and confirm they fail for the right reason.**

```bash
# Run specific test file
pants test tests/manager/repositories/test_feature.py

# Run specific test
pants test tests/manager/repositories/test_feature.py::TestFeature::test_returns_domain_with_record
```

**Expected failure reasons:**
- `ImportError` - Component doesn't exist yet (good!)
- `AttributeError` - Method not implemented (good!)
- `AssertionError` - Logic incorrect (need to verify this is expected)

**If tests pass unexpectedly:**
- Verify test logic is correct
- Check if feature already implemented
- Ensure test actually exercises the code

## Step 4: Implement Minimum Code

**Write the simplest code that makes tests pass.**

### Implementation Principles

1. **Concise and focused**
   - Each function has clear, single purpose
   - Keep implementations brief (< 30 lines per function)
   - Extract helpers when logic exceeds ~20 lines

2. **No premature optimization**
   - Don't add features not covered by tests
   - Don't add configurability not required
   - Don't add error handling for impossible cases

3. **Complete type annotations**
   - All parameters and returns typed
   - Use domain types (SessionId, not str)
   - No `Any` types

4. **Explicit error handling**
   - Raise specific exceptions (inherit from BackendAIError)
   - Never silent failures (return None/empty)
   - Provide clear error messages

**See implementation examples:**
- `repositories/fair_share/repository.py` - Complete repository
- `services/storage_namespace/service.py` - Service implementation

## Step 5: Run Tests (Green)

**Verify all tests pass.**

```bash
# Run tests for changed code
pants test --changed-since=HEAD~1 --changed-dependents=transitive

# Run specific test class
pants test tests/manager/repositories/test_feature.py::TestFeature
```

**All tests must pass:**
- Success scenarios ✓
- Exception scenarios ✓
- No regressions in other tests ✓

**If tests fail:**
- Check failure reason (logic error, missing case)
- Fix implementation
- Re-run tests
- Do NOT skip failing tests

## Step 6: Refactor

**Improve code while keeping tests green.**

### Refactoring Checklist

- [ ] Extract long functions (> 30 lines)
- [ ] Remove duplication
- [ ] Improve naming
- [ ] Add missing type hints
- [ ] Simplify complex conditionals
- [ ] Apply repository base patterns (if applicable)

### Run Quality Checks

**After refactoring, always run:**

```bash
# Format code
pants fmt ::

# Fix auto-fixable issues
pants fix ::

# Check linting
pants lint --changed-since=HEAD~1

# Check types
pants check --changed-since=HEAD~1

# Run tests
pants test --changed-since=HEAD~1 --changed-dependents=transitive
```

**Fix all errors - never suppress:**
- Do NOT use `# noqa` to suppress linter warnings
- Do NOT use `# type: ignore` to suppress type errors
- Fix root cause instead of suppressing

See `BUILDING.md` for quality enforcement details.

**Refactoring principles:**
- Extract long functions into smaller, focused helpers
- Add comprehensive type hints
- Use descriptive names
- Improve readability without changing behavior

## Test Strategy by Component

**Choose testing approach based on what you're testing:**

### Repositories & Models
- **Real database** with `with_tables` (detailed usage in `tests/CLAUDE.md`)
- Test actual queries, transactions, constraints
- Verify FK relationships work

### Services & Handlers
- **Unit tests with mocking**
- Mock repository calls
- Focus on business logic

**See examples:** `tests/unit/manager/services/`

### Why This Distinction?
- Repositories: Integration points where actual behavior matters
- Services: Logic verification where isolation improves speed

See `tests/CLAUDE.md` for detailed testing strategies.

## TDD Workflow Examples

**See complete examples in:**
- `tests/unit/manager/repositories/` - Repository tests with `with_tables`
- `tests/unit/manager/services/` - Service tests with mocking
- `tests/CLAUDE.md` - Testing patterns and strategies

## Integration with Repository Development

When implementing repositories, combine with `/repository-guide`:

**1. Read repository-guide:**
- Understand base patterns
- Review existing implementations

**2. Follow TDD workflow:**
- Define scenarios (this skill)
- Write tests with `with_tables`
- Implement using base utilities
- Refactor

**Example workflow:**
```bash
# 1. Study repository patterns
Read /repository-guide

# 2. Define test scenarios (Step 1)
# Document in .claude/tasks/{feature}.md

# 3. Write failing tests (Step 2)
# Create tests/manager/repositories/test_{feature}.py
# Add BUILD file with python_tests()

# 4. Run tests (Step 3)
pants test tests/manager/repositories/test_{feature}.py

# 5. Implement using base patterns (Step 4)
# Apply Querier, BatchQuerier, Creator, etc.

# 6. Run tests (Step 5)
pants test tests/manager/repositories/test_{feature}.py

# 7. Refactor + quality checks (Step 6)
pants fmt ::
pants check --changed-since=HEAD~1
pants lint --changed-since=HEAD~1
```

## Common TDD Mistakes

### Mistake 1: Writing Implementation First
❌ **Wrong:** Implement → Write tests to verify
✅ **Correct:** Write tests → Implement to pass

### Mistake 2: Testing Implementation Details
❌ **Wrong:** Assert internal method calls, private state
✅ **Correct:** Test public behavior, outcomes

### Mistake 3: Large Test/Implementation Cycles
❌ **Wrong:** Write 20 tests → Implement everything
✅ **Correct:** One test → Small implementation → Repeat

### Mistake 4: Skipping Failure Verification
❌ **Wrong:** Write test → Implement → Run (pass)
✅ **Correct:** Write test → Run (fail) → Implement → Run (pass)

### Mistake 5: Suppressing Quality Errors
❌ **Wrong:** Add `# noqa` or `# type: ignore`
✅ **Correct:** Fix root cause

## Cross-References

- `tests/CLAUDE.md` - Testing guidelines and strategies
- `/repository-guide` - Repository implementation patterns
- `BUILDING.md` - Quality enforcement and build commands
- `src/ai/backend/manager/repositories/README.md` - Repository layer overview

## Summary

**TDD Cycle:**
1. **Define scenarios** (success + exceptions)
2. **Write failing tests** (with fixtures)
3. **Verify failure** (red state)
4. **Implement minimum** (concise, typed, explicit errors)
5. **Pass tests** (green state)
6. **Refactor** (improve while keeping green)

**Quality Rules:**
- Run `pants fmt`, `pants fix` after refactoring
- Run `pants lint`, `pants check` before commit
- Fix all errors - never suppress
- Tests must pass - never skip

**Test Strategy:**
- Repositories: Real DB with `with_tables`
- Services: Unit tests with mocking
- Always add BUILD file to test directories

**Remember:** Red → Green → Refactor → Repeat
