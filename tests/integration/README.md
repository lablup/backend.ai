# Integration Tests

This directory contains **integration tests** that verify the interaction between **multiple Backend.AI components** (manager, agent, storage-proxy, webserver, etc.) working together in realistic deployment scenarios.

## What Belongs Here

Integration tests focus on testing how **multiple Backend.AI components work together** as a complete system. Unlike unit tests (testing parts of a component) or component tests (testing one complete component), integration tests verify the **interactions and workflows between components**.

**Key distinction**: Integration tests require running multiple Backend.AI components simultaneously and verifying they communicate and coordinate correctly.

## Test Characteristics

Integration tests in this directory should:

- ✅ **Run multiple Backend.AI components**: Manager, agent, storage-proxy, etc. running simultaneously
- ✅ **Test inter-component communication**: Verify components communicate correctly
- ✅ **Use real infrastructure**: PostgreSQL, Redis, etcd, storage systems
- ✅ **Test complete workflows**: End-to-end scenarios spanning multiple components
- ✅ **Run in isolated environment**: Docker Compose, test clusters
- ✅ **Be slower**: May take seconds to minutes
- ✅ **Test realistic scenarios**: Simulate production workloads
- ✅ **Verify data consistency**: Check state across multiple components
- ✅ **Test failure scenarios**: Component failures, network partitions, timeouts

## Common Test Patterns

Integration tests typically cover:

**Multi-Component Workflows** - Workflows spanning multiple Backend.AI components:
- Session creation flow: Manager schedules → Agent provisions → Kernel starts
- File operations: Client uploads → Storage Proxy processes → Agent mounts
- Model serving: Manager deploys → Agent runs → App Proxy routes traffic

**External Service Integration** - Backend.AI components with real external systems:
- Database transaction isolation across services
- Distributed locking via etcd
- File upload/download through storage proxy
- Image pull from container registry
- Redis/Valkey pub/sub between components

**Infrastructure Tests** - Deployment and cluster scenarios:
- Agent failover when one agent goes down
- Manager cluster leader election
- Database connection pooling under load
- Service discovery and health checks

**End-to-End User Scenarios** - Complete user workflows:
- User logs in → Creates session → Uploads data → Runs computation → Downloads results
- Admin creates user → Sets quotas → User hits limits → Proper error handling

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

Integration tests are typically run separately from unit/component tests:

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
- ✅ Testing communication between multiple Backend.AI components (manager ↔ agent, manager ↔ storage-proxy)
- ✅ Testing complete workflows that span multiple components
- ✅ Verifying data consistency across components
- ✅ Testing with all Backend.AI components running together
- ✅ Validating deployment and infrastructure scenarios
- ✅ End-to-end user workflow validation
- ✅ Testing failure and recovery scenarios across components

Use **component tests** (see `tests/component/README.md`) when:
- ❌ Testing a single Backend.AI component in isolation
- ❌ Testing one component's API endpoints or models
- ❌ Don't need other Backend.AI components running
- ❌ Faster feedback is important

Use **unit tests** (see `tests/unit/README.md`) when:
- ❌ Testing individual parts within a component
- ❌ Testing specific functions, classes, or modules
- ❌ Don't need to run the entire component
- ❌ Need very fast test execution

## Performance Considerations

- **Parallel execution**: Integration tests may not be parallelizable due to shared resources
- **Test duration**: Expect 10-60 seconds per test
- **Resource usage**: May require 4GB+ RAM and multiple CPU cores
- **CI costs**: Consider running integration tests only on merge to main branch
- **Cleanup**: Always clean up test data and resources in teardown

