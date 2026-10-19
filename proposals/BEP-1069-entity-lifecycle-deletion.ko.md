---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-23
Created-Version: 26.8.0
Target-Version: 
Implemented-Version: 
---

# 엔티티 lifecycle 삭제 관리

## 관련 이슈

- BA-7026 — Epic
- BA-7030 — 이 BEP
- BA-6807 — 흡수: user, project purge 가 scope 별 RBAC role 을 남김
- BA-6186 — 흡수: scope 소유 role 의 연쇄 purge
- BA-7296 — 대체 (Not Planned): purge 조정을 lifecycle manager 로 옮기는 방향
- BA-4519 — storage proxy lifecycle 의 RBAC creator, purger
- BA-6738 — vfolder purge 때 소유자 위임
- BA-3709 — project soft delete
- BA-7285 — virtual scope RBAC
- BEP-1062 — virtual scope RBAC
- BA-7443 — 진행 중: user purger 를 models/ 로
- BA-7444 — 진행 중: resource_group purger 를 models/ 로
- BA-7449 — 진행 중: project purger 를 models/ 로
- BA-8573 — API 에서 Node 와 관계를 식별하는 방식 (삭제 응답 규칙)

## 목표

`domain`, `project`, `user`, `vfolder`, `image` 의 삭제를 하나의 lifecycle 로 다룬다.

지금은 소유 엔티티의 하위 자원을 **같은 요청 안에서 동기로** 지운다. DB 에만 있는 연결 행에는 맞다.
storage 에 실제 바이트가 있는 vfolder, proxy route 가 붙은 endpoint, agent 에서 도는 session 에는 맞지
않는다. DB 행을 지워도 그것들은 정리되지 않고, 정리가 한 트랜잭션에 들어가지도 않는다. 지금의 `user`
purge 는 session 을 종료 대상으로 **표시만** 하고 user 행을 지운다. 그래서 session 이 실제로 끝나기 전에
소유자가 사라진다.

이 BEP 는 네 가지를 정한다.

1. 업무 상태, soft delete, purge 진행을 각각 어느 컬럼에 두는지
2. 다섯 엔티티가 공유하는 **purge 진행 상태 전이**와 각 상태의 뜻
3. controller, coordinator, 엔티티 타입별 handler 의 자리
4. **실패 처리**와 **외부 자원과의 일관성**을 누가 맡는지, 그리고 API 응답

## 영역별 현재 설계와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 더할 것**을 나눈다.

### 2.1 삭제 상태의 표현

|  | 항목 |
| --- | --- |
| ✅ | `domain`, `project`: `is_active` boolean 과 status enum(`active` / `deleted` / `purging` / `purge-error`). soft delete 가 둘을 함께 쓴다 |
| ✅ | `user`: `UserStatus`(`active` / `inactive` / `deleted` / `before-verification` / `purging` / `purge-error`). restore 는 늘 `active` 로 되돌린다 |
| ✅ | `image`: `ImageStatus`(`ALIVE` / `DELETED` / `PURGING` / `PURGE_ERROR`). registry 재스캔이 `DELETED` 행을 `ALIVE` 로 되살린다 |
| ✅ | `vfolder`: `VFolderOperationStatus` 하나에 업무 상태(`ready` … `error`)와 삭제 단계(`delete-pending` → `delete-ongoing` → `delete-complete` / `delete-error`)가 함께 있다 |
| ✅ | `role`: `status`(`active` / `inactive` / `deleted`)와 `deleted_at`. restore 는 늘 `active` 로 되돌린다. `role_preset`: `deleted` boolean. `artifact`: `availability`(`ALIVE` / `DELETED`) |
| ✅ | `purging`, `purge-error` 값은 정의만 있고 쓰는 곳이 없다. purge 는 모두 요청 안에서 동기로 끝난다 |
| ✅ | 다섯 엔티티 모두 `restore` 가 있다 |
| ➕ | 업무 상태, soft delete, purge 진행을 컬럼 셋으로 나눈다 (3.1) |
| ➕ | soft delete 는 공통 Mixin 의 `deleted_at` 하나로 판단한다 |
| ➕ | 외부 자원을 정리하는 다섯 엔티티에 `purge_status` 컬럼을 둔다 |
| ➕ | 업무 status enum 에서 삭제 값(`deleted`, `purging`, `purge-error`, `delete-*`)을 뺀다. `domain`, `project` 는 status enum 과 `is_active` 를 지운다 |

`user` 의 soft delete 는 keypair 를 건드리지 않는다. 지운 user 의 API 접근은 인증 게이트가 막는다 (2.2).

### 2.2 인증 게이트

|  | 항목 |
| --- | --- |
| ✅ | 로그인(비밀번호) 경로가 `user.status` 를 본다. `deleted` 는 거부한다 |
| ✅ | API 요청 경로(keypair HMAC, JWT)가 `user.status` 를 본다 (`_AUTH_DENIED_USER_STATUSES`). 비활성, 삭제, purge 중인 user 를 거부한다 |
| ➕ | 게이트가 `deleted_at` 과 `purge_status` 를 본다. status 에서 삭제 값이 빠지기 전에 들어가야 한다 |

순서를 거꾸로 하면 soft delete 된 user 가 자기 키로 API 를 계속 부를 수 있다.

### 2.3 하위 자원 정리

`BatchPurgerSpec` 구현 29개는 두 종류로 나뉜다.

| 종류 | 대상 | 지금 방식이 맞는가 |
| --- | --- | --- |
| DB 에만 있는 연결 행과 딸린 행 | resource_group↔domain/project/keypair 연결, group_association, vfolder_permission, vfolder_invitation, error_log, keypair, user_role, session_idle_check, session_group | 맞다 |
| 외부 자원이 뒤에 있는 행 | endpoint (proxy route), routing, session (agent 의 컨테이너), vfolder (storage 의 바이트) | 맞지 않다 |

|  | 항목 |
| --- | --- |
| ✅ | 연결 행 purger 는 이미 subquery 기반 일괄 삭제로 돌고 `conflict_checks` 로 선행 조건을 본다 |
| ✅ | `user` purge 만 서비스 계층에서 절차로 처리한다: vfolder mount 확인, 공유 vfolder 이전, endpoint 위임, session 종료 표시, vfolder 삭제, 행 purge |
| ➕ | 외부 자원이 뒤에 있는 하위 자원은 **그 자원의 종료 경로로 진행하고, 끝난 것을 확인한 뒤에 행을 지운다.** 바로 지우지 않는다 |
| ➕ | 엔티티마다 정리 순서를 선언하고 서비스 메서드 본문에서 절차를 걷어낸다 |

### 2.4 lifecycle 장치

|  | 항목 |
| --- | --- |
| ✅ | `sokovan/reconciler`: 엔티티에 묶이지 않은 lifecycle coordinator. tick 한 번은 fetch → execute → classify → apply → post_process 이고, 엔티티별 retry, give-up, expiry 분류, stage 별 metric, 바로 시작하기 위한 valkey needed-flag 가 있다 |
| ✅ | `leader/tasks/retention_sweep.py`: leader 에서만 도는 `PeriodicTask`. 분산 잠금 없이 leader 선출로 한 번만 실행된다 |
| ✅ | `common/bgtask`: task id 를 발급하고 성공, 실패를 event 로 알린다 |
| ✅ | session 종료 경로: `mark_sessions_for_termination` 다음 tick 의 handler 가 `destroy_kernel` 을 부르고, 완료는 agent event 로 확인한다 |
| ➕ | sokovan 의 reconciler base 에서 session 스케줄링 어휘를 걷어낸다. base 는 sokovan 에 둔다 (3.2) |
| ➕ | 그 위에 **삭제 전용 lifecycle controller 와 coordinator** 를 만든다 |

reconciler base 는 지금 session 스케줄링 어휘에 묶여 있다: `SchedulingResult`, `HandlerPolicyResolver`,
`data/session/options` 의존.

### 2.5 RBAC scope 와 role

|  | 항목 |
| --- | --- |
| ✅ | `RBACEntityPurgerSpec` / `RBACEntityBatchPurgerSpec`: 행을 지우면 RBAC 그래프에 남긴 것도 지운다 |
| ➕ | scope 를 소유하는 엔티티(domain, project, user)를 purge 할 때 그 scope 에 자동으로 만든 role 과 매핑까지 지운다 (BA-6807, BA-6186) |

## 구현 설계

### 3.1 컬럼 셋: 업무 상태, soft delete, purge 진행

**삭제를 업무 status 값으로 표현하지 않는다.** 세 가지를 컬럼 셋에 나눠 둔다.

| 컬럼 | 답하는 질문 | 되돌릴 수 있는가 | 누가 쓰는가 | 어디에 두는가 |
| --- | --- | --- | --- | --- |
| `status` | 업무상 지금 어떤 상태인가 | 업무 규칙대로 | 그 엔티티의 업무 로직 | 업무 상태가 있는 엔티티. 엔티티마다 자기 enum |
| `deleted_at timestamptz NULL` | soft delete 됐는가 | 예 (`restore`) | soft delete, restore | soft delete 하는 모든 엔티티. 공통 Mixin |
| `purge_status` | purge 가 외부 자원을 정리하는 중인가, 실패했는가 | 아니오 | 삭제 coordinator | 외부 자원을 정리하는 엔티티. 공통 Mixin |

업무 상태와 삭제는 동시에 성립한다. `inactive` 인 채로 지운 user 가 있다. 한 enum 에 두면 restore 가
이전 상태를 잃는다. 지금 `user` 와 `role` 의 restore 가 늘 `active` 로 되돌리는 것이 그 결과다.
Kubernetes 는 삭제 요청(`metadata.deletionTimestamp`), 외부 정리(finalizer), 업무 상태(`status.phase`)를
다른 자리에 둔다. AIP-216 은 서로 배타적이지 않은 상태를 enum 하나에 두지 않는다.

### soft delete: `deleted_at`

- soft delete 여부는 `deleted_at IS NOT NULL` 하나로 판단한다. 같은 뜻의 boolean 을 따로 두지 않는다.
- `deleted_at` 은 `models/mixins/timestamp.py` 옆의 공통 Mixin 이 붙인다.
- soft delete 는 `deleted_at = now()`, restore 는 `deleted_at = NULL` 을 상수로 쓴다. 업무 `status` 는 건드리지
  않으므로 restore 뒤에 이전 상태가 남는다.
- soft delete 와 restore updater 는 이 Mixin 을 가진 행에 대해 하나씩 둔다. 엔티티마다 따로 만들지 않는다.

### purge 진행: `purge_status`

- 외부 자원을 정리해야 행을 지울 수 있는 엔티티에만 둔다: `user`, `project`, `domain`, `vfolder`, `image`.
- NOT NULL enum 이다. 기본값에 이름을 붙인다. 값은 기본값, `purging`, `purge-error` 셋이다.
- `purge_status` 가 기본값이 아니면 `deleted_at` 이 있어야 한다. CHECK 제약으로 강제한다.
- 정리가 끝나면 행을 지운다. 끝난 상태 값은 없다.
- 외부 정리가 없는 엔티티는 `purge_status` 가 없고 purge 가 요청 안에서 행을 지운다.

coordinator 는 엔티티 종류와 상관없이 `purge_status` 하나를 읽는다. 엔티티마다 다른 값(`purging`,
`PURGING`, `delete-ongoing`)을 맞추지 않는다.

### 엔티티별 처리

| 엔티티 | 업무 `status` | `deleted_at` | `purge_status` | 바뀌는 점 |
| --- | --- | --- | --- | --- |
| `user` | `active` / `inactive` / `before-verification` | 있음 | 있음 (session, endpoint, vfolder) | status 에서 `deleted`, `purging`, `purge-error` 를 뺀다 |
| `domain` | 없음 | 있음 | 있음 (session, RBAC) | status enum 과 `is_active` 를 지운다 |
| `project` | 없음 | 있음 | 있음 (session, endpoint, vfolder) | status enum 과 `is_active` 를 지운다 |
| `image` | 없음 | 있음 | 있음 (registry untag) | `ImageStatus` 를 지운다. registry 재스캔은 `deleted_at` 을 건드리지 않는다 |
| `vfolder` | `ready` … `error` | 있음 (`delete-pending` 을 대신함) | 있음 (`delete-ongoing` → `purging`, `delete-error` → `purge-error`) | `delete-complete` 를 지운다 |
| `role` | `active` / `inactive` | 있음 (이미 있음) | 없음 | status 에서 `deleted` 를 뺀다 |
| `artifact` | 없음 | 있음 (`availability` 를 대신함) | 없음 | `availability` 를 지운다 |
| `role_preset` | 없음 | 있음 (`deleted` 를 대신함) | 없음 | `deleted` 를 지운다 |
| session, kernel, deployment, route | 실행 lifecycle 그대로 | 없음 | 없음 | 없음 |
| keypair, resource group, container registry, storage namespace | `is_active` 는 켜고 끄는 업무 값 | 없음 | 없음 | 없음. soft delete 없이 purge 한다 |
| error log | `is_cleared` 는 확인 표시 | 없음 | 없음 | 없음 |

status 전이로 끝나는 lifecycle 은 soft delete 가 아니다. session 의 `TERMINATED`, deployment 의
`DESTROYED` 는 실행이 끝났다는 이력이고 되돌리지 않는다. 그 행은 retention 이 지운다.

### 읽기 규칙

| 읽기 | soft delete 된 행 |
| --- | --- |
| 목록 (search, scoped search) | 기본으로 뺀다. filter 의 `deletedAt` 조건으로 포함한다 |
| 단건 (get, `node(id:)`, bulk data loader) | 돌려준다 |
| 권한 | soft delete 는 권한 간선을 남긴다. purge 가 지운다 |
| 이름 unique 제약 | `WHERE deleted_at IS NULL` 부분 인덱스로 둔다. 같은 이름의 새 행이 생긴 뒤의 restore 는 integrity 오류가 되고 `integrity_error_checks` 가 도메인 오류로 바꾼다 |

### 전이

`purge_status` 가 `purging` 이나 `purge-error` 인 동안 그 엔티티의 `delete`, `restore`, `update` 는 거부한다.
정리 중인 것을 되살리거나 고칠 수 없다. `purge-error` 를 빠져나가는 길은 `force purge` 뿐이다 (3.5).

| 전이 | 계기 |
| --- | --- |
| `deleted_at`: NULL → 시각 | `delete` 요청 |
| `deleted_at`: 시각 → NULL | `restore` 요청 |
| `purge_status`: 기본값 → `purging` | `purge` 요청 (`deleted_at` 이 있어야 함) |
| 행 삭제 | 정리 완료 |
| `purge_status`: `purging` → `purge-error` | 재시도 소진 |
| 행 삭제 | `force purge` 요청 (3.5) |

### 3.2 reconciler base 는 sokovan 에 둔다

`sokovan/reconciler` 의 공통 ABC 는 `manager/reconciler` 로 옮기지 않는다. sokovan 이 tick 기반 엔티티
lifecycle 전반으로 넓어지고 삭제 lifecycle 도 그 안에 들어가므로 base 를 sokovan 밖으로 뺄 이유가 없다
(BA-7453).

삭제 coordinator 는 sokovan 안에서 그 base 를 상속한다. base 자체에 필요한 변경은 그대로다.

| 항목 | 변경 |
| --- | --- |
| `SchedulingResult` | 스케줄링과 무관한 중립 이름으로 일반화한다. 삭제 어휘로 바꾸지 않는다. 그러면 스케줄링이 쓸 수 없다 |
| `HandlerPolicyResolver` (`data/session/options` 에서 옴) | retry 횟수와 timeout 을 주는 인터페이스로 좁혀 base 로 옮긴다 |
| `ReconcilerStageMetadata.transitions` | 마지막 stage 의 성공이 status 전이가 아니라 **행 삭제**를 뜻할 수 있어야 한다 |
| `LockID` 와 분산 잠금 | 그대로. 잠금 없이 도는 stage 도 계속 허용한다 |
| `ReconcilerMetricObserver` | 그대로. label 이 어느 장치인지 담는다 |

`transitions` 가 status 타입 하나에 묶이므로 **엔티티 종류마다 stage, reconcile 타입, task spec 이 하나씩**
이다. 종류별 실패 격리와 종류별 주기가 함께 따라온다.

이력도 sokovan 을 따른다. 엔티티 종류마다 `ReconcileHistoryMixin` 을 두고 그 엔티티에 FK 를 건다. 시도,
거친 phase, 마지막 오류가 거기 남는다.

### 3.3 controller 와 coordinator

요청 쪽과 tick 쪽은 다르다. sokovan 의 분리를 따른다.

|  | lifecycle controller | lifecycle coordinator |
| --- | --- | --- |
| 부르는 곳 | 요청을 처리하는 서비스 | tick (event 또는 주기) |
| 하는 일 | 전이가 맞는지 확인하고 `purge_status` 를 `purging` 으로 바꾸고 needed-flag 를 세운다 | `purge_status` 가 `purging` 인 엔티티를 읽어 handler 를 한 단계 진행한다 |
| 선례 | `RouteController`: 메서드 하나 | `ReconcilerCoordinator`, `RouteCoordinator` |

**엔티티마다가 아니라 각각 하나다.** 엔티티마다 다른 것은 handler 뿐이다.

- `delete` 와 `restore` 는 이미 일반화돼 있다. `DeleteSingleEntityOpsAction` 과 `RestoreSingleEntityOpsAction` 이
  updater 하나를 받는 공통 base 다.
- purge 옵션은 모두 요청 시점에 DB 안에서 풀린다. `delegate_endpoint_ownership`, `purge_shared_vfolders`,
  `cascade_model_card` 는 소유를 넘기거나 참조 행을 지울 뿐 외부 자원을 건드리지 않는다.

coordinator 가 handler 에 묻는 것은 **한 단계 진행하고 진행 중, 완료, 실패를 알리라**는 것뿐이다. 삭제
어휘는 coordinator 계약에 넣지 않는다.

handler 는 `EntityType` 마다 하나이고 두 가지에 답한다.

| handler 가 답하는 것 | `user` 의 예 |
| --- | --- |
| 정리 stage 목록 | session → endpoint → vfolder → 연결 행 → RBAC role 과 scope |
| 엔티티 행을 지우는 방법 | 기존 `RBACEntityBatchPurger` |

**stage 등록이 어느 엔티티가 이 장치를 타는지 선언한다.** 경우는 셋이다.

|  | 동작 |
| --- | --- |
| stage 가 등록됨 | purge 요청이 `purge_status` 를 바꾸고 tick 이 진행한다 |
| stage 가 등록되지 않음 | 그대로. 요청이 기존 purger 로 그 자리에서 끝난다 |
| 탄다고 선언했지만 handler 가 없음 | 배선 오류. 요청을 거부한다 |

등록되지 않은 엔티티를 "행만 지운다"로 다루지 않는다. `ActionOperationType.PURGE` 를 선언한 엔티티가
열 개가 넘고 이 장치를 타는 것은 다섯이다. 행 삭제를 기본으로 두면 나머지가 정리 없이 조용히 지나가고,
등록을 빠뜨린 것과 정리할 것이 없는 것을 구분할 수 없다.

정리 stage 가 없는 handler 는 허용한다. 첫 tick 에 행 삭제로 끝나고, 그것이 선언한 뜻이다. 선언과
handler 등록이 어긋나면 registry sweep 테스트가 잡는다.

시작하는 길은 둘이다.

| 시작 | 보장 | 역할 |
| --- | --- | --- |
| 긴 주기 tick | 예 | 진행 중인 것을 모두 집는다. 정확성은 여기서 나온다 |
| needed-flag | 아니오 | `purge` 요청 직후 첫 단계를 앞당긴다 |

진행 상태는 엔티티 행에 있으므로 tick 사이에 들고 있는 것이 없다. 요청이 끊기거나 manager 가 재시작해도
다음 긴 주기 tick 이 집는다. `apply` 가 예외를 내면 `post_process` 는 돌지 않으므로 진행을 넘기는 일은
거기 두지 않는다.

### 3.4 정리 stage 계약

stage 는 세 가지에 답한다.

| 자리 | session stage 의 예 |
| --- | --- |
| 아직 terminal 이 아닌 것이 있는가 | `SessionStatus.terminal_statuses()` 밖의 session |
| terminal 로 보낸다 (멱등) | `mark_sessions_for_termination` |
| terminal 인 것을 지운다 | 기존 purger. kernel 행을 먼저, 순서대로 |

coordinator 는 tick 마다 stage 를 순서대로 돈다. 첫 자리가 비어 있지 않으면 둘째 자리를 실행하고 tick 을
끝낸다. 비어 있으면 셋째 자리를 실행하고 다음 stage 로 간다. 마지막 stage 가 끝나면 엔티티 행을 지운다.

이 세 자리는 삭제 handler 들이 공유하는 helper 이고 coordinator 계약이 아니다. 일반형은 **목표와 다른 것이
있는가 / 목표로 보낸다 / 도착한 것을 마무리한다**이고, terminal 기반 형태는 삭제용 특수화다.

retry 와 give-up 은 base 가 맡는다. `ReconcilerStage._classify_outcome` 은 `last.phase` 가 같을 때만 시도를
쌓으므로 **stage 이름을 phase 로 쓰면** 머무는 stage 는 give-up 으로 잡히고 다음으로 넘어가면 횟수가
초기화된다.

terminal 상태는 자원마다 이미 정의돼 있다.

| 자원 | terminal |
| --- | --- |
| session, kernel | `SessionStatus.terminal_statuses()`, `KernelStatus.terminal_statuses()` |
| routing, replica group | `RouteStatus.terminal_statuses()`, `ReplicaGroupLifecycle.terminal_statuses()` |
| endpoint | `EndpointLifecycle.DESTROYED` |

DB 에만 있는 연결 행과 딸린 행은 첫 자리가 늘 비어 있고 셋째 자리만 있다. 계약 하나가 두 종류를 다
덮는다.

**하위 자원이 그 자체로 관리 대상 엔티티면 소유자가 직접 지우지 않는다.** 소유자의 stage 는 첫 자리에서
그 행이 남았는지 묻고, 둘째 자리에서 그 행의 `purge_status` 를 `purging` 으로 바꾼다. 다 사라지면 나중
tick 에서 stage 를 통과한다. 소유자의 `purge` 는 하위 엔티티의 `delete` 가 아니라 `purge` 를 부르므로,
하위 엔티티는 soft delete 를 거치지 않고 `deleted_at` 과 `purge_status` 가 함께 쓰인다.

**kernel 은 어느 엔티티의 정리 stage 에도 직접 나오지 않는다.** kernel 행은 session stage 가 session 보다
먼저 지운다. 소유 엔티티는 session 만 가리킨다.

| 엔티티 | 정리 순서 |
| --- | --- |
| `user` | session → endpoint 해제 또는 위임 → vfolder → 연결 행과 딸린 행 → RBAC role 과 scope |
| `project` | session → endpoint 해제 → project vfolder → 연결 행 → RBAC role 과 scope |
| `domain` | session → 연결 행 → RBAC role 과 scope |
| `vfolder` | 초대와 권한 → storage 삭제 |
| `image` | registry untag (registry 가 요구할 때만) → alias |

각 stage 는 대상을 어느 컬럼으로 고르는지 스스로 밝힌다. session 은 각각 `domain_id`, `group_id`,
`user_uuid` 로 닿는다.

거부 조건은 지금의 `conflict_checks` 를 그대로 쓴다. 바뀌는 것은 평가 시점이다: 요청 시점이 아니라
**stage 실행 시점**.

registry untag 는 registry 타입이 요구할 때만 돌고 아니면 건너뛴다. 거부하지 않는다. untag 는 지금
Harbor 2 에만 구현돼 있다.

`image` 의 `purge_image`, `purge_images` 는 agent 디스크를 비우는 것이지 엔티티 삭제가 아니다. 이 BEP 는
행을 지우는 쪽만 다룬다.

### 3.5 force purge

정리를 기다리지 않고 행을 바로 지우는 탈출구다. **다섯 엔티티 모두**에 둔다.

|  | 기본 purge | force purge |
| --- | --- | --- |
| `purge_status` | `purging` 으로 바꿈 | 건드리지 않음 |
| 하위 자원 DB 행 | stage 마다 확인하며 지움 | 한 번에 지움 |
| 외부 자원 | 정리를 요청하고 완료를 확인함 | 정리를 **요청만 하고 확인하지 않음** |
| 엔티티 행 | 마지막 stage 뒤에 지움 | 바로 지움 |
| 먼저 soft delete | 필요 | 필요 없음 |

외부 자원이 실제로 정리됐는지는 보장하지 않는다. 그래서 기본 경로가 아니다.

지금의 동기 purge 가 바로 이 동작이다. 지금 코드는 그대로 force 경로로 옮기고, 새로 만드는 것은 요청 뒤에서
도는 기본 경로다.

**권한은 `purge` 와 같다.** purge 를 요청할 수 있으면 force purge 도 요청할 수 있다. force purge 가
`purge-error` 에서 다시 시도하는 길이기도 하다. 따로 재시도 API 를 두지 않는다.

### 3.6 외부 자원과의 일관성

**manager 가 조정한다.** 정리 stage 가 storage-proxy, appproxy, agent 호출을 직접 맡고 결과를 확인한 뒤
다음 stage 로 간다. 컴포넌트마다 자기 자원을 정리하고 event 로 알리는 방식은 쓰지 않는다. vfolder 삭제와
session 종료가 이미 manager 조정이고, 컴포넌트마다 새 정리 loop 를 세우지 않기 위해서다.

session 만 예외로 기존 종료 경로를 탄다. manager 가 종료를 표시하고 agent 가 event 로 확인하므로 정리
stage 는 첫 자리에서 그 확인을 볼 뿐이다.

DB 행과 외부 자원이 어긋나는 구간은 없앨 수 없다. 그 동안 `purge_status` 는 `purging` 으로 읽히고 재시도가
이어지며, 재시도를 다 쓰면 `purge-error` 로 드러난다.

### 3.7 API

| 연산 | 지금 | 이후 |
| --- | --- | --- |
| `delete` | domain, project 는 `is_active=False` 와 status, user, image 는 status | 다섯 모두 `deleted_at` 을 쓴다 |
| `restore` | 다섯 모두 있음. 업무 상태를 기본값으로 되돌림 | `deleted_at` 만 지운다. 업무 상태는 그대로. soft delete 된 상태에서만 허용 |
| `purge` | 모두 동기로 정리하고 끝나면 답함 | v2 는 기다리지 않는다 (아래). 기존 API 는 완료를 기다림 |
| `force purge` | vfolder 에만 있음 (`force_delete`) | 다섯 모두. 권한은 `purge` 와 같음 |

### v2 purge 응답

응답 시점에 Node 가 남아 있는지로 응답 모양이 정해진다. 어느 쪽인지는 엔티티가 `purge_status` 를 가졌는지로
정해지고, 같은 엔티티의 purge 가 경우에 따라 다르게 답하지 않는다.

| 항목 | 동기 purge (`purge_status` 없음) | 비동기 purge (`purge_status` 있음) |
| --- | --- | --- |
| 요청이 하는 일 | 행 삭제까지 끝낸다 | `purge_status` 를 `purging` 으로 바꾸고 끝낸다. 정리는 coordinator 가 tick 마다 진행한다 |
| GQL 응답 | `deletedId: ID!` 와 `entityId` 또는 `fieldId` | Node (`purgeStatus: PURGING`). `deletedId` 는 없다 |
| REST 응답 | 200, UUID | 202 Accepted, 엔티티 |
| 클라이언트 store | 응답의 `deletedId` 에 `@deleteEdge`, `@deleteRecord` 를 쓴다 | 응답으로 Node 를 갱신한다. 레코드는 아직 지우지 않는다 |
| 완료 확인 | 필요 없음 | `node(id:)` 가 null 을 돌려주면 끝 |
| 실패 | 요청이 오류로 끝난다 | 같은 Node 의 `purgeStatus: PURGE_ERROR` |
| 진행 중 다른 요청 | 없음 | update, delete, restore 는 409. purge 를 다시 보내면 같은 Node 를 돌려준다 |
| force purge | 없음 | 동기. GQL 은 `deletedId`, REST 와 DTO 는 UUID |

- global ID 는 GQL 층만 만든다. pydantic DTO 는 UUID 까지만 가진다.
- `deletedId` 는 Relay 의 `@deleteEdge`, `@deleteRecord` 가 받는 global ID 다. 행이 실제로 사라진 응답에만 준다.
- 목록에서 빠지는 시점은 따로 다루지 않는다. purge 는 soft delete 다음에 오고, soft delete 된 행은 기본 목록에서
  이미 빠져 있다.

### 기존 API 의 동기 계약

**기존 API(v1, legacy GQL)의 동기 계약은 바꾸지 않는다.** handler 가 controller 로 전이를 진행하고, 그
엔티티의 정리 완료를 구독하고, 기다렸다 답한다.

**기다림은 이 API handler 에만 있다.** 기존 호출자의 응답 계약을 지키기 위한 것이고, controller,
coordinator, 정리 stage 어디에도 기다림은 없다. 정리는 tick 마다 한 단계 진행하고, 그 단계가 끝나면 tick
도 끝난다. 다음 단계는 다음 tick 이 맡는다.

기다림의 상한은 **5분**이다. session 종료 확인처럼 여러 tick 에 걸치는 stage 는 그 안에 끝나지 않을 수
있다. 상한을 넘으면 timeout 으로 답하지만 **정리는 계속된다**.

완료는 `common/bgtask` 의 완료 event 로 구독한다. 클라이언트가 직접 구독할 task id 는 내보내지 않는다.

`deletedAt` 과 `purgeStatus` 는 엔티티의 필드로 내보낸다. join 이 필요 없고 값은 그 엔티티 타입의
스키마에만 나온다.

### 3.8 RBAC scope 와 role 의 연쇄 정리

scope 를 소유하는 엔티티를 purge 하면 그 scope 에 자동으로 만든 role 과 user 매핑을 같은 흐름의 stage
하나로 지운다 (BA-6807, BA-6186 흡수). BEP-1062 의 virtual scope 작업과 닿으므로 role 의 소유 정의는
BEP-1062 를 따르고, 이 BEP 는 정리가 **언제** 일어나는지만 정한다.

### 4. 이전과 호환

### 깨지는 것

| 항목 | 영향 |
| --- | --- |
| 업무 status 에서 삭제 값 제거 | DB 에는 저장하지 않는다. 기존 API 의 status 필드는 `deleted_at` 과 `purge_status` 를 업무 status 위에 덧씌워 계산한 값을 내보내고 deprecated 로 둔다. 새 필드 `deletedAt`, `purgeStatus` 를 더한다 |
| v2 `purge` 응답 | `purge_status` 가 있는 엔티티는 기다리지 않고 Node(GQL) 또는 202(REST)로 답한다 |
| 기존 API `purge` 응답 시간 | 계약은 같지만 5분을 넘으면 timeout 으로 답한다. 완료를 전제한 호출자는 그 경우를 다뤄야 한다 |
| `restore` 뒤의 업무 상태 | 기본값으로 되돌리지 않고 이전 상태가 남는다 |
| vfolder `delete-complete` | 없어진다. 정리 완료는 행 삭제다 |
| `domain`, `project` 의 `is_active` | `deleted_at` 에서 파생한 읽기 전용 값으로 남겼다가 호출자가 옮긴 뒤 지운다 |

### 이전

1. 공통 Mixin 으로 `deleted_at` 을 더하고, 업무 status 의 삭제 값으로 채운다. 이미 삭제된 행은 이전 업무 상태를
  알 수 없으므로 업무 status 를 기본값(`active`, `ready`)으로 옮긴다.
2. 다섯 엔티티에 `purge_status` 를 더하고 기본값으로 채운다. vfolder 의 `delete-ongoing` 은 `purging`,
  `delete-error` 는 `purge-error` 로 옮긴다. 엔티티 종류마다 reconcile 이력 테이블을 더한다.
3. 인증 게이트가 `deleted_at` 과 `purge_status` 를 보게 한 뒤에 status 에서 삭제 값을 뺀다. **순서를 거꾸로
  하면 soft delete 된 user 가 자기 키로 API 를 계속 부를 수 있다.**
4. `delete-complete` 에 남은 vfolder 행은 정리를 거쳐 지운다. vfolder 의 `performing`, `cloning`, `mounted`
  가 같은 enum 에 있는 것은 이 BEP 범위 밖이다.
5. `is_active` 와 status 의 삭제 값을 읽는 호출자를 `deleted_at`, `purge_status` 로 옮기고 지운다.

조사 중 발견한 결함: vfolder 삭제 실패 event 가 `delete-ongoing` 인 행에 닿지 않아 `delete-error` 가
기록되지 않는다 (`repositories/vfolder/deletion.py` 의 `update_vfolder_status` 가 `delete-pending` 인 행만
갱신). `purge_status` 로 옮기면서 함께 고친다.

### 진행 중인 작업

BA-7443, BA-7444, BA-7449 의 purger `models/` 이전은 **계획대로 계속한다.** 29개 중 연결 행 purger 는 이전
뒤에도 모양이 같으므로 재작업이 아니다. 외부 자원이 뒤에 있는 purger 만 이 BEP 의 정리 stage 로 옮긴다.

### 5. 구현 계획

| 단계 | 내용 |
| --- | --- |
| 1 | `deleted_at` 공통 Mixin 과 soft delete, restore updater 를 만들고 엔티티를 옮긴다. 업무 status 에서 삭제 값을 빼고 기존 API 의 status 는 파생값으로 내보낸다 |
| 2 | 인증 게이트가 `deleted_at`, `purge_status` 를 보게 한다. 1 의 status 정리보다 먼저 들어간다 |
| 3 | 지금의 동기 purge 를 `force purge` 로 옮기고 다섯 엔티티에 연다. 동작은 같다 |
| 4 | sokovan reconciler base 에서 스케줄링 어휘를 떼어 낸다. base 는 sokovan 에 둔다 |
| 5 | 다섯 엔티티에 `purge_status` 와 이력 테이블을 더한다 |
| 6 | controller, coordinator, 정리 stage 계약, registry sweep 테스트를 만든다. stage 가 가장 짧은 `domain` handler 로 흐름을 확인한다 |
| 7 | `vfolder`, `image`, `project`, `user` handler 를 붙이고 서비스의 절차 코드를 걷어낸다 |
| 8 | RBAC role 과 scope 연쇄 stage 를 더한다 (BA-6807, BA-6186) |
| 9 | v2 purge 를 비동기 응답(Node, 202)으로 바꾸고, 기존 API 의 purge handler 는 완료 구독으로 바꾼다 |
| 10 | `is_active` 와 status 삭제 값 호출자를 옮기고 지운다 |

## 결정 요약

| ID | 날짜 | 결정 | 이유 | 검토한 대안 |
| --- | --- | --- | --- | --- |
| D1 | 2026-10-20 | 업무 상태(`status`), soft delete(`deleted_at`), purge 진행(`purge_status`)을 컬럼 셋으로 나눈다. 업무 status 에 삭제 값을 두지 않는다. | 업무 상태와 삭제는 동시에 성립하고, 한 enum 에 두면 restore 가 이전 상태를 잃는다. coordinator 가 엔티티와 상관없이 `purge_status` 하나를 읽는다. | 엔티티마다 status enum 하나에 삭제와 purge 진행 값을 넣음 (이 BEP 의 이전 안). |
| D2 | 2026-10-20 | soft delete 는 nullable `deleted_at` 하나로 판단하고 공통 Mixin 이 붙인다. | 삭제 시각이 retention 기준이 된다. boolean 을 함께 두면 두 값이 어긋날 수 있다. | `deleted` boolean, boolean 과 시각 둘 다. |
| D3 | 2026-10-20 | `purge_status` 는 외부 자원을 정리하는 엔티티에만 두는 NOT NULL enum 이고 기본값에 이름을 붙인다. | 평소 값에 이름이 없으면 행이 정상인지 구분할 수 없다. | nullable `purge_status`. |
| D4 | 2026-10-20 | `purge_status` 가 있는 엔티티의 v2 purge 는 기다리지 않고 Node(GQL) 또는 202 와 엔티티(REST)로 답한다. 없는 엔티티와 force purge 는 동기로 `deletedId`(GQL) 또는 UUID 를 준다. | 응답 시점에 남아 있는 Node 를 지웠다고 답하지 않는다. `deletedId` 는 Relay store 에서 레코드를 빼는 데 쓰이므로 행이 사라졌을 때만 준다. | v2 도 완료를 기다렸다 `deletedId` 로 답함. |

## 열린 질문

| ID | 질문 |
| --- | --- |
| Q1 | `purge_status` 의 기본값 이름. |

## 참고

- [BEP-1062](BEP-1062-virtual-scope-rbac.md): Virtual Scope RBAC Ownership Model. role 의 소유 정의
- [BEP-1063](BEP-1063-db-record-retention.md): DB Record Retention Management. LeaderCron 주기 sweep 의 선례
- [BEP-1054](BEP-1054-reconciler-based-idle-checker.md): Reconciler Based Idle Checker. reconciler base 를 쓰는 선례
- [BEP-1061](BEP-1061-agent-kernel-lifecycle.md): Agent Kernel Lifecycle Structuring. kernel 종료 확인 경로
- [Kubernetes Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/): 삭제 요청, 외부 정리, 업무 상태의 분리
- [AIP-164 Soft delete](https://google.aip.dev/164), [AIP-216 States](https://google.aip.dev/216)

<!-- generated by hejo bep render from hejo report bep/entity-lifecycle-deletion (sha256 b9c917b892c57d87); edit the source, or hejo bep import after editing here -->
