---
name: cli-sdk-guide
description: Guide for implementing Backend.AI client SDK and CLI (Session, BaseFunction, @api_function, Click commands, Pydantic models, FieldSpec, output handlers, APIConfig, testing)
version: 1.0.0
dependencies:
  - api-guide
  - tdd-guide
tags:
  - client-sdk
  - cli
  - session
  - api-function
  - click
  - pydantic
  - output-handler
---

# CLI/SDK Implementation Guide

Guide for implementing Backend.AI client SDK and CLI with session management, API functions, and Click commands.

## Purpose

**SDK (Software Development Kit):**
- Python library for Backend.AI REST API
- Programmatic access for integrations and automation
- Async-first with sync wrapper for CLI compatibility

**CLI (Command Line Interface):**
- User-facing commands for Backend.AI operations
- Built on top of SDK functions
- Supports console and JSON output modes

**When to use:**
- SDK: Building integrations, automation scripts, web dashboards
- CLI: Interactive administration, shell scripts, CI/CD pipelines
- Direct API: Only when SDK doesn't support the operation yet

## Architecture Overview

**Layers:** CLI → SDK → REST API → Manager

**Flow:** CLI commands call SDK functions through Session, which makes HTTP requests to REST API endpoints.

**CLI Layer:**
- `ExtendedCommandGroup` - Command groups with aliases and interrupt handling
- `LazyGroup` - Lazy loading for faster startup
- `CLIContext` - Shared state (config, output mode)
- `@pass_ctx_obj` - CLIContext injection decorator
- `FieldSpec` - Output field definitions
- `BaseOutputHandler` - Console/JSON formatters

**SDK Layer:**
- `BaseFunction` - Metaclass for API function classes
- `@api_function` - Decorator for API methods
- `AsyncSession` - Primary async HTTP session
- `Session` - Sync wrapper for CLI
- `api_session` - ContextVar for session context

**Data Layer:**
- **Pydantic models** - Request/Response DTOs (future standard)
- **attrs classes** - Legacy DTOs (current usage in `client/cli/types.py`)
- New code should use Pydantic (`common/dto/`)

**Config Layer:**
- `APIConfig` - Environment variables and .env file
- `CLIContext` - CLI state and output handler

## SDK Implementation Patterns

### Session Management

**AsyncSession (Primary):**
- Async context manager for API operations
- Manages HTTP client lifecycle, authentication tokens
- Uses `api_session` ContextVar for context propagation

**Session (Sync Wrapper):**
- Synchronous wrapper for CLI commands
- Creates async event loop internally
- Same interface as AsyncSession

**See:**
- `client/session.py` - Session and AsyncSession implementation
- `client/request.py` - HTTP request handling
- `client/config.py` - APIConfig for environment variables

### API Function Pattern

**@api_function decorator:**
- Wraps instance methods as API functions
- Retrieves session from `api_session` ContextVar
- Handles async/sync execution
- Provides consistent error handling

**BaseFunction metaclass:**
- Creates function group instances bound to session
- Examples: `session.FairShare`, `session.Admin`

**Standard operations:**
- `create_*` - POST requests
- `get_*` - GET single item
- `search_*` - GET collection with filters
- `update_*` - PATCH requests
- `delete_*` - DELETE requests
- `purge_*` - Permanent deletion

**See:**
- `client/func/base.py` - BaseFunction and @api_function
- `client/func/fair_share.py` - Complete implementation example

### Pydantic Models (Future Standard)

**Current state:**
- **attrs** - Current usage in `client/cli/types.py`
- **Pydantic** - Future standard in `common/dto/`
- **New code should use Pydantic**

**Why Pydantic:**
- Runtime type validation
- Automatic JSON serialization/deserialization
- IDE autocomplete and type checking
- Better error messages

**Usage:**
- `model_dump(mode="json", exclude_none=True)` - To JSON dict
- `model_validate(data)` - From JSON dict
- Handles nested models automatically

**See:**
- `client/func/fair_share.py` - Pydantic usage in SDK
- `common/dto/fair_share.py` - Shared DTO definitions

### SDK Implementation Flow

**Standard pattern:**
1. Define request/response Pydantic models
2. Create method with @api_function decorator
3. Build Request object with endpoint and data
4. Fetch JSON response from session
5. Parse with `Response.model_validate(data)`
6. Return typed result

**See complete example:**
- `client/func/fair_share.py` - All standard operations (create, get, search, update, delete)

## CLI Implementation Patterns

### Click Command Structure

**Command organization:**
- `ExtendedCommandGroup` - Enhanced Click group with interrupt handling
- `LazyGroup` - Defers module imports until needed
- `@pass_ctx_obj` - Type-safe CLIContext injection

**See:**
- `client/cli/main.py` - Main entry and command groups
- `client/cli/extensions.py` - @pass_ctx_obj decorator
- `client/cli/fair_share/__init__.py` - LazyGroup usage

### Output Handlers

**FieldSpec:**
- Defines displayable fields for a model
- Specifies field name, human-readable label, formatters
- Supports nested fields (dot notation) and custom formatters

**BaseOutputHandler:**
- `print_item()` - Single item display
- `print_list()` - Collection display
- `print_error()` - Error messages
- Implementations: ConsoleOutputHandler (table), JSONOutputHandler

**See:**
- `client/output/types.py` - FieldSpec and BaseOutputHandler protocol
- `client/output/fields.py` - Field utilities
- `client/cli/fair_share/commands.py` - FieldSpec definitions and usage

### CLI + SDK Integration

**Pattern:**
- Click command → Session context → SDK function → REST API
- Catch `BackendAIError` exceptions
- Use `ctx.output.print_error()` for consistent formatting
- Exit with appropriate ExitCode

**Error handling:**
- All exceptions inherit from `BackendAIError`
- Exit codes from `ExitCode` enum (OK=0, FAILURE=1, INVALID_ARGUMENT=2, PERMISSION_DENIED=3)
- `ctx.output.print_error()` handles both console and JSON modes

**See:**
- `client/cli/fair_share/commands.py` - Complete CLI integration
- `client/cli/types.py` - CLIContext and ExitCode
- `client/exceptions.py` - Exception hierarchy

## Common Patterns

| Pattern | SDK | CLI |
|---------|-----|-----|
| **Session** | `async with AsyncSession()` | `with Session()` (sync wrapper) |
| **Request** | `Request("POST", "/endpoint", json={...})` | SDK handles internally |
| **Response** | `Response.model_validate(data)` | SDK returns parsed model |
| **Output** | Return Pydantic model | `ctx.output.print_item()` or `print_list()` |
| **Error** | Raise `BackendAIError` subclass | `print_error()` + `sys.exit(ExitCode)` |
| **Config** | `APIConfig()` reads environment | Passed via `CLIContext` |
| **Async** | Always async (`async def`, `await`) | Sync wrapper handles internally |

## Implementation Checklist

When implementing new CLI/SDK feature:

1. ✅ **Implement REST API** (`/api-guide`)
   - Handler with standard operations
   - Proper error responses

2. ✅ **Define Pydantic models**
   - Request DTOs in `common/dto/`
   - Response DTOs shared with API layer

3. ✅ **Implement SDK function**
   - Add method to appropriate function group
   - Use `@api_function` decorator
   - Handle all operations (create, get, search, update, delete)

4. ✅ **Define FieldSpec**
   - List displayable fields
   - Add formatters for complex types
   - Consider both console and JSON output

5. ✅ **Implement CLI commands**
   - Add Click command group
   - Map options/arguments to SDK calls
   - Handle errors with proper exit codes

6. ✅ **Write tests** (`/tdd-guide`)
   - SDK: Mock HTTP responses (pytest-aiohttp)
   - CLI: Use CliRunner, mock SDK functions (not HTTP)
   - Verify request/response serialization

7. ✅ **Update documentation**
   - Add usage examples to README
   - Document new CLI commands

## Testing

**SDK tests:**
- Mock HTTP responses with `pytest-aiohttp`
- Test request serialization and response parsing
- Verify Pydantic model validation

**CLI tests:**
- Use Click's `CliRunner` for command invocation
- Mock SDK functions (not HTTP layer)
- Test output formatting and exit codes

**See:**
- `/tdd-guide` skill for testing workflow
- `tests/unit/client/` - Test examples

## Reference Files

**Complete implementations:**
- `client/func/fair_share.py` - Full SDK with Pydantic models
- `client/cli/fair_share/commands.py` - Full CLI with all patterns

**Architecture components:**
- `client/session.py` - Session and AsyncSession
- `client/func/base.py` - @api_function and BaseFunction
- `client/cli/main.py` - CLI entry point
- `client/cli/extensions.py` - @pass_ctx_obj decorator
- `client/output/types.py` - FieldSpec and output handlers
- `client/config.py` - APIConfig
- `client/cli/types.py` - CLIContext and ExitCode
- `client/exceptions.py` - Exception hierarchy

**Related skills:**
- `/api-guide` - REST API implementation (prerequisite)
- `/tdd-guide` - Testing workflow
