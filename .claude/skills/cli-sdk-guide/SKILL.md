---
name: cli-sdk-guide
description: Guide for implementing Backend.AI client SDK and CLI (Session, BaseFunction, @api_function, Click commands, Pydantic models, FieldSpec, output handlers, APIConfig, testing)
version: 1.0.0
dependencies:
  - api-guide
  - test-guide
tags:
  - client-sdk
  - cli
  - session
  - api-function
  - click
  - pydantic
  - output-handler
---

# CLI and SDK implementation guide

The client SDK and CLI cover session management, API functions and Click commands.

## Purpose

**SDK (software development kit):**

- A Python library for the Backend.AI REST API
- Programmatic access for integrations and automation
- Async-first, with a sync wrapper for CLI compatibility

**CLI (command line interface):**

- User-facing commands for Backend.AI operations
- Built on top of SDK functions
- Supports console and JSON output modes

Use the SDK for integrations, automation scripts and web dashboards. Use the CLI for interactive administration, shell scripts and CI/CD pipelines. Use the API directly only when the SDK does not support the operation yet.

## Architecture overview

Layers: CLI → SDK → REST API → manager

CLI commands call SDK functions through Session, which makes HTTP requests to REST API endpoints.

CLI layer:

- `ExtendedCommandGroup` - command groups with aliases and interrupt handling
- `LazyGroup` - lazy loading for faster startup
- `CLIContext` - shared state (config, output mode)
- `@pass_ctx_obj` - CLIContext injection decorator
- `FieldSpec` - output field definitions
- `BaseOutputHandler` - console and JSON formatters

SDK layer:

- `BaseFunction` - metaclass for API function classes
- `@api_function` - decorator for API methods
- `AsyncSession` - primary async HTTP session
- `Session` - sync wrapper for the CLI
- `api_session` - ContextVar for session context

Data layer:

- Request and response DTOs are Pydantic models from `common/dto/`
- `client/cli/types.py` still uses legacy attrs classes

Config layer:

- `APIConfig` - environment variables and the `.env` file
- `CLIContext` - CLI state and output handler

## SDK implementation patterns

### Session management

**AsyncSession (primary):**

- An async context manager for API operations
- Manages the HTTP client lifecycle and authentication tokens
- Uses the `api_session` ContextVar for context propagation

**Session (sync wrapper):**

- A synchronous wrapper for CLI commands
- Creates an async event loop internally
- Has the same interface as AsyncSession

See `client/session.py` for Session and AsyncSession, `client/request.py` for HTTP request handling, and `client/config.py` for APIConfig.

### API function pattern

**@api_function decorator:**

- Wraps instance methods as API functions
- Retrieves the session from the `api_session` ContextVar
- Handles async and sync execution
- Provides consistent error handling

**BaseFunction metaclass:**

- Creates function group instances bound to the session
- Examples: `session.FairShare`, `session.Admin`

Standard operations:

- `create_*` - POST requests
- `get_*` - GET a single item
- `search_*` - GET a collection with filters
- `update_*` - PATCH requests
- `delete_*` - DELETE requests
- `purge_*` - permanent deletion

See `client/func/base.py` for BaseFunction and @api_function, and `client/func/fair_share.py` for a complete implementation.

### Pydantic models

New code uses Pydantic models from `common/dto/`. The current `client/cli/types.py` still uses attrs classes.

Pydantic gives runtime type validation, automatic JSON serialization and deserialization, IDE autocomplete and type checking, and better error messages.

Usage:

- `model_dump(mode="json", exclude_none=True)` to a JSON dict
- `model_validate(data)` from a JSON dict
- Nested models are handled automatically

See `client/func/fair_share.py` for Pydantic usage in the SDK and `common/dto/fair_share.py` for shared DTO definitions.

### SDK implementation flow

1. Define the request and response Pydantic models
2. Create the method with the `@api_function` decorator
3. Build the Request object with the endpoint and data
4. Get the JSON response from the session
5. Parse it with `Response.model_validate(data)`
6. Return the typed result

See `client/func/fair_share.py` for all standard operations (create, get, search, update, delete).

## CLI implementation patterns

### Click command structure

Command organization:

- `ExtendedCommandGroup` - an enhanced Click group with interrupt handling
- `LazyGroup` - defers module imports until needed
- `@pass_ctx_obj` - type-safe CLIContext injection

See `client/cli/main.py` for the main entry and command groups, `client/cli/extensions.py` for the `@pass_ctx_obj` decorator, and `client/cli/fair_share/__init__.py` for LazyGroup usage.

### Output handlers

**FieldSpec:**

- Defines the displayable fields of a model
- Specifies the field name, human-readable label and formatters
- Supports nested fields with dot notation and custom formatters

**BaseOutputHandler:**

- `print_item()` - single item display
- `print_list()` - collection display
- `print_error()` - error messages
- Implementations: ConsoleOutputHandler (table) and JSONOutputHandler

See `client/output/types.py` for FieldSpec and the BaseOutputHandler protocol, `client/output/fields.py` for field utilities, and `client/cli/fair_share/commands.py` for FieldSpec definitions and usage.

### CLI and SDK integration

Pattern:

- Click command → Session context → SDK function → REST API
- Catch `BackendAIError` exceptions
- Use `ctx.output.print_error()` for consistent formatting
- Exit with the appropriate ExitCode

Error handling:

- All exceptions inherit from `BackendAIError`
- Exit codes come from the `ExitCode` enum (OK=0, FAILURE=1, INVALID_ARGUMENT=2, PERMISSION_DENIED=3)
- `ctx.output.print_error()` handles both console and JSON modes

See `client/cli/fair_share/commands.py` for complete CLI integration, `client/cli/types.py` for CLIContext and ExitCode, and `client/exceptions.py` for the exception hierarchy.

## Common patterns

| Pattern | SDK | CLI |
|---|---|---|
| **Session** | `async with AsyncSession()` | `with Session()` (sync wrapper) |
| **Request** | `Request("POST", "/endpoint", json={...})` | The SDK handles it internally |
| **Response** | `Response.model_validate(data)` | The SDK returns the parsed model |
| **Output** | Return a Pydantic model | `ctx.output.print_item()` or `print_list()` |
| **Error** | Raise a `BackendAIError` subclass | `print_error()` and `sys.exit(ExitCode)` |
| **Config** | `APIConfig()` reads the environment | Passed via `CLIContext` |
| **Async** | Always async (`async def`, `await`) | The sync wrapper handles it internally |

## Implementation checklist

When implementing a new CLI or SDK feature:

1. **Implement the REST API** (`/api-guide`)
   - Handler with the standard operations
   - Proper error responses

2. **Define the Pydantic models**
   - Request DTOs in `common/dto/`
   - Response DTOs shared with the API layer

3. **Implement the SDK function**
   - Add the method to the appropriate function group
   - Use the `@api_function` decorator
   - Handle all operations: create, get, search, update and delete

4. **Define the FieldSpec**
   - List the displayable fields
   - Add formatters for complex types
   - Consider both console and JSON output

5. **Implement the CLI commands**
   - Add the Click command group
   - Map options and arguments to SDK calls
   - Handle errors with the proper exit codes

6. **Write tests** (`/test-guide`)
   - SDK: mock HTTP responses with pytest-aiohttp
   - CLI: use CliRunner and mock the SDK functions, not the HTTP layer
   - Verify request and response serialization

7. **Update the documentation**
   - Add usage examples to the README
   - Document the new CLI commands

## Testing

SDK tests:

- Mock HTTP responses with `pytest-aiohttp`
- Test request serialization and response parsing
- Verify Pydantic model validation

CLI tests:

- Use the Click `CliRunner` for command invocation
- Mock the SDK functions, not the HTTP layer
- Test output formatting and exit codes

See `/test-guide` for the testing workflow and `tests/unit/client/` for test examples.

## Reference files

Complete implementations:

- `client/func/fair_share.py` - Full SDK with Pydantic models
- `client/cli/fair_share/commands.py` - Full CLI with all patterns

Architecture components:

- `client/session.py` - Session and AsyncSession
- `client/func/base.py` - @api_function and BaseFunction
- `client/cli/main.py` - CLI entry point
- `client/cli/extensions.py` - @pass_ctx_obj decorator
- `client/output/types.py` - FieldSpec and output handlers
- `client/config.py` - APIConfig
- `client/cli/types.py` - CLIContext and ExitCode
- `client/exceptions.py` - Exception hierarchy

## V2 SDK and CLI

All new SDK and CLI work uses the v2 pattern.

### V2 SDK client

`client/v2/domains_v2/`:

- Inherits `BaseDomainClient` and receives `BackendAIAuthClient` through the constructor
- Uses v2 DTOs from `common/dto/manager/v2/` only
- `typed_request()` handles serialization and response parsing
- Registry: `V2ClientRegistry` (`client/v2/v2_registry.py`) with `@cached_property` per domain

### V2 CLI

`client/cli/v2/`

Command pattern: `./bai [admin] {entity} [{sub-entity}] {operation}`

- `admin_` SDK methods map to commands under `./bai admin {entity} ...`
- Non-admin methods map to `./bai {entity} ...`
- Entity names are **singular**, such as domain, user and agent
- Each entity has its own directory with `__init__.py` and `commands.py`
- Admin commands live in `admin/{entity}.py`
- Sub-entities are separate Click sub-groups (revision, channel, role and so on)
- Construct Pydantic DTOs with explicit field arguments, never by unpacking kwargs
- Filter options are domain-specific CLI arguments (`--name-contains`, `--status` and so on)
- `--order-by field:direction` accepts multiple values
- Config comes from `~/.backend.ai/` via `load_v2_config()`, which returns a `V2ConnectionConfig` dataclass

### V2 config

`~/.backend.ai/`:

- `config.toml` - endpoint, endpoint_type, api_version
- `credentials.toml` - access_key, secret_key
- `session/cookie.dat` - webserver session cookie for login and logout

## Related documents

- `/api-guide` - REST API implementation (prerequisite)
- `/test-guide` - Testing workflow
- `/local-dev` - Service management and CLI testing
