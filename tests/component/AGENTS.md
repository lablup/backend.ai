# Component tests: Guardrails

> Test the HTTP API layer with a real aiohttp server and a real DB.
> Verify business logic in `tests/unit/`: do not duplicate it here.

## What to test here

- HTTP routing, auth decorators, request/response serialization.
- Per-role behavior differences (superadmin vs user keypair).
- Error responses for invalid input at the API boundary.

## Core fixtures

`create_app_and_client` (`AppBuilder`): starts a real aiohttp server with optional `cleanup_contexts`.
Returns `(app, client)` via the `AppBuilder` protocol:
```python
async def test_something(create_app_and_client: AppBuilder) -> None:
    app, client = await create_app_and_client(...)
```

`get_headers(keypair, method, path, ...)`: generates signed HMAC auth headers.
- Do not build auth headers yourself: always use this fixture.

## BUILD files

- Every new subdirectory needs a `BUILD` file containing `python_tests()`.

## What does not belong here

- Business logic assertions (service behavior) → `tests/unit/`.
- Full end-to-end user workflows (create → list → delete) → `tests/integration/`.
- Using raw `aiohttp.ClientSession`: always go through the provided fixtures.
