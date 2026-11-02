# 그룹 세션을 위한 세션 그룹 배치

## 관련 이슈

- Epic **BA-6990**, 이 BEP **BA-6991**
- 선행 조건(완료): **BA-6135**(PR #13066). endpoint replica spreading 사슬에 producer 가 없는 죽은 코드임을 확인하고 제거했다. 이 BEP 는 그 빈틈을 일급 개념으로 다시 설계한다.
- 인접: **[BEP-1055](BEP-1055-preemption-scheduler-mechanics.md)**. 같은 provisioner/selector pipeline 을 다른 축에서 공유한다(선점은 "누가 축출되는가", 이 BEP 는 "어디로 가는가"에 답한다)

## 1. 목표

**"이 세션들을 agent 별로 서로 떨어뜨려(spread) 두거나 함께 모아(pack) 둔다"를 일급 배치 정책으로 승격한다.**

지금 배치 전략은 자원 그룹의 `agent_selection_strategy`(dispersed/concentrated/roundrobin/legacy) 하나뿐이다. 그것은 cluster 전체를 채우는 방법에 답하고, 특정 세션 묶음이 서로 어떤 위치에 있어야 하는지는 표현하지 못한다. 대표적인 사례로, 한 deployment 의 replica 세션은 서로 다른 agent 에 있어야 agent 하나가 죽어도 서비스가 살아남는다. scheduler 에는 그 요구를 표현할 어휘가 없다.

BA-6135 는 `kernel_counts_at_endpoint` spreading 사슬을 어떤 producer 도 채운 적이 없다는 것을 확인하고 제거했다. 그래서 "replica 는 흩어진다"는 계약은 문서와 아무것도 강제하지 않는 설정 값(`enforce_spreading_endpoint_replica`)에만 남아 있다. 이 BEP 는 replica 전용 특수 사례가 아니라 일반 개념으로 그 기능을 되살린다.

**세션 그룹**은 공통 관심사를 공유하는 세션 묶음이며 그 배치 정책을 가진다. deployment replica 가 첫 사례이고 그룹을 자동으로 생성하는 유일한 경로이지만, **개념 자체가 deployment 전용은 아니다**. 사용자가 세션 대기열 추가 시 그룹을 지정할 수 있고, 분산 학습 job 같은 workload 도 같은 장치를 사용한다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 2.1 개념과 model

| | 항목 |
|---|---|
| ✅ | 세션 묶음 개념이 없다. `sessions.group_id` 는 project(사용자 그룹)이며 **배치 그룹이 아니다**. 이름이 오해를 일으킨다 |
| ✅ | deployment replica 는 `sessions.replica_id → routings → replica_groups` 로만 간접적으로 식별되고, scheduler 는 그 경로를 읽지 않는다 |
| ✅ | `sessions.designated_agent_ids` + `options.agent_selection_policy`: 한 세션을 특정 agent 에 고정하는 축 |
| ➕ | 새 `session_groups` 테이블. 배치 정책을 담는 주체 |
| ➕ | `sessions.session_group_id`, **nullable** FK. NULL 은 "배치 제약 없음"이고 일반 세션의 기본값이다 |
| ➕ | `replica_groups.session_group_id`, **NOT NULL** FK. replica group 은 늘 자기 세션 그룹을 함께 생성한다(1:1) |

> **모든 세션이 그룹을 갖지는 않는다.** 대부분의 세션은 배치 제약이 필요 없고, 그런 세션마다 구성원 하나짜리 그룹 row 를 강제하면 보여 줄 것이 없는 row 만 세션마다 늘어난다. 제약이 필요한 세션만 그룹을 가진다.

### 2.2 API

| | 항목 |
|---|---|
| ✅ | 세션 생성은 `designated_agents` + `agent_selection_policy`(`strict`/`preferred`)를 받는다. **적용 수준이 둘이라는 선례** |
| ✅ | 자원 그룹 scheduler opts 는 `agent_selection_strategy` 를 담고, 관리자가 자원 그룹별로 정한다 |
| ✅ | 자원 그룹 scheduler opts 는 `enforce_spreading_endpoint_replica: bool` 을 담는다. **강제하는 것이 없는 외부 계약** |
| ➕ | 세션 그룹 v2 API, 표준 6개 동작(생성/조회/검색/변경/삭제/영구 삭제) |
| ➕ | **세션 대기열 추가 시 `session_group_id`**(선택). 생략하면 NULL, 곧 제약 없음 |
| ➕ | replica group 생성이 자기 세션 그룹을 생성하고 배치 정책을 받는다. **기본 `spread` + `preferred`** |
| ➕ | `enforce_spreading_endpoint_replica` 를 deprecate 한다. 값은 replica group 의 세션 그룹 정책으로 이전한다(3.f `enforce_spreading_endpoint_replica` 이전) |

> 사용자는 "이 세션들이 서로 어떤 위치에 있는가"를 선언하고 "이 세션이 어느 agent 로 가는가"를 선언하지 않는다. `designated_agents` 와는 다른 계층이고 둘은 함께 존재한다(2.5).

### 2.3 DB

새 `session_groups` 테이블:

| column | type | 비고 |
|--------|------|------|
| `id` | GUID PK | 사용자와 replica group 모두 이 id 로 그룹을 참조한다 |
| `domain_id` | FK | 소유 scope |
| `project_id` | FK | 소유 scope |
| `owner_user_id` | FK | 소유 scope |
| `placement_direction` | enum `spread` \| `pack` \| `none` | `none` 은 그룹을 유지하되 배치에서 빠진다 |
| `placement_enforcement` | enum `preferred` \| `strict` | 적용 수준 |
| `created_at` / `deleted_at` | timestamp | `deleted_at` 이 retention 기준이다(3.e 그룹 정리: retention catalog) |

**`name` column 이 없다.** `replica_groups` 도 없고 deployment 를 통해 식별된다. 사용자가 생성한 그룹도 마찬가지로 생성 시 반환한 id 로 참조한다. 사람이 읽는 이름은 실제 사용 사례가 요구할 때 추가하는 편이 낫다.

**소유권은 세션, deployment 와 맞아야 한다.**

| entity | 소유 field |
|--------|------------------|
| `sessions` | `domain_id`, `group_id`(project), `user_uuid` |
| `endpoints`(deployment) | `domain`, `project`, `session_owner`(+ `created_user`) |
| **`session_groups`(신규)** | `domain_id`, `project_id`, `owner_user_id`. **같은 세 축** |

**불변 조건: 그룹의 모든 구성원 세션은 같은 사용자에 속한다**(`session.user_uuid == group.owner_user_id`). project 나 domain 을 공유한다고 다른 사용자의 세션이 그룹에 들어올 수 있는 것은 아니다. 그룹 정책이 구성원의 배치 방법을 정하므로, 다른 사람의 세션을 받아들이는 것은 그 사람의 배치에 간섭하는 일이다. `domain_id`/`project_id` 는 조회 범위와 정리만 담당하고, 편입은 `owner_user_id` 만으로 판단한다.

- deployment 가 생성한 세션 그룹은 endpoint 의 `(domain, project, session_owner)` 를 상속한다. route 세션은 `session_owner` 의 `user_uuid` 로 생성되므로 불변 조건은 구조상 성립한다.
- 소유자가 다른 세션을 편입하면 거부한다.
- 그룹 조회 권한과 정책 변경 권한은 소유 scope 의 기존 RBAC 규칙을 따른다.

기존 테이블 변경:

| | 항목 | 삭제 동작 |
|---|---|---|
| ➕ | `sessions.session_group_id`, `session_groups.id` 를 참조하는 **nullable** FK(index 대상. agent 별 구성원 질의의 join key 다) | `ON DELETE SET NULL`. 그룹이 먼저 사라지면 세션은 제약이 없는 상태가 될 뿐이다 |
| ➕ | `replica_groups.session_group_id`, `session_groups.id` 를 참조하는 **NOT NULL** FK | replica group 보다 앞서 retention catalog 가 정리한다(3.e 그룹 정리: retention catalog) |
| ➖ | 이전 후 `ScalingGroupOpts.enforce_spreading_endpoint_replica` 를 제거한다 | |

> 방향과 적용 수준을 별도 column 으로 둔 것은 서로 직교하기 때문이다. 하나의 enum(`spread_strict` 같은 값)으로 합치면 얻는 것 없이 값만 늘어난다.

### 2.4 sokovan(scheduler 동작)

| | 항목 |
|---|---|
| ✅ | selector pipeline: **제외 filter → 상태 filter → order → strategy 선택**. order 는 선호 등급으로 좁히기만 하고 제외하지 않는다 |
| ✅ | `DesignatedStrictTrackerFilter`(제외) / `DesignatedPreferredOrder`(order). **strict 는 filter, preferred 는 order 라는 선례** |
| ✅ | 제외 filter 의 계약: *"어떤 상태 변경으로도 살릴 수 없는 agent 를 버린다(선점 포함)"*. strict 배치 제약에 필요한 의미와 정확히 같다(3.d 만족할 수 없는 strict 제약) |
| ✅ | `AgentStateTracker` 는 한 번의 스케줄링 pass 안에서 in-batch 할당(committed/pending)을 누적한다 |
| ✅ | `SystemSnapshot` 은 선점 후보를 포함해 자원 그룹별 스케줄링 상태를 이미 담는다 |
| ✅ | scheduler 는 **그룹 구성원 정보를 전혀 모른다**(핵심 빈틈) |
| ➕ | snapshot 에 agent 별 세션 그룹 구성원 정보(3.b 관찰: agent 별 구성원 수) |
| ➕ | `AgentStateTracker` 에 그룹별 in-batch 구성원 수. 한 pass 가 같은 그룹의 세션 여럿을 배치할 때 필요하다(3.c 배치 결정) |
| ➕ | `SessionGroupOrder`(preferred) + `SessionGroupStrictFilter`(**제외**)(3.c 배치 결정) |

### 2.5 직교성과 우선순위

세 축이 서로 다른 질문에 답하고, **더 국소적인 대상이 늘 먼저 적용된다.**

| 축 | 질문 | 정하는 주체 | 대상 | 우선순위 |
|------|----------|--------|--------|------------|
| `designated_agents`(기존) | 이 세션은 **어느 agent** 로 가는가 | 사용자, 세션별 | 세션 하나 | 1순위(가장 국소적) |
| **세션 그룹 정책(신규)** | 이 **세션들이 서로 어떤 위치에 있는가** | 그룹 소유자 | 그룹 구성원 | 2순위 |
| 자원 그룹 `agent_selection_strategy`(기존) | **cluster 를 어떻게 채우는가** | 관리자, 자원 그룹별 | 자원 그룹 전체 | 3순위(가장 전역적) |

**충돌 규칙: 세션 그룹 정책이 자원 그룹 strategy 를 이긴다.** 자원 그룹이 `concentrated`, 그룹이 `spread` 이면 후보를 먼저 구성원이 없는 agent 로 좁히고, concentrated 는 **그 집합 안에서** 고른다. 자원 그룹 strategy 는 버려지지 않고 세션 그룹이 남긴 후보 집합 위에서 동작한다.

> 이 우선순위는 기존 pipeline 순서(filter → order → strategy)에서 중재 로직 없이 나온다. 새 축을 위해 중재자를 넣지 않아도 되는 것이 이 설계의 핵심 이점이다.

## 3. 구현 설계

**핵심 흐름:** 그룹이 있는 세션에 대해 snapshot 이 agent 별 구성원 수를 담고, selector 가 그룹 정책으로 후보 agent 를 좁히고, 남은 것 중에서 자원 그룹 strategy 가 최종 선택을 한다.

### (a) 세션이 그룹을 갖는 경로

| 경로 | 시점 | FK |
|------|------|----|
| **세션 대기열 추가** | 사용자가 `session_group_id` 를 전달한다. 생략하면 NULL | `sessions.session_group_id`(nullable) |
| **replica group 생성** | 세션 그룹을 replica group 과 **항상 함께** 만든다(1:1). route 세션이 그것을 상속한다 | `replica_groups.session_group_id`(not null) |

`session_group_id` 가 NULL 인 세션은 이전과 똑같이 자원 그룹 strategy 만으로 배치된다. scheduler 에서 그룹과 관련된 경로는 모두 그룹이 있는 세션에서만 진입한다.

**replica group 의 기본 정책은 `spread` + `preferred`** 다. 가능하면 replica 가 서로 다른 agent 에 배치되고, agent 하나가 꽉 차도 rollout 이 멈추지 않는다.

### (b) 관찰: agent 별 구성원 수

selector 는 주어진 agent 가 이 그룹의 구성원을 지금 몇 개 보유하는지 알아야 한다.

- 출처는 **`resource_allocations`**(점유의 기준)와 `sessions.session_group_id` 의 join 이다. `kernels.occupied_slots` 는 읽지 않는다.
- 관찰 범위는 **이미 agent 에 묶인 모든 살아 있는 세션**이고 RUNNING 만이 아니다. 예약(SCHEDULED/PREPARING)을 가진 세션도 세야 한다. 그렇지 않으면 아직 뜨지 않은 replica 를 세지 않아 한 agent 에 몰린다.
- **다중 node(cluster) 세션은 자기 kernel 을 하나라도 두는 agent 마다 1로 센다.** 여러 agent 를 점유하므로 spread 관점에서 그 agent 들은 이미 모두 그룹을 보유한 상태다.
- snapshot 의 자원 그룹 scope 가 기존 선점 후보 snapshot 옆에 그룹별, agent 별 count map 으로 담는다.
- loading 은 **이번 pass 의 대기 세션 그룹으로 제한한다**. 그룹 세션이 없는 pass 는 아무것도 읽지 않는다.

### (c) 배치 결정: 기존 pipeline 에 두 가지 추가

적용 수준이 어느 pipeline 단계에 붙는지가 곧 의미다. `designated_agents` 도 이미 그렇게 동작한다.

| 적용 수준 | pipeline 단계 | 동작 |
|-------------|----------------|----------|
| `preferred` | **order**(`SessionGroupOrder`) | 선호 등급으로만 좁힌다. 선호 agent 에 용량이 없으면 남은 후보가 그대로 남고 배치는 성공한다 |
| `strict` | **제외 filter**(`SessionGroupStrictFilter`) | 조건에 맞지 않는 agent 를 제거한다. 후보 집합이 비면 배치 오류다(3.d 만족할 수 없는 strict 제약) |
| `none` | — | 그룹은 유지하되 배치에 참여하지 않는다 |

**rank 함수(order, 낮을수록 선호):**

| 방향 | rank | 효과 |
|-----------|------|--------|
| `spread` | agent 의 구성원 수 | 구성원이 가장 적은 agent 로 좁힌다. 구성원이 0인 agent 가 있으면 그 등급만 남는다 |
| `pack` | agent 의 구성원 수에 음수를 취한 값 | 구성원이 가장 많은 agent 로 좁힌다. 그룹이 가능한 한 적은 agent 로 모인다 |

두 방향은 부호만 반대인 같은 rank 다. pipeline 은 **모든 후보에 걸쳐** 최솟값 rank 를 택하므로 음수를 취한 count 는 전역 최댓값을 고른다. `pack` 은 "가장 꽉 찬 agent"를 표현할 수 있고 실제로 그렇게 동작한다. 자원 그룹 strategy 는 남은 등급 안에서 여전히 고르며, agent 여럿이 동률일 때 의미가 있다.

**filter 조건(strict):**

| 방향 | 통과 조건 | 비고 |
|-----------|-------------|------|
| `spread` | agent 의 구성원 수가 0 | 자원 그룹의 모든 agent 가 이미 구성원을 가지면 후보 집합이 비고 배치 오류가 난다(3.d 만족할 수 없는 strict 제약) |
| `pack` | agent 의 구성원 수가 0보다 큼 | **anchor 규칙**: 아직 구성원을 가진 agent 가 없을 때(첫 구성원)는 filter 를 적용하지 않는다. 그렇지 않으면 첫 세션을 영원히 배치할 수 없다. 이 규칙 때문에 `pack` + `strict` 는 후보 집합을 사실상 비우지 않는다 |

**한 pass 안에서의 누적.** 한 tick 에 같은 그룹의 세션 여럿을 배치하는 것(three-replica scale-out)은 정상 경로다. snapshot 만 보고 판단하면 셋 모두 "구성원 0"을 보고 같은 agent 에 배치된다. 그래서 `AgentStateTracker` 는 slot 과 container 수를 담는 것과 같은 방식으로, 같은 all-or-nothing `commit()`/`rollback()` 계약 아래 **그룹별 in-batch 증가분**을 담는다. rank 와 filter 는 늘 `관찰값 + in-batch`를 읽는다.

### (d) 만족할 수 없는 strict 제약은 선점 트리거가 아니다

strict 를 **제외 filter** 단계에 두는 것은 의미상의 선언이고, 그 단계 자체의 계약이 근거다.

> *"어떤 상태 변경으로도 살릴 수 없는 agent 를 버린다(선점 포함)."*

`spread` + `strict` 에서 후보 집합이 비었다는 것은 **자원 그룹의 모든 agent 가 이미 이 그룹의 구성원을 하나씩 보유**한다는 의미다. 자원을 비워도 소용없다. 다른 사람의 세션을 축출해도 그 agent 에는 이 그룹의 구성원이 그대로 남는다. 따라서:

| 측면 | 동작 |
|--------|----------|
| 후보 집합이 빔 | `NoCompatibleAgentError`. strict `designated_agents` 와 같은 경로다 |
| 선점 | **시도하지 않는다.** 제외 단계는 선점 planner 에 도달하기 전에 실행된다 |
| 세션 상태 | provisioner 가 `SchedulingFailure` 를 기록한다. **세션은 PENDING 으로 남고 다음 tick 에 재시도한다**. 배치 실패는 세션 종료가 아니다 |
| 복구 | 다른 구성원이 종료되어 agent 가 비면 세션은 정상적으로 배치된다 |

"오류로 처리한다"와 "세션이 종료된다"는 다른 일이다. 사용자는 배치를 차단한 그룹과 방향을 알려 주는 실패 사유를 보고, 조건이 풀리면 세션은 스스로 배치된다.

### (e) 그룹 정리: retention catalog 를 통한다

**결론부터: 그룹은 기존 cascade 로 정리되지 않는다. retention catalog 에 명시적 spec 이 필요하다.**

애플리케이션은 replica group 을 영구 삭제하지 않는다. lifecycle 을 terminal 상태로 옮기고, row 삭제는 **retention sweep 의 bulk DELETE** 가 맡는다(`RetentionCategory.DEPLOYMENTS` 가 `routings` → `replica_groups` → `endpoints` 순서로 각자의 기준에서 삭제한다). 삭제 시점에 cascade 를 걸 애플리케이션 수준 hook 이 없다.

DB `ON DELETE CASCADE` 도 사용할 수 없다. FK 가 `replica_groups.session_group_id → session_groups.id` 방향이라 DB cascade 는 **반대** 방향으로 동작한다(그룹을 삭제하면 replica group 이 삭제된다).

따라서 두 종류의 그룹 모두 retention catalog 가 정리한다.

| 그룹 종류 | 정리 |
|------------|---------|
| replica group 이 소유 | `DEPLOYMENTS` 카테고리에 세션 그룹 spec 을 두고 **`replica_groups` spec 앞에** 배치해, 아직 남아 있는 부모 FK 로 정리한다. endpoint id 로 `deployment_revisions` 를 먼저 정리하는 것과 같은 패턴이다 |
| 사용자가 생성 | `SESSIONS` 카테고리에 spec 을 두고 자기 `deleted_at` 기준에 `NOT EXISTS (구성원 세션)` guard 를 붙여, 살아 있는 구성원이 있는 그룹은 절대 제거하지 않는다 |

**새 retention 카테고리는 없다.** `DEPLOYMENTS` 와 `SESSIONS` 에 spec 을 하나씩 추가하면 충분하다. 카테고리는 관리자가 조정하는 단위이고, 그룹 retention 을 따로 조정할 이유가 없다. 그룹이 자기를 소유한 replica group 이나 구성원 세션보다 오래 살아남아야 할 일은 없다.

replica group spec 은 역방향 FK 로 부모의 기준을 맞춘다. terminal replica group 을 대상으로 `session_groups.id IN (SELECT replica_groups.session_group_id ...)` 로 그룹 row 를 고르고, 기존 spec 의 부모 기준 형태를 사용한다. **spec 순서가 정확성을 정한다.** `replica_groups` spec 이 먼저 실행되면 원천이 이미 비어 있고 그룹은 영구히 고아가 된다. 여기서 catalog 순서는 계약이므로 주석으로 밝혀야 한다.

사용자가 만든 그룹은 명시적 삭제/영구 삭제 API 로도 제거할 수 있다. 구성원이 끝났다는 이유만으로 자동 삭제하지 않는다. 그룹을 새 세션에 다시 사용하는 것이 정상 패턴이기 때문이다. 버려진 그룹은 위의 `deleted_at` sweep 이 모은다.

**그룹이 구성원보다 먼저 사라질 수 있다.** `SESSIONS` 와 `DEPLOYMENTS` 는 정책과 기준이 독립된 별도 카테고리라 삭제 순서가 정해져 있지 않다. 그래서 `sessions.session_group_id` 가 `ON DELETE SET NULL` 이다. 세션 row 는 먼저 사라진 그룹에도 살아남고, 이미 끝난 배치는 다시 보지 않는다(3.g 정책 변경의 범위).

### (f) `enforce_spreading_endpoint_replica` 이전

replica group 만 이전한다. 일반 세션은 그룹이 NULL 이고 backfill 이 필요 없다.

| 단계 | 내용 |
|------|---------|
| 1 | 기존 replica group 마다 세션 그룹을 생성하고 `replica_groups.session_group_id`(NOT NULL)를 backfill 한다 |
| 2 | 소유 자원 그룹의 값이 `true` 였으면 정책을 `spread` + **`preferred`** 로, 아니면 `none` 으로 정한다 |
| 3 | field 를 deprecated 로 표시하고 읽지 않는다(동작 변화 없음. 강제하던 것이 없었다) |
| 4 | 다음 major 에서 schema 와 API 에서 제거한다 |

`strict` 가 아니라 `preferred` 로 이전하는 이유: 그 값은 한 번도 강제된 적이 없으므로 `strict` 로 승격하면 이전에 잘 배포되던 서비스가 배치 실패에 빠질 수 있다. **관찰 가능한 동작이 나빠지지 않는 방향으로 이전하고, strict 는 사용자가 명시적으로 선택하게 한다.**

### (g) 정책 변경의 범위

**정책 변경은 그 이후의 배치에만 적용된다.** 이미 배치된 세션은 재배치하지 않는다. rebalancing 은 없다. 정책은 그룹의 *다음* 세션이 어디로 갈지 정하고, 실행 중인 세션을 소급해 제약하지 않는다.

### 이름: `spread` / `pack`

업계 표준 짝을 사용한다. `dispersed`/`concentrated` 는 Backend.AI 고유 표현에 가깝다.

| 시스템 | 떨어뜨리기 | 함께 모으기 |
|--------|-------|----------|
| Kubernetes | Pod Topology **Spread** Constraints, `LeastAllocated` | **Bin packing**, `MostAllocated` |
| Slurm | `--spread-job` | `CR_Pack_Nodes` |
| Nomad | `spread` block | Bin-packing(기본값) |
| Docker Swarm | `spread` | `binpack` |

자원 그룹 축은 기존 `dispersed`/`concentrated` 를 유지한다. 두 축의 어휘가 다르면 서로 직교한다는 신호가 된다.

## 결정 요약

| 결정 | 내용 |
|----------|---------|
| 개념 | 세션 그룹은 공통 관심사를 공유하는 세션 묶음이며 배치 정책을 가진다. **deployment 전용이 아니고 세션 대기열 추가 시에도 고를 수 있다** |
| 데이터 model | 새 `session_groups` 테이블. `sessions.session_group_id` 는 **nullable**, `replica_groups.session_group_id` 는 **NOT NULL** |
| 모든 세션의 그룹 소속 | **기각.** NULL 은 "제약 없음"이고 일반 세션의 기본값이다 |
| `name` column | 추가하지 않는다. `replica_groups` 도 deployment 를 통해 식별되고, 사용자 그룹은 id 로 참조한다 |
| 소유 scope | `domain_id` / `project_id` / `owner_user_id`. 세션, endpoint 와 같은 세 축이다. deployment 의 그룹은 endpoint 값을 상속한다 |
| 구성원 소유권 | **그룹의 모든 구성원은 한 사용자에 속한다.** project 나 domain 을 공유해도 다른 사용자의 세션을 받아들이지 않는다. 그러면 정책이 그 사람의 배치를 정하게 된다 |
| 정책 축 | **방향(`spread`\|`pack`\|`none`) x 적용 수준(`preferred`\|`strict`)** 을 두 column 으로 둔다 |
| 세분성 | **agent 단위.** agent 는 보통 node 이므로 별도 topology 축을 두지 않는다 |
| 직교성 | 자원 그룹 `agent_selection_strategy` 와 별개 축이다. 자원 그룹 strategy 는 세션 그룹이 남긴 후보 집합 위에서 동작한다 |
| 우선순위 | `designated_agents` > **세션 그룹** > 자원 그룹 strategy. 더 국소적인 대상이 늘 먼저 적용된다 |
| 구현 지점 | `preferred` 는 tracker **order**, `strict` 는 **제외 filter**. 기존 `designated_agents` 선례를 따르고 중재 로직은 없다 |
| rank | 부호만 반대인 같은 rank: spread 는 구성원 수, pack 은 구성원 수의 음수(모든 후보에 걸친 pipeline 의 최솟값이 곧 전역 최댓값이 된다). `pack` 은 첫 구성원에 제약을 건너뛴다(**anchor 규칙**) |
| 만족할 수 없는 strict | **선점하지 않고 오류로 기록한다.** 어떤 상태 변경으로도 구제할 수 없는 조건(선점 포함)은 제외 단계에 속한다. 세션은 PENDING 으로 남아 재시도한다 |
| 관찰 | `resource_allocations` 와 `sessions.session_group_id` 의 join. agent 에 묶인 모든 살아 있는 세션이 세어지고, 다중 node 세션은 agent 마다 한 번 센다. 이번 pass 의 그룹만 load 한다 |
| in-batch 누적 | 기존 commit/rollback 계약 아래 `AgentStateTracker` 에 그룹별 증가분을 둔다 |
| deployment 기본값 | replica group 은 세션 그룹을 **`spread` + `preferred`** 로 만든다 |
| 정책 변경 | **새 배치에만 적용된다.** 기존 세션은 재배치하지 않는다 |
| 사전 검증 | **없다.** 목표 구성원 수가 agent 수보다 큰 `spread` + `strict` 조차 생성 시에 거부하지 않는다. replica 수와 agent 수는 runtime 에 함께 변하므로 생성 시점의 판정은 곧 낡는다. 3.d 의 runtime 실패로만 드러난다 |
| 정리 | **기존 cascade 가 적용되지 않는다.** 삭제는 retention sweep 이 맡고 FK 방향이 DB cascade 를 배제하므로, `DEPLOYMENTS`(**`replica_groups` 앞**)와 `SESSIONS`(`deleted_at` + `NOT EXISTS` guard)에 spec 을 추가한다. **새 카테고리는 없다** |
| legacy | `enforce_spreading_endpoint_replica` 는 replica group 만 `spread`+`preferred`(또는 `none`)로 이전한 뒤 deprecated 된다 |
| 이름 | k8s/Slurm/Nomad/Swarm 을 따라 `spread`/`pack`. 자원 그룹 축은 `dispersed`/`concentrated` 를 유지한다 |

## 열린 질문

- **적합성 검사가 그룹 제약을 존중하는지.** selector 는 스케줄링 pass 와 세션 배치 계산 적합성 검사가 공유한다. 거기에 그룹 제약을 적용하면 "이 세션이 지금 시작할 수 있는가"가 더 정확해지지만, 그 경로에서도 그룹 관찰을 load 해야 한다.

## 참고

- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md). 같은 provisioner/selector pipeline. snapshot 과 tracker 계약을 확장한 선례
- [BEP-1006](BEP-1006-service-deployment-strategy.md). deployment 와 replica group 구조
- [BEP-1063](BEP-1063-db-record-retention.md). 정리 spec 을 추가하는 retention catalog
- 선례: [Kubernetes Pod Topology Spread Constraints / Resource Bin Packing](https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/)(`whenUnsatisfiable: DoNotSchedule|ScheduleAnyway` 가 strict/preferred 에 대응한다), [Slurm `--spread-job` / `CR_Pack_Nodes`](https://slurm.schedmd.com/srun.html), Docker Swarm `spread`/`binpack`, Nomad `spread` block
