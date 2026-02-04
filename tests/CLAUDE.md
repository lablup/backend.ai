# Testing Guidelines

This document provides testing patterns and best practices for Backend.AI.
For TDD workflow, see `/tdd-guide` skill.

## Test Strategy

**Use the appropriate testing approach based on the component:**

### Repositories & Models
- **Use real database connections** with `ai.backend.testutils.db.with_tables`
- **Use real Redis connections** when testing cache operations
- Test actual database interactions (queries, transactions, constraints)
- Include all Row dependencies in `with_tables` for proper FK constraints

### Services, Handlers, Controllers
- **Use unit tests with mocking**
- Mock repository calls and external dependencies
- Focus on business logic validation
- Use `unittest.mock.AsyncMock` for async mocking

**Why this distinction?**
- Repositories/Models: Integration points where actual behavior matters
- Other layers: Logic verification where isolation improves speed and clarity

## Test Structure & Organization

### Use Test Classes
Group tests by target unit (class, module, or function):

```python
class TestScheduleSessionsLifecycleHandler:
    """Tests for ScheduleSessionsLifecycleHandler."""

    async def test_all_sessions_scheduled_successfully(self, ...) -> None:
        ...

    async def test_partial_scheduling_failure(self, ...) -> None:
        ...
```

### Use Fixtures for Test Scenarios
Express test conditions through fixtures, not inline setup:

```python
@pytest.fixture
def session_with_pending_status() -> SessionData:
    return create_session(status=SessionStatus.PENDING)

@pytest.fixture
def mock_provisioner_success(mock_provisioner: AsyncMock) -> AsyncMock:
    mock_provisioner.schedule_scaling_group.return_value = ScheduleResult(...)
    return mock_provisioner

async def test_success(
    handler: ScheduleSessionsLifecycleHandler,
    session_with_pending_status: SessionData,
    mock_provisioner_success: AsyncMock,
) -> None:
    # Act
    result = await handler.execute("default", [session_with_pending_status])

    # Assert
    assert len(result.successes) == 1
```

### Keep Test Functions Concise
Focus on: Arrange (fixtures) → Act (call) → Assert (verify)

### No Cross-Test Imports
- Never import from other test files
- Shared utilities go in `conftest.py` or `ai.backend.testutils`

## Database Tests with `with_tables`

When using `with_tables` from `ai.backend.testutils.db`:

**Critical Rules:**
1. **Include all Row dependencies**: SQLAlchemy uses string-based relationships.
   If `RowA` has relationships to `RowB`, both must be in `with_tables`.
2. **Order by FK dependencies**: Parent tables before children.
3. **Trace relationship chains**: Check each Row's `relationship()` definitions.
4. **Import all related Rows**: Do NOT use `# noqa: F401` - include them in `with_tables`.

```python
@pytest.fixture
async def sample_data(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncGenerator[list[DataRow], None]:
    data = []
    async with with_tables(
        database_engine,
        [
            ParentRow,      # Parent first
            ChildRow,       # Child second (FK to Parent)
            GrandChildRow,  # Grandchild third (FK to Child)
        ],
    ) as db_sess:
        # Create test data
        parent = ParentRow(...)
        db_sess.add(parent)
        await db_sess.flush()

        child = ChildRow(parent_id=parent.id, ...)
        db_sess.add(child)
        await db_sess.flush()

        yield [parent, child]

        # Cleanup (reverse order)
        await db_sess.delete(child)
        await db_sess.delete(parent)
```

## Type Hints in Tests

**All test code must have complete type annotations:**
- Fixture references in test functions: `session: SessionRow`
- Fixture functions: `-> SessionRow` or `-> AsyncGenerator[SessionRow, None]`
- Test functions: `-> None`
- Mock objects: Use `typing.Protocol` or `typing.TypedDict` when applicable

```python
@pytest.fixture
async def sample_data(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncGenerator[list[DataRow], None]:
    ...

async def test_something(
    repository: FairShareRepository,
    sample_data: list[DataRow],
) -> None:
    ...
```

## BUILD Files for Tests

**Required for every test directory:**

```python
# tests/manager/repositories/BUILD
python_tests()
```

```python
# tests/testutils/BUILD
python_testutils()
```

**Rules:**
- Add BUILD file when creating new test directories
- Use `python_tests()` for test modules
- Use `python_testutils()` for shared utilities
- Do NOT list dependencies explicitly - Pants infers from imports

See `BUILDING.md` for detailed BUILD file policies.

## Running Tests

```bash
# Run all tests in a directory
pants test tests/manager::

# Run specific test file
pants test tests/manager/repositories/test_fair_share.py

# Run tests for changed code
pants test --changed-since=HEAD~1 --changed-dependents=transitive
```

## TDD Workflow

For complete TDD workflow (scenario definition → test writing → implementation):
- See `/tdd-guide` skill
- Includes step-by-step process and examples

## Quality Checks

**Always fix errors - never suppress:**
- Run `pants lint` and fix issues
- Run `pants check` and fix type errors
- Do NOT use `# noqa` or `# type: ignore`

See `BUILDING.md` for quality enforcement details.
