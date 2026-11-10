# DB 기록 보존 관리

## 관련 이슈

- Epic **BA-6924**, 이 BEP **BA-6925**
- 인접(상호 참조만 하고 여기서 다루지 않는다): **BA-4383**(아티팩트 저장소 보존), **BA-3037**(사용하지 않는 docker image GC)

## 1. 목표

Backend.AI 는 이력 row 를 계속 쌓는다. event/감사/로그인 로그, reconcile 과 스케줄링 이력, 종료된 세션과 커널, 파괴된 deployment 기록, 사용량 집계가 그렇다. **그 증가를 제한하는 통일된 방법이 없다.** 지금은 부분적인 장치가 둘뿐이다. `error_logs` 테이블 하나를 하드코딩된 etcd 키 하나로 스윕하는 전용 `GlobalTimer`, 그리고 직접 작성한 고정 목록을 `clear-history` CLI 로 수동 삭제하는 방식이다. 나머지는 한도 없이 증가한다.

이 BEP 는 **범용 보존 계층**을 정의한다. superadmin 이 **데이터 카테고리마다** 보존 기간을 선언하면 manager 가 그 기간이 지난 기록을 배치로, 참조 안전하게 주기적으로 purge 한다. 목적은 **무한정 쌓이는 DB 기록의 시스템 수준 정리**다.

**비목표:**

- **스코프별(project/domain/user) 보존.** 목적은 시스템 전체 정리이고 정책은 **카테고리마다 전역으로** 적용된다. 지금 스코프별 요구가 없고, 성숙한 스케줄러도 purge 를 전역으로 둔다(Slurm `slurmdbd.conf` 의 `Purge*After` 는 계정별이 아니라 `slurmdbd` 별이다). 구체적 필요가 생기면 나중에 스코프를 추가할 수 있다.
- **삭제 표시 / 아카이브.** 모든 카테고리가 영구 삭제한다. 청구 데이터는 아카이브가 아니라 긴 기본 기간으로 보호한다.
- **Redis / DB 가 아닌 저장소 정리.** 이 BEP 는 **DB 기록만** 다룬다. Redis 통계 등 DB 밖 저장소는 별개 관심사이고 범위 밖이다(기존 CLI 가 계속 맡는다).
- 아티팩트와 오브젝트 스토리지 보존(BA-4383), docker image GC(BA-3037). 기반이 다르므로 따로 추적한다.
- **`vfolders` / `images` / `service_catalog` / `artifacts` 정리.** 각각 사정이 다르므로(전용 타임스탬프가 없음, 차단하는 `RESTRICT` FK, heartbeat 나이로 스윕하는 편이 나은 실행 중 registry, 별도 epic) 여기서는 범위 밖이고 따로 다룬다.
- **`VACUUM FULL` 자동화.** 테이블을 잠그므로 수동 CLI 작업으로 남긴다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 2.1 정책 저장

| | 항목 |
|---|---|
| ✅ | `error_logs` 보존은 etcd 키 `config/logs/error/retention` 하나다(기본 90d) |
| ➕ | `retention_policies` DB 테이블, **카테고리마다 row 하나**. 보존 기간 + 활성 여부(스윕 주기와 배치 크기는 서버 설정에 둔다) |

### 2.2 대상 범위 (카탈로그)

| | 항목 |
|---|---|
| ✅ | `error_logs`(timer) + 종료된 세션과 커널 및 `error_logs`(CLI) |
| ➕ | 도메인 **카테고리** 여덟 개(`logs`/`login`/`reconcile_history`/`roles_invitations`/`deployments`/`sessions`/`usage_records`/`usage_buckets`)와 카테고리마다 코드에 담은 참조 안전 삭제 절차 |

### 2.3 스윕 실행

| | 항목 |
|---|---|
| ✅ | `GlobalTimer` + `LOCKID_LOG_CLEANUP_TIMER` 분산 잠금 → `DoLogCleanupEvent` handler. 그리고 수동 `clear-history` CLI |
| ➕ | manager 의 **`LeaderCron`** 에 두는 `PeriodicTask` 하나. tick 마다 활성 정책을 모두 처리하는 전역 주기 하나. 배치 삭제 |

### 2.4 관리 표면

| | 항목 |
|---|---|
| ✅ | 없음. etcd 를 직접 편집하거나 CLI 를 직접 실행한다 |
| ➕ | `retention_policies` 에 대한 **superadmin** v2 GraphQL + REST CRUD. `UserRole.SUPERADMIN` 역할 게이트로 인가한다(RBAC 스코프 해석이 아니다) |

### 2.5 CLI 와 공간 확보

| | 항목 |
|---|---|
| ✅ | `clear-history` 는 종료된 세션과 커널, `error_logs`, Redis 통계를 삭제한 뒤 `VACUUM` / `VACUUM FULL` 을 실행한다 |
| ➕ | 반복 DB 삭제는 정책으로 옮긴다. CLI 는 수동 강제 스윕과 `VACUUM FULL` 담당으로 남기고, 스윕은 autovacuum 에 맡긴다 |

## 3. 구현 설계

**핵심 흐름:** leader 에서만 실행되는 주기 task 가 활성 정책을 읽는다 → repository 로 정책의 **카테고리** 삭제를 해석한다 → `now − retention_period` 보다 오래된 row 를 **배치로, 배치마다 커밋하며** 삭제한다 → `last_swept_at` 을 기록한다. 비워진 공간은 autovacuum 이 회수한다.

### (a) 정책 저장: `retention_policies`

보존 정책은 superadmin 이 실행 중에 카테고리마다 CRUD 하는 **데이터**다. 감사와 조회가 필요하다. 검토한 대안은 다음과 같다.

| 대안 | 사용하지 않는 이유 |
|---|---|
| etcd 확장(에러 보존 선례) | 평평한 key-value 라 카테고리 여럿을 효율적으로 열거할 수 없고 감사도 타입 검증도 없다. 키 하나에는 맞지만 카탈로그에는 맞지 않는다 |
| **새 `retention_policies` DB 테이블(채택)** | 조회, 감사, 표준 v2 CRUD 가 된다 |

(서버 설정은 여기서 대안이 아니다. 서버 설정은 `batch_size` / `sweep_interval` 같은 **정적인 운영 값**을 담고, 정책은 실행 중에 admin 이 CRUD 하는 데이터다.)

이 설계는 **도메인 카테고리마다 그 테이블을 어떻게 정리하는가를 정하는 일**이다. 정리 방식(경계 column + 참조 안전 삭제 절차)은 **테이블 성질에 따라 코드에 고정되고**(b), 정책 row 는 admin 이 조정하는 값(`retention_period`, `enabled`)만 담는다. `category` 는 정책 row 를 코드 쪽 정리에 잇는 **식별자**일 뿐이고, 확장 가능한 판별자나 spec 추상화가 아니다(idle checker 장치와 무관하다).

| column | 타입 | 설명 |
|---|---|---|
| `id` | UUID, PK | 정책 식별자 |
| `category` | string, unique | 정리 대상 식별자(`RetentionCategory` enum 값, 문자열로 저장). 코드 카탈로그로 검증하고 모르는 카테고리는 거부한다. enum 은 테이블 참조를 담지 않는다 |
| `retention_period` | interval | 기간 기준. `now − retention_period` 보다 오래된 row 가 대상이다 |
| `enabled` | bool | 이 정책을 스윕에서 처리하는지 |
| `last_swept_at` | timestamptz, nullable | **읽기 전용** 관측 필드. 이 정책을 마지막으로 스윕한 시각(게이트가 아니다) |
| `created_at` / `updated_at` | timestamptz | 감사 타임스탬프 |

`category` 에 unique 를 건다. 카테고리마다 정책 하나다. 마이그레이션이 카탈로그 카테고리마다 보수적 기본값으로 row 하나를 미리 저장하고, 이후 admin 이 조정한다. 정책이 없거나 비활성이면 "이 카테고리는 스윕하지 않는다"는 뜻이다.

**사용자에게 보이는 값은 `retention_period` 와 `enabled` 로 줄인다.** 스윕 주기와 배치 크기는 **서버 설정**(manager 통합 설정의 `retention` 절, 사용자에게 노출하지 않는다)에 둔다.

| 서버 설정 | 뜻 |
|---|---|
| `retention.sweep_interval` | `PeriodicTask` tick 주기(전역 값 하나). tick 마다 활성 정책을 모두 처리한다 |
| `retention.batch_size` | 배치마다 삭제하는 row 수(잠금 시간을 제한한다) |
| `retention.per_tick_budget`(선택) | tick 마다 삭제하는 총 row 수 상한 |

- **`batch_size` 를 정책 필드로 두지 않는 이유:** 성능과 안전 값이지 보존 결정이 아니다. 사용자가 예를 들어 `1` 로 두면 삭제가 영영 따라잡지 못하는 위험이 있다. → 서버 설정.
- **`sweep_interval` 을 정책별로 두지 않는 이유:** 스윕 주기는 운영 조정이지 카테고리별 보존 결정이 아니다(의미 있는 정책 값은 `retention_period` 뿐이다). task 는 tick 하나로 실행되고 tick 마다 활성 정책을 모두 처리하므로 정책별 게이트가 필요 없다. → 서버 설정 하나.

### (b) 대상 카탈로그: 도메인 카테고리와 안전 삭제

보존 대상은 **도메인 카테고리**로 묶는다. 카테고리마다 정리 방식(경계 column + 참조 안전 삭제 절차)은 **코드에 고정**되고 테이블 성질이 이끌며, 정책 row 는 `retention_period` / `enabled` 만 담는다. 카테고리 하나가 테이블 여럿에 걸칠 수 있다. 경계 column 을 공유하는 테이블은 **Mixin** 으로 함께 처리하고, 경계가 다른 테이블은 카테고리를 공유하되 각자 spec 을 둔다(`retention_period` 는 공유한다).

**경계 column 원칙:** 경계는 **"마지막 의미 있는 변경" 타임스탬프**여야 최근에 손댄 row 가 purge 되지 않는다. 제자리에서 변경되는 테이블은 `updated_at`, 추가만 되는 테이블은 `created_at`, 수명 주기 기록은 종료 전이 시각(`terminated_at` / `destroyed_at` / `invalidated_at` / `expires_at`)에 종료 상태 필터를 추가한다.

**카테고리 이름:** 식별자는 사용자에게 보이므로(superadmin API) 외부 도메인 이름을 사용한다(물리 테이블 `endpoints` → 도메인 `deployments`).

**여덟 카테고리:**

| 카테고리 | 테이블 | 경계 | 기본값 | 처리 |
|---|---|---|---|---|
| `logs` | `event_logs`, `audit_logs`, `error_logs` | `created_at` | 1년 | 공통 column Mixin(묶음). `error_logs` 는 경계를 넘은 row 를 모두 삭제한다 |
| `login` | `login_history`, `login_sessions` | login_history `created_at`; login_sessions `invalidated_at` + `{INVALIDATED, REVOKED}` | 1년 | 도메인 묶음, 테이블별 spec |
| `reconcile_history` | `session_scheduling_history`, `kernel_scheduling_history`, `deployment_history`, `route_history`, `replica_group_history` | `updated_at`(`attempts++` merge) | 1년 | 공통 column Mixin(묶음) |
| `roles_invitations` | `roles`, `vfolder_invitations`, `entity_shares` | roles `deleted_at`+`DELETED`; `entity_shares` 는 둘로 나뉜다. 아직 기다리는 제안은 지난 `expires_at`, 끝난 것은 종료 상태 + `updated_at` | 1년 | 도메인 묶음(초대 통합), 테이블별 spec |
| `deployments` | `endpoints`(파괴됨), `endpoint_tokens`(만료됨) | endpoints `DESTROYED`+`destroyed_at`; tokens `expires_at` | 1년 | 도메인 묶음. endpoints 는 전용, tokens 는 단순 |
| `sessions` | `sessions`(+ `kernels`) | session/kernel `DEAD_*_STATUSES {TERMINATED, CANCELLED}` + `terminated_at` | 1년 | 전용(순서 있는 삭제) |
| `usage_records` | `kernel_usage_records` | `period_end` | **90일** | 단순. 원본 기록을 버킷으로 집계하므로 짧게 둔다 |
| `usage_buckets` | `domain/project/user_usage_buckets`(+ `usage_bucket_entries`) | `period_end` | 2년 | 전용(entries → buckets) |

**전용 절차:**

- `sessions`: `kernels` 먼저 삭제(`sessions.id` 에서 kernels 로 cascade 가 없다) → `sessions`. `session_dependencies` / `vfolder_attachment` 는 cascade 된다. `routings.session` 은 `ON DELETE RESTRICT` 이므로 남은 routing 이 없는 session 으로 거른다. 정본 `DEAD_SESSION_STATUSES` / `DEAD_KERNEL_STATUSES` frozenset 을 재사용한다(`models/session/row.py`, `models/kernel/row.py`).
- `deployments`(endpoints): 자식이 cascade 된다(`replica_groups`, `routings`, `endpoint_auto_scaling_rules`, `deployment_policies`). FK 가 없는 GUID 자식(`deployment_revisions`)은 endpoint id 로 삭제한다. `routings`(`TERMINATED`) / `replica_groups`(`DRAINED`)는 종료 타임스탬프가 없어 endpoint cascade 로 연쇄 purge 한다. `endpoint_tokens` 는 같은 카테고리에서 `expires_at` 으로 정리한다.
- `usage_buckets`: `usage_bucket_entries` 는 타임스탬프도 FK 도 없다. purge 한 버킷 id 로 entries 를 먼저 삭제하고 그다음 버킷을 삭제한다.

**프록시 타임스탬프 주의:** 역할과 vfolder 초대에는 전용 종료 타임스탬프가 없어 `updated_at` / `modified_at` 이 유예 경계가 된다. 종료 상태 뒤에는 변경이 없으므로 대략 안전하지만 정밀하지는 않다.

**보류 / 제외**(비목표): `vfolders`(`DELETE_COMPLETE`, `model_cards.vfolder` `RESTRICT` 가 차단할 수 있다), `images`(`DELETED`, 전용 타임스탬프가 없어 `deleted_at` 이 필요하다), `service_catalog`(`DEREGISTERED`, heartbeat 나이로 스윕하는 편이 낫다), `artifacts`(`DELETED`, BA-4383 범위), `artifact_revisions`(`FAILED`/`REJECTED` 는 재시도할 수 있다), `agents`(`kernels.agent` FK 에 cascade 가 없다), `users` / `keypairs`(되돌릴 수 있고 참조가 넓다).

**기본 보존 seed**(모두 admin 이 조정할 수 있다):

| 카테고리 | 기본값 | 근거 |
|---|---|---|
| `logs`, `login`, `reconcile_history`, `roles_invitations`, `deployments`, `sessions` | **1년** | LTS 지원 기간 |
| `usage_records` | **90일** | 원본 기록을 버킷으로 집계하므로 짧게 둔다 |
| `usage_buckets` | **2년** | 청구 대사, 규정 준수 |

### (c) 스윕: LeaderCron 주기 task

스윕은 manager 의 **`LeaderCron`** 에서 `PeriodicTask` 하나로 실행되고, `GlobalTimer` + 분산 잠금 경로도 sokovan reconciler 도 아니다.

- **leader 선출이 분산 잠금을 대신한다.** `LeaderCron` 은 선출된 leader 에서만 task 를 실행하므로(`ValkeyLeaderElection`) 단일 실행이 보장된다. `LOCKID_LOG_CLEANUP_TIMER` 가 더는 필요 없다.
- **reconciler 가 아니다.** 보존에는 엔티티별 수렴도, 재시도할 결과도, tick 사이 상태도 없다. 주기적 배치 삭제다.

tick 마다 **활성 정책을 모두** 처리한다. 카테고리마다 `threshold = now − retention_period` 를 계산하고 `retention.batch_size` 청크로 `retention.per_tick_budget` 까지 오래된 row 를 삭제한 뒤 `last_swept_at` 을 기록한다.

**삭제 의미(구현 계약):** 삭제는 repository 의 공유 write ops 위 배치 purge(기존 `BatchPurger` 프레임워크)로 하고 연결 지점에서 raw SQL 을 사용하지 않는다. `category → tables` 매핑은 보존 repository 하나 안에 둔다(모듈 전역 없음). 공통 column 테이블은 Mixin 을 공유하고, 여러 테이블 카테고리는 순서 있는 purge 를 실행한다. 삭제는 pagination 이 아니라 **청크 기반(삭제하며 진행)** 이다. 삭제된 row 는 조건 집합에서 빠지므로 `batch_size` 청크마다 cursor 나 offset 없이 자연히 진행한다. 각 청크는 **자기 트랜잭션으로 커밋**한다(짧은 잠금, 재개 가능, `per_tick_budget` 준수). 여러 테이블 카테고리에서 한 배치의 관련 삭제는 그 트랜잭션 안에서 원자적이고, 다른 카테고리는 독립 트랜잭션으로 실행한다. 공간은 autovacuum 이 회수하고 스윕은 `VACUUM` 을 실행하지 않는다.

**장시간 실행 안전.** 기존 LeaderCron task 와 달리 이 스윕은 오래 실행될 수 있지만 배치 설계가 그것을 가둔다. 별도 asyncio task(event loop 나 다른 task 를 차단하지 않는다), 배치별 커밋(긴 트랜잭션 없음), 같은 leader 에서 재진입 없음, 멱등 삭제(실행 중 leader 가 교체되면 최대 무해한 겹침만 생긴다). `per_tick_budget` 이 밀린 양을 tick 들로 나누어 한 번의 실행이 길어지지 않게 한다.

### (d) Admin API: superadmin v2 CRUD

`retention_policies` 는 전체 계층(REST v2 + Strawberry GraphQL + 공유 adapter + SDK v2 + CLI v2)으로 노출하는 v2 엔티티이고 **superadmin 전용**이며 표준 6개 연산을 갖는다. `category` 는 카탈로그로 검증한다. 카테고리 집합이 고정이므로 흔한 연산은 seed row 에 대한 `update`(기간 조정, 활성 여부 변경)이다. 조회는 `last_swept_at` 을 노출한다.

**인가는 RBAC 스코프 해석이 아니라 superadmin 역할 게이트다.** `retention_policies` 는 어느 스코프에도 속하지 않는 전역 단일 설정이고, RBAC 스코프 계층은 `ScopeType.GLOBAL` / `GLOBAL_SCOPE_ID` 를 deprecated 로 두었다. 그래서 이 엔티티는 **RBAC `EntityType`/`ScopeType` 으로 등록하지 않고 가상 스코프에도 연결하지 않는다.** 다른 전역 superadmin 전용 연산(resource policy/preset 변경, agent 검색)과 같이 `UserRole.SUPERADMIN` 역할 게이트로 인가한다. 스코프가 없으므로 service 계층에 스코프 해석 부담이 없고 `scope_entity_combinations` 항목도 없다.

### (e) `clear-history` CLI: 반복 작업을 흡수하고 탈출구는 남긴다

| 책임 | 새 위치 |
|---|---|
| 반복 `error_logs` 삭제(옛 etcd timer) | `logs` 정책(error_logs 포함). 자동 스윕. `GlobalTimer` + `DoLogCleanupEvent` 경로와 etcd 키는 폐기한다(기본 1년) |
| 반복 종료 세션/커널 **DB** 삭제 | `sessions` 정책. 자동 스윕(DB 기록만) |
| 종료 커널 Redis 통계 삭제 | **범위 밖**(DB 전용). Redis 는 별도 저장소이고 CLI 가 계속 맡는다 |
| 일회성 강제 정리 | CLI 유지. 카테고리의 즉시 스윕을 실행한다 |
| `VACUUM` / `VACUUM FULL` | CLI 유지. 자동 스윕이 실행하지 않는 방해가 큰 공간 확보 |

CLI 는 **제거하지 않는다.** 자동 정책 계층 위의 수동 탈출구가 된다.

### (f) 마이그레이션 / 호환성

- 새 테이블 `retention_policies` 를 만들고 카탈로그 카테고리마다 위 기본값으로 row 하나를 미리 저장한다.
- `error_logs` 의 `GlobalTimer` 의존과 `DoLogCleanupEvent` handler 를 폐기하고 `LOCKID_LOG_CLEANUP_TIMER` 를 비운다. etcd 키 `config/logs/error/retention` 을 폐기한다(`error_logs` 는 `logs` 카테고리에서 기본 1년이다).
- `clear-history` CLI 표면에 breaking change 는 없다. 반복 DB 역할은 대체되지만 명령은 계속 실행된다.

## 4. 결정 요약

| 결정 | 내용 |
|---|---|
| 저장 | 새 `retention_policies` DB 테이블(etcd 아님). 정책은 조회, 감사, 표준 v2 CRUD 가 필요한 실행 중 admin CRUD 데이터다 |
| 키 | `category` 로 키를 잡는 평평한 테이블 하나. 카테고리마다 전역 정책 하나 |
| 범위 | **스코프별(project/domain/user)은 비목표.** 시스템 전체 정리이고 카테고리별 전역 정책이다. Slurm 도 purge 를 전역으로 둔다 |
| 로직 위치 | admin 이 조정하는 `retention_period` / `enabled` 는 정책 row 에, 경계 column 과 삭제 절차는 **테이블 성질에 따라 코드에 고정**(확장 가능한 판별자나 spec 추상화가 아니다) |
| 카테고리 | 도메인 기준 여덟: `logs`, `login`, `reconcile_history`, `roles_invitations`, `deployments`, `sessions`, `usage_records`, `usage_buckets`. 공통 column 테이블은 Mixin 을 공유하고 나머지는 공유 `retention_period` 아래 테이블별 spec 을 사용한다 |
| 경계 column | "마지막 의미 있는 변경". 제자리 변경 → `updated_at`, 추가만 → `created_at`, 수명 주기 → 종료 전이 시각 + 종료 상태. audit/error 에는 `updated_at` 이 없어 `created_at` |
| 스윕 | `LeaderCron` 의 `PeriodicTask`. `GlobalTimer`+잠금도 reconciler 도 아니다. repository `BatchPurger` 로 청크 기반(삭제하며 진행)이고 배치마다 커밋한다. 카테고리는 독립 트랜잭션 |
| 정책 값 | 사용자에게 보이는 값은 `retention_period` / `enabled` 뿐이다. `sweep_interval` / `batch_size` 는 서버 설정이다. batch=1 같은 위험을 피한다. `last_swept_at` 은 읽기 전용 관측 값이다 |
| 기본값 | 대부분 **1년(LTS)**. `usage_records` **90일**(원본을 버킷으로 집계), `usage_buckets` **2년**. 모두 admin 이 조정한다 |
| 저장소 범위 | **DB 기록만.** Redis 등 DB 밖 정리는 범위 밖이고 CLI 가 맡는다 |
| 청구 | 긴 기본 기간을 둔 영구 삭제. 삭제 표시나 아카이브가 아니다 |
| 공간 확보 | 자동 스윕은 `VACUUM` 을 실행하지 않는다. `VACUUM FULL` 은 CLI 에 남는다 |
| 인가 | `UserRole.SUPERADMIN` 역할 게이트. RBAC `EntityType`/`ScopeType` 이 아니고 가상 스코프에 연결하지 않는다. 전역 단일 설정은 붙일 스코프가 없다 |

## 5. 열린 질문

- RBAC action 프레임워크에서 전역 superadmin 전용 action 을 일급으로 다루는 일. RBAC 프레임워크 수준의 **별도 이슈**로 나눈다(이 BEP 는 기존 `UserRole.SUPERADMIN` 게이트를 사용하므로 진행을 차단하지 않는다).
- 구체적 서버 설정 기본값(`retention.sweep_interval`, `retention.batch_size`, `retention.per_tick_budget`). 구현할 때 정한다.

## 6. 참고

- `dependencies/processing/log_cleanup_timer.py`, `event_dispatcher/handlers/log_cleanup.py`, `cli/__main__.py::clear_history`
- `common/leader/tasks/leader_cron.py`, `dependencies/orchestration/leader_election.py`
- `repositories/base/purger.py`(`BatchPurger`), `repositories/ops/base/provider.py`(`WriteOps.batch_purge`)
- `models/endpoint/row.py`(`destroyed_at` / `lifecycle_stage`), `models/session/row.py` & `models/kernel/row.py`(`DEAD_*_STATUSES`)
- 선례: Slurm `slurmdbd.conf` 의 `Purge*After` / `Archive*`. 카테고리별 전역 purge([docs](https://slurm.schedmd.com/slurmdbd.conf.html))
- [BEP-1054](BEP-1054-reconciler-based-idle-checker.md)(reconciler idle checker)
