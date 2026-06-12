# Testing guidelines — Guardrails

> For background and rationale, see `CONTEXTS.md` in this directory. For the TDD workflow, patterns, and code examples, see the `/tdd-guide` skill; for BUILD policies, see `BUILDING.md`.

## Which directory to use

| Test target | Directory |
|-------------|----------|
| Service / handler logic (mocked) | `tests/unit/{component}/` |
| Repository / Model (real DB, `with_tables`) | `tests/unit/{component}/repositories/` |
| HTTP API layer (real aiohttp server + DB) | `tests/component/{component}/` |
| E2E user scenarios (Client SDK v2) | `tests/integration/` |

Each directory keeps its setup patterns in its own `AGENTS.md`.

## Test strategy

- **Repository / Model**: Verify real interactions (queries, transactions, constraints) with a real DB (`ai.backend.testutils.db.with_tables`) and real Redis. Do NOT mock DB calls.
- **Service / Handler / Controller**: Mocked unit tests. Mock repository calls and external dependencies with `unittest.mock.AsyncMock` and verify the business logic.
- For the rationale behind the distinction, see `CONTEXTS.md`.

## What to test (behavior, not implementation)

Test the observable contract — a good test is one that survives a refactor as long as the behavior is the same.

- **Do test**: Constraints/preconditions the code enforces (e.g., empty scope → `EmptySearchScopeError`), the promises a method makes to its callers (abstraction guarantees), and actual results (with `with_tables`: create→read-back, update reflected, purge removed, scoped filtering).
- **Do NOT test**: Implementation details, spying on internal call wiring, or delegation logic already verified by a lower layer. (For examples, see `CONTEXTS.md`)

## Test structure

- Group by the unit under test (class/module/function) into test classes.
- Express test conditions as fixtures, not inline setup.
- Keep functions concise: Arrange (fixture) → Act → Assert.
- Do NOT import from other test files — put shared utilities in `conftest.py` or `ai.backend.testutils`.
- For patterns and examples, see the `/tdd-guide` skill.

## `with_tables` core rules

- Include all `Row` dependencies (SQLAlchemy string relationships — if `RowA` relates to `RowB`, include both).
- In FK order (parents first). Follow each Row's `relationship()` to trace the chain.
- Import all related Rows without `# noqa: F401` and put them into `with_tables`.

## Test type hints

- All test code has complete type annotations: fixture references, function returns, and test functions (`-> None`).
  Use `typing.Protocol`/`TypedDict` for mocks when needed.

## BUILD files

- Add a `BUILD` to every new test directory: `python_tests()` for test modules, `python_testutils()` for shared utilities.
- Do NOT declare dependencies explicitly — Pants infers them from imports. For details, see `BUILDING.md`.
