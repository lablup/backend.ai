## login_history

[어댑터](/src/ai/backend/manager/api/adapters/login_history/adapter.py)

시나리오: 완성

- ops 구성 (3)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - my_search: 대표 성공 ✓ · 대표 거부 ✓

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 막는 전체 검색을 superadmin 이 필터, 정렬, 페이지와 함께 호출하면, 사용자와 무관하게 필터에 걸리는 이력의 첫 페이지가 정렬 순서대로 반환됩니다](#searching-the-superadmin-searches-the-login-history-of-every-user) | 성공 |
| [도메인 스코프에서 사용자 READ 를 받은 일반 사용자가 전체 검색을 호출하면, 전역 역할이 막습니다](#searching-a-regular-user-may-not-search-the-login-history-of-every-user) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 를 받은 사용자가 자기 기록 둘을 id 로 조회하면, 요청한 순서대로 노드 전체가 반환됩니다](#batch_loading-a-user-granted-read-on-themselves-loads-their-own-records-in-order) | 성공 |
| [자기 사용자에 READ 를 받은 사용자가 자기 기록과 다른 사용자의 기록을 함께 조회하면, 자기 기록은 노드 전체로, 다른 사용자의 기록은 권한 부족으로 그 항목에만 응답합니다](#batch_loading-a-record-of-another-user-is-refused-in-its-own-slot) | 거부 |

**my_search**

| 시나리오 | 판정 |
|---|---|
| [자기 사용자에 READ 를 받은 사용자가 필터, 정렬, 페이지와 함께 조회하면, 자기 이력 중 필터에 걸리는 첫 페이지가 정렬 순서대로 반환되고 다른 사용자의 이력은 빠집니다](#searching-a-user-granted-read-on-themselves-searches-their-own-login-history) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 이력을 조회하면, 본인이어도 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-their-own-login-history) | 거부 |

### admin_search

<a id="searching-the-superadmin-searches-the-login-history-of-every-user"></a>

#### [the-superadmin-searches-the-login-history-of-every-user](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

전역 역할이 막는 전체 검색을 superadmin 이 필터, 정렬, 페이지와 함께 호출하면, 사용자와 무관하게 필터에 걸리는 이력의 첫 페이지가 정렬 순서대로 반환됩니다

Given

- 도메인 하나와 superadmin 한 명, 사용자 둘이 남긴 이력 넷. 성공 하나, 차단 하나, 자격 증명 오류 하나, 비활성 하나
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
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_blocked
  - 일반 사용자 user-2: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_invalid_credentials
  - 일반 사용자 user-2: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_user_inactive

When

- LoginHistoryAdapter.admin_search: user-3이 모든 사용자의 로그인 이력을 조회합니다

Then

- 필터에 걸리는 기록 중 정렬 순서의 앞 페이지만 오고, 다음 페이지가 남습니다
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 미리 저장한 기록와 같다
  - items[0].field_id: 미리 저장한 기록와 같다
  - items[0].user_id: 기록 소유자와 같다
  - items[0].domain_name = 'home-1'
  - items[0].result = 'failed_blocked'
  - items[0].fail_reason = 'reason of failed_blocked'
  - items[0].client_ip = '203.0.113.10'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 미리 저장한 기록와 같다
  - items[1].field_id: 미리 저장한 기록와 같다
  - items[1].user_id: 기록 소유자와 같다
  - items[1].domain_name = 'home-1'
  - items[1].result = 'failed_invalid_credentials'
  - items[1].fail_reason = 'reason of failed_invalid_credentials'
  - items[1].client_ip = '203.0.113.10'
  - items[1].created_at: 이 실행이 쓴 시각

<a id="searching-a-regular-user-may-not-search-the-login-history-of-every-user"></a>

#### [a-regular-user-may-not-search-the-login-history-of-every-user](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

도메인 스코프에서 사용자 READ 를 받은 일반 사용자가 전체 검색을 호출하면, 전역 역할이 막습니다

Given

- 도메인 하나와 이력을 남긴 사용자 하나, 호출자는 도메인 스코프에서 사용자 READ 권한을 받은 일반 사용자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginHistoryAdapter.admin_search: user-2이 모든 사용자의 로그인 이력을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-granted-read-on-themselves-loads-their-own-records-in-order"></a>

#### [a-user-granted-read-on-themselves-loads-their-own-records-in-order](/tests/scenario/bai_scenario/manager/login_history/test_batch_loading.py): pass

자기 사용자에 READ 를 받은 사용자가 자기 기록 둘을 id 로 조회하면, 요청한 순서대로 노드 전체가 반환됩니다

Given

- 도메인 하나와 사용자 둘. 호출자는 자기 사용자에 READ 권한을 받았고, 이력은 호출자의 성공 하나, 호출자의 차단 하나, 다른 사용자의 성공 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_blocked
  - 일반 사용자 user-2: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.batch_load_by_ids: user-1이 기록 2개를 id 로 한 번에 조회합니다

Then

- 요청한 순서대로 항목마다 노드 전체 또는 권한 부족이 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 기록와 같다
  - [0].field_id: 미리 저장한 기록와 같다
  - [0].user_id: 기록 소유자와 같다
  - [0].domain_name = 'home-1'
  - [0].result = 'failed_blocked'
  - [0].fail_reason = 'reason of failed_blocked'
  - [0].client_ip = '203.0.113.10'
  - [0].created_at: 이 실행이 쓴 시각
  - [1].id: 미리 저장한 기록와 같다
  - [1].field_id: 미리 저장한 기록와 같다
  - [1].user_id: 기록 소유자와 같다
  - [1].domain_name = 'home-1'
  - [1].result = 'success'
  - [1].fail_reason = None
  - [1].client_ip = None
  - [1].created_at: 이 실행이 쓴 시각

<a id="batch_loading-a-record-of-another-user-is-refused-in-its-own-slot"></a>

#### [a-record-of-another-user-is-refused-in-its-own-slot](/tests/scenario/bai_scenario/manager/login_history/test_batch_loading.py): pass

자기 사용자에 READ 를 받은 사용자가 자기 기록과 다른 사용자의 기록을 함께 조회하면, 자기 기록은 노드 전체로, 다른 사용자의 기록은 권한 부족으로 그 항목에만 응답합니다

Given

- 도메인 하나와 사용자 둘. 호출자는 자기 사용자에 READ 권한을 받았고, 이력은 호출자의 성공 하나, 호출자의 차단 하나, 다른 사용자의 성공 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_blocked
  - 일반 사용자 user-2: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.batch_load_by_ids: user-1이 기록 2개를 id 로 한 번에 조회합니다

Then

- 요청한 순서대로 항목마다 노드 전체 또는 권한 부족이 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 기록와 같다
  - [0].field_id: 미리 저장한 기록와 같다
  - [0].user_id: 기록 소유자와 같다
  - [0].domain_name = 'home-1'
  - [0].result = 'success'
  - [0].fail_reason = None
  - [0].client_ip = None
  - [0].created_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission

### my_search

<a id="searching-a-user-granted-read-on-themselves-searches-their-own-login-history"></a>

#### [a-user-granted-read-on-themselves-searches-their-own-login-history](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

자기 사용자에 READ 를 받은 사용자가 필터, 정렬, 페이지와 함께 조회하면, 자기 이력 중 필터에 걸리는 첫 페이지가 정렬 순서대로 반환되고 다른 사용자의 이력은 빠집니다

Given

- 도메인 하나와 사용자 둘. 호출자의 이력 넷(성공, 차단, 자격 증명 오류, 비활성)과 다른 사용자의 자격 증명 오류 이력 하나, 호출자는 자기 사용자에 READ 권한을 받았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_blocked
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_invalid_credentials
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_user_inactive
  - 일반 사용자 user-2: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_invalid_credentials
  - 사용자 READ 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.my_search: user-1이 자기 로그인 이력을 조회합니다

Then

- 필터에 걸리는 기록 중 정렬 순서의 앞 페이지만 오고, 다음 페이지가 남습니다
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 미리 저장한 기록와 같다
  - items[0].field_id: 미리 저장한 기록와 같다
  - items[0].user_id: 기록 소유자와 같다
  - items[0].domain_name = 'home-1'
  - items[0].result = 'failed_blocked'
  - items[0].fail_reason = 'reason of failed_blocked'
  - items[0].client_ip = '203.0.113.10'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 미리 저장한 기록와 같다
  - items[1].field_id: 미리 저장한 기록와 같다
  - items[1].user_id: 기록 소유자와 같다
  - items[1].domain_name = 'home-1'
  - items[1].result = 'failed_invalid_credentials'
  - items[1].fail_reason = 'reason of failed_invalid_credentials'
  - items[1].client_ip = '203.0.113.10'
  - items[1].created_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-search-their-own-login-history"></a>

#### [a-user-granted-nothing-may-not-search-their-own-login-history](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

아무 권한도 받지 않은 사용자가 자기 이력을 조회하면, 본인이어도 권한 부족으로 거부됩니다

Given

- 도메인 하나와 사용자 둘. 호출자의 이력 넷(성공, 차단, 자격 증명 오류, 비활성)과 다른 사용자의 자격 증명 오류 이력 하나, 호출자는 아무 권한도 받지 않았습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 success
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_blocked
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_invalid_credentials
  - 일반 사용자 user-1: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_user_inactive
  - 일반 사용자 user-2: 로그인 시도 이력 하나를 갖습니다. 결과는 failed_invalid_credentials

When

- LoginHistoryAdapter.my_search: user-1이 자기 로그인 이력을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

