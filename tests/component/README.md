# Component Tests

This directory contains **component tests** that verify **a complete Backend.AI component** (manager, agent, storage-proxy, etc.) from an external perspective, treating the component as a black box.

## What Belongs Here

Component tests focus on testing **one complete Backend.AI component** through its public interfaces (APIs, models, endpoints) without concern for internal implementation details. Unlike unit tests that test individual parts, component tests verify the **overall behavior of a component** as a cohesive unit.

**Key distinction**: Component tests run a complete Backend.AI component and may use real infrastructure (PostgreSQL, Redis, etc.), but don't require running multiple Backend.AI components together.

## Test Characteristics

Component tests in this directory should:

- ✅ **Test one complete Backend.AI component**: Run the full component (manager, agent, etc.) as a unified system
- ✅ **Test through public interfaces**: Use HTTP APIs, GraphQL endpoints, public models
- ✅ **Don't mock internal implementation**: Test all internal parts working together (services, repositories, models)
- ✅ **May use real infrastructure**: Can spin up PostgreSQL, Redis, etcd, etc. as needed
- ✅ **Isolate from other Backend.AI components**: Don't require running other Backend.AI components
- ✅ **Test realistic scenarios**: Simulate real usage patterns and workflows
- ✅ **Verify behavior, not implementation**: Focus on what the component does, not how
- ✅ **Test error cases**: Verify proper error handling and responses

## Common Test Patterns

Component tests typically cover:

**API Endpoint Tests** - HTTP/REST and GraphQL endpoints:
- `tests/component/manager/api/test_auth.py` - Authentication endpoints
- `tests/component/manager/api/test_group.py` - Group management API
- `tests/component/manager/api/test_ratelimit.py` - Rate limiting behavior
- `tests/component/manager/api/test_config.py` - Configuration API

**Top-Level Model Tests** - Model behavior from external perspective:
- `tests/component/manager/models/test_container_registries.py` - Container registry operations
- `tests/component/manager/models/test_vfolder.py` - Virtual folder behavior

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
- Test classes: `Test<FeatureName>` (when grouping related scenarios)
- Fixtures: Use descriptive names like `api_client`, `test_database`, `sample_request`

## Best Practices

1. **Test from user perspective**: Write tests as if you're using the API
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
4. **Setup and teardown properly**: Use fixtures to manage test state
5. **Avoid testing implementation details**: Don't assert on internal state
6. **Test API contracts**: Verify request/response schemas
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
- Testing public API endpoints of a Backend.AI component
- Testing complete workflows within a single Backend.AI component
- Testing a component's external behavior without running other components
- Testing model behavior from external perspective
- Verifying API contracts and schemas

Use **unit tests** (see `tests/unit/README.md`) when:
- Testing individual parts: service methods, repository classes, utility functions
- Testing internal implementation details
- Testing adapters, dataloaders, and other internal utilities
- Don't need to run the entire component

Use **integration tests** (see `tests/integration/README.md`) when:
- Testing multiple Backend.AI components working together
- Testing workflows that span manager, agent, and storage-proxy
- Testing end-to-end scenarios with all components running
- Testing complete system behavior
