# Component Tests — Guardrails

> Tests the HTTP API layer with a real aiohttp server and real DB.
> Business logic is verified in `tests/unit/` — do not duplicate it here.

## What to Test Here

- HTTP routing, auth decorators, request/response serialization.
- Behavior differences between roles (superadmin vs. user keypair).
- Error responses for invalid inputs at the API boundary.

## Core Fixtures

**`create_app_and_client` (`AppBuilder`)** — spins up a real aiohttp server with selective
`cleanup_contexts`. Returns `(app, client)` via the `AppBuilder` protocol:
```python
async def test_something(create_app_and_client: AppBuilder) -> None:
    app, client = await create_app_and_client(...)
```

**`get_headers(keypair, method, path, ...)`** — generates signed HMAC auth headers.
- NEVER construct auth headers manually — always use this fixture.

## No `@pytest.mark.integration` Marker

Component tests run whenever a DB is available — do not add `@pytest.mark.integration`.
That marker is for `tests/integration/` only.

## BUILD Files

- Every new subdirectory needs a `BUILD` file with `python_tests()`.

## What Does NOT Belong Here

- Business logic assertions (service behavior) → `tests/unit/`.
- Full E2E user workflows (create → list → delete) → `tests/integration/`.
- Raw `aiohttp.ClientSession` usage — always go through the provided fixtures.
