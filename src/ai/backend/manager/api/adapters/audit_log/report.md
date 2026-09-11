## audit_log

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/audit_log/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/audit_log/adapter.py)

Not exercised by any scenario: batch_load_fields.

### batch_loading

#### [a-user-who-is-not-the-superadmin-may-not-read-by-id](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

슈퍼관리자도 모니터도 아닌 사용자가 id 둘을 읽으면, 요청 전체가 역할 부족으로 거부된다

Given

- id로 집을 기록 둘과, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'edited' 기록
  - 일반 사용자 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 있는 id 둘을 한 번에

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [reading-an-empty-list-answers-empty-without-passing-the-gate](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

빈 id 목록으로 읽으면, 문도 지나지 않고 빈 답이 온다

Given

- id로 집을 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 빈 id 목록으로

Then

- 준 순서대로 오고, 없는 id 자리는 비어 있다
  - operations = []

#### [reading-present-and-absent-ids-answers-each-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

있는 id 둘과 없는 id 하나를 한 번에 읽으면, 준 순서대로 오고 없는 자리는 비어 있다

Given

- id로 집을 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 있는 id 둘과 없는 id 하나를 한 번에

Then

- 준 순서대로 오고, 없는 id 자리는 비어 있다
  - operations = ['edited', None, 'created']

#### [the-monitor-role-reading-by-id-sees-the-same-nodes-as-the-superadmin](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

이 읽기도 읽기이므로 모니터 역할 사용자가 id 둘을 읽으면, 슈퍼관리자와 같은 답을 본다

Given

- id로 집을 기록 둘과, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 모니터 user-1: 'edited' 기록
  - 모니터 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 있는 id 둘을 한 번에

Then

- 준 순서대로 오고, 없는 id 자리는 비어 있다
  - operations = ['edited', 'created']

### scoped_searching

#### [a-scope-id-that-is-not-an-entity-id-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

지목한 id가 id 꼴이 아니면, 입력이 틀렸다는 이유로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-1이 id 꼴이 아닌 값을 지목해 검색

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [a-status-filter-narrows-within-the-named-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

한 엔티티에 성공 기록과 거부 기록이 있을 때 그것을 지목하고 성공 상태로 걸러 검색하면, 성공한 것만 온다

Given

- 성공한 기록과 거부된 기록을 가진 프로젝트 하나와, 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-1: 'succeeded' 기록
  - 프로젝트 team-1: 'was-refused' 기록, denied 상태
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목하고 성공 상태로 걸러 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['succeeded']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-may-not-read-even-the-records-they-triggered](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

자기 자신에 읽기 권한을 받지 않은 사용자가 자기를 일으킨 사람으로 지목해 검색하면, 권한 부족으로 거부된다. 자기 기록을 읽는 문이 따로 없기 때문이다

Given

- 두 사용자가 각각 일으킨 기록과, 그중 첫 사용자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'acted-by-me' 기록, 일으킨 사용자가 정해져 있음
  - 일반 사용자 user-2: 'acted-by-another' 기록, 일으킨 사용자가 정해져 있음

When

- AuditLogAdapter.scoped_search — user-1이 일으킨 사용자를 지목해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-scope-search-an-entity](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

아무 권한도 받지 않은 사용자가 엔티티를 지목해 검색하면, 권한 부족으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

두 사용자가 각각 기록을 남겼고 한 사용자에 읽기 권한을 받은 사람이 그 사용자를 일으킨 사람으로 지목해 검색하면, 그 사용자가 일으킨 기록만 온다

Given

- 두 사용자가 각각 일으킨 기록과, 그 사용자에 읽기 권한을 받은 다른 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'acted-by-me' 기록, 일으킨 사용자가 정해져 있음
  - 일반 사용자 user-2: 'acted-by-another' 기록, 일으킨 사용자가 정해져 있음
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: user 전체에 READ 허용
  - 일반 사용자 user-3: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-3이 일으킨 사용자를 지목해 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['acted-by-me']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-read-on-an-entity-reads-only-that-entitys-records](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

두 엔티티에 기록이 하나씩 있고 한쪽에만 읽기 권한을 받은 사용자가 그 엔티티를 지목해 검색하면, 그 엔티티의 기록만 온다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['edited']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [naming-an-entity-nothing-answers-to-is-refused-as-permission](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

다른 엔티티에 읽기 권한을 받은 사용자가 아무것도 아닌 id를 지목해 검색하면, 그 id에 걸린 권한이 없어 권한 부족으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [naming-several-readable-entities-merges-their-records-newest-first](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

두 엔티티에 모두 읽기 권한을 받은 사용자가 둘을 함께 지목해 검색하면, 두 기록이 다 오고 최근 것이 먼저다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째·둘째 프로젝트에 읽기 권한 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유
  - 역할 record-reader-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-2: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-2 보유

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['edited', 'created']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-caps-a-scoped-page-and-says-more-follow](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

지목한 엔티티에 기록이 많고 페이지 크기를 대지 않으면, 열 건까지 오고 다음 페이지가 있다고 답한다

Given

- 기록 11개를 가진 프로젝트 하나와, 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-1: 'op-0' 기록
  - 프로젝트 team-1: 'op-1' 기록
  - 프로젝트 team-1: 'op-2' 기록
  - 프로젝트 team-1: 'op-3' 기록
  - 프로젝트 team-1: 'op-4' 기록
  - 프로젝트 team-1: 'op-5' 기록
  - 프로젝트 team-1: 'op-6' 기록
  - 프로젝트 team-1: 'op-7' 기록
  - 프로젝트 team-1: 'op-8' 기록
  - 프로젝트 team-1: 'op-9' 기록
  - 프로젝트 team-1: 'op-10' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 기본 페이지 크기만큼 오고 다음 페이지가 있다고 답한다
  - items_count = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [one-unreadable-entity-among-those-named-refuses-the-whole-read](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

한쪽에만 읽기 권한을 받은 사용자가 두 엔티티를 함께 지목해 검색하면, 볼 수 있는 것만 주는 대신 요청 전체가 권한 부족으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-monitor-role-without-a-grant-may-not-scope-search](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

모니터 역할 사용자라도 권한 없이 엔티티를 지목해 검색하면, 권한 부족으로 거부된다. 모니터가 지나는 것은 역할 문뿐이고 이 문은 권한 그래프가 지킨다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 받은 monitor 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-superadmin-naming-an-entity-nothing-answers-to-sees-an-empty-page](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

슈퍼관리자가 아무것도 아닌 id를 지목해 검색하면, 권한 검사를 지나 빈 답을 본다. 대상 없음으로 거부하는 자리가 아니다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 받은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-reads-a-named-entitys-records-without-a-grant](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 엔티티를 지목해 그 기록을 읽는다. 이 문은 권한 그래프가 지키기 때문이다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 받은 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 프로젝트 team-1: 'edited' 기록
  - 프로젝트 other-1: 'created' 기록
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지목해 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['edited']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

### searching

#### [a-cursor-that-cannot-be-decoded-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

해석할 수 없는 커서로 검색하면, 커서가 틀렸다는 이유로 거부된다

Given

- 서로 다른 시각의 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.admin_search — user-1이 깨진 커서로 검색

Then

- 거부된다
  - 거부: InvalidCursor

#### [a-status-filter-narrows-the-answer-to-the-status-it-names](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

성공 기록과 거부 기록이 섞여 있을 때 성공 상태로 걸러 검색하면, 성공한 것만 온다

Given

- 성공한 기록과 거부된 기록, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'succeeded' 기록
  - 슈퍼관리자 user-1: 'was-refused' 기록, denied 상태

When

- AuditLogAdapter.admin_search — user-1이 성공 상태로 걸러 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['succeeded']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-every-record](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

슈퍼관리자도 모니터도 아닌 사용자가 전체를 검색하면, 역할 부족으로 거부된다

Given

- 서로 다른 시각의 기록 둘과, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'edited' 기록
  - 일반 사용자 user-1: 'created' 기록

When

- AuditLogAdapter.admin_search — user-1이 필터 없이 전체 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-actor-filter-narrows-the-answer-to-the-user-who-triggered-it](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

두 사용자가 각각 기록을 남겼을 때 한 사용자로 걸러 검색하면, 그 사용자가 일으킨 것만 온다

Given

- 두 사용자가 각각 남긴 기록과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'acted-by-me' 기록, 일으킨 사용자가 정해져 있음
  - 일반 사용자 user-2: 'acted-by-another' 기록, 일으킨 사용자가 정해져 있음

When

- AuditLogAdapter.admin_search — user-3이 일으킨 사용자로 걸러 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['acted-by-me']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [naming-two-pagination-modes-at-once-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

오프셋 방식과 커서 방식을 함께 주고 검색하면, 입력이 틀렸다는 이유로 거부된다

Given

- 서로 다른 시각의 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.admin_search — user-1이 두 페이지 방식을 함께 주고 검색

Then

- 거부된다
  - 거부: InvalidGraphQLParameters

#### [omitting-the-page-size-caps-the-page-and-says-more-follow](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

페이지 크기를 대지 않고 검색하면, 열 건까지 오고 다음 페이지가 있다고 답한다

Given

- 기록 11개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'op-0' 기록
  - 슈퍼관리자 user-1: 'op-1' 기록
  - 슈퍼관리자 user-1: 'op-2' 기록
  - 슈퍼관리자 user-1: 'op-3' 기록
  - 슈퍼관리자 user-1: 'op-4' 기록
  - 슈퍼관리자 user-1: 'op-5' 기록
  - 슈퍼관리자 user-1: 'op-6' 기록
  - 슈퍼관리자 user-1: 'op-7' 기록
  - 슈퍼관리자 user-1: 'op-8' 기록
  - 슈퍼관리자 user-1: 'op-9' 기록
  - 슈퍼관리자 user-1: 'op-10' 기록

When

- AuditLogAdapter.admin_search — user-1이 크기 없이 검색

Then

- 기본 페이지 크기만큼 오고 다음 페이지가 있다고 답한다
  - items_count = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [the-monitor-role-searching-sees-the-same-records-as-the-superadmin](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

검색은 읽기이므로 모니터 역할 사용자도 전역 문을 지나 슈퍼관리자와 같은 답을 본다

Given

- 서로 다른 시각의 기록 둘과, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 모니터 user-1: 'edited' 기록
  - 모니터 user-1: 'created' 기록

When

- AuditLogAdapter.admin_search — user-1이 필터 없이 전체 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['edited', 'created']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-searching-without-a-filter-sees-every-record-newest-first](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

기록 둘이 있고 슈퍼관리자가 필터 없이 검색하면, 둘 다 오고 최근 것이 먼저다

Given

- 서로 다른 시각의 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.admin_search — user-1이 필터 없이 전체 검색

Then

- 지목한 기록이 순서대로, 그리고 그것만 온다
  - items = ['edited', 'created']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-does-not-let-a-plain-user-search-every-record](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아닌 사용자는 전체를 검색할 수 없다. 이 문은 권한 그래프가 아니라 역할이 지킨다

Given

- 서로 다른 시각의 기록 둘과, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'edited' 기록
  - 일반 사용자 user-1: 'created' 기록

When

- AuditLogAdapter.admin_search — user-1이 필터 없이 전체 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

