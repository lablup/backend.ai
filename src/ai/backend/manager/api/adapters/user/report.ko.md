## user

[배경](/src/ai/backend/manager/api/adapters/user/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/user/adapter.py)

시나리오: 미완성 3 / 53

- ops 구성 (27)
  - LoginHistoryAdapter.admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - LoginHistoryAdapter.batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - LoginHistoryAdapter.my_search: 대표 성공 ✓ · 대표 거부 ✓
  - LoginSessionAdapter.admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - LoginSessionAdapter.batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - LoginSessionAdapter.my_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.admin_search_keypairs: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.batch_lookup_by_emails: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.bulk_get_keypair_ids: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.bulk_lookup_keypair_access_keys: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.domain_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.gql_admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.gql_admin_search_keypairs: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.gql_scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.gql_search_by_domain: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.gql_search_by_project: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.project_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.resolve_domain_id: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.role_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - UserAdapter.search_my_keypairs: 대표 성공 ✓ · 대표 거부 ✓
  - UserConfigAdapter.delete_default_auto_generated_file: 대표 성공 ✗ · 대표 거부 ✓: SCENARIO-GAP
  - UserConfigAdapter.get_default_auto_generated_file: 대표 성공 ✗ · 대표 거부 ✓: SCENARIO-GAP
  - UserConfigAdapter.get_default_auto_generated_files: 대표 성공 ✓ · 대표 거부 ✓
  - UserConfigAdapter.update_default_auto_generated_file: 대표 성공 ✗ · 대표 거부 ✓: SCENARIO-GAP
- ops + 직접 구현 (7)
  - UserAdapter.bulk_create_users: 성공 있음 1 · 거부 있음 1 (atomic_bulk_get_ops, global_scope)
  - UserAdapter.bulk_create_users_with_keypair: 성공 있음 1 · 거부 있음 1 (atomic_bulk_get_ops, global_scope)
  - UserAdapter.bulk_update_users: 성공 있음 3 · 거부 있음 1 (atomic_bulk_get_ops, global_scope, partial_bulk_get_ops, single_entity)
  - UserAdapter.create_user: 성공 있음 1 · 거부 있음 2 (atomic_bulk_get_ops, scope)
  - UserAdapter.delete_user_by_id: 성공 있음 1 · 거부 있음 1 (atomic_bulk_get_ops, single_entity)
  - UserAdapter.get: 성공 있음 1 · 거부 있음 1 (atomic_bulk_get_ops, single_entity)
  - UserAdapter.update_user_by_id: 성공 있음 7 · 거부 있음 6 (atomic_bulk_get_ops, single_entity)
- 직접 구현 (19)
  - LoginSessionAdapter.admin_revoke: 성공 있음 1 · 거부 있음 2 (global_scope)
  - LoginSessionAdapter.admin_unblock_user: 성공 있음 2 · 거부 있음 1 (global_scope)
  - LoginSessionAdapter.my_revoke: 성공 있음 1 · 거부 있음 3 (single_field)
  - UserAdapter.admin_create_keypair: 성공 있음 1 · 거부 있음 2 (single_entity)
  - UserAdapter.admin_delete_keypair: 성공 있음 1 · 거부 있음 3 (single_field)
  - UserAdapter.admin_delete_ssh_keypair: 성공 있음 1 · 거부 있음 2 (single_entity)
  - UserAdapter.admin_get_keypair: 성공 있음 1 · 거부 있음 1 (single_field)
  - UserAdapter.admin_get_ssh_keypair: 성공 있음 1 · 거부 있음 1 (single_entity)
  - UserAdapter.admin_register_ssh_keypair: 성공 있음 1 · 거부 있음 2 (single_entity)
  - UserAdapter.admin_update_keypair: 성공 있음 1 · 거부 있음 3 (single_field)
  - UserAdapter.bulk_purge_users: 성공 있음 2 · 거부 있음 1 (global_scope)
  - UserAdapter.issue_my_keypair: 성공 있음 2 · 거부 있음 1 (single_entity)
  - UserAdapter.purge_user_by_id: 성공 있음 1 · 거부 있음 2 (single_entity)
  - UserAdapter.restore_user_by_id: 성공 있음 1 · 거부 있음 2 (single_entity)
  - UserAdapter.revoke_my_keypair: 성공 있음 1 · 거부 있음 4 (single_field)
  - UserAdapter.switch_default_access_key: 성공 있음 1 · 거부 있음 2 (single_entity)
  - UserAdapter.update_my_keypair: 성공 있음 1 · 거부 있음 3 (single_field)
  - UserAdapter.update_user: 성공 있음 1 · 거부 있음 1 (single_entity)
  - UserConfigAdapter.create_auto_generated_file: 성공 있음 1 · 거부 있음 2 (single_entity)

**LoginHistoryAdapter.admin_search**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 이력 검색에서 superadmin 이 조회하면, 사용자와 무관하게 미리 저장한 이력이 생성 시각 내림차순으로 옵니다](#login_history-the-superadmin-searches-every-users-login-history) | 성공 |
| [권한 받은 사용자가 이력 전체 검색을 하려 하면, 전역 역할 문이 막습니다](#login_history-a-user-who-is-not-the-superadmin-may-not-search-every-login-history) | 거부 |

**LoginHistoryAdapter.batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 를 받은 사용자가 자기 이력과 없는 id 를 한 번에 읽으면, 자기 이력 전체와 빈 값이 차례로 옵니다](#login_history-a-user-granted-read-on-themselves-loads-their-own-history-by-id) | 성공 |
| [권한을 받지 않은 사용자가 자기 이력과 없는 id 를 한 번에 읽으면, 그 이력 항목은 권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다](#login_history-a-user-granted-nothing-gets-a-rejection-for-their-own-history) | 거부 |

**LoginHistoryAdapter.my_search**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 를 받은 사용자가 조회하면, 다른 사용자의 이력은 빠집니다](#login_history-a-user-granted-read-on-themselves-searches-only-their-own-login-history) | 성공 |
| [역할 없이 자기 이력을 조회하려 하면, 본인이어도 스코프 권한 문이 막습니다](#login_history-a-user-granted-nothing-may-not-search-their-own-login-history) | 거부 |

**LoginSessionAdapter.admin_search**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 세션 검색에서 superadmin 이 페이지 인자 없이 조회하면, 사용자와 무관하게 미리 저장한 세션이 생성 시각 내림차순으로 옵니다](#login_sessions-the-superadmin-searches-every-users-login-sessions) | 성공 |
| [권한 받은 사용자가 세션 전체 검색을 하려 하면, 전역 역할 문이 막습니다](#login_sessions-a-user-who-is-not-the-superadmin-may-not-search-every-login-session) | 거부 |

**LoginSessionAdapter.batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 를 받은 사용자가 자기 세션과 없는 id 를 한 번에 읽으면, 자기 세션 전체와 빈 값이 차례로 옵니다](#login_sessions-a-user-granted-read-on-themselves-loads-their-own-session-by-id) | 성공 |
| [권한을 받지 않은 사용자가 자기 세션과 없는 id 를 한 번에 읽으면, 그 세션 항목은 권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다](#login_sessions-a-user-granted-nothing-gets-a-rejection-for-their-own-session) | 거부 |

**LoginSessionAdapter.my_search**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 를 받은 사용자가 조회하면, 다른 사용자의 세션은 빠집니다](#login_sessions-a-user-granted-read-on-themselves-searches-only-their-own-login-sessions) | 성공 |
| [역할 없이 자기 세션을 조회하려 하면, 본인이어도 스코프 권한 문이 막습니다](#login_sessions-a-user-granted-nothing-may-not-search-their-own-login-sessions) | 거부 |

**UserAdapter.admin_search**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 검색에서 superadmin 이 필터 없이 조회하면, 삭제 상태 사용자를 포함해 미리 저장한 사용자가 모두 옵니다](#searching-the-superadmin-searching-every-user-counts-deleted-ones-too) | 성공 |
| [도메인 스코프 권한을 받은 사용자라도 전체 검색을 하려 하면, 전역 역할 문이 막습니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-user) | 거부 |

**UserAdapter.admin_search_keypairs**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 키 검색에서 superadmin 이 페이지 인자 없이 조회하면, 모든 사용자의 키가 오고 limit 자리는 비어서 옵니다](#managing_keypairs-the-superadmin-searching-every-key-gets-every-users-key) | 성공 |
| [권한 받은 사용자가 키 전체 검색을 하려 하면, 전역 역할 문이 막습니다](#managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key) | 거부 |

**UserAdapter.batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [권한 없는 사용자가 빈 id 목록을 주면, 어떤 액션도 호출하지 않고 빈 목록이 응답으로 옵니다](#reading-a-batch-load-of-no-ids-answers-an-empty-list) | 성공 |
| [superadmin 이 있는 id 와 없는 id 를 함께 요청하면, 권한 문을 지나 없는 원소 자리에 빈 값이 옵니다](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |
| [한 사용자에게만 읽기 권한을 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, 없는 id 를 한 번에 요청하면, 입력 순서대로 원소별 결과가 옵니다](#reading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order) | 거부 |

**UserAdapter.batch_lookup_by_emails**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 그 사용자의 email 을 찾으면, 그 사용자의 id 가 응답으로 옵니다](#reading-a-user-granted-read-on-another-user-looks-up-their-id-by-email) | 성공 |
| [권한 없는 사용자가 빈 email 목록을 주면, 어떤 액션도 호출하지 않고 빈 목록이 응답으로 옵니다](#reading-an-email-lookup-of-no-emails-answers-an-empty-list) | 성공 |
| [한 사용자에게만 읽기 권한을 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, 없는 email 을 한 번에 찾으면, 첫째는 id, 나머지 둘은 같은 거부가 입력 순서대로 옵니다](#reading-an-unreadable-user-and-a-missing-email-are-refused-alike) | 거부 |

**UserAdapter.bulk_get_keypair_ids**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 그 사용자의 키와 없는 id 를 한 번에 읽으면, 키 전체와 빈 값이 차례로 옵니다](#loading_keypairs-a-user-granted-read-on-another-loads-their-key-by-id) | 성공 |
| [권한을 받지 않은 사용자가 다른 사용자의 키와 없는 id 를 한 번에 읽으면, 그 키 항목은 권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다](#loading_keypairs-a-user-granted-nothing-gets-a-rejection-for-anothers-key) | 거부 |

**UserAdapter.bulk_lookup_keypair_access_keys**

| 시나리오 | 판정 |
|---|---|
| [사용자가 access key 와 어떤 키도 아닌 access key 를 한 번에 찾으면, 첫째는 그 키의 id 로, 둘째는 빈 값으로 옵니다](#loading_keypairs-a-user-looks-up-the-keypair-an-access-key-names) | 성공 |
| [로그인 문맥 없이 access key 로 키를 찾으면, 사용자를 찾을 수 없다는 것으로 거부됩니다](#loading_keypairs-looking-up-an-access-key-without-login-is-refused) | 거부 |

**UserAdapter.domain_search**

| 시나리오 | 판정 |
|---|---|
| [도메인 스코프에서 사용자 READ 를 받은 사용자가 도메인 이름으로 조회하면, 다른 도메인 사용자는 빠집니다](#searching-a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users) | 성공 |
| [역할을 받지 않은 사용자가 도메인 이름으로 조회하려 하면, 스코프 권한 문이 막습니다](#searching-a-user-granted-nothing-may-not-search-a-domain-by-name) | 거부 |
| [권한 받은 사용자가 어떤 도메인도 아닌 이름으로 조회하려 하면, 스코프 검사 전에 이름 조회 단계가 대상 없음으로 막습니다](#searching-searching-a-domain-name-nothing-answers-to-is-not-found) | 거부 |

**UserAdapter.gql_admin_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 커서와 페이지 인자를 모두 생략하고 조회하면, 생성 시각 내림차순으로 열 명까지 오고 다음 페이지 여부가 함께 옵니다](#searching-a-gql-search-without-page-arguments-answers-the-newest-ten) | 성공 |
| [권한 받은 사용자가 GQL 전체 검색을 하려 하면, 전역 역할 문이 막습니다](#searching-a-user-who-is-not-the-superadmin-may-not-gql-search-every-user) | 거부 |

**UserAdapter.gql_admin_search_keypairs**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 GQL 키 검색에서 superadmin 이 정책 이름을 주면, 그 정책을 사용하는 키만 옵니다](#managing_keypairs-the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only) | 성공 |
| [권한 받은 사용자가 GQL 키 검색을 하려 하면, 전역 역할 문이 막습니다](#managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql) | 거부 |

**UserAdapter.gql_scoped_search**

| 시나리오 | 판정 |
|---|---|
| [같은 권한으로 GQL 스코프 검색을 하면, 두 스코프 사용자가 커서 응답으로 옵니다](#searching-a-gql-scoped-search-over-two-granted-scopes-joins-their-users) | 성공 |
| [한 스코프에만 READ 를 받고 GQL 스코프 검색에 둘을 주면, 스코프 권한 문이 전체를 막습니다](#searching-one-scope-without-a-grant-refuses-the-whole-gql-scoped-search) | 거부 |

**UserAdapter.gql_search_by_domain**

| 시나리오 | 판정 |
|---|---|
| [같은 권한으로 GQL 도메인 검색을 하면, 그 도메인 사용자만 커서 응답으로 옵니다](#searching-a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users) | 성공 |
| [역할 없이 GQL 도메인 검색을 하면, 스코프 권한 문이 막습니다](#searching-a-user-granted-nothing-may-not-gql-search-a-domain) | 거부 |

**UserAdapter.gql_search_by_project**

| 시나리오 | 판정 |
|---|---|
| [같은 권한으로 GQL 프로젝트 검색을 하면, 멤버 목록의 사용자만 커서 응답으로 옵니다](#searching-a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster) | 성공 |
| [역할 없이 GQL 프로젝트 검색을 하면, 스코프 권한 문이 막습니다](#searching-a-user-granted-nothing-may-not-gql-search-a-project) | 거부 |

**UserAdapter.project_search**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 스코프에서 사용자 READ 를 받은 사용자가 그 프로젝트로 조회하면, 멤버 목록에 오른 사용자만 옵니다](#searching-a-user-granted-on-a-project-searching-it-finds-only-its-roster) | 성공 |
| [역할 없이 프로젝트 검색을 하면, 스코프 권한 문이 막습니다](#searching-a-user-granted-nothing-may-not-search-a-project) | 거부 |

**UserAdapter.resolve_domain_id**

| 시나리오 | 판정 |
|---|---|
| [도메인에 속한 사용자가 그 도메인의 이름으로 id 를 찾으면, 그 도메인의 id 가 응답으로 옵니다](#resolving_domain-a-user-resolves-the-id-of-a-domain-by-its-name) | 성공 |
| [아무 도메인도 갖지 않은 이름으로 id 를 찾으면, 대상이 없다는 것으로 거부됩니다](#resolving_domain-resolving-a-domain-name-nothing-answers-to-is-not-found) | 거부 |

**UserAdapter.role_search**

| 시나리오 | 판정 |
|---|---|
| [역할이 걸린 스코프의 사용자 READ 를 받은 사용자가 역할 하나를 주면, 그 역할을 배정받은 사용자만 옵니다](#searching-a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders) | 성공 |
| [전역 역할이 문인 역할 검색에서 superadmin 이 역할 하나를 주면, 그 역할을 배정받은 사용자만 옵니다](#searching-the-superadmin-searching-by-role-finds-only-its-holders) | 성공 |
| [아무 권한도 받지 않은 사용자가 역할로 조회하려 하면, 스코프 권한 문이 막습니다](#searching-a-user-granted-nothing-may-not-search-by-role) | 거부 |

**UserAdapter.scoped_search**

| 시나리오 | 판정 |
|---|---|
| [도메인과 프로젝트 스코프 모두에서 READ 를 받은 사용자가 두 스코프를 함께 주면, 두 스코프의 사용자가 중복 없이 합쳐집니다](#searching-a-scoped-search-over-two-granted-scopes-joins-their-users) | 성공 |
| [권한 받은 사용자가 페이지 인자 없이 스코프 검색을 하면, limit 50 offset 0이 응답에 실립니다](#searching-a-scoped-search-without-page-arguments-answers-up-to-fifty) | 성공 |
| [첫 스코프에만 READ 를 받은 사용자가 두 스코프를 함께 주면, 스코프 권한 문이 전체를 막습니다](#searching-one-scope-without-a-grant-refuses-the-whole-scoped-search) | 거부 |

**UserAdapter.search_my_keypairs**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 를 받은 사용자가 자기 키를 조회하면, 다른 사용자의 키는 빠집니다](#own_keypairs-a-user-granted-read-searching-their-keys-sees-only-their-own) | 성공 |
| [권한 받은 사용자가 페이지 인자 없이 조회하면, 생성 시각 내림차순 열 개와 다음 페이지 여부가 응답으로 옵니다](#own_keypairs-searching-own-keys-without-page-arguments-answers-the-ten-newest) | 성공 |
| [역할 없이 자기 키를 조회하려 하면, 스코프 권한 문이 막습니다](#own_keypairs-a-user-granted-nothing-may-not-search-their-own-keys) | 거부 |

**UserConfigAdapter.delete_default_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [권한을 받지 않은 사용자가 자기 설정 파일을 지우려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-delete-a-config-file) | 거부 |
| [READ 와 UPDATE 를 받은 사용자가 기본으로 표시되지 않은 설정 파일을 지우려 하면, 대상이 없다는 것으로 거부됩니다](#config_files-deleting-a-config-file-that-is-not-marked-default-is-not-found) | 거부 |

**UserConfigAdapter.get_default_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 기본으로 표시되지 않은 설정 파일을 읽으려 하면, 대상이 없다는 것으로 거부됩니다](#config_files-a-config-file-that-is-not-marked-default-is-not-found) | 거부 |
| [권한을 받지 않은 사용자가 자기 설정 파일을 읽으려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-read-a-config-file) | 거부 |

**UserConfigAdapter.get_default_auto_generated_files**

| 시나리오 | 판정 |
|---|---|
| [READ 를 받은 사용자가 자기 설정 파일 중 기본으로 표시된 것을 훑으면, 빈 목록이 옵니다](#config_files-a-user-granted-read-on-themselves-lists-no-default-config-file) | 성공 |
| [권한을 받지 않은 사용자가 자기 설정 파일을 훑으려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-list-their-config-files) | 거부 |

**UserConfigAdapter.update_default_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [권한을 받지 않은 사용자가 자기 설정 파일을 고치려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-update-a-config-file) | 거부 |
| [READ 와 UPDATE 를 받은 사용자가 기본으로 표시되지 않은 설정 파일을 고치려 하면, 대상이 없다는 것으로 거부됩니다](#config_files-updating-a-config-file-that-is-not-marked-default-is-not-found) | 거부 |

**UserAdapter.bulk_create_users**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 사용자 하나를 일괄 생성하면, 만든 사용자 하나가 오고 실패한 것은 없습니다](#creating-the-superadmin-bulk-creates-a-user) | 성공 |
| [도메인 스코프에서 CREATE 를 받은 사용자라도 일괄 생성하려 하면, 전역 역할 문이 막습니다](#creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users) | 거부 |

**UserAdapter.bulk_create_users_with_keypair**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 키를 함께 받는 일괄 생성으로 사용자 하나를 만들면, 만든 사용자와 그 기본 키가 비밀 키와 함께 오고 실패한 것은 없습니다](#creating-the-superadmin-bulk-creates-a-user-and-gets-its-keypair) | 성공 |
| [권한 받은 사용자가 이 일괄 생성을 하려 하면, 전역 역할 문이 막습니다](#creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs) | 거부 |

**UserAdapter.bulk_update_users**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 일괄 수정으로 활성 사용자에 DELETED, 삭제 상태 사용자에 ACTIVE, 다른 삭제 상태 사용자에 전체 이름을 주면, 둘은 삭제와 복원을 거쳐 수정 목록에, 하나는 실패로 담깁니다](#retiring-a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit) | 성공 |
| [superadmin 이 일괄 수정과 함께 다른 사용자의 키로 기본 키 전환을 주면, 그 사용자는 수정 목록에서 빠지고 실패로 담깁니다](#editing-a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed) | 성공 |
| [전역 역할이 문인 일괄 수정에서 superadmin 이 있는 사용자와 이름이 겹치게 변경하는 사용자를 함께 주면, 하나는 수정되고 하나는 사용자 id 와 함께 실패로 담깁니다](#editing-the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart) | 성공 |
| [도메인 스코프에서 UPDATE 를 받은 사용자라도 일괄 수정하려 하면, 전역 역할 문이 막습니다](#editing-a-user-who-is-not-the-superadmin-may-not-bulk-edit-users) | 거부 |

**UserAdapter.create_user**

| 시나리오 | 판정 |
|---|---|
| [도메인 스코프에서 사용자 읽기와 생성 권한을 받은 사용자가 그 도메인에 사용자를 만들면, 만든 사용자 전체와 기본 키가 비밀 키와 함께 옵니다](#creating-a-user-granted-create-on-a-domain-makes-a-user-in-it) | 성공 |
| [역할을 받지 않은 사용자가 생성하려 하면, 도메인 스코프 권한 문이 막습니다](#creating-a-user-granted-nothing-may-not-create-a-user) | 거부 |
| [권한 받은 사용자가 어떤 도메인도 아닌 이름을 주면, 도메인 이름 조회 단계가 대상 없음으로 막습니다](#creating-a-user-may-not-be-created-in-a-domain-name-nothing-answers-to) | 거부 |

**UserAdapter.delete_user_by_id**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 SOFT_DELETE 를 받은 사용자가 삭제하면, 성공이 오고 그 사용자 상태가 삭제로 변경됩니다](#retiring-a-user-granted-soft-delete-marks-another-user-deleted) | 성공 |
| [역할 없이 삭제하려 하면, 엔티티 권한 문이 막습니다](#retiring-a-user-granted-nothing-may-not-delete-another-user) | 거부 |

**UserAdapter.get**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 읽으면, 기본 키까지 채운 노드 전체가 응답으로 옵니다](#reading-a-user-granted-read-on-another-user-reads-their-whole-node) | 성공 |
| [아무 역할도 받지 않은 사용자가 다른 사용자를 읽으려 하면, 엔티티 권한 문이 막습니다](#reading-a-user-granted-nothing-may-not-read-another-user) | 거부 |

**UserAdapter.update_user_by_id**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 전체 이름만 주면, 전체 이름만 변경된 노드가 응답으로 옵니다](#editing-a-user-granted-update-changing-only-the-full-name-leaves-the-rest) | 성공 |
| [대상 사용자 스코프에서 SOFT_DELETE 와 READ 를 받은 사용자가 삭제 상태 사용자에 수정으로 ACTIVE 를 주면, 복원과 같이 활성이 됩니다](#retiring-an-edit-to-active-on-a-deleted-user-restores-the-user) | 성공 |
| [대상 사용자 스코프에서 SOFT_DELETE 와 READ 를 받은 사용자가 수정으로 DELETED 를 주면, 삭제와 같이 삭제 상태가 됩니다](#retiring-an-edit-to-deleted-soft-deletes-the-user) | 성공 |
| [대상 사용자 스코프에서 UPDATE 와 READ 를 받은 다른 사용자가 비밀번호 변경을 요구받는 사용자에게 새 비밀번호만 주면, 요구가 남은 노드가 응답으로 옵니다](#editing-another-users-new-password-leaves-the-password-change-requirement) | 성공 |
| [권한 받은 사용자가 대상 사용자의 다른 키를 기본 키로 지정하면, 수정이 반영된 뒤 기본 키가 옮겨간 노드가 응답으로 옵니다](#editing-naming-a-default-key-in-an-edit-moves-the-default-to-it) | 성공 |
| [권한 받은 사용자가 소속 프로젝트 자리에 빈 값을 주면, 소속을 건드리지 않고 나머지 수정만 반영됩니다](#editing-null-project-ids-in-an-edit-leave-the-membership-as-it-is) | 성공 |
| [비밀번호 변경을 요구받는 사용자가 자기 사용자 스코프에서 UPDATE 와 READ 를 받고, 새 비밀번호와 요구 해제를 함께 주면, 요구가 해제된 노드가 응답으로 옵니다](#editing-setting-ones-own-new-password-lifts-the-password-change-requirement) | 성공 |
| [역할을 받지 않은 사용자가 수정하려 하면, 엔티티 권한 문이 막습니다](#editing-a-user-granted-nothing-may-not-edit-another-user) | 거부 |
| [권한 받은 사용자가 이미 쓰이는 사용자 이름을 주면, 입력 검증이 막습니다](#editing-a-username-another-user-holds-may-not-be-taken) | 거부 |
| [대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 삭제 상태 사용자의 전체 이름을 변경하면, 삭제된 사용자라 거부됩니다](#retiring-an-edit-of-another-field-on-a-deleted-user-is-refused) | 거부 |
| [대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 수정으로 BEFORE_VERIFICATION 을 주면, 입력 검증이 막습니다](#retiring-an-edit-to-a-status-other-than-active-or-inactive-is-refused) | 거부 |
| [대상 사용자 스코프에서 UPDATE 와 READ 만 받은 사용자가 수정으로 DELETED 를 주면, 삭제의 엔티티 권한 문이 막습니다](#retiring-an-edit-to-deleted-is-refused-without-soft-delete) | 거부 |
| [삭제 상태 사용자에 수정으로 DELETED 만 주면, 아무것도 변경되지 않고 그 사용자가 응답으로 옵니다](#retiring-an-edit-to-deleted-on-a-deleted-user-changes-nothing) | 거부 |

**LoginSessionAdapter.admin_revoke**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 관리자 회수에서 superadmin 이 다른 사용자의 세션을 회수하면, 성공이 오고 세션 전체 검색에서 빠지며 관리자가 회수했다는 이력이 생깁니다](#login_sessions-the-superadmin-revokes-another-users-login-session) | 성공 |
| [권한 받은 사용자가 관리자 회수를 하려 하면, 전역 역할 문이 막습니다](#login_sessions-a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin) | 거부 |
| [superadmin 이 없는 세션 id 를 주면, 입력 검증이 막습니다](#login_sessions-even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist) | 거부 |

**LoginSessionAdapter.admin_unblock_user**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 차단 해제에서 superadmin 이 사용자 이름을 주면, 성공이 오고 그 이름의 차단 기록이 사라집니다](#login_sessions-the-superadmin-unblocks-a-user) | 성공 |
| [superadmin 이 어떤 사용자도 아닌 이름을 주면, 존재를 확인하지 않고 성공이 옵니다](#login_sessions-unblocking-a-username-nobody-holds-still-succeeds) | 성공 |
| [권한 받은 사용자가 차단을 해제하려 하면, 전역 역할 문이 막습니다](#login_sessions-a-user-who-is-not-the-superadmin-may-not-unblock-a-user) | 거부 |

**LoginSessionAdapter.my_revoke**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 와 UPDATE 를 받은 사용자가 자기 세션을 회수하면, 성공이 오고 그 세션은 더 조회되지 않으며 사용자가 회수했다는 이력이 생깁니다](#login_sessions-a-user-granted-update-on-themselves-revokes-their-own-login-session) | 성공 |
| [역할 없이 회수하려 하면, 소유자 조회 단계가 막습니다](#login_sessions-a-user-granted-nothing-may-not-revoke-their-own-login-session) | 거부 |
| [자기 스코프에서만 READ 와 UPDATE 를 받은 사용자가 다른 사용자의 세션을 주면, 그 소유자에 대한 조회 단계가 막습니다](#login_sessions-a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session) | 거부 |
| [READ 만 받고 회수하려 하면, 엔티티 권한 문이 막습니다](#login_sessions-a-user-granted-only-read-may-not-revoke-their-own-login-session) | 거부 |

**UserAdapter.admin_create_keypair**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아니어도 대상 사용자 스코프에서 UPDATE 를 받은 사용자가 정책을 주고 키를 생성하면, 기본 아닌 새 키와 secret 이 응답으로 옵니다](#managing_keypairs-a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy) | 성공 |
| [권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막습니다](#managing_keypairs-a-key-may-not-be-made-under-a-policy-that-does-not-exist) | 거부 |
| [역할 없이 키를 생성하려 하면, 엔티티 권한 문이 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-make-a-key-for-another) | 거부 |

**UserAdapter.admin_delete_keypair**

| 시나리오 | 판정 |
|---|---|
| [대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 삭제하면, 삭제한 키의 access key 가 응답으로 옵니다](#managing_keypairs-a-granted-user-deleting-another-users-extra-key-gets-its-access-key) | 성공 |
| [역할 없이 삭제하려 하면, 소유자 조회 단계가 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-delete-another-users-key) | 거부 |
| [READ 만 받고 삭제하려 하면, 엔티티 권한 문이 막습니다](#managing_keypairs-a-user-granted-only-read-may-not-delete-another-users-key) | 거부 |
| [권한 받은 사용자가 대상의 기본 키를 삭제하려 하면, 입력 검증이 막습니다](#managing_keypairs-another-users-default-key-may-not-be-deleted) | 거부 |

**UserAdapter.admin_delete_ssh_keypair**

| 시나리오 | 판정 |
|---|---|
| [대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 삭제하면, access key 가 오고 공개키가 비워집니다](#managing_keypairs-a-granted-user-clearing-another-users-ssh-key-empties-the-public-key) | 성공 |
| [역할 없이 삭제하려 하면, 소유자 조회 단계가 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-clear-another-users-ssh-key) | 거부 |
| [READ 만 받고 삭제하려 하면, 엔티티 권한 문이 막습니다](#managing_keypairs-a-user-granted-only-read-may-not-clear-another-users-ssh-key) | 거부 |

**UserAdapter.admin_get_keypair**

| 시나리오 | 판정 |
|---|---|
| [대상 스코프에서 READ 를 받은 사용자가 읽으면, 그 키 노드 전체가 응답으로 옵니다](#managing_keypairs-a-granted-user-reads-another-users-key-by-access-key) | 성공 |
| [역할 없이 읽으려 하면, 소유자 조회 단계가 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-read-another-users-key) | 거부 |

**UserAdapter.admin_get_ssh_keypair**

| 시나리오 | 판정 |
|---|---|
| [대상 스코프에서 READ 를 받은 사용자가 읽으면, access key 와 공개키만 오고 개인키는 오지 않습니다](#managing_keypairs-a-granted-user-reads-another-users-ssh-public-key-only) | 성공 |
| [역할 없이 읽으려 하면, 소유자 조회 단계가 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-read-another-users-ssh-public-key) | 거부 |

**UserAdapter.admin_register_ssh_keypair**

| 시나리오 | 판정 |
|---|---|
| [대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 공개키와 개인키를 주면, 형식 검사 없이 덮어쓰고 access key 가 응답으로 옵니다](#managing_keypairs-a-granted-user-registering-another-users-ssh-key-gets-the-access-key) | 성공 |
| [역할 없이 등록하려 하면, 소유자 조회 단계가 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-register-another-users-ssh-key) | 거부 |
| [READ 만 받고 등록하려 하면, 엔티티 권한 문이 막습니다](#managing_keypairs-a-user-granted-only-read-may-not-register-another-users-ssh-key) | 거부 |

**UserAdapter.admin_update_keypair**

| 시나리오 | 판정 |
|---|---|
| [대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 요청 한도만 주면, 나머지는 그대로이고 한도만 변경된 키 노드가 응답으로 옵니다](#managing_keypairs-a-granted-user-changing-another-users-rate-limit-changes-only-that) | 성공 |
| [역할 없이 변경하려 하면, 소유자 조회 단계가 막습니다](#managing_keypairs-a-user-granted-nothing-may-not-change-another-users-key) | 거부 |
| [READ 만 받고 변경하려 하면, 엔티티 권한 문이 막습니다](#managing_keypairs-a-user-granted-only-read-may-not-change-another-users-key) | 거부 |
| [권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막습니다](#managing_keypairs-another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist) | 거부 |

**UserAdapter.bulk_purge_users**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 있는 사용자와 없는 id 를 함께 주면, 하나는 영구 삭제되고 없는 id 는 실패로 담깁니다](#retiring-a-bulk-purge-records-a-missing-id-as-a-failure) | 성공 |
| [전역 역할이 문인 일괄 영구 삭제에서 superadmin 이 사용자 둘을 주면, 두 id 와 개수 둘이 응답으로 옵니다](#retiring-the-superadmin-bulk-purge-answers-the-purged-ids-and-count) | 성공 |
| [도메인 스코프에서 HARD_DELETE 를 받은 사용자라도 일괄 영구 삭제를 하려 하면, 전역 역할 문이 막습니다](#retiring-a-user-who-is-not-the-superadmin-may-not-purge-in-bulk) | 거부 |

**UserAdapter.issue_my_keypair**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자 스코프에서 UPDATE 를 받은 사용자가 발급하면, 기본 키의 관리자 표시, 정책, 요청 한도를 따르고 기본 표시는 없는 키와 secret 이 응답으로 옵니다](#own_keypairs-a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key) | 성공 |
| [권한 받은 사용자가 키를 발급하고 그 키로 기본 키를 옮긴 다음 원래 기본 키를 회수하면, 세 호출이 차례로 통과하고 발급한 키 하나만 남습니다](#own_keypairs-an-issued-key-made-default-lets-the-original-default-key-be-revoked) | 성공 |
| [역할을 받지 않은 사용자가 자기 키를 발급하려 하면, 본인이어도 엔티티 권한 문이 막습니다](#own_keypairs-a-user-granted-nothing-may-not-issue-their-own-key) | 거부 |

**UserAdapter.purge_user_by_id**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 HARD_DELETE 를 받은 사용자가 삭제되지 않은 사용자를 영구 삭제해도, 성공이 오고 그 사용자를 더 찾을 수 없습니다](#retiring-a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions) | 성공 |
| [역할 없이 영구 삭제하려 하면, 엔티티 권한 문이 막습니다](#retiring-a-user-granted-nothing-may-not-purge-another-user) | 거부 |
| [권한 받은 사용자가 넘겨받을 관리자로 없는 id 를 주면, 입력 검증이 막습니다](#retiring-purging-a-user-to-an-admin-who-does-not-exist-is-refused) | 거부 |

**UserAdapter.restore_user_by_id**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 SOFT_DELETE 를 받은 사용자가 삭제 상태 사용자를 복원하면, 성공이 오고 상태가 활성으로 변경됩니다](#retiring-a-user-granted-soft-delete-restores-a-deleted-user-to-active) | 성공 |
| [역할 없이 복원하려 하면, 엔티티 권한 문이 막습니다](#retiring-a-user-granted-nothing-may-not-restore-another-user) | 거부 |
| [권한 받은 사용자가 삭제되지 않은 비활성 사용자를 복원하려 하면, 삭제 상태가 아니라 거부됩니다](#retiring-restoring-a-user-who-was-not-deleted-is-refused) | 거부 |

**UserAdapter.revoke_my_keypair**

| 시나리오 | 판정 |
|---|---|
| [권한 받은 사용자가 자기의 기본 아닌 키를 회수하면, 성공이 오고 자기 키 검색에서 그 키가 빠집니다](#own_keypairs-a-user-granted-read-and-update-revokes-a-non-default-key) | 성공 |
| [역할을 받지 않은 사용자가 회수하려 하면, 소유자 조회 단계가 없는 키와 같은 예외로 막습니다](#own_keypairs-a-user-granted-nothing-may-not-revoke-their-own-key) | 거부 |
| [자기 스코프에서 READ 만 받은 사용자가 회수하려 하면, 소유자 조회는 지나고 엔티티 권한 문이 막습니다](#own_keypairs-a-user-granted-only-read-may-not-revoke-their-own-key) | 거부 |
| [권한 받은 사용자가 어떤 키도 아닌 값을 주면, 소유자 조회 단계가 권한 없음과 같은 예외로 막습니다](#own_keypairs-an-access-key-nobody-holds-may-not-be-revoked) | 거부 |
| [권한 받은 사용자가 자기 기본 키를 회수하려 하면, 입력 검증이 막습니다](#own_keypairs-the-default-key-may-not-be-revoked) | 거부 |

**UserAdapter.switch_default_access_key**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 UPDATE 를 받은 사용자가 기본 아닌 활성 키로 기본 키를 옮기면, 성공이 오고 사용자 노드의 기본 키가 그 키가 됩니다](#own_keypairs-a-user-granted-read-and-update-moves-their-default-key) | 성공 |
| [역할 없이 기본 키를 옮기려 하면, 엔티티 권한 문이 막습니다](#own_keypairs-a-user-granted-nothing-may-not-move-their-default-key) | 거부 |
| [권한 받은 사용자가 다른 사용자의 키를 주면, 입력 검증이 막습니다](#own_keypairs-someone-elses-key-may-not-become-the-default-key) | 거부 |

**UserAdapter.update_my_keypair**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 READ 와 UPDATE 를 받은 사용자가 기본 아닌 키를 비활성으로 변경하면, 활성만 변경된 키 노드가 응답으로 옵니다](#own_keypairs-a-user-granted-read-and-update-turns-off-a-non-default-key) | 성공 |
| [역할 없이 키를 비활성으로 변경하려 하면, 소유자 조회 단계가 막습니다](#own_keypairs-a-user-granted-nothing-may-not-turn-off-their-own-key) | 거부 |
| [READ 만 받고 키를 비활성으로 변경하려 하면, 엔티티 권한 문이 막습니다](#own_keypairs-a-user-granted-only-read-may-not-turn-off-their-own-key) | 거부 |
| [권한 받은 사용자가 자기 기본 키를 비활성으로 변경하려 하면, 입력 검증이 막습니다](#own_keypairs-the-default-key-may-not-be-turned-off) | 거부 |

**UserAdapter.update_user**

| 시나리오 | 판정 |
|---|---|
| [대상 사용자 스코프에서 UPDATE 를 받은 사용자가 허용 IP 만 담은 수정을 보내면, 성공 표시가 오고 그 사용자의 허용 IP 가 변경됩니다](#editing-a-user-granted-update-changes-the-allowed-client-ip) | 성공 |
| [역할 없이 허용 IP 수정을 보내면, 엔티티 권한 문이 막습니다](#editing-a-user-granted-nothing-may-not-change-the-allowed-client-ip) | 거부 |

**UserConfigAdapter.create_auto_generated_file**

| 시나리오 | 판정 |
|---|---|
| [자기 자신에게 UPDATE 를 받은 사용자가 설정 파일을 만들면, 빈 응답이 옵니다](#config_files-a-user-granted-update-on-themselves-writes-their-own-config-file) | 성공 |
| [UPDATE 를 받은 사용자가 관리자가 쓰는 자리에 설정 파일을 만들려 하면, 입력 검증이 거부합니다](#config_files-a-config-file-in-a-place-the-manager-keeps-is-refused) | 거부 |
| [권한을 받지 않은 사용자가 자기 설정 파일을 만들려 하면, 권한 부족으로 거부됩니다](#config_files-a-user-granted-nothing-may-not-write-a-config-file) | 거부 |

### LoginHistoryAdapter.admin_search

<a id="login_history-the-superadmin-searches-every-users-login-history"></a>

#### [the-superadmin-searches-every-users-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

전역 역할이 문인 이력 검색에서 superadmin 이 조회하면, 사용자와 무관하게 미리 저장한 이력이 생성 시각 내림차순으로 옵니다

Given

- 도메인 하나와 superadmin, 성공 기록을 하나씩 가진 사용자 둘
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 성공한 로그인 이력 하나를 갖습니다
  - 일반 사용자 user-2: 성공한 로그인 이력 하나를 갖습니다

When

- LoginHistoryAdapter.admin_search: user-3이 로그인 이력 전체를 조회합니다

Then

- 미리 저장한 기록이 모두 순서대로 옵니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 미리 저장한 기록와 같다
  - items[0].user_id: 기록 소유자와 같다
  - items[0].domain_name = 'home-1'
  - items[0].result = 'success'
  - items[0].fail_reason = None
  - items[0].client_ip = None
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 미리 저장한 기록와 같다
  - items[1].user_id: 기록 소유자와 같다
  - items[1].domain_name = 'home-1'
  - items[1].result = 'success'
  - items[1].fail_reason = None
  - items[1].client_ip = None
  - items[1].created_at: 이 실행이 쓴 시각

<a id="login_history-a-user-who-is-not-the-superadmin-may-not-search-every-login-history"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

권한 받은 사용자가 이력 전체 검색을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나, 호출자는 도메인 스코프에서 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.admin_search: user-1이 로그인 이력 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### LoginHistoryAdapter.batch_load_by_ids

<a id="login_history-a-user-granted-read-on-themselves-loads-their-own-history-by-id"></a>

#### [a-user-granted-read-on-themselves-loads-their-own-history-by-id](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

자기 스코프에서 READ 를 받은 사용자가 자기 이력과 없는 id 를 한 번에 읽으면, 자기 이력 전체와 빈 값이 차례로 옵니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 성공한 로그인 이력 하나를 갖습니다
  - 일반 사용자 user-2: 성공한 로그인 이력 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.batch_load_by_ids: user-1이 자기 이력과 없는 id 를 일괄 읽습니다

Then

- 읽은 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 저장한 기록와 같다
  - [0].user_id: 기록 소유자와 같다
  - [0].domain_name = 'home-1'
  - [0].result = 'success'
  - [0].fail_reason = None
  - [0].client_ip = None
  - [0].created_at: 이 실행이 쓴 시각
  - [1] = None

<a id="login_history-a-user-granted-nothing-gets-a-rejection-for-their-own-history"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-their-own-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

권한을 받지 않은 사용자가 자기 이력과 없는 id 를 한 번에 읽으면, 그 이력 항목은 권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다

Given

- 도메인 하나와 사용자 둘, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 성공한 로그인 이력 하나를 갖습니다
  - 일반 사용자 user-2: 성공한 로그인 이력 하나를 갖습니다

When

- LoginHistoryAdapter.batch_load_by_ids: user-1이 자기 이력과 없는 id 를 일괄 읽습니다

Then

- 읽을 수 없는 이력은 권한 부족으로 거부되고, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - 거부: NotEnoughPermission
  - [1] = None

### LoginHistoryAdapter.my_search

<a id="login_history-a-user-granted-read-on-themselves-searches-only-their-own-login-history"></a>

#### [a-user-granted-read-on-themselves-searches-only-their-own-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

자기 스코프에서 READ 를 받은 사용자가 조회하면, 다른 사용자의 이력은 빠집니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 성공한 로그인 이력 하나를 갖습니다
  - 일반 사용자 user-2: 성공한 로그인 이력 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.my_search: user-1이 자기 로그인 이력을 조회합니다

Then

- 자기 기록 하나만 옵니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 기록와 같다
  - items[0].user_id: 기록 소유자와 같다
  - items[0].domain_name = 'home-1'
  - items[0].result = 'success'
  - items[0].fail_reason = None
  - items[0].client_ip = None
  - items[0].created_at: 이 실행이 쓴 시각

<a id="login_history-a-user-granted-nothing-may-not-search-their-own-login-history"></a>

#### [a-user-granted-nothing-may-not-search-their-own-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

역할 없이 자기 이력을 조회하려 하면, 본인이어도 스코프 권한 문이 막습니다

Given

- 도메인 하나와 사용자 둘, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 성공한 로그인 이력 하나를 갖습니다

When

- LoginHistoryAdapter.my_search: user-1이 자기 로그인 이력을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### LoginSessionAdapter.admin_search

<a id="login_sessions-the-superadmin-searches-every-users-login-sessions"></a>

#### [the-superadmin-searches-every-users-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

전역 역할이 문인 세션 검색에서 superadmin 이 페이지 인자 없이 조회하면, 사용자와 무관하게 미리 저장한 세션이 생성 시각 내림차순으로 옵니다

Given

- 도메인 하나와 superadmin, 세션을 하나씩 가진 사용자 둘
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_search: user-3이 세션 전체를 조회합니다

Then

- 미리 저장한 세션이 모두 순서대로 옵니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 미리 저장한 세션와 같다
  - items[0].user_id: 세션 소유자와 같다
  - items[0].access_key: 세션을 연 키와 같다
  - items[0].status = 'active'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None
  - items[1].id: 미리 저장한 세션와 같다
  - items[1].user_id: 세션 소유자와 같다
  - items[1].access_key: 세션을 연 키와 같다
  - items[1].status = 'active'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].last_accessed_at = None
  - items[1].invalidated_at = None

<a id="login_sessions-a-user-who-is-not-the-superadmin-may-not-search-every-login-session"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

권한 받은 사용자가 세션 전체 검색을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 세션을 가진 사용자 하나, 호출자는 도메인 스코프에서 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginSessionAdapter.admin_search: user-2이 세션 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### LoginSessionAdapter.batch_load_by_ids

<a id="login_sessions-a-user-granted-read-on-themselves-loads-their-own-session-by-id"></a>

#### [a-user-granted-read-on-themselves-loads-their-own-session-by-id](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

자기 스코프에서 READ 를 받은 사용자가 자기 세션과 없는 id 를 한 번에 읽으면, 자기 세션 전체와 빈 값이 차례로 옵니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.batch_load_by_ids: user-1이 자기 세션과 없는 id 를 일괄 읽습니다

Then

- 읽은 세션은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 저장한 세션와 같다
  - [0].user_id: 세션 소유자와 같다
  - [0].access_key: 세션을 연 키와 같다
  - [0].status = 'active'
  - [0].created_at: 이 실행이 쓴 시각
  - [0].last_accessed_at = None
  - [0].invalidated_at = None
  - [1] = None

<a id="login_sessions-a-user-granted-nothing-gets-a-rejection-for-their-own-session"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-their-own-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

권한을 받지 않은 사용자가 자기 세션과 없는 id 를 한 번에 읽으면, 그 세션 항목은 권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다

Given

- 도메인 하나와 사용자 둘, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.batch_load_by_ids: user-1이 자기 세션과 없는 id 를 일괄 읽습니다

Then

- 읽을 수 없는 세션은 권한 부족으로 거부되고, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - 거부: NotEnoughPermission
  - [1] = None

### LoginSessionAdapter.my_search

<a id="login_sessions-a-user-granted-read-on-themselves-searches-only-their-own-login-sessions"></a>

#### [a-user-granted-read-on-themselves-searches-only-their-own-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

자기 스코프에서 READ 를 받은 사용자가 조회하면, 다른 사용자의 세션은 빠집니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_search: user-1이 자기 세션을 조회합니다

Then

- 자기 세션 하나만 옵니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 세션와 같다
  - items[0].user_id: 세션 소유자와 같다
  - items[0].access_key: 세션을 연 키와 같다
  - items[0].status = 'active'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

<a id="login_sessions-a-user-granted-nothing-may-not-search-their-own-login-sessions"></a>

#### [a-user-granted-nothing-may-not-search-their-own-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

역할 없이 자기 세션을 조회하려 하면, 본인이어도 스코프 권한 문이 막습니다

Given

- 도메인 하나와 사용자 둘, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.my_search: user-1이 자기 세션을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.admin_search

<a id="searching-the-superadmin-searching-every-user-counts-deleted-ones-too"></a>

#### [the-superadmin-searching-every-user-counts-deleted-ones-too](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

전역 역할이 문인 검색에서 superadmin 이 필터 없이 조회하면, 삭제 상태 사용자를 포함해 미리 저장한 사용자가 모두 옵니다

Given

- 도메인 하나와 활성 사용자 하나, 삭제 상태 사용자 하나, 그리고 superadmin
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 삭제 상태 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.admin_search: user-3이 필터 없이 전체를 조회합니다

Then

- 삭제 상태를 포함해 미리 저장한 사용자가 모두 옵니다
  - items(by name, name and state) = [('user-1', 'active'), ('user-2', 'deleted'), ('user-3', 'active')]
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-user"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-user](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

도메인 스코프 권한을 받은 사용자라도 전체 검색을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.admin_search: user-1이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.admin_search_keypairs

<a id="managing_keypairs-the-superadmin-searching-every-key-gets-every-users-key"></a>

#### [the-superadmin-searching-every-key-gets-every-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

전역 역할이 문인 키 검색에서 superadmin 이 페이지 인자 없이 조회하면, 모든 사용자의 키가 오고 limit 자리는 비어서 옵니다

Given

- 도메인 하나와 사용자 둘, superadmin 한 명, 저마다 다른 키페어 정책
  - 도메인 home-1
  - 자기 키페어 정책을 가진 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.admin_search_keypairs: user-3이 페이지 인자 없이 모든 키를 조회합니다

Then

- 모든 사용자의 키가 소유자 순으로 옵니다
  - items.length = 3
  - items[0].id: 건너뜀: 시드가 만든 난수 키입니다
  - items[0].access_key: 건너뜀: 시드가 만든 난수 키입니다
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = ''
  - items[0].num_queries = 0
  - items[0].last_used = None
  - items[0].user_id: 키 소유자와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].modified_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 시드가 만든 난수 키입니다
  - items[1].access_key: 건너뜀: 시드가 만든 난수 키입니다
  - items[1].is_active = True
  - items[1].is_admin = False
  - items[1].is_default = True
  - items[1].rate_limit = 10000
  - items[1].resource_policy = 'keypair-policy-2'
  - items[1].ssh_public_key = ''
  - items[1].num_queries = 0
  - items[1].last_used = None
  - items[1].user_id: 키 소유자와 같다
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].modified_at: 이 실행이 쓴 시각
  - items[2].id: 건너뜀: 시드가 만든 난수 키입니다
  - items[2].access_key: 건너뜀: 시드가 만든 난수 키입니다
  - items[2].is_active = True
  - items[2].is_admin = True
  - items[2].is_default = True
  - items[2].rate_limit = 10000
  - items[2].resource_policy = 'keypair-policy-3'
  - items[2].ssh_public_key = ''
  - items[2].num_queries = 0
  - items[2].last_used = None
  - items[2].user_id: 키 소유자와 같다
  - items[2].created_at: 이 실행이 쓴 시각
  - items[2].modified_at: 이 실행이 쓴 시각
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = None

<a id="managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

권한 받은 사용자가 키 전체 검색을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.admin_search_keypairs: user-1이 페이지 인자 없이 모든 키를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.batch_load_by_ids

<a id="reading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

권한 없는 사용자가 빈 id 목록을 주면, 어떤 액션도 호출하지 않고 빈 목록이 응답으로 옵니다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.batch_load_by_ids: user-2이 빈 목록으로 일괄 읽습니다

Then

- 빈 목록이 응답으로 옵니다
  - loaded = []

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

superadmin 이 있는 id 와 없는 id 를 함께 요청하면, 권한 문을 지나 없는 원소 자리에 빈 값이 옵니다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.batch_load_by_ids: user-2이 user-1과 없는 id 를 일괄 읽습니다

Then

- 있는 사람은 노드, 없는 id 자리는 비어서 옵니다
  - length = 2
  - [0].id: 미리 저장한 사용자와 같다
  - [0].basic_info.username = 'user-1'
  - [0].basic_info.email = 'user-1@scenario.local'
  - [0].basic_info.full_name = None
  - [0].basic_info.description = None
  - [0].basic_info.integration_name = None
  - [0].status.status = 'active'
  - [0].status.status_info = None
  - [0].status.need_password_change = False
  - [0].organization.domain_name = 'home-1'
  - [0].organization.role = 'user'
  - [0].organization.resource_policy = 'user-policy-1'
  - [0].organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - [0].security.allowed_client_ip = None
  - [0].security.totp_activated = False
  - [0].security.totp_activated_at = None
  - [0].security.sudo_session_enabled = False
  - [0].container.container_uid = None
  - [0].container.container_main_gid = None
  - [0].container.container_gids = None
  - [0].timestamps.created_at: 이 실행이 쓴 시각
  - [0].timestamps.modified_at: 이 실행이 쓴 시각
  - [1] = None

<a id="reading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order"></a>

#### [a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

한 사용자에게만 읽기 권한을 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, 없는 id 를 한 번에 요청하면, 입력 순서대로 원소별 결과가 옵니다

Given

- 도메인 하나와 사용자 셋, 호출자는 한 사람에 대한 사용자 읽기 권한만 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.batch_load_by_ids: user-3이 user-1, user-2, 없는 id 순으로 일괄 읽습니다

Then

- 원소마다 결과가 입력 순서대로 옵니다
  - length = 3
  - [0].id: 미리 저장한 사용자와 같다
  - [0].basic_info.username = 'user-1'
  - [0].basic_info.email = 'user-1@scenario.local'
  - [0].basic_info.full_name = None
  - [0].basic_info.description = None
  - [0].basic_info.integration_name = None
  - [0].status.status = 'active'
  - [0].status.status_info = None
  - [0].status.need_password_change = False
  - [0].organization.domain_name = 'home-1'
  - [0].organization.role = 'user'
  - [0].organization.resource_policy = 'user-policy-1'
  - [0].organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - [0].security.allowed_client_ip = None
  - [0].security.totp_activated = False
  - [0].security.totp_activated_at = None
  - [0].security.sudo_session_enabled = False
  - [0].container.container_uid = None
  - [0].container.container_main_gid = None
  - [0].container.container_gids = None
  - [0].timestamps.created_at: 이 실행이 쓴 시각
  - [0].timestamps.modified_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### UserAdapter.batch_lookup_by_emails

<a id="reading-a-user-granted-read-on-another-user-looks-up-their-id-by-email"></a>

#### [a-user-granted-read-on-another-user-looks-up-their-id-by-email](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 그 사용자의 email 을 찾으면, 그 사용자의 id 가 응답으로 옵니다

Given

- 도메인 하나와 사용자 둘, 한 사람은 다른 사람에 대한 사용자 읽기 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.batch_lookup_by_emails: user-2이 user-1의 email 로 찾습니다

Then

- 찾은 사용자의 id 가 응답으로 옵니다
  - length = 1
  - [0]: 대상 사용자의 id 와 같다

<a id="reading-an-email-lookup-of-no-emails-answers-an-empty-list"></a>

#### [an-email-lookup-of-no-emails-answers-an-empty-list](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

권한 없는 사용자가 빈 email 목록을 주면, 어떤 액션도 호출하지 않고 빈 목록이 응답으로 옵니다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.batch_lookup_by_emails: user-2이 빈 목록으로 email 을 찾습니다

Then

- 빈 목록이 응답으로 옵니다
  - loaded = []

<a id="reading-an-unreadable-user-and-a-missing-email-are-refused-alike"></a>

#### [an-unreadable-user-and-a-missing-email-are-refused-alike](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

한 사용자에게만 읽기 권한을 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, 없는 email 을 한 번에 찾으면, 첫째는 id, 나머지 둘은 같은 거부가 입력 순서대로 옵니다

Given

- 도메인 하나와 사용자 셋, 호출자는 한 사람에 대한 사용자 읽기 권한만 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.batch_lookup_by_emails: user-3이 user-1, user-2, 없는 email 순으로 email 을 찾습니다

Then

- 읽을 수 있는 사람은 id, 나머지 둘은 같은 거부가 입력 순서대로 옵니다
  - length = 3
  - [0]: 읽을 수 있는 사용자의 id 와 같다
  - 거부: GenericBadRequest
  - 거부: GenericBadRequest

### UserAdapter.bulk_get_keypair_ids

<a id="loading_keypairs-a-user-granted-read-on-another-loads-their-key-by-id"></a>

#### [a-user-granted-read-on-another-loads-their-key-by-id](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 그 사용자의 키와 없는 id 를 한 번에 읽으면, 키 전체와 빈 값이 차례로 옵니다

Given

- 도메인 하나와 사용자 둘, 대상은 기본이 아닌 키를 하나 더 갖고, 호출자는 대상에 대한 사용자 읽기 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.bulk_get_keypair_ids: user-2이 user-1의 키와 없는 id 를 일괄 읽습니다

Then

- 읽은 키는 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - id: 미리 저장한 키페어와 같다
  - access_key: 미리 저장한 키페어와 같다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-2'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키페어 소유자와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - field_id: 미리 저장한 키페어와 같다
  - [1] = None

<a id="loading_keypairs-a-user-granted-nothing-gets-a-rejection-for-anothers-key"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-anothers-key](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

권한을 받지 않은 사용자가 다른 사용자의 키와 없는 id 를 한 번에 읽으면, 그 키 항목은 권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다

Given

- 도메인 하나와 사용자 둘, 대상은 기본이 아닌 키를 하나 더 갖고, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.bulk_get_keypair_ids: user-2이 user-1의 키와 없는 id 를 일괄 읽습니다

Then

- 읽을 수 없는 키는 권한 부족으로 거부되고, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - 거부: NotEnoughPermission
  - [1] = None

### UserAdapter.bulk_lookup_keypair_access_keys

<a id="loading_keypairs-a-user-looks-up-the-keypair-an-access-key-names"></a>

#### [a-user-looks-up-the-keypair-an-access-key-names](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

사용자가 access key 와 어떤 키도 아닌 access key 를 한 번에 찾으면, 첫째는 그 키의 id 로, 둘째는 빈 값으로 옵니다

Given

- 도메인 하나와 사용자 둘, 대상은 기본이 아닌 키를 하나 더 갖고, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.bulk_lookup_keypair_access_keys: user-2이 user-1의 access key 와 없는 access key 로 키를 찾습니다

Then

- 찾은 키의 id 는 그 키의 것이고, 없는 access key 자리는 비어 있습니다
  - length = 2
  - [0]: 미리 저장한 키페어와 같다
  - [1] = None

<a id="loading_keypairs-looking-up-an-access-key-without-login-is-refused"></a>

#### [looking-up-an-access-key-without-login-is-refused](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

로그인 문맥 없이 access key 로 키를 찾으면, 사용자를 찾을 수 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 둘, 대상은 기본이 아닌 키를 하나 더 갖고, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.bulk_lookup_keypair_access_keys: 로그인 문맥 없이 access key 로 키를 찾습니다

Then

- 거부됩니다
  - 거부: UserNotFound

### UserAdapter.domain_search

<a id="searching-a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users"></a>

#### [a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

도메인 스코프에서 사용자 READ 를 받은 사용자가 도메인 이름으로 조회하면, 다른 도메인 사용자는 빠집니다

Given

- 도메인 하나, 같은 도메인 사용자 하나와 다른 도메인 사용자 하나, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 other-1
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.domain_search: user-3이 home-1으로 조회합니다

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실립니다
  - items(by name) = ['user-1', 'user-3']
  - pagination.total = 2
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-granted-nothing-may-not-search-a-domain-by-name"></a>

#### [a-user-granted-nothing-may-not-search-a-domain-by-name](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

역할을 받지 않은 사용자가 도메인 이름으로 조회하려 하면, 스코프 권한 문이 막습니다

Given

- 도메인 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.domain_search: user-1이 home-1으로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="searching-searching-a-domain-name-nothing-answers-to-is-not-found"></a>

#### [searching-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

권한 받은 사용자가 어떤 도메인도 아닌 이름으로 조회하려 하면, 스코프 검사 전에 이름 조회 단계가 대상 없음으로 막습니다

Given

- 도메인 하나, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.domain_search: user-1이 no-such-domain 으로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### UserAdapter.gql_admin_search

<a id="searching-a-gql-search-without-page-arguments-answers-the-newest-ten"></a>

#### [a-gql-search-without-page-arguments-answers-the-newest-ten](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

superadmin 이 커서와 페이지 인자를 모두 생략하고 조회하면, 생성 시각 내림차순으로 열 명까지 오고 다음 페이지 여부가 함께 옵니다

Given

- 도메인 하나와 사용자 11명, 그리고 superadmin
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 user-4: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-5: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 일반 사용자 user-5: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-6: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-6: 동시 세션 5개까지
    - 일반 사용자 user-6: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-7: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-7: 동시 세션 5개까지
    - 일반 사용자 user-7: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-8: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-8: 동시 세션 5개까지
    - 일반 사용자 user-8: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-9: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-9: 동시 세션 5개까지
    - 일반 사용자 user-9: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-10: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-10: 동시 세션 5개까지
    - 일반 사용자 user-10: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-11: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-11: 동시 세션 5개까지
    - 일반 사용자 user-11: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-12: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-12: 동시 세션 5개까지
    - superadmin user-12: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.gql_admin_search: user-12이 페이지 인자 없이 GQL 로 전체를 조회합니다

Then

- 미리 저장한 사용자 중 열 명이 최근순으로 오고 다음 페이지가 있습니다
  - items.length = 10
  - items(names): 모두 미리 저장한 사용자 중에서 옵니다
  - items(creation time): 생성 시각 내림차순입니다
  - total_count = 12
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-gql-search-every-user"></a>

#### [a-user-who-is-not-the-superadmin-may-not-gql-search-every-user](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

권한 받은 사용자가 GQL 전체 검색을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.gql_admin_search: user-1이 페이지 인자 없이 GQL 로 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.gql_admin_search_keypairs

<a id="managing_keypairs-the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only"></a>

#### [the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

전역 역할이 문인 GQL 키 검색에서 superadmin 이 정책 이름을 주면, 그 정책을 사용하는 키만 옵니다

Given

- 도메인 하나와 사용자 둘, superadmin 한 명, 저마다 다른 키페어 정책
  - 도메인 home-1
  - 자기 키페어 정책을 가진 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.gql_admin_search_keypairs: user-3이 keypair-policy-1으로 필터 기반 GQL 키 검색을 합니다

Then

- 그 정책을 사용하는 키 하나만 옵니다
  - items.length = 1
  - items[0].id: 건너뜀: 시드가 만든 난수 키입니다
  - items[0].access_key: 건너뜀: 시드가 만든 난수 키입니다
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = ''
  - items[0].num_queries = 0
  - items[0].last_used = None
  - items[0].user_id: 키 소유자와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].modified_at: 이 실행이 쓴 시각
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

권한 받은 사용자가 GQL 키 검색을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.gql_admin_search_keypairs: user-1이 GQL 로 모든 키를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.gql_scoped_search

<a id="searching-a-gql-scoped-search-over-two-granted-scopes-joins-their-users"></a>

#### [a-gql-scoped-search-over-two-granted-scopes-joins-their-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

같은 권한으로 GQL 스코프 검색을 하면, 두 스코프 사용자가 커서 응답으로 옵니다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 멤버 목록 사용자 하나, 호출자는 첫 도메인 스코프와 그 프로젝트 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 프로젝트 research-1 멤버 목록에 추가됨
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
    - 역할 user-role-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-2: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-2 보유

When

- UserAdapter.gql_scoped_search: user-2이 home-1과 research-1 두 스코프로 GQL 조회합니다

Then

- 닿는 사용자가 모두 한 페이지로 옵니다
  - items(by name) = ['user-1', 'user-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-one-scope-without-a-grant-refuses-the-whole-gql-scoped-search"></a>

#### [one-scope-without-a-grant-refuses-the-whole-gql-scoped-search](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

한 스코프에만 READ 를 받고 GQL 스코프 검색에 둘을 주면, 스코프 권한 문이 전체를 막습니다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 멤버 목록 사용자 하나, 호출자는 첫 도메인 스코프의 사용자 READ 만 받았습니다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 프로젝트 research-1 멤버 목록에 추가됨
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.gql_scoped_search: user-2이 home-1과 research-1 두 스코프로 GQL 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.gql_search_by_domain

<a id="searching-a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users"></a>

#### [a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

같은 권한으로 GQL 도메인 검색을 하면, 그 도메인 사용자만 커서 응답으로 옵니다

Given

- 도메인 하나, 같은 도메인 사용자 하나와 다른 도메인 사용자 하나, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 other-1
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.gql_search_by_domain: user-3이 home-1으로 GQL 조회합니다

Then

- 닿는 사용자가 모두 한 페이지로 옵니다
  - items(by name) = ['user-1', 'user-3']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-gql-search-a-domain"></a>

#### [a-user-granted-nothing-may-not-gql-search-a-domain](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

역할 없이 GQL 도메인 검색을 하면, 스코프 권한 문이 막습니다

Given

- 도메인 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.gql_search_by_domain: user-1이 home-1으로 GQL 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.gql_search_by_project

<a id="searching-a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster"></a>

#### [a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

같은 권한으로 GQL 프로젝트 검색을 하면, 멤버 목록의 사용자만 커서 응답으로 옵니다

Given

- 도메인 하나와 프로젝트 하나, 멤버 목록에 오른 사용자 하나와 오르지 않은 사용자 하나, 호출자는 그 프로젝트 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 프로젝트 research-1 멤버 목록에 추가됨
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.gql_search_by_project: user-3이 research-1으로 GQL 조회합니다

Then

- 닿는 사용자가 모두 한 페이지로 옵니다
  - items(by name) = ['user-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-gql-search-a-project"></a>

#### [a-user-granted-nothing-may-not-gql-search-a-project](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

역할 없이 GQL 프로젝트 검색을 하면, 스코프 권한 문이 막습니다

Given

- 도메인 하나와 프로젝트 하나, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.gql_search_by_project: user-1이 research-1으로 GQL 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.project_search

<a id="searching-a-user-granted-on-a-project-searching-it-finds-only-its-roster"></a>

#### [a-user-granted-on-a-project-searching-it-finds-only-its-roster](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

프로젝트 스코프에서 사용자 READ 를 받은 사용자가 그 프로젝트로 조회하면, 멤버 목록에 오른 사용자만 옵니다

Given

- 도메인 하나와 프로젝트 하나, 멤버 목록에 오른 사용자 하나와 오르지 않은 사용자 하나, 호출자는 그 프로젝트 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 프로젝트 research-1 멤버 목록에 추가됨
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.project_search: user-3이 research-1으로 조회합니다

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실립니다
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-granted-nothing-may-not-search-a-project"></a>

#### [a-user-granted-nothing-may-not-search-a-project](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

역할 없이 프로젝트 검색을 하면, 스코프 권한 문이 막습니다

Given

- 도메인 하나와 프로젝트 하나, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.project_search: user-1이 research-1으로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.resolve_domain_id

<a id="resolving_domain-a-user-resolves-the-id-of-a-domain-by-its-name"></a>

#### [a-user-resolves-the-id-of-a-domain-by-its-name](/tests/scenario/bai_scenario/manager/user/test_resolving_domain.py): pass

도메인에 속한 사용자가 그 도메인의 이름으로 id 를 찾으면, 그 도메인의 id 가 응답으로 옵니다

Given

- 도메인 하나와, 그 도메인에 속한 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.resolve_domain_id: user-1이 home-1의 id 를 찾습니다

Then

- 그 도메인의 id 가 응답으로 옵니다
  - id: 미리 저장한 도메인의 id 와 같다

<a id="resolving_domain-resolving-a-domain-name-nothing-answers-to-is-not-found"></a>

#### [resolving-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/user/test_resolving_domain.py): pass

아무 도메인도 갖지 않은 이름으로 id 를 찾으면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.resolve_domain_id: user-1이 no-such-domain 의 id 를 찾습니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### UserAdapter.role_search

<a id="searching-a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders"></a>

#### [a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

역할이 걸린 스코프의 사용자 READ 를 받은 사용자가 역할 하나를 주면, 그 역할을 배정받은 사용자만 옵니다

Given

- 도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 holder-role-1: 부여된 스코프 안에서만 적용됩니다
  - 일반 사용자 user-1: 역할 holder-role-1 보유
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.role_search: user-3이 역할로 필터 기반 조회합니다

Then

- 역할을 받은 사람만 옵니다
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-the-superadmin-searching-by-role-finds-only-its-holders"></a>

#### [the-superadmin-searching-by-role-finds-only-its-holders](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

전역 역할이 문인 역할 검색에서 superadmin 이 역할 하나를 주면, 그 역할을 배정받은 사용자만 옵니다

Given

- 도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 호출자는 superadmin
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 holder-role-1: 부여된 스코프 안에서만 적용됩니다
  - 일반 사용자 user-1: 역할 holder-role-1 보유

When

- UserAdapter.role_search: user-3이 역할로 필터 기반 조회합니다

Then

- 역할을 받은 사람만 옵니다
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-granted-nothing-may-not-search-by-role"></a>

#### [a-user-granted-nothing-may-not-search-by-role](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

아무 권한도 받지 않은 사용자가 역할로 조회하려 하면, 스코프 권한 문이 막습니다

Given

- 도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 holder-role-1: 부여된 스코프 안에서만 적용됩니다
  - 일반 사용자 user-1: 역할 holder-role-1 보유

When

- UserAdapter.role_search: user-3이 역할로 필터 기반 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.scoped_search

<a id="searching-a-scoped-search-over-two-granted-scopes-joins-their-users"></a>

#### [a-scoped-search-over-two-granted-scopes-joins-their-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

도메인과 프로젝트 스코프 모두에서 READ 를 받은 사용자가 두 스코프를 함께 주면, 두 스코프의 사용자가 중복 없이 합쳐집니다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 멤버 목록 사용자 하나, 호출자는 첫 도메인 스코프와 그 프로젝트 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 프로젝트 research-1 멤버 목록에 추가됨
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
    - 역할 user-role-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-2: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-2 보유

When

- UserAdapter.scoped_search: user-2이 home-1과 research-1 두 스코프로 조회합니다

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실립니다
  - items(by name) = ['user-1', 'user-2']
  - pagination.total = 2
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-scoped-search-without-page-arguments-answers-up-to-fifty"></a>

#### [a-scoped-search-without-page-arguments-answers-up-to-fifty](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

권한 받은 사용자가 페이지 인자 없이 스코프 검색을 하면, limit 50 offset 0이 응답에 실립니다

Given

- 도메인 하나, 호출자는 그 도메인 스코프의 사용자 READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.scoped_search: user-1이 페이지 인자 없이 home-1 스코프로 조회합니다

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실립니다
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-one-scope-without-a-grant-refuses-the-whole-scoped-search"></a>

#### [one-scope-without-a-grant-refuses-the-whole-scoped-search](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

첫 스코프에만 READ 를 받은 사용자가 두 스코프를 함께 주면, 스코프 권한 문이 전체를 막습니다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 멤버 목록 사용자 하나, 호출자는 첫 도메인 스코프의 사용자 READ 만 받았습니다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 프로젝트 research-1 멤버 목록에 추가됨
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.scoped_search: user-2이 home-1과 research-1 두 스코프로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.search_my_keypairs

<a id="own_keypairs-a-user-granted-read-searching-their-keys-sees-only-their-own"></a>

#### [a-user-granted-read-searching-their-keys-sees-only-their-own](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

자기 스코프에서 READ 를 받은 사용자가 자기 키를 조회하면, 다른 사용자의 키는 빠집니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 기본 아닌 키를 가진 다른 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.search_my_keypairs: user-1이 페이지 인자 없이 자기 키를 조회합니다

Then

- 자기 키 둘만 옵니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.is_default(extra key first) = [False, True]
  - items[the extra key].id: 미리 저장한 키페어와 같다
  - items[the extra key].access_key: 미리 저장한 키페어와 같다
  - items[the extra key].is_active = True
  - items[the extra key].is_admin = False
  - items[the extra key].is_default = False
  - items[the extra key].rate_limit = 10000
  - items[the extra key].resource_policy = 'keypair-policy-1'
  - items[the extra key].ssh_public_key = ''
  - items[the extra key].num_queries = 0
  - items[the extra key].last_used = None
  - items[the extra key].user_id: 키페어 소유자와 같다
  - items[the extra key].created_at: 이 실행이 쓴 시각
  - items[the extra key].modified_at: 이 실행이 쓴 시각
  - items[the default key].id: 건너뜀: 시드가 매번 새로 만든 access key 입니다
  - items[the default key].access_key: 건너뜀: 시드가 매번 새로 만든 access key 입니다
  - items[the default key].is_active = True
  - items[the default key].is_admin = False
  - items[the default key].is_default = True
  - items[the default key].rate_limit = 10000
  - items[the default key].resource_policy = 'keypair-policy-1'
  - items[the default key].ssh_public_key = ''
  - items[the default key].num_queries = 0
  - items[the default key].last_used = None
  - items[the default key].user_id: 키 소유자와 같다
  - items[the default key].created_at: 이 실행이 쓴 시각
  - items[the default key].modified_at: 이 실행이 쓴 시각

<a id="own_keypairs-searching-own-keys-without-page-arguments-answers-the-ten-newest"></a>

#### [searching-own-keys-without-page-arguments-answers-the-ten-newest](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 페이지 인자 없이 조회하면, 생성 시각 내림차순 열 개와 다음 페이지 여부가 응답으로 옵니다

Given

- 도메인 하나와 기본 아닌 키 10개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.search_my_keypairs: user-1이 페이지 인자 없이 자기 키를 조회합니다

Then

- 자기 키 열한 개 중 열 개가 최근순으로 오고 다음 페이지가 있습니다
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False
  - items.length = 10
  - items(created_at, field_id): 생성 시각 내림차순, 같은 시각이면 field id 오름차순입니다
  - items.user_id: 모두 부른 사람와 같다
  - items.created_at: 이 실행이 쓴 시각
  - the remaining item fields: 건너뜀: 순서와 개수를 보는 행입니다. 키 노드 전체는 다른 행이 봅니다

<a id="own_keypairs-a-user-granted-nothing-may-not-search-their-own-keys"></a>

#### [a-user-granted-nothing-may-not-search-their-own-keys](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

역할 없이 자기 키를 조회하려 하면, 스코프 권한 문이 막습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.search_my_keypairs: user-1이 페이지 인자 없이 자기 키를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserConfigAdapter.delete_default_auto_generated_file

<a id="config_files-a-user-granted-nothing-may-not-delete-a-config-file"></a>

#### [a-user-granted-nothing-may-not-delete-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 설정 파일을 지우려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserConfigAdapter.delete_default_auto_generated_file: user-1이 자기 설정 파일 하나를 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="config_files-deleting-a-config-file-that-is-not-marked-default-is-not-found"></a>

#### [deleting-a-config-file-that-is-not-marked-default-is-not-found](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

READ 와 UPDATE 를 받은 사용자가 기본으로 표시되지 않은 설정 파일을 지우려 하면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 기본으로 표시되지 않은 설정 파일 하나를 갖고 있습니다, 사용자는 자기 자신에게 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본으로 표시되지 않은 설정 파일 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserConfigAdapter.delete_default_auto_generated_file: user-1이 자기 설정 파일 하나를 지웁니다

Then

- 거부됩니다
  - 거부: DotfileNotFound

### UserConfigAdapter.get_default_auto_generated_file

<a id="config_files-a-config-file-that-is-not-marked-default-is-not-found"></a>

#### [a-config-file-that-is-not-marked-default-is-not-found](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

READ 를 받은 사용자가 기본으로 표시되지 않은 설정 파일을 읽으려 하면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 기본으로 표시되지 않은 설정 파일 하나를 갖고 있습니다, 사용자는 자기 자신에게 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본으로 표시되지 않은 설정 파일 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserConfigAdapter.get_default_auto_generated_file: user-1이 자기 설정 파일 하나를 읽습니다

Then

- 거부됩니다
  - 거부: DotfileNotFound

<a id="config_files-a-user-granted-nothing-may-not-read-a-config-file"></a>

#### [a-user-granted-nothing-may-not-read-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 설정 파일을 읽으려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserConfigAdapter.get_default_auto_generated_file: user-1이 자기 설정 파일 하나를 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserConfigAdapter.get_default_auto_generated_files

<a id="config_files-a-user-granted-read-on-themselves-lists-no-default-config-file"></a>

#### [a-user-granted-read-on-themselves-lists-no-default-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

READ 를 받은 사용자가 자기 설정 파일 중 기본으로 표시된 것을 훑으면, 빈 목록이 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 자기 자신에게 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserConfigAdapter.get_default_auto_generated_files: user-1이 기본으로 표시된 자기 설정 파일을 훑습니다

Then

- 기본으로 표시된 파일이 없어 빈 목록이 옵니다
  - files = []

<a id="config_files-a-user-granted-nothing-may-not-list-their-config-files"></a>

#### [a-user-granted-nothing-may-not-list-their-config-files](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 설정 파일을 훑으려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserConfigAdapter.get_default_auto_generated_files: user-1이 기본으로 표시된 자기 설정 파일을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserConfigAdapter.update_default_auto_generated_file

<a id="config_files-a-user-granted-nothing-may-not-update-a-config-file"></a>

#### [a-user-granted-nothing-may-not-update-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 설정 파일을 고치려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserConfigAdapter.update_default_auto_generated_file: user-1이 자기 설정 파일 하나의 권한과 내용을 바꿉니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="config_files-updating-a-config-file-that-is-not-marked-default-is-not-found"></a>

#### [updating-a-config-file-that-is-not-marked-default-is-not-found](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

READ 와 UPDATE 를 받은 사용자가 기본으로 표시되지 않은 설정 파일을 고치려 하면, 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 기본으로 표시되지 않은 설정 파일 하나를 갖고 있습니다, 사용자는 자기 자신에게 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본으로 표시되지 않은 설정 파일 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserConfigAdapter.update_default_auto_generated_file: user-1이 자기 설정 파일 하나의 권한과 내용을 바꿉니다

Then

- 거부됩니다
  - 거부: DotfileNotFound

### UserAdapter.bulk_create_users

<a id="creating-the-superadmin-bulk-creates-a-user"></a>

#### [the-superadmin-bulk-creates-a-user](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

superadmin 이 사용자 하나를 일괄 생성하면, 만든 사용자 하나가 오고 실패한 것은 없습니다

Given

- 도메인 하나와 superadmin 한 명, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
  - 기본 키페어 정책 default-keypair-policy-1: 키페어가 정책을 대지 않으면 이 정책을 받습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.bulk_create_users: user-1이 home-1에 made 을 일괄 생성합니다

Then

- 만든 사용자 하나가 응답으로 오고, 실패한 것은 없습니다
  - created_users.length = 1
  - failed = []
  - user.id: 건너뜀: 데이터베이스가 생성합니다
  - user.entity_id: 그 사용자의 id 와 같다
  - user.basic_info.username = 'made'
  - user.basic_info.email = 'made@scenario.local'
  - user.basic_info.full_name = None
  - user.basic_info.description = None
  - user.basic_info.integration_name = None
  - user.status.status = 'active'
  - user.status.status_info = None
  - user.status.need_password_change = False
  - user.organization.domain_name = 'home-1'
  - user.organization.domain_id: 미리 저장한 도메인의 id 와 같다
  - user.organization.role = 'user'
  - user.organization.resource_policy = 'user-policy-1'
  - user.organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - user.security.allowed_client_ip = None
  - user.security.totp_activated = False
  - user.security.totp_activated_at = None
  - user.security.sudo_session_enabled = False
  - user.container.container_uid = None
  - user.container.container_main_gid = None
  - user.container.container_gids = None
  - user.timestamps.created_at: 이 실행이 쓴 시각
  - user.timestamps.modified_at: 이 실행이 쓴 시각

<a id="creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users"></a>

#### [a-user-who-is-not-the-superadmin-may-not-bulk-create-users](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

도메인 스코프에서 CREATE 를 받은 사용자라도 일괄 생성하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 CREATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.bulk_create_users: user-1이 home-1에 made 을 일괄 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.bulk_create_users_with_keypair

<a id="creating-the-superadmin-bulk-creates-a-user-and-gets-its-keypair"></a>

#### [the-superadmin-bulk-creates-a-user-and-gets-its-keypair](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

superadmin 이 키를 함께 받는 일괄 생성으로 사용자 하나를 만들면, 만든 사용자와 그 기본 키가 비밀 키와 함께 오고 실패한 것은 없습니다

Given

- 도메인 하나와 superadmin 한 명, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
  - 기본 키페어 정책 default-keypair-policy-1: 키페어가 정책을 대지 않으면 이 정책을 받습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.bulk_create_users_with_keypair: user-1이 home-1에 made 을 일괄 생성합니다

Then

- 만든 사용자와 그 기본 키가 비밀 키와 함께 응답으로 오고, 실패한 것은 없습니다
  - created.length = 1
  - failed = []
  - user.id: 건너뜀: 데이터베이스가 생성합니다
  - user.entity_id: 그 사용자의 id 와 같다
  - user.basic_info.username = 'made'
  - user.basic_info.email = 'made@scenario.local'
  - user.basic_info.full_name = None
  - user.basic_info.description = None
  - user.basic_info.integration_name = None
  - user.status.status = 'active'
  - user.status.status_info = None
  - user.status.need_password_change = False
  - user.organization.domain_name = 'home-1'
  - user.organization.domain_id: 미리 저장한 도메인의 id 와 같다
  - user.organization.role = 'user'
  - user.organization.resource_policy = 'user-policy-1'
  - user.organization.main_access_key: 이 호출이 만든 키와 같다
  - user.security.allowed_client_ip = None
  - user.security.totp_activated = False
  - user.security.totp_activated_at = None
  - user.security.sudo_session_enabled = False
  - user.container.container_uid = None
  - user.container.container_main_gid = None
  - user.container.container_gids = None
  - user.timestamps.created_at: 이 실행이 쓴 시각
  - user.timestamps.modified_at: 이 실행이 쓴 시각
  - created[0].keypair.id: 건너뜀: 매니저가 만든 access key 입니다
  - created[0].keypair.field_id: 건너뜀: 데이터베이스가 생성합니다
  - created[0].keypair.access_key: 건너뜀: 매니저가 만듭니다
  - created[0].keypair.is_active = True
  - created[0].keypair.is_admin = False
  - created[0].keypair.is_default = True
  - created[0].keypair.rate_limit = 10000
  - created[0].keypair.resource_policy = 'default-keypair-policy-1'
  - created[0].keypair.ssh_public_key: 건너뜀: 매니저가 만든 RSA 키입니다
  - created[0].keypair.num_queries = 0
  - created[0].keypair.last_used = None
  - created[0].keypair.user_id: 방금 만든 사용자와 같다
  - created[0].keypair.created_at: 이 실행이 쓴 시각
  - created[0].keypair.modified_at: 이 실행이 쓴 시각
  - created[0].secret_key: 매니저가 만든 비밀 키가 채워져 있습니다

<a id="creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs"></a>

#### [a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

권한 받은 사용자가 이 일괄 생성을 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 CREATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.bulk_create_users_with_keypair: user-1이 home-1에 made 을 일괄 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.bulk_update_users

<a id="retiring-a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit"></a>

#### [a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

superadmin 이 일괄 수정으로 활성 사용자에 DELETED, 삭제 상태 사용자에 ACTIVE, 다른 삭제 상태 사용자에 전체 이름을 주면, 둘은 삭제와 복원을 거쳐 수정 목록에, 하나는 실패로 담깁니다

Given

- 도메인 하나와 superadmin 하나, 활성 사용자 하나, 삭제 상태 사용자 둘
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - superadmin user-4: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.bulk_update_users: user-4이 user-1에 DELETED, user-2에 ACTIVE, user-3에 전체 이름을 일괄 수정으로 줍니다

Then

- 삭제한 사용자와 복원한 사용자가 수정 목록에, 나머지 하나가 실패 목록에 옵니다
  - updated_users.id: DELETED 와 ACTIVE 를 준 사용자와 같다
  - failed.user_id: 삭제 상태에서 전체 이름만 변경한 사용자와 같다
  - failed.message: 건너뜀: 예외 메시지는 변경되어도 되는 값입니다
  - updated_users[deleted user].id: 미리 저장한 사용자와 같다
  - updated_users[deleted user].basic_info.username = 'user-1'
  - updated_users[deleted user].basic_info.email = 'user-1@scenario.local'
  - updated_users[deleted user].basic_info.full_name = None
  - updated_users[deleted user].basic_info.description = None
  - updated_users[deleted user].basic_info.integration_name = None
  - updated_users[deleted user].status.status = 'deleted'
  - updated_users[deleted user].status.status_info = 'admin-requested'
  - updated_users[deleted user].status.need_password_change = False
  - updated_users[deleted user].organization.domain_name = 'home-1'
  - updated_users[deleted user].organization.role = 'user'
  - updated_users[deleted user].organization.resource_policy = 'user-policy-1'
  - updated_users[deleted user].organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - updated_users[deleted user].security.allowed_client_ip = None
  - updated_users[deleted user].security.totp_activated = False
  - updated_users[deleted user].security.totp_activated_at = None
  - updated_users[deleted user].security.sudo_session_enabled = False
  - updated_users[deleted user].container.container_uid = None
  - updated_users[deleted user].container.container_main_gid = None
  - updated_users[deleted user].container.container_gids = None
  - updated_users[deleted user].timestamps.created_at: 이 실행이 쓴 시각
  - updated_users[deleted user].timestamps.modified_at: 이 실행이 쓴 시각
  - updated_users[restored user].id: 미리 저장한 사용자와 같다
  - updated_users[restored user].basic_info.username = 'user-2'
  - updated_users[restored user].basic_info.email = 'user-2@scenario.local'
  - updated_users[restored user].basic_info.full_name = None
  - updated_users[restored user].basic_info.description = None
  - updated_users[restored user].basic_info.integration_name = None
  - updated_users[restored user].status.status = 'active'
  - updated_users[restored user].status.status_info = 'admin-requested'
  - updated_users[restored user].status.need_password_change = False
  - updated_users[restored user].organization.domain_name = 'home-1'
  - updated_users[restored user].organization.role = 'user'
  - updated_users[restored user].organization.resource_policy = 'user-policy-2'
  - updated_users[restored user].organization.main_access_key: 활성 기본 키가 없어 비어 있습니다
  - updated_users[restored user].security.allowed_client_ip = None
  - updated_users[restored user].security.totp_activated = False
  - updated_users[restored user].security.totp_activated_at = None
  - updated_users[restored user].security.sudo_session_enabled = False
  - updated_users[restored user].container.container_uid = None
  - updated_users[restored user].container.container_main_gid = None
  - updated_users[restored user].container.container_gids = None
  - updated_users[restored user].timestamps.created_at: 이 실행이 쓴 시각
  - updated_users[restored user].timestamps.modified_at: 이 실행이 쓴 시각

<a id="editing-a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed"></a>

#### [a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

superadmin 이 일괄 수정과 함께 다른 사용자의 키로 기본 키 전환을 주면, 그 사용자는 수정 목록에서 빠지고 실패로 담깁니다

Given

- 도메인 하나와 대상 사용자, 사용자 1명 더, 호출자는 superadmin 입니다, 한 사람에게 기본이 아닌 키가 하나 더 있습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - superadmin user-4: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.bulk_update_users: user-3이 user-1을 일괄 수정하며 user-2의 키로 기본 키를 옮깁니다

Then

- 수정 목록은 비고, 그 사용자가 실패 목록에 옵니다
  - updated_users = []
  - failed.length = 1
  - failed[0].user_id: 기본 키를 옮기려던 사용자와 같다
  - failed[0].message: 건너뜀: 예외 메시지는 변경되어도 되는 값입니다

<a id="editing-the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart"></a>

#### [the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

전역 역할이 문인 일괄 수정에서 superadmin 이 있는 사용자와 이름이 겹치게 변경하는 사용자를 함께 주면, 하나는 수정되고 하나는 사용자 id 와 함께 실패로 담깁니다

Given

- 도메인 하나와 대상 사용자, 사용자 2명 더, 호출자는 superadmin 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - superadmin user-4: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-5: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - superadmin user-5: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.bulk_update_users: user-4이 user-1의 전체 이름을 변경하고 user-3의 이름을 user-2로 일괄 수정합니다

Then

- 하나는 수정 목록에, 하나는 실패 목록에 옵니다
  - updated_users.length = 1
  - failed.length = 1
  - updated_users[0].id: 미리 저장한 사용자와 같다
  - updated_users[0].basic_info.username = 'user-1'
  - updated_users[0].basic_info.email = 'user-1@scenario.local'
  - updated_users[0].basic_info.full_name = 'renamed'
  - updated_users[0].basic_info.description = None
  - updated_users[0].basic_info.integration_name = None
  - updated_users[0].status.status = 'active'
  - updated_users[0].status.status_info = None
  - updated_users[0].status.need_password_change = False
  - updated_users[0].organization.domain_name = 'home-1'
  - updated_users[0].organization.role = 'user'
  - updated_users[0].organization.resource_policy = 'user-policy-1'
  - updated_users[0].organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - updated_users[0].security.allowed_client_ip = None
  - updated_users[0].security.totp_activated = False
  - updated_users[0].security.totp_activated_at = None
  - updated_users[0].security.sudo_session_enabled = False
  - updated_users[0].container.container_uid = None
  - updated_users[0].container.container_main_gid = None
  - updated_users[0].container.container_gids = None
  - updated_users[0].timestamps.created_at: 이 실행이 쓴 시각
  - updated_users[0].timestamps.modified_at: 이 실행이 쓴 시각
  - failed[0].user_id: 이름이 겹치게 변경한 사용자와 같다
  - failed[0].message: 건너뜀: 예외 메시지는 변경되어도 되는 값입니다

<a id="editing-a-user-who-is-not-the-superadmin-may-not-bulk-edit-users"></a>

#### [a-user-who-is-not-the-superadmin-may-not-bulk-edit-users](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

도메인 스코프에서 UPDATE 를 받은 사용자라도 일괄 수정하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 사용자 2명 더, 호출자는 user 이고 도메인 스코프에서 UPDATE 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 user-4: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-5: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - superadmin user-5: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-4: 역할 user-role-1 보유

When

- UserAdapter.bulk_update_users: user-4이 user-1의 전체 이름을 변경하고 user-3의 이름을 user-2로 일괄 수정합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.create_user

<a id="creating-a-user-granted-create-on-a-domain-makes-a-user-in-it"></a>

#### [a-user-granted-create-on-a-domain-makes-a-user-in-it](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

도메인 스코프에서 사용자 읽기와 생성 권한을 받은 사용자가 그 도메인에 사용자를 만들면, 만든 사용자 전체와 기본 키가 비밀 키와 함께 옵니다

Given

- 도메인 하나와 user 한 명, 호출자는 도메인 스코프에서 사용자 READ and CREATE 권한을 받았습니다
  - 도메인 home-1
  - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
  - 기본 키페어 정책 default-keypair-policy-1: 키페어가 정책을 대지 않으면 이 정책을 받습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, CREATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.create_user: user-1이 home-1에 made 을 생성합니다

Then

- 만든 사용자 전체와, 그 사용자의 기본 키가 비밀 키와 함께 응답으로 옵니다
  - user.id: 건너뜀: 데이터베이스가 생성합니다
  - user.entity_id: 그 사용자의 id 와 같다
  - user.basic_info.username = 'made'
  - user.basic_info.email = 'made@scenario.local'
  - user.basic_info.full_name = None
  - user.basic_info.description = None
  - user.basic_info.integration_name = None
  - user.status.status = 'active'
  - user.status.status_info = None
  - user.status.need_password_change = False
  - user.organization.domain_name = 'home-1'
  - user.organization.domain_id: 미리 저장한 도메인의 id 와 같다
  - user.organization.role = 'user'
  - user.organization.resource_policy = 'user-policy-1'
  - user.organization.main_access_key: 이 호출이 만든 키와 같다
  - user.security.allowed_client_ip = None
  - user.security.totp_activated = False
  - user.security.totp_activated_at = None
  - user.security.sudo_session_enabled = False
  - user.container.container_uid = None
  - user.container.container_main_gid = None
  - user.container.container_gids = None
  - user.timestamps.created_at: 이 실행이 쓴 시각
  - user.timestamps.modified_at: 이 실행이 쓴 시각
  - keypair.id: 건너뜀: 매니저가 만든 access key 입니다
  - keypair.field_id: 건너뜀: 데이터베이스가 생성합니다
  - keypair.access_key: 건너뜀: 매니저가 만듭니다
  - keypair.is_active = True
  - keypair.is_admin = False
  - keypair.is_default = True
  - keypair.rate_limit = 10000
  - keypair.resource_policy = 'default-keypair-policy-1'
  - keypair.ssh_public_key: 건너뜀: 매니저가 만든 RSA 키입니다
  - keypair.num_queries = 0
  - keypair.last_used = None
  - keypair.user_id: 방금 만든 사용자와 같다
  - keypair.created_at: 이 실행이 쓴 시각
  - keypair.modified_at: 이 실행이 쓴 시각
  - secret_key: 매니저가 만든 비밀 키가 채워져 있습니다

<a id="creating-a-user-granted-nothing-may-not-create-a-user"></a>

#### [a-user-granted-nothing-may-not-create-a-user](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

역할을 받지 않은 사용자가 생성하려 하면, 도메인 스코프 권한 문이 막습니다

Given

- 도메인 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.create_user: user-1이 home-1에 made 을 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="creating-a-user-may-not-be-created-in-a-domain-name-nothing-answers-to"></a>

#### [a-user-may-not-be-created-in-a-domain-name-nothing-answers-to](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

권한 받은 사용자가 어떤 도메인도 아닌 이름을 주면, 도메인 이름 조회 단계가 대상 없음으로 막습니다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 CREATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.create_user: user-1이 no-such-domain 에 made 을 생성합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### UserAdapter.delete_user_by_id

<a id="retiring-a-user-granted-soft-delete-marks-another-user-deleted"></a>

#### [a-user-granted-soft-delete-marks-another-user-deleted](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 SOFT_DELETE 를 받은 사용자가 삭제하면, 성공이 오고 그 사용자 상태가 삭제로 변경됩니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 SOFT_DELETE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.delete_user_by_id: user-2이 user-1을 삭제하고 다시 읽습니다

Then

- 성공이 오고, 다시 읽은 사용자는 deleted 상태입니다
  - success = True
  - the read that follows.id: 미리 저장한 사용자와 같다
  - the read that follows.basic_info.username = 'user-1'
  - the read that follows.basic_info.email = 'user-1@scenario.local'
  - the read that follows.basic_info.full_name = None
  - the read that follows.basic_info.description = None
  - the read that follows.basic_info.integration_name = None
  - the read that follows.status.status = 'deleted'
  - the read that follows.status.status_info = 'admin-requested'
  - the read that follows.status.need_password_change = False
  - the read that follows.organization.domain_name = 'home-1'
  - the read that follows.organization.role = 'user'
  - the read that follows.organization.resource_policy = 'user-policy-1'
  - the read that follows.organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - the read that follows.security.allowed_client_ip = None
  - the read that follows.security.totp_activated = False
  - the read that follows.security.totp_activated_at = None
  - the read that follows.security.sudo_session_enabled = False
  - the read that follows.container.container_uid = None
  - the read that follows.container.container_main_gid = None
  - the read that follows.container.container_gids = None
  - the read that follows.timestamps.created_at: 이 실행이 쓴 시각
  - the read that follows.timestamps.modified_at: 이 실행이 쓴 시각

<a id="retiring-a-user-granted-nothing-may-not-delete-another-user"></a>

#### [a-user-granted-nothing-may-not-delete-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

역할 없이 삭제하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.delete_user_by_id: user-2이 user-1을 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.get

<a id="reading-a-user-granted-read-on-another-user-reads-their-whole-node"></a>

#### [a-user-granted-read-on-another-user-reads-their-whole-node](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 읽으면, 기본 키까지 채운 노드 전체가 응답으로 옵니다

Given

- 도메인 하나와 사용자 둘, 한 사람은 다른 사람에 대한 사용자 읽기 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.get: user-2이 user-1을 id 로 읽습니다

Then

- 읽은 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="reading-a-user-granted-nothing-may-not-read-another-user"></a>

#### [a-user-granted-nothing-may-not-read-another-user](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

아무 역할도 받지 않은 사용자가 다른 사용자를 읽으려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.get: user-2이 user-1을 id 로 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.update_user_by_id

<a id="editing-a-user-granted-update-changing-only-the-full-name-leaves-the-rest"></a>

#### [a-user-granted-update-changing-only-the-full-name-leaves-the-rest](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 전체 이름만 주면, 전체 이름만 변경된 노드가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 호출자는 user 이고 대상 사용자 스코프에서 UPDATE, READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 전체 이름을 renamed 로 변경합니다

Then

- 전체 이름만 변경된 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = 'renamed'
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="retiring-an-edit-to-active-on-a-deleted-user-restores-the-user"></a>

#### [an-edit-to-active-on-a-deleted-user-restores-the-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 SOFT_DELETE 와 READ 를 받은 사용자가 삭제 상태 사용자에 수정으로 ACTIVE 를 주면, 복원과 같이 활성이 됩니다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 호출자는 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 SOFT_DELETE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 상태에 ACTIVE 를 줍니다

Then

- active 상태의 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = 'admin-requested'
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 활성 기본 키가 없어 비어 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="retiring-an-edit-to-deleted-soft-deletes-the-user"></a>

#### [an-edit-to-deleted-soft-deletes-the-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 SOFT_DELETE 와 READ 를 받은 사용자가 수정으로 DELETED 를 주면, 삭제와 같이 삭제 상태가 됩니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 SOFT_DELETE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 상태에 DELETED 를 줍니다

Then

- deleted 상태의 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'deleted'
  - status.status_info = 'admin-requested'
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="editing-another-users-new-password-leaves-the-password-change-requirement"></a>

#### [another-users-new-password-leaves-the-password-change-requirement](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

대상 사용자 스코프에서 UPDATE 와 READ 를 받은 다른 사용자가 비밀번호 변경을 요구받는 사용자에게 새 비밀번호만 주면, 요구가 남은 노드가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 호출자는 user 이고 대상 사용자 스코프에서 UPDATE, READ 를 받았습니다, 대상 사용자는 비밀번호 변경을 요구받습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다, 비밀번호 변경을 요구받습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 비밀번호만 변경합니다

Then

- 비밀번호 변경 요구가 남은 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = True
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="editing-naming-a-default-key-in-an-edit-moves-the-default-to-it"></a>

#### [naming-a-default-key-in-an-edit-moves-the-default-to-it](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

권한 받은 사용자가 대상 사용자의 다른 키를 기본 키로 지정하면, 수정이 반영된 뒤 기본 키가 옮겨간 노드가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 호출자는 user 이고 대상 사용자 스코프에서 UPDATE, READ 를 받았습니다, 한 사람에게 기본이 아닌 키가 하나 더 있습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.update_user_by_id: user-2이 user-1의 추가한 키를 기본 키로 지정합니다

Then

- 기본 키가 추가한 키로 옮겨간 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 추가한 키와 같다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="editing-null-project-ids-in-an-edit-leave-the-membership-as-it-is"></a>

#### [null-project-ids-in-an-edit-leave-the-membership-as-it-is](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

권한 받은 사용자가 소속 프로젝트 자리에 빈 값을 주면, 소속을 건드리지 않고 나머지 수정만 반영됩니다

Given

- 도메인 하나와 프로젝트 하나, 그 멤버 목록에 오른 대상 사용자, 대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 team-1
  - 일반 사용자 user-1: 프로젝트 team-1 멤버 목록에 추가됨
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 소속 프로젝트에 빈 값을 주고, user-3이 team-1으로 조회합니다

Then

- 사용자는 그대로이고 프로젝트 멤버 목록에 남아 있습니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각
  - the project search that follows.items: 멤버 목록에 올린 대상 사용자 하나와 같다
  - the project search that follows.pagination.total = 1
  - the project search that follows.pagination.offset = 0
  - the project search that follows.pagination.limit = 50

<a id="editing-setting-ones-own-new-password-lifts-the-password-change-requirement"></a>

#### [setting-ones-own-new-password-lifts-the-password-change-requirement](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

비밀번호 변경을 요구받는 사용자가 자기 사용자 스코프에서 UPDATE 와 READ 를 받고, 새 비밀번호와 요구 해제를 함께 주면, 요구가 해제된 노드가 응답으로 옵니다

Given

- 도메인 하나와 비밀번호 변경을 요구받는 사용자 한 명, 그 사용자는 자기 사용자 스코프에서 UPDATE, READ 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다, 비밀번호 변경을 요구받습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-1이 자기 비밀번호를 변경하며 비밀번호 변경 요구를 해제합니다

Then

- 비밀번호 변경 요구가 해제된 사용자 전체가 응답으로 옵니다
  - id: 미리 저장한 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-edit-another-user"></a>

#### [a-user-granted-nothing-may-not-edit-another-user](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

역할을 받지 않은 사용자가 수정하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 user 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.update_user_by_id: user-2이 user-1의 전체 이름을 renamed 로 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-a-username-another-user-holds-may-not-be-taken"></a>

#### [a-username-another-user-holds-may-not-be-taken](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

권한 받은 사용자가 이미 쓰이는 사용자 이름을 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 대상 사용자, 사용자 1명 더, 호출자는 user 이고 대상 사용자 스코프에서 UPDATE 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - superadmin user-4: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-3이 user-1의 이름을 user-2로 변경합니다

Then

- 거부됩니다
  - 거부: UserModificationBadRequest

<a id="retiring-an-edit-of-another-field-on-a-deleted-user-is-refused"></a>

#### [an-edit-of-another-field-on-a-deleted-user-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 삭제 상태 사용자의 전체 이름을 변경하면, 삭제된 사용자라 거부됩니다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 호출자는 대상에 대한 사용자 UPDATE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 전체 이름을 변경합니다

Then

- 거부됩니다
  - 거부: UserDeleted

<a id="retiring-an-edit-to-a-status-other-than-active-or-inactive-is-refused"></a>

#### [an-edit-to-a-status-other-than-active-or-inactive-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 수정으로 BEFORE_VERIFICATION 을 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 대상에 대한 사용자 UPDATE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 상태에 BEFORE_VERIFICATION 을 줍니다

Then

- 거부됩니다
  - 거부: UserModificationBadRequest

<a id="retiring-an-edit-to-deleted-is-refused-without-soft-delete"></a>

#### [an-edit-to-deleted-is-refused-without-soft-delete](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 UPDATE 와 READ 만 받은 사용자가 수정으로 DELETED 를 주면, 삭제의 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 대상에 대한 사용자 UPDATE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 상태에 DELETED 를 줍니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-an-edit-to-deleted-on-a-deleted-user-changes-nothing"></a>

#### [an-edit-to-deleted-on-a-deleted-user-changes-nothing](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

삭제 상태 사용자에 수정으로 DELETED 만 주면, 아무것도 변경되지 않고 그 사용자가 응답으로 옵니다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 호출자는 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 SOFT_DELETE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id: user-2이 user-1의 상태에 DELETED 를 줍니다

Then

- 삭제 상태 그대로인 사용자 전체가 응답으로 옵니다
  - 거부: NotEnoughPermission

### LoginSessionAdapter.admin_revoke

<a id="login_sessions-the-superadmin-revokes-another-users-login-session"></a>

#### [the-superadmin-revokes-another-users-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

전역 역할이 문인 관리자 회수에서 superadmin 이 다른 사용자의 세션을 회수하면, 성공이 오고 세션 전체 검색에서 빠지며 관리자가 회수했다는 이력이 생깁니다

Given

- 도메인 하나와 superadmin, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_revoke: user-2이 관리자 경로로 user-1의 세션을 회수합니다

Then

- 회수가 성공하고 뒤이은 조회에 세션이 없습니다
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
  - after.has_next_page = False
  - after.has_previous_page = False

<a id="login_sessions-a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin"></a>

#### [a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

권한 받은 사용자가 관리자 회수를 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 세션을 가진 사용자 하나, 호출자는 도메인 스코프에서 사용자 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginSessionAdapter.admin_revoke: user-2이 관리자 경로로 user-1의 세션을 회수합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="login_sessions-even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist"></a>

#### [even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

superadmin 이 없는 세션 id 를 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 superadmin, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_revoke: user-2이 관리자 경로로 없는 세션을 회수합니다

Then

- 거부됩니다
  - 거부: LoginSessionNotFoundError

### LoginSessionAdapter.admin_unblock_user

<a id="login_sessions-the-superadmin-unblocks-a-user"></a>

#### [the-superadmin-unblocks-a-user](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

전역 역할이 문인 차단 해제에서 superadmin 이 사용자 이름을 주면, 성공이 오고 그 이름의 차단 기록이 사라집니다

Given

- 도메인 하나와 superadmin, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_unblock_user: user-2이 user-1의 차단을 해제합니다

Then

- 차단 해제가 성공합니다
  - success = True

<a id="login_sessions-unblocking-a-username-nobody-holds-still-succeeds"></a>

#### [unblocking-a-username-nobody-holds-still-succeeds](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

superadmin 이 어떤 사용자도 아닌 이름을 주면, 존재를 확인하지 않고 성공이 옵니다

Given

- 도메인 하나와 superadmin, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_unblock_user: user-2이 어떤 사용자도 아닌 이름의 차단을 해제합니다

Then

- 차단 해제가 성공합니다
  - success = True

<a id="login_sessions-a-user-who-is-not-the-superadmin-may-not-unblock-a-user"></a>

#### [a-user-who-is-not-the-superadmin-may-not-unblock-a-user](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

권한 받은 사용자가 차단을 해제하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 세션을 가진 사용자 하나, 호출자는 도메인 스코프에서 사용자 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginSessionAdapter.admin_unblock_user: user-2이 user-1의 차단을 해제합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### LoginSessionAdapter.my_revoke

<a id="login_sessions-a-user-granted-update-on-themselves-revokes-their-own-login-session"></a>

#### [a-user-granted-update-on-themselves-revokes-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

자기 스코프에서 READ 와 UPDATE 를 받은 사용자가 자기 세션을 회수하면, 성공이 오고 그 세션은 더 조회되지 않으며 사용자가 회수했다는 이력이 생깁니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_revoke: user-1이 자기 세션을 회수합니다

Then

- 회수가 성공하고 뒤이은 조회에 세션이 없습니다
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
  - after.has_next_page = False
  - after.has_previous_page = False

<a id="login_sessions-a-user-granted-nothing-may-not-revoke-their-own-login-session"></a>

#### [a-user-granted-nothing-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

역할 없이 회수하려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 사용자 둘, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.my_revoke: user-1이 자기 세션을 회수합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="login_sessions-a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session"></a>

#### [a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

자기 스코프에서만 READ 와 UPDATE 를 받은 사용자가 다른 사용자의 세션을 주면, 그 소유자에 대한 조회 단계가 막습니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_revoke: user-1이 user-2의 세션을 회수합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="login_sessions-a-user-granted-only-read-may-not-revoke-their-own-login-session"></a>

#### [a-user-granted-only-read-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

READ 만 받고 회수하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 사용자 둘, 호출자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_revoke: user-1이 자기 세션을 회수합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.admin_create_keypair

<a id="managing_keypairs-a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy"></a>

#### [a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

superadmin 이 아니어도 대상 사용자 스코프에서 UPDATE 를 받은 사용자가 정책을 주고 키를 생성하면, 기본 아닌 새 키와 secret 이 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_create_keypair: user-2이 user-1에게 granted-policy-1으로 키를 생성합니다

Then

- 생성한 키 전체와 secret 이 응답으로 옵니다
  - id: 건너뜀: 매니저가 생성한 access key 입니다
  - access_key: 건너뜀: 매니저가 생성합니다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 30000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key: 건너뜀: 매니저가 생성한 RSA 키입니다
  - num_queries = 0
  - last_used = None
  - user_id: 키페어 소유자와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - secret_key: 건너뜀: 매니저가 생성합니다

<a id="managing_keypairs-a-key-may-not-be-made-under-a-policy-that-does-not-exist"></a>

#### [a-key-may-not-be-made-under-a-policy-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_create_keypair: user-2이 user-1에게 없는 정책으로 키를 생성합니다

Then

- 거부됩니다
  - 거부: KeypairResourcePolicyNotFound

<a id="managing_keypairs-a-user-granted-nothing-may-not-make-a-key-for-another"></a>

#### [a-user-granted-nothing-may-not-make-a-key-for-another](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 키를 생성하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_create_keypair: user-2이 user-1에게 granted-policy-1으로 키를 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.admin_delete_keypair

<a id="managing_keypairs-a-granted-user-deleting-another-users-extra-key-gets-its-access-key"></a>

#### [a-granted-user-deleting-another-users-extra-key-gets-its-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 삭제하면, 삭제한 키의 access key 가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 대상에 대한 사용자 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_keypair: user-2이 user-1의 기본 아닌 키를 삭제합니다

Then

- 삭제한 키의 access key 가 응답으로 옵니다
  - access_key: 미리 저장한 키와 같다

<a id="managing_keypairs-a-user-granted-nothing-may-not-delete-another-users-key"></a>

#### [a-user-granted-nothing-may-not-delete-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 삭제하려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.admin_delete_keypair: user-2이 user-1의 기본 아닌 키를 삭제합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-delete-another-users-key"></a>

#### [a-user-granted-only-read-may-not-delete-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

READ 만 받고 삭제하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 대상에 대한 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_keypair: user-2이 user-1의 기본 아닌 키를 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="managing_keypairs-another-users-default-key-may-not-be-deleted"></a>

#### [another-users-default-key-may-not-be-deleted](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

권한 받은 사용자가 대상의 기본 키를 삭제하려 하면, 입력 검증이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_keypair: user-2이 user-1의 기본 키를 삭제합니다

Then

- 거부됩니다
  - 거부: KeyPairForbidden

### UserAdapter.admin_delete_ssh_keypair

<a id="managing_keypairs-a-granted-user-clearing-another-users-ssh-key-empties-the-public-key"></a>

#### [a-granted-user-clearing-another-users-ssh-key-empties-the-public-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 삭제하면, access key 가 오고 공개키가 비워집니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_ssh_keypair: user-2이 user-1의 기본 키에서 SSH 키를 삭제하고 읽습니다

Then

- 대상의 기본 키가 오고, 뒤이은 읽기에서 공개키가 변경되어 있습니다
  - access_key: 대상의 기본 키와 같다
  - the ssh_public_key of the read that follows = None

<a id="managing_keypairs-a-user-granted-nothing-may-not-clear-another-users-ssh-key"></a>

#### [a-user-granted-nothing-may-not-clear-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 삭제하려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_delete_ssh_keypair: user-2이 user-1의 기본 키에서 SSH 키를 삭제하고 읽습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-clear-another-users-ssh-key"></a>

#### [a-user-granted-only-read-may-not-clear-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

READ 만 받고 삭제하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_ssh_keypair: user-2이 user-1의 기본 키에서 SSH 키를 삭제하고 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.admin_get_keypair

<a id="managing_keypairs-a-granted-user-reads-another-users-key-by-access-key"></a>

#### [a-granted-user-reads-another-users-key-by-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

대상 스코프에서 READ 를 받은 사용자가 읽으면, 그 키 노드 전체가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 대상에 대한 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_get_keypair: user-2이 user-1의 키를 access key 로 읽습니다

Then

- 미리 저장한 키 전체가 응답으로 옵니다
  - id: 미리 저장한 키와 같다
  - access_key: 미리 저장한 키와 같다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키 소유자와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="managing_keypairs-a-user-granted-nothing-may-not-read-another-users-key"></a>

#### [a-user-granted-nothing-may-not-read-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 읽으려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.admin_get_keypair: user-2이 user-1의 키를 access key 로 읽습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### UserAdapter.admin_get_ssh_keypair

<a id="managing_keypairs-a-granted-user-reads-another-users-ssh-public-key-only"></a>

#### [a-granted-user-reads-another-users-ssh-public-key-only](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

대상 스코프에서 READ 를 받은 사용자가 읽으면, access key 와 공개키만 오고 개인키는 오지 않습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_get_ssh_keypair: user-2이 user-1의 SSH 공개키를 읽습니다

Then

- access key 와 공개키만 응답으로 옵니다
  - keypair.access_key: 대상의 기본 키와 같다
  - keypair.ssh_public_key = ''

<a id="managing_keypairs-a-user-granted-nothing-may-not-read-another-users-ssh-public-key"></a>

#### [a-user-granted-nothing-may-not-read-another-users-ssh-public-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 읽으려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_get_ssh_keypair: user-2이 user-1의 SSH 공개키를 읽습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### UserAdapter.admin_register_ssh_keypair

<a id="managing_keypairs-a-granted-user-registering-another-users-ssh-key-gets-the-access-key"></a>

#### [a-granted-user-registering-another-users-ssh-key-gets-the-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 공개키와 개인키를 주면, 형식 검사 없이 덮어쓰고 access key 가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_register_ssh_keypair: user-2이 user-1의 기본 키에 SSH 키를 등록하고 읽습니다

Then

- 대상의 기본 키가 오고, 뒤이은 읽기에서 공개키가 변경되어 있습니다
  - access_key: 대상의 기본 키와 같다
  - the ssh_public_key of the read that follows = 'ssh-rsa scenario-public-key'

<a id="managing_keypairs-a-user-granted-nothing-may-not-register-another-users-ssh-key"></a>

#### [a-user-granted-nothing-may-not-register-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 등록하려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_register_ssh_keypair: user-2이 user-1의 기본 키에 SSH 키를 등록하고 읽습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-register-another-users-ssh-key"></a>

#### [a-user-granted-only-read-may-not-register-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

READ 만 받고 등록하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 대상에 대한 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_register_ssh_keypair: user-2이 user-1의 기본 키에 SSH 키를 등록하고 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.admin_update_keypair

<a id="managing_keypairs-a-granted-user-changing-another-users-rate-limit-changes-only-that"></a>

#### [a-granted-user-changing-another-users-rate-limit-changes-only-that](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

대상 스코프에서 READ 와 UPDATE 를 받은 사용자가 요청 한도만 주면, 나머지는 그대로이고 한도만 변경된 키 노드가 응답으로 옵니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 대상에 대한 사용자 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_update_keypair: user-2이 user-1의 키에 요청 한도를 지정합니다

Then

- 요청 한도만 변경된 키 전체가 응답으로 옵니다
  - id: 미리 저장한 키와 같다
  - access_key: 미리 저장한 키와 같다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 45000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키 소유자와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="managing_keypairs-a-user-granted-nothing-may-not-change-another-users-key"></a>

#### [a-user-granted-nothing-may-not-change-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

역할 없이 변경하려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.admin_update_keypair: user-2이 user-1의 키에 요청 한도를 지정합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-change-another-users-key"></a>

#### [a-user-granted-only-read-may-not-change-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

READ 만 받고 변경하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 대상에 대한 사용자 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_update_keypair: user-2이 user-1의 키에 요청 한도를 지정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="managing_keypairs-another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist"></a>

#### [another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 대상 사용자, 대상에게 기본 아닌 키 하나, 호출자는 대상에 대한 사용자 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_update_keypair: user-2이 user-1의 키에 요청 한도와 없는 정책을 지정합니다

Then

- 거부됩니다
  - 거부: KeypairResourcePolicyNotFound

### UserAdapter.bulk_purge_users

<a id="retiring-a-bulk-purge-records-a-missing-id-as-a-failure"></a>

#### [a-bulk-purge-records-a-missing-id-as-a-failure](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

superadmin 이 있는 사용자와 없는 id 를 함께 주면, 하나는 영구 삭제되고 없는 id 는 실패로 담깁니다

Given

- 도메인 하나와 superadmin 하나, 사용자 1명, 그리고 어떤 사용자도 아닌 id 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.bulk_purge_users: user-2이 user-1와 없는 id 를 일괄로 영구 삭제합니다

Then

- 삭제한 사용자 id 와 개수, 그리고 실패가 응답으로 옵니다
  - successes: 미리 저장한 사용자 전부와 같다
  - purged_count = 1
  - failed.user_id: 없는 id 와 같다
  - failed.message: 건너뜀: 예외 메시지는 변경되어도 되는 값입니다

<a id="retiring-the-superadmin-bulk-purge-answers-the-purged-ids-and-count"></a>

#### [the-superadmin-bulk-purge-answers-the-purged-ids-and-count](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

전역 역할이 문인 일괄 영구 삭제에서 superadmin 이 사용자 둘을 주면, 두 id 와 개수 둘이 응답으로 옵니다

Given

- 도메인 하나와 superadmin 하나, 사용자 2명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.bulk_purge_users: user-3이 user-1, user-2를 일괄로 영구 삭제합니다

Then

- 삭제한 사용자 id 와 개수, 그리고 실패가 응답으로 옵니다
  - successes: 미리 저장한 사용자 전부와 같다
  - purged_count = 2
  - failed = []

<a id="retiring-a-user-who-is-not-the-superadmin-may-not-purge-in-bulk"></a>

#### [a-user-who-is-not-the-superadmin-may-not-purge-in-bulk](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

도메인 스코프에서 HARD_DELETE 를 받은 사용자라도 일괄 영구 삭제를 하려 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 사용자 하나, 호출자는 도메인 스코프의 사용자 HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 HARD_DELETE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.bulk_purge_users: user-2이 user-1를 일괄로 영구 삭제합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### UserAdapter.issue_my_keypair

<a id="own_keypairs-a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key"></a>

#### [a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

자기 사용자 스코프에서 UPDATE 를 받은 사용자가 발급하면, 기본 키의 관리자 표시, 정책, 요청 한도를 따르고 기본 표시는 없는 키와 secret 이 응답으로 옵니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.issue_my_keypair: user-1이 자기 키를 발급합니다

Then

- 기본 키를 따르는 기본 아닌 새 키와 secret 이 응답으로 옵니다
  - id: 건너뜀: 매니저가 생성한 access key 입니다
  - access_key: 건너뜀: 매니저가 생성합니다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-1'
  - ssh_public_key: 건너뜀: 매니저가 생성한 RSA 키입니다
  - num_queries = 0
  - last_used = None
  - user_id: 키페어 소유자와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - secret_key: 건너뜀: 매니저가 매번 새로 생성합니다

<a id="own_keypairs-an-issued-key-made-default-lets-the-original-default-key-be-revoked"></a>

#### [an-issued-key-made-default-lets-the-original-default-key-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 키를 발급하고 그 키로 기본 키를 옮긴 다음 원래 기본 키를 회수하면, 세 호출이 차례로 통과하고 발급한 키 하나만 남습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.issue_my_keypair: user-1이 자기 키 검색으로 기본 키를 찾고, 키를 발급해 그 키로 기본 키를 옮긴 다음 원래 기본 키를 회수하고 자기 키를 다시 조회합니다

Then

- 세 호출이 통과하고 발급한 키 하나만 남습니다
  - issued.id: 건너뜀: 매니저가 생성한 access key 입니다
  - issued.access_key: 건너뜀: 매니저가 생성합니다
  - issued.is_active = True
  - issued.is_admin = False
  - issued.is_default = False
  - issued.rate_limit = 10000
  - issued.resource_policy = 'keypair-policy-1'
  - issued.ssh_public_key: 건너뜀: 매니저가 생성한 RSA 키입니다
  - issued.num_queries = 0
  - issued.last_used = None
  - issued.user_id: 키페어 소유자와 같다
  - issued.created_at: 이 실행이 쓴 시각
  - issued.modified_at: 이 실행이 쓴 시각
  - issued.secret_key: 건너뜀: 매니저가 매번 새로 생성합니다
  - switched = True
  - revoked = True
  - after.total_count = 1
  - after.has_next_page = False
  - after.has_previous_page = False
  - after.items.access_key: 발급한 키와 같다
  - after.items[0].is_active = True
  - after.items[0].is_admin = False
  - after.items[0].is_default = True
  - after.items[0].rate_limit = 10000
  - after.items[0].resource_policy = 'keypair-policy-1'
  - after.items[0].ssh_public_key: 건너뜀: 매니저가 생성한 RSA 키입니다
  - after.items[0].num_queries = 0
  - after.items[0].last_used = None
  - after.items[0].user_id: 키 소유자와 같다
  - after.items[0].created_at: 이 실행이 쓴 시각
  - after.items[0].modified_at: 이 실행이 쓴 시각

<a id="own_keypairs-a-user-granted-nothing-may-not-issue-their-own-key"></a>

#### [a-user-granted-nothing-may-not-issue-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

역할을 받지 않은 사용자가 자기 키를 발급하려 하면, 본인이어도 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.issue_my_keypair: user-1이 자기 키를 발급합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserAdapter.purge_user_by_id

<a id="retiring-a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions"></a>

#### [a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 HARD_DELETE 를 받은 사용자가 삭제되지 않은 사용자를 영구 삭제해도, 성공이 오고 그 사용자를 더 찾을 수 없습니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 대상에 대한 사용자 HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 HARD_DELETE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.purge_user_by_id: user-2이 자기에게 넘기며 user-1을 영구 삭제하고, 뒤이어 user-3이 일괄 읽습니다

Then

- 성공이 오고, 그 사용자를 더 찾을 수 없습니다
  - success = True
  - the batch read that follows: 건너뜀: 없는 id 에 superadmin 이 받는 응답은 아직 정해지지 않았습니다

<a id="retiring-a-user-granted-nothing-may-not-purge-another-user"></a>

#### [a-user-granted-nothing-may-not-purge-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

역할 없이 영구 삭제하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.purge_user_by_id: user-2이 자기에게 넘기며 user-1을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-purging-a-user-to-an-admin-who-does-not-exist-is-refused"></a>

#### [purging-a-user-to-an-admin-who-does-not-exist-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

권한 받은 사용자가 넘겨받을 관리자로 없는 id 를 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 대상 사용자 하나, 호출자는 대상에 대한 사용자 HARD_DELETE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 HARD_DELETE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.purge_user_by_id: user-2이 없는 관리자 id 에게 넘기며 user-1을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: UserNotFound

### UserAdapter.restore_user_by_id

<a id="retiring-a-user-granted-soft-delete-restores-a-deleted-user-to-active"></a>

#### [a-user-granted-soft-delete-restores-a-deleted-user-to-active](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

대상 사용자 스코프에서 SOFT_DELETE 를 받은 사용자가 삭제 상태 사용자를 복원하면, 성공이 오고 상태가 활성으로 변경됩니다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 호출자는 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 SOFT_DELETE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.restore_user_by_id: user-2이 user-1을 복원하고 다시 읽습니다

Then

- 성공이 오고, 다시 읽은 사용자는 active 상태입니다
  - success = True
  - the read that follows.id: 미리 저장한 사용자와 같다
  - the read that follows.basic_info.username = 'user-1'
  - the read that follows.basic_info.email = 'user-1@scenario.local'
  - the read that follows.basic_info.full_name = None
  - the read that follows.basic_info.description = None
  - the read that follows.basic_info.integration_name = None
  - the read that follows.status.status = 'active'
  - the read that follows.status.status_info = 'admin-requested'
  - the read that follows.status.need_password_change = False
  - the read that follows.organization.domain_name = 'home-1'
  - the read that follows.organization.role = 'user'
  - the read that follows.organization.resource_policy = 'user-policy-1'
  - the read that follows.organization.main_access_key: 활성 기본 키가 없어 비어 있습니다
  - the read that follows.security.allowed_client_ip = None
  - the read that follows.security.totp_activated = False
  - the read that follows.security.totp_activated_at = None
  - the read that follows.security.sudo_session_enabled = False
  - the read that follows.container.container_uid = None
  - the read that follows.container.container_main_gid = None
  - the read that follows.container.container_gids = None
  - the read that follows.timestamps.created_at: 이 실행이 쓴 시각
  - the read that follows.timestamps.modified_at: 이 실행이 쓴 시각

<a id="retiring-a-user-granted-nothing-may-not-restore-another-user"></a>

#### [a-user-granted-nothing-may-not-restore-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

역할 없이 복원하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.restore_user_by_id: user-2이 user-1을 복원합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-restoring-a-user-who-was-not-deleted-is-refused"></a>

#### [restoring-a-user-who-was-not-deleted-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

권한 받은 사용자가 삭제되지 않은 비활성 사용자를 복원하려 하면, 삭제 상태가 아니라 거부됩니다

Given

- 도메인 하나와 대상 inactive 상태 사용자 하나, 호출자는 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 inactive 상태 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 inactive, 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 SOFT_DELETE, READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.restore_user_by_id: user-2이 user-1을 복원합니다

Then

- 거부됩니다
  - 거부: UserModificationBadRequest

### UserAdapter.revoke_my_keypair

<a id="own_keypairs-a-user-granted-read-and-update-revokes-a-non-default-key"></a>

#### [a-user-granted-read-and-update-revokes-a-non-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 자기의 기본 아닌 키를 회수하면, 성공이 오고 자기 키 검색에서 그 키가 빠집니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair: user-1이 기본 아닌 자기 키를 회수하고 자기 키를 다시 조회합니다

Then

- 회수에 성공하고, 뒤이은 자기 키 검색에 기본 키만 남습니다
  - success = True
  - after.total_count = 1
  - after.has_next_page = False
  - after.has_previous_page = False
  - after.items.length = 1
  - after.items[0].id: 건너뜀: 시드가 매번 새로 만든 access key 입니다
  - after.items[0].access_key: 건너뜀: 시드가 매번 새로 만든 access key 입니다
  - after.items[0].is_active = True
  - after.items[0].is_admin = False
  - after.items[0].is_default = True
  - after.items[0].rate_limit = 10000
  - after.items[0].resource_policy = 'keypair-policy-1'
  - after.items[0].ssh_public_key = ''
  - after.items[0].num_queries = 0
  - after.items[0].last_used = None
  - after.items[0].user_id: 키 소유자와 같다
  - after.items[0].created_at: 이 실행이 쓴 시각
  - after.items[0].modified_at: 이 실행이 쓴 시각

<a id="own_keypairs-a-user-granted-nothing-may-not-revoke-their-own-key"></a>

#### [a-user-granted-nothing-may-not-revoke-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

역할을 받지 않은 사용자가 회수하려 하면, 소유자 조회 단계가 없는 키와 같은 예외로 막습니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.revoke_my_keypair: user-1이 기본 아닌 자기 키를 회수하고 자기 키를 다시 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="own_keypairs-a-user-granted-only-read-may-not-revoke-their-own-key"></a>

#### [a-user-granted-only-read-may-not-revoke-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

자기 스코프에서 READ 만 받은 사용자가 회수하려 하면, 소유자 조회는 지나고 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair: user-1이 기본 아닌 자기 키를 회수하고 자기 키를 다시 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="own_keypairs-an-access-key-nobody-holds-may-not-be-revoked"></a>

#### [an-access-key-nobody-holds-may-not-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 어떤 키도 아닌 값을 주면, 소유자 조회 단계가 권한 없음과 같은 예외로 막습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair: user-1이 어떤 키도 아닌 값으로 회수합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="own_keypairs-the-default-key-may-not-be-revoked"></a>

#### [the-default-key-may-not-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 자기 기본 키를 회수하려 하면, 입력 검증이 막습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair: user-1이 자기 키 검색으로 기본 키를 찾아 그 키를 회수합니다

Then

- 거부됩니다
  - 거부: KeyPairForbidden

### UserAdapter.switch_default_access_key

<a id="own_keypairs-a-user-granted-read-and-update-moves-their-default-key"></a>

#### [a-user-granted-read-and-update-moves-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

자기 스코프에서 UPDATE 를 받은 사용자가 기본 아닌 활성 키로 기본 키를 옮기면, 성공이 오고 사용자 노드의 기본 키가 그 키가 됩니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.switch_default_access_key: user-1이 기본 아닌 자기 키로 기본 키를 옮기고 자기 사용자를 다시 읽습니다

Then

- 전환에 성공하고, 뒤이은 읽기에서 기본 키가 추가한 키입니다
  - success = True
  - node.id: 미리 저장한 사용자와 같다
  - node.basic_info.username = 'user-1'
  - node.basic_info.email = 'user-1@scenario.local'
  - node.basic_info.full_name = None
  - node.basic_info.description = None
  - node.basic_info.integration_name = None
  - node.status.status = 'active'
  - node.status.status_info = None
  - node.status.need_password_change = False
  - node.organization.domain_name = 'home-1'
  - node.organization.role = 'user'
  - node.organization.resource_policy = 'user-policy-1'
  - node.organization.main_access_key: 추가한 키와 같다
  - node.security.allowed_client_ip = None
  - node.security.totp_activated = False
  - node.security.totp_activated_at = None
  - node.security.sudo_session_enabled = False
  - node.container.container_uid = None
  - node.container.container_main_gid = None
  - node.container.container_gids = None
  - node.timestamps.created_at: 이 실행이 쓴 시각
  - node.timestamps.modified_at: 이 실행이 쓴 시각

<a id="own_keypairs-a-user-granted-nothing-may-not-move-their-default-key"></a>

#### [a-user-granted-nothing-may-not-move-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

역할 없이 기본 키를 옮기려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.switch_default_access_key: user-1이 기본 아닌 자기 키로 기본 키를 옮깁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="own_keypairs-someone-elses-key-may-not-become-the-default-key"></a>

#### [someone-elses-key-may-not-become-the-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 다른 사용자의 키를 주면, 입력 검증이 막습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 기본 아닌 키를 가진 다른 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.switch_default_access_key: user-1이 다른 사용자의 키로 기본 키를 옮깁니다

Then

- 거부됩니다
  - 거부: KeyPairForbidden

### UserAdapter.update_my_keypair

<a id="own_keypairs-a-user-granted-read-and-update-turns-off-a-non-default-key"></a>

#### [a-user-granted-read-and-update-turns-off-a-non-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

자기 스코프에서 READ 와 UPDATE 를 받은 사용자가 기본 아닌 키를 비활성으로 변경하면, 활성만 변경된 키 노드가 응답으로 옵니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_my_keypair: user-1이 기본 아닌 자기 키를 비활성으로 변경합니다

Then

- 활성만 변경된 키 노드 전체가 응답으로 옵니다
  - id: 미리 저장한 키페어와 같다
  - access_key: 미리 저장한 키페어와 같다
  - is_active = False
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키페어 소유자와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="own_keypairs-a-user-granted-nothing-may-not-turn-off-their-own-key"></a>

#### [a-user-granted-nothing-may-not-turn-off-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

역할 없이 키를 비활성으로 변경하려 하면, 소유자 조회 단계가 막습니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다

When

- UserAdapter.update_my_keypair: user-1이 기본 아닌 자기 키를 비활성으로 변경합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="own_keypairs-a-user-granted-only-read-may-not-turn-off-their-own-key"></a>

#### [a-user-granted-only-read-may-not-turn-off-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

READ 만 받고 키를 비활성으로 변경하려 하면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_my_keypair: user-1이 기본 아닌 자기 키를 비활성으로 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="own_keypairs-the-default-key-may-not-be-turned-off"></a>

#### [the-default-key-may-not-be-turned-off](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

권한 받은 사용자가 자기 기본 키를 비활성으로 변경하려 하면, 입력 검증이 막습니다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_my_keypair: user-1이 자기 키 검색으로 기본 키를 찾아 비활성으로 변경합니다

Then

- 거부됩니다
  - 거부: KeyPairForbidden

### UserAdapter.update_user

<a id="editing-a-user-granted-update-changes-the-allowed-client-ip"></a>

#### [a-user-granted-update-changes-the-allowed-client-ip](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

대상 사용자 스코프에서 UPDATE 를 받은 사용자가 허용 IP 만 담은 수정을 보내면, 성공 표시가 오고 그 사용자의 허용 IP 가 변경됩니다

Given

- 도메인 하나와 대상 사용자, 호출자는 user 이고 대상 사용자 스코프에서 UPDATE 를 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user: user-2이 user-1의 허용 IP 를 변경하고, user-3이 다시 읽습니다

Then

- 성공이 오고, 다시 읽은 사용자는 허용 IP 만 변경되어 있습니다
  - success = True
  - the read that follows.id: 미리 저장한 사용자와 같다
  - the read that follows.basic_info.username = 'user-1'
  - the read that follows.basic_info.email = 'user-1@scenario.local'
  - the read that follows.basic_info.full_name = None
  - the read that follows.basic_info.description = None
  - the read that follows.basic_info.integration_name = None
  - the read that follows.status.status = 'active'
  - the read that follows.status.status_info = None
  - the read that follows.status.need_password_change = False
  - the read that follows.organization.domain_name = 'home-1'
  - the read that follows.organization.role = 'user'
  - the read that follows.organization.resource_policy = 'user-policy-1'
  - the read that follows.organization.main_access_key: 그 사용자의 기본 키가 채워져 있습니다
  - the read that follows.security.allowed_client_ip = ['10.0.0.1/32']
  - the read that follows.security.totp_activated = False
  - the read that follows.security.totp_activated_at = None
  - the read that follows.security.sudo_session_enabled = False
  - the read that follows.container.container_uid = None
  - the read that follows.container.container_main_gid = None
  - the read that follows.container.container_gids = None
  - the read that follows.timestamps.created_at: 이 실행이 쓴 시각
  - the read that follows.timestamps.modified_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-change-the-allowed-client-ip"></a>

#### [a-user-granted-nothing-may-not-change-the-allowed-client-ip](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

역할 없이 허용 IP 수정을 보내면, 엔티티 권한 문이 막습니다

Given

- 도메인 하나와 대상 사용자, 호출자는 user 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserAdapter.update_user: user-2이 user-1의 허용 IP 를 변경하고, user-3이 다시 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### UserConfigAdapter.create_auto_generated_file

<a id="config_files-a-user-granted-update-on-themselves-writes-their-own-config-file"></a>

#### [a-user-granted-update-on-themselves-writes-their-own-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

자기 자신에게 UPDATE 를 받은 사용자가 설정 파일을 만들면, 빈 응답이 옵니다

Given

- 도메인 하나와 사용자 하나, 사용자는 자기 자신에게 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserConfigAdapter.create_auto_generated_file: user-1이 자기 설정 파일을 하나 만듭니다

Then

- 빈 응답이 옵니다
  - response = {}

<a id="config_files-a-config-file-in-a-place-the-manager-keeps-is-refused"></a>

#### [a-config-file-in-a-place-the-manager-keeps-is-refused](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

UPDATE 를 받은 사용자가 관리자가 쓰는 자리에 설정 파일을 만들려 하면, 입력 검증이 거부합니다

Given

- 도메인 하나와 사용자 하나, 사용자는 자기 자신에게 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserConfigAdapter.create_auto_generated_file: user-1이 관리자가 쓰는 자리에 설정 파일을 만들려 합니다

Then

- 거부됩니다
  - 거부: InvalidDotfilePath

<a id="config_files-a-user-granted-nothing-may-not-write-a-config-file"></a>

#### [a-user-granted-nothing-may-not-write-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

권한을 받지 않은 사용자가 자기 설정 파일을 만들려 하면, 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 하나, 사용자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- UserConfigAdapter.create_auto_generated_file: user-1이 자기 설정 파일을 하나 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

