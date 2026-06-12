# Unit tests — Guardrails

> For the TDD workflow, see the `/tdd-guide` skill; for the `with_tables` patterns, see `tests/AGENTS.md`.

## Directory layout

Mirror `src/ai/backend/{component}/` exactly: `tests/unit/{component}/services/`,
`tests/unit/{component}/repositories/`, etc.

## Service / Handler tests (mocked)

- Mock all repository calls with `unittest.mock.AsyncMock`.
- Do NOT bring up a real DB or a real aiohttp server — that belongs to `tests/component/`.
- One test class per target class, one test function per meaningful behavior.

## Repository / Model tests (real DB)

- Place them under `tests/unit/{component}/repositories/`.
- Use `with_tables` from `ai.backend.testutils.db` together with the real `database_engine` fixture.
- List all `Row` dependencies in FK order (parents first).
- Do NOT mock DB calls — the point is to verify real queries and constraints.

## BUILD files

- Every new test directory needs a `BUILD` file containing `python_tests()`.
- Place shared fixtures in `conftest.py` — do NOT import from sibling test files.

## What does NOT belong here

- Real aiohttp server setup (`create_app_and_client`) → `tests/component/`.
- E2E scenarios using `BackendAIClientRegistry` → `tests/integration/`.
