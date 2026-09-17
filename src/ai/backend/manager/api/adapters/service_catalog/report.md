## service_catalog

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/service_catalog/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/service_catalog/adapter.py)

Not exercised by any scenario: batch_load_fields.

### searching

#### [a-group-filter-narrows-the-answer-to-the-services-of-that-group](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

그룹이 다른 서비스 둘 중 한 그룹으로 걸러 조회하면, 답에는 그 그룹의 서비스만 남는다

Given

- 그룹이 다른 서비스 둘과, 슈퍼관리자 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-1: agent 그룹에 정상 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 manager 그룹으로 걸러 조회

Then

- 골라낸 그룹의 서비스 하나만 남는다
  - items.id: 골라낸 서비스와 같다
  - items.service_group = ['manager']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-status-equals-filter-keeps-the-services-of-that-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

상태마다 하나씩 있는 서비스를 비정상과 같은 것으로 걸러 조회하면 비정상 서비스만 반환된다

Given

- 정상·비정상·등록 해제 상태의 서비스 하나씩과, 슈퍼관리자 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록됨
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 상태가 unhealthy인 것으로 걸러 조회

Then

- 비정상 상태의 서비스만 반환된다
  - items.id: 그 상태로 심은 서비스와 같다
  - items.instance_id = ['unhealthy-1']
  - items.status = [<ServiceCatalogStatus.UNHEALTHY: 'unhealthy'>]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-status-in-filter-keeps-the-services-of-a-listed-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

상태마다 하나씩 있는 서비스를 비정상·등록 해제 목록에 든 것으로 걸러 조회하면 비정상과 등록 해제 서비스만 반환된다

Given

- 정상·비정상·등록 해제 상태의 서비스 하나씩과, 슈퍼관리자 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록됨
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 상태가 unhealthy, deregistered 중 하나인 것으로 걸러 조회

Then

- 비정상·등록 해제 상태의 서비스만 반환된다
  - items.id: 그 상태로 심은 서비스와 같다
  - items.instance_id = ['deregistered-1', 'unhealthy-1']
  - items.status = [<ServiceCatalogStatus.DEREGISTERED: 'deregistered'>, <ServiceCatalogStatus.UNHEALTHY: 'unhealthy'>]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-status-not-equals-filter-drops-the-services-of-that-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

상태마다 하나씩 있는 서비스를 비정상과 다른 것으로 걸러 조회하면 정상과 등록 해제 서비스만 반환된다

Given

- 정상·비정상·등록 해제 상태의 서비스 하나씩과, 슈퍼관리자 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록됨
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 상태가 unhealthy이 아닌 것으로 걸러 조회

Then

- 정상·등록 해제 상태의 서비스만 반환된다
  - items.id: 그 상태로 심은 서비스와 같다
  - items.instance_id = ['deregistered-1', 'healthy-1']
  - items.status = [<ServiceCatalogStatus.DEREGISTERED: 'deregistered'>, <ServiceCatalogStatus.HEALTHY: 'healthy'>]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-status-not-in-filter-drops-the-services-of-a-listed-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

상태마다 하나씩 있는 서비스를 비정상·등록 해제 목록에 들지 않은 것으로 걸러 조회하면 정상 서비스만 반환된다

Given

- 정상·비정상·등록 해제 상태의 서비스 하나씩과, 슈퍼관리자 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록됨
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 상태가 unhealthy, deregistered 중 어느 것도 아닌 것으로 걸러 조회

Then

- 정상 상태의 서비스만 반환된다
  - items.id: 그 상태로 심은 서비스와 같다
  - items.instance_id = ['healthy-1']
  - items.status = [<ServiceCatalogStatus.HEALTHY: 'healthy'>]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-services](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부된다

Given

- 서비스 2개와, 일반 사용자 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖는다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [omitting-the-page-size-answers-ten-services-and-a-next-page](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

서비스 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다

Given

- 서비스 11개와, 슈퍼관리자 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖는다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-2: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-3: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-4: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-5: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-6: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-7: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-8: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-9: manager 그룹에 정상 상태로 등록됨
  - 서비스 other-10: manager 그룹에 정상 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 기본 크기의 첫 페이지가 반환된다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [the-monitor-role-counts-every-service-as-the-superadmin-does](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

모니터 역할이 필터 없이 조회하면 슈퍼관리자와 같은 답을 받는다. 이 검색은 읽기 연산이라 모니터 역할이 전역 역할 검사를 통과한다

Given

- 서비스 2개와, 모니터 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖는다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 심은 서비스가 모두, 엔드포인트와 함께 통째로 집계된다
  - items.instance_id = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 심은 서비스와 같다
  - items[0].service_group = 'manager'
  - items[0].instance_id = 'other-1'
  - items[0].display_name = 'other-1'
  - items[0].version = '26.9.0'
  - items[0].labels = {}
  - items[0].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[0].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[0].registered_at: 이 실행이 쓴 시각
  - items[0].last_heartbeat: 이 실행이 쓴 시각
  - items[0].config_hash = ''
  - items[0].len(endpoints) = 0
  - items[1].id: 심은 서비스와 같다
  - items[1].service_group = 'manager'
  - items[1].instance_id = 'wanted-1'
  - items[1].display_name = 'wanted-1'
  - items[1].version = '26.9.0'
  - items[1].labels = {}
  - items[1].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[1].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[1].registered_at: 이 실행이 쓴 시각
  - items[1].last_heartbeat: 이 실행이 쓴 시각
  - items[1].config_hash = ''
  - items[1].len(endpoints) = 1
  - items[1].endpoints[0].id: 무시함 — 데이터베이스가 만든다
  - items[1].endpoints[0].role = 'api'
  - items[1].endpoints[0].scope = 'public'
  - items[1].endpoints[0].address = '127.0.0.1'
  - items[1].endpoints[0].port = 8080
  - items[1].endpoints[0].protocol = 'http'
  - items[1].endpoints[0].metadata = {'zone': 'a'}

#### [the-superadmin-counts-every-service-laid-with-its-endpoints](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py) — pass

서비스 둘 중 하나가 엔드포인트를 가질 때 슈퍼관리자가 필터 없이 조회하면, 둘 다 집계되고 엔드포인트가 함께 담긴다

Given

- 서비스 2개와, 슈퍼관리자 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록됨
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖는다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록됨
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ServiceCatalogAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 심은 서비스가 모두, 엔드포인트와 함께 통째로 집계된다
  - items.instance_id = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 심은 서비스와 같다
  - items[0].service_group = 'manager'
  - items[0].instance_id = 'other-1'
  - items[0].display_name = 'other-1'
  - items[0].version = '26.9.0'
  - items[0].labels = {}
  - items[0].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[0].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[0].registered_at: 이 실행이 쓴 시각
  - items[0].last_heartbeat: 이 실행이 쓴 시각
  - items[0].config_hash = ''
  - items[0].len(endpoints) = 0
  - items[1].id: 심은 서비스와 같다
  - items[1].service_group = 'manager'
  - items[1].instance_id = 'wanted-1'
  - items[1].display_name = 'wanted-1'
  - items[1].version = '26.9.0'
  - items[1].labels = {}
  - items[1].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[1].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[1].registered_at: 이 실행이 쓴 시각
  - items[1].last_heartbeat: 이 실행이 쓴 시각
  - items[1].config_hash = ''
  - items[1].len(endpoints) = 1
  - items[1].endpoints[0].id: 무시함 — 데이터베이스가 만든다
  - items[1].endpoints[0].role = 'api'
  - items[1].endpoints[0].scope = 'public'
  - items[1].endpoints[0].address = '127.0.0.1'
  - items[1].endpoints[0].port = 8080
  - items[1].endpoints[0].protocol = 'http'
  - items[1].endpoints[0].metadata = {'zone': 'a'}

