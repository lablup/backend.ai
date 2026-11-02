# Agent 커널 수명 주기 구조화

## 관련 이슈

- Epic **BA-6074**, 이 BEP **BA-6687**
- 하위: **BA-6075**(task 관리 구조), **BA-6077**(create 단계), **BA-6078**(prepare 단계), **BA-6079**(terminate 단계)
- 상위(참조만 하고 펼치지 않는다): **[BEP-1002](BEP-1002-agent-architecture.md)**(runner/Provisioner/Stage), **[BEP-1057](BEP-1057-agent-re-architecture.md)**(agent 재설계, ComputeBackend, LifecycleService)
- 패턴 참조: **[BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md)**(sokovan 상태 전이), `kernel_scheduling_history`

## 1. 목표

Agent 의 명령형 커널 수명 주기(지금은 `agent.py` 의 `create_kernel` 안에 인라인으로 있다)를 세 축으로 구조화한다.

| 축 | 내용 |
|---|---|
| 비동기 트리거 계약 | 오래 걸리는 트리거는 ack 를 즉시 반환하고, 진행, 완료, 실패는 event 로만 전달한다 |
| 실행과 event 분리 | 단계 handler 는 동작을 실행하고 응답만 반환한다. 전이 event 발행은 별도 계층이다 |
| 통합 전이 event | 가벼운 `(from, to)` event 하나가 Manager 의 커널 이력 기록과 상태 전이를 함께 이끈다 |

**핵심 재정의:** 권위 있는 커널 상태 **기계는 Manager sokovan 에만 둔다.** Agent 는 그 권위를 갖지 않고 자기 실행 단계를 추적하며 전이를 *보고*한다. 전이 검증, retry, timeout, reschedule 은 sokovan 의 책임이다. 이렇게 Epic 의 "agent 상태 기계 handler" 구도를 다듬는다.

**경계:** 커널 내부 자원 준비와 정리 순서는 BEP-1002, instance 프리미티브는 BEP-1057, 상태 권위는 sokovan 에 속한다. 이 BEP 는 그 위의 조정이다(비동기 실행 구조화 + 전이 event).

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 있음 / ➕ 추가할 것**.

### 2.1 수명 주기 실행 (prepare / create / terminate)

| | 항목 |
|---|---|
| ✅ | `create_kernel`(agent.py:2528)이 pull, 자원, scratch, container 를 인라인으로 동기 실행한다. 추상 `prepare_*`/`start_container`/`destroy_kernel`/`clean_kernel` |
| ✅ | `stage/kernel_lifecycle/docker/` 에 자원별 `Provisioner`/`Stage` 초안이 있다(`common/stage/types.py` 기반). 그러나 **실행 경로에 연결되지 않았다.** 이를 순서대로 실행하는 runner/DAG 가 없다 |
| ✅ | `compute_backend/` 의 `ComputeBackend`/`ComputeInstance`(BEP-1057 1단계 진행 중) |
| ➕ | 단계를 순서대로 실행하고 응답을 반환하는 Prepare/Create/Terminate handler (3.b) |

### 2.2 상태 표현 / 전이 event

| | 항목 |
|---|---|
| ✅ | 비공식 `KernelLifecycleStatus{PREPARING,RUNNING,TERMINATING}`(가변 속성) + `LifecycleEvent` IntEnum + `container_lifecycle_queue`(정식 상태 기계가 아니다) |
| ✅ | 세분화된 `Kernel*AnycastEvent`(Preparing/Pulling/Creating/Started/Terminating/Terminated, 상태를 이끈다, anycast = at-least-once) + `Kernel*BroadcastEvent`(UI/스트리밍) |
| ✅ | 커널 상태 기계와 retry/reschedule 은 Manager sokovan 에 있다(`ScheduleCoordinator.handle_kernel_running -> mark_kernel_running`) |
| ➕ | 세분화된 anycast 수명 주기 event 를 대체하는 가벼운 통합 `KernelStatusTransitionAnycastEvent(kernel_id, from, to, reason)` (3.c, 3.d) |

### 2.3 이력 저장

| | 항목 |
|---|---|
| ✅ | `KernelRow.status_history`(JSONB, status -> timestamp) |
| ✅ | `kernel_scheduling_history` 테이블: `kernel_id, phase, from_status, to_status, result, error_code, message, attempts, sub_steps`. sokovan 이 자기 스케줄링 단계 기록에 사용한다 |
| ➕ | Agent 가 보고한 전이를 **`kernel_scheduling_history`** 에 기록한다(새 저장소 없음, 3.e) |

### 2.4 task 관리 / 비동기 트리거

| | 항목 |
|---|---|
| ✅ | `tasks/` 의 `PeriodicTask`/`LocalCron`(`SyncContainerLifecyclesTask` 등), `kernel_registry/` 의 container label 로더와 기록기(pickle 을 사용하지 않는 복구 경로) |
| ✅ | 지금 create 는 동기 경로이고, 오래 걸리는 동작을 호출자가 끝날 때까지 기다린다 |
| ➕ | 비동기 트리거 진입점 + executor + 별도 전이 event 계층 (3.a, 3.c) |

## 3. 구현 설계

### (a) 비동기 트리거 계약 (강한 규칙)

모든 수명 주기 트리거(prepare/create/terminate)는 같은 계약을 따른다.

1. 진입점(RPC/HTTP)이 요청을 검증하고 작업을 대기열에 추가한다.
2. **ack(Accepted) 를 즉시 반환한다.** 동작이 끝날 때까지 기다리지 않는다.
3. 진행, 완료, 실패는 event 로만 Manager 에 전달한다.

이 계약은 오늘의 `container_lifecycle_queue` 를 보편적인 진입 계약으로 일반화하고 동기 `create_kernel` 경로를 없앤다. BEP-1057 2단계(HTTP 진입)와 맞물린다. HTTP route 가 ack 를 반환하고 executor 가 작업을 실행한다.

```
Manager --trigger--> Agent entry (validate, enqueue, return ack)
                          |
                    [async] Executor -> stage handler (prepare/create/terminate)
                          |  returns response (result)
                          v
                    Transition-event layer (separate): update local phase -> emit transition event
                          |
                    anycast --> Manager (record kernel history + apply from -> to)
```

### (b) 실행 계층 — 단계 handler (BA-6077/78/79)

handler 는 커널 수명 주기의 실행 단위다. 각자 BEP-1002 의 `Provisioner`/`Stage` 를 받아 사용하고 BEP-1057 의 `ComputeBackend` 를 호출해 동작을 수행하며, **응답만 반환한다**(event 를 발행하지 않는다). retry 는 맡지 않는다. 실패하면 확보한 자원을 역순으로 정리하고 실패 응답을 반환하며, reschedule 은 sokovan 이 정한다. sokovan 의 "handler 하나 = 파일 하나" 규칙을 따른다.

| handler | 로컬 단계 전이 | 내부 작업(agent 로컬) | Story |
|---|---|---|---|
| PrepareHandler | `-> PREPARING`, `PREPARING -> PULLING` | pull_image, prepare_scratch, prepare_resource, prepare_network, prepare_mounts | BA-6078 |
| CreateHandler | `-> CREATING`, `CREATING -> RUNNING` | create_container, start_container | BA-6077 |
| TerminateHandler | `-> TERMINATING`, `TERMINATING -> TERMINATED` | stop_container, cleanup_scratch, release_resources | BA-6079 |

- `from`/`to` 는 sokovan `KernelStatus` 값을 사용하므로 발행한 전이가 sokovan 상태 기계에 그대로 매핑된다.
- **내부 작업은 agent 로컬이다(로컬 로깅, 지표).** event 에 싣지 않는다. Manager 에는 상태 전이만 보고한다.
- 실패하면 로컬 정리 뒤에 **agent 처리 실패를 보고한다**(전이 event `result=FAILED` + `error_code`/`message`). **CANCELLED/reschedule 은 커널 이력의 관심사가 아니라 sokovan 세션 스케줄링에 속한다.** Agent 는 CANCELLED 전이를 발행하지 않는다.
- handler 는 같은 커널에 다시 실행해도 안전해야 한다(조정 sweep 이나 Manager 재트리거가 다시 호출할 수 있다). 정리 단계는 멱등이고, 생성 단계는 kernel-id 상관 키로 기존 instance 를 찾아낸다(BEP-1057).

### (c) 전이 event 계층 (별도, BA-6075)

실행과 분리된 계층이다. handler 응답을 받아 (1) 로컬 단계를 `from -> to` 로 진행하고, (2) 통합 전이 event 를 발행한다. 수명 주기 전이의 Agent 에서 Manager 로 가는 유일한 출구다. 로컬 단계는 권위 있는 상태가 아니라 진행 추적이다(단계 순서 정하기, 중복 작업 피하기, 전이의 `from` 채우기).

### (d) 통합 전이 event

세분화된 anycast 수명 주기 event 를 가벼운 타입 하나로 대체한다. **단계/step payload 를 싣지 않는다.** 전이와 그 처리 결과만 담는다.

| 필드 | 의미 |
|---|---|
| `kernel_id` | 대상 커널 |
| `from_status` | 전이 전 `KernelStatus`(Agent 의 로컬 단계) |
| `to_status` | 전이 뒤 시도한 `KernelStatus` |
| `reason` | 전이 사유(기존 `KernelLifecycleEventReason`) |
| `result` | Agent 처리 결과: `SUCCESS` / `FAILED` |
| `error_code`, `message` | 실패 상세(성공이면 비어 있다) |

- Agent 는 `SUCCESS`/`FAILED` 만 보고한다. 실패의 retry/timeout/give_up 분류는 sokovan 이 정한다(handler 가 성공/실패를 반환하고 sokovan coordinator 가 분류하는 모델과 같다).
- Manager 는 세분화 event 마다 handler 를 두는 대신 `from -> to` 를 일반적으로 적용한다(sokovan 의 선언적 전이 모델과 같다).
- `from_status` 덕분에 Manager 는 중복되거나 오래된 전이를 멱등하게 거부할 수 있다.
- **세분화 broadcast event 는 유지한다.** UI/스트리밍이 단계별 타입 payload 에 의존한다. (앞으로는 anycast 만 발행하고 그것에서 broadcast 를 파생하는 방향이다. 이 BEP 범위 밖이다.)

### (e) Manager 기록 / 적용 계약

`KernelStatusTransitionAnycastEvent` 를 받으면:

1. **이력 기록:** 전이를 `kernel_scheduling_history` 에 기록한다. Agent 의 `KernelStatus` 전이와 처리 결과를 테이블의 phase/from_status/to_status/result/error_code/message column 에 매핑한다. **새 저장소를 생성하지 않는다.** `sub_steps` 는 sokovan 자기 단계용이고 Agent 는 채우지 않는다.
2. **상태 적용:** sokovan 의 전이 검증을 따르며 `from -> to` 를 적용한다. retry/timeout/reschedule 은 sokovan 에 남는다.

기존에 세분화 event 로 커널 상태를 변경하던 소비자는 단일 전이 handler 로 옮긴다.

### (f) 재시작 독립성

Agent 재시작은 **커널 수명 주기와 커널 이력에 영향을 주지 않는다.** 재시작하면 로컬 단계를 `kernel_registry` 의 container label 에서 복원하지만, 이는 구동용일 뿐이다. 재시작 자체는 event 를 발행하지 않고 이력도 건드리지 않는다. 실제 상태 변화(예: container 가 실제로 사라짐)는 조정 sweep(3.g)이 재시작과 무관하게 감지해 정상 전이 event 로 보고한다. pickle 은 배제한다.

### (g) 전달 보장

"전이마다 event 를 발행한다"는 보장은 새 ack 프로토콜이 아니라 계층으로 마련한다.

1. **구조적 발행:** 전이 event 계층이 handler 응답을 받은 뒤 건너뛸 수 없는 단계로 전이 event 를 발행한다. event 를 발행하지 않고 전이를 적용하는 일은 없다.
2. **at-least-once 전송:** anycast 는 consumer group 을 사용하는 Redis Stream 이다(ack + re-claim).
3. **수렴:** 주기 조정 sweep(`SyncContainerLifecyclesTask` 확장)이 실제 container 상태에서 다시 도출하고 Manager 가 놓쳤을 수 있는 전이를 다시 발행한다. Manager 는 `from_status` 로 멱등하게 적용하므로 다시 발행해도 안전하다. (heartbeat digest 는 두지 않는다.)

이는 sokovan 의 보장 모델(이력 기록 + at-least-once event + sweep 수렴)과 같다. exactly-once 는 아니다.

## 4. 결정 요약

| 결정 | 내용 |
|---|---|
| 상태 기계 권위 | Manager sokovan 에만 둔다. Agent 는 로컬 단계를 추적하고 전이를 보고한다 |
| 트리거 | ack 를 먼저 비동기로 반환하고, 결과는 event 로 |
| 관심사 분리 | 실행(응답 반환)과 전이 event(별도 계층) |
| 통합 event | 가벼운 `KernelStatusTransitionAnycastEvent(kernel_id, from, to, reason, result, error_code, message)` 가 anycast 수명 주기 event 를 대체한다. 단계/step payload 없음. 세분화 broadcast 는 유지 |
| 이력 저장 | `kernel_scheduling_history` 에 기록한다. 새 저장소 없음 |
| 재시작 | 커널과 이력에 영향 없음. 로컬 단계만 container label 에서 복원한다 |
| 실패/취소 | agent 처리 실패는 전이 `result=FAILED` + error 로 보고한다. CANCELLED/reschedule 은 sokovan 세션 스케줄링에 속한다 |
| retry | Agent 가 맡지 않는다. sokovan 의 give_up/expired → reschedule |
| 전달 보장 | 구조적 발행 + at-least-once + sweep 수렴(heartbeat 없음 / 재시작 event 없음). exactly-once 아님 |
| 경계 | 자원 순서와 정리 = BEP-1002, instance = BEP-1057, 상태 권위 = sokovan |

## 5. 열린 질문

- 조정 sweep 의 범위: `SyncContainerLifecyclesTask` 확장으로 충분한지, 전용 조정 task 가 필요한지에 대한 결정이 필요하다.

## 6. 참고

- [BEP-1002](BEP-1002-agent-architecture.md), [BEP-1057](BEP-1057-agent-re-architecture.md), [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md)
- `src/ai/backend/manager/models/scheduling_history/row.py` — `kernel_scheduling_history` 테이블
- `src/ai/backend/manager/models/kernel/` — `KernelRow.status_history`
- `src/ai/backend/common/events/event_types/kernel/` — 기존 커널 anycast/broadcast event
- `src/ai/backend/agent/AGENTS.md` — event 전용 출구, `stage/` 상태 기계 규칙
