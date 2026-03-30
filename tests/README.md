# Backend.AI Test Suite

This directory contains the comprehensive test suite for Backend.AI, organized into three categories based on testing scope and isolation level.

## Directory Structure

```
tests/
├── unit/           # Unit tests - isolated, fast tests with mocked dependencies
├── component/      # Component tests - external behavior tests for Backend.AI components
└── integration/    # Integration tests - multi Backend.AI component workflow tests
```

## Test Categories Overview

### [Unit Tests](unit/README.md) (`tests/unit/`)

Tests individual parts (functions, classes, modules) within a Backend.AI component.

- **Scope**: Specific parts of a Backend.AI component
- **Backend.AI Components**: Parts of one component (e.g., a repository class, a service method)
- **Infrastructure**: May use real PostgreSQL, Redis, etc.
- **Speed**: Fast (milliseconds to seconds)
- **When to use**: Testing internal logic, data access layers, utilities

**Examples**: Repository methods, service business logic, utility functions, dataloaders

### [Component Tests](component/README.md) (`tests/component/`)

Tests one complete Backend.AI component (manager, agent, storage-proxy, etc.) from external perspective.

- **Scope**: One complete Backend.AI component
- **Backend.AI Components**: Entire component running (manager, agent, etc.)
- **Infrastructure**: May use real PostgreSQL, Redis, etc.
- **Speed**: Moderate (seconds)
- **When to use**: Testing component APIs, endpoints, complete workflows within one component

**Examples**: HTTP API endpoints, GraphQL queries, component external behavior

### [Integration Tests](integration/README.md) (`tests/integration/`)

Tests **multiple Backend.AI components** working together as a complete system.

- **Scope**: Multiple Backend.AI components
- **Backend.AI Components**: Multiple components running simultaneously (manager + agent + storage-proxy)
- **Infrastructure**: Real PostgreSQL, Redis, etcd, storage systems
- **Speed**: Slow (seconds to minutes)
- **When to use**: Testing inter-component communication, end-to-end workflows

**Examples**: Manager scheduling sessions on agent, storage operations across components, complete user workflows

## Comparison Table

| Aspect | Unit Tests | Component Tests | Integration Tests |
|--------|-----------|-----------------|-------------------|
| **Backend.AI Components** | Test parts of one component | Test one complete component | Test multiple components together |
| **Scope** | Individual function/class/module | Complete component (manager, agent, etc.) | Multiple components (manager + agent + storage-proxy) |
| **Internal Parts** | Test specific parts | Test all parts of one component | Test components working together |
| **Infrastructure** | May use real PostgreSQL, Redis, etc. | May use real PostgreSQL, Redis, etc. | Use real PostgreSQL, Redis, etc. |
| **Environment** | In-process or single process | Single component process | Multi-component cluster |
| **Speed** | Fast (ms to seconds) | Moderate (seconds) | Slow (seconds to minutes) |
| **Focus** | How specific parts work | What one component does | How components interact |
| **Example** | Testing a repository class | Testing an API endpoint | Testing manager scheduling a session on agent |

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

## Test Selection Guide

**When writing a new test, ask yourself:**

1. **Am I testing a specific part of a Backend.AI component?** → Unit test
   - Testing a function, class, or module in isolation
   - May use real infrastructure (PostgreSQL, Redis)
   - Don't need to run the entire component
   - Example: Testing a repository class, a service method

2. **Am I testing one complete Backend.AI component?** → Component test
   - Testing the entire component (manager, agent, etc.)
   - Testing from external perspective via APIs
   - Don't need other Backend.AI components running
   - Example: Testing manager's HTTP API endpoints

3. **Am I testing multiple Backend.AI components together?** → Integration test
   - Testing manager, agent, storage-proxy, etc. working together
   - Testing inter-component communication
   - Testing complete end-to-end workflows
   - Example: Testing manager scheduling a session that runs on agent

## Documentation

For detailed guidelines on each test category, see:
- [Unit Tests Guide](unit/README.md)
- [Component Tests Guide](component/README.md)
- [Integration Tests Guide](integration/README.md)

## Build System

This project uses **Pantsbuild** for test execution and dependency management.

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

1. Choose the appropriate category (unit/component/integration)
2. Follow existing patterns in that category
3. Ensure BUILD files are properly configured
4. Run tests locally before committing
5. Refer to the category-specific README for detailed guidelines
