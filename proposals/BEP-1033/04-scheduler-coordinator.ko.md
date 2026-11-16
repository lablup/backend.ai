# ScheduleCoordinator 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 `ScheduleCoordinator` 의 테스트 시나리오를 정의한다.

sokovan coordinator 는 전체 스케줄링 흐름을 조정한다:
1. handler 의 `lock_id` 에 따라 lock 을 획득한다
2. 자원 그룹을 병렬로 순회한다
3. handler 설정에 따라 session 과 kernel 을 조회한다
4. handler 를 실행한다
5. 실패를 `give_up`, `expired`, `need_retry` 로 분류한다
6. 특정 상태 전이에 hook 을 실행한다
7. 이력 기록과 함께 상태 변경을 일괄 적용한다
8. 전이 event 를 브로드캐스트한다
9. PostProcessor chain 을 실행한다(schedule 표시, cache 무효화)

**소스 파일:**
- `sokovan/scheduler/coordinator.py`
- `sokovan/scheduler/post_processors/`

---

## 실패 분류

sokovan coordinator 는 다음 기준으로 실패를 분류한다:

| 우선순위 | 분류 | 조건 |
|----------|---------------|-----------|
| 1 | `give_up` | `phase_attempts >= SERVICE_MAX_RETRIES` (5) |
| 2 | `expired` | `elapsed > STATUS_TIMEOUT_MAP[status]` |
| 3 | `need_retry` | 기본값(give_up 도 expired 도 아님) |

**timeout 임계값:**
- PREPARING: 900초(15분)
- PULLING: 900초(15분)
- CREATING: 600초(10분)

---

### SC-CO-001: 실패를 give_up 으로 분류

- **목적**: 최대 재시도를 넘은 session 을 give_up 으로 분류하는지 확인한다
- **설정:**
  - `phase_attempts = 5` 인 session `s1`(SERVICE_MAX_RETRIES 와 같음)
  - handler 가 `s1` 을 실패로 반환한다
- **실행:** `_classify_failures([failure_s1], [session_s1])`
- **검증:**
  - `result.give_up` 에 `s1` 이 포함된다
  - `result.expired` 는 비어 있다
  - `result.need_retry` 는 비어 있다
- **분류**: `happy-path`

---

### SC-CO-002: 실패를 expired 로 분류

- **목적**: timeout 을 넘은 session 을 expired 로 분류하는지 확인한다
- **설정:**
  - PREPARING 상태의 session `s1`
  - `phase_started_at = now - 16 minutes`, 15분 임계값 초과
  - `phase_attempts = 1`, 최대 재시도 미만
- **실행:** `_classify_failures([failure_s1], [session_s1])`
- **검증:**
  - `result.expired` 에 `s1` 이 포함된다
  - `result.give_up` 은 비어 있다
  - `result.need_retry` 는 비어 있다
- **분류**: `happy-path`

---

### SC-CO-003: 실패를 need_retry 로 분류

- **목적**: give_up 과 expired 에 해당하지 않는 실패를 need_retry 로 분류하는지 확인한다
- **설정:**
  - PREPARING 상태의 session `s1`
  - `phase_started_at = now - 5 minutes`, 임계값 이내
  - `phase_attempts = 1`, 최대 재시도 미만
- **실행:** `_classify_failures([failure_s1], [session_s1])`
- **검증:**
  - `result.need_retry` 에 `s1` 이 포함된다
  - `result.give_up` 은 비어 있다
  - `result.expired` 는 비어 있다
- **분류**: `happy-path`

---

### SC-CO-004: give_up 이 expired 보다 우선한다

- **목적**: give_up 분류가 우선하는지 확인한다
- **설정:**
  - session `s1`:
    - `phase_attempts = 5`, 최대 재시도 초과
    - `phase_started_at = now - 20 minutes`, timeout 도 초과
- **실행:** `_classify_failures([failure_s1], [session_s1])`
- **검증:**
  - `result.give_up` 에 `s1` 이 포함된다
  - `result.expired` 는 비어 있다(give_up 이 우선한다)
- **분류**: `edge-case`

---

## hook 실행

### SC-CO-005: RUNNING 전이의 hook 실행

- **목적**: RUNNING 으로 전이하는 session 에 hook 을 실행하는지 확인한다
- **의존성(mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`:
    - 반환: `RunningStatusHook`(mock)
  - `running_hook.execute(session_with_kernels)`:
    - 반환: `None`
  - `repository.search_sessions_with_kernels_for_handler(querier)`:
    - 반환: `[SessionWithKernels(s1)]`
- **입력:**
  - `session_infos`: `[SessionTransitionInfo(s1)]`
  - `target_status`: `SessionStatus.RUNNING`
- **실행:** `await _execute_transition_hooks(session_infos, target_status)`
- **검증:**
  - `hook_registry.get_hook.assert_called_with(SessionStatus.RUNNING)`
  - `running_hook.execute.assert_called_once()`
  - 결과의 `successful_sessions` 에 `s1` 이 포함된다
- **분류**: `happy-path`

---

### SC-CO-006: hook 실패가 session 을 제외

- **목적**: hook 실패가 session 전이를 차단하는지 확인한다
- **의존성(mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`:
    - 반환: `RunningStatusHook`(mock)
  - `running_hook.execute(session_with_kernels)`:
    - 발생: `Exception("Hook failed")`
  - `repository.search_sessions_with_kernels_for_handler(querier)`:
    - 반환: `[SessionWithKernels(s1), SessionWithKernels(s2)]`
- **입력:**
  - `session_infos`: `[SessionTransitionInfo(s1), SessionTransitionInfo(s2)]`
  - `target_status`: `SessionStatus.RUNNING`
- **실행:** `await _execute_transition_hooks(session_infos, target_status)`
- **검증:**
  - `result.successful_sessions` 에는 hook 이 성공한 session 만 포함된다
  - 실패한 session 에 에러를 기록한다
- **분류**: `error-case`

---

### SC-CO-007: 등록된 hook 없음, 모든 session 통과

- **목적**: 등록된 hook 이 없으면 session 이 통과하는지 확인한다
- **의존성(mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`:
    - 반환: `None`
- **입력:**
  - `session_infos`: `[SessionTransitionInfo(s1)]`
  - `target_status`: `SessionStatus.RUNNING`
- **실행:** `await _execute_transition_hooks(session_infos, target_status)`
- **검증:**
  - 이 경로를 호출하지 않는다(_execute_transition_hooks 를 호출하기 전에 hook 을 확인한다)
- **참고**: hook 확인은 실제로 이 method 를 호출하기 전에 일어난다
- **분류**: `edge-case`

---

## 상태 전이 적용

### SC-CO-008: 이력을 포함한 일괄 상태 변경

- **목적**: 상태 변경과 이력을 원자적으로 적용하는지 확인한다
- **의존성(mock):**
  - `repository.update_with_history(updater, creator)`:
    - 반환: `2`(변경 건수)
- **입력:**
  - `handler_name`: `"schedule-sessions"`
  - `session_infos`: `[SessionTransitionInfo(s1), SessionTransitionInfo(s2)]`
  - `transition`: `TransitionStatus(session=SCHEDULED, kernel=SCHEDULED)`
  - `scheduling_result`: `SchedulingResult.SUCCESS`
- **실행:** `await _apply_transition(handler_name, session_infos, transition, scheduling_result, records)`
- **검증:**
  - `repository.update_with_history.assert_called_once()`
  - updater spec 에 `to_status=SCHEDULED` 가 포함된다
  - session 마다 이력 spec 을 생성한다
- **분류**: `happy-path`

---

### SC-CO-009: give_up 시 kernel 을 PENDING 으로 초기화

- **목적**: session 이 PENDING 으로 전이할 때 kernel 을 초기화하는지 확인한다
- **의존성(mock):**
  - `kernel_state_engine.reset_kernels_to_pending_for_sessions([s1])`:
    - 반환: `2`(초기화 건수)
- **입력:**
  - `transition.kernel`: `KernelStatus.PENDING`
  - `session_ids`: `[s1]`
- **실행:** `transition.kernel == PENDING` 일 때 `_apply_transition()` 을 통해 실행한다
- **검증:**
  - `kernel_state_engine.reset_kernels_to_pending_for_sessions.assert_called_once_with([s1], reason="EXCEEDED_MAX_RETRIES")`
- **분류**: `happy-path`

---

## event 브로드캐스트

### SC-CO-010: 성공 전이의 event 브로드캐스트

- **목적**: 전이에 대해 SchedulingBroadcastEvent 를 보내는지 확인한다
- **의존성(mock):**
  - `event_producer.broadcast_events_batch(events)`:
    - 반환: `None`
- **입력:**
  - `sessions`: `[SessionTransitionInfo(s1, creation_id=c1), SessionTransitionInfo(s2, creation_id=c2)]`
  - `to_status`: `SessionStatus.RUNNING`
- **실행:** `await _broadcast_transition_events(sessions, to_status)`
- **검증:**
  - `event_producer.broadcast_events_batch.assert_called_once()`
  - event 목록에 SchedulingBroadcastEvent 2개가 포함된다
  - event 에 `session_id`, `creation_id`, `status_transition` 이 포함된다
- **분류**: `happy-path`

---

## 전체 수명 주기 handler 처리

### SC-CO-011: 수명 주기 handler 전체 흐름

- **목적**: 수명 주기 handler 처리의 종단 간 테스트
- **설정:**
  - 자원 그룹: `["default", "gpu"]`
  - handler: `ScheduleSessionsLifecycleHandler`
  - handler 에 `lock_id` 가 있다
- **의존성(mock):**
  - `lock_factory(lock_id, lifetime)`: context manager 반환
  - `repository.get_schedulable_scaling_groups()`: `["default", "gpu"]` 반환
  - `repository.get_sessions_for_handler()`: 자원 그룹별 session 반환
  - `repository.get_last_session_histories()`: 이력 map 반환
  - `handler.execute()`: 결과 반환
  - `repository.update_with_history()`: 건수 반환
- **실행:** `await process_lifecycle_schedule(ScheduleType.SCHEDULE)`
- **검증:**
  - lock 을 획득하고 해제한다
  - 두 자원 그룹을 병렬로 처리한다
  - 자원 그룹마다 handler 를 실행한다
  - 상태 변경을 적용한다
- **분류**: `happy-path`

---

### SC-CO-012: lock_id 가 있는 handler 의 lock 획득

- **목적**: handler 에 lock_id 가 있으면 lock 을 획득하는지 확인한다
- **의존성(mock):**
  - `lock_factory(LockID.LOCKID_SOKOVAN_TARGET_PENDING, lifetime)`:
    - 반환: AsyncContextManager
  - `config_provider.config.manager.session_schedule_lock_lifetime`:
    - 반환: `30.0`
- **입력:**
  - `lock_id = LockID.LOCKID_SOKOVAN_TARGET_PENDING` 인 handler
- **실행:** `_process_lifecycle_handler_schedule()` 을 통해 실행한다
- **검증:**
  - `lock_factory.assert_called_with(LockID.LOCKID_SOKOVAN_TARGET_PENDING, 30.0)`
- **분류**: `happy-path`

---

### SC-CO-013: lock_id 가 없는 handler 는 lock 없음

- **목적**: lock_id 가 없는 handler 는 lock 을 획득하지 않는지 확인한다
- **의존성(mock):**
  - (lock factory 호출 없음)
- **입력:**
  - `lock_id = None` 인 handler
- **실행:** `_process_lifecycle_handler_schedule()` 을 통해 실행한다
- **검증:**
  - `lock_factory.assert_not_called()`
- **분류**: `edge-case`

---

### SC-CO-014: 자원 그룹 처리 에러 기록

- **목적**: 병렬 처리 중 발생한 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `repository.get_schedulable_scaling_groups()`: `["default", "gpu"]` 반환
  - `_process_scaling_group("default", ...)`: 정상 반환
  - `_process_scaling_group("gpu", ...)`: `Exception("DB error")` 발생
- **실행:** `await process_lifecycle_schedule(ScheduleType.SCHEDULE)`
- **검증:**
  - "gpu" 자원 그룹의 에러를 기록한다
  - "default" 자원 그룹은 계속 처리한다
  - method 가 True 를 반환한다(부분 성공)
- **분류**: `error-case`

---

## 승격 handler 처리

### SC-CO-015: 승격 spec 이 kernel 매칭 조건을 사용한다

- **목적**: 승격 spec 조회에 kernel 매칭이 포함되는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - 반환: `[SessionInfo(s1)]`
- **입력:**
  - spec: `PromotionSpec(name="promote-to-running", kernel_match_type=NOT_ANY, target_kernel_statuses=pre_running_statuses())`
- **실행:** `_process_promotion_scaling_group(spec, schedule_type, scaling_group)` 을 통해 실행한다
- **검증:**
  - querier 조건에 `by_kernel_match(pre_running_statuses(), NOT_ANY)` 가 포함된다
- **분류**: `happy-path`

---

## kernel handler 처리

### SC-CO-016: kernel handler 가 kernel 결과를 처리한다

- **목적**: kernel 상태 전이를 적용하는지 확인한다
- **의존성(mock):**
  - `repository.search_kernels_for_handler(querier)`:
    - 반환: `KernelSearchResult(items=[k1, k2])`
  - `handler.execute()`:
    - 반환: `KernelExecutionResult(successes=[k1], failures=[k2])`
  - `kernel_state_engine.mark_kernel_terminated(k2, reason)`:
    - 반환: `True`
- **실행:** `_process_kernel_scaling_group()` 을 통해 실행한다
- **검증:**
  - `kernel_state_engine.mark_kernel_terminated.assert_called_with(k2, "kernel_handler_failure")`
  - handler 지표를 기록한다
- **분류**: `happy-path`

---

## 이력 기록

### SC-CO-017: 이력에서 phase_attempts 설정

- **목적**: 마지막으로 일치한 이력에서 phase_attempts 를 설정하는지 확인한다
- **의존성(mock):**
  - `repository.get_last_session_histories([s1])`:
    - 반환: `{s1: SchedulingHistoryRecord(phase="schedule-sessions", attempts=2)}`
- **입력:**
  - handler 가 `schedule-sessions` 인 session `s1`
- **실행:** `_process_scaling_group()` 을 통해 실행한다
- **검증:**
  - `session.phase_attempts == 2`
  - `session.phase_started_at` 을 설정한다
- **분류**: `happy-path`

---

### SC-CO-018: phase 가 다르면 phase_attempts 초기화

- **목적**: 이력 phase 가 일치하지 않으면 phase_attempts 가 0 인지 확인한다
- **의존성(mock):**
  - `repository.get_last_session_histories([s1])`:
    - 반환: `{s1: SchedulingHistoryRecord(phase="start-sessions", attempts=5)}`
- **입력:**
  - handler 가 `schedule-sessions` 인 session `s1`, 이력과 다름
- **실행:** `_process_scaling_group()` 을 통해 실행한다
- **검증:**
  - `session.phase_attempts == 0`, 이력 phase 가 일치하지 않음
  - `session.phase_started_at == None`
- **분류**: `edge-case`

---

### SC-CO-019: 생략된 session 을 상태 변경 없이 기록

- **목적**: 생략된 session 을 이력에 기록하는지 확인한다
- **의존성(mock):**
  - `handler.execute()`:
    - 반환: `SessionExecutionResult(skipped=[SessionTransitionInfo(s1, reason="blocked")])`
  - `repository.create_scheduling_history(creator)`:
    - 반환: `None`
- **실행:** `_record_skipped_history()` 를 통해 실행한다
- **검증:**
  - `result=SKIPPED` 로 이력을 생성한다
  - `from_status == to_status`, 변경 없음
- **분류**: `happy-path`

---

## PostProcessor chain 실행

sokovan coordinator 는 handler 실행 후 PostProcessor chain 으로 공통 후처리를 수행한다.

**소스 파일:** `sokovan/scheduler/post_processors/`

### SC-CO-020: ScheduleMarkingPostProcessor 가 다음 schedule type 을 표시한다

- **목적**: 상태 전이 후 올바른 schedule type 을 표시하는지 확인한다
- **의존성(mock):**
  - `scheduling_controller.mark_scheduling_needed(ScheduleType.CHECK_PRECONDITION)`:
    - 반환: `None`
- **입력:**
  - `context.target_status`: `SessionStatus.SCHEDULED`
  - `context.result`: `SessionExecutionResult(successes=[...])`
- **실행:** `await schedule_marking_post_processor.execute(context)`
- **검증:**
  - `scheduling_controller.mark_scheduling_needed.assert_called_once_with(ScheduleType.CHECK_PRECONDITION)`
- **분류**: `happy-path`

---

### SC-CO-021: 매핑 없는 상태에서는 ScheduleMarkingPostProcessor 생략

- **목적**: 상태에 매핑이 없으면 표시를 생략하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `context.target_status`: `SessionStatus.PENDING`, mapping = None
  - `context.result`: `SessionExecutionResult(successes=[...])`
- **실행:** `await schedule_marking_post_processor.execute(context)`
- **검증:**
  - `scheduling_controller.mark_scheduling_needed.assert_not_called()`
- **분류**: `edge-case`

---

### SC-CO-022: target_status=None 이면 ScheduleMarkingPostProcessor 생략

- **목적**: target_status 가 None 이면 표시를 생략하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `context.target_status`: `None`
  - `context.result`: `SessionExecutionResult(successes=[...])`
- **실행:** `await schedule_marking_post_processor.execute(context)`
- **검증:**
  - `scheduling_controller.mark_scheduling_needed.assert_not_called()`
- **분류**: `edge-case`

---

### SC-CO-023: CacheInvalidationPostProcessor 가 영향받은 access key cache 를 무효화한다

- **목적**: successes 와 failures 에서 access key 를 모아 cache 를 무효화하는지 확인한다
- **의존성(mock):**
  - `repository.invalidate_kernel_related_cache([ak1, ak2, ak3])`:
    - 반환: `None`
- **입력:**
  - `context.result`:
    ```python
    SessionExecutionResult(
        successes=[SessionTransitionInfo(access_key=ak1), SessionTransitionInfo(access_key=ak2)],
        failures=[SessionTransitionInfo(access_key=ak3)]
    )
    ```
- **실행:** `await cache_invalidation_post_processor.execute(context)`
- **검증:**
  - `repository.invalidate_kernel_related_cache` 를 호출한다
  - 인자에 `{ak1, ak2, ak3}` 가 포함된다(순서 무관)
- **분류**: `happy-path`

---

### SC-CO-024: access key 가 없으면 CacheInvalidationPostProcessor 생략

- **목적**: 영향받은 access key 가 없으면 cache 무효화를 생략하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `context.result`:
    ```python
    SessionExecutionResult(
        successes=[SessionTransitionInfo(access_key=None)],
        failures=[]
    )
    ```
- **실행:** `await cache_invalidation_post_processor.execute(context)`
- **검증:**
  - `repository.invalidate_kernel_related_cache.assert_not_called()`
- **분류**: `edge-case`

---

### SC-CO-025: 모든 PostProcessor 를 호출한다

- **목적**: sokovan coordinator 가 등록된 PostProcessor 를 모두 호출하는지 확인한다
- **의존성(mock):**
  - `schedule_marking_post_processor.execute()`:
    - 반환: `None`
  - `cache_invalidation_post_processor.execute()`:
    - 반환: `None`
- **입력:**
  - `result`: `SessionExecutionResult(successes=[SessionTransitionInfo(...)])`
  - `target_status`: `SessionStatus.SCHEDULED`
- **실행:** `await coordinator._run_post_processors(result, target_status)`
- **검증:**
  - `schedule_marking_post_processor.execute.assert_called_once()`
  - `cache_invalidation_post_processor.execute.assert_called_once()`
- **분류**: `happy-path`
