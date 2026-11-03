# 선점 scheduler 동작 원리

## 관련 이슈

- Epic **BA-3056**, 이 BEP **BA-6692**(**BA-3058** 구현을 차단한다)
- **BA-6926** 으로 개정: 선점용 스코프 로컬 `job_priority`(2.4절, 3.a절, 3.b절)
- 상위 명세(동기): **[BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md)** 를 참조하고 다시 서술하지 않는다
- 선행 조건(완료): BA-3057(자원 그룹 설정), BA-4912(`is_preemptible`). 범위 밖: BA-4913(Not Planned)

## 1. 목표

우선순위가 높은 대기 세션이 자원 부족으로 기다릴 때, **이미 실행 중인 우선순위가 낮은 세션을 선점해 용량을 확보한다**. 동기와 상위 명세는 BEP-1014 에 있다.

지금까지 선점은 **데이터, 설정, API 표면만** 있고, **실제로 선점을 수행하는 scheduler 로직이 없다**. 이 BEP 가 그 빠진 부분, 곧 **scheduler 가 선점을 수행하는 방식**을 정의한다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 2.1 API(사용자와 관리자 트리거)

| | 항목 |
|---|---|
| ✅ | 세션 생성 시 사용자가 `priority`(0..100)와 `is_preemptible`(기본 True)을 정한다: `services/session/actions/{create_from_params,enqueue_session}` |
| ✅ | 관리자가 자원 그룹 설정으로 `preemptible_priority`, `order`, `mode` 를 정한다: 자원 그룹 API |
| ➕ | 자원 그룹 설정에 `preemption.enabled`(선점 활성화 값)와 `preemption_min_runtime`(3절의 anti-thrashing 값)을 노출한다 |
| ➕ | 세션 생성 시 사용자가 `job_priority` 도 정한다. 세션의 **스코프 로컬** 선점 우선순위이고 선점에만 사용된다(2.4절 참고). 전역 scheduler `priority` 와 다르다 |
| ➕ | 키페어(사용자) 자원 정책에 `max_priority` 를 추가한다. 사용자가 세션 생성 시 선언할 수 있는 `priority` 의 상한이다(2.4절) |
| ➕ | 자원 그룹 설정에서 관리자 `preemptible_priority` 를 제거한다. victim 을 상대적 `job_priority` 로 고르면 사용되지 않는다(3.b절) |

> 선점은 사용자가 직접 호출하지 않는다. scheduler 가 자동으로 판단하므로 **새 트리거 API 가 없다**.

### 2.2 DB(저장 데이터)

| | 항목 |
|---|---|
| ✅ | `SessionRow.priority`(기본 10), `SessionRow.is_preemptible`(기본 True) |
| ✅ | `ScalingGroupOpts.preemption = PreemptionConfig(preemptible_priority=5, order, mode)`, `PreemptionMode=terminate\|reschedule`, `PreemptionOrder=oldest\|newest`(BEP-1014 의 "suspend" 는 오타다). **활성화 값 field 가 없다** |
| ✅ | `SessionStatus`: PENDING, **DEPRIORITIZING**(재시도 포기 시 자기 priority 를 10 낮추고 다시 PENDING 이 된다), ..., TERMINATING, TERMINATED |
| ➕ | 새 `PreemptionConfig.enabled: bool`: 선점 활성화 값, **기본 False(opt-in)** |
| ➕ | 새 `SessionStatus.PREEMPTED`: 확정된 victim 의 **단일 상태**다. kernel 정리 뒤 모드에 따라 **PENDING(reschedule)이나 TERMINATED(terminate)** 로 분기한다(3.(c)절) |
| ➕ | 새 `preemption_min_runtime` 설정 field(자원 그룹 opts) |
| ➕ | 새 `SessionRow.job_priority`(기본 10): 스코프 로컬 선점 우선순위이고 같은 스코프 소유자 안에서만 비교한다(2.4절, 3.b절) |
| ➕ | 새 키페어 자원 정책 field `max_priority`: 전역 `priority` 의 사용자별 상한(2.4절) |
| ➕ | `PreemptionConfig.preemptible_priority` 제거: victim 을 상대적 `job_priority` 로 고르면 자원 그룹의 절대 임계값은 필요 없다(3.b절) |

### 2.3 Sokovan(scheduler 동작)

| | 항목 |
|---|---|
| ✅ | 스케줄링 loop: `ScheduleCoordinator`(timer, 자원 그룹별) → `ScheduleSessionsLifecycleHandler` → `provisioner.schedule_scaling_group()` |
| ✅ | provisioner: 순서(최상위 우선순위 묶음) → 검증 → agent 선택 → 할당. **자원을 해제하지 않는다** |
| ✅ | 종료: `mark_sessions_terminating()` → 다음 tick 의 `TerminateSessionsLifecycleHandler` → `destroy_kernel`(**비동기**, agent event 로 완료 확인) |
| ✅ | `is_preemptible` 은 **배포 기본값(False)과 자원 그룹 기본값 병합에만** 사용되고, **스케줄링 판단에는 읽지 않는다(핵심 빈틈)** |
| ➕ | 실행 중 세션(agent 별로 묶음)을 snapshot 에 추가한다(3.(a)절) |
| ➕ | 선점 **planner**: 후보 filter 와 victim 선정(3.(b)절) |
| ➕ | **(주입된) controller 가 victim 을 PREEMPTED 로 표시**하고, 새 선점 handler 가 모드(terminate/reschedule)로 분기하며, 여러 tick 에 걸친 진행 중 표시를 둔다(3.(c)절) |

> 종료가 비동기이므로 provisioner 가 동기로 종료할 수 없고, **선점은 본질적으로 여러 tick 에 걸친다**.

### 2.4 우선순위 모델: `priority` 와 `job_priority`

선점은 scheduler `priority` 가 아니라 **새 축 `job_priority`** 로 판단한다. 세 축은 서로 다른 질문에 답하고 서로 다른 단계에 적용된다.

| 축 | 무엇인가 | 정하는 주체 | 단계 | 이 개정 |
|------|------|--------|-------|----------------|
| scheduler `priority`(기존) | 대기 queue 의 시스템 전체 순서 | 사용자, 키페어 정책 `max_priority` 까지 | **먼저: 스케줄링** | 유지하고 선점에서 제외한다 |
| `job_priority`(신규) | 자기 스코프 안에서 **자기 job 사이의** 순위 | 사용자, 세션 생성 시 | **스케줄링 후: 선점** | 도입하고, victim 비교의 **유일한** key 로 사용한다 |
| fair share | 스케줄링 *방식*(sequencer)의 차이 | 없음 | 스케줄링(대안) | **무관하고 건드리지 않는다** |

**적용 방식은 다음과 같다.** scheduler 가 queue 를 `priority` 로 먼저 정렬한다. 맨 앞 대기 세션을 배치할 수 없으면 선점이 **그 소유자 자신의** 실행 중 세션 중 `job_priority` 가 더 낮은 것을 축출한다. "내 급한 job 이 내 background job 을 밀어낸다"는 뜻이다. 다른 소유자의 세션은 비교에 들어가지 않는다.

**`job_priority` 의 범위:**

| 스코프 | 소유자 key | v1 |
|-------|-----------|----|
| 사용자 | `session.user_uuid` | ✅ victim 을 대기 세션의 `user_uuid` 로 제한한다 |
| 프로젝트 | `session.group_id` | ➖ **미래**: "프로젝트 세션"(사용자가 아니라 프로젝트에 속한 세션) 개념이 필요하다 |

`job_priority` 값은 **한 소유자 안에서만 비교 가능**하고 전역 의미가 없다. v1 은 소유자 key 를 `user_uuid` 로 고정한다. 더 넓은 스코프는 같은 column 을 재사용하고 비교에 사용하는 소유자 key 만 변경한다.

> 키페어 자원 정책 `max_priority` 는 사용자가 세션 생성 시 선언하는 전역 `priority` 를 제한한다. `job_priority` 는 사용자 자신의 job 순서만 변경하므로 그런 상한이 필요 없다.

> **주의: v1 의 소유자 내 규칙과 BEP-1014 의 동기.** BEP-1014 의 원래 동인은 *tenant 간* 선점이었다(공유 cluster 에서 *다른* 소유자의 우선순위 낮은 작업을 축출하는 것). v1 은 victim 을 **같은 사용자**로 제한하므로 실제로 여는 사례는 좁고 안전한 하나다. "내 급한 job 이 내 background job 을 선점한다"이다. 의도했다. tenant 간 선점은 누가 누구의 작업을 축출할 수 있는지에 대한 정책이 필요하고, 그 정책은 사용자가 선언한 `job_priority` 가 아니라 **관리자가 관리하는 스코프 간 축**에 기대야 한다. 따라서 tenant 간 선점은 열린 질문의 미래 축으로 남긴다.

## 3. 구현 설계

**핵심 흐름:** 대기 세션 배치 실패 → **planner 가 victim 선정** → **controller 가 PREEMPTED 로 표시하고 모드로 분기** → (다음 tick) 자원이 확보되면 평소 할당이 대기 세션을 배치한다.

### (a) 데이터 계층: snapshot 의 실행 중 세션

할당이 agent 별로 이뤄지므로, 실행 중 세션의 **선점 관련 데이터를 agent 별로 묶어** snapshot 에 추가한다.

- `job_priority`(victim 비교 key), `user_uuid`(같은 소유자 filter 의 스코프 소유자 key. 프로젝트 스코프가 열리면 `group_id` 추가), is_preemptible, 점유 slot, agent binding, 생성 시각(`order` 와 최소 실행 시간용), cluster_mode(다중 node victim 처리용), session_type 과 private flag(후보 제외).
- repository 가 `RUNNING` 세션을 agent 별 점유 slot 과 함께 가져온다. 정확한 타입과 field signature 는 구현 세부다.

### (b) Provisioner: 선점 planner(읽기와 제안)

할당에 실패하면 provisioner 가 planner 를 호출한다. planner 는 **읽고 제안만** 한다. 실제 축출은 controller 가 시작한다(provisioner 는 자원을 해제하지 않는 채로 남는다). victim 결정은 `ScheduleResult` 로 반환한다.

**victim 후보 조건**(모두 AND):

| 조건 | 비고 |
|-----------|------|
| `status == RUNNING` | PREEMPTED/TERMINATING 을 제외해 진행 중인 victim 을 다시 고르지 않는다 |
| `is_preemptible` 이고 private/SFTP 가 아님 | 세션별 opt-out 과 인프라 세션을 제외한다 |
| `victim.user_uuid == pending.user_uuid` | **같은 스코프 소유자(v1 은 사용자 스코프). `job_priority` 는 한 소유자 안에서만 비교한다** |
| `victim.job_priority < pending.job_priority`(엄격) | **전역 `priority` 가 아니라 스코프 로컬 `job_priority` 로 선점한다. 같은 `job_priority` 는 절대 선점하지 않는다** |
| `now - started_at >= preemption_min_runtime` | anti-thrashing. **기본 0(비활성)** |

**victim 선정**(agent 별):
- 대기 세션을 배치할 수 있는 agent 에서 **`job_priority` 오름차순, 다음으로 설정한 `order` 전략**으로 victim 을 고른다. `oldest`/`newest` 는 시작 시각으로 동률을 깨고, `fewest-sessions`/`smallest-resources` 는 대기 세션의 부족분을 고려해 고른다. `preemption_order` 는 유지한다(`preemptible_priority` 임계값만 제거한다).
- **완전히 만족할 때만** 선점한다. `free(A) + sum(victim slots) >= requested` 이고, 부분 선점은 하지 않는다(낭비되는 종료와 livelock 을 피한다).
- **v1 트리거는 단일 node 대기 세션뿐이다.** 다중 node victim 은 허용하지만 **모든 kernel 에 걸쳐 원자적으로** 축출한다(부분 gang 선점 없음). 다중 node(agent 간) 트리거는 범위 밖이다.
- 한 tick 안에서 선정한 victim 집합을 유지해 한 세션이 대기 세션 둘에 두 번 계산되지 않게 한다.

### (c) 축출: controller 가 PREEMPTED 로 표시한 뒤 모드로 분기

스케줄 pass(handler)는 **판단하고 제안만** 한다. victim 을 직접 변경하지 않는다(대상이 PENDING 이라 부수 효과를 최소로 유지한다). victim 결정(`ScheduleResult`)을 받으면 **주입된 `scheduling_controller` 가 victim 을 공통 `PREEMPTED` 상태로 표시**하고(event 브로드캐스트와 다음 tick 스케줄 pass 요청을 함께 한다), 사용자 요청 종료가 `mark_sessions_for_termination` 으로 사용하는 것과 같은 controller 진입 방식을 따른다.

그다음 **`PREEMPTED` 를 대상으로 하는 새 선점 lifecycle handler 가 kernel 을 정리하고 `preemption.mode` 로 목적지를 정한다.**

- **terminate**: 기존 종료 경로로 전달해 `TERMINATED` 로 간다. 이유는 `PREEMPTED_BY_SCHEDULER` 다.
- **reschedule**: **같은 세션을 `PENDING` 으로 다시 대기열에 넣는다**(session id, config, priority, `job_priority` 유지, Slurm REQUEUE). 체크포인트를 사용하는 batch 작업에 맞는다. **interactive 세션은 container 안 상태를 잃는다(받아들이고 문서화한다).**

```
victim selected -> PREEMPTED (kernel cleanup)
  ├ [terminate]  -> TERMINATED
  └ [reschedule] -> PENDING   (priority preserved, re-competes)
```

별도 `RESCHEDULING` 상태는 없다. `PREEMPTED` 가 kernel 정리 단계를 포괄하고, **최종 목적지(PENDING/TERMINATED)만 모드에 따라 다르다.** 이렇게 "선점 결정"과 "모드별 실행"을 분리한다.

**여러 tick:** PREEMPTED 인 victim(또는 뒤따르는 TERMINATING)은 후보 집합에서 빠지므로 다시 골라지지 않는다. 아직 기다리는 대기 세션이 *다른* 세션을 선점하지 않게 **진행 중 표시**로 재트리거를 차단한다(자원이 확보되거나 timeout 이 될 때까지). 확보된 자원을 강하게 예약하지는 않는다. pass 는 sequencer 의 최상위 우선순위 우선 정렬에 기댄다(약한 보장).

## 결정 요약

| 결정 | 내용 |
|----------|---------|
| 활성화 값 | 새 자원 그룹 `PreemptionConfig.enabled`, 기본 False(opt-in). 비활성화하면 선점하지 않는다 |
| 트리거 | 평소 할당에 실패하고 선점이 활성화되어 있으며 완전히 만족하는 victim 집합이 있을 때 선점한다 |
| 축출 경로 | 스케줄 pass 는 제안만 하고, **(주입된) controller 가 victim 을 `PREEMPTED` 로 표시**하며, 새 선점 handler 가 모드로 분기한다 |
| 상태 모델 | 새 상태 `PREEMPTED` 하나 → terminate: TERMINATED / reschedule: PENDING(REQUEUE, id 와 priority, `job_priority` 유지). 별도 RESCHEDULING 없음 |
| 선점 축 | 전역 scheduler `priority` 가 아니라 새 **`job_priority`**(스코프 로컬)로 선점한다. victim 은 같은 소유자 안에서 상대 비교로 고른다 |
| 우선순위 스코프 | v1 은 사용자 스코프뿐(`victim.user_uuid == pending.user_uuid`). 프로젝트 스코프는 미래다("프로젝트 세션" 필요) |
| 설정 변경 | 자원 그룹 `preemptible_priority` 를 제거한다(절대 임계값이 필요 없다). `preemption_order` 는 유지하고 `oldest\|newest\|fewest-sessions\|smallest-resources` 로 넓힌다(BA-6748). 뒤의 둘은 대기 세션의 부족분을 고려해 victim 을 고른다 |
| 우선순위 상한 | 키페어 자원 정책 `max_priority` 가 사용자가 선언하는 전역 `priority` 를 제한한다. `job_priority` 는 상한이 필요 없다(자기 스코프) |
| 범위 | v1 단일 node 트리거와 다중 node victim 원자 축출. 부분 선점 없음 |
| anti-thrashing | 완전 만족 시에만 선점하고, 같은 `job_priority` 는 절대 선점하지 않으며, `preemption_min_runtime`(기본 0)을 사용한다. Slurm 의 `PreemptExemptTime` 도 설정하지 않으면 예외가 없다(-1 은 0 과 같다) |
| pipeline | provisioner planner(읽기와 제안) + controller 가 축출 시작 |
| 범위 밖 | BA-4913 의 넓은 자원 정책 priority 검증(Not Planned). 전역 `priority` 에 대한 키페어 `max_priority` 상한만 범위 안이다(2.4절) |

## 열린 질문

- tenant 간(스코프 간) 선점: v1 의 같은 소유자 규칙은 *다른* 소유자의 세션을 축출할 수 없다. 다른 tenant 의 우선순위 낮은 작업을 축출하는 일은 별도의 **관리자 관리 스코프 간(프로젝트) 축**에 속하고, "프로젝트 세션" 개념에 달려 있으며, 사용자가 선언한 `job_priority` 와 섞으면 안 된다.
- 다중 node(agent 간) 트리거 선점: v1 범위 밖이고 후속 BEP/Epic 이다.
- 확보된 자원의 강한 예약(v1 은 약함): 필요성은 후속에서 정한다.

## 참고

- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md): 상위 동기와 명세
- 선례: Slurm(REQUEUE, PreemptExemptTime), Kubernetes(Pod 선점, node 단위), Volcano/Kueue(gang)
