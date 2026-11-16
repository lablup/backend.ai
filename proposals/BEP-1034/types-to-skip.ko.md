# KernelV2 GQL - 건너뛸 타입

이 타입들은 **구현하지 않는다**. 다른 설계로 대체하기로 정했다.

---

## 요약

| 타입 | 위치 | 이유 |
|------|----------|--------|
| `SchedulerPredicateGQL` | `common/types.py` | 새 scheduler 설계로 대체 |
| `SchedulerInfoGQL` | `common/types.py` | 새 scheduler 설계로 대체 |
| `KernelStatusHistoryEntryGQL` | `kernel/types.py` | 새 상태 추적 설계로 대체 |
| `KernelStatusHistoryGQL` | `kernel/types.py` | 새 상태 추적 설계로 대체 |
| `VFolderMountGQL` | `common/types.py` | `VFolderNode` 연결로 대체 |

---

## Scheduler 타입

### SchedulerPredicateGQL

**동작**: 구현하지 않는다. 새 scheduler 설계로 대체한다.

### SchedulerInfoGQL

**동작**: 구현하지 않는다. 새 scheduler 설계로 대체한다.

---

## 상태 이력 타입

### KernelStatusHistoryEntryGQL

**동작**: 구현하지 않는다. 상태 이력 설계는 다시 검토한다.

### KernelStatusHistoryGQL

**동작**: 구현하지 않는다. 상태 이력 설계는 다시 검토한다.

---

## VFolder 타입

### VFolderMountGQL

**동작**: 구현하지 않는다. `KernelV2GQL` 의 `VFolderNode` 연결로 대체한다.

---

## 영향을 받는 상위 타입

건너뛴 타입 참조를 제거하려면 다음 타입을 수정해야 한다.

### KernelLifecycleInfoGQL

`status_history`, `status_info`, `status_data`, `status_changed` 필드를 제거한다.
