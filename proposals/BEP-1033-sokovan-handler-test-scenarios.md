---
Author: Hyeokjin Jeon (achimnol@lablup.com)
Status: Draft
Created: 2025-01-19
Created-Version: 25.3.0
Target-Version:
Implemented-Version:
---

# Sokovan Handler Test Scenarios

## Related Issues

- JIRA: BA-3936

## Motivation

After the Sokovan scheduler refactoring (BA-3936), the responsibilities of handlers have been clearly separated, but systematic test coverage for them is lacking.

Current issues:
- Handler unit tests are absent or written based on the old implementation
- Integration tests for the Coordinator-Handler pattern are insufficient
- Deployment/Route handler tests are completely missing
- Tests for status transition verification logic are insufficient

By clearly defining test scenarios:
1. Explicitly verify the responsibility scope of each handler
2. Establish a baseline for regression prevention
3. Provide a reference guide when adding new handlers

---

## Current Test Coverage

### Line Coverage Summary (pants test --test-use-coverage)

```
pants test --force --test-use-coverage --coverage-py-global-report \
  --coverage-py-filter='["ai.backend.manager.sokovan"]' \
  tests/unit/manager/sokovan/::
```

#### Scheduler Handler Line Coverage

| File | Stmts | Miss | Cover | Notes |
|------|-------|------|-------|-------|
| **scheduler/coordinator.py** | 406 | 406 | **0%** | ❌ No tests |
| **scheduler/factory.py** | 68 | 68 | **0%** | ❌ No tests |
| scheduler/handlers/base.py | 37 | 37 | **0%** | ❌ No tests |
| scheduler/handlers/lifecycle/check_precondition.py | 52 | 52 | **0%** | ❌ No tests |
| scheduler/handlers/lifecycle/schedule_sessions.py | 60 | 60 | **0%** | ❌ No tests |
| scheduler/handlers/lifecycle/start_sessions.py | 51 | 51 | **0%** | ❌ No tests |
| scheduler/handlers/lifecycle/terminate_sessions.py | 46 | 46 | **0%** | ❌ No tests |
| scheduler/handlers/lifecycle/deprioritize_sessions.py | 47 | 47 | **0%** | ❌ No tests |
| scheduler/handlers/maintenance/sweep_sessions.py | 53 | 53 | **0%** | ❌ No tests |
| scheduler/handlers/promotion/base.py | 39 | 39 | **0%** | ❌ No tests |
| scheduler/handlers/promotion/promote_to_prepared.py | 38 | 38 | **0%** | ❌ No tests |
| scheduler/handlers/promotion/promote_to_running.py | 45 | 45 | **0%** | ❌ No tests |
| scheduler/handlers/promotion/detect_termination.py | 51 | 51 | **0%** | ❌ No tests |
| scheduler/handlers/promotion/promote_to_terminated.py | 51 | 51 | **0%** | ❌ No tests |
| scheduler/handlers/kernel/base.py | 30 | 30 | **0%** | ❌ No tests |
| scheduler/handlers/kernel/sweep_stale_kernels.py | 46 | 46 | **0%** | ❌ No tests |
| scheduler/hooks/registry.py | 34 | 34 | **0%** | ❌ No tests |
| scheduler/hooks/status.py | 113 | 113 | **0%** | ❌ No tests |
| scheduler/launcher/launcher.py | 201 | 201 | **0%** | ❌ No tests |
| scheduler/kernel/state_engine.py | 50 | 50 | **0%** | ❌ No tests |
| **Handler Subtotal** | **1,518** | **1,518** | **0%** | |

#### Scheduler Provisioner Line Coverage (✅ Well Tested)

| File | Stmts | Miss | Cover |
|------|-------|------|-------|
| scheduler/provisioner/provisioner.py | 176 | 32 | 82% |
| scheduler/provisioner/selectors/selector.py | 172 | 14 | 92% |
| scheduler/provisioner/selectors/concentrated.py | 28 | 2 | 93% |
| scheduler/provisioner/selectors/dispersed.py | 18 | 2 | 89% |
| scheduler/provisioner/selectors/legacy.py | 18 | 2 | 89% |
| scheduler/provisioner/selectors/roundrobin.py | 13 | 2 | 85% |
| scheduler/provisioner/selectors/utils.py | 19 | 0 | 100% |
| scheduler/provisioner/sequencers/fifo.py | 15 | 0 | 100% |
| scheduler/provisioner/sequencers/lifo.py | 17 | 5 | 71% |
| scheduler/provisioner/sequencers/drf.py | 35 | 1 | 97% |
| **Provisioner Subtotal** | **~500** | **~60** | **~88%** |

#### Deployment Handler Line Coverage

| File | Stmts | Miss | Cover | Notes |
|------|-------|------|-------|-------|
| deployment/coordinator.py | 129 | 21 | 84% | History recording only |
| deployment/handlers/base.py | 38 | 8 | 79% | Indirectly called from Coordinator |
| deployment/handlers/pending.py | 41 | 8 | 80% | Indirectly called from Coordinator |
| deployment/handlers/replica.py | 40 | 10 | 75% | Indirectly called from Coordinator |
| deployment/handlers/scaling.py | 44 | 11 | 75% | Indirectly called from Coordinator |
| deployment/handlers/reconcile.py | 41 | 11 | 73% | Indirectly called from Coordinator |
| deployment/handlers/destroying.py | 44 | 11 | 75% | Indirectly called from Coordinator |
| deployment/executor.py | 252 | 196 | **22%** | ⚠️ Low coverage |
| deployment/deployment_controller.py | 101 | 48 | 52% | |
| **Deployment Subtotal** | **~730** | **~324** | **~56%** |

#### Route Handler Line Coverage

| File | Stmts | Miss | Cover | Notes |
|------|-------|------|-------|-------|
| route/coordinator.py | 131 | 21 | 84% | History recording only |
| route/handlers/base.py | 42 | 9 | 79% | Indirectly called from Coordinator |
| route/handlers/provisioning.py | 42 | 7 | 83% | Indirectly called from Coordinator |
| route/handlers/health_check.py | 42 | 10 | 76% | Indirectly called from Coordinator |
| route/handlers/running.py | 43 | 11 | 74% | Indirectly called from Coordinator |
| route/handlers/route_eviction.py | 43 | 11 | 74% | Indirectly called from Coordinator |
| route/handlers/terminating.py | 42 | 10 | 76% | Indirectly called from Coordinator |
| route/handlers/service_discovery_sync.py | 48 | 16 | 67% | |
| route/executor.py | 187 | 149 | **20%** | ⚠️ Low coverage |
| **Route Subtotal** | **~620** | **~244** | **~61%** |

### Coverage Gap Summary

| Area | Lines | Coverage | Status |
|------|-------|----------|--------|
| Scheduler Handlers | 1,518 | **0%** | ❌ Critical |
| Scheduler Provisioner | ~500 | ~88% | ✅ Good |
| Deployment | ~730 | ~56% | ⚠️ Partial |
| Route | ~620 | ~61% | ⚠️ Partial |

**Core Issue**: Scheduler Handler area has **1,518 lines at 0% coverage**

---

### Test Count

### Sokovan Scheduler (180 tests)

| Component | Test Count | Test Content |
|-----------|-----------|--------------|
| **provisioner/selectors** | 61 | Agent selection strategies (concentrated, dispersed, roundrobin, legacy) |
| **provisioner/validators** | 38 | Resource limit validation (quota, concurrency, dependencies) |
| **provisioner/sequencers** | 16 | Scheduling order (FIFO, LIFO, DRF) |
| **recorder** | 39 | History recording |
| **provisioner (root)** | 6 | Provisioner integration, agent selection strategy |
| **test_scheduler.py** | 9 | SessionProvisioner allocation |
| **test_terminate_sessions.py** | 6 | SessionTerminator |

### Sokovan Deployment (24 tests)

| Component | Test Count | Test Content |
|-----------|-----------|--------------|
| **revision_generator** | 9 | Service definition load, merge |
| **definition_generator** | 6 | Model definition registry |
| **route/coordinator_history** | 5 | Route status history recording |
| **coordinator_history** | 4 | Deployment status history recording |

### Sokovan Scheduling Controller (54 tests)

| Component | Test Count | Test Content |
|-----------|-----------|--------------|
| **validators/test_rules** | 13 | Validation rules |
| **validators/test_scaling_group_filter** | 12 | Scaling group filter |
| **validators/test_mount** | 12 | Mount validation |
| **test_integration** | 10 | Integration tests |
| **preparers/test_cluster** | 7 | Cluster preparation |

### Repository Tests (43 tests)

| Component | Test Count | Test Content |
|-----------|-----------|--------------|
| **scheduler/test_update_with_history** | 18 | Status update with history |
| **scheduler/test_termination** | 12 | Termination handling (some broken) |
| **schedule/test_termination** | 8 | Legacy termination |
| **schedule/test_fetch_pending_sessions** | 3 | Pending session retrieval |
| **scheduler/test_db_source_isolation** | 2 | DB source isolation |

### Coverage Gap Analysis

#### ❌ No Tests (Critical)

| Area | Handler | Current Status |
|------|---------|----------------|
| Scheduler Lifecycle | CheckPreconditionLifecycleHandler | **No tests** |
| Scheduler Lifecycle | ScheduleSessionsLifecycleHandler | **No tests** |
| Scheduler Lifecycle | StartSessionsLifecycleHandler | **No tests** |
| Scheduler Lifecycle | TerminateSessionsLifecycleHandler | Terminator only tested (6) |
| Scheduler Lifecycle | DeprioritizeSessionsLifecycleHandler | **No tests** |
| Scheduler Maintenance | SweepSessionsLifecycleHandler | **No tests** |
| Scheduler Promotion | PromoteToPreparedPromotionHandler | **No tests** |
| Scheduler Promotion | PromoteToRunningPromotionHandler | **No tests** |
| Scheduler Promotion | DetectTerminationPromotionHandler | **No tests** |
| Scheduler Promotion | PromoteToTerminatedPromotionHandler | **No tests** |
| Scheduler Kernel | SweepStaleKernelsKernelHandler | **No tests** |
| Scheduler | Coordinator | **No tests** |
| Deployment | CheckPendingDeploymentHandler | **No tests** |
| Deployment | CheckReplicaDeploymentHandler | **No tests** |
| Deployment | ScalingDeploymentHandler | **No tests** |
| Deployment | ReconcileDeploymentHandler | **No tests** |
| Deployment | DestroyingDeploymentHandler | **No tests** |
| Deployment | DeploymentCoordinator | History recording only tested (4) |
| Route | ProvisioningRouteHandler | **No tests** |
| Route | HealthCheckRouteHandler | **No tests** |
| Route | RunningRouteHandler | **No tests** |
| Route | RouteEvictionRouteHandler | **No tests** |
| Route | TerminatingRouteHandler | **No tests** |
| Route | ServiceDiscoverySyncRouteHandler | **No tests** |
| Route | RouteCoordinator | History recording only tested (5) |

#### ✅ Well Tested (Good)

| Area | Test Count | Coverage |
|------|-----------|----------|
| Agent Selector strategies | 61 | ✅ Sufficient |
| Provisioner Validators | 38 | ✅ Sufficient |
| Sequencers | 16 | ✅ Sufficient |
| Recorder | 39 | ✅ Sufficient |
| Scheduling Controller Validators | 37 | ✅ Sufficient |

#### ⚠️ Partially Tested (Partial)

| Area | Current | Needed |
|------|---------|--------|
| SessionProvisioner | 9 allocation tests | Need to add validation flow |
| SessionTerminator | 6 tests | Need to add various error cases |
| Coordinator History | 9 tests | Need failure classification tests |

### Test Directory Structure (Current)

```
tests/unit/manager/
├── sokovan/
│   ├── scheduler/
│   │   ├── provisioner/
│   │   │   ├── selectors/        # ✅ 61 tests
│   │   │   ├── validators/       # ✅ 38 tests
│   │   │   └── sequencers/       # ✅ 16 tests
│   │   ├── recorder/             # ✅ 39 tests
│   │   ├── test_scheduler.py     # ⚠️ 9 tests (Provisioner only)
│   │   └── test_terminate_sessions.py  # ⚠️ 6 tests
│   │   └── handlers/             # ❌ None
│   ├── deployment/
│   │   ├── definition_generator/ # ⚠️ 6 tests
│   │   ├── revision_generator/   # ⚠️ 9 tests
│   │   ├── route/
│   │   │   └── test_coordinator_history.py  # ⚠️ 5 tests
│   │   ├── test_coordinator_history.py      # ⚠️ 4 tests
│   │   └── handlers/             # ❌ None
│   └── scheduling_controller/
│       ├── validators/           # ✅ 37 tests
│       ├── preparers/            # ✅ 7 tests
│       └── test_integration.py   # ✅ 10 tests
└── repositories/
    ├── scheduler/                # ⚠️ 32 tests
    └── schedule/                 # ⚠️ 11 tests
```

## Current Design

### Handler Architecture Overview

```
sokovan/
├── scheduler/
│   └── handlers/
│       ├── lifecycle/          # Session lifecycle
│       ├── promotion/          # Status promotion
│       ├── maintenance/        # Maintenance
│       └── kernel/             # Kernel level
├── deployment/
│   ├── handlers/               # Deployment lifecycle
│   └── route/
│       └── handlers/           # Route lifecycle
```

### Scheduler Handlers (12)

| Category | Handler | Responsibility |
|----------|---------|----------------|
| Lifecycle | CheckPreconditionLifecycleHandler | Pre-scheduling condition checks (quota, resource policy) |
| Lifecycle | ScheduleSessionsLifecycleHandler | Session-agent matching and allocation |
| Lifecycle | StartSessionsLifecycleHandler | Start allocated sessions (SCHEDULED → PREPARING) |
| Lifecycle | TerminateSessionsLifecycleHandler | Session termination handling |
| Lifecycle | DeprioritizeSessionsLifecycleHandler | Priority demotion for sessions exceeding retries |
| Maintenance | SweepSessionsLifecycleHandler | Orphaned session cleanup |
| Promotion | PromoteToPreparedPromotionHandler | PULLING → PREPARED promotion |
| Promotion | PromoteToRunningPromotionHandler | PREPARED → RUNNING promotion |
| Promotion | DetectTerminationPromotionHandler | Termination state detection (TERMINATING sessions) |
| Promotion | PromoteToTerminatedPromotionHandler | → TERMINATED final promotion |
| Kernel | SweepStaleKernelsKernelHandler | Stale kernel cleanup |

### Deployment Handlers (5)

| Handler | Responsibility |
|---------|----------------|
| CheckPendingDeploymentHandler | PENDING deployment handling |
| CheckReplicaDeploymentHandler | Replica status check |
| ScalingDeploymentHandler | Scale up/down handling |
| ReconcileDeploymentHandler | State inconsistency reconciliation |
| DestroyingDeploymentHandler | Deployment deletion handling |

### Route Handlers (6)

| Handler | Responsibility |
|---------|----------------|
| ProvisioningRouteHandler | Route provisioning |
| HealthCheckRouteHandler | Route health check |
| RunningRouteHandler | Running route management |
| RouteEvictionRouteHandler | Route eviction handling |
| TerminatingRouteHandler | Route termination handling |
| ServiceDiscoverySyncRouteHandler | Service discovery synchronization |

## Proposed Design

### Test Classification System

```
tests/unit/manager/sokovan/
├── scheduler/
│   └── handlers/
│       ├── lifecycle/
│       │   ├── test_check_precondition.py
│       │   ├── test_schedule_sessions.py
│       │   ├── test_start_sessions.py
│       │   ├── test_terminate_sessions.py
│       │   ├── test_deprioritize_sessions.py
│       │   └── test_sweep_sessions.py
│       ├── promotion/
│       │   ├── test_promote_to_prepared.py
│       │   ├── test_promote_to_running.py
│       │   ├── test_detect_termination.py
│       │   └── test_promote_to_terminated.py
│       ├── kernel/
│       │   └── test_sweep_stale_kernels.py
│       └── test_coordinator_integration.py
├── deployment/
│   ├── handlers/
│   │   ├── test_check_pending.py
│   │   ├── test_check_replica.py
│   │   ├── test_scaling.py
│   │   ├── test_reconcile.py
│   │   └── test_destroying.py
│   └── route/
│       └── handlers/
│           ├── test_provisioning.py
│           ├── test_health_check.py
│           ├── test_running.py
│           ├── test_route_eviction.py
│           ├── test_terminating.py
│           └── test_service_discovery_sync.py
```

---

## Test Scenarios

### 1. Scheduler Lifecycle Handlers

#### 1.1 CheckPreconditionLifecycleHandler

**Purpose**: Pre-scheduling condition checks (quota, resource policy, domain/group settings)

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| CP-001 | All conditions met | Valid PENDING session | Included in successes |
| CP-002 | Quota exceeded | User quota at 100%, new session request | Included in failures, status_info="quota-exceeded" |
| CP-003 | Domain disabled | Session from domain with is_active=False | Included in failures |
| CP-004 | Group disabled | Session from group with is_active=False | Included in failures |
| CP-005 | Resource policy violation | max_vfolder_count exceeded | Included in failures |
| CP-006 | Empty input | No sessions | Empty result returned |
| CP-007 | Mixed failures | Some succeed, some fail | Each classified accordingly |

#### 1.2 ScheduleSessionsLifecycleHandler

**Purpose**: Session-agent matching and resource allocation

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| SS-001 | Single session scheduling | 1 PENDING session, sufficient agents | successes, agent assigned |
| SS-002 | Multiple session scheduling | N PENDING sessions, sufficient agents | All successes |
| SS-003 | Insufficient resources | Session request > available resources | failures, status_info="no-available-agent" |
| SS-004 | Designated agent used | designated_agent_ids set | Assigned only to designated agents |
| SS-005 | Designated agent absent | Non-existent agent designated | failures |
| SS-006 | Cluster session | cluster_size > 1 | All kernels assigned |
| SS-007 | Mixed workload | GPU + CPU sessions | Each assigned to appropriate agent |
| SS-008 | Priority scheduling | Sessions with different priorities | Higher priority first |
| SS-009 | starts_at reservation | Future time set | Skipped until scheduled time |
| SS-010 | Private session | is_private=True | Dedicated agent or failure |

#### 1.3 StartSessionsLifecycleHandler

**Purpose**: SCHEDULED session start trigger

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| ST-001 | Normal start | SCHEDULED session | successes, prepare_session called |
| ST-002 | Agent connection failure | Agent unreachable | failures |
| ST-003 | Image pulling starts | Agent without image | Transition to PULLING state |
| ST-004 | Image cache exists | Agent with image | PREPARING → PREPARED |
| ST-005 | Cluster start | Multi-kernel session | All kernels started |
| ST-006 | Partial failure | Only some kernels fail to start | failures (entire session) |

#### 1.4 TerminateSessionsLifecycleHandler

**Purpose**: TERMINATING session termination handling

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| TS-001 | Normal termination | TERMINATING session | successes, kernel destroy called |
| TS-002 | Agent LOST | Agent status=LOST | successes (forced termination) |
| TS-003 | No container | container_id=None | successes (DB update only) |
| TS-004 | Partial kernel failure | Some kernel destroy failures | Failed kernels await retry |
| TS-005 | Cluster termination | Multi-kernel session | All kernels terminated |
| TS-006 | Already terminated | Kernel already TERMINATED | skipped |

#### 1.5 DeprioritizeSessionsLifecycleHandler

**Purpose**: Priority demotion handling for sessions exceeding retries

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| DP-001 | Priority demotion | DEPRIORITIZING session | Transition to PENDING, lower priority |
| DP-002 | Already lowest priority | priority=0 | Transition to CANCELLED |
| DP-003 | Empty input | No sessions | Empty result |

#### 1.6 SweepSessionsLifecycleHandler

**Purpose**: Orphaned session cleanup

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| SW-001 | Stale PREPARING | PREPARING state > timeout | Transition to TERMINATING |
| SW-002 | Stale PULLING | PULLING state > timeout | Transition to TERMINATING |
| SW-003 | Normal session | Timeout not exceeded | skipped |
| SW-004 | Session without kernels | Session exists, 0 kernels | Transition to CANCELLED |

---

### 2. Scheduler Promotion Handlers

#### 2.1 PromoteToPreparedPromotionHandler

**Purpose**: Confirm image pulling completion and promote to PREPARED

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| PP-001 | Pulling complete | All kernel images ready | successes, transition to PREPARED |
| PP-002 | Pulling in progress | Some kernels still pulling | skipped |
| PP-003 | Pulling failed | Error from agent | failures |
| PP-004 | Cluster pulling | Multi-kernel session | Promote when all kernels complete |
| PP-005 | Timeout exceeded | PULLING > 15 minutes | failures (expired) |

#### 2.2 PromoteToRunningPromotionHandler

**Purpose**: Confirm container creation completion and promote to RUNNING

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| PR-001 | Creation complete | All kernels have container_id | successes, transition to RUNNING |
| PR-002 | Creation in progress | container_id=None | skipped |
| PR-003 | Creation failed | Agent error | failures |
| PR-004 | Cluster creation | Multi-kernel | Promote when all kernels complete |
| PR-005 | Timeout exceeded | CREATING > 10 minutes | failures (expired) |
| PR-006 | Partial failure | Only some kernels created | failures (entire session) |

#### 2.3 DetectTerminationPromotionHandler

**Purpose**: Detect kernel termination status for TERMINATING sessions

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| DT-001 | All kernels terminated | All kernels TERMINATED | successes |
| DT-002 | Termination in progress | Some kernels TERMINATING | skipped |
| DT-003 | Agent LOST | Agent unreachable | successes (forced completion) |
| DT-004 | Mixed state | Some TERMINATED, some RUNNING | skipped |

#### 2.4 PromoteToTerminatedPromotionHandler

**Purpose**: Transition session to TERMINATED final state

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| PT-001 | Normal termination | TERMINATING session | TERMINATED, result recorded |
| PT-002 | Terminated with error | status_info="error" | TERMINATED, result=ERROR |
| PT-003 | User cancellation | status_info="user-requested" | TERMINATED, result=USER_CANCELLED |

---

### 3. Scheduler Kernel Handlers

#### 3.1 SweepStaleKernelsKernelHandler

**Purpose**: Detect and handle stale RUNNING kernels

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| SK-001 | Stale kernel detected | last_stat > threshold | Kernel transition to TERMINATING |
| SK-002 | Normal kernel | last_stat is recent | No change |
| SK-003 | Agent LOST | Agent unreachable | Kernel transition to TERMINATING |
| SK-004 | No container | container_id=None, RUNNING | Kernel transition to TERMINATED |

---

### 4. Deployment Handlers

#### 4.1 CheckPendingDeploymentHandler

**Purpose**: PENDING deployment handling and initial session creation

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| CD-001 | New deployment | PENDING state | Transition to PROVISIONING, session creation request |
| CD-002 | Insufficient resources | No available resources | Remain PENDING, await retry |
| CD-003 | Configuration error | Invalid image | Transition to FAILED |

#### 4.2 CheckReplicaDeploymentHandler

**Purpose**: Verify replica count maintenance

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| CR-001 | Replicas normal | current == desired | No change |
| CR-002 | Replicas insufficient | current < desired | Scale-up trigger |
| CR-003 | Replicas exceeded | current > desired | Scale-down trigger |
| CR-004 | Unhealthy replicas | Unhealthy replicas present | Replacement trigger |

#### 4.3 ScalingDeploymentHandler

**Purpose**: Execute deployment scale up/down

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| SC-001 | Scale up | desired_replicas increased | New sessions created |
| SC-002 | Scale down | desired_replicas decreased | Sessions terminated (lowest priority first) |
| SC-003 | Gradual scaling | Large change | Batch processing |
| SC-004 | Scale up with insufficient resources | No available resources | Partial scale-up, remainder awaits |

#### 4.4 ReconcileDeploymentHandler

**Purpose**: State inconsistency reconciliation

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| RC-001 | Session state mismatch | DB and actual state differ | State synchronization |
| RC-002 | Orphaned session | Session without deployment | Session terminated |
| RC-003 | Route mismatch | Replica without route | Route created |

#### 4.5 DestroyingDeploymentHandler

**Purpose**: Deployment deletion handling

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| DD-001 | Normal deletion | DESTROYING deployment | All sessions terminated, transition to DESTROYED |
| DD-002 | Sessions terminating | Some sessions TERMINATING | Remain DESTROYING, wait |
| DD-003 | Force deletion | force=True | Immediate DESTROYED, async cleanup |

---

### 5. Route Handlers

#### 5.1 ProvisioningRouteHandler

**Purpose**: Route initial provisioning

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| RP-001 | Normal provisioning | PROVISIONING route | Session connected, transition to HEALTH_CHECKING |
| RP-002 | Session not ready | Session still PREPARING | Remain PROVISIONING |
| RP-003 | Session failed | Session TERMINATED | Transition to FAILED |

#### 5.2 HealthCheckRouteHandler

**Purpose**: Route health check execution

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| RH-001 | Health check passed | Endpoint responds normally | Transition to RUNNING |
| RH-002 | Health check failed | Endpoint unresponsive | FAILED after retries |
| RH-003 | Timeout | Response delayed | Retry |
| RH-004 | Consecutive successes required | success_threshold=3 | Transition after 3 consecutive successes |

#### 5.3 RunningRouteHandler

**Purpose**: Running route monitoring

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| RR-001 | Normal state | Health check passed | Remain RUNNING |
| RR-002 | Health check failed | Consecutive failures | Transition to UNHEALTHY |
| RR-003 | Session terminated | Connected session TERMINATED | Transition to TERMINATING |
| RR-004 | Traffic distribution | Weight updated | Routing table refreshed |

#### 5.4 RouteEvictionRouteHandler

**Purpose**: Unhealthy route eviction

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| RE-001 | Eviction executed | UNHEALTHY route | Transition to EVICTING, traffic blocked |
| RE-002 | Replacement route exists | Other healthy routes available | Traffic redistributed |
| RE-003 | Last route | No replacement available | Warning raised, service down notification |

#### 5.5 TerminatingRouteHandler

**Purpose**: Route termination handling

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| RT-001 | Normal termination | TERMINATING route | Transition to TERMINATED |
| RT-002 | Connection drain | Active connections exist | Wait for drain completion |
| RT-003 | Force termination | Timeout exceeded | Immediate TERMINATED |

#### 5.6 ServiceDiscoverySyncRouteHandler

**Purpose**: Service discovery synchronization

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| SD-001 | Route registration | New RUNNING route | Registered in discovery |
| SD-002 | Route deregistration | TERMINATED route | Removed from discovery |
| SD-003 | Metadata update | Weight changed | Discovery metadata refreshed |
| SD-004 | Sync failure | Discovery connection failure | Queued for retry |

---

### 6. Coordinator Integration Tests

#### 6.1 Failure Classification

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| FC-001 | Need Retry | First failure, timeout not exceeded | Retry transition applied |
| FC-002 | Expired | Timeout exceeded | Expired transition applied |
| FC-003 | Give Up | max_retries exceeded | give_up transition applied |

#### 6.2 Hook Execution

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| HE-001 | Running Hook | RUNNING transition succeeded | occupied_slots updated, event published |
| HE-002 | Terminated Hook | TERMINATED transition succeeded | Resources released, event published |
| HE-003 | Hook failure | Exception during hook execution | Logged, transition still completed |

#### 6.3 Distributed Lock

| ID | Scenario | Input | Expected Result |
|----|----------|-------|-----------------|
| DL-001 | Lock acquired | First request | Handler executed |
| DL-002 | Lock contention | Concurrent requests | Only one executed, others wait |
| DL-003 | Lock timeout | Long wait | Retry on next cycle after timeout |

---

## Migration / Compatibility

### Backward Compatibility
- Existing tests are maintained, but gradually migrated to the new pattern
- Mock-based unit tests and real DB-based integration tests run in parallel

### Breaking Changes
- None (test code additions only)

## Implementation Plan

### Phase 1: Test Infrastructure Setup
1. Create test directory structure
2. Define common fixtures (mock repository, mock launcher, etc.)
3. Create test data factories

### Phase 2: Scheduler Handler Tests
1. Lifecycle Handler tests (6)
2. Promotion Handler tests (4)
3. Kernel Handler tests (1)
4. Coordinator integration tests

### Phase 3: Deployment Handler Tests
1. Deployment Handler tests (5)
2. Route Handler tests (6)

### Phase 4: E2E Scenario Tests
1. Full session lifecycle tests
2. Deployment scaling scenarios
3. Failure recovery scenarios

## Open Questions

1. What should the Mock vs Real DB ratio be?
   - Unit tests: Mock-based
   - Integration tests: Real DB (PostgreSQL testcontainer)
==> Planning to use Real DB only in repository tests and component tests

2. How to test external dependencies (agent RPC)?
   - Use mock agent client
   - Use real agent in integration tests if needed

3. How to verify asynchronous events?
   - Capture published events with EventProducer mock
   - Verify event contents with assertions

## References

- [BEP-1029: Sokovan Observer Handler](BEP-1029-sokovan-observer-handler.md)
- [BEP-1030: Sokovan Scheduler Status Transition](BEP-1030-sokovan-scheduler-status-transition.md)
- [BA-3936: Scheduling Coordinator Integration](https://lablup.atlassian.net/browse/BA-3936)
