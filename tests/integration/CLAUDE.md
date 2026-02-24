# Integration Tests — Guardrails

> Full-stack E2E tests using Client SDK v2. Validates user-facing workflows end to end.

## What to Test Here

- Complete user-perspective scenarios: create → read → update → delete flows.
- Permission boundaries between roles (superadmin vs. regular user).
- Behaviors that span multiple API calls or components.

## `@pytest.mark.integration` Marker

Apply at the **class level** — required for all test classes here:
```python
@pytest.mark.integration
class TestUserLifecycle:
    async def test_full_user_lifecycle(self, admin_registry, ...) -> None:
```

## Core Fixtures

**`admin_registry`** — `BackendAIClientRegistry` with superadmin keypair.
**`user_registry`** — `BackendAIClientRegistry` with normal-user keypair.

- NEVER use raw `aiohttp.ClientSession` or hand-crafted auth headers.
- Always call the API through `BackendAIClientRegistry` methods.

## Server Setup

Integration tests use a full-stack server (`cleanup_contexts=None`, all contexts included).
Do not change `cleanup_contexts` from `None` in `server_factory` — integration tests
require all contexts running.

## Directory Structure

Keep domain-based subdirectory structure: `integration/user/`, `integration/session/`, etc.
Each subdirectory needs its own `BUILD` with `python_tests()`.

## What Does NOT Belong Here

- Unit-level assertions on service internals → `tests/unit/`.
- HTTP-layer-only checks (routing, auth decorators) → `tests/component/`.
