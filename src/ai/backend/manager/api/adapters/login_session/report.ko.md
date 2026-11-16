## login_session

[어댑터](/src/ai/backend/manager/api/adapters/login_session/adapter.py)

시나리오: 완성

- ops 구성 (3)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - my_search: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (3)
  - admin_revoke: 성공 있음 1 · 거부 있음 1 (global_scope)
  - admin_unblock_user: 성공 있음 1 · 거부 있음 1 (global_scope)
  - my_revoke: 성공 있음 1 · 거부 있음 1 (single_field)

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 세션 전체 검색에서 superadmin 이 상태 필터, 상태 정렬, 페이지를 주면, 사용자와 무관하게 필터에 맞는 세션이 세어지고 필터에 걸리는 세션은 빠집니다](#searching-the-superadmin-searches-every-users-login-sessions) | 성공 |
| [자기 사용자에 READ 를 받은 일반 사용자가 세션 전체 검색을 하면, 전역 역할 문이 막습니다](#searching-a-regular-user-may-not-search-every-login-session) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 를 받은 사용자가 자기 세션 둘을 id 로 읽으면 둘 다 옵니다](#batch_loading-a-user-granted-read-on-themselves-loads-their-own-login-sessions) | 성공 |
| [자기 사용자에 READ 를 받은 사용자가 자기 세션과 다른 사용자의 세션을 함께 읽으면, 다른 사용자의 세션만 거부됩니다](#batch_loading-a-user-granted-read-on-themselves-is-denied-another-users-login-session) | 거부 |

**my_search**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 를 받은 사용자가 상태 필터, 상태 정렬, 페이지를 주고 자기 세션을 조회하면, 다른 사용자의 세션과 필터에 걸리는 세션은 빠집니다](#searching-a-user-granted-read-on-themselves-searches-their-own-login-sessions) | 성공 |
| [자기 사용자에 UPDATE 만 받은 사용자가 자기 세션을 조회하면, 본인이어도 권한 검사가 막습니다](#searching-a-user-granted-only-update-may-not-search-their-own-login-sessions) | 거부 |

**admin_revoke**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 관리자 회수에서 superadmin 이 다른 사용자의 세션을 회수하면 성공합니다](#revoking-the-superadmin-revokes-another-users-login-session) | 성공 |
| [자기 사용자에 READ 와 UPDATE 를 받은 일반 사용자가 관리자 호출로 자기 세션을 회수하면, 전역 역할 문이 막습니다](#revoking-a-regular-user-may-not-revoke-a-login-session-as-admin) | 거부 |

**admin_unblock_user**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 문인 차단 해제에서 superadmin 이 사용자 이름으로 차단을 해제하면 성공합니다](#unblocking-the-superadmin-unblocks-a-user) | 성공 |
| [자기 사용자에 READ 와 UPDATE 를 받은 일반 사용자가 자기 차단을 해제하면, 전역 역할 문이 막습니다](#unblocking-a-regular-user-may-not-unblock-a-user) | 거부 |

**my_revoke**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 와 UPDATE 를 받은 사용자가 자기 세션을 회수하면 성공합니다](#revoking-a-user-granted-update-on-themselves-revokes-their-own-login-session) | 성공 |
| [자기 사용자에 READ 만 받은 사용자가 자기 세션을 회수하면, 권한 검사가 막습니다](#revoking-a-user-granted-only-read-may-not-revoke-their-own-login-session) | 거부 |

### admin_search

<a id="searching-the-superadmin-searches-every-users-login-sessions"></a>

#### [the-superadmin-searches-every-users-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

전역 역할이 문인 세션 전체 검색에서 superadmin 이 상태 필터, 상태 정렬, 페이지를 주면, 사용자와 무관하게 필터에 맞는 세션이 세어지고 필터에 걸리는 세션은 빠집니다

Given

- 도메인 하나와 superadmin 호출자, 세션 셋을 가진 사용자와 세션 하나를 가진 사용자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-2: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-2: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
  - 일반 사용자 user-3: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-3: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_search: user-1이 세션 전체에서 상태가 active 나 revoked 인 것을 상태 내림차순으로 첫 하나만 조회합니다

Then

- 걸린 3개 중 revoked 세션이 첫 페이지에 오고 다음 페이지가 있습니다
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 세션와 같다
  - items[0].field_id: 미리 저장한 세션와 같다
  - items[0].user_id: 세션 소유자와 같다
  - items[0].access_key: 세션을 연 키와 같다
  - items[0].status = 'revoked'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

<a id="searching-a-regular-user-may-not-search-every-login-session"></a>

#### [a-regular-user-may-not-search-every-login-session](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

자기 사용자에 READ 를 받은 일반 사용자가 세션 전체 검색을 하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ 권한을 받았습니다
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
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_search: user-1이 세션 전체에서 상태가 active 나 revoked 인 것을 상태 내림차순으로 첫 하나만 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-granted-read-on-themselves-loads-their-own-login-sessions"></a>

#### [a-user-granted-read-on-themselves-loads-their-own-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_batch_loading.py): pass

자기 사용자에 READ 를 받은 사용자가 자기 세션 둘을 id 로 읽으면 둘 다 옵니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ 권한을 받았습니다
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
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.batch_load_by_ids: user-1이 자기 active 세션과 revoked 세션을 id 로 함께 읽습니다

Then

- 두 세션이 요청한 순서대로 옵니다
  - length = 2
  - [0].id: 미리 저장한 세션와 같다
  - [0].field_id: 미리 저장한 세션와 같다
  - [0].user_id: 세션 소유자와 같다
  - [0].access_key: 세션을 연 키와 같다
  - [0].status = 'active'
  - [0].created_at: 이 실행이 쓴 시각
  - [0].last_accessed_at = None
  - [0].invalidated_at = None
  - [1].id: 미리 저장한 세션와 같다
  - [1].field_id: 미리 저장한 세션와 같다
  - [1].user_id: 세션 소유자와 같다
  - [1].access_key: 세션을 연 키와 같다
  - [1].status = 'revoked'
  - [1].created_at: 이 실행이 쓴 시각
  - [1].last_accessed_at = None
  - [1].invalidated_at = None

<a id="batch_loading-a-user-granted-read-on-themselves-is-denied-another-users-login-session"></a>

#### [a-user-granted-read-on-themselves-is-denied-another-users-login-session](/tests/scenario/bai_scenario/manager/login_session/test_batch_loading.py): pass

자기 사용자에 READ 를 받은 사용자가 자기 세션과 다른 사용자의 세션을 함께 읽으면, 다른 사용자의 세션만 거부됩니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ 권한을 받았습니다
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
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.batch_load_by_ids: user-1이 자기 active 세션과 user-2의 세션을 id 로 함께 읽습니다

Then

- 자기 세션은 오고, 다른 사용자의 세션 자리에는 거부가 옵니다
  - length = 2
  - [0].id: 미리 저장한 세션와 같다
  - [0].field_id: 미리 저장한 세션와 같다
  - [0].user_id: 세션 소유자와 같다
  - [0].access_key: 세션을 연 키와 같다
  - [0].status = 'active'
  - [0].created_at: 이 실행이 쓴 시각
  - [0].last_accessed_at = None
  - [0].invalidated_at = None
  - 거부: NotEnoughPermission

### my_search

<a id="searching-a-user-granted-read-on-themselves-searches-their-own-login-sessions"></a>

#### [a-user-granted-read-on-themselves-searches-their-own-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

자기 사용자에 READ 를 받은 사용자가 상태 필터, 상태 정렬, 페이지를 주고 자기 세션을 조회하면, 다른 사용자의 세션과 필터에 걸리는 세션은 빠집니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ 권한을 받았습니다
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
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.my_search: user-1이 자기 세션에서 상태가 active 나 revoked 인 것을 상태 오름차순으로 첫 하나만 조회합니다

Then

- 걸린 2개 중 active 세션이 첫 페이지에 오고 다음 페이지가 있습니다
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 세션와 같다
  - items[0].field_id: 미리 저장한 세션와 같다
  - items[0].user_id: 세션 소유자와 같다
  - items[0].access_key: 세션을 연 키와 같다
  - items[0].status = 'active'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

<a id="searching-a-user-granted-only-update-may-not-search-their-own-login-sessions"></a>

#### [a-user-granted-only-update-may-not-search-their-own-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

자기 사용자에 UPDATE 만 받은 사용자가 자기 세션을 조회하면, 본인이어도 권한 검사가 막습니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.my_search: user-1이 자기 세션에서 상태가 active 나 revoked 인 것을 상태 오름차순으로 첫 하나만 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### admin_revoke

<a id="revoking-the-superadmin-revokes-another-users-login-session"></a>

#### [the-superadmin-revokes-another-users-login-session](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

전역 역할이 문인 관리자 회수에서 superadmin 이 다른 사용자의 세션을 회수하면 성공합니다

Given

- 도메인 하나와 superadmin 호출자, 세션 셋을 가진 사용자와 세션 하나를 가진 사용자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-2: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-2: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
  - 일반 사용자 user-3: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-3: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_revoke: user-1이 관리자 호출로 user-2의 active 세션을 회수합니다

Then

- 회수가 성공합니다
  - success = True

<a id="revoking-a-regular-user-may-not-revoke-a-login-session-as-admin"></a>

#### [a-regular-user-may-not-revoke-a-login-session-as-admin](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

자기 사용자에 READ 와 UPDATE 를 받은 일반 사용자가 관리자 호출로 자기 세션을 회수하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_revoke: user-1이 관리자 호출로 user-1의 active 세션을 회수합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_unblock_user

<a id="unblocking-the-superadmin-unblocks-a-user"></a>

#### [the-superadmin-unblocks-a-user](/tests/scenario/bai_scenario/manager/login_session/test_unblocking.py): pass

전역 역할이 문인 차단 해제에서 superadmin 이 사용자 이름으로 차단을 해제하면 성공합니다

Given

- 도메인 하나와 superadmin 호출자, 세션 셋을 가진 사용자와 세션 하나를 가진 사용자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-2: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-2: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
  - 일반 사용자 user-3: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-3: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_unblock_user: user-1이 user-2의 차단을 해제합니다

Then

- 차단 해제가 성공합니다
  - success = True

<a id="unblocking-a-regular-user-may-not-unblock-a-user"></a>

#### [a-regular-user-may-not-unblock-a-user](/tests/scenario/bai_scenario/manager/login_session/test_unblocking.py): pass

자기 사용자에 READ 와 UPDATE 를 받은 일반 사용자가 자기 차단을 해제하면, 전역 역할 문이 막습니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.admin_unblock_user: user-1이 user-1의 차단을 해제합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### my_revoke

<a id="revoking-a-user-granted-update-on-themselves-revokes-their-own-login-session"></a>

#### [a-user-granted-update-on-themselves-revokes-their-own-login-session](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

자기 사용자에 READ 와 UPDATE 를 받은 사용자가 자기 세션을 회수하면 성공합니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ, UPDATE 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 사용자 READ, UPDATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.my_revoke: user-1이 자기 active 세션을 회수합니다

Then

- 회수가 성공합니다
  - success = True

<a id="revoking-a-user-granted-only-read-may-not-revoke-their-own-login-session"></a>

#### [a-user-granted-only-read-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

자기 사용자에 READ 만 받은 사용자가 자기 세션을 회수하면, 권한 검사가 막습니다

Given

- 도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 사용자에 READ 권한을 받았습니다
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
    - 일반 사용자 user-1: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-1: 상태가 active 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 revoked 인 로그인 세션 하나를 갖습니다
  - 일반 사용자 user-1: 상태가 invalidated 인 로그인 세션 하나를 갖습니다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 일반 사용자 user-2: 상태가 active 인 로그인 세션 하나를 갖습니다

When

- LoginSessionAdapter.my_revoke: user-1이 자기 active 세션을 회수합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

