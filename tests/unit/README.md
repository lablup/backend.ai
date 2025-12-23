# Unit Tests

This directory contains **unit tests** that verify **individual parts** (functions, classes, modules) of Backend.AI components in isolation from other Backend.AI components.

## What Belongs Here

Unit tests focus on testing internal logic, data transformations, and implementation details of **specific parts** within a Backend.AI component, such as:
- A single service method
- A repository class
- A utility function
- A data loader
- A configuration loader

**Important**: Unit tests may spin up external infrastructure (PostgreSQL, Redis, etc.) as needed. The key distinction is that unit tests test **parts of a Backend.AI component**, not the entire component or multiple components together.

## Test Characteristics

Unit tests in this directory should:

- ✅ **Test individual parts**: Focus on a specific function, class, or module within a Backend.AI component
- ✅ **Isolate from other Backend.AI components**: Don't require running other Backend.AI components (manager, agent, storage-proxy, etc.)
- ✅ **May use real infrastructure**: Can spin up PostgreSQL, Redis, etcd, etc. as needed for the test
  - Example: Repository tests use real PostgreSQL databases
  - Example: ValkeyClient tests use real Redis instances
- ✅ **Run relatively fast**: Most complete in milliseconds to a few seconds
- ✅ **Be deterministic**: Same input always produces same output
- ✅ **Focus on implementation**: Test how specific parts work internally
- ✅ **Use fixtures extensively**: Share test data and infrastructure setup via pytest fixtures

## Common Test Patterns

Unit tests can cover various parts of a Backend.AI component:

**Service Layer Tests** - Business logic in service classes:
- `tests/unit/manager/services/auth/test_authorize.py` - Authorization logic
- `tests/unit/manager/services/session/actions/test_create.py` - Session creation business rules

**Repository Tests** - Data access layers (often with real PostgreSQL):
- `tests/unit/manager/repositories/agent/test_repository.py` - Agent data queries
- `tests/unit/manager/repositories/user/test_user_repository.py` - User CRUD operations

**Internal API Components** - API implementation details:
- `tests/unit/manager/api/gql/test_adapter.py` - GraphQL adapters
- `tests/unit/manager/api/artifact/test_dataloader.py` - DataLoaders

**Model Utilities** - Model helpers and serialization:
- `tests/unit/manager/models/gql_models/test_container_registry_nodes.py` - GraphQL node structure
- `tests/unit/manager/models/test_utils.py` - Model helper functions

**Configuration and Dependencies** - Setup and bootstrap logic:
- `tests/unit/manager/config/test_unified.py` - Configuration loading
- `tests/unit/manager/dependencies/bootstrap/test_config.py` - Dependency injection

**Client Wrappers** - Client libraries for external services (often with real infrastructure):
- `tests/unit/common/clients/valkey_client/test_valkey_artifact_client.py` - Valkey client (with real Redis)
- `tests/unit/manager/clients/test_storage_proxy_client.py` - Storage proxy client wrapper

**Utilities and Helpers** - Reusable functions:
- `tests/unit/common/test_types.py` - Type utilities
- `tests/unit/manager/test_utils.py` - Manager utilities

**Background Tasks** - Background job logic:
- `tests/unit/manager/bgtask/tasks/test_commit_session.py` - Session commit task

## Directory Structure

```
tests/unit/
├── agent/              # Agent component unit tests
├── appproxy/          # App proxy unit tests
├── cli/               # CLI utility tests
├── client/            # Client SDK unit tests
├── common/            # Common utilities unit tests
├── manager/           # Manager component unit tests
│   ├── actions/       # Action processor tests
│   ├── api/           # API implementation tests
│   │   ├── gql/       # GraphQL adapter tests
│   │   ├── artifact/  # Artifact dataloader tests
│   │   └── ...
│   ├── bgtask/        # Background task tests
│   ├── config/        # Configuration tests
│   ├── dependencies/  # Dependency injection tests
│   ├── integration/   # Service integration tests
│   ├── models/        # Model utility tests
│   ├── repositories/  # Repository tests
│   ├── services/      # Service layer tests
│   └── ...
└── ...
```

## Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_<behavior_being_tested>()`
- Test classes (if used): `Test<ComponentName>`
- Fixtures: Use descriptive names like `mock_db_session`, `sample_user_data`

## Best Practices

1. **One logical assertion per test**: Keep tests focused on a single behavior
2. **Arrange-Act-Assert (AAA)**: Structure tests clearly
   ```python
   def test_user_creation():
       # Arrange
       user_data = {"name": "Alice", "email": "alice@example.com"}

       # Act
       user = create_user(user_data)

       # Assert
       assert user.name == "Alice"
   ```
3. **Use descriptive test names**: Test name should describe what is being tested
4. **Use real infrastructure when appropriate**: Don't hesitate to use real PostgreSQL, Redis, etc. if testing code that directly interacts with them
5. **Mock Backend.AI components**: Mock other Backend.AI components and external APIs, but use real infrastructure (databases, caches) when testing code that directly uses them
6. **Avoid testing implementation details too deeply**: Focus on behavior, not internals
7. **Use type hints**: Add type annotations to test code for better IDE support

## Running Unit Tests

```bash
# Run all unit tests
pants test tests/unit/::

# Run unit tests for specific component
pants test tests/unit/manager/::

# Run specific test file
pants test tests/unit/manager/services/auth/test_authorize.py

# Run with verbose output
pants test --test-debug tests/unit/manager/::
```

## When NOT to Use Unit Tests

Consider using **component tests** instead when:
- Testing a complete Backend.AI component (manager, agent, storage-proxy, etc.) from external perspective
- Testing full HTTP request/response cycles through API endpoints
- Testing complete workflows within a single Backend.AI component
- Testing top-level model behavior (not internal utilities)

Consider using **integration tests** instead when:
- Testing interactions between multiple Backend.AI components
- Testing end-to-end workflows that span manager, agent, and storage-proxy
- Testing complete system behavior with all components running

See `tests/component/README.md` and `tests/integration/README.md` for guidelines.
