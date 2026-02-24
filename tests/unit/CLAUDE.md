# Unit Tests — Guardrails

> For TDD workflow, see `/tdd-guide` skill. For `with_tables` patterns, see `tests/CLAUDE.md`.

## Directory Layout

Mirror `src/ai/backend/{component}/` exactly:
`tests/unit/{component}/services/`, `tests/unit/{component}/repositories/`, etc.

## Service / Handler Tests (mocking)

- Mock all repository calls with `unittest.mock.AsyncMock`.
- Do NOT spin up a real DB or real aiohttp server — that belongs in `tests/component/`.
- One test class per target class; one test function per meaningful behavior.

## Repository / Model Tests (real DB)

- Place under `tests/unit/{component}/repositories/`.
- Use `with_tables` from `ai.backend.testutils.db` with a real `database_engine` fixture.
- List all `Row` dependencies in FK order (parent before child).
- Do NOT mock DB calls — the point is to test actual queries and constraints.

## BUILD Files

- Every new test directory needs a `BUILD` file with `python_tests()`.
- Shared fixtures go in `conftest.py` — never import from sibling test files.

## What Does NOT Belong Here

- Real aiohttp server setup (`create_app_and_client`) → use `tests/component/`.
- E2E user scenarios using `BackendAIClientRegistry` → use `tests/integration/`.
