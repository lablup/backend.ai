# tests/manager/ — Legacy Directory

> This directory is legacy. Do NOT add new test files or subdirectories here.

## Current Contents

- `tests/manager/models/` — legacy ORM model tests
- `tests/manager/repositories/` — legacy repository DB tests

## Where to Add New Tests Instead

| What you want to test | Where to add it |
|-----------------------|----------------|
| New repository / model (real DB) | `tests/unit/manager/repositories/` |
| New service / handler (mocking) | `tests/unit/manager/services/` |
| New API endpoint (real server) | `tests/component/manager/api/` |

## Existing Tests

- Modifying existing tests in this directory is allowed.
- Existing pattern: `database_engine` fixture + `with_tables` (same as `tests/unit/`).
- Do NOT create new `.py` files or subdirectories here.
