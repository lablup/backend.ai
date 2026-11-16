# Agent↔자원 그룹 등록: Manager DB 를 기준으로

## 관련 이슈

- Epic **BA-6800**, 이 BEP **BA-6801**
- 진행 중인 `scaling_group` 이름 → `resource_group_id` migration 과 일관성을 유지해야 한다: BA-6706, BA-6780, BA-6050/6051, BA-6644/6710/6713
- 배경: 운영 스케줄링 장애(배포 시점에 자원 그룹 가정이 깨진 agent 에 session 이 계속 묶여 있었다)

## 1. 목표

**agent 의 자원 그룹 소속에 대한 기준을 로컬 설정에서 manager DB 로 옮긴다.**

지금은 agent 의 로컬 `scaling-group` 설정이 사실상 기준이다. agent 는 agent heartbeat 마다 `scaling_group` 을 보고하고, manager 의 upsert 가 **매** beat 마다 `agents.scaling_group` / `agents.resource_group_id` 를 다시 기록한다(`ON CONFLICT DO UPDATE`). 그래서 오래된 설정이나 기본 설정으로 부팅한 agent 는 다음 heartbeat 에서 **조용히 자신을 잘못된 자원 그룹으로 옮기고**, 그 위에서 실행 중인 session 을 고아로 만든다. 그룹 변경 시 조정, 정리, reschedule 이 없다.

이 BEP 는 세 가지를 정한다.

1. heartbeat 가 그룹을 다시 기록하지 않게 하고 DB 를 기준으로 삼는다(설정은 최초 등록 seed 일 뿐이다).
2. 보상 부채인 manager→agent RPC push(`agent.toml` 재작성)를 제거한다.
3. 의도적인 그룹 변경에 실제 orchestration 경로(session 정리)를 준다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 2.1 Agent (heartbeat 보고)

| | 항목 |
|---|---|
| ✅ | agent heartbeat 마다 `AgentInfo` 에 로컬 설정 값(`self.local_config.agent.scaling_group`)을 보낸다. `agent/agent.py:1277` |
| ➕ | agent 설정에서 `scaling-group` 을 제거하고 새 `initial_resource_group_name`(최초 등록 seed 전용)으로 교체한다. agent 는 계속 보고하지만(호환), 보고 값이 더 이상 DB 그룹을 변경하지 않는다 |

### 2.2 Manager: heartbeat 의 DB 기록

| | 항목 |
|---|---|
| ✅ | upsert 가 beat 마다 `scaling_group`(string)과 `resource_group_id`(FK)를 다시 기록한다. `scaling_group` 은 `insert_fields` 와 `update_fields` **양쪽**에 있다. `repositories/agent/db_source/db_source.py:106-133`, `data/agent/types.py:127,147` |
| ✅ | `from_state_comparison` 이 그룹 변경 시 `need_resource_slot_update=True` 를 지정한다. `data/agent/types.py:206` |
| ➕ | heartbeat 는 **agent 의 상태와 자원만** 변경하고 그룹은 절대 변경하지 않도록 제한한다. `update_fields` 에서 `scaling_group`/`resource_group_id` 를 제거하고 `insert_fields`(최초 등록 seed)에는 남긴다 |
| ➕ | `scaling_groups.is_default` 를 추가한다(기본값은 최대 하나, partial unique index). 최초 등록 해석에서 설정 이름이 null 이거나 해석되지 않으면 기본 그룹으로 fallback 한다(명시한 이름이 해석되지 않으면 warning 을 기록한다) |

### 2.3 API: 그룹 변경 (superadmin)

| | 항목 |
|---|---|
| ✅ | `ModifyAgent`(gql_legacy)가 두 column 을 기록하고 `registry.update_scaling_group` RPC push 도 한다. session 정리, reschedule, 유휴 검사는 **없다**. 죽은 agent 에도 RPC 를 건너뛰지 않는다는 TODO 가 있다. `api/gql_legacy/agent.py:906-930` |
| ✅ | `registry.update_scaling_group` 은 agent 의 `agent.toml`(+`.bak`)과 in-memory 설정을 재작성하는 RPC 다. 호출자는 `ModifyAgent` 하나다. `registry.py:1395`, `agent/server.py:630`, `agent/agent.py:1569` |
| ➕ | 충돌 session 정리를 **service 계층 경로 하나**로 구현한다(parameter: policy enum + `force`). v1/v2 가 공유한다 |
| ➕ | RPC push 를 제거한다. **v1 `ModifyAgent`** 는 service 를 하드코딩 값(`TERMINATE` + `force`)으로 호출하므로 항상 즉시 종료한다 |
| ➕ | **새 v2 API**: policy enum(reschedule/terminate)과 `force` 를 사용자 입력으로 받고 web UI 화면도 제공한다 |

### 2.4 Sokovan: liveness sweep

| | 항목 |
|---|---|
| ✅ | stale kernel sweep 은 kernel 의 **고정된** `resource_group_id` 와 소유 agent 로 범위를 정하고, agent 의 *현재* 그룹은 사용하지 않는다. `sokovan/scheduler/coordinator.py:641`, `terminator/terminator.py:187`, `models/kernel/conditions.py:126` |
| ➕ | 변경 없음. 기준을 뒤집으면 heartbeat 로 생기는 고아를 원천에서 차단하고, 의도적인 이동으로 생긴 고아는 새 API 가 정리한다 (2.3 API: 그룹 변경) |

### 2.5 etcd: sgroup 설정 scope

| | 항목 |
|---|---|
| ✅ | agent 가 로컬 설정으로 `sgroup/<name>` scope prefix 를 만든다. 시작 시 읽기는 기본 MERGED scope 를 사용하므로 sgroup override 가 있으면 global 값 위에 merge 된다. `agent/server.py:1461`, `common/etcd.py:636-672` |
| ✅ | **sgroup scope key 를 기록하는 코드는 없다**(install 은 GLOBAL 만 seed 하고, SGROUP scope 는 unit test 만 사용한다). override 는 수동 CLI(`mgr etcd put --scope sgroup`)로만 설정할 수 있는 휴면 기능이다. `install/context.py:409`, `manager/cli/etcd.py:45` |
| ➕ | sgroup override 가 없다고 가정하고 **agent SGROUP scope 를 완전히 제거한다**. RPC, 설정 toml 재작성, prefix 생성 경로가 모두 순수 삭제가 된다 |

## 3. 구현 설계

**핵심 흐름**: heartbeat 는 여전히 그룹을 보고하지만 manager 가 무시한다. DB 가 기준이다. 그룹은 명시적인 API 로만 변경할 수 있고, 새 API 가 session 정리를 책임진다.

### 3.1 기준 전환 (결정 #1, #2)

- **최초 등록은 INSERT 시점 seed 뿐이다**. 설정 `scaling-group` 은 `agents` row 가 처음 생성될 때만 적용한다. heartbeat 의 `update_fields` 에서 `scaling_group`/`resource_group_id` 를 제거하고 `insert_fields` 에는 남긴다. 이후에는 DB 가 기준이다.
- **"최초 등록"의 정의**: LOST row 가 남으므로 INSERT 때만 seed 한다는 것은 "row 가 없을 때만 설정을 적용한다"는 의미이다. 재배포(같은 agent_id 로 재부팅)는 UPDATE 경로를 타므로 설정이 다시 적용되지 않는다. **의도한 동작이다**. agent 이동은 설정 편집이 아니라 admin API 로 한다.
- 따라서 manager 는 heartbeat 에서 agent 의 상태와 자원만 변경하고 스스로 보고한 그룹은 무시한다.
- **설정 field 변경**: agent 설정 `scaling-group` 을 제거하고 **nullable** `initial_resource_group_name` 을 새로 둔다(즉시 교체하고 deprecation 기간은 두지 않는다). 설정은 사람이 아는 **자원 그룹 이름**을 담는다. UUID 는 미리 알기 어렵고 설정을 id 로 다루는 것은 적절하지 않다. manager 가 **INSERT 시 이름을 `resource_group_id` 로 해석한다**(기존 `_resolve_scaling_group_id` 경로 재사용). 설정이 이름 기반이므로 진행 중인 id migration 과 독립이다.
- **기본 자원 그룹과 fallback(최초 등록에만)**: `scaling_groups` 에 `is_default` flag 를 추가하고 partial unique index(`WHERE is_default`)로 **최대 하나**의 기본값을 강제한다. 최소 하나는 **보장하지 않는다**. 최초 등록 때 manager 가 설정 이름을 해석한다. 이름이 **null 이거나 해석되지 않으면** `is_default` 그룹으로 fallback 한다. 해석되지 않는 *명시적* 이름도 fallback 하지만 **warning 을 기록한다**(null 이름은 일반적인 zero-config 경로이므로 warning 이 필요 없다). 기본 그룹이 없고 사용할 수 있는 이름도 없으면 등록이 명확한 에러로 실패한다. 그룹에 `is_default` 를 설정하면 같은 트랜잭션에서 이전 기본값을 해제한다. fixture 는 기본 그룹 하나를 지정한다. 이렇게 하면 agent 등록의 신뢰성을 유지하면서(agent heartbeat 는 event 기반이므로 hard failure 는 agent 를 보이지 않게 만들 뿐이다) 토폴로지는 DB 기준으로 남는다.

### 3.2 RPC push 제거 (결정 #3)

- `registry.update_scaling_group` 과 agent 쪽 `agent.toml` 재작성(+`.bak`), in-memory 변경을 삭제한다.
- 그 RPC 는 다음 heartbeat 가 변경을 되돌리지 않게 하려고만 존재한다. 순수한 **보상 부채**다. DB 가 기준이 되면 존재 이유가 없어진다. 호출자는 `ModifyAgent` 하나다.

### 3.3 그룹 변경 orchestration (결정 #4)

그룹을 옮기면 충돌 session(`kernel.resource_group_id != agent.current_resource_group`)을 조정한다. 조정은 policy enum `{RESCHEDULE, TERMINATE}` 과 `force` 를 parameter 로 받는 **service 계층 경로 하나**다. v1 과 v2 가 이 service 를 **같은 방식으로** 호출하고, API 계층에서 전달하는 값만 다르다.

- **policy enum `{RESCHEDULE, TERMINATE}`** 은 모든 충돌 session 에 일괄 적용한다(session 유형별 자동 분기는 없다).
- **`force` 동작(v2)**:
  - `force` 미설정: 충돌 session 이 없으면 성공하고, 있으면 실패한다(admin 이 먼저 비운다).
  - `force` 설정: 충돌 session 을 선택한 policy 의 상태로 즉시 전이한다(terminate 는 TERMINATING, reschedule 은 re-enqueue/PENDING). 실제 정리는 기반 종료 경로가 async 이므로 **비동기로** 진행된다.
- **v1 `ModifyAgent`(superadmin)**: 같은 service 를 **하드코딩 값**(`policy=TERMINATE`, `force=True`)으로 호출하므로 충돌 session 을 항상 즉시 종료한다. RPC push 는 제거한다.
- **v2 새 API**: policy enum 과 `force` 를 **사용자 입력**으로 받고 충돌 session, policy, 결과를 web UI 에 표시한다(frontend 작업 항목).
- **reschedule 의 실제 의미**: session 은 **자기 자원 그룹(원래 그룹)을 유지한다**. 같은 그룹 안의 다른 agent 에 배치되도록 다시 대기열에 들어간다. batch session 은 다시 경쟁해 재개하지만, interactive session 은 live container migration 이 없어 reschedule 이 사실상 종료 후 재생성(상태 유실)이다. 호출자가 명시적으로 선택하는 일이고 UI 가 경고한다.
- **`RESCHEDULING` 상태 의존(순서)**: 중간 re-enqueue 상태 `RESCHEDULING` 은 선점 작업([BEP-1055](BEP-1055-preemption-scheduler-mechanics.md)/BA-3058)이 도입한다. 따라서 이 BEP 의 reschedule 경로는 그 상태가 들어온 **뒤에 구현한다**. 지금은 설계에서만 고려한다. 그때까지 terminate policy 가 주 구현 대상이다.
- **multi-node overlay 네트워크 재참여(추가 작업 필요)**: multi-node session 은 manager 가 session 마다 생성한 Docker Swarm overlay 네트워크(`bai-multinode-{session_id}`)로 kernel 을 묶는다. reschedule 이 다른 agent 에 kernel 을 다시 만들면 그 overlay 네트워크에 **재참여하는 작업이 필요하다**.
- **유예 구간 없음**. agent heartbeat 가 더 이상 agent 를 옮기지 않으므로 "일시적인 설정 오류가 실행 중 session 을 죽인다"는 위험이 사라졌고, `force` 는 즉시 전이 모델이므로 timer 기반 유예 기간이 필요 없다.

### 3.4 etcd sgroup scope 처리 (결정 #5)

- **sgroup override 가 없다고 가정한다**. 근거: 자동 기록 주체가 없고(install 은 GLOBAL 만 seed 하고 sgroup 기록은 unit test 에만 있다), 문서가 없으며, agent **시작** 때만 merge 되는 휴면 기능이다.
- 따라서 **agent SGROUP scope 자체를 제거한다**. RPC, 설정 toml 재작성, prefix 생성이 모두 순수 삭제가 된다.
- **migration 주의**: 배포 환경에서 `sgroup/<name>/...` override 를 수동으로 설정한 적이 있으면 그 값을 GLOBAL/NODE scope 로 옮겨야 한다(문서화한다).

### 3.5 신규 agent 와 재할당 agent (결정 #6)

기준 전환은 두 경우 모두 배포 시점 버그를 없앤다.
- 최초 프로비저닝: INSERT 가 설정을 seed 로 한 번 읽으므로 올바르다.
- 재배포: UPDATE 경로가 DB 값을 유지하므로 오래된 설정이 실행 중 agent 를 옮길 수 없다.

### 3.6 migration / 호환성 (결정 #7)

- **agent 설정은 fail-fast 로 깨지는 변경이다**. `scaling-group` 을 제거하고, 남겨 두면 agent 가 **시작 시 실패한다**(조용히 무시하거나 alias 하지 않는다). 운영자는 `initial_resource_group_name` 으로 전환해야 한다. 설정을 편집해 agent 를 옮기던 방식은 더 이상 동작하지 않는다(이동은 API 로 한다). rollout note 에 적는다.
- 설정은 **이름 기반**이므로 진행 중인 이름 → `resource_group_id` migration(BA-6706, BA-6780, BA-6050/6051, BA-6644/6710/6713)과 **독립이다**. manager 가 INSERT 시 이름을 id 로 해석한다. 다만 `data/agent/types.py` 의 `from_state_comparison` 이 이미 그룹 변경 시 `need_resource_slot_update` 를 지정하므로 그 상호작용은 검토가 필요하다.
- **Schema**: `scaling_groups.is_default` 를 추가하고 partial unique index(`WHERE is_default`)로 기본 그룹을 최대 하나로 둔다. fixture 가 그룹 하나를 기본값으로 표시한다.

## 4. 결정 요약

| 결정 | 내용 |
|----------|---------|
| 기준 | manager DB 가 기준이다. heartbeat 는 agent 의 상태와 자원만 변경하고 그룹은 변경하지 않는다 |
| 설정 field | agent `scaling-group` 을 제거하고 **nullable** `initial_resource_group_name` 을 둔다(**이름** 기반이며 INSERT 시 id 로 해석한다). **fail-fast 로 깨지는 변경**이다(이전 설정은 시작 시 실패한다) |
| 기본 자원 그룹 | `scaling_groups.is_default` 를 추가한다(최대 하나, partial unique index, 최소 하나는 보장하지 않음). 최초 등록에서 설정 이름이 null 이거나 해석되지 않으면 기본값으로 fallback 한다. 해석되지 않는 명시적 이름도 fallback 하지만 warning 을 기록한다. 기본값도 없고 사용할 수 있는 이름도 없으면 등록이 실패한다 |
| 최초 등록 정의 | row 가 없을 때만 설정을 seed 한다(INSERT). 재배포(UPDATE)는 DB 값을 유지한다. 의도한 동작이다 |
| heartbeat | 스스로 보고한 그룹을 무시한다(`update_fields` 에서 `scaling_group`/`resource_group_id` 를 제거하고 `insert_fields` 에 남긴다) |
| RPC 제거 | `registry.update_scaling_group` 과 agent `agent.toml` 재작성(보상 부채)을 삭제한다 |
| orchestration 구조 | 충돌 session 정리는 service 계층 경로 하나다(parameter: policy enum + `force`). v1/v2 가 공유하고 전달하는 값만 다르다 |
| v1 `ModifyAgent` | service 를 하드코딩(`TERMINATE` + `force`)으로 호출하므로 항상 즉시 종료한다 |
| v2 새 API | policy enum 과 `force` 를 사용자 입력으로 받는다. `force` 미설정이면 충돌이 없을 때 성공하고 있을 때 실패한다. 설정하면 즉시 전이한다 |
| 정리 policy | enum `{RESCHEDULE, TERMINATE}` 을 모든 충돌 session 에 일괄 적용한다(자동 분기 없음). interactive reschedule 은 상태를 잃는다 |
| reschedule 범위 | session 은 자기 자원 그룹을 유지한다(원래 그룹 안에서 다시 대기열에 들어간다). `RESCHEDULING` 상태는 선점 작업(BEP-1055/BA-3058)과 함께 온다. 지금은 terminate 를 먼저 구현한다 |
| force 동작 | TERMINATING 또는 re-enqueue 로 즉시 전이한 뒤 비동기로 진행한다. 유예 구간은 없다 |
| etcd sgroup | override 가 없다고 가정하고 agent SGROUP scope 를 제거한다(순수 삭제). 수동 override 는 GLOBAL/NODE 로 옮긴다 |

## 5. 열린 질문

- `is_default` 가 **session** 의 기본 그룹 선택도 좌우해야 하는지. 그룹을 생략한 session 은 지금 허용된 첫 후보를 고른다(`registry.py:2022`). 이 BEP 범위 밖이고 후속 검토 대상이다.
- 새 v2 API 의 정확한 엔드포인트와 GraphQL 이름 같은 구현 세부는 구현 PR 에서 정한다.

> 결정 요약과 본문으로 옮긴 항목: ModifyAgent 기본 policy(terminate), `force` 미설정 동작, 설정 교체(이름 기반 + fail-fast 로 깨짐, INSERT 시 id 로 해석하므로 id migration 과 독립), reschedule 범위(자원 그룹 유지 + `RESCHEDULING` 은 선점 작업을 따름).

## 6. 참고

- Epic **BA-6800**
- 관련 migration: BA-6706, BA-6780, BA-6050/6051, BA-6644/6710/6713
- `RESCHEDULING` 상태 의존: [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md) / BA-3058 (reschedule/terminate 분기, live migration 이 없을 때 interactive 상태 유실)
