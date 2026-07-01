# Integration tests — Guardrails

> Full-stack E2E tests using Client SDK v2. Verify user-facing workflows end to end.

## What to test here

- Complete user-perspective scenarios: create → read → update → delete flows.
- Permission boundaries across roles (superadmin vs regular user).
- Behavior spanning multiple API calls or components.

## `@pytest.mark.integration` marker

Attach it at the **class level** — required on every test class here:
```python
@pytest.mark.integration
class TestUserLifecycle:
    async def test_full_user_lifecycle(self, admin_registry, ...) -> None:
```

## Core fixtures

`admin_registry` — a `BackendAIClientRegistry` with a superadmin keypair.
`user_registry` — a `BackendAIClientRegistry` with a regular user keypair.

- Do NOT use raw `aiohttp.ClientSession` or hand-built auth headers.
- Always call the API through `BackendAIClientRegistry` methods.

## Server setup

Integration tests use the full-stack server (`cleanup_contexts=None`, all contexts included).
Do NOT change `cleanup_contexts` from `None` in `server_factory` — integration tests require all
contexts to be up.

## Directory structure

Maintain a domain-based subdirectory structure: `integration/user/`, `integration/session/`, etc.
Each subdirectory needs a `BUILD` containing `python_tests()`.

## What does NOT belong here

- Unit-level assertions about service internals → `tests/unit/`.
- HTTP-layer-only checks (routing, auth decorators) → `tests/component/`.
