## service_catalog

[배경](/src/ai/backend/manager/api/adapters/service_catalog/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/service_catalog/adapter.py)

시나리오: 미완성 1 / 2

- ops 구성 (1)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (1)
  - batch_load_by_ids: 성공 있음 1 · 거부 없음 (partial_bulk): SCENARIO-GAP

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [그룹이 다른 서비스 둘 중 한 그룹으로 필터 기반 조회하면, 응답에는 그 그룹의 서비스만 남습니다](#searching-a-group-filter-narrows-the-answer-to-the-services-of-that-group) | 성공 |
| [상태마다 하나씩 있는 서비스를 비정상과 같은 것으로 필터 기반 조회하면 비정상 서비스만 반환됩니다](#searching-a-status-equals-filter-keeps-the-services-of-that-status) | 성공 |
| [상태마다 하나씩 있는 서비스를 비정상, 등록 해제 목록에 든 것으로 필터 기반 조회하면 비정상과 등록 해제 서비스만 반환됩니다](#searching-a-status-in-filter-keeps-the-services-of-a-listed-status) | 성공 |
| [상태마다 하나씩 있는 서비스를 비정상과 다른 것으로 필터 기반 조회하면 정상과 등록 해제 서비스만 반환됩니다](#searching-a-status-not-equals-filter-drops-the-services-of-that-status) | 성공 |
| [상태마다 하나씩 있는 서비스를 비정상, 등록 해제 목록에 들지 않은 것으로 필터 기반 조회하면 정상 서비스만 반환됩니다](#searching-a-status-not-in-filter-drops-the-services-of-a-listed-status) | 성공 |
| [서비스 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답합니다](#searching-omitting-the-page-size-answers-ten-services-and-a-next-page) | 성공 |
| [모니터 역할이 필터 없이 조회하면 superadmin 과 같은 응답을 받습니다. 이 검색은 읽기 연산이라 모니터 역할이 전역 역할 검사를 통과합니다](#searching-the-monitor-role-counts-every-service-as-the-superadmin-does) | 성공 |
| [서비스 둘 중 하나가 엔드포인트를 가질 때 superadmin 이 필터 없이 조회하면, 둘 다 한 번씩 집계됩니다](#searching-the-superadmin-counts-every-service-laid-once) | 성공 |
| [superadmin 이 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-services) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 미리 저장한 서비스 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |

### admin_search

<a id="searching-a-group-filter-narrows-the-answer-to-the-services-of-that-group"></a>

#### [a-group-filter-narrows-the-answer-to-the-services-of-that-group](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

그룹이 다른 서비스 둘 중 한 그룹으로 필터 기반 조회하면, 응답에는 그 그룹의 서비스만 남습니다

Given

- 그룹이 다른 서비스 둘과, superadmin 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-1: agent 그룹에 정상 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 manager 그룹으로 필터 기반 조회합니다

Then

- 골라낸 그룹의 서비스 하나만 남습니다
  - items.id: 골라낸 서비스와 같다
  - items.service_group = ['manager']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-equals-filter-keeps-the-services-of-that-status"></a>

#### [a-status-equals-filter-keeps-the-services-of-that-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

상태마다 하나씩 있는 서비스를 비정상과 같은 것으로 필터 기반 조회하면 비정상 서비스만 반환됩니다

Given

- 정상, 비정상, 등록 해제 상태의 서비스 하나씩과, superadmin 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록합니다
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 상태가 비정상 인 것으로 필터 기반 조회합니다

Then

- 비정상 상태의 서비스만 반환됩니다
  - items.id: 그 상태로 미리 저장한 서비스와 같다
  - items.instance_id = ['unhealthy-1']
  - items.status = [<ServiceCatalogStatus.UNHEALTHY: 'unhealthy'>]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-in-filter-keeps-the-services-of-a-listed-status"></a>

#### [a-status-in-filter-keeps-the-services-of-a-listed-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

상태마다 하나씩 있는 서비스를 비정상, 등록 해제 목록에 든 것으로 필터 기반 조회하면 비정상과 등록 해제 서비스만 반환됩니다

Given

- 정상, 비정상, 등록 해제 상태의 서비스 하나씩과, superadmin 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록합니다
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 상태가 비정상, 등록 해제 중 하나인 것으로 필터 기반 조회합니다

Then

- 비정상, 등록 해제 상태의 서비스만 반환됩니다
  - items.id: 그 상태로 미리 저장한 서비스와 같다
  - items.instance_id = ['deregistered-1', 'unhealthy-1']
  - items.status = [<ServiceCatalogStatus.DEREGISTERED: 'deregistered'>, <ServiceCatalogStatus.UNHEALTHY: 'unhealthy'>]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-not-equals-filter-drops-the-services-of-that-status"></a>

#### [a-status-not-equals-filter-drops-the-services-of-that-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

상태마다 하나씩 있는 서비스를 비정상과 다른 것으로 필터 기반 조회하면 정상과 등록 해제 서비스만 반환됩니다

Given

- 정상, 비정상, 등록 해제 상태의 서비스 하나씩과, superadmin 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록합니다
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 상태가 비정상 이 아닌 것으로 필터 기반 조회합니다

Then

- 정상, 등록 해제 상태의 서비스만 반환됩니다
  - items.id: 그 상태로 미리 저장한 서비스와 같다
  - items.instance_id = ['deregistered-1', 'healthy-1']
  - items.status = [<ServiceCatalogStatus.DEREGISTERED: 'deregistered'>, <ServiceCatalogStatus.HEALTHY: 'healthy'>]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-not-in-filter-drops-the-services-of-a-listed-status"></a>

#### [a-status-not-in-filter-drops-the-services-of-a-listed-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

상태마다 하나씩 있는 서비스를 비정상, 등록 해제 목록에 들지 않은 것으로 필터 기반 조회하면 정상 서비스만 반환됩니다

Given

- 정상, 비정상, 등록 해제 상태의 서비스 하나씩과, superadmin 한 명
  - 서비스 healthy-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 unhealthy-1: manager 그룹에 비정상 상태로 등록합니다
  - 서비스 deregistered-1: manager 그룹에 등록 해제 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 상태가 비정상, 등록 해제 중 어느 것도 아닌 것으로 필터 기반 조회합니다

Then

- 정상 상태의 서비스만 반환됩니다
  - items.id: 그 상태로 미리 저장한 서비스와 같다
  - items.instance_id = ['healthy-1']
  - items.status = [<ServiceCatalogStatus.HEALTHY: 'healthy'>]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-services-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-services-and-a-next-page](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

서비스 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답합니다

Given

- 서비스 11개와, superadmin 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖습니다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-2: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-3: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-4: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-5: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-6: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-7: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-8: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-9: manager 그룹에 정상 상태로 등록합니다
  - 서비스 other-10: manager 그룹에 정상 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 기본 크기의 첫 페이지가 반환됩니다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-the-monitor-role-counts-every-service-as-the-superadmin-does"></a>

#### [the-monitor-role-counts-every-service-as-the-superadmin-does](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

모니터 역할이 필터 없이 조회하면 superadmin 과 같은 응답을 받습니다. 이 검색은 읽기 연산이라 모니터 역할이 전역 역할 검사를 통과합니다

Given

- 서비스 2개와, 모니터 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖습니다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 서비스가 모두 한 번씩 집계되어 전체가 반환됩니다
  - items.instance_id = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 저장한 서비스와 같다
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
  - items[1].id: 미리 저장한 서비스와 같다
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

<a id="searching-the-superadmin-counts-every-service-laid-once"></a>

#### [the-superadmin-counts-every-service-laid-once](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

서비스 둘 중 하나가 엔드포인트를 가질 때 superadmin 이 필터 없이 조회하면, 둘 다 한 번씩 집계됩니다

Given

- 서비스 2개와, superadmin 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖습니다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 서비스가 모두 한 번씩 집계되어 전체가 반환됩니다
  - items.instance_id = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 저장한 서비스와 같다
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
  - items[1].id: 미리 저장한 서비스와 같다
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

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-services"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-services](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

superadmin 이 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부됩니다

Given

- 서비스 2개와, 일반 사용자 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖습니다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/service_catalog/test_reading.py): pass

superadmin 이 미리 저장한 서비스 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다

Given

- 서비스 2개와, superadmin 한 명
  - 서비스 wanted-1: manager 그룹에 정상 상태로 등록합니다
  - 서비스 wanted-1: http://127.0.0.1:8080 엔드포인트 하나를 갖습니다
  - 서비스 other-1: manager 그룹에 정상 상태로 등록합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ServiceCatalogAdapter.batch_load_by_ids: user-1이 미리 저장한 서비스 2개와 없는 id 하나를 한 번에 조회합니다

Then

- 요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다
  - len(items) = 3
  - items[0].entity_id: 미리 저장한 서비스와 같다
  - items[0].id: 미리 저장한 서비스와 같다
  - items[0].service_group = 'manager'
  - items[0].instance_id = 'wanted-1'
  - items[0].display_name = 'wanted-1'
  - items[0].version = '26.9.0'
  - items[0].labels = {}
  - items[0].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[0].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[0].registered_at: 이 실행이 쓴 시각
  - items[0].last_heartbeat: 이 실행이 쓴 시각
  - items[0].config_hash = ''
  - items[1].entity_id: 미리 저장한 서비스와 같다
  - items[1].id: 미리 저장한 서비스와 같다
  - items[1].service_group = 'manager'
  - items[1].instance_id = 'other-1'
  - items[1].display_name = 'other-1'
  - items[1].version = '26.9.0'
  - items[1].labels = {}
  - items[1].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[1].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[1].registered_at: 이 실행이 쓴 시각
  - items[1].last_heartbeat: 이 실행이 쓴 시각
  - items[1].config_hash = ''
  - items[2] = None

