# user adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 로그인 세션과 로그인 이력은 adapter 가 따로 있지만 사용자가 own 하는 필드이므로 이 문서에 둔다.

경로는 따로 적지 않으면 `src/ai/backend/manager/` 기준이다. 조사 기준은 main `a42719cb67` 이다. BA-7885(배정과 역할 읽기를 스코프로)와 BA-7889(사용자 일괄 읽기를 partial bulk get 으로)가 반영된 연결 및 호출 경로다.

## 어댑터가 제공하는 것

`./backend.ai mgr ops list --concern organization` 은 97건을 낸다. 사용자 46, 도메인 16, 프로젝트 15, auth 7, 그리고 필드는 error_log 4, keypair 4, login_session 3, login_history 2 다. BA-7799 작성 시점의 96건에서 프로젝트 한 건이 늘었다.

### 사용자 adapter (`api/adapters/user/adapter.py`)

| 메서드 | 위치 | 요청 | 응답 | 요청 외 인자 | 거치는 Action |
|---|---|---|---|---|---|
| resolve_domain_id | 217 | — | `DomainID` | 도메인 이름 | `LookupDomainAction` |
| batch_load_by_ids | 224 | — | `list[UserNode \| Exception \| None]` | 사용자 id 목록 | `BulkGetUsersAction` |
| batch_lookup_by_emails | 240 | — | `list[UserID \| Exception]` | email 목록 | `BulkLookupUsersAction` |
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
| update_user_by_id | 595 | `UpdateUserInput` | `UpdateUserPayload` | 사용자 id | `UpdateUserAction`, 기본 키를 지정할 때 `SwitchDefaultAccessKeyAction`, `status` 에 따라 `GetUserAction`, `DeleteUserAction`, `RestoreUserAction`(아래 표) |
| delete_user_by_id | 626 | `DeleteUserInput` | `DeleteUserPayload` | — | `DeleteUserAction` |
| restore_user_by_id | 631 | `RestoreUserInput` | `RestoreUserPayload` | — | `RestoreUserAction` |
| purge_user_by_id | 636 | `PurgeUserInput` | `PurgeUserPayload` | 관리자 사용자 id | `PurgeUserAction` |
| bulk_create_users | 660 | `BulkCreateUserAction` | `BulkCreateUsersPayload` | — | `BulkCreateUserAction` |
| bulk_create_users_with_keypair | 679 | `BulkCreateUserAction` | `BulkCreateUsersWithKeypairPayload` | — | `BulkCreateUserAction` |
| bulk_update_users | 771 | `BulkUpdateUsersInput` | `BulkUpdateUsersPayload` | — | `BulkUpdateUserAction`, `SwitchDefaultAccessKeyAction`, `status` 에 따라 `BulkGetUsersAction`, `DeleteUserAction`, `RestoreUserAction`, `GetUserAction` |
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
| gql_admin_search_keypairs | 995 | `AdminSearchKeypairsInput` | `SearchResult[KeypairNode]` | 자원 정책 이름(선택) | `AdminSearchKeypairsAction` |

사용자 노드를 응답하는 메서드는 모두 끝에서 `GetDefaultKeypairsAction` 을 한 번 더 호출한다(`adapter.py:1633-1649`). 다음 절의 gate 가 여기에도 적용된다.

`bulk_*` 와 `update_user` 는 Action 을 요청으로 그대로 받는다. 변환은 GQL resolver 의 역할이다(`api/gql/user/resolver/mutation.py:178,210,369,561,645`).

### 수정 요청의 `status`

update_user_by_id 와 bulk_update_users 는 같은 기준으로 `status` 를 나눈다(`adapter.py:626-641`). 기준은 `UserStatus` 의 `deletes_from`, `restores_from`, `is_updater_value_from` 셋이다(`data/user/types.py:57-67`). legacy GQL `modify_user` 와 legacy REST `PATCH /admin/users/{user_id}` 도 같은 셋을 같은 순서로 사용한다. bulk 는 항목마다 따로 나누고, 실패는 그 항목의 `failed` 에 담는다.

| 준 `status` | 현재 상태 | 동작 |
|---|---|---|
| DELETED | DELETED 아님 | 나머지 필드를 수정하고 기본 키를 전환한 뒤 `DeleteUserAction`. 응답은 뒤이어 읽은 사용자 |
| DELETED | DELETED | 아무것도 적용하지 않는다. 나머지 필드가 있으면 수정이 `UserDeleted` 로 차단된다 |
| ACTIVE | DELETED | `RestoreUserAction` 뒤 나머지 필드 수정 |
| ACTIVE, INACTIVE | 그 밖 | `UserUpdater` 가 작성한다 |
| BEFORE_VERIFICATION | 관계없음 | `UserUpdater` 가 `UserModificationBadRequest` 로 차단한다(`models/user/updaters.py:54-59`) |

- DELETED 는 deprecated 다. 입력 설명에는 삭제와 복원으로 처리된다고 적었다. 다음 LTS 에서 제외한다.
- 삭제와 복원은 각 Action 의 권한(사용자 SOFT_DELETE)을 따로 받는다. UPDATE 만 받은 사용자가 DELETED 를 주면 `NotEnoughPermission` 이다.
- `UserUpdater` 는 삭제 상태와 영구 삭제 중인 사용자를 차단하는 guard 둘을 가진다(`models/user/updaters.py:75-87`). 저장소가 수정 호출에 guard 를 싣고, 차단되면 첫 실패 guard 의 예외를 낸다(`db_source.py:360-371`).

### 로그인 세션 adapter (`api/adapters/login_session/adapter.py`)

| 메서드 | 위치 | 요청 | 응답 | 요청 외 인자 | 거치는 Action |
|---|---|---|---|---|---|
| admin_search | 67 | `AdminSearchLoginSessionsInput` | `AdminSearchLoginSessionsPayload` | — | `GlobalSearchLoginSessionsAction` |
| my_search | 96 | `MySearchLoginSessionsInput` | `MySearchLoginSessionsPayload` | 현재 사용자 컨텍스트 | `SearchLoginSessionsAction` |
| my_revoke | 127 | `MyRevokeLoginSessionInput` | `RevokeLoginSessionPayload` | — | `RevokeLoginSessionAction` |
| admin_revoke | 134 | `AdminRevokeLoginSessionInput` | `RevokeLoginSessionPayload` | — | `GlobalRevokeLoginSessionAction` |
| admin_unblock_user | 143 | `AdminUnblockUserInput` | `UnblockUserPayload` | — | `GlobalUnblockUserAction` |

### 로그인 이력 adapter (`api/adapters/login_history/adapter.py`)

| 메서드 | 요청 | 응답 | 요청 외 인자 | 거치는 Action |
|---|---|---|---|---|
| admin_search | `AdminSearchLoginHistoryInput` | `AdminSearchLoginHistoryPayload` | — | `GlobalSearchLoginHistoryAction` |
| my_search | `MySearchLoginHistoryInput` | `MySearchLoginHistoryPayload` | 현재 사용자 컨텍스트 | `SearchLoginHistoryAction` |

## 무엇이 차단하는가

### Gate 와 예외

| Gate | 연결 종류 | 거부 예외 | superadmin | 집행을 끄면 | 근거 |
|---|---|---|---|---|---|
| 전역 역할 | `global_scope`, `global_search_ops` | `InsufficientPrivilege` | 통과. monitor 는 GET, SEARCH, LOOKUP 만 통과 | 그대로 차단한다 | `actions/v2/global_scope/processor.py:51`, `superadmin.py:22-34`, `actions/types.py:106` |
| 엔티티 권한 | `single_entity`, field `single_field` | `NotEnoughPermission` | 통과 | 통과 | `actions/v2/single_entity/validator/rbac.py:33-54` |
| 엔티티 권한, 소유자 조회 단계 | `key_field_lookup_ops`, `key_owner_lookup_ops` | `GenericBadRequest`. 없는 키와 권한 없음이 같은 예외다 | 통과. 없는 키는 `FieldNotFoundError` | 권한은 통과하고 없는 키는 여전히 `GenericBadRequest` | `actions/v2/lookup/processor.py:99-110,132-146` |
| 스코프 권한 | `scope`, `scope_search_ops`, field `search_ops` | `NotEnoughPermission`. 여러 스코프 중 하나라도 차단되면 전체를 거부 | 통과 | 통과 | `actions/v2/scope/validator/rbac.py:38-66` |
| 입력 검증 | 없음. service 와 repository 가 실행 중에 낸다 | 경우마다 다르다 | 해당 없음 | 해당 없음 | 아래 표 |

- 집행 스위치는 `manager.rbac.enforcement_enabled` 이고 기본값은 True 다(`config/unified.py:630-650`).
- 권한은 GET, SEARCH, LOOKUP 이 READ 로, DELETE 와 RESTORE 가 SOFT_DELETE 로, PURGE 가 HARD_DELETE 로 바뀐다(`actions/types.py:160-182`).
- 권한 검사가 실행보다 먼저 실행된다. superadmin 이 아닌 사용자는 대상이 없어도 `NotEnoughPermission` 을 받는다. 대상 없음을 보는 row 는 superadmin 이거나 집행을 끈 상태여야 한다.
- 본인에 대한 예외는 없다. 검사기가 건너뛰는 조건은 superadmin 과 집행 꺼짐뿐이다(`single_entity/validator/rbac.py:35-54`). 자기 키를 발급하는 사용자도 자기 사용자에 대한 권한을 받아야 한다.
- 키페어, 로그인 세션, 로그인 이력의 권한은 소유 사용자에 대한 사용자 엔티티 권한으로 본다. 권한 쿼리는 `entity_type == user` 이고 모든 필드에 적용된 row 만 읽는다(`repositories/ops/v2/permission/read.py:212-215`).

### 메서드별

| 메서드 | Gate (순서대로) | 권한 대상 | 거부 예외 |
|---|---|---|---|
| resolve_domain_id | 인증만 | — | 없는 이름은 `EntityNotFoundError`(`repositories/ops/repository.py:127-132`). 사용자 시나리오가 아니라 시나리오 표에 row 가 없다(열린 질문) |
| batch_load_by_ids | 엔티티 권한, 원소마다 | 각 사용자에 READ | 원소 단위. 요청에 없는데 필요한 값 절 아래의 표 |
| batch_lookup_by_emails | 인증, 이어서 엔티티 권한을 키마다(`bulk_lookup_ops`) | 찾은 각 사용자에 READ | 없는 email 과 읽을 수 없는 사용자의 email 은 모두 `GenericBadRequest` 원소. superadmin 에게는 없는 email 이 `EntityNotFoundError` 원소 |
| gql_admin_search, admin_search | 전역 역할 | — | `InsufficientPrivilege` |
| role_search | 전역 역할 | — | `InsufficientPrivilege`. 이름과 달리 스코프 검색이 아니라 전역 검색에 역할 조건을 붙인다(`adapter.py:469-470`) |
| gql_search_by_domain, domain_search | 인증(도메인 이름 조회), 이어서 스코프 권한 | 도메인 스코프에 사용자 READ | `EntityNotFoundError`, `NotEnoughPermission` |
| gql_search_by_project, project_search | 스코프 권한 | 프로젝트 스코프에 사용자 READ | `NotEnoughPermission` |
| scoped_search, gql_scoped_search | 스코프 권한, 항목마다 | 도메인, 프로젝트, 역할 스코프 각각에 사용자 READ(`services/user/actions/scoped_search.py:40-77,106-107`) | `NotEnoughPermission` |
| get | 엔티티 권한 | 사용자 READ | `NotEnoughPermission` |
| create_user | 인증(도메인 이름 조회), 이어서 스코프 권한, 이어서 입력 검증 | 도메인 스코프에 사용자 CREATE(`create_user.py:39-40`) | `EntityNotFoundError`, `NotEnoughPermission`, `UserConflict` |
| update_user_by_id | 엔티티 권한, 이어서 입력 검증 | 사용자 UPDATE. 삭제된 사용자에 DELETED 와 ACTIVE 를 주면 사용자 SOFT_DELETE 도, 그때 상태를 읽느라 READ 도 필요하다 | `NotEnoughPermission`, `UserModificationBadRequest`, `UserNotFound`, `UserDeleted`, `UserPurgeInProgress`, 기본 키 전환에서 `KeyPairNotFound` 또는 `KeyPairForbidden` |
| delete_user_by_id, restore_user_by_id | 엔티티 권한, 이어서 입력 검증 | 사용자 SOFT_DELETE | `NotEnoughPermission`, restore_user_by_id 는 삭제 상태가 아닌 사용자에 `UserModificationBadRequest` |
| purge_user_by_id | 엔티티 권한, 이어서 입력 검증 | 사용자 HARD_DELETE | `NotEnoughPermission`, 관리자 id 가 없으면 `UserNotFound`(`services/user/service.py:186`), 활성 커널에 vfolder 가 연결되어 있으면 `UserPurgeFailure` |
| bulk_create_users, bulk_create_users_with_keypair | 전역 역할, 이어서 입력 검증 | superadmin 만(monitor 는 읽기 호출만 통과) | `InsufficientPrivilege`, 항목별 실패는 응답에 담긴다 |
| bulk_update_users, bulk_purge_users | 전역 역할, 이어서 입력 검증 | superadmin 만 | `InsufficientPrivilege`, 항목별 실패는 응답에 담긴다. bulk_update_users 의 삭제와 복원은 항목마다 엔티티 권한을 따로 본다 |
| update_user | 엔티티 권한 | 사용자 UPDATE | `NotEnoughPermission` |
| issue_my_keypair | 엔티티 권한 | 사용자 UPDATE | `NotEnoughPermission` |
| switch_default_access_key | 엔티티 권한, 이어서 입력 검증 | 사용자 UPDATE | `NotEnoughPermission`, 남의 키나 비활성 키는 `KeyPairForbidden`, 없는 키는 `KeyPairNotFound`(`repositories/user/db_source/db_source.py:920-929`) |
| search_my_keypairs | 스코프 권한 | 자기 사용자 스코프에 사용자 READ(`keypair_ops.py:183-188`) | `NotEnoughPermission` |
| admin_create_keypair | 엔티티 권한, 이어서 입력 검증 | 대상 사용자 UPDATE. 이름과 달리 전역 역할 gate 가 아니다 | `NotEnoughPermission`, `KeypairResourcePolicyNotFound` |
| revoke_my_keypair, admin_delete_keypair | 소유자 조회, 이어서 엔티티 권한, 이어서 입력 검증 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission`, 기본 키면 `KeyPairForbidden`(`models/keypair/purgers.py:43-51`) |
| update_my_keypair, admin_update_keypair | 소유자 조회, 이어서 엔티티 권한, 이어서 입력 검증 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission`, 기본 키를 비활성화하면 `KeyPairForbidden`(`models/keypair/updaters.py:121-131`), 없는 정책은 `KeypairResourcePolicyNotFound` |
| admin_get_keypair | 소유자 조회, 이어서 엔티티 권한 | 소유자 READ 두 번 | `GenericBadRequest` |
| admin_register_ssh_keypair, admin_delete_ssh_keypair | 소유자 조회, 이어서 엔티티 권한 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission` |
| admin_get_ssh_keypair | 소유자 조회, 이어서 엔티티 권한 | 소유자 READ 두 번 | `GenericBadRequest` |
| admin_search_keypairs, gql_admin_search_keypairs | 전역 역할 | — | `InsufficientPrivilege` |
| login_session.admin_search, login_history.admin_search | 전역 역할 | — | `InsufficientPrivilege` |
| login_session.my_search, login_history.my_search | 스코프 권한 | 자기 사용자 스코프에 사용자 READ(`services/auth/actions/search_login_sessions.py:47-53`) | `NotEnoughPermission` |
| login_session.my_revoke | 소유자 조회, 이어서 엔티티 권한 | 소유자 READ, 이어서 소유자 UPDATE | `GenericBadRequest`, `NotEnoughPermission` |
| login_session.admin_revoke | 전역 역할, 이어서 입력 검증 | superadmin 만 | `InsufficientPrivilege`, 없는 세션은 `LoginSessionNotFoundError`(`repositories/auth/db_source/db_source.py:766-769`) |
| login_session.admin_unblock_user | 전역 역할 | superadmin 만 | `InsufficientPrivilege` |

사용자 노드를 응답하는 메서드는 모두 응답에 담기는 사용자 전원에 대해 READ 가 한 번 더 필요하다. `GetDefaultKeypairsAction` 이 소유자 전원을 한꺼번에 검사하고, 하나라도 차단되면 호출 전체가 `NotEnoughPermission` 으로 끝난다(`actions/v2/bulk/validator/rbac.py:91-98`). 생성 권한만 받은 사용자는 생성한 사용자를 응답으로 받지 못한다.

## 그래프에서의 위치

사용자는 도메인 스코프 안에 생성된다. 생성 gate 는 도메인 스코프의 사용자 CREATE 다(`create_user.py:39-40`). 그래서 권한을 받은 사용자 시나리오가 성립한다.

- 사용자 자신의 가상 엔티티가 자기를 own 하고 govern 한다(`repositories/ops/v2/graph_write.py:59-74`). 사용자 스코프에 둔 역할이 사용자 권한을 주면 그 사용자에 대한 엔티티 권한 검사와 스코프 권한 검사가 모두 통과한다.
- 도메인이 사용자를 own 하고 govern 한다(`graph_write.py:146-176`). 도메인 스코프에 둔 역할은 그 도메인 사용자 전원에 대해 통한다.
- 사용자 스코프의 프리셋 역할을 생성한다(`repositories/ops/v2/entity_write.py:131,323-360`). 소유자 프리셋은 `auto_assign: true` 라 사용자를 생성할 때 본인에게 배정된다(`seeds/manager/role_preset/user-owner.yaml:7`, `repositories/ops/v2/user/write.py:99-101`). 그 전에 생성한 사용자는 마이그레이션 `dc61fa027fc1` 이 배정했다.
- 시나리오 템플릿 데이터베이스에는 프리셋 row 가 없어 프리셋 역할이 하나도 생기지 않는다(`entity_write.py:379-380`). 필요한 권한은 역할을 직접 미리 저장한다.

## 요청에 없는데 필요한 값

| 값 | 어디서 오는가 | 근거 |
|---|---|---|
| 키페어 자원 정책 | 기본 표시가 붙은 정책 하나를 조회한다. 이 조회는 대체될 예정이라 시나리오에서 다루지 않는다 | `db_source.py:159-166` |
| 사용자 자원 정책 | 요청의 기본값 `"default"` | `common/dto/manager/v2/user/request.py:89-92`, `models/user/creators.py:116` |
| 개인 프로젝트의 자원 정책 | 코드가 고정한 이름 `"default"` | `models/project/creators.py:66-67` |
| 개인 프로젝트 이름 | 사용자 이름. 겹치면 `-2` 부터 `-999`, 그래도 겹치면 사용자 id | `repositories/ops/v2/user/write.py:175-199` |
| access key, secret key | 생성한다. secret 은 키 provider 풀로 암호화한다 | `common/auth/keypair.py`, `repositories/auth/keypair_secrets.py` |
| default SSH keypair | 사용자와 같은 트랜잭션에서 생성한다. 비밀키는 키 provider 풀로 암호화한다 | `repositories/auth/keypair_secrets.py`, `repositories/ops/v2/user/write.py` |
| 기본 액세스 키의 활성, 관리자 표시 | 사용자 상태가 ACTIVE 인지, 역할이 SUPERADMIN 이나 ADMIN 인지 | `write.py:106-107` |
| 비밀번호 해시 설정 | manager 설정 `auth.password_hash_*` | `adapter.py:491-496` |
| 도메인 id | 이름으로 조회한다 | `adapter.py:217-220` |
| 새로 발급하는 키페어의 활성, 관리자, 정책, 요청 한도 | 사용자의 기본 키를 따른다 | `db_source.py:896-901` |
| 관리자 영구 삭제의 관리자 사용자 | 요청 외 인자. 공유 vfolder 와 배포 엔드포인트를 전달받는다 | `services/user/service.py:185-259` |

## 전체를 사용해야 하는 합성 연산

`V2UserWriteOps.create_user(FullUserCreator)`(`repositories/ops/v2/user/write.py:84-111`). adapter 의 생성과 시나리오 seed(`tests/scenario/bai_scenario/seeds/user/user.py`)가 같은 연산을 사용한다.

| 순서 | 작성하는 row | 근거 |
|---|---|---|
| 1 | 도메인 가상 엔티티(없을 때만) | `write.py:87`, `graph_write.py:44-69` |
| 2 | 사용자 row | `entity_write.py:127-128` |
| 3 | 사용자 가상 엔티티, 자기 소속, 스코프 연결 | `entity_write.py:130` |
| 4 | 사용자 스코프의 프리셋 역할과 권한 | `entity_write.py:131,323-360` |
| 5 | 도메인이 사용자를 own 하고 govern 하는 row | `entity_write.py:132`, `graph_write.py:146-176` |
| 6 | 사용자 스코프와 도메인 스코프의 자동 배정 역할 배정 | `write.py:92`, `entity_write.py:296-319` |
| 7 | 기본 액세스 키 | `write.py:93,97-111` |
| 8 | 개인 프로젝트와 그 프리셋 역할, 도메인 소유 | `write.py:94,146-165` |
| 9 | 개인 프로젝트 멤버 목록 등재 | `write.py:164`, `repositories/ops/v2/roster/write.py:191-198` |

adapter 경로는 앞뒤에 둘을 추가한다. 같은 쓰기 트랜잭션 안에서 이메일과 사용자 이름 중복을 먼저 보고(`db_source.py:188-191`), 뒤에 요청의 프로젝트와 도메인의 모델 스토어 프로젝트에 등재한다(`write.py:113-124,213-226`).

| 항목 | seed | adapter 생성 |
|---|---|---|
| 중복 검사 | 없음 | 있음 |
| 키페어 정책 | 앞 단계가 생성한 정책 | 기본 표시 정책 조회(대체 예정) |
| 키 값 | 평문 | 생성, 암호화 |
| 프로젝트 등재 | 없음 | 있음 |

## adapter 가 요구하는 의존성

검색 넷은 service 를 거치지 않고 ops 로 응답한다(`services/auth/processors.py:211-218`).

## 외부 service 경계

에이전트 RPC 에 접근하는 경로는 없다.

## 응답에 담기는 것

기본은 노드 전체 비교다. 아래는 값을 말할 수 없거나 조건으로 확인하는 항목이다.

### 사용자 노드

| 항목 | 검사 |
|---|---|
| `id` | 무시. 데이터베이스가 생성한다 |
| `basic_info.*`, `status.status`, `status.need_password_change`, `organization.role`, `organization.resource_policy`, `security.allowed_client_ip`, `security.totp_activated`, `security.sudo_session_enabled`, `container.*` | 요청 값 또는 요청에 없는데 필요한 값 절과 열린 질문이 적은 기본값과 같다 |
| `status.status_info` | 생성 직후 None, 상태를 변경하면 `"admin-requested"`(`db_source.py:317-319,347-363`) |
| `organization.domain_name` | 앞 단계가 생성한 도메인 이름과 같다 |
| `organization.main_access_key` | 그 사용자의 기본 키와 같다. 기본 키가 비활성이면 None(`models/keypair/queriers.py:28-29`) |
| `security.totp_activated_at` | None |
| `timestamps.created_at`, `timestamps.modified_at` | 이 실행이 기록한 시각 |

### 키페어 노드

| 항목 | 검사 |
|---|---|
| `id`, `access_key` | 생성한 키면 무시. 미리 저장한 키면 그 키와 같다 |
| `is_active`, `is_admin`, `is_default`, `rate_limit`, `resource_policy` | 값으로 본다 |
| `num_queries` | 0 |
| `last_used` | None |
| `ssh_public_key` | deprecated. 소유자의 default SSH keypair 공개키로, 한 사용자의 keypair 모두에 같다 |
| `created_at`, `modified_at` | 이 실행이 기록한 시각 |
| `user_id` | 소유 사용자와 같다 |
| 발급 응답의 secret key | 무시. 매번 새로 생성한다 |

### 목록 응답

| 항목 | 검사 |
|---|---|
| `items` | 미리 저장한 row 의 이름이나 access key 목록으로 비교한다. 순서를 보장하지 않는 검색은 이름순으로 정렬해 비교한다 |
| 순서 | 한 트랜잭션에서 미리 저장한 row 는 생성 시각이 같다. 생성 시각 내림차순 뒤의 동률 정렬(사용자는 id, 키페어는 access key, 로그인 세션과 이력은 id, 모두 오름차순)이 순서를 정한다 |
| `total_count`, `pagination.total` | 값 |
| `has_next_page`, `has_previous_page` | 값 |
| `pagination.offset`, `pagination.limit` | 값. 키페어 전체 검색은 limit 을 생략하면 None 을 응답한다(`adapter.py:988-992`) |

### 성공만 응답하는 것

`DeleteUserPayload`, `RestoreUserPayload`, `PurgeUserPayload`, `RevokeMyKeypairPayload`, `SwitchMyMainAccessKeyPayload`, `UpdateMyAllowedClientIPPayload`, `RevokeLoginSessionPayload`, `UnblockUserPayload` 는 `success` 만 담는다. 이 row 들은 응답과 함께 같은 adapter 의 조회 호출을 뒤이어 호출해 변경된 결과가 조회되는지 본다. 시나리오 표의 기대 칸에 있는 "뒤이은" 조회가 그것이다.

## 열린 질문

1. **auth 7건 중 adapter 를 거치지 않는 것이 다섯이다.** 로그인 세션 adapter 가 호출하는 것은 `global_revoke_login_session`, `global_unblock_user` 둘이다(`api/adapters/login_session/adapter.py:136,145`). 나머지 다섯은 REST handler 가 processor 를 바로 호출한다. `authorize`, `get_role`, `update_password_no_auth` 는 `api/rest/auth/handler.py`, `public_resolve_access_key_scope` 는 `api/rest/session/handler.py` 등 셋이다. vfolder 목록의 이메일 위임은 `LookupUserAction` 을 호출한다(`api/rest/vfolder/handler.py`). `authorize` 와 `update_password_no_auth` 는 Action 이 요청 객체를 담는다(`services/auth/actions/authorize.py`). 이번 작업은 handler 호출을 adapter 로 옮기지 않고, 다섯의 시나리오는 뒤로 미룬다.
2. **로그인 세션과 로그인 이력의 write spec 을 추가한다.** 지금은 인증 흐름의 raw insert 만 있다(`repositories/auth/db_source/db_source.py:557-597`). 사용자가 own 하는 필드 creator 둘을 `models/login_session/` 아래에 두고, 시나리오는 `adding` 으로 미리 저장한다. 추가 범위는 구현 단계에서 따로 설명한다.
3. **역할 스코프 항목의 권한 대상.** 스코프 검색에 역할 스코프를 주면 역할 id 를 스코프로 삼아 사용자 READ 를 검사한다(`services/user/actions/scoped_search.py:70-77`). 역할을 govern 하는 스코프에 준 권한이 그 검사를 통과하는지 확인하지 못해 시나리오 표에 row 를 두지 않았다.
4. **소속 프로젝트 항목에 빈 값을 주면 아무 일도 없다.** 요청 설명은 "빈 값이면 비운다"(`common/dto/manager/v2/user/request.py:149`)인데 adapter 는 무시한다(`adapter.py:615-619`). 시나리오 표는 지금 동작을 row 로 고정했다. 설명과 동작 중 어느 쪽을 수정해야 하는지에 대한 결정이 필요하다.
5. **영구 삭제는 먼저 삭제된 상태를 요구하지 않는다.** 상태 검사가 없다(`services/user/service.py:185-259`). 의도인지 확인하지 못했다.
6. **superadmin 이 없는 사용자를 읽거나 수정할 때의 예외.** 읽기는 docstring 상 `UserNotFound`(`service.py:179-180`)지만 repository 까지 따라가지 않았다. 시나리오 표에 row 를 두지 않았다.
7. **사용자 수정의 소속 동기화와 기본 키 전환은 수정과 다른 트랜잭션이다.** 기본 키 전환이 실패해도 앞의 수정은 남는다(`adapter.py:621-623`, `db_source.py:697-711`). 이 부분 실패를 row 로 고정하는 방안에 대한 결정이 필요하다.
8. **도메인 이름으로 도메인 id 를 얻는 메서드는 사용자 시나리오가 아니다.** `resolve_domain_id`(`adapter.py:217-220`)는 도메인만 조회하므로 시나리오 표에 row 를 두지 않았고, report 의 호출되지 않은 호출에 남는다. adapter 안에서는 생성과 도메인 검색이 사용하고, 밖에서는 일괄 생성 resolver 가 호출한다(`api/gql/user/resolver/mutation.py:122`). 그 호출을 다른 경로로 옮기면 private 으로 변경할 수 있다.
9. **로그인 세션 해지가 남기는 이력은 시나리오가 보지 않는다.** 해지는 세션 row 를 삭제하면서 사용자 해지 또는 관리자 해지 결과의 이력 한 row 를 작성한다(`repositories/auth/db_source/db_source.py:744-786`). 시나리오 한 row 가 adapter 하나만 받아 이력 adapter 로 뒤이어 조회할 수 없다.
10. **로그인 세션 adapter 와 로그인 이력 adapter 의 문서.** 두 패키지에는 `KNOWLEDGE.md` 가 없고 이 문서가 두 패키지를 다룬다. 이 문서를 참조하는 문서를 추가하는 방안과 report 가 두 패키지로 나뉘는 것을 맞추는 방안에 대한 결정이 필요하다.
