# BEP-1033 Sokovan Handler Test Scenarios - Overview

## Purpose

This document series defines test scenarios for Sokovan scheduler components based on actual code analysis. Each scenario is designed to be implementable as a pytest test case.

## Target Components

| Category | Component | Document |
|----------|-----------|----------|
| **Scheduler Handlers** | Lifecycle Handlers | [01-scheduler-lifecycle-handlers.md](./01-scheduler-lifecycle-handlers.md) |
| | Promotion Handlers | [02-scheduler-promotion-handlers.md](./02-scheduler-promotion-handlers.md) |
| | Kernel Handlers | [03-scheduler-kernel-handlers.md](./03-scheduler-kernel-handlers.md) |
| **Core Components** | ScheduleCoordinator | [04-scheduler-coordinator.md](./04-scheduler-coordinator.md) |
| | SessionProvisioner | [05-provisioner.md](./05-provisioner.md) |
| | SessionLauncher | [06-launcher.md](./06-launcher.md) |
| | SessionTerminator | [07-terminator.md](./07-terminator.md) |
| **Deployment/Route** | DeploymentExecutor | [08-deployment-executor.md](./08-deployment-executor.md) |
| | RouteExecutor | [09-route-executor.md](./09-route-executor.md) |

## Code Architecture Summary

### Handler Execution Pattern

All handlers are executed consistently by the Coordinator following this pattern:
1. Acquire lock (if `handler.lock_id` is set)
2. Query sessions per scaling group based on `target_statuses()` and `target_kernel_statuses()`
3. Set `phase_attempts` and `phase_started_at` from scheduling history
4. Execute `handler.execute(scaling_group, sessions)`
5. Classify failures as `give_up`, `expired`, or `need_retry`
6. Apply status transitions based on `handler.status_transitions()`
7. Broadcast events
8. Execute PostProcessor chain (schedule marking, cache invalidation)

### PostProcessor Architecture

The Coordinator performs common post-processing tasks through a PostProcessor chain after handler execution:

```python
# Source: sokovan/scheduler/post_processors/

class PostProcessor(ABC):
    @abstractmethod
    async def execute(self, context: PostProcessorContext) -> None:
        ...

@dataclass
class PostProcessorContext:
    result: SessionExecutionResult
    target_status: SessionStatus | None
```

**Default PostProcessor Chain:**
1. `ScheduleMarkingPostProcessor`: Marks next schedule type based on status transition
2. `CacheInvalidationPostProcessor`: Invalidates kernel-related cache for affected access keys

**STATUS_TO_NEXT_SCHEDULE_TYPE Mapping:**
| target_status | next_schedule_type |
|---------------|-------------------|
| SCHEDULED | CHECK_PRECONDITION |
| PULLING | START |
| PREPARING | START |
| RUNNING | START |
| TERMINATED | SCHEDULE |
| TERMINATING | CHECK_TERMINATING_PROGRESS |
| PENDING, PREPARED, CREATING, DEPRIORITIZING | None (no marking) |

### Handler Types

| Type | Input Data | Kernel Matching Logic |
|------|------------|----------------------|
| **Lifecycle Handler** | `SessionWithKernels` | ANY match (at least one kernel matches) |
| **Promotion Handler** | `SessionInfo` | ALL/ANY/NOT_ANY match (configurable) |
| **Kernel Handler** | `KernelInfo` | Direct kernel status filtering |

### Status Transition Definition (BEP-1030)

Handlers define transitions via `status_transitions()`:

```python
StatusTransitions(
    success=TransitionStatus(session=..., kernel=...),  # On success
    need_retry=...,  # Retryable (default for failures)
    expired=...,     # Timeout exceeded
    give_up=...,     # Max retries exceeded
)
```

## Scenario Format

Each scenario follows this structure:

```markdown
### SC-XX-NNN: Scenario Title

- **Purpose**: What this test verifies
- **Dependencies (Mock):**
  - `component.method()`: Return value or exception
- **Input:**
  - Data passed to handler.execute()
- **Execution:** `await handler.execute(scaling_group, sessions)`
- **Verification:**
  - **Return Value**: Expected result structure
  - **Mock Calls**: Dependency call verification
  - **Side Effects**: State changes (if any)
- **Classification**: `happy-path` | `error-case` | `edge-case`
```

## Test Implementation Guidelines

### Mock Hierarchy

```
Handler Tests:
├── Mock: Repository, Launcher, Terminator, Provisioner
└── Real: Handler logic

Coordinator Tests:
├── Mock: Repository, Handler, HookRegistry, EventProducer, PostProcessors
└── Real: Failure classification, transition application, PostProcessor chain execution

PostProcessor Tests:
├── Mock: SchedulingController, Repository
└── Real: PostProcessor logic

Component Tests (Provisioner/Launcher/Terminator):
├── Mock: AgentClientPool, ValkeyScheduleClient, Repository
└── Real: Business logic
```

### Common Test Fixtures

```python
@pytest.fixture
def session_with_kernels() -> SessionWithKernels:
    """SessionWithKernels test data factory."""
    ...

@pytest.fixture
def scheduling_data() -> SchedulingData:
    """SchedulingData factory (provisioner input)."""
    ...

@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock SchedulerRepository with common methods."""
    ...
```

### Assertion Patterns

```python
# Handler result verification
assert len(result.successes) == expected_count
assert result.successes[0].session_id == expected_id
assert result.successes[0].reason == "expected-reason"

# Mock call verification
mock_launcher.trigger_image_pulling.assert_called_once()
mock_repository.get_scheduling_data.assert_called_with(scaling_group)

# Transition info verification
info = result.successes[0]
assert info.from_status == SessionStatus.PENDING
assert info.access_key == expected_access_key
```

## Coverage Summary

| Component | Scenarios | Happy Path | Error Cases | Edge Cases |
|-----------|-----------|------------|-------------|------------|
| Lifecycle Handlers | 19 | 7 | 3 | 9 |
| Promotion Handlers | 14 | 8 | 1 | 5 |
| Kernel Handlers | 10 | 5 | 1 | 4 |
| Coordinator | 25 | 16 | 2 | 7 |
| Provisioner (Integration) | 15 | 9 | 4 | 2 |
| - Validator | 18 | 9 | 9 | 0 |
| - Sequencer | 7 | 5 | 0 | 2 |
| - Selector | 12 | 7 | 4 | 1 |
| - Allocator | 4 | 1 | 2 | 1 |
| Launcher | 18 | 11 | 6 | 1 |
| Terminator | 17 | 7 | 3 | 7 |
| DeploymentExecutor | 19 | 9 | 6 | 4 |
| RouteExecutor | 24 | 12 | 7 | 5 |
| **Total** | **202** | **106** | **48** | **48** |

**Note:** Handler post_process test scenarios have been integrated into Coordinator's PostProcessor scenarios.

## Key Findings from Code Analysis

### 1. Handler Return Behavior

| Handler | Returns successes? | Returns failures? | Returns skipped? | post_process behavior |
|---------|-------------------|------------------|-----------------|----------------------|
| CheckPrecondition | All as success | No | No | no-op (handled by Coordinator PostProcessor) |
| ScheduleSessions | From provisioner result | No | Non-scheduled sessions | no-op (handled by Coordinator PostProcessor) |
| StartSessions | All as success | No | No | no-op |
| DeprioritizeSessions | All as success | No | No | no-op |
| TerminateSessions | None (empty result) | No | No | no-op (event-based) |
| SweepSessions | No | Timed-out as failure | No | no-op (handled by Coordinator PostProcessor) |
| Promotion Handlers | All as success | No | No | no-op (handled by Coordinator PostProcessor) |
| SweepStaleKernels | Alive as success | Dead as failure | No | no-op (handled by Coordinator) |

**Note**: All handlers' `post_process()` are essentially no-op. Schedule marking and cache invalidation are handled collectively by the Coordinator's PostProcessor chain.

### 2. Coordinator Failure Classification

Failures are classified based on these criteria:
1. **give_up**: `phase_attempts >= SERVICE_MAX_RETRIES` (5)
2. **expired**: `elapsed > STATUS_TIMEOUT_MAP[status]`
   - PREPARING: 900 seconds (15 minutes)
   - PULLING: 900 seconds (15 minutes)
   - CREATING: 600 seconds (10 minutes)
3. **need_retry**: Default (neither give_up nor expired)

### 3. Hook Execution

Hooks are executed for specific status transitions:
- `SessionStatus.RUNNING`: occupied_slots calculation, BATCH/INFERENCE type handling
- `SessionStatus.TERMINATED`: Cleanup tasks
- Hook failures block the transition (all hooks are blocking)

### 4. Event Broadcasting

Events are broadcast after status transitions for:
- All successful Lifecycle handler transitions (when `transitions.success.session` is set)
- All successful Promotion handler transitions
- Not applicable to Kernel handlers (kernel events originate from agents)
