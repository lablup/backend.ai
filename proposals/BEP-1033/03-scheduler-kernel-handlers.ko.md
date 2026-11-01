# scheduler kernel handler 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 scheduler kernel handler 의 테스트 시나리오를 정의한다.

kernel handler 는 session 이 아니라 `KernelInfo` 객체를 직접 다룬다. sokovan coordinator 가
`search_kernels_for_handler()` 로 kernel 을 조회하고 kernel 수준 상태 전이를 적용한다.

**소스 파일:**
- `sokovan/scheduler/handlers/kernel/sweep_stale_kernels.py`

---

## SweepStaleKernelsKernelHandler (SWEEP_STALE_KERNELS)

**실제 동작:**
1. sokovan coordinator 에서 `KernelInfo` 목록을 받는다(RUNNING kernel)
2. 2단계 검증을 위해 `terminator.check_stale_kernels()` 에 위임한다:
   - 1단계: Valkey 의 presence 상태를 확인한다
   - 2단계: agent 의 `check_running()` RPC 로 검증한다
3. kernel 을 분류한다:
   - **successes**: 살아 있는 kernel(상태 변경 없음)
   - **failures**: 죽었거나 stale 상태인 kernel(TERMINATED 로 전이)

**의존성(mock 대상):**
- `terminator: SessionTerminator`
  - `check_stale_kernels(kernels)` → `list[KernelId]` (죽은 kernel id)

**참고:** schedule 표시는 sokovan coordinator 가 kernel 실패 결과를 바탕으로 직접 처리한다.

**상태 전이:**
```python
success = None  # Maintain current status (kernel is alive)
failure = KernelStatus.TERMINATED  # Kernel is dead/stale
```

---

### SC-SK-001: 모든 kernel 이 살아 있음, 상태 변경 없음

- **목적**: 살아 있음을 확인한 kernel 을 successes 로 반환하는지 확인한다
- **의존성(mock):**
  - `terminator.check_stale_kernels([k1, k2])`:
    - 반환: `[]`  # 죽은 kernel 없음
- **입력:**
  - `scaling_group`: `"default"`
  - `kernels`: `[KernelInfo(k1, status=RUNNING), KernelInfo(k2, status=RUNNING)]`
- **실행:** `await handler.execute("default", kernels)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 2
    - `result.successes[0].kernel_id` == `k1`
    - `result.successes[0].from_status` == `KernelStatus.RUNNING`
    - `result.successes[0].reason` == `None`
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `terminator.check_stale_kernels.assert_called_once()`
- **분류**: `happy-path`

---

### SC-SK-002: 죽은 kernel 감지, failure 로 표시

- **목적**: 죽은 kernel 을 TERMINATED 전이를 위해 failures 로 반환하는지 확인한다
- **의존성(mock):**
  - `terminator.check_stale_kernels([k1, k2, k3])`:
    - 반환: `[k2]`  # k2 가 죽었다
- **입력:**
  - `scaling_group`: `"default"`
  - `kernels`: `[KernelInfo(k1, status=RUNNING), KernelInfo(k2, status=RUNNING), KernelInfo(k3, status=RUNNING)]`
- **실행:** `await handler.execute("default", kernels)`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 2  # k1 과 k3
    - `len(result.failures)` == 1
    - `result.failures[0].kernel_id` == `k2`
    - `result.failures[0].from_status` == `KernelStatus.RUNNING`
    - `result.failures[0].reason` == `"STALE_KERNEL"`
- **분류**: `happy-path`

---

### SC-SK-003: 빈 kernel 목록은 빈 결과를 반환한다

- **목적**: handler 가 빈 입력을 에러 없이 처리하는지 확인한다
- **의존성(mock):**
  - (호출 없음, 조기 반환)
- **입력:**
  - `scaling_group`: `"default"`
  - `kernels`: `[]`
- **실행:** `await handler.execute("default", [])`
- **검증:**
  - **반환 값:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **mock 호출:**
    - `terminator.check_stale_kernels.assert_not_called()`
- **분류**: `edge-case`

---

## 통합: kernel handler 와 sokovan coordinator 흐름

### SC-KH-INT-001: stale kernel sweep 전체 흐름

- **목적**: stale kernel 감지와 상태 변경의 종단 간 테스트
- **설정:**
  - RUNNING kernel 3개: `k1`, `k2`, `k3`
  - Valkey presence: `k1` = STALE, `k2` = ALIVE, `k3` = STALE
  - agent 검증: `k1` = False(죽음), `k3` = True(실제로 살아 있음)
- **실행 흐름:**
  1. sokovan coordinator 가 `search_kernels_for_handler()` 로 RUNNING kernel 을 조회한다
  2. sokovan coordinator 가 `handler.execute("default", [k1, k2, k3])` 를 호출한다
  3. handler 가 `terminator.check_stale_kernels()` 를 호출한다
  4. terminator 가 `[k1]` 을 반환한다(k1 만 실제로 죽었다)
  5. handler 가 `successes=[k2, k3], failures=[k1]` 을 반환한다
  6. sokovan coordinator 가 `_handle_kernel_result()` 를 호출한다
  7. sokovan coordinator 가 `kernel_state_engine.mark_kernel_terminated(k1, "kernel_handler_failure")` 를 호출한다
  8. sokovan coordinator 가 `handler.post_process(result)` 를 호출한다
- **검증:**
  - `k1` 만 TERMINATED 로 표시한다
  - `k2` 와 `k3` 는 RUNNING 으로 남는다
  - DETECT_KERNEL_TERMINATION 을 트리거한다
- **분류**: `happy-path`

---

### SC-KH-INT-002: kernel handler 의 lock 획득

- **목적**: sokovan coordinator 가 kernel handler 에 올바른 lock 을 획득하는지 확인한다
- **의존성(mock):**
  - `lock_factory(LockID.LOCKID_SOKOVAN_TARGET_TERMINATING, lifetime)`:
    - 반환: AsyncContextManager(mock)
- **입력:**
  - handler: `SweepStaleKernelsKernelHandler`, `lock_id` 보유
- **실행:** sokovan coordinator 의 `_process_kernel_schedule()` 를 통해 실행한다
- **검증:**
  - `LockID.LOCKID_SOKOVAN_TARGET_TERMINATING` 으로 lock 을 획득한다
  - handler 실행 후 lock 을 해제한다
- **분류**: `happy-path`

---

## SessionTerminator 의 check_stale_kernels 구현

`SessionTerminator` 의 `check_stale_kernels()` method 는 2단계 검증을 수행한다:

### 1단계: Valkey presence 확인

```python
statuses = await self._valkey_schedule.check_kernel_presence_status_batch(
    kernel_ids, agent_ids=agent_ids
)
# Filter STALE or None status
stale_kernel_id_set = {
    kernel_id for kernel_id in kernel_ids
    if (status := statuses.get(kernel_id)) is None
    or status.presence == HealthCheckStatus.STALE
}
```

### 2단계: agent 검증

```python
for kernel_info in kernels:
    if kernel_info.id not in stale_kernel_id_set:
        continue
    async with self._agent_client_pool.acquire(agent_id) as client:
        is_running = await client.check_running(kernel_info.id)
    if is_running is False:  # Explicit False only
        dead_kernel_ids.append(kernel_info.id)
```

---

### SC-CSK-001: Valkey 가 모두 ALIVE 를 반환한다

- **목적**: 잠재적으로 stale 상태인 kernel 이 없을 때 조기에 반환하는지 테스트한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - 반환: `{k1: HealthCheckStatus.ALIVE, k2: HealthCheckStatus.ALIVE}`
- **입력:**
  - `kernels`: `[KernelInfo(k1, agent=a1), KernelInfo(k2, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - **반환 값:** `[]`(죽은 kernel 없음)
  - **mock 호출:**
    - `agent_client_pool.acquire.assert_not_called()`(agent 검증 불필요)
- **분류**: `happy-path`

---

### SC-CSK-002: Valkey 가 STALE 을 반환하고 agent 가 죽음을 확인한다

- **목적**: 죽은 kernel 이 확인된 경우 2단계 검증 전체를 테스트한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - 반환: `{k1: HealthCheckStatus.STALE}`
  - `agent_client.check_running(k1)`:
    - 반환: `False`
- **입력:**
  - `kernels`: `[KernelInfo(k1, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - **반환 값:** `[k1]`
  - **mock 호출:**
    - `agent_client.check_running.assert_called_once_with(k1)`
- **분류**: `happy-path`

---

### SC-CSK-003: Valkey 가 STALE 을 반환했지만 agent 는 실행 중임을 보인다

- **목적**: Valkey 의 오탐을 테스트한다(kernel 은 실제로 살아 있음)
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - 반환: `{k1: HealthCheckStatus.STALE}`
  - `agent_client.check_running(k1)`:
    - 반환: `True`
- **입력:**
  - `kernels`: `[KernelInfo(k1, agent=a1)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - **반환 값:** `[]`(kernel 이 실제로 살아 있음)
- **분류**: `edge-case`

---

### SC-CSK-004: agent 검증 실패, kernel 생략

- **목적**: agent 통신 실패를 정상적으로 처리하는지 테스트한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - 반환: `{k1: HealthCheckStatus.STALE, k2: HealthCheckStatus.STALE}`
  - `agent_client.check_running(k1)`:
    - 발생: `Exception("Connection refused")`
  - `agent_client.check_running(k2)`:
    - 반환: `False`
- **입력:**
  - `kernels`: `[KernelInfo(k1, agent=a1), KernelInfo(k2, agent=a2)]`
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - **반환 값:** `[k2]`(k1 은 에러로 생략, k2 는 죽음 확인)
  - k1 에 warning 을 기록한다
- **분류**: `error-case`

---

### SC-CSK-005: agent 가 없는 kernel 은 생략한다

- **목적**: 배정된 agent 가 없는 kernel 을 생략하는지 테스트한다
- **의존성(mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - 반환: `{k1: HealthCheckStatus.STALE}`
- **입력:**
  - `kernels`: `[KernelInfo(k1, agent=None)]`  # 배정된 agent 없음
- **실행:** `await terminator.check_stale_kernels(kernels)`
- **검증:**
  - **반환 값:** `[]`(agent 없이는 검증할 수 없음)
  - `agent_client_pool.acquire.assert_not_called()`
- **분류**: `edge-case`
