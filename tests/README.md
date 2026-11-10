# Backend.AI Test Suite

This directory holds the test suite for Backend.AI, in three categories by testing scope and isolation level.

## Directory Structure

```
tests/
├── unit/           # Unit tests - isolated, fast tests with mocked dependencies
├── component/      # Component tests - external behavior tests for Backend.AI components
└── integration/    # Integration tests - multi Backend.AI component workflow tests
```

## Test Categories Overview

### [Unit Tests](unit/README.md) (`tests/unit/`)

Tests a single part of a Backend.AI component, such as a function, a class or a module.

- **Scope**: Specific parts of a Backend.AI component
- **Backend.AI components**: Parts of one component, such as a repository class or a service method
- **Infrastructure**: May use real PostgreSQL, Valkey, etc.
- **Speed**: Fast (milliseconds to seconds)
- **When to use**: Testing internal logic, data access layers, utilities

**Examples**: Repository methods, service business logic, utility functions, DataLoaders

### [Component Tests](component/README.md) (`tests/component/`)

Tests one complete Backend.AI component, such as the manager, the agent or the storage proxy, from the outside.

- **Scope**: One complete Backend.AI component
- **Backend.AI components**: Entire component running (manager, agent, etc.)
- **Infrastructure**: May use real PostgreSQL, Valkey, etc.
- **Speed**: Moderate (seconds)
- **When to use**: Testing component APIs, routes, complete workflows within one component

**Examples**: HTTP API routes, GraphQL queries, external behavior of a component

### [Integration Tests](integration/README.md) (`tests/integration/`)

Tests **multiple Backend.AI components** working together as a complete system.

- **Scope**: Multiple Backend.AI components
- **Backend.AI components**: Multiple components running simultaneously (manager, agent and storage proxy)
- **Infrastructure**: Real PostgreSQL, Valkey, etcd and storage systems
- **Speed**: Slow (seconds to minutes)
- **When to use**: Testing communication between components, end-to-end workflows

**Examples**: Manager scheduling sessions on an agent, storage operations across components, complete user workflows

## Comparison Table

| Aspect | Unit Tests | Component Tests | Integration Tests |
|--------|-----------|-----------------|-------------------|
| **Backend.AI components** | Test parts of one component | Test one complete component | Test multiple components together |
| **Scope** | Individual function, class or module | Complete component (manager, agent, etc.) | Multiple components (manager, agent and storage proxy) |
| **Internal Parts** | Test specific parts | Test all parts of one component | Test components working together |
| **Infrastructure** | May use real PostgreSQL, Valkey, etc. | May use real PostgreSQL, Valkey, etc. | Use real PostgreSQL, Valkey, etc. |
| **Environment** | In-process or single process | Single component process | Multi-component cluster |
| **Speed** | Fast (milliseconds to seconds) | Moderate (seconds) | Slow (seconds to minutes) |
| **Focus** | How specific parts work | What one component does | How components interact |
| **Example** | Testing a repository class | Testing an API route | Testing the manager scheduling a session on an agent |

## Quick Start

```bash
# Run all tests
pants test ::

# Run specific category
pants test tests/unit/::
pants test tests/component/::
pants test tests/integration/::

# Run specific component
pants test tests/unit/manager/::
pants test tests/component/agent/::

# Run changed tests only
pants test --changed-since=HEAD~1
```

## Test containers

The `etcd_container`, `redis_container` and `postgres_container` fixtures in
`src/ai/backend/testutils/bootstrap.py` take their containers from a pool with one
container per (role, Pants execution slot). Pants runs one pytest process per slot at a
time, so a process reuses the containers that the previous process in its slot left
running instead of starting new ones. The pool is keyed by checkout path, so worktrees do
not share it.

| Step | Who |
|---|---|
| Create a slot's container | The first process in that slot; later processes in the slot reuse it |
| Reset between processes | postgres: per-process database `test_db_<token>`; etcd: per-process namespace; redis: FLUSHALL on attach |
| Remove the pool | A detached reaper (flock on `tmp/backend.ai/test-pool/holders`) once no process has held the pool for 20 s |

`BACKEND_TEST_SHARE_CONTAINERS=0` makes each process start and remove its own containers
instead.

## Test batches

`tests/component/BUILD` sets `batch_compatibility_tag="component"` for every
`python_tests` target under it, so Pants runs up to `[test].batch_size` files in one
pytest process. Files in a batch share one database, etcd namespace and redis, so a
test must clean up what its fixtures wrote.

| Rule | |
|---|---|
| A tag names an infrastructure set | `component` = postgres + etcd + redis; `component-agent` = pulled docker images |
| Set it once, in the subtree's top `__defaults__` | Do not set it on an individual `python_tests` target |
| A new tag needs a different infrastructure set | Write the reason in that BUILD file |
| State leaking between files is a fixture bug | Fix the fixture; do not split the tag or pull the file out of the batch |

## Test Selection Guide

**When writing a new test, ask yourself:**

1. **Testing a specific part of a Backend.AI component** → Unit test
   - Testing a function, class or module in isolation
   - May use real infrastructure, such as PostgreSQL and Valkey
   - Do not need to run the entire component
   - Example: Testing a repository class, a service method

2. **Testing one complete Backend.AI component** → Component test
   - Testing the entire component (manager, agent, etc.)
   - Testing from the outside through APIs
   - Do not need other Backend.AI components running
   - Example: Testing the manager's HTTP API routes

3. **Testing multiple Backend.AI components together** → Integration test
   - Testing the manager, agent and storage proxy working together
   - Testing communication between components
   - Testing complete end-to-end workflows
   - Example: Testing the manager scheduling a session that runs on an agent

## Related documents

For detailed guidelines on each test category, see:
- [Unit Tests Guide](unit/README.md)
- [Component Tests Guide](component/README.md)
- [Integration Tests Guide](integration/README.md)

## Build System

This project uses **Pants** for test execution and dependency management.

Each test directory requires a `BUILD` file:

```python
# Test utilities (conftest.py, helpers)
python_test_utils(
    sources=["*.py", "!test_*.py"],
)

# Test files
python_tests(
    name="tests",
    dependencies=["src/ai/backend/{component}:src"],
)
```

## Contributing

When adding new tests:

1. Choose the appropriate category (unit, component or integration)
2. Follow existing patterns in that category
3. Ensure BUILD files are properly configured
4. Run tests locally before committing
5. Refer to the category-specific README for detailed guidelines
