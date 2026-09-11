## prometheus_query_preset_category

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/prometheus_query_preset_category/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/prometheus_query_preset_category/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-name-another-category-already-holds-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

이미 다른 카테고리가 사용 중인 이름으로 슈퍼관리자가 다시 생성하면, 이름 중복으로 거부된다. 저장소의 유일 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다

Given

- 이미 있는 카테고리 하나와, superadmin 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 이미 있는 이름 category-1(으)로 다시 생성

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [a-user-who-is-not-the-superadmin-may-not-create-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 카테고리를 생성하려 하면, 역할 부족으로 거부된다

Given

- 카테고리가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 이름 cpu(으)로 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [creating-a-category-with-a-description-carries-it-on-the-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

슈퍼관리자가 이름과 설명을 함께 지정해 생성하면, 지정한 값이 그대로 담긴 노드가 반환된다

Given

- 카테고리가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 이름 cpu(으)로 생성

Then

- 생성한 카테고리 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu'
  - description = '새로 만든 카테고리'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [creating-a-category-with-a-name-alone-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

슈퍼관리자가 이름만 지정해 카테고리를 생성하면, 설명이 비어 있는 노드 전체가 반환된다

Given

- 카테고리가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 이름 cpu(으)로 생성

Then

- 생성한 카테고리 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

권한 검사를 꺼도 카테고리 생성은 여전히 거부된다. 생성은 권한 그래프가 아니라 역할로 보호되기 때문이다

Given

- 카테고리가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 이름 cpu(으)로 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### loading

#### [loading-an-empty-id-list-answers-an-empty-list](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_loading.py) — pass

카테고리가 있어도 빈 id 목록으로 조회하면, 빈 응답이 반환된다

Given

- 카테고리 1개와, user 한 명
  - 카테고리 wanted-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 응답이 반환된다
  - answer = []

#### [loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_loading.py) — pass

카테고리 둘과 없는 id 하나를 섞어 한 번에 조회하면, 있는 둘은 노드로 없는 하나는 빈 항목으로 반환되고 순서가 요청한 순서와 같다

Given

- 카테고리 2개와, user 한 명
  - 카테고리 wanted-1
  - 카테고리 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 카테고리 2개의 id와 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로, 없는 id 자리는 비어서 반환된다
  - len = 3
  - [0]: 1번째로 요청한 id의 카테고리 전체와 같다
  - [1]: 2번째로 요청한 id의 카테고리 전체와 같다
  - [2] = None

### purging

#### [a-user-granted-nothing-may-not-remove-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py) — pass

같은 카테고리가 있고 아무 권한도 없는 사용자가 삭제하면, 권한 부족으로 거부된다

Given

- 이미 있는 카테고리 하나와, user 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 category-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다

Given

- 이미 있는 카테고리 하나와, superadmin 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-removes-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py) — pass

카테고리 하나가 있고 슈퍼관리자가 삭제하면, 삭제한 id를 담은 응답이 반환된다

Given

- 이미 있는 카테고리 하나와, superadmin 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 category-1 삭제

Then

- 삭제한 카테고리를 응답한다
  - id: 미리 만들어 둔 카테고리와 같다

#### [turning-enforcement-off-lets-a-user-remove-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 카테고리를 삭제할 수 있다. 삭제는 역할이 아니라 권한 그래프로 보호되기 때문이다

Given

- 이미 있는 카테고리 하나와, user 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 category-1 삭제

Then

- 삭제한 카테고리를 응답한다
  - id: 미리 만들어 둔 카테고리와 같다

### reading

#### [a-call-carrying-no-user-may-not-read-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py) — pass

카테고리 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 인증 실패로 거부된다

Given

- 이미 있는 카테고리 하나, 호출자 없음
  - 카테고리 category-1

When

- PrometheusQueryPresetCategoryAdapter.get — 사용자 컨텍스트 없이 category-1 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-reads-a-category-by-id](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py) — pass

카테고리 하나가 있고 아무 권한도 없는 사용자가 id로 조회하면, 그 카테고리 전체가 반환된다

Given

- 이미 있는 카테고리 하나와, user 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.get — user-1이 category-1(으)로 조회

Then

- 미리 만들어 둔 카테고리 전체가 반환된다
  - id: 미리 만들어 둔 카테고리와 같다
  - name = 'category-1'
  - description = '미리 만들어 둔 카테고리'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-id-nothing-answers-to-is-not-found-for-anyone](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. 조회는 인증만 확인하므로 권한 검사가 먼저 막지 않는다

Given

- 이미 있는 카테고리 하나와, user 한 명
  - 카테고리 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.get — user-1이 존재하지 않는 id(으)로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### searching

#### [a-call-carrying-no-user-may-not-search-categories](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

카테고리 하나가 있고 사용자 컨텍스트 없이 검색하면, 인증 실패로 거부된다

Given

- 이미 있는 카테고리 하나, 호출자 없음
  - 카테고리 category-1

When

- PrometheusQueryPresetCategoryAdapter.search — 사용자 컨텍스트 없이 전체 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-counts-every-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

카테고리 둘이 있고 아무 권한도 없는 사용자가 필터 없이 검색하면, 둘 다 집계된다

Given

- 카테고리 2개와, user 한 명
  - 카테고리 wanted-1
  - 카테고리 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.search — user-1이 필터 없이 전체 조회

Then

- 미리 만들어 둔 카테고리가 모두, 그리고 그것만 집계된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-name-keeps-only-the-category-of-that-name](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

이름이 다른 카테고리 셋이 있을 때 이름 필터로 검색하면, 그 이름의 카테고리만 반환된다

Given

- 카테고리 3개와, user 한 명
  - 카테고리 wanted-1
  - 카테고리 other-1
  - 카테고리 other-2
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.search — user-1이 wanted-1 이름 필터로 조회

Then

- 이름 필터에 맞는 하나만 집계된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-and-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

카테고리 11개가 있을 때 크기 없이 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다

Given

- 카테고리 11개와, user 한 명
  - 카테고리 wanted-1
  - 카테고리 other-1
  - 카테고리 other-2
  - 카테고리 other-3
  - 카테고리 other-4
  - 카테고리 other-5
  - 카테고리 other-6
  - 카테고리 other-7
  - 카테고리 other-8
  - 카테고리 other-9
  - 카테고리 other-10
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.search — user-1이 필터 없이 전체 조회

Then

- 한 페이지만 반환되고 다음 페이지가 있다고 응답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

