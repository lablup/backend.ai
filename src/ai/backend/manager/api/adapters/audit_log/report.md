## audit_log

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/audit_log/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/audit_log/adapter.py)

Not exercised by any scenario: batch_load_fields.

### batch_loading

#### [a-user-who-is-not-the-superadmin-may-not-read-by-id](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

슈퍼관리자도 모니터도 아닌 사용자가 id 둘을 조회하면, 요청 전체가 역할 부족으로 거부된다

Given

- id로 조회할 기록 둘과, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'edited' 기록
  - 일반 사용자 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 있는 id 둘을 한 번에 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [reading-an-empty-list-answers-empty-without-passing-the-gate](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

빈 id 목록으로 조회하면, 권한 검사도 거치지 않고 빈 응답이 반환된다

Given

- id로 조회할 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 요청한 순서대로 노드가 반환되고, 없는 id 자리는 비어 있다
  - length = 0

#### [reading-present-and-absent-ids-answers-each-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

있는 id 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 자리는 비어 있다

Given

- id로 조회할 기록 둘과, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 슈퍼관리자 user-1: 'edited' 기록
  - 슈퍼관리자 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 있는 id 둘과 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로 노드가 반환되고, 없는 id 자리는 비어 있다
  - length = 3
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - slot[1] = None
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [the-monitor-role-reading-by-id-sees-the-same-nodes-as-the-superadmin](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py) — pass

이 조회도 읽기 연산이므로 모니터 역할 사용자가 id 둘을 조회하면, 슈퍼관리자와 같은 응답을 받는다

Given

- id로 조회할 기록 둘과, monitor 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 모니터 user-1: 'edited' 기록
  - 모니터 user-1: 'created' 기록

When

- AuditLogAdapter.batch_load_by_ids — user-1이 있는 id 둘을 한 번에 조회

Then

- 요청한 순서대로 노드가 반환되고, 없는 id 자리는 비어 있다
  - length = 2
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

### scoped_searching

#### [a-record-tagged-with-a-scope-is-found-by-searching-that-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

다른 엔티티에 대한 기록이 한 프로젝트를 스코프로 달고 있을 때 그 프로젝트를 지목해 검색하면, 대상 엔티티가 그 프로젝트가 아니어도 그 기록이 온다

Given

- 다른 엔티티에 대한 기록이 한 프로젝트를 스코프로 달고 있고, 그 프로젝트에 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'linked' 기록, 스코프 1개 달림
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: project 전체에 READ 허용
  - 일반 사용자 user-2: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-2이 엔티티를 지정해 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'linked'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'linked was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [a-scope-id-that-is-not-an-entity-id-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

지정한 id가 id 형식이 아니면, 잘못된 입력으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한을 받은 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 id 형식이 아닌 값을 지정해 검색

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [a-status-filter-narrows-within-the-named-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

한 엔티티에 성공 기록과 거부 기록이 있을 때 그것을 지정하고 성공 상태 필터로 검색하면, 성공한 기록만 반환된다

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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정하고 성공 상태 필터로 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'succeeded'
  - entity_type = 'project'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'succeeded was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [a-user-granted-nothing-may-not-read-even-the-records-they-triggered](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

자기 자신에 읽기 권한을 받지 않은 사용자가 자기를 실행한 사용자로 지정해 검색하면, 권한 부족으로 거부된다. 자기 기록을 조회하는 호출이 따로 없기 때문이다

Given

- 두 사용자가 각각 실행한 기록과, 그중 첫 사용자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 'acted-by-me' 기록, 실행한 사용자가 정해져 있음
  - 일반 사용자 user-2: 'acted-by-another' 기록, 실행한 사용자가 정해져 있음

When

- AuditLogAdapter.scoped_search — user-1이 실행한 사용자를 지정해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-scope-search-an-entity](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

아무 권한도 없는 사용자가 엔티티를 지정해 검색하면, 권한 부족으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 없는 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

두 사용자가 각각 기록을 남겼고 한 사용자에 읽기 권한을 받은 사용자가 그 사용자를 실행한 사용자로 지정해 검색하면, 그 사용자가 실행한 기록만 반환된다

Given

- 두 사용자가 각각 실행한 기록과, 그 사용자에 대한 읽기 권한을 받은 다른 사용자 한 명
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
  - 일반 사용자 user-1: 'acted-by-me' 기록, 실행한 사용자가 정해져 있음
  - 일반 사용자 user-2: 'acted-by-another' 기록, 실행한 사용자가 정해져 있음
  - 역할 record-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 record-reader-1: user 전체에 READ 허용
  - 일반 사용자 user-3: 역할 record-reader-1 보유

When

- AuditLogAdapter.scoped_search — user-3이 실행한 사용자를 지정해 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'acted-by-me'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'acted-by-me was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by: 실행한 사용자와 같다

#### [a-user-granted-read-on-an-entity-reads-only-that-entitys-records](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

두 엔티티에 기록이 하나씩 있고 한쪽에만 읽기 권한을 받은 사용자가 그 엔티티를 지정해 검색하면, 그 엔티티의 기록만 반환된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한을 받은 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [naming-an-entity-nothing-answers-to-is-refused-as-permission](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

다른 엔티티에 읽기 권한을 받은 사용자가 어느 엔티티도 아닌 id를 지정해 검색하면, 그 id에 부여된 권한이 없어 권한 부족으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한을 받은 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [naming-several-readable-entities-merges-their-records-newest-first](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

두 엔티티에 모두 읽기 권한을 받은 사용자가 둘을 함께 지정해 검색하면, 두 기록이 다 반환되고 최근 것이 먼저다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째·둘째 프로젝트에 읽기 권한을 받은 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'created'
  - entity_type = 'project'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [omitting-the-page-size-caps-a-scoped-page-and-says-more-follow](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

지정한 엔티티에 기록이 많고 페이지 크기를 지정하지 않으면, 10건까지 반환되고 다음 페이지가 있다고 응답한다

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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 기본 페이지 크기만큼 반환되고 다음 페이지가 있다고 응답한다
  - items_count = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [one-unreadable-entity-among-those-named-refuses-the-whole-read](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

한쪽에만 읽기 권한을 받은 사용자가 두 엔티티를 함께 지정해 검색하면, 볼 수 있는 것만 주는 대신 요청 전체가 권한 부족으로 거부된다

Given

- 서로 다른 프로젝트의 기록 둘과, 첫째 프로젝트에 읽기 권한을 받은 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-monitor-role-without-a-grant-may-not-scope-search](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

모니터 역할 사용자라도 권한 없이 엔티티를 지정해 검색하면, 권한 부족으로 거부된다. 모니터가 통과하는 것은 역할 검사뿐이고 이 검색은 권한 그래프로 보호된다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 없는 monitor 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-superadmin-naming-an-entity-nothing-answers-to-sees-an-empty-page](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

슈퍼관리자가 어느 엔티티도 아닌 id를 지정해 검색하면, 권한 검사를 통과해 빈 응답을 받는다. 대상 없음으로 거부하는 경우가 아니다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 없는 superadmin 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-reads-a-named-entitys-records-without-a-grant](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 엔티티를 지정해 그 기록을 검색할 수 있다. 이 검색은 권한 그래프로 보호되기 때문이다

Given

- 서로 다른 프로젝트의 기록 둘과, 아무 권한도 없는 user 한 명
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

- AuditLogAdapter.scoped_search — user-1이 엔티티를 지정해 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

### searching

#### [a-cursor-that-cannot-be-decoded-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

해석할 수 없는 커서로 검색하면, 잘못된 커서로 거부된다

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

- AuditLogAdapter.admin_search — user-1이 손상된 커서로 검색

Then

- 거부된다
  - 거부: InvalidCursor

#### [a-status-filter-narrows-the-answer-to-the-status-it-names](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

성공 기록과 거부 기록이 섞여 있을 때 성공 상태 필터로 검색하면, 성공한 기록만 반환된다

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

- AuditLogAdapter.admin_search — user-1이 성공 상태 필터로 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'succeeded'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'succeeded was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

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

두 사용자가 각각 기록을 남겼을 때 한 사용자 필터로 검색하면, 그 사용자가 실행한 기록만 반환된다

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
  - 일반 사용자 user-1: 'acted-by-me' 기록, 실행한 사용자가 정해져 있음
  - 일반 사용자 user-2: 'acted-by-another' 기록, 실행한 사용자가 정해져 있음

When

- AuditLogAdapter.admin_search — user-3이 실행한 사용자 필터로 검색

Then

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'acted-by-me'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'acted-by-me was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by: 실행한 사용자와 같다

#### [naming-two-pagination-modes-at-once-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

오프셋 방식과 커서 방식을 함께 지정해 검색하면, 잘못된 입력으로 거부된다

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

- AuditLogAdapter.admin_search — user-1이 두 페이지 방식을 함께 지정해 검색

Then

- 거부된다
  - 거부: InvalidGraphQLParameters

#### [omitting-the-page-size-caps-the-page-and-says-more-follow](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

페이지 크기를 지정하지 않고 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다

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

- 기본 페이지 크기만큼 반환되고 다음 페이지가 있다고 응답한다
  - items_count = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [the-monitor-role-searching-sees-the-same-records-as-the-superadmin](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

검색은 읽기 연산이므로 모니터 역할 사용자도 전역 역할 검사를 통과해 슈퍼관리자와 같은 응답을 받는다

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

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [the-superadmin-searching-without-a-filter-sees-every-record-newest-first](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

기록 둘이 있고 슈퍼관리자가 필터 없이 검색하면, 둘 다 반환되고 최근 것이 먼저다

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

- 지정한 기록이 순서대로, 그리고 그것만 반환된다
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: 무시함 — 데이터베이스가 만든다
  - action_id: 무시함 — 실행마다 새로 생성된다
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: 기록의 대상 엔티티와 같다
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

#### [turning-enforcement-off-does-not-let-a-plain-user-search-every-record](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py) — pass

권한 검사를 꺼도 슈퍼관리자가 아닌 사용자는 전체를 검색할 수 없다. 이 검색은 권한 그래프가 아니라 역할로 보호된다

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

