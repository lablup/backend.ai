# SessionTerminator 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 `SessionTerminator` 의 테스트 시나리오를 정의한다.

terminator 는 다음을 처리한다.
1. **session 종료**: agent 에 `destroy_kernel()` RPC 를 보낸다.
2. **stale kernel 감지**: 2단계 검증(Valkey + agent).

**소스 파일:** `sokovan/scheduler/terminator/terminator.py`

---

## terminate_sessions_for_handler 흐름

```python
async def terminate_sessions_for_handler(terminating_sessions) -> None:
    # 1. Collect termination tasks for all kernels with agents
    for session in terminating_sessions:
        for kernel in session.kernels:
            if kernel.agent_id:
                task = _terminate_kernel(agent_id, kernel_id, session_id, reason, slots)
                all_tasks.append(task)
            else:
                skipped_kernels += 1

    # 2. Execute all termination tasks concurrently
    results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # 3. No return value (status updates via events)
    # Internally _terminate_sessions_internal() returns ScheduleResult but
    # public API returns None
```

---

## check_stale_kernels 흐름

```python
async def check_stale_kernels(kernels) -> list[KernelId]:
    # Stage 1: Check presence status from Valkey
    statuses = await valkey_schedule.check_kernel_presence_status_batch(kernel_ids, agent_ids)

    # Filter STALE or None
    stale_kernel_id_set = {
        kernel_id for kernel_id in kernel_ids
        if statuses.get(kernel_id) is None or status.presence == STALE
    }

    # Stage 2: Verify with agent
    for kernel_info in kernels:
        if kernel_info.id not in stale_kernel_id_set:
            continue
        is_running = await client.check_running(kernel_info.id)
        if is_running is False:  # Explicit False only
            dead_kernel_ids.append(kernel_info.id)

    return dead_kernel_ids
```

---

## 의존성(mock 대상)

- `agent_client_pool: AgentClientPool`
  - `acquire(agent_id)` → `AsyncContextManager[AgentClient]`
  - `AgentClient.destroy_kernel(kernel_id, session_id, reason, suppress_events)` → `None`
  - `AgentClient.check_running(kernel_id)` → `bool | None`
- `valkey_schedule: ValkeyScheduleClient`
  - `check_kernel_presence_status_batch(kernel_ids, agent_ids)` → `dict[KernelId, HealthStatus]`

---

## session 종료 시나리오

### SC-TE-001: 모든 kernel 을 정상적으로 종료한다

- **목적**: agent 가 있는 모든 kernel 에 destroy_kernel 을 호출하는지 확인한다
- **의존성(mock):**
  - `agent_client.destroy_kernel(k1, s1, reason, suppress_events=False)`:
    - 반환: `None`
  - `agent_client.destroy_kernel(k2, s1, reason, suppress_events=False)`:
    - 반환: `None`
- **입력:**
  - agent `a1` 에 kernel 2개를 가진 session `s1`
- **실행:** `await terminator.terminate_sessions_for_handler([session])`
- **검증:**
  - `destroy_kernel` 을 두 번 호출한다
  - 반환 값이 없다(`None`). 상태 변경은 event 로 처리한다
- **분류**: `happy-path`

---

### SC-TE-002: agent 가 없는 kernel 은 생략한다

- **목적**: agent 배정이 없는 kernel 을 생략하는지 확인한다
- **의존성(mock):**
  - kernel 하나에만 agent 가 있다
- **입력:**
  - kernel 2개를 가진 session: `k1`(agent=a1), `k2`(agent=None)
- **실행:** `await terminator.terminate_sessions_for_handler([session])`
- **검증:**
  - `destroy_kernel` 을 한 번 호출한다(k1 만)
  - 생략한 kernel 을 log 에 기록한다
- **분류**: `edge-case`

---

### SC-TE-003: 빈 session 목록은 즉시 반환한다

- **목적**: 빈 입력에 조기 반환하는지 확인한다
- **입력:**
  - `terminating_sessions = []`
- **실행:** `await terminator.terminate_sessions_for_handler([])`
- **검증:**
  - 반환 값이 없다(`None`)
  - agent 호출이 없다
- **분류**: `edge-case`

---

### SC-TE-004: 일부 종료 실패를 기록한다

- **목적**: 일부 실패가 다른 종료를 차단하지 않는지 확인한다
- **의존성(mock):**
  - `agent_client.destroy_kernel(k1, ...)`:
    - 발생: `AgentError("Agent offline")`
  - `agent_client.destroy_kernel(k2, ...)`:
    - 반환: `None`
- **입력:**
  - agent 2개에 kernel 을 가진 session
- **실행:** `await terminator.terminate_sessions_for_handler([session])`
- **검증:**
  - destroy_kernel 을 둘 다 시도한다(return_exceptions 로 gather)
  - 실패를 warning 으로 기록한다
  - 성공 1건, 실패 1건
- **분류**: `error-case`

---

### SC-TE-005: 여러 session 을 병렬로 종료한다

- **목적**: 모든 session 의 kernel 을 동시에 처리하는지 확인한다
- **의존성(mock):**
  - destroy_kernel 호출이 모두 성공한다
- **입력:**
  - kernel 2개씩 가진 session 3개(kernel 6개)
- **실행:** `await terminator.terminate_sessions_for_handler(sessions)`
- **검증:**
  - 종료 task 6개를 생성한다
  - 모두 gather 로 실행한다(병렬)
- **분류**: `happy-path`

---

### SC-TE-006: KernelTerminationResult 가 세부 정보를 담는다

- **목적**: 종료 결과 구조를 확인한다
- **의존성(mock):**
  - `destroy_kernel` 이 정상으로 반환한다
- **입력:**
  - `occupied_slots = ResourceSlot(cpu=4, mem=8GB)` 인 kernel
- **실행:** `_terminate_kernel()` 을 통해 실행한다
- **검증:**
  - 결과에 `kernel_id`, `agent_id`, `occupied_slots`, `success=True` 가 있다
- **분류**: `happy-path`

---

### SC-TE-007: 종료 에러를 결과에 담는다

- **목적**: 실패 시 에러 세부 정보를 담는지 확인한다
- **의존성(mock):**
  - `destroy_kernel` 이 `AgentError("Connection timeout")` 를 발생시킨다
- **실행:** `_terminate_kernel()` 을 통해 실행한다
- **검증:**
  - 결과에 `success=False`, `error="Connection timeout"` 이 있다
- **분류**: `error-case`

---

## stale kernel 감지 시나리오

### SC-TE-008: stale kernel 이 없고 Valkey 가 모두 ALIVE 를 반환한다

- **목적**: stale kernel 이 없을 때 조기 반환하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1, k2], ...)`:
    - 반환: `{k1: ALIVE, k2: ALIVE}`
- **입력:**
  - `kernels = [KernelInfo(k1, agent=a1), KernelInfo(k2, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[]`
  - `agent_client.check_running.assert_not_called()`(2단계가 필요 없다)
- **분류**: `happy-path`

---

### SC-TE-009: Valkey 가 STALE 을 반환하고 agent 가 죽음을 확인한다

- **목적**: 죽은 kernel 에 2단계 감지를 모두 수행하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - 반환: `{k1: STALE}`
  - `agent_client.check_running(k1)`:
    - 반환: `False`
- **입력:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[k1]`
  - 검증을 위해 `check_running` 을 호출한다
- **분류**: `happy-path`

---

### SC-TE-010: Valkey 가 STALE 을 반환했지만 agent 는 살아 있음을 보인다

- **목적**: 오탐 처리를 확인한다(kernel 은 실제로 실행 중)
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - 반환: `{k1: STALE}`
  - `agent_client.check_running(k1)`:
    - 반환: `True`
- **입력:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[]`(kernel 이 살아 있고 죽지 않았다)
- **분류**: `edge-case`

---

### SC-TE-011: presence 정보가 없으면(None) stale 로 처리한다

- **목적**: None 상태가 agent 검증을 트리거하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - 반환: `{}`(k1 이 결과에 없다)
  - `agent_client.check_running(k1)`:
    - 반환: `False`
- **입력:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[k1]`
  - 없는 상태를 STALE 과 같게 처리한다
- **분류**: `edge-case`

---

### SC-TE-012: agent 검증이 실패하면 kernel 을 생략한다

- **목적**: agent 통신 에러를 정상적으로 처리하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch(...)`:
    - 반환: `{k1: STALE, k2: STALE}`
  - `agent_client.check_running(k1)`:
    - 발생: `Exception("Agent unreachable")`
  - `agent_client.check_running(k2)`:
    - 반환: `False`
- **입력:**
  - 둘 다 stale 인 kernel 2개
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[k2]`(k1 은 에러로 생략)
  - k1 에 warning 을 기록한다
- **분류**: `error-case`

---

### SC-TE-013: agent 가 없는 kernel 은 2단계에서 생략한다

- **목적**: agent 가 없는 kernel 을 검증할 수 없는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - 반환: `{k1: STALE}`
- **입력:**
  - `kernels = [KernelInfo(k1, agent=None)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[]`(agent 없이는 검증할 수 없다)
  - `agent_client_pool.acquire.assert_not_called()`
- **분류**: `edge-case`

---

### SC-TE-014: 빈 kernel 목록은 즉시 반환한다

- **목적**: 빈 입력에 조기 반환하는지 확인한다
- **입력:**
  - `kernels = []`
- **실행:** `await terminator.check_stale_kernels([])`
- **검증:**
  - 반환: `[]`
  - Valkey 와 agent 호출이 없다
- **분류**: `edge-case`

---

### SC-TE-015: 결과가 섞여 있음, 일부는 살아 있고 일부는 죽었다

- **목적**: kernel 여러 개를 올바르게 필터링하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1, k2, k3], ...)`:
    - 반환: `{k1: ALIVE, k2: STALE, k3: STALE}`
  - `agent_client.check_running(k2)`:
    - 반환: `False`(죽음)
  - `agent_client.check_running(k3)`:
    - 반환: `True`(살아 있음)
- **입력:**
  - kernel 3개: k1(ALIVE), k2(STALE, 죽음), k3(STALE, 살아 있음)
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[k2]`(k2 만 실제로 죽었다)
  - k2, k3 에만 `check_running` 을 호출한다
  - k1 에는 `check_running` 을 호출하지 않는다(Valkey 가 ALIVE)
- **분류**: `happy-path`

---

### SC-TE-016: agent 검증이 None 을 반환하면 kernel 을 생략한다

- **목적**: agent 가 None 을 반환해도 kernel 을 종료하지 않는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - 반환: `{k1: STALE}`
  - `agent_client.check_running(k1)`:
    - 반환: `None`(불확실)
- **입력:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - 반환: `[]`(종료하려면 명시적인 False 가 필요하다)
- **참고**: `is_running is False` 일 때만 종료를 트리거한다
- **분류**: `edge-case`

---

## handler 와의 통합

### SC-TE-INT-001: stale sweep 전체 흐름

- **목적**: SweepStaleKernelsKernelHandler 로 종단 간 테스트를 한다
- **설정:**
  - RUNNING kernel 5개
  - Valkey: ALIVE 2개, STALE 3개
  - agent 검증: stale 중 1개 죽음, 2개 살아 있음
- **실행 흐름:**
  1. sokovan coordinator 가 RUNNING kernel 을 조회한다
  2. handler 가 `terminator.check_stale_kernels()` 를 호출한다
  3. terminator 가 Valkey 를 확인한 뒤 agent 를 확인한다
  4. 죽은 kernel id 1개를 반환한다
  5. handler 가 죽은 kernel 을 failure 로 반환한다
  6. sokovan coordinator 가 kernel 을 TERMINATED 로 표시한다
- **검증:**
  - kernel 1개만 종료한다(올바른 필터링)
- **분류**: `happy-path`
