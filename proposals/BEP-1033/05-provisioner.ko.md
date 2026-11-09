# Provisioner 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 Provisioner 구성 요소의 테스트 시나리오를 정의한다.

Provisioner 는 PENDING → SCHEDULED 상태 전이 파이프라인을 조정한다:
1. **Sequencing**: 설정된 FIFO, LIFO, DRF sequencer 로 workload 의 순서를 정한다
2. **Validation**: workload 마다 quota 와 제약을 확인한다
3. **Agent Selection**: 설정된 전략으로 agent 를 선택한다
4. **Allocation**: 할당 정보를 database 에 저장한다

**테스트 구조:**
- **SessionProvisioner**: Validator, Sequencer, Selector, Allocator 를 mock 으로 대체해 조정 동작을 테스트한다
- **Validator**: 개별 검증 규칙을 테스트한다
- **Sequencer**: 순서 결정 전략(FIFO, LIFO, DRF)을 테스트한다
- **Selector**: agent 선택 전략(RoundRobin, Concentrated, Dispersed)을 테스트한다
- **Allocator**: 할당 로직을 테스트한다

**소스 파일:**
- `sokovan/scheduler/provisioner/provisioner.py`
- `sokovan/scheduler/provisioner/validators/`
- `sokovan/scheduler/provisioner/sequencers/`
- `sokovan/scheduler/provisioner/selectors/`
- `sokovan/scheduler/provisioner/allocators/`

---

# 1부: SessionProvisioner 테스트

---

## schedule_scaling_group 흐름

```python
async def schedule_scaling_group(scaling_group, scheduling_data) -> ScheduleResult:
    # 1. Convert to SessionWorkload
    workloads = [session.to_session_workload() for session in scheduling_data.pending_sessions.sessions]

    # 2. Convert to SystemSnapshot
    system_snapshot = scheduling_data.snapshot_data.to_system_snapshot(...)

    # 3. Sequencing (shared step)
    sequenced_workloads = sequencer.sequence(system_snapshot, workloads)

    # 4. Per-workload processing
    for workload in sequenced_workloads:
        try:
            allocation = await _schedule_workload(workload, ...)
            session_allocations.append(allocation)
        except Exception:
            scheduling_failures.append(SchedulingFailure(...))

    # 5. Batch allocation
    scheduled_sessions = await allocator.allocate(batch)

    # 6. Update Valkey queue with failed sessions
    await valkey_schedule.set_pending_queue(scaling_group, failure_ids)

    return ScheduleResult(scheduled_sessions=scheduled_sessions)
```

---

## 의존성(mock 대상)

- `validator: SchedulingValidator`
  - `validate(snapshot, workload)` → 실패하면 예외를 발생시킨다
- `sequencer: SchedulingSequencer`
  - `sequence(snapshot, workloads)` → `list[SessionWorkload]`
- `agent_selector: AgentSelector`
  - `select_agents_for_batch_requirements(...)` → `list[AgentSelection]`
- `allocator: SchedulingAllocator`
  - `allocate(batch)` → `list[ScheduledSessionData]`
- `repository: SchedulerRepository`
  - 다양한 조회 method
- `valkey_schedule: ValkeyScheduleClient`
  - `set_pending_queue(scaling_group, session_ids)` → `None`

---

## 정상 경로 시나리오

### SC-PR-001: 모든 session 스케줄링 성공

- **목적**: 모든 workload 가 파이프라인을 통과해 할당되는지 확인한다
- **의존성(mock):**
  - `sequencer.sequence(snapshot, [w1, w2])`:
    - 반환: `[w1, w2]`(FIFO 순서)
  - `validator.validate(snapshot, w1)`:
    - 반환: `None`(통과)
  - `validator.validate(snapshot, w2)`:
    - 반환: `None`(통과)
  - `agent_selector.select_agents_for_batch_requirements(...)`:
    - 반환: 호출마다 `[AgentSelection(agent_id=a1, ...)]`
  - `allocator.allocate(batch)`:
    - 반환: `[ScheduledSessionData(s1), ScheduledSessionData(s2)]`
- **입력:**
  - 대기 session 2개를 가진 `scheduling_data`
- **실행:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **검증:**
  - `len(result.scheduled_sessions)` == 2
  - `valkey_schedule.set_pending_queue.assert_called_with("default", [])`(실패 없음)
- **분류**: `happy-path`

---

### SC-PR-002: snapshot 이 없으면 빈 결과 반환

- **목적**: snapshot data 가 없을 때 조기 반환하는지 확인한다
- **의존성(mock):**
  - (조기 반환 뒤에는 호출이 없어야 한다)
- **입력:**
  - `scheduling_data.snapshot_data = None`
- **실행:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **검증:**
  - `result` 는 빈 ScheduleResult 다
  - snapshot 이 없으면 warning log 를 남긴다
- **분류**: `edge-case`

---

### SC-PR-003: sequencer 가 DRF 로 workload 순서를 정한다

- **목적**: scheduler 설정에 따라 DRF sequencer 가 선택되는지 확인한다
- **의존성(mock):**
  - `scheduling_data.scaling_group.scheduler = "drf"`
- **입력:**
  - 자원 요구 사항이 다른 workload 3개
- **실행:** `_get_sequencer("drf")` 를 통해 실행한다
- **검증:**
  - DRF sequencer 를 사용한다(fair share 순서로 정렬)
- **분류**: `happy-path`

---

## 검증 실패 시나리오

### SC-PR-004: 검증 실패가 SchedulingFailure 를 생성한다

- **목적**: 검증 예외를 잡아 기록하는지 확인한다
- **의존성(mock):**
  - `validator.validate(snapshot, w1)`:
    - 발생: `QuotaExceeded("User quota exceeded")`
- **입력:**
  - workload `w1` 하나
- **실행:** `schedule_scaling_group()` 안의 `_schedule_workload()` 를 통해 실행한다
- **검증:**
  - `scheduling_failures` 에 `w1` 의 실패가 포함된다
  - `failure.msg` 에 "User quota exceeded" 가 포함된다
  - workload 가 agent selector 로 전달되지 않는다
- **분류**: `error-case`

---

### SC-PR-005: 일부 검증 실패

- **목적**: 일부가 검증에 실패해도 유효한 session 은 진행하는지 확인한다
- **의존성(mock):**
  - `validator.validate(snapshot, w1)`:
    - 발생: `QuotaExceeded("...")`
  - `validator.validate(snapshot, w2)`:
    - 반환: `None`(통과)
  - `allocator.allocate(batch)`:
    - 반환: `[ScheduledSessionData(s2)]`
- **입력:**
  - workload 2개, `w1`(실패), `w2`(통과)
- **실행:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **검증:**
  - `len(result.scheduled_sessions)` == 1, `w2` 만 포함한다
  - `valkey_schedule.set_pending_queue.assert_called_with("default", [s1])`
- **분류**: `error-case`

---

## agent 선택 시나리오

### SC-PR-006: agent 선택이 설정된 전략을 사용한다

- **목적**: 설정에 따라 올바른 agent selector 를 사용하는지 확인한다
- **의존성(mock):**
  - `scheduling_data.scaling_group.scheduler_opts.agent_selection_strategy = CONCENTRATED`
  - `agent_selector_pool[CONCENTRATED].select_agents_for_batch_requirements(...)`:
    - 반환: `[AgentSelection(...)]`
- **실행:** `_schedule_workload()` 를 통해 실행한다
- **검증:**
  - Concentrated selector 를 사용한다(dispersed 아님)
- **분류**: `happy-path`

---

### SC-PR-007: agent 선택 실패가 SchedulingFailure 를 생성한다

- **목적**: agent 선택 예외를 잡는지 확인한다
- **의존성(mock):**
  - `agent_selector.select_agents_for_batch_requirements(...)`:
    - 발생: `AgentSelectionError("No agents available")`
- **입력:**
  - GPU 8개가 필요한 workload, 충분한 agent 없음
- **실행:** `schedule_scaling_group()` 안의 `_schedule_workload()` 를 통해 실행한다
- **검증:**
  - `scheduling_failures` 에 실패가 포함된다
  - `failure.msg` 에 "No agents available" 가 포함된다
- **분류**: `error-case`

---

### SC-PR-008: 지정된 agent 선택

- **목적**: 지정된 agent 를 selector 에 전달하는지 확인한다
- **의존성(mock):**
  - `workload.designated_agent_ids = [a1]`
  - `agent_selector.select_agents_for_batch_requirements(..., designated_agent_ids=[a1])`:
    - 반환: `[AgentSelection(agent_id=a1)]`
- **실행:** `_allocate_workload()` 를 통해 실행한다
- **검증:**
  - selector 를 designated_agent_ids 와 함께 호출한다
- **분류**: `happy-path`

---

## snapshot 갱신 시나리오

### SC-PR-009: 할당 뒤 snapshot 갱신

- **목적**: 다음 workload 를 위해 메모리 내 snapshot 을 갱신하는지 확인한다
- **설정:**
  - 초기 keypair 점유: `{ak1: {occupied_slots: 0, session_count: 0}}`
  - workload 에 CPU 4개를 할당한다
- **의존성(mock):**
  - `w1` 할당 성공
- **실행:** 할당 뒤 `_update_system_snapshot()` 를 통해 실행한다
- **검증:**
  - `snapshot.resource_occupancy.by_keypair[ak1].occupied_slots` 가 증가한다
  - `snapshot.resource_occupancy.by_keypair[ak1].session_count` 가 증가한다
  - `snapshot.resource_occupancy.by_user[user_uuid]` 가 증가한다
  - `snapshot.resource_occupancy.by_group[group_id]` 가 증가한다
  - `snapshot.resource_occupancy.by_domain[domain_name]` 가 증가한다
- **분류**: `happy-path`

---

### SC-PR-010: SFTP session 이 sftp_session_count 를 갱신한다

- **목적**: private(SFTP) session 이 올바른 counter 를 갱신하는지 확인한다
- **설정:**
  - `workload.is_private = True`
- **실행:** `_update_system_snapshot()` 를 통해 실행한다
- **검증:**
  - `snapshot.resource_occupancy.by_keypair[ak].sftp_session_count` 가 증가한다
  - `snapshot.concurrency.sftp_sessions_by_keypair[ak]` 가 증가한다
  - 일반 `session_count` 는 증가하지 않는다
- **분류**: `edge-case`

---

## 실행 기록 시나리오

### SC-PR-011: 실행 기록이 단계를 담는다

- **목적**: recorder context 가 모든 단계를 담는지 확인한다
- **의존성(mock):**
  - 모든 단계가 성공한다
- **실행:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **검증:**
  - 기록에 `["sequencing", "validation", "agent_selection", "allocation"]` 단계가 포함된다
  - 각 단계에 하위 단계가 포함된다
  - 할당 결과에 통과한 predicate 가 채워진다
- **분류**: `happy-path`

---

### SC-PR-012: 실패한 단계를 predicate 에 기록

- **목적**: 실패한 단계가 failed_phases 에 나타나는지 확인한다
- **의존성(mock):**
  - `validator.validate()` 가 예외를 발생시킨다
- **입력:**
  - 검증에 실패하는 workload
- **실행:** `schedule_scaling_group()` 를 통해 실행한다
- **검증:**
  - `scheduling_failure.failed_phases` 에 validation predicate 가 포함된다
  - `scheduling_failure.passed_phases` 에 sequencing predicate 가 포함된다
- **분류**: `error-case`

---

## Valkey queue 갱신 시나리오

### SC-PR-013: 실패한 id 를 Valkey queue 에 기록

- **목적**: 재시도를 위해 실패한 session id 를 저장하는지 확인한다
- **의존성(mock):**
  - workload 3개 중 2개가 실패한다
  - `valkey_schedule.set_pending_queue(scaling_group, failure_ids)`:
    - 반환: `None`
- **입력:**
  - workload 3개, 2개 실패
- **실행:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **검증:**
  - `valkey_schedule.set_pending_queue.assert_called_with("default", [s1, s2])`
- **분류**: `happy-path`

---

## 동시성, batch 시나리오

### SC-PR-014: 여러 workload 에 걸쳐 agent 상태 갱신

- **목적**: 변경 가능한 agent 가 할당을 반영하는지 확인한다
- **설정:**
  - CPU 10개 용량의 agent `a1`
  - workload `w1` 은 CPU 4개가 필요하다
  - workload `w2` 는 CPU 4개가 필요하다
- **실행:** 두 workload 를 같은 agent 에 할당한다
- **검증:**
  - 두 번 할당한 뒤 agent `a1` 은 CPU 8개를 사용한다
  - CPU 4개가 필요한 세 번째 workload 는 실패한다(자원 부족)
- **분류**: `happy-path`

---

### SC-PR-015: batch 할당의 원자성

- **목적**: 효율을 위해 할당을 하나의 batch 로 처리하는지 확인한다
- **의존성(mock):**
  - `allocator.allocate(batch)`:
    - 여러 할당을 담은 batch 를 받는다
    - 반환: `list[ScheduledSessionData]`
- **입력:**
  - 검증을 모두 통과한 workload 3개
- **실행:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **검증:**
  - `allocator.allocate.assert_called_once()`(batch 호출 한 번)
  - batch 에 할당 3개가 모두 포함된다
- **분류**: `happy-path`

---

# 2부: Validator 테스트

## 개요

`SchedulingValidator` 는 여러 `ValidatorRule` 을 순서대로 적용한다.
각 규칙은 `SystemSnapshot` 과 `SessionWorkload` 를 검증하고 실패하면 예외를 발생시킨다.

**소스 파일:** `sokovan/scheduler/provisioner/validators/`

**검증 규칙:**
| 규칙 | 예외 | 목적 |
|------|-----------|---------|
| `ConcurrencyValidator` | `ConcurrencyLimitExceeded` | keypair 별 동시 session 한도 |
| `DependenciesValidator` | `DependenciesNotSatisfied` | session 의존 관계 충족 여부 |
| `KeypairResourceLimitValidator` | `KeypairResourceQuotaExceeded` | keypair 자원 quota |
| `UserResourceLimitValidator` | `UserResourceQuotaExceeded` | 사용자 자원 quota |
| `GroupResourceLimitValidator` | `GroupResourceQuotaExceeded` | 프로젝트 자원 quota |
| `DomainResourceLimitValidator` | `DomainResourceQuotaExceeded` | 도메인 자원 quota |
| `PendingSessionCountLimitValidator` | `PendingSessionCountLimitExceeded` | 대기 session 수 한도 |
| `PendingSessionResourceLimitValidator` | `PendingSessionResourceLimitExceeded` | 대기 session 자원 한도 |

---

## SchedulingValidator 통합 테스트

### SC-VD-001: 모든 규칙 통과

- **목적**: 모든 검증 규칙이 통과하면 예외가 없는지 확인한다
- **의존성(mock):**
  - `rule1.validate(snapshot, workload)`: 반환 `None`
  - `rule2.validate(snapshot, workload)`: 반환 `None`
- **입력:**
  - `snapshot`: quota 와 자원이 충분하다
  - `workload`: 유효한 session workload
- **실행:** `validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
  - 모든 규칙의 `validate()` 를 호출한다
- **분류**: `happy-path`

---

### SC-VD-002: 규칙 하나가 실패하면 예외 발생

- **목적**: 규칙 하나가 실패하면 그 예외를 그대로 발생시키는지 확인한다
- **의존성(mock):**
  - `rule1.validate(snapshot, workload)`: `QuotaExceeded` 발생
  - `rule2.validate(snapshot, workload)`: 반환 `None`(통과)
- **실행:** `validator.validate(snapshot, workload)`
- **검증:**
  - `QuotaExceeded` 예외가 발생한다(에러 하나는 그대로 발생시킨다)
  - `rule2.validate.assert_called_once()`(모든 규칙을 실행한다)
- **분류**: `error-case`

---

### SC-VD-002-1: 여러 규칙이 실패하면 MultipleValidationErrors 발생

- **목적**: 여러 규칙이 실패하면 모든 에러를 모으는지 확인한다
- **의존성(mock):**
  - `rule1.validate(snapshot, workload)`: `QuotaExceeded` 발생
  - `rule2.validate(snapshot, workload)`: `ConcurrencyLimitExceeded` 발생
  - `rule3.validate(snapshot, workload)`: 반환 `None`(통과)
- **실행:** `validator.validate(snapshot, workload)`
- **검증:**
  - `MultipleValidationErrors` 예외가 발생한다
  - `len(exception.errors)` == 2
  - 모든 규칙의 `validate()` 를 호출한다
- **분류**: `error-case`

---

## ConcurrencyValidator 테스트

### SC-VD-003: 동시 session 한도 이내, 통과

- **목적**: 동시 session 수가 한도 이내일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.keypair_policies[ak1].max_concurrent_sessions` = 5
  - `snapshot.concurrency.sessions_by_keypair[ak1]` = 3
  - `workload.access_key` = `ak1`
  - `workload.is_private` = `False`
- **실행:** `concurrency_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-004: 동시 session 한도 초과, 실패

- **목적**: 동시 session 수가 한도를 넘을 때 실패하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.keypair_policies[ak1].max_concurrent_sessions` = 5
  - `snapshot.concurrency.sessions_by_keypair[ak1]` = 5
  - `workload.access_key` = `ak1`
  - `workload.is_private` = `False`
- **실행:** `concurrency_validator.validate(snapshot, workload)`
- **검증:**
  - `ConcurrencyLimitExceeded` 예외가 발생한다
- **분류**: `error-case`

---

## DependenciesValidator 테스트

### SC-VD-005: 의존 관계 없음, 통과

- **목적**: 의존 관계가 없는 session 은 항상 통과하는지 확인한다
- **입력:**
  - `workload.depends_on` = `[]`
- **실행:** `dependencies_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-006: 모든 의존 관계 충족, 통과

- **목적**: 의존 session 이 모두 TERMINATED + SUCCESS 일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.session_dependencies.by_session[workload.session_id]` = `[
      DependencyInfo(depends_on=s1, dependency_status=TERMINATED, dependency_result=SUCCESS),
      DependencyInfo(depends_on=s2, dependency_status=TERMINATED, dependency_result=SUCCESS)
    ]`
- **실행:** `dependencies_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-007: 의존 관계 미충족, 실패

- **목적**: 의존 session 이 TERMINATED + SUCCESS 가 아닐 때 실패하는지 확인한다
- **입력:**
  - `snapshot.session_dependencies.by_session[workload.session_id]` = `[
      DependencyInfo(depends_on=s1, dependency_status=TERMINATED, dependency_result=SUCCESS),
      DependencyInfo(depends_on=s2, dependency_status=RUNNING, dependency_result=UNDEFINED)
    ]`
- **실행:** `dependencies_validator.validate(snapshot, workload)`
- **검증:**
  - `DependenciesNotSatisfied` 예외가 발생한다
  - 예외 message 에 `s2` 가 포함된다
- **분류**: `error-case`

---

## KeypairResourceLimitValidator 테스트

### SC-VD-008: keypair 자원 quota 이내, 통과

- **목적**: 요청 자원이 keypair quota 이내일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_keypair[ak1].total_resource_slots` = `{cpu: 100}`
  - `snapshot.resource_occupancy.by_keypair[ak1].occupied_slots` = `{cpu: 50}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `keypair_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-009: keypair 자원 quota 초과, 실패

- **목적**: 요청 자원이 keypair quota 를 넘을 때 실패하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_keypair[ak1].total_resource_slots` = `{cpu: 100}`
  - `snapshot.resource_occupancy.by_keypair[ak1].occupied_slots` = `{cpu: 95}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `keypair_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - `KeypairResourceQuotaExceeded` 예외가 발생한다
- **분류**: `error-case`

---

## UserResourceLimitValidator 테스트

### SC-VD-010: 사용자 자원 quota 이내, 통과

- **목적**: 요청 자원이 사용자 quota 이내일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_user[user1].total_resource_slots` = `{cpu: 200}`
  - `snapshot.resource_occupancy.by_user[user1].occupied_slots` = `{cpu: 50}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `user_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-011: 사용자 자원 quota 초과, 실패

- **목적**: 요청 자원이 사용자 quota 를 넘을 때 실패하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_user[user1].total_resource_slots` = `{cpu: 200}`
  - `snapshot.resource_occupancy.by_user[user1].occupied_slots` = `{cpu: 195}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `user_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - `UserResourceQuotaExceeded` 예외가 발생한다
- **분류**: `error-case`

---

## GroupResourceLimitValidator 테스트

### SC-VD-012: 프로젝트 자원 quota 이내, 통과

- **목적**: 요청 자원이 프로젝트 quota 이내일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_group[g1].total_resource_slots` = `{cpu: 500}`
  - `snapshot.resource_occupancy.by_group[g1].occupied_slots` = `{cpu: 100}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `group_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-013: 프로젝트 자원 quota 초과, 실패

- **목적**: 요청 자원이 프로젝트 quota 를 넘을 때 실패하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_group[g1].total_resource_slots` = `{cpu: 500}`
  - `snapshot.resource_occupancy.by_group[g1].occupied_slots` = `{cpu: 495}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `group_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - `GroupResourceQuotaExceeded` 예외가 발생한다
- **분류**: `error-case`

---

## DomainResourceLimitValidator 테스트

### SC-VD-014: 도메인 자원 quota 이내, 통과

- **목적**: 요청 자원이 도메인 quota 이내일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_domain[d1].total_resource_slots` = `{cpu: 1000}`
  - `snapshot.resource_occupancy.by_domain[d1].occupied_slots` = `{cpu: 500}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `domain_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-015: 도메인 자원 quota 초과, 실패

- **목적**: 요청 자원이 도메인 quota 를 넘을 때 실패하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_domain[d1].total_resource_slots` = `{cpu: 1000}`
  - `snapshot.resource_occupancy.by_domain[d1].occupied_slots` = `{cpu: 995}`
  - `workload.requested_slots` = `{cpu: 10}`
- **실행:** `domain_resource_limit_validator.validate(snapshot, workload)`
- **검증:**
  - `DomainResourceQuotaExceeded` 예외가 발생한다
- **분류**: `error-case`

---

## PendingSessionCountLimitValidator 테스트

### SC-VD-016: 대기 session 수 한도 이내, 통과

- **목적**: 대기 session 수가 한도 이내일 때 통과하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_keypair[ak1].max_pending_session_count` = 10
  - `snapshot.concurrency.pending_sessions_by_keypair[ak1]` = 5
- **실행:** `pending_session_count_limit_validator.validate(snapshot, workload)`
- **검증:**
  - 예외가 발생하지 않는다
- **분류**: `happy-path`

---

### SC-VD-017: 대기 session 수 한도 초과, 실패

- **목적**: 대기 session 수가 한도를 넘을 때 실패하는지 확인한다
- **입력:**
  - `snapshot.resource_policy.by_keypair[ak1].max_pending_session_count` = 10
  - `snapshot.concurrency.pending_sessions_by_keypair[ak1]` = 10
- **실행:** `pending_session_count_limit_validator.validate(snapshot, workload)`
- **검증:**
  - `PendingSessionCountLimitExceeded` 예외가 발생한다
- **분류**: `error-case`

---

# 3부: Sequencer 테스트

## 개요

`SchedulingSequencer` 는 우선순위로 workload 를 필터링한 뒤 전략에 따라 순서를 정한다.

**소스 파일:** `sokovan/scheduler/provisioner/sequencers/`

**Sequencer 전략:**
| 전략 | 알고리즘 |
|----------|-----------|
| `FIFOSequencer` | 먼저 들어온 것 먼저 처리(원래 순서) |
| `LIFOSequencer` | 나중에 들어온 것 먼저 처리(역순) |
| `DRFSequencer` | Dominant Resource Fairness(fair share) |

---

## SchedulingSequencer 통합 테스트

### SC-SQ-001: 우선순위가 가장 높은 workload 만 선택

- **목적**: 순서 결정에 우선순위가 가장 높은 workload 만 포함되는지 확인한다
- **입력:**
  - `workloads`: `[w1(priority=10), w2(priority=5), w3(priority=10)]`
- **실행:** `sequencer.sequence(snapshot, workloads)`
- **검증:**
  - 결과에 `w1`, `w3` 만 포함된다(priority=10)
  - `w2` 는 제외된다(priority=5)
- **분류**: `happy-path`

---

### SC-SQ-002: 빈 workload 목록, WorkloadSequencer 수준

- **목적**: 빈 목록이 빈 목록을 반환하는지 확인한다(WorkloadSequencer 직접 호출)
- **입력:**
  - `workloads`: `[]`
- **실행:** `workload_sequencer.sequence(snapshot, [])`(예: DRFSequencer)
- **검증:**
  - 결과는 빈 목록이다(DRFSequencer 는 조기 반환한다)
- **참고:** `SchedulingSequencer.sequence()` 는 빈 목록에서 `max()` 호출 시 에러가 날 수 있다. 호출부에서 검증해야 한다
- **분류**: `edge-case`

---

## FIFOSequencer 테스트

### SC-SQ-003: FIFO 는 원래 순서를 유지한다

- **목적**: 원래 순서가 유지되는지 확인한다
- **입력:**
  - `workloads`: `[w1, w2, w3]`(모두 같은 우선순위)
- **실행:** `fifo_sequencer.sequence(snapshot, workloads)`
- **검증:**
  - 결과 순서: `[w1, w2, w3]`
- **분류**: `happy-path`

---

## LIFOSequencer 테스트

### SC-SQ-004: LIFO 는 순서를 뒤집는다

- **목적**: 역순이 되는지 확인한다
- **입력:**
  - `workloads`: `[w1, w2, w3]`(모두 같은 우선순위)
- **실행:** `lifo_sequencer.sequence(snapshot, workloads)`
- **검증:**
  - 결과 순서: `[w3, w2, w1]`
- **분류**: `happy-path`

---

## DRFSequencer 테스트

### SC-SQ-005: DRF, 점유율이 낮은 workload 우선

- **목적**: dominant share 가 낮은 workload 를 먼저 스케줄링하는지 확인한다
- **입력:**
  - `snapshot.total_capacity` = `{cpu: 100, mem: 1000}`
  - `snapshot.resource_occupancy.by_keypair`:
    - `ak1`: `{cpu: 50}`(dominant share = 50%)
    - `ak2`: `{cpu: 10}`(dominant share = 10%)
  - `workloads`: `[w1(ak1), w2(ak2)]`
- **실행:** `drf_sequencer.sequence(snapshot, workloads)`
- **검증:**
  - 결과 순서: `[w2, w1]`(점유율이 낮은 ak2 우선)
- **분류**: `happy-path`

---

### SC-SQ-006: DRF, 점유율이 같으면 안정 정렬

- **목적**: dominant share 가 같을 때 원래 순서를 유지하는지 확인한다
- **입력:**
  - dominant share 가 같은 workload 2개
- **실행:** `drf_sequencer.sequence(snapshot, workloads)`
- **검증:**
  - 원래 순서를 유지한다(안정 정렬)
- **분류**: `edge-case`

---

### SC-SQ-007: DRF, 여러 자원 유형

- **목적**: 자원 유형 중 가장 높은 점유율이 dominant share 가 되는지 확인한다
- **입력:**
  - `snapshot.total_capacity` = `{cpu: 100, gpu: 10}`
  - `snapshot.resource_occupancy.by_keypair[ak1]` = `{cpu: 10, gpu: 5}`
  - dominant share = max(10/100, 5/10) = 50%(GPU)
- **실행:** `drf_sequencer.sequence(snapshot, workloads)`
- **검증:**
  - GPU 점유율을 dominant share 로 사용한다
- **분류**: `happy-path`

---

# 4부: Selector 테스트

## 개요

`AgentSelector` 는 architecture 호환성과 자원 가용성을 확인한 뒤 전략에 따라 선택한다.

**소스 파일:** `sokovan/scheduler/provisioner/selectors/`

**선택 전략:**
| 전략 | 알고리즘 |
|----------|-----------|
| `RoundRobinAgentSelector` | 순환 선택 |
| `ConcentratedAgentSelector` | 자원 최소화(빈틈없이 채움) |
| `DispersedAgentSelector` | 자원 최대화(넓게 분산) |

**선택 절차:**
1. architecture 호환성으로 필터링한다
2. 자원 가용성(slot, container 수)으로 필터링한다
3. 지정된 agent 를 확인한다(사용 가능하면 사용한다)
4. 전략에 따라 선택한다
5. batch 선택 중 상태를 추적한다

---

## AgentSelector 공통 테스트

### SC-SL-001: architecture 불일치, 실패

- **목적**: architecture 가 맞는 agent 가 없을 때 실패하는지 확인한다
- **입력:**
  - `agents`: `[AgentInfo(arch="x86_64"), AgentInfo(arch="x86_64")]`
  - `requirements.architecture` = `"aarch64"`
- **실행:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **검증:**
  - `NoCompatibleAgentError` 예외가 발생한다
- **분류**: `error-case`

---

### SC-SL-002: 자원 부족, 실패

- **목적**: 충분한 자원을 가진 agent 가 없을 때 실패하는지 확인한다
- **입력:**
  - `agents`: `[AgentInfo(available_slots={cpu: 2})]`
  - `requirements.requested_slots` = `{cpu: 8}`
- **실행:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **검증:**
  - `InsufficientResourcesError` 예외가 발생한다
- **분류**: `error-case`

---

### SC-SL-003: container 수 한도 초과, 실패

- **목적**: container 수 한도를 넘을 때 실패하는지 확인한다
- **입력:**
  - `agents`: `[AgentInfo(container_count=10)]`
  - `config.max_container_count` = 10
- **실행:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **검증:**
  - `ContainerLimitExceededError` 예외가 발생한다
- **분류**: `error-case`

---

### SC-SL-004: 지정된 agent 사용

- **목적**: 지정된 agent 가 호환되면 사용하는지 확인한다
- **입력:**
  - `agents`: `[AgentInfo(id=a1), AgentInfo(id=a2)]`
  - `designated_agent_ids` = `[a1]`
- **실행:** `selector.select_agents_for_batch_requirements(agents, criteria, config, designated_agent_ids=[a1])`
- **검증:**
  - 결과로 `a1` 을 선택한다
- **분류**: `happy-path`

---

### SC-SL-005: 지정된 agent 사용 불가, 에러

- **목적**: 지정된 agent 가 호환되지 않을 때 에러가 나는지 확인한다(대체 없음)
- **입력:**
  - `agents`: `[AgentInfo(id=a1, arch="x86_64"), AgentInfo(id=a2, arch="aarch64")]`
  - `designated_agent_ids` = `[a1]`
  - `requirements.architecture` = `"aarch64"`
- **실행:** `selector.select_agents_for_batch_requirements(..., designated_agent_ids=[a1])`
- **검증:**
  - `NoAvailableAgentError` 예외가 발생한다
  - 예외 message 에 "Designated agent" 가 포함된다
- **분류**: `error-case`

---

### SC-SL-006: batch 선택의 상태 추적

- **목적**: batch 선택 중 agent 상태를 추적하는지 확인한다
- **입력:**
  - `agents`: `[AgentInfo(id=a1, available_slots={cpu: 10})]`
  - `requirements`: kernel 2개, 각각 CPU 4개 필요
- **실행:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **검증:**
  - 첫 선택 뒤 a1 의 추적 상태: `additional_slots={cpu: 4}`
  - 두 번째 선택이 추적 상태를 반영한다
- **분류**: `happy-path`

---

## RoundRobinAgentSelector 테스트

### SC-SL-007: RoundRobin, index 기반 선택

- **목적**: agent 를 index 로 선택하는지 확인한다(agent_id 로 정렬)
- **입력:**
  - `agents`: `[AgentInfo(id="a3"), AgentInfo(id="a1"), AgentInfo(id="a2")]`
  - `selector.next_index` = 0
- **실행:** `select_tracker_by_strategy(trackers, ...)`
- **검증:**
  - `[a1, a2, a3]` 로 정렬 → index 0 → `a1` 선택
- **참고:** index 는 자동으로 증가하지 않는다. 호출부에서 관리한다
- **분류**: `happy-path`

---

### SC-SL-008: RoundRobin, index 나머지 연산으로 순환

- **목적**: index 가 agent 수를 넘으면 나머지 연산으로 순환하는지 확인한다
- **입력:**
  - `agents`: `[a1, a2]`(정렬됨)
  - `selector.next_index` = 5
- **실행:** `select_tracker_by_strategy()`
- **검증:**
  - `5 % 2 = 1` → `a2` 선택
- **분류**: `edge-case`

---

## ConcentratedAgentSelector 테스트

### SC-SL-009: Concentrated, 가용 자원이 가장 적은 agent 선택

- **목적**: 가용 자원이 가장 적은 agent 를 선택하는지 확인한다
- **입력:**
  - `agents`:
    - `a1`: `available_slots={cpu: 10}`
    - `a2`: `available_slots={cpu: 5}`
- **실행:** `concentrated_selector.select_tracker_by_strategy(...)`
- **검증:**
  - `a2` 선택(자원 최소)
- **분류**: `happy-path`

---

### SC-SL-010: Concentrated, 사용하지 않는 자원 유형 최소화

- **목적**: 사용하지 않는 자원 유형이 없는 agent 를 선호하는지 확인한다
- **입력:**
  - `a1`: `available_slots={cpu: 10, gpu: 4}`(GPU 미사용)
  - `a2`: `available_slots={cpu: 10}`
  - `requirements.requested_slots` = `{cpu: 4}`(GPU 불필요)
- **실행:** `concentrated_selector.select_tracker_by_strategy(...)`
- **검증:**
  - `a2` 선택(사용하지 않는 자원 유형 없음)
- **분류**: `happy-path`

---

## DispersedAgentSelector 테스트

### SC-SL-011: Dispersed, 가용 자원이 가장 많은 agent 선택

- **목적**: 가용 자원이 가장 많은 agent 를 선택하는지 확인한다
- **입력:**
  - `agents`:
    - `a1`: `available_slots={cpu: 10}`
    - `a2`: `available_slots={cpu: 20}`
- **실행:** `dispersed_selector.select_tracker_by_strategy(...)`
- **검증:**
  - `a2` 선택(자원 최대)
- **분류**: `happy-path`

---

### SC-SL-012: Dispersed, 부하 분산

- **목적**: 연속 선택이 서로 다른 agent 로 분산되는지 확인한다
- **입력:**
  - `agents`:
    - `a1`: `available_slots={cpu: 20}`
    - `a2`: `available_slots={cpu: 20}`
  - `requirements`: CPU 10개 필요
- **실행:** 두 번 선택한다
- **검증:**
  - 첫 번째: `a1` 또는 `a2`
  - 두 번째: 다른 agent(상태 추적이 줄어든 가용량을 반영한다)
- **분류**: `happy-path`

---

# 5부: Allocator 테스트

## 개요

`RepositoryAllocator` 는 할당을 `SchedulerRepository.allocate_sessions()` 에 위임한다.

**소스 파일:** `sokovan/scheduler/provisioner/allocators/`

---

### SC-AL-001: batch 할당 성공

- **목적**: 모든 할당을 성공적으로 처리하는지 확인한다
- **의존성(mock):**
  - `repository.allocate_sessions(batch)`:
    - 반환: `[ScheduledSessionData(s1), ScheduledSessionData(s2)]`
- **입력:**
  - `batch`: 성공한 할당 2개
- **실행:** `await allocator.allocate(batch)`
- **검증:**
  - `len(result)` == 2
  - `repository.allocate_sessions.assert_called_once_with(batch)`
- **분류**: `happy-path`

---

### SC-AL-002: 빈 batch 할당

- **목적**: 빈 batch 가 빈 결과를 반환하는지 확인한다
- **의존성(mock):**
  - `repository.allocate_sessions(batch)`:
    - 반환: `[]`
- **입력:**
  - `batch`: 빈 batch
- **실행:** `await allocator.allocate(batch)`
- **검증:**
  - `result` == `[]`
- **분류**: `edge-case`

---

### SC-AL-003: 일부 실패한 batch

- **목적**: 실패가 섞인 batch 를 올바르게 처리하는지 확인한다
- **의존성(mock):**
  - `repository.allocate_sessions(batch)`:
    - 반환: `[ScheduledSessionData(s1)]`(s2 실패)
- **입력:**
  - `batch`: 성공 1개, 실패 1개
- **실행:** `await allocator.allocate(batch)`
- **검증:**
  - `len(result)` == 1
  - 실패한 session 은 결과에 포함되지 않는다
- **분류**: `error-case`

---

### SC-AL-004: repository 예외 전파

- **목적**: repository 예외가 적절히 전파되는지 확인한다
- **의존성(mock):**
  - `repository.allocate_sessions(batch)`:
    - 발생: `DatabaseError("Connection failed")`
- **실행:** `await allocator.allocate(batch)`
- **검증:**
  - `DatabaseError` 예외가 발생한다
- **분류**: `error-case`
