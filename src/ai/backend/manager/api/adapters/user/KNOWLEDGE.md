---
name: user-adapter-scenarios
type: reference
description: what the user adapter and the login session and login history adapters it owns guarantee, as gates, graph position, answers and a scenario table
scope: src/ai/backend/manager/api/adapters/user
keywords: [user, keypair, login session, login history, scenario, adapter, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-15
status: draft
---
# 사용자 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 로그인 세션과 로그인 이력은 어댑터가 따로 있지만
사용자가 소유하는 필드이므로 이 문서에 둔다.

경로는 따로 적지 않으면 `src/ai/backend/manager/` 기준이다. 조사 기준은 main `a42719cb67`이다.
BA-7885(배정과 역할 읽기를 스코프로)와 BA-7889(사용자 일괄 읽기를 partial bulk get으로)가 반영된
배선이다.

## 1. 어댑터가 제공하는 것

`./backend.ai mgr ops list --concern organization`은 97건을 낸다. 사용자 46, 도메인 16, 프로젝트 15,
auth 7, 필드는 error_log 4, keypair 4, login_session 3, login_history 2다. BA-7799 작성 시점의
96건에서 프로젝트 한 건이 늘었다.

### 사용자 어댑터 (`api/adapters/user/adapter.py`)

| 메서드 | 줄 | 요청 | 답 | 요청 외 인자 | 거치는 액션 |
|---|---|---|---|---|---|
| resolve_domain_id | 217 | — | `DomainID` | 도메인 이름 | `LookupDomainAction` |
| batch_load_by_ids | 224 | — | `list[UserNode \| Exception \| None]` | 사용자 id 목록 | `BulkGetUsersAction` |
| gql_admin_search | 240 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | — | `GlobalSearchUsersAction` |
| gql_search_by_domain | 267 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | 도메인 이름 | `LookupDomainAction`, `ScopedSearchUsersAction` |
| gql_search_by_project | 300 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | 프로젝트 id | `ScopedSearchUsersAction` |
| admin_search | 335 | `SearchUsersRequest` | `SearchUsersPayload` | — | `GlobalSearchUsersAction` |
| scoped_search | 362 | `ScopedSearchUsersInput` | `SearchUsersPayload` | — | `ScopedSearchUsersAction` |
| gql_scoped_search | 388 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | `UserScope` | `ScopedSearchUsersAction` |
| domain_search | 418 | `SearchUsersRequest` | `SearchUsersPayload` | 도메인 이름 | `LookupDomainAction`, `ScopedSearchUsersAction` |
| project_search | 440 | `SearchUsersRequest` | `SearchUsersPayload` | 프로젝트 id | `ScopedSearchUsersAction` |
| role_search | 462 | `SearchUsersRequest` | `SearchUsersPayload` | 역할 id | `GlobalSearchUsersAction` |
| get | 482 | — | `UserPayload` | 사용자 id | `GetUserAction` |
| create_user | 489 | `CreateUserInput` | `CreateUserPayload` | — | `LookupDomainAction`, `CreateUserAction` |
| update_user_by_id | 525 | `UpdateUserInput` | `UpdateUserPayload` | 사용자 id | `UpdateUserAction`, 기본 키를 줄 때 `SwitchDefaultAccessKeyAction` |
| delete_user_by_id | 626 | `DeleteUserInput` | `DeleteUserPayload` | — | `DeleteUserAction` |
| restore_user_by_id | 631 | `RestoreUserInput` | `RestoreUserPayload` | — | `RestoreUserAction` |
| purge_user_by_id | 636 | `PurgeUserInput` | `PurgeUserPayload` | 관리자 사용자 id | `PurgeUserAction` |
| bulk_create_users | 660 | `BulkCreateUserAction` | `BulkCreateUsersPayload` | — | `BulkCreateUserAction` |
| bulk_create_users_with_keypair | 679 | `BulkCreateUserAction` | `BulkCreateUsersWithKeypairPayload` | — | `BulkCreateUserAction` |
| bulk_modify_users | 706 | `BulkUpdateUserAction` | `BulkUpdateUsersPayload` | 사용자별 기본 키 전환 목록 | `BulkUpdateUserAction`, `SwitchDefaultAccessKeyAction` |
| bulk_purge_users | 736 | `BulkPurgeUserAction` | `BulkPurgeUsersPayload` | — | `BulkPurgeUserAction` |
| update_user | 752 | `UpdateUserAction` | `UpdateMyAllowedClientIPPayload` | — | `UpdateUserAction` |
| issue_my_keypair | 759 | — | `IssueMyKeypairPayload` | 사용자 id | `IssueMyKeypairAction` |
| revoke_my_keypair | 769 | — | `RevokeMyKeypairPayload` | access key | `LookupKeypairByAccessKeyAction`, `PurgeKeypairAction` |
| update_my_keypair | 774 | — | `UpdateMyKeypairPayload` | access key, 활성 여부 | `LookupKeypairByAccessKeyAction`, `UpdateKeypairAction` |
| switch_default_access_key | 784 | — | `SwitchMyMainAccessKeyPayload` | 사용자 id, access key | `SwitchDefaultAccessKeyAction` |
| search_my_keypairs | 793 | `SearchMyKeypairsRequest` | `SearchResult[KeypairNode]` | 현재 사용자 컨텍스트 | `SearchMyKeypairsAction` |
| admin_create_keypair | 864 | `AdminCreateKeypairInput` | `AdminCreateKeypairPayload` | — | `AdminCreateKeypairAction` |
| admin_update_keypair | 902 | `AdminUpdateKeypairInput` | `AdminUpdateKeypairPayload` | — | `LookupKeypairByAccessKeyAction`, `UpdateKeypairAction` |
| admin_delete_keypair | 917 | — | `AdminDeleteKeypairPayload` | access key | `LookupKeypairByAccessKeyAction`, `PurgeKeypairAction` |
| admin_get_keypair | 921 | — | `KeypairNode` | access key | `LookupKeypairByAccessKeyAction`, `GetKeypairAction` |
| admin_register_ssh_keypair | 928 | `AdminRegisterSSHKeypairInput` | `AdminRegisterSSHKeypairPayload` | — | `LookupKeypairOwnerByAccessKeyAction`, `AdminRegisterSSHKeypairAction` |
| admin_delete_ssh_keypair | 942 | — | `AdminDeleteSSHKeypairPayload` | access key | `LookupKeypairOwnerByAccessKeyAction`, `AdminDeleteSSHKeypairAction` |
| admin_get_ssh_keypair | 951 | — | `AdminGetSSHKeypairPayload` | access key | `LookupKeypairOwnerByAccessKeyAction`, `AdminGetSSHKeypairAction` |
| admin_search_keypairs | 965 | `AdminSearchKeypairsInput` | `AdminSearchKeypairsPayload` | — | `AdminSearchKeypairsAction` |
| gql_admin_search_keypairs | 995 | `AdminSearchKeypairsInput` | `SearchResult[KeypairNode]` | 리소스 정책 이름(선택) | `AdminSearchKeypairsAction` |

사용자 노드를 답하는 메서드는 모두 끝에 `GetDefaultKeypairsAction`을 한 번 더 부른다(`adapter.py:1633-1649`).
2절의 문이 여기에도 걸린다.

`bulk_*`와 `update_user`는 요청으로 액션을 그대로 받는다. 변환은 GQL 리졸버의 몫이다
(`api/gql/user/resolver/mutation.py:178,210,369,561,645`).

### 로그인 세션 어댑터 (`api/adapters/login_session/adapter.py`)

| 메서드 | 줄 | 요청 | 답 | 요청 외 인자 | 거치는 액션 |
|---|---|---|---|---|---|
| admin_search | 67 | `AdminSearchLoginSessionsInput` | `AdminSearchLoginSessionsPayload` | — | `GlobalSearchLoginSessionsAction` |
| my_search | 96 | `MySearchLoginSessionsInput` | `MySearchLoginSessionsPayload` | 현재 사용자 컨텍스트 | `SearchLoginSessionsAction` |
| my_revoke | 127 | `MyRevokeLoginSessionInput` | `RevokeLoginSessionPayload` | — | `RevokeLoginSessionAction` |
| admin_revoke | 134 | `AdminRevokeLoginSessionInput` | `RevokeLoginSessionPayload` | — | `GlobalRevokeLoginSessionAction` |
| admin_unblock_user | 143 | `AdminUnblockUserInput` | `UnblockUserPayload` | — | `GlobalUnblockUserAction` |

### 로그인 이력 어댑터 (`api/adapters/login_history/adapter.py`)

| 메서드 | 요청 | 답 | 요청 외 인자 | 거치는 액션 |
|---|---|---|---|---|
| admin_search | `AdminSearchLoginHistoryInput` | `AdminSearchLoginHistoryPayload` | — | `GlobalSearchLoginHistoryAction` |
| my_search | `MySearchLoginHistoryInput` | `MySearchLoginHistoryPayload` | 현재 사용자 컨텍스트 | `SearchLoginHistoryAction` |

## 2. 무엇이 막는가

### 문과 예외

| 문 | 배선 종류 | 거부 예외 | 슈퍼관리자 | 집행을 끄면 | 근거 |
|---|---|---|---|---|---|
| 전역 역할 | `global_scope`, `global_search_ops` | `InsufficientPrivilege` | 통과. 모니터는 GET/SEARCH/LOOKUP만 통과 | 그대로 막는다 | `actions/v2/global_scope/processor.py:51`, `superadmin.py:22-34`, `actions/types.py:106` |
| 엔티티 권한 | `single_entity`, field `single_field` | `NotEnoughPermission` | 통과 | 통과 | `actions/v2/single_entity/validator/rbac.py:33-54` |
| 엔티티 권한, 소유자 조회 단계 | `key_field_lookup_ops`, `key_owner_lookup_ops` | `GenericBadRequest`. 없는 키와 권한 없음이 같은 예외다 | 통과. 없는 키는 `FieldNotFoundError` | 권한은 통과, 없는 키는 여전히 `GenericBadRequest` | `actions/v2/lookup/processor.py:99-110,132-146` |
| 스코프 권한 | `scope`, `scope_search_ops`, field `search_ops` | `NotEnoughPermission`. 여러 스코프 중 하나라도 막히면 전부 거부 | 통과 | 통과 | `actions/v2/scope/validator/rbac.py:38-66` |
| 입력 검증 | 없음. 서비스와 리포지토리가 실행 중에 낸다 | 경우마다 다르다 | 해당 없음 | 해당 없음 | 아래 표 |

- 집행 스위치는 `manager.rbac.enforcement_enabled`, 기본 True(`config/unified.py:630-650`).
- 권한은 GET/SEARCH/LOOKUP이 READ, DELETE/RESTORE가 SOFT_DELETE, PURGE가 HARD_DELETE로 바뀐다(`actions/types.py:160-182`).
- 권한 검사가 실행보다 먼저 돈다. 슈퍼관리자가 아닌 사용자는 대상이 없어도 `NotEnoughPermission`을 받는다. 대상 없음을 보는 행은 슈퍼관리자이거나 집행을 끈 상태여야 한다.
- 본인에 대한 예외는 없다. 검사기가 건너뛰는 조건은 슈퍼관리자와 집행 꺼짐뿐이다(`single_entity/validator/rbac.py:35-54`). 자기 키를 발급하는 사람도 자기 사용자에 대한 권한을 받아야 한다.
- 키페어, 로그인 세션, 로그인 이력의 권한은 소유 사용자에 대한 사용자 엔티티 권한으로 본다. 권한 쿼리는 `entity_type == user`이고 모든 필드에 걸린 행만 읽는다(`repositories/ops/v2/permission/read.py:212-215`).

### 메서드별

| 메서드 | 문 (순서대로) | 권한 대상 | 거부 예외 |
|---|---|---|---|
| resolve_domain_id | 인증만 | — | 없는 이름은 `EntityNotFoundError` (`repositories/ops/repository.py:127-132`). 사용자 시나리오가 아니라 9절에 행이 없다(10절) |
| batch_load_by_ids | 엔티티 권한, 원소마다 | 각 사용자에 READ | 원소 단위. 4절 아래 표 |
| gql_admin_search, admin_search | 전역 역할 | — | `InsufficientPrivilege` |
| role_search | 전역 역할 | — | `InsufficientPrivilege`. 이름과 달리 스코프 검색이 아니라 전역 검색에 역할 조건을 붙인다(`adapter.py:469-470`) |
| gql_search_by_domain, domain_search | 인증(도메인 이름 조회) → 스코프 권한 | 도메인 스코프에 사용자 READ | `EntityNotFoundError`, `NotEnoughPermission` |
| gql_search_by_project, project_search | 스코프 권한 | 프로젝트 스코프에 사용자 READ | `NotEnoughPermission` |
| scoped_search, gql_scoped_search | 스코프 권한, 항목마다 | 도메인, 프로젝트, 역할 스코프 각각에 사용자 READ (`services/user/actions/scoped_search.py:40-77,106-107`) | `NotEnoughPermission` |
| get | 엔티티 권한 | 사용자 READ | `NotEnoughPermission` |
| create_user | 인증(도메인 이름 조회) → 스코프 권한 → 입력 검증 | 도메인 스코프에 사용자 CREATE (`create_user.py:39-40`) | `EntityNotFoundError`, `NotEnoughPermission`, `UserConflict` |
| update_user_by_id | 엔티티 권한 → 입력 검증 | 사용자 UPDATE | `NotEnoughPermission`, `UserModificationBadRequest`, `UserNotFound`, 기본 키 전환에서 `KeyPairNotFound`/`KeyPairForbidden` |
| delete_user_by_id, restore_user_by_id | 엔티티 권한 | 사용자 SOFT_DELETE | `NotEnoughPermission` |
| purge_user_by_id | 엔티티 권한 → 입력 검증 | 사용자 HARD_DELETE | `NotEnoughPermission`, 관리자 id가 없으면 `UserNotFound` (`services/user/service.py:186`), 활성 커널에 폴더가 걸려 있으면 `UserPurgeFailure` |
| bulk_create_users, bulk_create_users_with_keypair | 전역 역할 → 입력 검증 | 슈퍼관리자만 (쓰기라 모니터 불가) | `InsufficientPrivilege`, 항목별 실패는 답에 담긴다 |
| bulk_modify_users, bulk_purge_users | 전역 역할 → 입력 검증 | 슈퍼관리자만 | `InsufficientPrivilege`, 항목별 실패는 답에 담긴다 |
| update_user | 엔티티 권한 | 사용자 UPDATE | `NotEnoughPermission` |
| issue_my_keypair | 엔티티 권한 | 사용자 UPDATE | `NotEnoughPermission` |
| switch_default_access_key | 엔티티 권한 → 입력 검증 | 사용자 UPDATE | `NotEnoughPermission`, 남의 키나 비활성 키는 `KeyPairForbidden`, 없는 키는 `KeyPairNotFound` (`repositories/user/db_source/db_source.py:920-929`) |
| search_my_keypairs | 스코프 권한 | 자기 사용자 스코프에 사용자 READ (`keypair_ops.py:183-188`) | `NotEnoughPermission` |
| admin_create_keypair | 엔티티 권한 → 입력 검증 | 대상 사용자 UPDATE. 이름과 달리 전역 역할 문이 아니다 | `NotEnoughPermission`, `KeypairResourcePolicyNotFound` |
| revoke_my_keypair, admin_delete_keypair | 소유자 조회 → 엔티티 권한 → 입력 검증 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission`, 기본 키면 `KeyPairForbidden` (`models/keypair/purgers.py:43-51`) |
| update_my_keypair, admin_update_keypair | 소유자 조회 → 엔티티 권한 → 입력 검증 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission`, 기본 키를 끄면 `KeyPairForbidden` (`models/keypair/updaters.py:121-131`), 없는 정책은 `KeypairResourcePolicyNotFound` |
| admin_get_keypair | 소유자 조회 → 엔티티 권한 | 소유자 READ 두 번 | `GenericBadRequest` |
| admin_register_ssh_keypair, admin_delete_ssh_keypair | 소유자 조회 → 엔티티 권한 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission` |
| admin_get_ssh_keypair | 소유자 조회 → 엔티티 권한 | 소유자 READ 두 번 | `GenericBadRequest` |
| admin_search_keypairs, gql_admin_search_keypairs | 전역 역할 | — | `InsufficientPrivilege` |
| login_session.admin_search, login_history.admin_search | 전역 역할 | — | `InsufficientPrivilege` |
| login_session.my_search, login_history.my_search | 스코프 권한 | 자기 사용자 스코프에 사용자 READ (`services/auth/actions/search_login_sessions.py:47-53`) | `NotEnoughPermission` |
| login_session.my_revoke | 소유자 조회 → 엔티티 권한 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission` |
| login_session.admin_revoke | 전역 역할 → 입력 검증 | 슈퍼관리자만 | `InsufficientPrivilege`, 없는 세션은 `LoginSessionNotFoundError` (`repositories/auth/db_source/db_source.py:766-769`) |
| login_session.admin_unblock_user | 전역 역할 | 슈퍼관리자만 | `InsufficientPrivilege` |

사용자 노드를 답하는 메서드는 모두 답에 담기는 사용자 전원에 대해 READ가 한 번 더 필요하다.
`GetDefaultKeypairsAction`이 소유자 전원을 한꺼번에 검사하고, 하나라도 막히면 호출 전체가
`NotEnoughPermission`으로 끝난다(`actions/v2/bulk/validator/rbac.py:91-98`). 생성 권한만 받은 사용자는
만든 사용자를 답으로 받지 못한다.

## 3. 그래프 위치

사용자는 도메인 스코프 안에 만들어진다. 생성 문은 도메인 스코프의 사용자 CREATE다(`create_user.py:39-40`).
그래서 권한 받은 사용자 시나리오가 성립한다.

- 사용자 자기 자신의 가상 엔티티가 자기를 소유하고 다스린다(`repositories/ops/v2/graph_write.py:59-74`). 사용자 스코프에 둔 역할이 사용자 권한을 주면 그 사용자에 대한 엔티티 권한 검사와 스코프 권한 검사가 모두 통과한다.
- 도메인이 사용자를 소유하고 다스린다(`graph_write.py:146-176`). 도메인 스코프에 둔 역할은 그 도메인 사용자 전원에 대해 통한다.
- 사용자 스코프의 프리셋 역할을 만든다(`repositories/ops/v2/entity_write.py:131,323-360`). 소유자 프리셋은 `auto_assign: false`라 본인에게 자동으로 배정되지 않는다(`data/permission/seed/roles/user-owner.yaml:4,49`).
- 시나리오 템플릿 데이터베이스에는 프리셋 행이 없어서 프리셋 역할이 하나도 생기지 않는다(`entity_write.py:379-380`). 필요한 권한은 역할을 직접 심어 준다.

## 4. 요청에 없는데 필요한 값

| 값 | 어디서 오는가 | 근거 |
|---|---|---|
| 키페어 리소스 정책 | 기본 표시가 붙은 정책 하나를 조회한다. 이 조회는 대체될 예정이라 시나리오에서 다루지 않는다 | `db_source.py:159-166` |
| 사용자 리소스 정책 | 요청의 기본값 `"default"` | `common/dto/manager/v2/user/request.py:89-92`, `models/user/creators.py:116` |
| 개인 프로젝트의 리소스 정책 | 코드가 못박은 이름 `"default"` | `models/project/creators.py:66-67` |
| 개인 프로젝트 이름 | 사용자 이름. 겹치면 `-2`부터 `-999`, 그래도 겹치면 사용자 id | `repositories/ops/v2/user/write.py:175-199` |
| access key, secret key, SSH 키쌍 | 생성한다. secret은 키 제공자 풀로 암호화한다 | `models/keypair/row.py:158-202` |
| 기본 키페어의 활성, 관리자 표시 | 사용자 상태가 ACTIVE인지, 역할이 SUPERADMIN이나 ADMIN인지 | `write.py:106-107` |
| 비밀번호 해시 설정 | 매니저 설정 `auth.password_hash_*` | `adapter.py:491-496` |
| 도메인 id | 이름으로 조회한다 | `adapter.py:217-220` |
| 새로 발급하는 키페어의 활성, 관리자, 정책, 요청 한도 | 사용자의 기본 키를 따른다 | `db_source.py:896-901` |
| 관리자 퍼지의 관리자 사용자 | 요청 외 인자. 공유 폴더와 엔드포인트를 넘겨받는다 | `services/user/service.py:185-259` |

## 5. 통째로 써야 하는 합성 연산

`V2UserWriteOps.create_user(FullUserCreator)` (`repositories/ops/v2/user/write.py:84-111`). 어댑터의 생성과
시나리오 seed(`tests/scenario/bai_scenario/seeds/user/user.py`)가 같은 연산을 쓴다.

| 순서 | 쓰는 행 | 근거 |
|---|---|---|
| 1 | 도메인 가상 엔티티 (없을 때만) | `write.py:87`, `graph_write.py:44-69` |
| 2 | 사용자 행 | `entity_write.py:127-128` |
| 3 | 사용자 가상 엔티티, 자기 소속, 스코프 연결 | `entity_write.py:130` |
| 4 | 사용자 스코프의 프리셋 역할과 권한 | `entity_write.py:131,323-360` |
| 5 | 도메인이 사용자를 소유하고 다스리는 행 | `entity_write.py:132`, `graph_write.py:146-176` |
| 6 | 사용자 스코프와 도메인 스코프의 자동 배정 역할 배정 | `write.py:92`, `entity_write.py:296-319` |
| 7 | 기본 키페어 | `write.py:93,97-111` |
| 8 | 개인 프로젝트와 그 프리셋 역할, 도메인 소유 | `write.py:94,146-165` |
| 9 | 개인 프로젝트 명부 등재 | `write.py:164`, `repositories/ops/v2/roster/write.py:191-198` |

어댑터 경로는 앞뒤에 둘을 더한다. 같은 쓰기 트랜잭션 안에서 이메일과 사용자 이름 중복을 먼저 보고
(`db_source.py:188-191`), 뒤에 요청의 프로젝트와 도메인의 모델 스토어 프로젝트에 등재한다
(`write.py:113-124,213-226`).

| 항목 | seed | 어댑터 생성 |
|---|---|---|
| 중복 검사 | 없음 | 있음 |
| 키페어 정책 | 앞 단계가 만든 정책 | 기본 표시 정책 조회(대체 예정) |
| 키 값 | 평문, SSH 키는 빈 문자열 | 생성, 암호화 |
| 프로젝트 등재 | 없음 | 있음 |

## 6. 어댑터가 요구하는 의존성

| 생성자 인자 | 닿는 메서드 | 시나리오 |
|---|---|---|
| `UserProcessors` | 전부 | 조립 |
| `DomainProcessors` | resolve_domain_id, create_user, domain_search, gql_search_by_domain | 조립 |
| `AuthConfig` | create_user, 비밀번호를 줄 때 update_user_by_id | 설정에서 |
| `KeyProviderPool` | secret을 답하는 메서드(create_user, bulk_create_users_with_keypair, issue_my_keypair, admin_create_keypair). 리포지토리의 키 생성 | 평문 풀 |

| `UserService` 인자 | 닿는 경로 | 시나리오 |
|---|---|---|
| `StorageSessionManager` | 퍼지할 사용자에게 지울 폴더가 있을 때 (`repositories/vfolder/deletion.py:51-52,75`) | unwired |
| `ValkeyStatClient` | 월간 통계. 어댑터 메서드는 닿지 않는다 (`service.py:289-302`) | 이미 있는 것 |
| `AgentRegistry` | 저장만 하고 쓰지 않는다 (`service.py:139`) | unwired |
| `UserRepository` | 전부 | 조립 |
| `SchedulingController` | 퍼지할 사용자에게 자원을 점유한 세션이 있을 때 (`service.py:245-250`) | unwired |

| `AuthService` 인자 (로그인 세션, 이력 어댑터) | 닿는 경로 | 시나리오 |
|---|---|---|
| `auth_repository` | my_revoke, admin_revoke | 조립 |
| `valkey_session_client` | my_revoke, admin_revoke, admin_unblock_user | 실제 Valkey |
| `client_ip_masking_repository` | my_revoke, admin_revoke가 이력을 남길 때 | 조립 |
| 나머지 일곱 (`hook_plugin_ctx`, `config_provider`, `user_resource_policy_repository`, `user_repository`, `group_repository`, `ssh_key_validator`, `key_provider_pool`) | 닿지 않는다 | unwired |

검색 네 개는 서비스를 거치지 않고 ops로 답한다(`services/auth/processors.py:211-218`).

## 7. 외부 서비스 경계

| 클라이언트 | 누가 부르는가 | 시나리오 |
|---|---|---|
| `StorageSessionManager` | 퍼지, 지울 폴더가 있을 때만 | 폴더 없는 사용자로만 퍼지해 닿지 않게 한다 |
| `SchedulingController` | 퍼지, 점유 세션이 있을 때만 | 세션 없는 사용자로만 퍼지한다 |
| `ValkeySessionClient` | 로그인 세션 회수(세션 키 삭제), 차단 해제(로그인 차단 키 삭제) (`common/clients/valkey_client/valkey_session/client.py:165-172,206-214`) | 실제 Valkey |

에이전트 RPC에 닿는 경로는 없다.

## 8. 답이 싣는 것

기본은 노드 전체 비교다. 아래는 값을 말할 수 없거나 조건으로 보는 자리다.

### 사용자 노드

| 자리 | 검사 |
|---|---|
| `id` | 무시. 데이터베이스가 만든다 |
| `basic_info.*`, `status.status`, `status.need_password_change`, `organization.role`, `organization.resource_policy`, `security.allowed_client_ip`, `security.totp_activated`, `security.sudo_session_enabled`, `container.*` | 요청 값 또는 4절, 9절이 적은 기본값과 같다 |
| `status.status_info` | 생성 직후 None, 상태를 바꾸면 `"admin-requested"` (`db_source.py:317-319,347-363`) |
| `organization.domain_name` | 앞 단계가 만든 도메인 이름과 같다 |
| `organization.main_access_key` | 그 사용자 기본 키와 같다. 기본 키가 비활성이면 None (`models/keypair/queriers.py:28-29`) |
| `security.totp_activated_at` | None |
| `timestamps.created_at`, `timestamps.modified_at` | 이 실행이 쓴 시각 |

### 키페어 노드

| 자리 | 검사 |
|---|---|
| `id`, `access_key` | 생성한 키면 무시. 심은 키면 심은 키와 같다 |
| `is_active`, `is_admin`, `is_default`, `rate_limit`, `resource_policy` | 값으로 본다 |
| `num_queries` | 0 |
| `last_used` | None |
| `ssh_public_key` | 생성 경로면 무시(생성한 RSA 키), 심은 키면 빈 문자열 |
| `created_at`, `modified_at` | 이 실행이 쓴 시각 |
| `user_id` | 소유 사용자와 같다 |
| 발급 답의 secret key | 무시. 매번 새로 만든다 |

### 목록 답

| 자리 | 검사 |
|---|---|
| `items` | 심은 행의 이름이나 access key 목록으로 비교한다. 순서를 보장하지 않는 검색은 이름순으로 정렬해 비교한다 |
| 순서 | 한 트랜잭션에서 심은 행은 생성 시각이 같다. 생성 시각 내림차순 뒤의 동률 정렬(사용자는 id, 키페어는 access key, 로그인 세션과 이력은 id, 모두 오름차순)이 순서를 정한다 |
| `total_count`, `pagination.total` | 값 |
| `has_next_page`, `has_previous_page` | 값 |
| `pagination.offset`, `pagination.limit` | 값. 키페어 전체 검색은 limit을 생략하면 None을 답한다 (`adapter.py:988-992`) |

### 성공만 답하는 것

`DeleteUserPayload`, `RestoreUserPayload`, `PurgeUserPayload`, `RevokeMyKeypairPayload`,
`SwitchMyMainAccessKeyPayload`, `UpdateMyAllowedClientIPPayload`, `RevokeLoginSessionPayload`,
`UnblockUserPayload`는 `success`만 싣는다. 이 행들은 답과 함께, 같은 어댑터의 조회 호출을 뒤이어 불러
바뀐 결과가 조회되는지 본다. 9절 기대 칸의 "뒤이은" 조회가 그것이다.

## 9. 시나리오 목록

공통 전제: 사용자는 모두 5절의 합성 연산으로 심는다. 그 전에 프로젝트 정책(4절의 `"default"`),
사용자 정책, 키페어 정책을 심는다. 아래 전제 칸은 이것을 반복하지 않는다.

역할을 준다는 말은 역할 하나를 그 스코프에 만들고, 그 역할에 사용자 엔티티 권한을 모든 필드로 한
줄 주고, 행위자에게 배정한다는 뜻이다.

### 사용자 읽기

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 권한 받은 사용자가 사용자를 읽으면 그 사용자 노드 전체가 온다 | 대상 사용자 스코프에서 사용자 READ를 받은 사용자가 읽으면, 기본 키까지 채운 노드 전체가 답으로 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 사용자 스코프에 READ를 준 역할을 행위자에게 | 노드 전체, 8절 기본대로 |
| 권한 없는 사용자는 다른 사용자를 읽을 수 없다 | 아무 역할도 받지 않은 사용자가 다른 사용자를 읽으려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 일괄 읽기는 원소마다 노드와 거부를 입력 순서대로 답한다 | 한 사용자에게만 READ를 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, 없는 id를 한 번에 요청하면, 입력 순서대로 원소별 결과가 온다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 행위자 하나, 첫 사용자 스코프에 READ를 준 역할을 행위자에게 | 원소 표 참고 |
| 슈퍼관리자의 일괄 읽기에서 없는 id는 비어 온다 | 슈퍼관리자가 있는 id와 없는 id를 함께 요청하면, 권한 문을 지나 없는 원소 자리에 빈 값이 온다 | 슈퍼관리자 | 도메인 하나, 사용자 하나 | 있는 id는 노드, 없는 id는 None |
| 빈 목록으로 일괄 읽기를 하면 빈 목록이 온다 | 권한 없는 사용자가 빈 id 목록을 주면, 어떤 액션도 부르지 않고 빈 목록이 답으로 온다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나 | 빈 목록 |

일괄 읽기 원소 표 (권한 받은 사용자 행):

| 원소 | 기대 |
|---|---|
| READ를 받은 사용자 | 노드. 8절 기준 |
| READ를 받지 않은 사용자 | `NotEnoughPermission` 예외 원소 |
| 없는 id | `NotEnoughPermission` 예외 원소. 슈퍼관리자가 아니면 대상 없음이 드러나지 않는다 |

### 사용자 검색

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 슈퍼관리자가 전체 사용자를 훑으면 삭제된 사용자까지 모두 센다 | 전역 역할이 문인 검색에서 슈퍼관리자가 필터 없이 훑으면, 삭제 상태 사용자를 포함해 심은 사용자가 모두 온다 | 슈퍼관리자 | 도메인 하나, 활성 사용자 하나, 삭제 상태 사용자 하나 | 목록 전체 비교, 전체 개수 셋(슈퍼관리자 포함), 기본 페이지 limit 50 offset 0 |
| 슈퍼관리자가 아니면 전체 사용자를 훑을 수 없다 | 도메인 스코프 권한을 받은 사용자라도 전체 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 READ를 준 역할을 행위자에게 | `InsufficientPrivilege` |
| 페이지 인자를 주지 않은 GQL 전체 검색은 최근 가입순 열 명까지 온다 | 슈퍼관리자가 커서와 페이지 인자를 모두 생략하고 훑으면, 생성 시각 내림차순으로 열 명까지 오고 다음 페이지 여부가 함께 온다 | 슈퍼관리자 | 도메인 하나, 사용자 열한 명 | 목록 순서 비교, 전체 개수 열둘, 다음 페이지 있음 |
| 슈퍼관리자가 아니면 GQL 전체 검색을 할 수 없다 | 권한 받은 사용자가 GQL 전체 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 위와 같음 | `InsufficientPrivilege` |
| 슈퍼관리자가 역할로 걸러 훑으면 그 역할을 받은 사용자만 온다 | 전역 역할이 문인 역할 검색에서 슈퍼관리자가 역할 하나를 주면, 그 역할을 배정받은 사용자만 온다 | 슈퍼관리자 | 도메인 하나, 사용자 둘, 역할 하나를 첫 사용자에게 | 목록 전체 비교, 개수 하나 |
| 슈퍼관리자가 아니면 역할로 걸러 훑을 수 없다 | 그 역할의 스코프 권한을 받은 사용자라도 역할 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 역할 하나, 도메인 스코프에 READ를 준 역할을 행위자에게 | `InsufficientPrivilege` |
| 도메인 스코프 권한을 받은 사용자가 도메인 이름으로 훑으면 그 도메인 사용자만 온다 | 도메인 스코프에서 사용자 READ를 받은 사용자가 도메인 이름으로 훑으면, 다른 도메인 사용자는 빠진다 | 권한 받은 사용자 | 도메인 둘, 도메인마다 사용자 하나, 행위자는 첫 도메인 소속, 첫 도메인 스코프에 READ를 준 역할을 행위자에게 | 목록 전체 비교(첫 도메인 사용자와 행위자) |
| 권한 없는 사용자는 도메인 이름으로 사용자를 훑을 수 없다 | 역할을 받지 않은 사용자가 도메인 이름으로 훑으려 하면, 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나 | `NotEnoughPermission` |
| 없는 도메인 이름으로는 사용자를 훑을 수 없다 | 권한 받은 사용자가 없는 도메인 이름으로 훑으려 하면, 스코프 검사 전에 이름 조회 단계가 대상 없음으로 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 READ를 준 역할 | `EntityNotFoundError` |
| 도메인 스코프 권한을 받은 사용자가 GQL로 도메인 사용자를 훑는다 | 같은 권한으로 GQL 도메인 검색을 하면, 그 도메인 사용자만 커서 답으로 온다 | 권한 받은 사용자 | 도메인 스코프 행과 같음 | 목록 전체 비교, 페이지 여부 |
| 권한 없는 사용자는 GQL로 도메인 사용자를 훑을 수 없다 | 역할 없이 GQL 도메인 검색을 하면, 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나 | `NotEnoughPermission` |
| 프로젝트 스코프 권한을 받은 사용자가 프로젝트로 훑으면 명부의 사용자만 온다 | 프로젝트 스코프에서 사용자 READ를 받은 사용자가 그 프로젝트로 훑으면, 명부에 오른 사용자만 온다 | 권한 받은 사용자 | 도메인 하나, 프로젝트 하나, 명부에 오른 사용자 하나, 오르지 않은 사용자 하나, 프로젝트 스코프에 READ를 준 역할을 행위자에게 | 목록 전체 비교 |
| 권한 없는 사용자는 프로젝트로 사용자를 훑을 수 없다 | 역할 없이 프로젝트 검색을 하면, 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 프로젝트 하나, 행위자 하나 | `NotEnoughPermission` |
| 프로젝트 스코프 권한을 받은 사용자가 GQL로 프로젝트 사용자를 훑는다 | 같은 권한으로 GQL 프로젝트 검색을 하면, 명부의 사용자만 커서 답으로 온다 | 권한 받은 사용자 | 프로젝트 스코프 행과 같음 | 목록 전체 비교, 페이지 여부 |
| 권한 없는 사용자는 GQL로 프로젝트 사용자를 훑을 수 없다 | 역할 없이 GQL 프로젝트 검색을 하면, 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 프로젝트 하나, 행위자 하나 | `NotEnoughPermission` |
| 스코프 두 개를 주면 둘 중 어느 쪽에든 닿는 사용자가 합쳐져 온다 | 도메인과 프로젝트 스코프 모두에서 READ를 받은 사용자가 두 스코프를 함께 주면, 두 스코프의 사용자가 중복 없이 합쳐진다 | 권한 받은 사용자 | 도메인 둘, 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나, 첫 도메인 스코프와 그 프로젝트 스코프에 READ를 준 역할 둘을 행위자에게 | 목록 전체 비교 |
| 스코프 중 하나라도 권한이 없으면 스코프 검색을 할 수 없다 | 첫 스코프에만 READ를 받은 사용자가 두 스코프를 함께 주면, 스코프 권한 문이 전체를 막는다 | 권한 받은 사용자 | 위에서 프로젝트 스코프 역할을 뺀 것 | `NotEnoughPermission` |
| 스코프 두 개를 준 GQL 스코프 검색도 합쳐져 온다 | 같은 권한으로 GQL 스코프 검색을 하면, 두 스코프 사용자가 커서 답으로 온다 | 권한 받은 사용자 | 스코프 두 개 행과 같음 | 목록 전체 비교, 페이지 여부 |
| 스코프 중 하나라도 권한이 없으면 GQL 스코프 검색을 할 수 없다 | 한 스코프에만 READ를 받고 GQL 스코프 검색에 둘을 주면, 스코프 권한 문이 전체를 막는다 | 권한 받은 사용자 | 거부 행과 같음 | `NotEnoughPermission` |
| 스코프 검색에서 페이지 인자를 생략하면 쉰 명까지 온다 | 권한 받은 사용자가 페이지 인자 없이 스코프 검색을 하면, limit 50 offset 0이 답에 실린다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 READ를 준 역할 | `pagination` 값 비교 |

### 사용자 만들기

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 도메인 스코프 권한을 받은 사용자가 만든 사용자는 그 도메인에 속하고 기본 키를 받는다 | 도메인 스코프에서 사용자 CREATE와 READ를 받은 사용자가 필수 항목과 선택 항목을 모두 주고 만들면, 요청 값이 담긴 노드와 새 기본 키가 답으로 온다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 CREATE와 READ를 준 역할 | 노드 전체, 8절 기본대로. 키 노드는 기본 키 표시, 요청 한도 10000 |
| 필수 항목만 주고 만든 사용자는 선택 항목이 기본값으로 채워진다 | 권한 받은 사용자가 이메일, 이름, 비밀번호, 도메인, 상태, 역할만 주면, 나머지가 기본값으로 채워진 노드가 온다 | 권한 받은 사용자 | 위와 같음 | 노드 전체. 비밀번호 변경 요구 없음, 전체 이름과 설명 None, TOTP 꺼짐, 리소스 정책 `"default"`, sudo 꺼짐, 컨테이너 설정 None |
| 권한 없는 사용자는 사용자를 만들 수 없다 | 역할을 받지 않은 사용자가 만들려 하면, 도메인 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나 | `NotEnoughPermission` |
| 생성 권한만 받은 사용자는 만든 사용자를 답으로 받을 수 없다 | 도메인 스코프에서 CREATE만 받은 사용자가 만들면, 사용자는 쓰이지만 답을 채우는 기본 키 읽기에서 엔티티 권한 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 CREATE만 준 역할 | `NotEnoughPermission` |
| 이미 쓰이는 이메일로는 사용자를 만들 수 없다 | 권한 받은 사용자가 다른 사용자의 이메일로 만들려 하면, 입력 검증이 겹침으로 막는다 | 권한 받은 사용자 | 도메인 하나, 기존 사용자 하나, 행위자 하나, 도메인 스코프에 CREATE를 준 역할 | `UserConflict` |
| 없는 도메인 이름으로는 사용자를 만들 수 없다 | 권한 받은 사용자가 없는 도메인 이름을 주면, 도메인 이름 조회 단계가 대상 없음으로 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 CREATE를 준 역할 | `EntityNotFoundError` |
| 슈퍼관리자가 일괄 생성하면 만든 사용자 목록과 실패 목록이 함께 온다 | 전역 역할이 문인 일괄 생성에서 슈퍼관리자가 새 사용자 하나와 이메일이 겹치는 사용자 하나를 주면, 하나는 만들어지고 하나는 순번과 함께 실패로 담긴다 | 슈퍼관리자 | 도메인 하나, 기존 사용자 하나 | 만든 목록 노드 하나, 실패 목록 순번 1과 그 이름과 이메일, 메시지 무시 |
| 슈퍼관리자가 아니면 일괄 생성할 수 없다 | 도메인 스코프에서 CREATE를 받은 사용자라도 일괄 생성을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 CREATE를 준 역할 | `InsufficientPrivilege` |
| 슈퍼관리자가 키를 함께 받는 일괄 생성을 하면 사용자마다 기본 키가 붙어 온다 | 전역 역할이 문인 이 일괄 생성에서 슈퍼관리자가 새 사용자 둘을 주면, 사용자 노드와 그 기본 키가 짝으로 온다 | 슈퍼관리자 | 도메인 하나 | 짝 둘, 키 노드는 기본 키 표시, 실패 목록 비어 있음 |
| 슈퍼관리자가 아니면 키를 함께 받는 일괄 생성을 할 수 없다 | 권한 받은 사용자가 이 일괄 생성을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 위 거부 행과 같음 | `InsufficientPrivilege` |

### 사용자 수정

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 권한 받은 사용자가 전체 이름만 바꾸면 나머지는 그대로다 | 대상 사용자 스코프에서 UPDATE와 READ를 받은 사용자가 전체 이름만 주면, 전체 이름만 바뀐 노드가 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 UPDATE와 READ를 준 역할 | 노드 전체, 전체 이름만 새 값, 수정 시각은 이 실행이 쓴 시각 |
| 권한 없는 사용자는 다른 사용자를 수정할 수 없다 | 역할을 받지 않은 사용자가 수정하려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 다른 사용자가 쓰는 이름으로는 사용자 이름을 바꿀 수 없다 | 권한 받은 사용자가 이미 쓰이는 사용자 이름을 주면, 입력 검증이 막는다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 행위자 하나, 첫 사용자 스코프에 UPDATE를 준 역할 | `UserModificationBadRequest` |
| 소속 프로젝트를 비우라고 빈 값을 줘도 소속은 그대로다 | 권한 받은 사용자가 소속 프로젝트 자리에 빈 값을 주면, 소속을 건드리지 않고 나머지 수정만 반영된다 | 권한 받은 사용자 | 도메인 하나, 프로젝트 하나, 그 명부의 대상 사용자, 행위자 하나, 대상 스코프에 UPDATE와 READ를 준 역할 | 노드 전체 변화 없음, 수정 뒤 프로젝트 검색에 대상이 남는다 |
| 기본 키를 함께 주면 수정 뒤 그 키가 기본 키가 된다 | 권한 받은 사용자가 대상 사용자의 다른 키를 기본 키로 주면, 수정이 반영된 뒤 기본 키가 옮겨간 노드가 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나와 기본 아닌 키 하나, 행위자 하나, 대상 스코프에 UPDATE와 READ를 준 역할 | 노드 전체, 기본 키가 추가한 키와 같다 |
| 권한 받은 사용자가 접속 허용 IP를 바꾸면 성공만 답한다 | 대상 사용자 스코프에서 UPDATE를 받은 사용자가 허용 IP만 담은 수정을 보내면, 성공 표시가 오고 그 사용자의 허용 IP가 바뀐다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 UPDATE를 준 역할 | 성공 참, 뒤이은 읽기에서 허용 IP 새 값. 단일 주소는 `/32`가 붙은 저장 형태로 온다 |
| 권한 없는 사용자는 접속 허용 IP를 바꿀 수 없다 | 역할 없이 허용 IP 수정을 보내면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 슈퍼관리자가 일괄 수정하면 수정된 사용자와 실패가 나뉘어 온다 | 전역 역할이 문인 일괄 수정에서 슈퍼관리자가 있는 사용자와 이름이 겹치게 바꾸는 사용자를 함께 주면, 하나는 수정되고 하나는 사용자 id와 함께 실패로 담긴다 | 슈퍼관리자 | 도메인 하나, 사용자 셋 | 수정 목록 노드 하나, 실패 목록 사용자 id 하나, 메시지 무시 |
| 일괄 수정에서 기본 키 전환이 실패한 사용자는 실패로 옮겨진다 | 슈퍼관리자가 일괄 수정과 함께 남의 키로 기본 키 전환을 주면, 그 사용자는 수정 목록에서 빠지고 실패로 담긴다 | 슈퍼관리자 | 도메인 하나, 사용자 둘 | 수정 목록 비어 있음, 실패 목록 사용자 id 하나 |
| 슈퍼관리자가 아니면 일괄 수정할 수 없다 | 도메인 스코프에서 UPDATE를 받은 사용자라도 일괄 수정을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 UPDATE를 준 역할 | `InsufficientPrivilege` |

### 사용자 물리기, 되살리기, 지우기

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 권한 받은 사용자가 사용자를 물리면 그 사용자는 삭제 상태가 된다 | 대상 사용자 스코프에서 SOFT_DELETE를 받은 사용자가 물리면, 성공이 오고 그 사용자 상태가 삭제로 바뀐다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 SOFT_DELETE를 준 역할 | 성공 참, 뒤이은 읽기에서 상태 삭제, 상태 사유 `"admin-requested"` |
| 권한 없는 사용자는 사용자를 물릴 수 없다 | 역할 없이 물리려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 권한 받은 사용자가 물린 사용자를 되살리면 활성이 된다 | 대상 사용자 스코프에서 SOFT_DELETE를 받은 사용자가 삭제 상태 사용자를 되살리면, 성공이 오고 상태가 활성으로 바뀐다 | 권한 받은 사용자 | 도메인 하나, 삭제 상태 대상 사용자 하나, 행위자 하나, 대상 스코프에 SOFT_DELETE를 준 역할 | 성공 참, 뒤이은 읽기에서 상태 활성 |
| 물리지 않은 사용자를 되살려도 활성이 된다 | 권한 받은 사용자가 비활성 사용자를 되살리면, 현재 상태와 무관하게 활성이 된다 | 권한 받은 사용자 | 도메인 하나, 비활성 대상 사용자 하나, 행위자 하나, 대상 스코프에 SOFT_DELETE를 준 역할 | 성공 참, 뒤이은 읽기에서 상태 활성 |
| 권한 없는 사용자는 사용자를 되살릴 수 없다 | 역할 없이 되살리려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 삭제 상태 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 권한 받은 사용자가 폴더와 세션이 없는 사용자를 지우면 그 사용자가 사라진다 | 대상 사용자 스코프에서 HARD_DELETE를 받은 사용자가 물리지 않은 사용자를 지워도, 성공이 오고 그 사용자를 더 찾을 수 없다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 HARD_DELETE를 준 역할 | 성공 참, 뒤이은 슈퍼관리자 일괄 읽기에서 None |
| 권한 없는 사용자는 사용자를 지울 수 없다 | 역할 없이 지우려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 없는 관리자 id로는 사용자를 지울 수 없다 | 권한 받은 사용자가 넘겨받을 관리자로 없는 id를 주면, 입력 검증이 막는다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 HARD_DELETE를 준 역할 | `UserNotFound` |
| 슈퍼관리자가 일괄로 지우면 지운 사용자 id와 개수가 온다 | 전역 역할이 문인 일괄 지우기에서 슈퍼관리자가 사용자 둘을 주면, 두 id와 개수 둘이 온다 | 슈퍼관리자 | 도메인 하나, 사용자 둘 | 성공 목록 두 id, 개수 둘, 실패 목록 비어 있음 |
| 일괄 지우기에서 없는 사용자는 실패로 담긴다 | 슈퍼관리자가 있는 사용자와 없는 id를 함께 주면, 하나는 지워지고 없는 id는 실패로 담긴다 | 슈퍼관리자 | 도메인 하나, 사용자 하나 | 성공 목록 한 id, 개수 하나, 실패 목록 없는 id, 메시지 무시 |
| 슈퍼관리자가 아니면 일괄로 지울 수 없다 | 도메인 스코프에서 HARD_DELETE를 받은 사용자라도 일괄 지우기를 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 HARD_DELETE를 준 역할 | `InsufficientPrivilege` |

### 자기 키페어

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 자기 사용자에 UPDATE를 받은 사용자가 키를 발급하면 기본 키를 따르는 새 키가 온다 | 자기 사용자 스코프에서 UPDATE를 받은 사용자가 발급하면, 기본 키의 관리자 표시, 정책, 요청 한도를 따르고 기본 표시는 없는 키와 secret이 온다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 자기 스코프에 UPDATE를 준 역할 | 키 노드 전체, 활성, 기본 아님, 정책과 요청 한도는 기본 키와 같다 |
| 권한 없는 사용자는 자기 키를 발급할 수 없다 | 역할을 받지 않은 사용자가 자기 키를 발급하려 하면, 본인이어도 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나 | `NotEnoughPermission` |
| 자기 사용자에 READ와 UPDATE를 받은 사용자가 기본 아닌 키를 회수하면 그 키가 사라진다 | 권한 받은 사용자가 자기의 기본 아닌 키를 회수하면, 성공이 오고 자기 키 검색에서 그 키가 빠진다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | 성공 참, 뒤이은 자기 키 검색에 기본 키만 |
| 권한 없는 사용자는 자기 키를 회수할 수 없다 | 역할을 받지 않은 사용자가 회수하려 하면, 소유자 조회 단계가 없는 키와 같은 예외로 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 자기 키를 회수할 수 없다 | 자기 스코프에서 READ만 받은 사용자가 회수하려 하면, 소유자 조회는 지나고 엔티티 권한 문이 막는다 | 권한 받은 사용자 | 위 전제에 READ만 준 역할 | `NotEnoughPermission` |
| 기본 키는 회수할 수 없다 | 권한 받은 사용자가 자기 기본 키를 회수하려 하면, 입력 검증이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | `KeyPairForbidden` |
| 없는 access key는 회수할 수 없다 | 권한 받은 사용자가 어떤 키도 아닌 값을 주면, 소유자 조회 단계가 권한 없음과 같은 예외로 막는다 | 권한 받은 사용자 | 위와 같음 | `GenericBadRequest` |
| 권한 받은 사용자가 기본 아닌 키를 끄면 꺼진 키 노드가 온다 | 자기 스코프에서 READ와 UPDATE를 받은 사용자가 기본 아닌 키를 비활성으로 바꾸면, 활성만 바뀐 키 노드가 온다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | 키 노드 전체, 활성 거짓 |
| 권한 없는 사용자는 자기 키를 끌 수 없다 | 역할 없이 키를 끄려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 자기 키를 끌 수 없다 | READ만 받고 키를 끄려 하면, 엔티티 권한 문이 막는다 | 권한 받은 사용자 | READ만 준 역할 | `NotEnoughPermission` |
| 기본 키는 끌 수 없다 | 권한 받은 사용자가 자기 기본 키를 비활성으로 바꾸려 하면, 입력 검증이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | `KeyPairForbidden` |
| 권한 받은 사용자가 기본 키를 옮기면 옮긴 키가 기본이 된다 | 자기 스코프에서 UPDATE를 받은 사용자가 기본 아닌 활성 키로 기본 키를 옮기면, 성공이 오고 사용자 노드의 기본 키가 그 키가 된다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | 성공 참, 뒤이은 읽기에서 기본 키가 추가한 키와 같다 |
| 권한 없는 사용자는 기본 키를 옮길 수 없다 | 역할 없이 기본 키를 옮기려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 하나 | `NotEnoughPermission` |
| 남의 키로는 기본 키를 옮길 수 없다 | 권한 받은 사용자가 다른 사용자의 키를 주면, 입력 검증이 막는다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 자기 스코프에 UPDATE를 준 역할 | `KeyPairForbidden` |
| 권한 받은 사용자가 자기 키를 훑으면 자기 키만 온다 | 자기 스코프에서 READ를 받은 사용자가 자기 키를 훑으면, 다른 사용자의 키는 빠진다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 행위자에게 기본 아닌 키 하나, 자기 스코프에 READ를 준 역할 | 목록 두 키(기본 키와 추가한 키), 개수 둘 |
| 권한 없는 사용자는 자기 키를 훑을 수 없다 | 역할 없이 자기 키를 훑으려 하면, 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나 | `NotEnoughPermission` |
| 페이지 인자를 생략한 자기 키 검색은 최근 발급순 열 개까지 온다 | 권한 받은 사용자가 페이지 인자 없이 훑으면, 생성 시각 내림차순 열 개와 다음 페이지 여부가 온다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나와 기본 아닌 키 열 개, 자기 스코프에 READ를 준 역할 | 목록 순서 비교, 개수 열하나, 다음 페이지 있음 |
| 발급한 키를 기본으로 옮기면 원래 기본 키를 회수할 수 있다 | 권한 받은 사용자가 키를 발급하고 그 키로 기본 키를 옮긴 다음 원래 기본 키를 회수하면, 세 호출이 차례로 통과하고 발급한 키 하나만 남는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | 발급 답의 키로 전환 성공, 회수 성공, 뒤이은 자기 키 검색에 발급한 키 하나 |

### 관리자 키페어

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 대상 사용자에 UPDATE를 받은 사용자가 키를 만들어 주면 요청한 정책의 키가 온다 | 슈퍼관리자가 아니어도 대상 사용자 스코프에서 UPDATE를 받은 사용자가 정책을 주고 키를 만들면, 기본 아닌 새 키와 secret이 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 UPDATE를 준 역할 | 키 노드 전체, 활성 참, 관리자 거짓, 요청 한도 30000, 기본 아님 |
| 권한 없는 사용자는 남에게 키를 만들어 줄 수 없다 | 역할 없이 키를 만들려 하면, 엔티티 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `NotEnoughPermission` |
| 없는 정책으로는 키를 만들어 줄 수 없다 | 권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막는다 | 권한 받은 사용자 | 위 성공 행과 같음 | `KeypairResourcePolicyNotFound` |
| 권한 받은 사용자가 남의 키 요청 한도를 바꾸면 한도만 바뀐다 | 대상 스코프에서 READ와 UPDATE를 받은 사용자가 요청 한도만 주면, 나머지는 그대로이고 한도만 바뀐 키 노드가 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나와 기본 아닌 키 하나, 행위자 하나, 대상 스코프에 READ와 UPDATE를 준 역할 | 키 노드 전체, 요청 한도 새 값 |
| 권한 없는 사용자는 남의 키를 바꿀 수 없다 | 역할 없이 바꾸려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나와 기본 아닌 키 하나, 행위자 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 남의 키를 바꿀 수 없다 | READ만 받고 바꾸려 하면, 엔티티 권한 문이 막는다 | 권한 받은 사용자 | READ만 준 역할 | `NotEnoughPermission` |
| 없는 정책으로는 남의 키를 바꿀 수 없다 | 권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막는다 | 권한 받은 사용자 | 성공 행과 같음 | `KeypairResourcePolicyNotFound` |
| 권한 받은 사용자가 남의 기본 아닌 키를 지우면 지운 access key가 온다 | 대상 스코프에서 READ와 UPDATE를 받은 사용자가 지우면, 지운 키의 access key가 답으로 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나와 기본 아닌 키 하나, 행위자 하나, 대상 스코프에 READ와 UPDATE를 준 역할 | access key가 심은 키와 같다 |
| 권한 없는 사용자는 남의 키를 지울 수 없다 | 역할 없이 지우려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나와 기본 아닌 키 하나, 행위자 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 남의 키를 지울 수 없다 | READ만 받고 지우려 하면, 엔티티 권한 문이 막는다 | 권한 받은 사용자 | READ만 준 역할 | `NotEnoughPermission` |
| 남의 기본 키는 지울 수 없다 | 권한 받은 사용자가 대상의 기본 키를 지우려 하면, 입력 검증이 막는다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 READ와 UPDATE를 준 역할 | `KeyPairForbidden` |
| 권한 받은 사용자가 access key로 남의 키를 읽는다 | 대상 스코프에서 READ를 받은 사용자가 읽으면, 그 키 노드 전체가 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나와 기본 아닌 키 하나, 행위자 하나, 대상 스코프에 READ를 준 역할 | 키 노드 전체, 8절 기본대로 |
| 권한 없는 사용자는 access key로 남의 키를 읽을 수 없다 | 역할 없이 읽으려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `GenericBadRequest` |
| 권한 받은 사용자가 남의 SSH 키를 등록하면 그 access key가 온다 | 대상 스코프에서 READ와 UPDATE를 받은 사용자가 공개키와 개인키를 주면, 형식 검사 없이 덮어쓰고 access key가 답으로 온다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 READ와 UPDATE를 준 역할 | access key가 대상 기본 키와 같다, 뒤이은 SSH 키 읽기에서 준 공개키 |
| 권한 없는 사용자는 남의 SSH 키를 등록할 수 없다 | 역할 없이 등록하려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 남의 SSH 키를 등록할 수 없다 | READ만 받고 등록하려 하면, 엔티티 권한 문이 막는다 | 권한 받은 사용자 | READ만 준 역할 | `NotEnoughPermission` |
| 권한 받은 사용자가 남의 SSH 키를 지우면 그 access key가 온다 | 대상 스코프에서 READ와 UPDATE를 받은 사용자가 지우면, access key가 오고 공개키가 비워진다 | 권한 받은 사용자 | 등록 성공 행과 같음 | access key가 대상 기본 키와 같다, 뒤이은 SSH 키 읽기에서 공개키 None |
| 권한 없는 사용자는 남의 SSH 키를 지울 수 없다 | 역할 없이 지우려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 남의 SSH 키를 지울 수 없다 | READ만 받고 지우려 하면, 엔티티 권한 문이 막는다 | 권한 받은 사용자 | READ만 준 역할 | `NotEnoughPermission` |
| 권한 받은 사용자가 남의 SSH 공개키를 읽는다 | 대상 스코프에서 READ를 받은 사용자가 읽으면, access key와 공개키만 오고 개인키는 오지 않는다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 READ를 준 역할 | access key가 대상 기본 키와 같다, 공개키는 심은 빈 문자열 |
| 권한 없는 사용자는 남의 SSH 공개키를 읽을 수 없다 | 역할 없이 읽으려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나 | `GenericBadRequest` |
| 슈퍼관리자가 모든 키를 훑으면 사용자와 무관하게 전부 온다 | 전역 역할이 문인 키 검색에서 슈퍼관리자가 페이지 인자 없이 훑으면, 모든 사용자의 키가 오고 limit 자리는 비어서 온다 | 슈퍼관리자 | 도메인 하나, 사용자 둘 | 목록 세 키(슈퍼관리자 포함), 전체 셋, offset 0, limit None |
| 슈퍼관리자가 아니면 모든 키를 훑을 수 없다 | 권한 받은 사용자가 키 전체 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 READ를 준 역할 | `InsufficientPrivilege` |
| 슈퍼관리자가 정책 이름으로 GQL 키 검색을 걸면 그 정책의 키만 온다 | 전역 역할이 문인 GQL 키 검색에서 슈퍼관리자가 정책 이름을 주면, 그 정책을 쓰는 키만 온다 | 슈퍼관리자 | 도메인 하나, 키페어 정책 둘, 정책마다 사용자 하나 | 목록 한 키, 개수 하나, 페이지 여부 |
| 슈퍼관리자가 아니면 GQL로 모든 키를 훑을 수 없다 | 권한 받은 사용자가 GQL 키 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 위 거부 행과 같음 | `InsufficientPrivilege` |

### 로그인 세션과 로그인 이력

로그인 세션과 로그인 이력은 사용자가 소유하는 필드 행으로 심는다. 두 테이블의 write spec은 구현 단계에서
더한다(10절 2번).

| summary | description | 행위자 | 전제 | 기대 |
|---|---|---|---|---|
| 슈퍼관리자가 로그인 세션 전체를 훑으면 모든 사용자의 세션이 최근순으로 온다 | 전역 역할이 문인 세션 검색에서 슈퍼관리자가 페이지 인자 없이 훑으면, 사용자와 무관하게 심은 세션이 생성 시각 내림차순으로 온다 | 슈퍼관리자 | 도메인 하나, 사용자 둘, 사용자마다 활성 세션 하나 | 목록 순서 비교, 노드마다 소유자와 access key는 심은 값, 상태 활성, 개수 둘, 페이지 없음 |
| 슈퍼관리자가 아니면 로그인 세션 전체를 훑을 수 없다 | 권한 받은 사용자가 세션 전체 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 READ를 준 역할 | `InsufficientPrivilege` |
| 자기 사용자에 READ를 받은 사용자가 자기 로그인 세션을 훑으면 자기 세션만 온다 | 자기 스코프에서 READ를 받은 사용자가 훑으면, 다른 사용자의 세션은 빠진다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 사용자마다 세션 하나, 자기 스코프에 READ를 준 역할 | 목록 한 세션, 소유자가 행위자와 같다, 개수 하나 |
| 권한 없는 사용자는 자기 로그인 세션을 훑을 수 없다 | 역할 없이 자기 세션을 훑으려 하면, 본인이어도 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나와 세션 하나 | `NotEnoughPermission` |
| 권한 받은 사용자가 자기 로그인 세션을 회수하면 세션이 사라진다 | 자기 스코프에서 READ와 UPDATE를 받은 사용자가 자기 세션을 회수하면, 성공이 오고 그 세션은 더 조회되지 않는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나와 세션 하나, 자기 스코프에 READ와 UPDATE를 준 역할 | 성공 참, 뒤이은 자기 세션 검색 비어 있음 |
| 권한 없는 사용자는 자기 로그인 세션을 회수할 수 없다 | 역할 없이 회수하려 하면, 소유자 조회 단계가 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나와 세션 하나 | `GenericBadRequest` |
| 읽기 권한만 받은 사용자는 자기 로그인 세션을 회수할 수 없다 | READ만 받고 회수하려 하면, 엔티티 권한 문이 막는다 | 권한 받은 사용자 | 위 전제에 READ만 준 역할 | `NotEnoughPermission` |
| 자기 권한으로는 남의 로그인 세션을 회수할 수 없다 | 자기 스코프에서만 READ와 UPDATE를 받은 사용자가 다른 사용자의 세션을 주면, 그 소유자에 대한 조회 단계가 막는다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 둘째 사용자의 세션 하나, 행위자 자기 스코프에 READ와 UPDATE를 준 역할 | `GenericBadRequest` |
| 슈퍼관리자가 남의 로그인 세션을 회수하면 세션이 사라진다 | 전역 역할이 문인 관리자 회수에서 슈퍼관리자가 다른 사용자의 세션을 회수하면, 성공이 오고 세션 전체 검색에서 빠진다 | 슈퍼관리자 | 도메인 하나, 대상 사용자 하나와 세션 하나 | 성공 참, 뒤이은 세션 전체 검색 비어 있음 |
| 슈퍼관리자라도 없는 로그인 세션은 회수할 수 없다 | 슈퍼관리자가 없는 세션 id를 주면, 입력 검증이 막는다 | 슈퍼관리자 | 도메인 하나 | `LoginSessionNotFoundError` |
| 슈퍼관리자가 아니면 로그인 세션을 관리자 경로로 회수할 수 없다 | 권한 받은 사용자가 관리자 회수를 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나와 세션 하나, 행위자 하나, 대상 스코프에 UPDATE를 준 역할 | `InsufficientPrivilege` |
| 슈퍼관리자가 차단을 풀면 그 사용자의 로그인 차단 기록이 지워진다 | 전역 역할이 문인 차단 해제에서 슈퍼관리자가 사용자 이름을 주면, 성공이 오고 그 이름의 차단 기록이 사라진다 | 슈퍼관리자 | 도메인 하나, 대상 사용자 하나 | 성공 참 |
| 없는 사용자 이름으로 차단을 풀어도 성공한다 | 슈퍼관리자가 어떤 사용자도 아닌 이름을 주면, 존재를 확인하지 않고 성공이 온다 | 슈퍼관리자 | 도메인 하나 | 성공 참 |
| 슈퍼관리자가 아니면 차단을 풀 수 없다 | 권한 받은 사용자가 차단을 풀려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 대상 사용자 하나, 행위자 하나, 대상 스코프에 UPDATE를 준 역할 | `InsufficientPrivilege` |
| 슈퍼관리자가 로그인 이력 전체를 훑으면 모든 사용자의 이력이 최근순으로 온다 | 전역 역할이 문인 이력 검색에서 슈퍼관리자가 훑으면, 사용자와 무관하게 심은 이력이 생성 시각 내림차순으로 온다 | 슈퍼관리자 | 도메인 하나, 사용자 둘, 사용자마다 성공 이력 하나 | 목록 순서 비교, 노드마다 소유자, 도메인 이름, 결과는 심은 값, 개수 둘 |
| 슈퍼관리자가 아니면 로그인 이력 전체를 훑을 수 없다 | 권한 받은 사용자가 이력 전체 검색을 하려 하면, 전역 역할 문이 막는다 | 권한 받은 사용자 | 도메인 하나, 행위자 하나, 도메인 스코프에 READ를 준 역할 | `InsufficientPrivilege` |
| 자기 사용자에 READ를 받은 사용자가 자기 로그인 이력을 훑으면 자기 이력만 온다 | 자기 스코프에서 READ를 받은 사용자가 훑으면, 다른 사용자의 이력은 빠진다 | 권한 받은 사용자 | 도메인 하나, 사용자 둘, 사용자마다 이력 하나, 자기 스코프에 READ를 준 역할 | 목록 한 줄, 소유자가 행위자와 같다, 개수 하나 |
| 권한 없는 사용자는 자기 로그인 이력을 훑을 수 없다 | 역할 없이 자기 이력을 훑으려 하면, 본인이어도 스코프 권한 문이 막는다 | 권한 없는 사용자 | 도메인 하나, 행위자 하나와 이력 하나 | `NotEnoughPermission` |

## 10. 열린 질문

1. **auth 7건은 어댑터를 거치지 않는 것이 다섯이다.** 로그인 세션 어댑터가 부르는 것은 `global_revoke_login_session`, `global_unblock_user` 둘이다(`api/adapters/login_session/adapter.py:136,145`). 나머지 다섯은 REST 핸들러가 프로세서를 바로 부른다. `authorize`, `get_role`, `update_password_no_auth`는 `api/rest/auth/handler.py`, `public_resolve_access_key_scope`는 `api/rest/session/handler.py` 등 셋이다. vfolder 목록의 이메일 위임은 `LookupUserAction`을 부른다(`api/rest/vfolder/handler.py`). `authorize`와 `update_password_no_auth`는 액션이 요청 객체를 싣는다(`services/auth/actions/authorize.py`). 이번 작업은 핸들러 호출을 어댑터로 옮기지 않고, 다섯의 시나리오는 뒤로 미룬다.
2. **로그인 세션과 로그인 이력의 write spec을 더한다.** 지금은 인증 흐름의 raw insert만 있다(`repositories/auth/db_source/db_source.py:557-597`). 사용자가 소유하는 필드 creator 둘을 `models/login_session/` 아래에 두고, 시나리오는 `adding`으로 심는다. 추가 범위는 구현 단계에서 따로 설명한다.
3. **역할 스코프 항목의 권한 대상.** 스코프 검색에 역할 스코프를 주면 역할 id를 스코프로 삼아 사용자 READ를 검사한다(`services/user/actions/scoped_search.py:70-77`). 역할을 다스리는 스코프에 준 권한이 그 검사를 통과하는지 확인하지 못해 9절에 행을 두지 않았다.
4. **소속 프로젝트 자리에 빈 값을 주면 아무 일도 없다.** 요청 설명은 "빈 값이면 비운다"(`common/dto/manager/v2/user/request.py:149`)인데 어댑터는 무시한다(`adapter.py:615-619`). 9절은 지금 동작을 행으로 고정했다. 설명과 동작 중 어느 쪽을 고칠지 정해야 한다.
5. **퍼지는 먼저 물린 상태를 요구하지 않는다.** 상태 검사가 없다(`services/user/service.py:185-259`). 의도인지 확인하지 못했다.
6. **슈퍼관리자가 없는 사용자를 읽거나 수정할 때의 예외.** 읽기는 docstring상 `UserNotFound`(`service.py:179-180`)지만 리포지토리까지 따라가지 않았다. 9절에 행을 두지 않았다.
7. **사용자 수정의 소속 동기화와 기본 키 전환은 수정과 다른 트랜잭션이다.** 기본 키 전환이 실패해도 앞의 수정은 남는다(`adapter.py:621-623`, `db_source.py:697-711`). 이 부분 실패를 행으로 고정할지 정해야 한다.
8. **도메인 이름으로 도메인 id를 얻는 메서드는 사용자 시나리오가 아니다.** `resolve_domain_id`(`adapter.py:217-220`)는 도메인 조회만 하므로 9절에 행을 두지 않았고, 레포트의 부르지 않은 호출에 남는다. 어댑터 안에서는 생성과 도메인 검색이 쓰고, 밖에서는 일괄 생성 리졸버가 부른다(`api/gql/user/resolver/mutation.py:122`). 그 호출을 다른 경로로 옮기면 private으로 바꿀 수 있다.
9. **로그인 세션 회수가 남기는 이력은 시나리오가 보지 않는다.** 회수는 세션 행을 지우면서 사용자 회수 또는 관리자 회수 결과의 이력 한 줄을 쓴다(`repositories/auth/db_source/db_source.py:744-786`). 시나리오 한 행이 어댑터 하나만 받아 이력 어댑터로 뒤이어 조회할 수 없다.
10. **로그인 세션 어댑터와 로그인 이력 어댑터의 문서.** 두 패키지의 `KNOWLEDGE.md`는 아직 TODO다. 이 문서를 가리키게 고칠지, report가 두 패키지로 나뉘는 것을 어떻게 맞출지 정해야 한다.
