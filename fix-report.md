# Fix Report: BA-4993 (Agent Lifecycle Test Relocation)

## Changes Made

| Item | Action | Notes |
|------|--------|-------|
| `tests/component/agent/test_agent_lifecycle.py` | Deleted | Moved to unit test directory |
| `tests/unit/manager/services/agent/test_agent_lifecycle.py` | Created | Direct port of the component test |
| `tests/unit/manager/services/agent/conftest.py` | Created | Infrastructure + lifecycle fixtures |
| `tests/unit/manager/services/agent/BUILD` | Updated | Added `python_test_utils()` for conftest.py |
| `tests/component/agent/conftest.py` | Updated | Removed lifecycle-specific fixtures |

## Rationale

The test file directly invokes `AgentService` methods (`mark_agent_exit`,
`handle_heartbeat`, `watcher_agent_start/stop/restart`) — it does not test
through the HTTP API layer.  Per the project's test classification guidelines
(`tests/component/CLAUDE.md`), component tests must exercise the HTTP layer.
Tests that call service/repository methods directly belong in `tests/unit/`.

The new conftest at `tests/unit/manager/services/agent/conftest.py` overrides
the `database_engine` guard defined in `tests/unit/manager/services/conftest.py`
and provides real DB + Valkey fixtures for these intentional service-integration
tests.

## Verification Results

| Criterion | Result |
|-----------|--------|
| `pants lint tests/unit/manager/services/agent/::` | PASS |
| `pants check tests/unit/manager/services/agent/::` | PASS (mypy: no issues in 3 source files) |
| `pants test tests/unit/manager/services/agent/test_agent_lifecycle.py` | PASS (21.75s) |
| `tests/component/agent/test_agent_lifecycle.py` no longer exists | CONFIRMED |
| No `tests/component/` files import `ai.backend.manager.services.agent.actions.*` | CONFIRMED |
