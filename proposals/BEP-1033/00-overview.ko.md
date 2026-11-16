# BEP-1033 Sokovan handler 테스트 시나리오 개요

## 목적

이 문서 시리즈는 실제 코드 분석을 바탕으로 Sokovan scheduler 구성 요소의 테스트 시나리오를 정의한다. 각 시나리오는 pytest 테스트 케이스로 구현할 수 있게 설계한다.

## 대상 구성 요소

| 분류 | 구성 요소 | 문서 |
|----------|-----------|----------|
| **scheduler handler** | 수명 주기 handler | [01-scheduler-lifecycle-handlers.md](./01-scheduler-lifecycle-handlers.md) |
| | 승격 handler | [02-scheduler-promotion-handlers.md](./02-scheduler-promotion-handlers.md) |
| | kernel handler | [03-scheduler-kernel-handlers.md](./03-scheduler-kernel-handlers.md) |
| **핵심 구성 요소** | ScheduleCoordinator | [04-scheduler-coordinator.md](./04-scheduler-coordinator.md) |
| | SessionProvisioner | [05-provisioner.md](./05-provisioner.md) |
| | SessionLauncher | [06-launcher.md](./06-launcher.md) |
| | SessionTerminator | [07-terminator.md](./07-terminator.md) |
| **배포/route** | DeploymentExecutor | [08-deployment-executor.md](./08-deployment-executor.md) |
| | RouteExecutor | [09-route-executor.md](./09-route-executor.md) |

## 코드 구조 요약

### handler 실행 패턴

모든 handler 는 sokovan coordinator 가 다음 패턴으로 일관되게 실행한다:
1. lock 을 획득한다(`handler.lock_id` 가 설정된 경우)
2. `target_statuses()` 와 `target_kernel_statuses()` 를 기준으로 자원 그룹별 session 을 조회한다
3. 스케줄링 이력에서 `phase_attempts` 와 `phase_started_at` 을 설정한다
4. `handler.execute(scaling_group, sessions)` 를 실행한다
5. 실패를 `give_up`, `expired`, `need_retry` 로 분류한다
6. `handler.status_transitions()` 에 따라 상태 전이를 적용한다
7. event 를 브로드캐스트한다
8. PostProcessor chain 을 실행한다(schedule 표시, cache 무효화)

### PostProcessor 구조

sokovan coordinator 는 handler 실행 후 PostProcessor chain 으로 공통 후처리를 수행한다:

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

**기본 PostProcessor chain:**
1. `ScheduleMarkingPostProcessor`: 상태 전이에 따라 다음 schedule type 을 표시한다
2. `CacheInvalidationPostProcessor`: 영향을 받은 access key 의 kernel 관련 cache 를 무효화한다

**STATUS_TO_NEXT_SCHEDULE_TYPE 매핑:**
| target_status | next_schedule_type |
|---------------|-------------------|
| SCHEDULED | CHECK_PRECONDITION |
| PULLING | START |
| PREPARING | START |
| RUNNING | START |
| TERMINATED | SCHEDULE |
| TERMINATING | CHECK_TERMINATING_PROGRESS |
| PENDING, PREPARED, CREATING, DEPRIORITIZING | None (표시 없음) |

### handler 유형

| 유형 | 입력 데이터 | kernel 매칭 방식 |
|------|------------|----------------------|
| **수명 주기 handler** | `SessionWithKernels` | ANY 매칭(kernel 하나 이상이 일치) |
| **승격 handler** | `SessionInfo` | ALL/ANY/NOT_ANY 매칭(설정 가능) |
| **kernel handler** | `KernelInfo` | kernel 상태를 직접 필터링 |

### 상태 전이 정의(BEP-1030)

handler 는 `status_transitions()` 로 전이를 정의한다:

```python
StatusTransitions(
    success=TransitionStatus(session=..., kernel=...),  # On success
    need_retry=...,  # Retryable (default for failures)
    expired=...,     # Timeout exceeded
    give_up=...,     # Max retries exceeded
)
```

## 시나리오 형식

각 시나리오는 다음 구조를 따른다:

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

## 테스트 구현 지침

### mock 계층

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

### 공통 테스트 fixture

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

### 단언 패턴

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

## 커버리지 요약

| 구성 요소 | 시나리오 | happy path | error case | edge case |
|-----------|-----------|------------|-------------|------------|
| 수명 주기 handler | 19 | 7 | 3 | 9 |
| 승격 handler | 14 | 8 | 1 | 5 |
| kernel handler | 10 | 5 | 1 | 4 |
| sokovan coordinator | 25 | 16 | 2 | 7 |
| provisioner(통합) | 15 | 9 | 4 | 2 |
| - validator | 18 | 9 | 9 | 0 |
| - sequencer | 7 | 5 | 0 | 2 |
| - selector | 12 | 7 | 4 | 1 |
| - allocator | 4 | 1 | 2 | 1 |
| launcher | 18 | 11 | 6 | 1 |
| terminator | 17 | 7 | 3 | 7 |
| DeploymentExecutor | 19 | 9 | 6 | 4 |
| RouteExecutor | 24 | 12 | 7 | 5 |
| **합계** | **202** | **106** | **48** | **48** |

**참고:** handler 의 post_process 테스트 시나리오는 sokovan coordinator 의 PostProcessor 시나리오에 통합했다.

## 코드 분석 주요 발견

### 1. handler 반환 동작

| handler | successes 반환 | failures 반환 | skipped 반환 | post_process 동작 |
|---------|-------------------|------------------|-----------------|----------------------|
| CheckPrecondition | 모두 success | 없음 | 없음 | no-op(sokovan coordinator 의 PostProcessor 가 처리) |
| ScheduleSessions | provisioner 결과에서 | 없음 | 스케줄되지 않은 session | no-op(sokovan coordinator 의 PostProcessor 가 처리) |
| StartSessions | 모두 success | 없음 | 없음 | no-op |
| DeprioritizeSessions | 모두 success | 없음 | 없음 | no-op |
| TerminateSessions | 없음(빈 결과) | 없음 | 없음 | no-op(event 기반) |
| SweepSessions | 없음 | timeout 이 초과된 session 을 failure 로 | 없음 | no-op(sokovan coordinator 의 PostProcessor 가 처리) |
| 승격 handler | 모두 success | 없음 | 없음 | no-op(sokovan coordinator 의 PostProcessor 가 처리) |
| SweepStaleKernels | 살아 있는 kernel 을 success 로 | 종료된 kernel 을 failure 로 | 없음 | no-op(sokovan coordinator 가 처리) |

**참고**: 모든 handler 의 `post_process()` 는 사실상 no-op 이다. schedule 표시와 cache 무효화는 sokovan coordinator 의 PostProcessor chain 이 일괄 처리한다.

### 2. sokovan coordinator 의 실패 분류

실패는 다음 기준으로 분류한다:
1. **give_up**: `phase_attempts >= SERVICE_MAX_RETRIES` (5)
2. **expired**: `elapsed > STATUS_TIMEOUT_MAP[status]`
   - PREPARING: 900초(15분)
   - PULLING: 900초(15분)
   - CREATING: 600초(10분)
3. **need_retry**: 기본값(give_up 도 expired 도 아님)

### 3. hook 실행

hook 은 특정 상태 전이에서 실행한다:
- `SessionStatus.RUNNING`: occupied_slots 계산, BATCH/INFERENCE 유형 처리
- `SessionStatus.TERMINATED`: 정리 작업
- hook 실패는 전이를 차단한다(모든 hook 이 차단 방식이다)

### 4. event 브로드캐스트

event 는 상태 전이 후 다음 경우에 브로드캐스트한다:
- 수명 주기 handler 의 성공 전이 전체(`transitions.success.session` 이 설정된 경우)
- 승격 handler 의 성공 전이 전체
- kernel handler 에는 해당하지 않는다(kernel event 는 agent 에서 발생한다)
