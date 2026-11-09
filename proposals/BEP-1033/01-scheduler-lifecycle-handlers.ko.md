# scheduler 수명 주기 handler 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 scheduler 수명 주기 handler 의 테스트 시나리오를 정의한다.

**소스 파일:**
- `sokovan/scheduler/handlers/lifecycle/check_precondition.py`
- `sokovan/scheduler/handlers/lifecycle/schedule_sessions.py`
- `sokovan/scheduler/handlers/lifecycle/start_sessions.py`
- `sokovan/scheduler/handlers/lifecycle/terminate_sessions.py`
- `sokovan/scheduler/handlers/lifecycle/deprioritize_sessions.py`
- `sokovan/scheduler/handlers/maintenance/sweep_sessions.py`

---

## CheckPreconditionLifecycleHandler

**실제 동작:**
1. 입력 `SessionWithKernels` 에서 session id 를 추출한다
2. `get_sessions_for_pull_by_ids()` 로 repository 에서 `SessionDataForPull` 을 조회한다
3. session 과 image config 를 담아 `launcher.trigger_image_pulling()` 을 호출한다
4. 입력 session 전체를 success 로 반환한다(image pulling 은 비동기다)

**의존성(mock 대상):**
- `launcher: SessionLauncher`
  - `trigger_image_pulling(sessions, image_configs)` → `None`
- `repository: SchedulerRepository`
  - `get_sessions_for_pull_by_ids(session_ids)` → `SessionsForPullResult`

**참고:** schedule 표시는 sokovan coordinator 의 PostProcessor 가 처리한다.

**상태 전이:**
```python
success = TransitionStatus(session=PREPARING, kernel=PREPARING)
expired = TransitionStatus(session=PENDING, kernel=PENDING)
```

---

### SC-CP-001: 모든 session 이 image pulling 을 트리거한다

- **목적**: SCHEDULED 상태 session 이 모두 image pulling 을 트리거하고 success 로 표시되는지 확인한다
- **의존성(mock):**
  - `repository.get_sessions_for_pull_by_ids([s1, s2])`:
    - 반환: `SessionsForPullResult(sessions=[session1_data, session2_data], image_configs={...})`
  - `launcher.trigger_image_pulling(sessions_data, image_configs)`:
    - 반환: `None`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=SCHEDULED), SessionWithKernels(s2, status=SCHEDULED)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.SCHEDULED`
    - `result.successes[0].reason` == `"passed-preconditions"`
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.get_sessions_for_pull_by_ids.assert_called_once_with([s1, s2])`
    - `launcher.trigger_image_pulling.assert_called_once()`
- **분류**: `happy-path`

---

### SC-CP-002: 빈 session 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.get_sessions_for_pull_by_ids.assert_not_called()`
    - `launcher.trigger_image_pulling.assert_not_called()`
- **분류**: `edge-case`

---

### SC-CP-003: launcher 예외가 전파된다

- **목적**: launcher 예외가 sokovan coordinator 로 전파되는지 확인한다
- **의존성(mock):**
  - `repository.get_sessions_for_pull_by_ids([s1])`:
    - 반환: `SessionsForPullResult(...)`
  - `launcher.trigger_image_pulling(...)`:
    - 발생: `AgentError("Connection failed")`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=SCHEDULED)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **예외**: `AgentError` 발생(sokovan coordinator 가 expired 전이로 처리)
- **분류**: `error-case`

---

## ScheduleSessionsLifecycleHandler

**실제 동작:**
1. 입력이 비어 있으면 조기에 반환한다
2. session id 로 session map 을 구성한다(이후 조회용)
3. 스케줄링에 필요한 전체 정보를 조회하기 위해 `repository.get_scheduling_data(scaling_group)` 을 호출한다
4. scheduling_data 가 None 이면 모든 session 을 `skipped` 로 반환한다
5. `provisioner.schedule_scaling_group(scaling_group, scheduling_data)` 를 호출한다
6. `schedule_result.scheduled_sessions` 를 `SessionTransitionInfo` success 로 매핑한다
7. 스케줄되지 않은 session(우선순위, 자원 제약)을 `skipped` 로 반환한다

**의존성(mock 대상):**
- `provisioner: SessionProvisioner`
  - `schedule_scaling_group(scaling_group, scheduling_data)` → `ScheduleResult`
- `repository: SchedulerRepository`
  - `get_scheduling_data(scaling_group)` → `Optional[SchedulingData]`

**참고:** schedule 표시와 cache 무효화는 sokovan coordinator 의 PostProcessor 가 처리한다.

**상태 전이:**
```python
success = TransitionStatus(session=SCHEDULED, kernel=SCHEDULED)
expired = TransitionStatus(session=TERMINATING, kernel=TERMINATING)
give_up = TransitionStatus(session=DEPRIORITIZING, kernel=None)
```

---

### SC-SS-001: provisioner 로 session 이 정상 스케줄된다

- **목적**: provisioner 결과가 handler 결과로 정확히 매핑되는지 확인한다
- **의존성(mock):**
  - `repository.get_scheduling_data("default")`:
    - 반환: `SchedulingData(...)`
  - `provisioner.schedule_scaling_group("default", scheduling_data)`:
    - 반환: `ScheduleResult(scheduled_sessions=[ScheduledSessionData(session_id=s1, ...), ScheduledSessionData(session_id=s2, ...)])`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.PENDING`
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.get_scheduling_data.assert_called_once_with("default")`
    - `provisioner.schedule_scaling_group.assert_called_once()`
- **분류**: `happy-path`

---

### SC-SS-002: scheduling data 가 없으면 모든 session 을 skipped 로 반환한다

- **목적**: scheduling_data 가 None 일 때 모든 session 을 skipped 로 반환하는지 확인한다
- **의존성(mock):**
  - `repository.get_scheduling_data("default")`:
    - 반환: `None`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
    - `len(result.skipped)` == 2
    - `result.skipped[0].session_id` == `s1`
    - `result.skipped[0].reason` == `"no-scheduling-data"`
    - `result.skipped[1].session_id` == `s2`
  - **mock 호출:**
    - `repository.get_scheduling_data.assert_called_once_with("default")`
    - `provisioner.schedule_scaling_group.assert_not_called()`
- **분류**: `edge-case`

---

### SC-SS-003: provisioner 부분 성공, 스케줄되지 않은 session 은 skipped 로 반환한다

- **목적**: 스케줄된 session 은 success, 스케줄되지 않은 session 은 skipped 로 반환하는지 확인한다
- **의존성(mock):**
  - `repository.get_scheduling_data("default")`:
    - 반환: `SchedulingData(...)`
  - `provisioner.schedule_scaling_group("default", scheduling_data)`:
    - 반환: `ScheduleResult(scheduled_sessions=[ScheduledSessionData(session_id=s1, ...)])`
    - 참고: s2 는 우선순위나 자원 제약으로 이번 주기에 스케줄되지 않았다
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 1
    - `result.successes[0].session_id` == `s1`
    - `len(result.failures)` == 0
    - `len(result.skipped)` == 1
    - `result.skipped[0].session_id` == `s2`
    - `result.skipped[0].from_status` == `SessionStatus.PENDING`
    - `result.skipped[0].reason` == `"not-scheduled-this-cycle"`
- **분류**: `happy-path`

---

### SC-SS-004: 빈 session 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.skipped)` == 0
  - **mock 호출:**
    - `repository.get_scheduling_data.assert_not_called()`
- **분류**: `edge-case`

---

### SC-SS-005: 자원 부족, 모든 session 이 skipped 로 반환된다

- **목적**: provisioner 가 아무 session 도 스케줄하지 않았을 때 모든 session 을 skipped 로 반환하는지 확인한다
- **의존성(mock):**
  - `repository.get_scheduling_data("default")`:
    - 반환: `SchedulingData(...)`
  - `provisioner.schedule_scaling_group("default", scheduling_data)`:
    - 반환: `ScheduleResult(scheduled_sessions=[])` (자원 부족으로 스케줄된 session 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
    - `len(result.skipped)` == 2
    - `result.skipped[0].session_id` == `s1`
    - `result.skipped[0].reason` == `"not-scheduled-this-cycle"`
    - `result.skipped[1].session_id` == `s2`
    - `result.skipped[1].reason` == `"not-scheduled-this-cycle"`
  - **mock 호출:**
    - `repository.get_scheduling_data.assert_called_once_with("default")`
    - `provisioner.schedule_scaling_group.assert_called_once()`
- **분류**: `edge-case`

---

## StartSessionsLifecycleHandler

**실제 동작:**
1. 입력이 비어 있으면 조기에 반환한다
2. 입력 `SessionWithKernels` 에서 session id 를 추출한다
3. `search_sessions_with_kernels_and_user()` 로 repository 에서 `SessionDataForStart` 를 조회한다
4. session 과 image config 를 담아 `launcher.start_sessions_for_handler()` 를 호출한다
5. 입력 session 전체를 success 로 반환한다(kernel 생성은 비동기다)

**의존성(mock 대상):**
- `launcher: SessionLauncher`
  - `start_sessions_for_handler(sessions, image_configs)` → `None`
- `repository: SchedulerRepository`
  - `search_sessions_with_kernels_and_user(querier)` → `SessionsWithUserResult`

**상태 전이:**
```python
success = TransitionStatus(session=CREATING, kernel=CREATING)
expired = TransitionStatus(session=PENDING, kernel=PENDING)
```

---

### SC-ST-001: 모든 session 이 정상 시작된다

- **목적**: PREPARED 상태 session 이 모두 kernel 생성을 트리거하고 success 로 표시되는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_with_kernels_and_user(querier)`:
    - 반환: `SessionsWithUserResult(sessions=[session1_data, session2_data], image_configs={...})`
  - `launcher.start_sessions_for_handler(sessions_data, image_configs)`:
    - 반환: `None`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PREPARED), SessionWithKernels(s2, status=PREPARED)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.PREPARED`
    - `result.successes[0].reason` == `"triggered-by-scheduler"`
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.search_sessions_with_kernels_and_user.assert_called_once()`
    - `launcher.start_sessions_for_handler.assert_called_once()`
- **분류**: `happy-path`

---

### SC-ST-002: 빈 session 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `launcher.start_sessions_for_handler.assert_not_called()`
- **분류**: `edge-case`

---

### SC-ST-003: launcher 예외가 전파된다

- **목적**: launcher 예외가 sokovan coordinator 로 전파되는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_with_kernels_and_user(querier)`:
    - 반환: `SessionsWithUserResult(...)`
  - `launcher.start_sessions_for_handler(...)`:
    - 발생: `AgentError("Connection failed")`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PREPARED)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **예외**: `AgentError` 발생(sokovan coordinator 가 expired 전이로 처리)
- **분류**: `error-case`

---

## TerminateSessionsLifecycleHandler

**실제 동작:**
1. 입력이 비어 있으면 조기에 반환한다
2. 입력 `SessionWithKernels` 에서 session id 를 추출한다
3. `get_terminating_sessions_by_ids()` 로 repository 에서 `TerminatingSessionData` 를 조회한다
4. 종료 중인 session 이 없으면 조기에 반환한다
5. 종료 RPC 를 보내기 위해 `terminator.terminate_sessions_for_handler()` 를 호출한다
6. 빈 결과를 반환한다(상태 변경은 agent event 로 일어난다)

**의존성(mock 대상):**
- `terminator: SessionTerminator`
  - `terminate_sessions_for_handler(terminating_sessions)` → `None`
- `repository: SchedulerRepository`
  - `get_terminating_sessions_by_ids(session_ids)` → `list[TerminatingSessionData]`

**상태 전이:**
```python
success = None  # Handled via agent events
expired = TransitionStatus(session=TERMINATED, kernel=TERMINATED)
give_up = TransitionStatus(session=TERMINATED, kernel=TERMINATED)
```

---

### SC-TS-001: session 이 종료 RPC 를 트리거하고 빈 결과를 반환한다

- **목적**: 종료 RPC 는 호출되지만 handler 가 빈 결과를 반환하는지 확인한다
- **의존성(mock):**
  - `repository.get_terminating_sessions_by_ids([s1, s2])`:
    - 반환: `[TerminatingSessionData(s1, ...), TerminatingSessionData(s2, ...)]`
  - `terminator.terminate_sessions_for_handler(terminating_sessions)`:
    - 반환: `None`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=TERMINATING), SessionWithKernels(s2, status=TERMINATING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0 (여기서 상태 전이는 없다)
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.get_terminating_sessions_by_ids.assert_called_once_with([s1, s2])`
    - `terminator.terminate_sessions_for_handler.assert_called_once()`
- **분류**: `happy-path`

---

### SC-TS-002: 종료 중인 session 이 없으면 빈 결과를 반환한다

- **목적**: handler 가 빈 repository 결과를 처리하는지 확인한다
- **의존성(mock):**
  - `repository.get_terminating_sessions_by_ids([s1])`:
    - 반환: `[]`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=TERMINATING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `terminator.terminate_sessions_for_handler.assert_not_called()`
- **분류**: `edge-case`

---

### SC-TS-003: 빈 session 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
  - **mock 호출:**
    - `repository.get_terminating_sessions_by_ids.assert_not_called()`
- **분류**: `edge-case`

---

## DeprioritizeSessionsLifecycleHandler

**실제 동작:**
1. 입력이 비어 있으면 조기에 반환한다
2. 입력 `SessionWithKernels` 에서 session id 를 추출한다
3. 우선순위를 DEPRIORITIZE_AMOUNT(10) 만큼 낮추기 위해 `repository.lower_session_priority()` 를 호출한다
4. 입력 session 전체를 success 로 반환한다(PENDING 으로 전이)

**의존성(mock 대상):**
- `repository: SchedulerRepository`
  - `lower_session_priority(session_ids, amount, min_priority)` → `None`

**상태 전이:**
```python
success = TransitionStatus(session=PENDING, kernel=None)  # No kernel change
```

---

### SC-DP-001: session 우선순위가 정상적으로 낮아진다

- **목적**: session 우선순위가 낮아지고 success 로 표시되는지 확인한다
- **의존성(mock):**
  - `repository.lower_session_priority([s1, s2], 10, SESSION_PRIORITY_MIN)`:
    - 반환: `None`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=DEPRIORITIZING), SessionWithKernels(s2, status=DEPRIORITIZING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.DEPRIORITIZING`
    - `result.successes[0].reason` == `"deprioritized-for-rescheduling"`
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.lower_session_priority.assert_called_once_with([s1, s2], 10, SESSION_PRIORITY_MIN)`
- **분류**: `happy-path`

---

### SC-DP-002: 빈 session 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
  - **mock 호출:**
    - `repository.lower_session_priority.assert_not_called()`
- **분류**: `edge-case`

---

## SweepSessionsLifecycleHandler

**실제 동작:**
1. 입력이 비어 있으면 조기에 반환한다
2. 입력 `SessionWithKernels` 에서 session id 를 추출한다
3. `get_pending_timeout_sessions_by_ids()` 로 repository 에서 타임아웃된 session 을 조회한다
4. 타임아웃된 session 이 없으면 조기에 반환한다
5. 타임아웃된 session 을 FAILURE 로 반환한다(sokovan coordinator 가 expired 로 분류한다)

**의존성(mock 대상):**
- `repository: SchedulerRepository`
  - `get_pending_timeout_sessions_by_ids(session_ids)` → `list[PendingTimeoutSessionData]`

**참고:** cache 무효화는 sokovan coordinator 의 PostProcessor 가 처리한다.

**상태 전이:**
```python
success = None  # No success transition for sweep
expired = TransitionStatus(session=TERMINATING, kernel=TERMINATING)
```

---

### SC-SW-001: 타임아웃된 session 을 failure 로 반환한다

- **목적**: pending timeout 을 초과한 session 이 failure 로 반환되는지 확인한다
- **의존성(mock):**
  - `repository.get_pending_timeout_sessions_by_ids([s1, s2])`:
    - 반환: `[PendingTimeoutSessionData(session_id=s1, ...)]` (s1 만 타임아웃)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 1
    - `result.failures[0].session_id` == `s1`
    - `result.failures[0].from_status` == `SessionStatus.PENDING`
    - `result.failures[0].reason` == `"PENDING_TIMEOUT_EXCEEDED"`
- **분류**: `happy-path`

---

### SC-SW-002: 타임아웃된 session 이 없으면 빈 결과를 반환한다

- **목적**: handler 가 타임아웃된 session 이 없는 경우를 처리하는지 확인한다
- **의존성(mock):**
  - `repository.get_pending_timeout_sessions_by_ids([s1])`:
    - 반환: `[]`
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING)]`
- **실행:** `await handler.execute("default", sessions)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
- **분류**: `edge-case`

---

### SC-SW-003: 빈 session 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음)
- **입력:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `repository.get_pending_timeout_sessions_by_ids.assert_not_called()`
- **분류**: `edge-case`

---

## 테스트 커버리지 요약

| handler | happy-path | edge-case | error-case | 합계 |
|---------|------------|-----------|------------|-------|
| CheckPrecondition | SC-CP-001 | SC-CP-002 | SC-CP-003 | 3 |
| ScheduleSessions | SC-SS-001, SC-SS-003 | SC-SS-002, SC-SS-004, SC-SS-005 | - | 5 |
| StartSessions | SC-ST-001 | SC-ST-002 | SC-ST-003 | 3 |
| TerminateSessions | SC-TS-001 | SC-TS-002, SC-TS-003 | - | 3 |
| DeprioritizeSessions | SC-DP-001 | SC-DP-002 | - | 2 |
| SweepSessions | SC-SW-001 | SC-SW-002, SC-SW-003 | - | 3 |
| **합계** | **7** | **9** | **3** | **19** |

### 주요 검증 지점

1. **의존성 호출 검증**: mock 으로 대체한 의존성(repository, launcher, provisioner, terminator)을 올바른 인자로 호출하는지 확인한다
2. **반환 값 검증**: successes, failures, skipped 목록 크기와 session_id, from_status, reason 을 확인한다
3. **skipped 반환 검증**: 우선순위나 자원 제약으로 스케줄되지 않은 session 이 skipped 로 반환되는지 확인한다
4. **예외 전파 검증**: 의존성 예외가 sokovan coordinator 로 올바르게 전파되는지 확인한다
5. **빈 입력 처리**: 빈 session 목록을 정상적으로 처리한다
