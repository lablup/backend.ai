## resource_usage

[어댑터](/src/ai/backend/manager/api/adapters/resource_usage/adapter.py)

시나리오: 완성

- ops 구성 (14)
  - admin_search_domain: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_project: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_user: 대표 성공 ✓ · 대표 거부 ✓
  - domain_search_domain: 대표 성공 ✓ · 대표 거부 ✓
  - domain_search_project: 대표 성공 ✓ · 대표 거부 ✓
  - domain_search_user: 대표 성공 ✓ · 대표 거부 ✓
  - gql_admin_search_domain: 대표 성공 ✓ · 대표 거부 ✓
  - gql_admin_search_project: 대표 성공 ✓ · 대표 거부 ✓
  - gql_admin_search_user: 대표 성공 ✓ · 대표 거부 ✓
  - gql_search_domain_scoped: 대표 성공 ✓ · 대표 거부 ✓
  - gql_search_project_scoped: 대표 성공 ✓ · 대표 거부 ✓
  - gql_search_project_unscoped: 대표 성공 ✓ · 대표 거부 ✓
  - gql_search_user_scoped: 대표 성공 ✓ · 대표 거부 ✓
  - gql_search_user_unscoped: 대표 성공 ✓ · 대표 거부 ✓

**admin_search_domain**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다](#searching-admin-search-domain-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 도메인 사용량 버킷을 훑으면 거부됩니다](#searching-admin-search-domain-is-refused-to-a-caller-without-permission) | 거부 |

**admin_search_project**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다](#searching-admin-search-project-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 프로젝트 사용량 버킷을 훑으면 거부됩니다](#searching-admin-search-project-is-refused-to-a-caller-without-permission) | 거부 |

**admin_search_user**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다](#searching-admin-search-user-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 사용자 사용량 버킷을 훑으면 거부됩니다](#searching-admin-search-user-is-refused-to-a-caller-without-permission) | 거부 |

**domain_search_domain**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹에서 읽을 수 있는 슈퍼관리자가 버킷이 없는 자리에서 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다](#searching-domain-search-domain-returns-an-empty-page) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인 사용량 버킷을 훑으면 거부됩니다](#searching-domain-search-domain-is-refused-to-a-caller-without-permission) | 거부 |

**domain_search_project**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹에서 읽을 수 있는 슈퍼관리자가 버킷이 없는 자리에서 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다](#searching-domain-search-project-returns-an-empty-page) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 사용량 버킷을 훑으면 거부됩니다](#searching-domain-search-project-is-refused-to-a-caller-without-permission) | 거부 |

**domain_search_user**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹에서 읽을 수 있는 슈퍼관리자가 버킷이 없는 자리에서 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다](#searching-domain-search-user-returns-an-empty-page) | 성공 |
| [아무 권한도 받지 않은 사용자가 사용자 사용량 버킷을 훑으면 거부됩니다](#searching-domain-search-user-is-refused-to-a-caller-without-permission) | 거부 |

**gql_admin_search_domain**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-admin-search-domain-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 GQL 경로로 도메인 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-admin-search-domain-is-refused-to-a-caller-without-permission) | 거부 |

**gql_admin_search_project**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-admin-search-project-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 GQL 경로로 프로젝트 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-admin-search-project-is-refused-to-a-caller-without-permission) | 거부 |

**gql_admin_search_user**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-admin-search-user-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 GQL 경로로 사용자 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-admin-search-user-is-refused-to-a-caller-without-permission) | 거부 |

**gql_search_domain_scoped**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-search-domain-scoped-returns-an-empty-page) | 성공 |
| [아무 권한도 받지 않은 사용자가 GQL 경로로 도메인 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-search-domain-scoped-is-refused-to-a-caller-without-permission) | 거부 |

**gql_search_project_scoped**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-search-project-scoped-returns-an-empty-page) | 성공 |
| [아무 권한도 받지 않은 사용자가 GQL 경로로 프로젝트 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-search-project-scoped-is-refused-to-a-caller-without-permission) | 거부 |

**gql_search_project_unscoped**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-search-project-unscoped-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 GQL 경로로 프로젝트 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-search-project-unscoped-is-refused-to-a-caller-without-permission) | 거부 |

**gql_search_user_scoped**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-search-user-scoped-returns-an-empty-page) | 성공 |
| [아무 권한도 받지 않은 사용자가 GQL 경로로 사용자 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-search-user-scoped-is-refused-to-a-caller-without-permission) | 거부 |

**gql_search_user_unscoped**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다](#gql_searching-gql-search-user-unscoped-returns-an-empty-page) | 성공 |
| [슈퍼관리자가 아닌 사용자가 GQL 경로로 사용자 사용량 버킷을 훑으면 거부됩니다](#gql_searching-gql-search-user-unscoped-is-refused-to-a-caller-without-permission) | 거부 |

### admin_search_domain

<a id="searching-admin-search-domain-returns-an-empty-page"></a>

#### [admin-search-domain-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.admin_search_domain: user-2 이 리소스 그룹 resource-group-1 의 도메인 사용량 버킷을 범위 없이 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-admin-search-domain-is-refused-to-a-caller-without-permission"></a>

#### [admin-search-domain-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 도메인 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.admin_search_domain: user-2 이 리소스 그룹 resource-group-1 의 도메인 사용량 버킷을 범위 없이 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_project

<a id="searching-admin-search-project-returns-an-empty-page"></a>

#### [admin-search-project-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.admin_search_project: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 범위 없이 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-admin-search-project-is-refused-to-a-caller-without-permission"></a>

#### [admin-search-project-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 프로젝트 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.admin_search_project: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 범위 없이 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_user

<a id="searching-admin-search-user-returns-an-empty-page"></a>

#### [admin-search-user-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.admin_search_user: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 범위 없이 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-admin-search-user-is-refused-to-a-caller-without-permission"></a>

#### [admin-search-user-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 사용자 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.admin_search_user: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 범위 없이 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### domain_search_domain

<a id="searching-domain-search-domain-returns-an-empty-page"></a>

#### [domain-search-domain-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

리소스 그룹에서 읽을 수 있는 슈퍼관리자가 버킷이 없는 자리에서 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.domain_search_domain: user-2 이 리소스 그룹 resource-group-1 을 범위로 도메인 사용량 버킷을 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-domain-search-domain-is-refused-to-a-caller-without-permission"></a>

#### [domain-search-domain-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

아무 권한도 받지 않은 사용자가 도메인 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.domain_search_domain: user-2 이 리소스 그룹 resource-group-1 을 범위로 도메인 사용량 버킷을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### domain_search_project

<a id="searching-domain-search-project-returns-an-empty-page"></a>

#### [domain-search-project-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

리소스 그룹에서 읽을 수 있는 슈퍼관리자가 버킷이 없는 자리에서 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.domain_search_project: user-2 이 리소스 그룹 resource-group-1 을 범위로 프로젝트 사용량 버킷을 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-domain-search-project-is-refused-to-a-caller-without-permission"></a>

#### [domain-search-project-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.domain_search_project: user-2 이 리소스 그룹 resource-group-1 을 범위로 프로젝트 사용량 버킷을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### domain_search_user

<a id="searching-domain-search-user-returns-an-empty-page"></a>

#### [domain-search-user-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

리소스 그룹에서 읽을 수 있는 슈퍼관리자가 버킷이 없는 자리에서 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.domain_search_user: user-2 이 리소스 그룹 resource-group-1 을 범위로 사용자 사용량 버킷을 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-domain-search-user-is-refused-to-a-caller-without-permission"></a>

#### [domain-search-user-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

아무 권한도 받지 않은 사용자가 사용자 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.domain_search_user: user-2 이 리소스 그룹 resource-group-1 을 범위로 사용자 사용량 버킷을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### gql_admin_search_domain

<a id="gql_searching-gql-admin-search-domain-returns-an-empty-page"></a>

#### [gql-admin-search-domain-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_admin_search_domain: user-2 이 리소스 그룹 resource-group-1 의 도메인 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-admin-search-domain-is-refused-to-a-caller-without-permission"></a>

#### [gql-admin-search-domain-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 아닌 사용자가 GQL 경로로 도메인 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_admin_search_domain: user-2 이 리소스 그룹 resource-group-1 의 도메인 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### gql_admin_search_project

<a id="gql_searching-gql-admin-search-project-returns-an-empty-page"></a>

#### [gql-admin-search-project-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_admin_search_project: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-admin-search-project-is-refused-to-a-caller-without-permission"></a>

#### [gql-admin-search-project-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 아닌 사용자가 GQL 경로로 프로젝트 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_admin_search_project: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### gql_admin_search_user

<a id="gql_searching-gql-admin-search-user-returns-an-empty-page"></a>

#### [gql-admin-search-user-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_admin_search_user: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-admin-search-user-is-refused-to-a-caller-without-permission"></a>

#### [gql-admin-search-user-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 아닌 사용자가 GQL 경로로 사용자 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_admin_search_user: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### gql_search_domain_scoped

<a id="gql_searching-gql-search-domain-scoped-returns-an-empty-page"></a>

#### [gql-search-domain-scoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 도메인 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_domain_scoped: user-2 이 리소스 그룹 resource-group-1 의 도메인 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-domain-scoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-domain-scoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

아무 권한도 받지 않은 사용자가 GQL 경로로 도메인 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_domain_scoped: user-2 이 리소스 그룹 resource-group-1 의 도메인 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### gql_search_project_scoped

<a id="gql_searching-gql-search-project-scoped-returns-an-empty-page"></a>

#### [gql-search-project-scoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_project_scoped: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-project-scoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-project-scoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

아무 권한도 받지 않은 사용자가 GQL 경로로 프로젝트 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_project_scoped: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### gql_search_project_unscoped

<a id="gql_searching-gql-search-project-unscoped-returns-an-empty-page"></a>

#### [gql-search-project-unscoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 프로젝트 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_project_unscoped: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-project-unscoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-project-unscoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 아닌 사용자가 GQL 경로로 프로젝트 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_project_unscoped: user-2 이 리소스 그룹 resource-group-1 의 프로젝트 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### gql_search_user_scoped

<a id="gql_searching-gql-search-user-scoped-returns-an-empty-page"></a>

#### [gql-search-user-scoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_user_scoped: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-user-scoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-user-scoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

아무 권한도 받지 않은 사용자가 GQL 경로로 사용자 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_user_scoped: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### gql_search_user_unscoped

<a id="gql_searching-gql-search-user-unscoped-returns-an-empty-page"></a>

#### [gql-search-user-unscoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 사용자 사용량 버킷을 훑으면 빈 페이지가 옵니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_user_unscoped: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 GQL 경로로 훑습니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-user-unscoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-user-unscoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

슈퍼관리자가 아닌 사용자가 GQL 경로로 사용자 사용량 버킷을 훑으면 거부됩니다

Given

- 사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, 아무 권한도 받지 않은 일반 사용자
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지

When

- ResourceUsageAdapter.gql_search_user_unscoped: user-2 이 리소스 그룹 resource-group-1 의 사용자 사용량 버킷을 GQL 경로로 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

