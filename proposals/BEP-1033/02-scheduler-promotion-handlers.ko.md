# scheduler 승격 spec 테스트 시나리오

## 개요

승격 동작은 선언형 `PromotionSpec` 으로 처리한다. 이전의 handler 기반 구현은 단순한 변환 로직에는
불필요한 추상화를 제거하면서 sokovan coordinator 로 통합했다.

sokovan coordinator 는 spec 의 kernel 매칭 조건으로 session 을 조회하고, 일치한 session 을
`SessionTransitionInfo` 로 직접 변환한다.

**소스 파일:**
- `sokovan/scheduler/types.py` - PromotionSpec 정의
- `sokovan/scheduler/factory.py` - spec 정의와 매핑
- `sokovan/scheduler/coordinator.py` - 승격 처리 로직
- `data/kernel/types.py` - KernelStatus 상태 묶음 정의

---

## PromotionSpec 구조

```python
@dataclass(frozen=True)
class PromotionSpec:
    name: str                                    # Operation identifier
    target_statuses: list[SessionStatus]         # Target session statuses
    target_kernel_statuses: list[KernelStatus]   # Kernel matching conditions
    kernel_match_type: KernelMatchType           # ALL/ANY/NOT_ANY
    success_status: SessionStatus                # Status to transition to on success
    reason: str                                  # Transition reason
```

---

## KernelStatus 상태 묶음

```python
class KernelStatus(CIStrEnum):
    @classmethod
    def pre_prepared_statuses(cls) -> frozenset[KernelStatus]:
        """Statuses before image pulling completion"""
        return frozenset((PENDING, SCHEDULED, PREPARING, BUILDING, PULLING))

    @classmethod
    def pre_running_statuses(cls) -> frozenset[KernelStatus]:
        """Statuses before kernel execution"""
        return frozenset((PENDING, SCHEDULED, PREPARING, BUILDING, PULLING, PREPARED, CREATING))
```

---

## 승격 spec 정의 4개

| ScheduleType | name | target_statuses | kernel_match | success_status | reason |
|--------------|------|-----------------|--------------|----------------|--------|
| CHECK_PULLING_PROGRESS | promote-to-prepared | PREPARING, PULLING | NOT_ANY(pre_prepared) | PREPARED | triggered-by-scheduler |
| CHECK_CREATING_PROGRESS | promote-to-running | CREATING | NOT_ANY(pre_running) | RUNNING | triggered-by-scheduler |
| CHECK_TERMINATING_PROGRESS | promote-to-terminated | TERMINATING | ALL(TERMINATED) | TERMINATED | triggered-by-scheduler |
| DETECT_KERNEL_TERMINATION | detect-termination | PENDING~RUNNING, DEPRIORITIZING | ANY(TERMINATED, CANCELLED) | TERMINATING | ABNORMAL_TERMINATION |

### kernel 매칭 의미

- **NOT_ANY**: 지정한 상태에 있는 kernel 이 없어야 한다(pre-X 상태를 벗어났는지 감지한다)
- **ANY**: 지정한 상태에 있는 kernel 이 하나 이상 있어야 한다(이상 동작을 감지한다)
- **ALL**: 모든 kernel 이 지정한 상태에 있어야 한다(완료를 검증한다)

---

## sokovan coordinator 승격 처리 흐름

```
_process_promotion_schedule(spec)
    └── per scaling_group (parallel):
            _process_promotion_scaling_group(spec, schedule_type, scaling_group)
                ├── Build BatchQuerier with kernel match conditions
                ├── repository.search_sessions_for_handler(querier)
                ├── [Phase: {spec.name}]  # e.g., "promote-to-prepared"
                │   └── [Step: check_kernel_status]
                │       └── Build SessionTransitionInfo from session_infos
                ├── _handle_promotion_status_transitions(spec, result, records)
                │   ├── Get hook for target status
                │   ├── Execute hooks (fetch full data if needed)
                │   └── Batch update sessions with history
                └── Run post-processors
```

---

## sokovan coordinator 승격 처리 시나리오

### SC-PS-001: NOT_ANY 조회 조건 검증(CHECK_PULLING_PROGRESS)

- **목적**: NOT_ANY 의미가 BatchQuerier 에 정확히 적용되는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - 반환: `[SessionInfo(s1, PREPARING), SessionInfo(s2, PULLING)]`
- **입력:**
  - `spec`: CHECK_PULLING_PROGRESS 의 PromotionSpec
  - `scaling_group`: `"default"`
- **실행:** `await coordinator._process_promotion_scaling_group(spec, schedule_type, "default")`
- **검증:**
  - **mock 호출:**
    - `search_sessions_for_handler` 호출의 querier 검증:
      - `SessionConditions.by_scaling_group("default")` 포함
      - `SessionConditions.by_statuses([PREPARING, PULLING])` 포함
      - `SessionConditions.by_kernel_match(KernelStatus.pre_prepared_statuses(), NOT_ANY)` 포함
- **분류**: `happy-path`

---

### SC-PS-002: ANY 조회 조건 검증(DETECT_KERNEL_TERMINATION)

- **목적**: ANY 의미가 BatchQuerier 에 정확히 적용되는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - 반환: `[SessionInfo(s1, RUNNING)]`, 일부 kernel 이 TERMINATED
- **입력:**
  - `spec`: DETECT_KERNEL_TERMINATION 의 PromotionSpec
  - `scaling_group`: `"default"`
- **검증:**
  - **mock 호출:**
    - `SessionConditions.by_kernel_match([TERMINATED], ANY)` 포함
- **분류**: `happy-path`

---

### SC-PS-003: SessionTransitionInfo 생성 검증

- **목적**: SessionInfo 에서 SessionTransitionInfo 로 올바르게 변환하는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - 반환: `[SessionInfo(s1, status=PREPARING, access_key="ak1", creation_id="c1")]`
  - `repository.update_sessions_status_with_history()`: 성공
- **입력:**
  - `spec`: promote-to-prepared(reason="triggered-by-scheduler")
  - `scaling_group`: `"default"`
- **검증:**
  - **상태 변경 호출:**
    - `session_id` == `s1`
    - `from_status` == `SessionStatus.PREPARING`
    - `to_status` == `SessionStatus.PREPARED`
    - `reason` == `"triggered-by-scheduler"`
- **분류**: `happy-path`

---

### SC-PS-004: 빈 session 목록 처리

- **목적**: 일치하는 session 이 없을 때 조기에 반환하는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler(querier)`: `[]` 반환
  - `repository.update_sessions_status_with_history()`: 호출하지 않아야 한다
- **검증:**
  - `update_sessions_status_with_history` 를 호출하지 않는다
- **분류**: `edge-case`

---

### SC-PS-005: 여러 session 일괄 처리

- **목적**: 여러 session 을 한 번에 처리하는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - 반환: `[SessionInfo(s1, CREATING), SessionInfo(s2, CREATING), SessionInfo(s3, CREATING)]`
- **입력:**
  - `spec`: promote-to-running
- **검증:**
  - session 3개가 모두 RUNNING 으로 전이한다
- **분류**: `happy-path`

---

### SC-PS-006: 자원 그룹 병렬 처리

- **목적**: 여러 자원 그룹을 병렬로 처리하는지 확인한다
- **의존성(mock):**
  - `repository.get_scaling_groups()`: `["sg1", "sg2", "sg3"]` 반환
- **검증:**
  - `search_sessions_for_handler` 를 3회 호출한다
- **분류**: `happy-path`

---

## kernel 매칭 시나리오: repository 통합

### SC-KM-001: NOT_ANY 매칭, pre-prepared 상태 없음 검증

- **목적**: NOT_ANY(pre_prepared) 가 올바르게 필터링하는지 확인한다
- **입력:**
  - `spec`: promote-to-prepared
  - DB session:
    - `s1`: kernel 2개, PREPARED, RUNNING → 포함(pre-prepared 없음)
    - `s2`: kernel 2개, PREPARED, PULLING → 제외(PULLING 은 pre-prepared)
    - `s3`: kernel 2개, RUNNING, TERMINATED → 포함(pre-prepared 없음)
- **검증:**
  - 조회 결과: `[s1, s3]`
  - PULLING kernel 때문에 `s2` 를 제외한다
- **분류**: `happy-path`
- **참고**: repository 단위 테스트

---

### SC-KM-002: NOT_ANY 매칭, terminal 상태 허용

- **목적**: NOT_ANY 가 terminal 상태를 허용하는지 확인한다
- **입력:**
  - `spec`: promote-to-running
  - DB session:
    - `s1`: kernel 2개, RUNNING, RUNNING → 포함
    - `s2`: kernel 2개, RUNNING, TERMINATED → 포함(부분 실패 허용)
    - `s3`: kernel 2개, RUNNING, CREATING → 제외(CREATING 은 pre-running)
- **검증:**
  - 조회 결과: `[s1, s2]`
  - 일부 kernel 이 TERMINATED 이어도 `s2` 를 포함한다(부분 실패 허용)
- **분류**: `happy-path`

---

### SC-KM-003: ANY 매칭, TERMINATED 감지

- **목적**: ANY(TERMINATED) 가 일부 kernel 의 종료를 감지하는지 확인한다
- **입력:**
  - `spec`: detect-termination
  - DB session:
    - `s1`: kernel 3개, RUNNING, RUNNING, TERMINATED → 포함(TERMINATED 1개)
    - `s2`: kernel 2개, RUNNING, RUNNING → 제외(TERMINATED 없음)
    - `s3`: kernel 2개, TERMINATED, TERMINATED → 포함(TERMINATED 2개)
- **검증:**
  - 조회 결과: `[s1, s3]`
  - TERMINATED kernel 이 없어 `s2` 를 제외한다
- **분류**: `happy-path`

---

### SC-KM-004: ALL 매칭, 모든 kernel 이 TERMINATED 이어야 함

- **목적**: ALL(TERMINATED) 가 완전한 종료에만 일치하는지 확인한다
- **입력:**
  - `spec`: promote-to-terminated
  - DB session:
    - `s1`: kernel 2개, TERMINATED, TERMINATED → 포함
    - `s2`: kernel 2개, TERMINATED, TERMINATING → 제외(하나는 아직 TERMINATING)
- **검증:**
  - 조회 결과: `[s1]`
- **분류**: `happy-path`

---

## hook 실행 시나리오

### SC-PH-001: RUNNING 상태 hook 실행

- **목적**: RUNNING 전이에서 hook 을 실행하는지 확인한다
- **의존성(mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`: Hook 반환
  - `hook.execute()`: `HookResult(successes=[s1])` 반환
- **검증:**
  - `get_hook(RUNNING)` 을 호출한다
  - `hook.execute()` 를 호출한다
- **분류**: `happy-path`

---

### SC-PH-002: hook 실패가 session 을 제외

- **목적**: hook 이 실패한 session 을 상태 전이에서 제외하는지 확인한다
- **의존성(mock):**
  - `hook.execute()`: `HookResult(successes=[s1], failures=[s2])` 반환
- **검증:**
  - `s1` 만 RUNNING 으로 전이한다
  - `s2` 는 전이하지 않는다
- **분류**: `error-case`

---

### SC-PH-003: 등록된 hook 없음, session 통과

- **목적**: 등록된 hook 이 없으면 session 이 그대로 통과하는지 확인한다
- **의존성(mock):**
  - `hook_registry.get_hook(SessionStatus.PREPARED)`: `None` 반환
- **검증:**
  - hook 조회만 수행하고, 실행 없이 상태 전이를 진행한다
- **분류**: `happy-path`

---

## 이력 기록 시나리오

### SC-HR-001: Phase/Step 기록 검증

- **목적**: 승격 처리 중 Phase 와 Step 을 기록하는지 확인한다
- **의존성(mock):**
  - `repository.search_sessions_for_handler()`: `[SessionInfo(s1)]` 반환
- **검증:**
  - `pool.build_all_records()` 호출 결과:
    - Phase: `spec.name`, 예: "promote-to-prepared"
    - Phase 상세: "Promoting to {success_status}"
    - Step: `"check_kernel_status"`
    - Step 상세: "All kernels ready for {success_status}"
- **분류**: `happy-path`

---

## PostProcessor 실행 시나리오

### SC-PP-001: 상태 전이 후 PostProcessor 실행

- **목적**: 상태 전이가 성공한 뒤 PostProcessor 를 실행하는지 확인한다
- **의존성(mock):**
  - `scheduling_controller.mark_next_schedule_needed()`: 호출 여부 검증
  - `valkey_schedule.invalidate_schedule_result_cache()`: 호출 여부 검증
- **검증:**
  - 다음 schedule type 을 표시한다
  - schedule 결과 cache 를 무효화한다
- **분류**: `happy-path`

---

### SC-PP-002: 전이가 없으면 PostProcessor 생략

- **목적**: 상태 전이가 없을 때 PostProcessor 를 실행하지 않는지 확인한다
- **검증:**
  - `mark_next_schedule_needed` 를 호출하지 않는다
- **분류**: `edge-case`

---

## spec 정의 검증 시나리오

### SC-SD-001: factory PromotionSpec 정의 검증

- **목적**: `_create_promotion_specs()` 가 올바른 spec 을 반환하는지 확인한다
- **실행:** `specs = _create_promotion_specs()`
- **검증:**
  - 4개 ScheduleType 에 대한 spec 을 정의한다
  - spec 마다 field 값을 검증한다:
    - CHECK_PULLING_PROGRESS:
      - `target_kernel_statuses` == `list(KernelStatus.pre_prepared_statuses())`
      - `kernel_match_type` == `NOT_ANY`
    - CHECK_CREATING_PROGRESS:
      - `target_kernel_statuses` == `list(KernelStatus.pre_running_statuses())`
      - `kernel_match_type` == `NOT_ANY`
    - CHECK_TERMINATING_PROGRESS:
      - `target_kernel_statuses` == `[TERMINATED]`
      - `kernel_match_type` == `ALL`
    - DETECT_KERNEL_TERMINATION:
      - `target_kernel_statuses` == `[TERMINATED]`
      - `kernel_match_type` == `ANY`
- **분류**: `happy-path`

---

## 테스트 커버리지 요약

| 분류 | happy-path | edge-case | error-case | 합계 |
|----------|------------|-----------|------------|-------|
| sokovan coordinator 처리 | SC-PS-001~006 | SC-PS-004 | - | 6 |
| kernel 매칭 | SC-KM-001~004 | - | - | 4 |
| hook 실행 | SC-PH-001, SC-PH-003 | - | SC-PH-002 | 3 |
| 이력 기록 | SC-HR-001 | - | - | 1 |
| PostProcessor | SC-PP-001 | SC-PP-002 | - | 2 |
| spec 정의 | SC-SD-001 | - | - | 1 |
| **합계** | **13** | **2** | **1** | **17** |

### 주요 검증 지점

1. **kernel 매칭 의미**: NOT_ANY, ANY, ALL 이 올바르게 동작하는지 확인한다
2. **terminal 상태 처리**: 부분 실패를 허용한다(일부 kernel 이 TERMINATED)
3. **조기 감지**: kernel 하나라도 TERMINATED 이면 ANY 가 즉시 감지한다
4. **이력 기록**: Phase 와 Step 을 올바르게 기록하는지 확인한다
5. **hook 실행**: 상태별 hook 호출과 실패 처리를 확인한다

### PromotionSpec 방식의 장점

- **선언형 정의**: 상태 전이 로직을 spec 에 명확히 정의한다
- **중복 제거**: 4개 handler 에 있던 동일한 변환 로직을 제거했다
- **테스트 단순화**: handler 별 테스트 대신 sokovan coordinator 수준 통합 테스트로 충분하다
- **유지보수성**: spec 정의 변경만으로 동작을 조정한다
- **상태 묶음 중앙화**: KernelStatus class method 로 상태 묶음을 관리한다
