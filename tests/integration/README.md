# Integration Tests

This directory holds **integration tests**. An integration test verifies the interaction between **multiple Backend.AI components** (manager, agent, storage proxy, webserver, etc.) working together in realistic deployment scenarios.

## What Belongs Here

An integration test looks at how **multiple Backend.AI components work together** as a complete system. Where a unit test tests parts of a component and a component test tests one complete component, an integration test verifies the **interactions and workflows between components**.

**Key distinction**: An integration test requires multiple Backend.AI components to run simultaneously and verifies that they communicate and coordinate correctly.

## Test Characteristics

An integration test in this directory follows these rules:

- **Run multiple Backend.AI components**: Manager, agent, storage proxy, etc. running simultaneously
- **Test communication between components**: Verify that components communicate correctly
- **Use real infrastructure**: PostgreSQL, Valkey, etcd and storage systems
- **Test complete workflows**: End-to-end scenarios spanning multiple components
- **Run in an isolated environment**: Docker Compose, test clusters
- **Be slower**: May take seconds to minutes
- **Test realistic scenarios**: Simulate production workloads
- **Verify data consistency**: Check state across multiple components
- **Test failure scenarios**: Component failures, network partitions, timeouts

## Common Test Patterns

An integration test typically covers:

**Multi-Component Workflows** - Workflows spanning multiple Backend.AI components:
- Session creation flow: manager schedules → agent provisions → kernel starts
- File operations: client uploads → storage proxy processes → agent mounts
- Model serving: manager deploys → agent runs → app proxy routes traffic

**External Service Integration** - Backend.AI components with real external systems:
- Database transaction isolation across services
- Distributed locking via etcd
- File upload and download through the storage proxy
- Image pull from a container registry
- Valkey pub/sub between components

**Infrastructure Tests** - Deployment and cluster scenarios:
- Agent failover when one agent goes down
- Manager cluster leader election
- Database connection pooling under load
- Service discovery and health checks

**End-to-End User Scenarios** - Complete user workflows:
- User logs in → Creates a session → Uploads data → Runs a computation → Downloads results
- Admin creates a user → Sets quotas → User hits the limits → Proper error handling

## Directory Structure

```
tests/integration/
├── session_lifecycle/      # End-to-end session tests
│   ├── test_create_session.py
│   ├── test_execute_code.py
│   └── test_terminate_session.py
├── storage/                # Storage integration tests
│   ├── test_file_upload.py
│   ├── test_vfolder_mount.py
│   └── test_s3_backend.py
├── multi_component/        # Cross-component tests
│   ├── test_manager_agent.py
│   ├── test_manager_storage.py
│   └── test_app_proxy_routing.py
├── database/               # Database integration
│   ├── test_transactions.py
│   └── test_migrations.py
├── external_services/      # External service tests
│   ├── test_container_registry.py
│   ├── test_etcd_coordination.py
│   └── test_redis_pubsub.py
├── ...
└── conftest.py            # Shared fixtures and setup
```

## Running Integration Tests

Integration tests are typically run separately from unit and component tests:

```bash
# Run all integration tests
pants test tests/integration/::

# Run specific integration test suite
pants test tests/integration/session_lifecycle/::

# Run in CI (with longer timeout)
pants test --test-timeout=300 tests/integration/::
```

## When to Use Integration Tests

Use integration tests when:
- Testing communication between multiple Backend.AI components (manager and agent, manager and storage proxy)
- Testing complete workflows that span multiple components
- Verifying data consistency across components
- Testing with all Backend.AI components running together
- Validating deployment and infrastructure scenarios
- Validating an end-to-end user workflow
- Testing failure and recovery scenarios across components

Use **component tests** (see `tests/component/README.md`) when:
- Testing a single Backend.AI component in isolation
- Testing one component's API routes or models
- Do not need other Backend.AI components running
- Faster feedback is important

Use **unit tests** (see `tests/unit/README.md`) when:
- Testing individual parts within a component
- Testing specific functions, classes or modules
- Do not need to run the entire component
- Need a very fast test execution

## Performance Considerations

- **Parallel execution**: Integration tests may not be parallelizable due to shared resources
- **Test duration**: Expect 10-60 seconds per test
- **Resource usage**: May require 4GB+ RAM and multiple CPU cores
- **CI costs**: Consider running integration tests only on merge to the main branch
- **Cleanup**: Always remove test data and resources in teardown
