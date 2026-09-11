## prometheus_query_preset_category

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/prometheus_query_preset_category/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/prometheus_query_preset_category/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-name-another-category-already-holds-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

이미 어떤 분류가 쓰고 있는 이름으로 슈퍼관리자가 다시 만들면, 이름이 겹친다는 이유로 거부된다. 저장소의 유일 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다

Given

- 이미 있는 분류 하나와, superadmin 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 이미 있는 category-1으로 다시 만듦

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [a-user-who-is-not-the-superadmin-may-not-create-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 분류를 만들려 하면, 역할로 막힌다

Given

- 분류가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 cpu으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [creating-a-category-with-a-description-carries-it-on-the-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

슈퍼관리자가 이름과 설명을 함께 주고 만들면, 준 값이 그대로 실린 노드가 온다

Given

- 분류가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 cpu으로 만듦

Then

- 만든 분류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu'
  - description = '새로 만든 분류'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [creating-a-category-with-a-name-alone-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

슈퍼관리자가 이름만 주고 분류를 만들면, 설명이 비어 있는 노드 전체가 답으로 온다

Given

- 분류가 하나도 없고, superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 cpu으로 만듦

Then

- 만든 분류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'cpu'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py) — pass

엔티티 권한 집행을 꺼도 분류 만들기는 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 분류가 하나도 없고, user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.create — user-1이 cpu으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### loading

#### [loading-an-empty-id-list-answers-an-empty-list](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_loading.py) — pass

분류가 있어도 빈 id 목록으로 읽으면, 빈 답이 온다

Given

- 분류 1개와, user 한 명
  - 분류 wanted-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - answer = []

#### [loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_loading.py) — pass

분류 둘과 없는 id 하나를 섞어 한 번에 읽으면, 있는 둘은 노드로 없는 하나는 빈 자리로 오고 순서가 준 순서와 같다

Given

- 분류 2개와, user 한 명
  - 분류 wanted-1
  - 분류 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.batch_load_by_ids — user-1이 심은 2개의 id와 없는 id 하나를 한 번에 조회

Then

- 준 순서대로, 없는 id 자리는 비어서 온다
  - len = 3
  - [0]: 1번째로 준 id의 분류 전체와 같다
  - [1]: 2번째로 준 id의 분류 전체와 같다
  - [2] = None

### reading

#### [a-call-carrying-no-user-may-not-read-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py) — pass

분류 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 인증으로 거부된다

Given

- 이미 있는 분류 하나, 부를 사람 없음
  - 분류 category-1

When

- PrometheusQueryPresetCategoryAdapter.get — 아무도 아닌 채로 category-1을 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-reads-a-category-by-id](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py) — pass

분류 하나가 있고 아무 권한도 받지 않은 사용자가 id로 조회하면, 그 분류 전체가 답으로 온다

Given

- 이미 있는 분류 하나와, user 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.get — user-1이 category-1로 조회

Then

- 심은 분류 전체가 온다
  - id: 심은 분류와 같다
  - name = 'category-1'
  - description = '심어둔 분류'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-id-nothing-answers-to-is-not-found-for-anyone](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. 읽기는 인증만 보므로 권한 문이 먼저 막지 않는다

Given

- 이미 있는 분류 하나와, user 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.get — user-1이 아무것도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### retiring

#### [a-user-granted-nothing-may-not-remove-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_retiring.py) — pass

같은 분류가 있고 아무 권한도 받지 않은 사용자가 지우면, 권한 부족으로 거부된다

Given

- 이미 있는 분류 하나와, user 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 category-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_retiring.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다

Given

- 이미 있는 분류 하나와, superadmin 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 아무것도 갖지 않은 id를 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-removes-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_retiring.py) — pass

분류 하나가 있고 슈퍼관리자가 지우면, 지운 id를 실은 답이 온다

Given

- 이미 있는 분류 하나와, superadmin 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 category-1를 지움

Then

- 지운 분류를 답한다
  - id: 심은 분류와 같다

#### [turning-enforcement-off-lets-a-user-remove-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_retiring.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 분류를 지운다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 이미 있는 분류 하나와, user 한 명
  - 분류 category-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.delete — user-1이 category-1를 지움

Then

- 지운 분류를 답한다
  - id: 심은 분류와 같다

### searching

#### [a-call-carrying-no-user-may-not-search-categories](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

분류 하나가 있고 사용자 컨텍스트 없이 훑으면, 인증으로 거부된다

Given

- 이미 있는 분류 하나, 부를 사람 없음
  - 분류 category-1

When

- PrometheusQueryPresetCategoryAdapter.search — 아무도 아닌 채로 전체 조회

Then

- 거부된다
  - 거부: UserNotFound

#### [a-user-granted-nothing-counts-every-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

분류 둘이 있고 아무 권한도 받지 않은 사용자가 필터 없이 훑으면, 둘을 모두 센다

Given

- 분류 2개와, user 한 명
  - 분류 wanted-1
  - 분류 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.search — user-1이 필터 없이 전체 조회

Then

- 심은 분류가 모두, 그리고 그것만 세어진다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-name-keeps-only-the-category-of-that-name](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

이름이 다른 분류 셋이 있을 때 이름으로 걸러 훑으면, 그 이름의 것만 남는다

Given

- 분류 3개와, user 한 명
  - 분류 wanted-1
  - 분류 other-1
  - 분류 other-2
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.search — user-1이 이름 wanted-1으로 걸러 조회

Then

- 이름으로 고른 하나만 세어진다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-and-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py) — pass

분류 열하나가 있을 때 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 분류 11개와, user 한 명
  - 분류 wanted-1
  - 분류 other-1
  - 분류 other-2
  - 분류 other-3
  - 분류 other-4
  - 분류 other-5
  - 분류 other-6
  - 분류 other-7
  - 분류 other-8
  - 분류 other-9
  - 분류 other-10
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- PrometheusQueryPresetCategoryAdapter.search — user-1이 필터 없이 전체 조회

Then

- 한 쪽만 오고 다음 쪽이 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

