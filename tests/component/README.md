# Component Tests

This directory holds **component tests**. A component test verifies **a complete Backend.AI component**, such as the manager, the agent or the storage proxy, from the outside, treating the component as a black box.

## What Belongs Here

A component test looks at **one complete Backend.AI component** through its public interfaces (APIs, models, routes) and ignores internal implementation details. Where a unit test tests one part, a component test verifies the **overall behavior of a component** as one unit.

**Key distinction**: A component test runs a complete Backend.AI component and may use real infrastructure, such as PostgreSQL and Valkey, but does not require multiple Backend.AI components to run together.

## Test Characteristics

A component test in this directory follows these rules:

- **Test one complete Backend.AI component**: Run the full component (manager, agent, etc.) as one system
- **Test through public interfaces**: Use HTTP APIs, GraphQL APIs, public models
- **Do not mock internal implementation**: Test all internal parts working together (services, repositories, models)
- **May use real infrastructure**: Start PostgreSQL, Valkey, etcd, etc. as needed
- **Isolate from other Backend.AI components**: Do not require other Backend.AI components to run
- **Test realistic scenarios**: Simulate real usage patterns and workflows
- **Verify behavior, not implementation**: Focus on what the component does, not how
- **Test error cases**: Verify proper error handling and responses

## Common Test Patterns

A component test typically covers:

**API Route Tests** - HTTP/REST and GraphQL routes:
- `tests/component/manager/api/test_auth.py` - Authentication routes
- `tests/component/manager/api/test_group.py` - Group management API
- `tests/component/manager/api/test_ratelimit.py` - Rate limiting behavior
- `tests/component/manager/api/test_config.py` - Configuration API

**Top-Level Model Tests** - Model behavior from the outside:
- `tests/component/manager/models/test_container_registries.py` - Container registry operations
- `tests/component/manager/models/test_vfolder.py` - Vfolder behavior

**GraphQL Schema Tests** - GraphQL queries and mutations:
- `tests/component/manager/models/gql_models/test_container_registries.py` - Container registry queries
- `tests/component/manager/models/gql_models/test_group.py` - Group operations
- `tests/component/manager/models/gql_models/test_container_registry_nodes_v2.py` - GraphQL node behavior

**Component Integration Tests** - Multiple internal subsystems working together:
- `tests/component/agent/docker/test_agent.py` - Docker agent with multiple subsystems

## Directory Structure

```
tests/component/
├── agent/
│   └── docker/           # Docker agent integration tests
│       ├── test_agent.py
│       ├── test_api.py
│       ├── test_kernel.py
│       └── ...
├── manager/
│    ├── api/              # Top-level API endpoint tests
│    │   ├── test_auth.py
│    │   ├── test_group.py
│    │   ├── test_ratelimit.py
│    │   └── ...
│    └── models/           # Top-level model tests
│        ├── gql_models/   # GraphQL schema tests
│        │   ├── test_container_registries.py
│        │   └── test_group.py
│        ├── test_container_registries.py
│        ├── test_session.py
│        └── test_vfolder.py
└── ...
```

## Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_<feature_or_behavior>()`
- Test classes: `Test<FeatureName>`, used when one class collects related scenarios
- Fixtures: Use descriptive names, such as `api_client`, `test_database`, `sample_request`

## Best Practices

1. **Test from the user's perspective**: Write a test as a client of the API
   ```python
   async def test_create_group(api_client: APIClient) -> None:
       # Arrange
       group_data = {"name": "developers", "description": "Dev team"}

       # Act
       response = await api_client.post("/groups", json=group_data)

       # Assert
       assert response.status == 201
       assert response.json()["name"] == "developers"
   ```

2. **Use realistic test data**: Test with data similar to production
3. **Test both success and failure paths**: Include error scenarios
4. **Set up and tear down properly**: Use fixtures to manage test state
5. **Avoid testing implementation details**: Do not assert on internal state
6. **Test API contracts**: Verify request and response schemas
7. **Use type hints**: Add type annotations for better code quality

## Running Component Tests

```bash
# Run all component tests
pants test tests/component/::

# Run component tests for specific component
pants test tests/component/manager/::

# Run API tests only
pants test tests/component/manager/api/::

# Run specific test file
pants test tests/component/manager/api/test_auth.py

# Run with verbose output
pants test --test-debug tests/component/manager/::
```


## When to Use Component Tests

Use component tests when:
- Testing public API routes of a Backend.AI component
- Testing complete workflows within a single Backend.AI component
- Testing a component's external behavior without running other components
- Testing model behavior from the outside
- Verifying API contracts and schemas

Use **unit tests** (see `tests/unit/README.md`) when:
- Testing individual parts: service methods, repository classes, utility functions
- Testing internal implementation details
- Testing adapters, DataLoaders and other internal utilities
- Do not need to run the entire component

Use **integration tests** (see `tests/integration/README.md`) when:
- Testing multiple Backend.AI components working together
- Testing workflows that span the manager, the agent and the storage proxy
- Testing end-to-end scenarios with all components running
- Testing complete system behavior
