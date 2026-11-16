## fair_share

[배경](/src/ai/backend/manager/api/adapters/fair_share/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/fair_share/adapter.py)

시나리오: 완성

- 직접 구현 (15)
  - atomic_bulk_upsert_domain: 성공 있음 1 · 거부 있음 2 (scope)
  - atomic_bulk_upsert_project: 성공 있음 1 · 거부 있음 2 (scope)
  - atomic_bulk_upsert_user: 성공 있음 1 · 거부 있음 2 (scope)
  - get_domain: 성공 있음 1 · 거부 있음 2 (scope)
  - get_project: 성공 있음 1 · 거부 있음 2 (scope)
  - get_user: 성공 있음 1 · 거부 있음 2 (scope)
  - search_domain: 성공 있음 1 · 거부 있음 1 (global_scope)
  - search_project: 성공 있음 1 · 거부 있음 1 (global_scope)
  - search_rg_domain: 성공 있음 1 · 거부 있음 2 (scope)
  - search_rg_project: 성공 있음 1 · 거부 있음 2 (scope)
  - search_rg_user: 성공 있음 1 · 거부 있음 2 (scope)
  - search_user: 성공 있음 1 · 거부 있음 1 (global_scope)
  - upsert_domain: 성공 있음 1 · 거부 있음 2 (scope)
  - upsert_project: 성공 있음 1 · 거부 있음 2 (scope)
  - upsert_user: 성공 있음 1 · 거부 있음 2 (scope)

**atomic_bulk_upsert_domain**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 도메인 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다](#atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다](#atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights) | 거부 |
| [그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다](#atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights) | 거부 |

**atomic_bulk_upsert_project**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 프로젝트 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다](#atomic_bulk_upserting_project-the-superadmin-sets-several-project-weights-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다](#atomic_bulk_upserting_project-a-user-granted-nothing-may-not-set-several-project-weights) | 거부 |
| [그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 프로젝트 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다](#atomic_bulk_upserting_project-a-user-granted-update-on-the-group-may-not-set-several-project-weights) | 거부 |

**atomic_bulk_upsert_user**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 사용자 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다](#atomic_bulk_upserting_user-the-superadmin-sets-several-user-weights-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 사용자 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다](#atomic_bulk_upserting_user-a-user-granted-nothing-may-not-set-several-user-weights) | 거부 |
| [그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 사용자 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다](#atomic_bulk_upserting_user-a-user-granted-update-on-the-group-may-not-set-several-user-weights) | 거부 |

**get_domain**

| 시나리오 | 판정 |
|---|---|
| [그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 도메인의 fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다](#getting-a-user-granted-fair-share-read-on-the-group-reads-a-domain-fair-share) | 성공 |
| [그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 도메인의 fair share 를 조회하면 권한 부족으로 거부됩니다](#getting-a-user-granted-only-fair-share-update-may-not-read-a-domain-fair-share) | 거부 |
| [fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 도메인의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다](#getting-reading-a-domain-fair-share-in-an-unknown-resource-group-fails) | 거부 |

**get_project**

| 시나리오 | 판정 |
|---|---|
| [그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 프로젝트의 fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다](#getting-a-user-granted-fair-share-read-on-the-group-reads-a-project-fair-share) | 성공 |
| [그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 프로젝트의 fair share 를 조회하면 권한 부족으로 거부됩니다](#getting-a-user-granted-only-fair-share-update-may-not-read-a-project-fair-share) | 거부 |
| [fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 프로젝트의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다](#getting-reading-a-project-fair-share-in-an-unknown-resource-group-fails) | 거부 |

**get_user**

| 시나리오 | 판정 |
|---|---|
| [그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 사용자의 fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다](#getting-a-user-granted-fair-share-read-on-the-group-reads-a-user-fair-share) | 성공 |
| [그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 사용자의 fair share 를 조회하면 권한 부족으로 거부됩니다](#getting-a-user-granted-only-fair-share-update-may-not-read-a-user-fair-share) | 거부 |
| [fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 사용자의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다](#getting-reading-a-user-fair-share-in-an-unknown-resource-group-fails) | 거부 |

**search_domain**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 막는 검색입니다. superadmin 이 도메인 fair share 를 한 리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다](#searching-the-superadmin-searches-the-domain-fair-shares-of-one-group) | 성공 |
| [일반 사용자가 리소스 그룹을 가리지 않고 도메인 fair share 를 검색하면 역할 부족으로 거부됩니다](#searching-a-regular-user-may-not-search-domain-fair-shares-across-groups) | 거부 |

**search_project**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 막는 검색입니다. superadmin 이 프로젝트 fair share 를 한 리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다](#searching-the-superadmin-searches-the-project-fair-shares-of-one-group) | 성공 |
| [일반 사용자가 리소스 그룹을 가리지 않고 프로젝트 fair share 를 검색하면 역할 부족으로 거부됩니다](#searching-a-regular-user-may-not-search-project-fair-shares-across-groups) | 거부 |

**search_rg_domain**

| 시나리오 | 판정 |
|---|---|
| [그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 도메인 fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 활성인 것 둘이 세어지고 둘째 것이 옵니다. 다른 리소스 그룹에만 기록한 도메인은 이 그룹의 기본값으로 오고 비활성 도메인은 오지 않습니다](#scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-domain-fair-shares) | 성공 |
| [그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 도메인 fair share 를 검색하면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-only-fair-share-update-may-not-search-domain-fair-shares) | 거부 |
| [fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 도메인 fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다](#scoped_searching-searching-domain-fair-shares-in-an-unknown-resource-group-fails) | 거부 |

**search_rg_project**

| 시나리오 | 판정 |
|---|---|
| [그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 프로젝트 fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 활성인 것 둘이 세어지고 둘째 것이 옵니다. 다른 도메인의 프로젝트와 비활성 프로젝트는 오지 않습니다](#scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-project-fair-shares) | 성공 |
| [그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 프로젝트 fair share 를 검색하면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-only-fair-share-update-may-not-search-project-fair-shares) | 거부 |
| [fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 프로젝트 fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다](#scoped_searching-searching-project-fair-shares-in-an-unknown-resource-group-fails) | 거부 |

**search_rg_user**

| 시나리오 | 판정 |
|---|---|
| [그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 사용자 fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 활성인 것 둘이 세어지고 둘째 것이 옵니다. 다른 프로젝트의 멤버와 비활성 멤버는 오지 않습니다](#scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-user-fair-shares) | 성공 |
| [그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 사용자 fair share 를 검색하면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-only-fair-share-update-may-not-search-user-fair-shares) | 거부 |
| [fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 사용자 fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다](#scoped_searching-searching-user-fair-shares-in-an-unknown-resource-group-fails) | 거부 |

**search_user**

| 시나리오 | 판정 |
|---|---|
| [전역 역할이 막는 검색입니다. superadmin 이 사용자 fair share 를 한 리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다](#searching-the-superadmin-searches-the-user-fair-shares-of-one-group) | 성공 |
| [일반 사용자가 리소스 그룹을 가리지 않고 사용자 fair share 를 검색하면 역할 부족으로 거부됩니다](#searching-a-regular-user-may-not-search-user-fair-shares-across-groups) | 거부 |

**upsert_domain**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 그룹 안 도메인의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다](#upserting-the-superadmin-sets-a-domain-weight) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부됩니다](#upserting-a-user-granted-nothing-may-not-set-a-domain-weight) | 거부 |
| [그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다](#upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight) | 거부 |

**upsert_project**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 그룹 안 프로젝트의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다](#upserting_project-the-superadmin-sets-a-project-weight) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트의 가중치를 정하려 하면 권한 부족으로 거부됩니다](#upserting_project-a-user-granted-nothing-may-not-set-a-project-weight) | 거부 |
| [그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 프로젝트의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다](#upserting_project-a-user-granted-update-on-the-group-may-not-set-a-project-weight) | 거부 |

**upsert_user**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 그룹 안 사용자의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다](#upserting_user-the-superadmin-sets-a-user-weight) | 성공 |
| [아무 권한도 받지 않은 사용자가 사용자의 가중치를 정하려 하면 권한 부족으로 거부됩니다](#upserting_user-a-user-granted-nothing-may-not-set-a-user-weight) | 거부 |
| [그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 사용자의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다](#upserting_user-a-user-granted-update-on-the-group-may-not-set-a-user-weight) | 거부 |

### atomic_bulk_upsert_domain

<a id="atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once"></a>

#### [the-superadmin-sets-several-domain-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py): pass

superadmin 이 도메인 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다

Given

- 리소스 그룹 하나와 도메인 2개, 그리고 superadmin 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.atomic_bulk_upsert_domain: user-1 이 resource-group-1 안 도메인 2개의 가중치를 한 번에 정합니다

Then

- 도메인 수만큼 정했다는 개수가 옵니다
  - upserted_count = 2

<a id="atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-domain-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py): pass

아무 권한도 받지 않은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 도메인 2개, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.atomic_bulk_upsert_domain: user-1 이 resource-group-1 안 도메인 2개의 가중치를 한 번에 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-domain-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py): pass

그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다

Given

- 리소스 그룹 하나와 도메인 2개, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- FairShareAdapter.atomic_bulk_upsert_domain: user-1 이 resource-group-1 안 도메인 2개의 가중치를 한 번에 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### atomic_bulk_upsert_project

<a id="atomic_bulk_upserting_project-the-superadmin-sets-several-project-weights-at-once"></a>

#### [the-superadmin-sets-several-project-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_project.py): pass

superadmin 이 프로젝트 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다

Given

- 리소스 그룹 하나와 프로젝트 2개, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.atomic_bulk_upsert_project: user-1 이 resource-group-1 안 프로젝트 2개의 가중치를 한 번에 정합니다

Then

- 프로젝트 수만큼 정했다는 개수가 옵니다
  - upserted_count = 2

<a id="atomic_bulk_upserting_project-a-user-granted-nothing-may-not-set-several-project-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-project-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_project.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 프로젝트 2개, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.atomic_bulk_upsert_project: user-1 이 resource-group-1 안 프로젝트 2개의 가중치를 한 번에 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="atomic_bulk_upserting_project-a-user-granted-update-on-the-group-may-not-set-several-project-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-project-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_project.py): pass

그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 프로젝트 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다

Given

- 리소스 그룹 하나와 프로젝트 2개, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- FairShareAdapter.atomic_bulk_upsert_project: user-1 이 resource-group-1 안 프로젝트 2개의 가중치를 한 번에 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### atomic_bulk_upsert_user

<a id="atomic_bulk_upserting_user-the-superadmin-sets-several-user-weights-at-once"></a>

#### [the-superadmin-sets-several-user-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_user.py): pass

superadmin 이 사용자 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 사용자 2명, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다

When

- FairShareAdapter.atomic_bulk_upsert_user: user-3 이 resource-group-1 안 사용자 2개의 가중치를 한 번에 정합니다

Then

- 사용자 수만큼 정했다는 개수가 옵니다
  - upserted_count = 2

<a id="atomic_bulk_upserting_user-a-user-granted-nothing-may-not-set-several-user-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-user-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_user.py): pass

아무 권한도 받지 않은 사용자가 사용자 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 사용자 2명, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
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
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다

When

- FairShareAdapter.atomic_bulk_upsert_user: user-3 이 resource-group-1 안 사용자 2개의 가중치를 한 번에 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="atomic_bulk_upserting_user-a-user-granted-update-on-the-group-may-not-set-several-user-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-user-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_user.py): pass

그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 사용자 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 사용자 2명, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
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
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-3: 역할 group-role-1 보유

When

- FairShareAdapter.atomic_bulk_upsert_user: user-3 이 resource-group-1 안 사용자 2개의 가중치를 한 번에 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_domain

<a id="getting-a-user-granted-fair-share-read-on-the-group-reads-a-domain-fair-share"></a>

#### [a-user-granted-fair-share-read-on-the-group-reads-a-domain-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 도메인의 fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다

Given

- 리소스 그룹 하나와 그 그룹에 fair share 를 기록한 도메인 하나, 그리고 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_domain: user-1 이 resource-group-1 안 도메인 home-1의 fair share 를 조회합니다

Then

- 그 도메인의 fair share 기록이 시드한 값 그대로 옵니다
  - id = 'resource-group-1:home-1'
  - resource_group_name = 'resource-group-1'
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 14
  - spec.lookback_days = 56
  - spec.decay_unit_days = 2
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('0.5')
  - calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - calculation_snapshot.normalized_usage = Decimal('0.25')
  - calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="getting-a-user-granted-only-fair-share-update-may-not-read-a-domain-fair-share"></a>

#### [a-user-granted-only-fair-share-update-may-not-read-a-domain-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 도메인의 fair share 를 조회하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 그 그룹에 fair share 를 기록한 도메인 하나, 그리고 그 그룹 범위의 fair share UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share UPDATE 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_domain: user-1 이 resource-group-1 안 도메인 home-1의 fair share 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="getting-reading-a-domain-fair-share-in-an-unknown-resource-group-fails"></a>

#### [reading-a-domain-fair-share-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 도메인의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다

Given

- 리소스 그룹 하나와 그 그룹에 fair share 를 기록한 도메인 하나, 그리고 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_domain: user-1 이 없는 리소스 그룹 이름으로 도메인 home-1의 fair share 를 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### get_project

<a id="getting-a-user-granted-fair-share-read-on-the-group-reads-a-project-fair-share"></a>

#### [a-user-granted-fair-share-read-on-the-group-reads-a-project-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 프로젝트의 fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다

Given

- 리소스 그룹 하나와 그 그룹에 fair share 를 기록한 프로젝트 하나, 그리고 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_project: user-1 이 resource-group-1 안 프로젝트 team-1의 fair share 를 조회합니다

Then

- 그 프로젝트의 fair share 기록이 시드한 값 그대로 옵니다
  - id: 리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값와 같다
  - resource_group_name = 'resource-group-1'
  - project_id: 시드한 프로젝트의 id 와 같다
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 14
  - spec.lookback_days = 56
  - spec.decay_unit_days = 2
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('0.5')
  - calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - calculation_snapshot.normalized_usage = Decimal('0.25')
  - calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="getting-a-user-granted-only-fair-share-update-may-not-read-a-project-fair-share"></a>

#### [a-user-granted-only-fair-share-update-may-not-read-a-project-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 프로젝트의 fair share 를 조회하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 그 그룹에 fair share 를 기록한 프로젝트 하나, 그리고 그 그룹 범위의 fair share UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share UPDATE 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_project: user-1 이 resource-group-1 안 프로젝트 team-1의 fair share 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="getting-reading-a-project-fair-share-in-an-unknown-resource-group-fails"></a>

#### [reading-a-project-fair-share-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 프로젝트의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다

Given

- 리소스 그룹 하나와 그 그룹에 fair share 를 기록한 프로젝트 하나, 그리고 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_project: user-1 이 없는 리소스 그룹 이름으로 프로젝트 team-1의 fair share 를 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### get_user

<a id="getting-a-user-granted-fair-share-read-on-the-group-reads-a-user-fair-share"></a>

#### [a-user-granted-fair-share-read-on-the-group-reads-a-user-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 사용자의 fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 그 그룹에 fair share 를 기록한 프로젝트 멤버 하나, 그리고 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 member-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 member-1: 프로젝트 team-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 member-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_user: user-1 이 resource-group-1 안 사용자 member-1의 fair share 를 조회합니다

Then

- 그 멤버의 fair share 기록이 시드한 값 그대로 옵니다
  - id: 리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값와 같다
  - resource_group_name = 'resource-group-1'
  - user_uuid: 시드한 사용자의 id 와 같다
  - project_id: 시드한 프로젝트의 id 와 같다
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 14
  - spec.lookback_days = 56
  - spec.decay_unit_days = 2
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('0.5')
  - calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - calculation_snapshot.normalized_usage = Decimal('0.25')
  - calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="getting-a-user-granted-only-fair-share-update-may-not-read-a-user-fair-share"></a>

#### [a-user-granted-only-fair-share-update-may-not-read-a-user-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 사용자의 fair share 를 조회하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 그 그룹에 fair share 를 기록한 프로젝트 멤버 하나, 그리고 그 그룹 범위의 fair share UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 member-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 member-1: 프로젝트 team-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share UPDATE 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 member-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_user: user-1 이 resource-group-1 안 사용자 member-1의 fair share 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="getting-reading-a-user-fair-share-in-an-unknown-resource-group-fails"></a>

#### [reading-a-user-fair-share-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 사용자의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 그 그룹에 fair share 를 기록한 프로젝트 멤버 하나, 그리고 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 member-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 member-1: 프로젝트 team-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 member-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.get_user: user-1 이 없는 리소스 그룹 이름으로 사용자 member-1의 fair share 를 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### search_domain

<a id="searching-the-superadmin-searches-the-domain-fair-shares-of-one-group"></a>

#### [the-superadmin-searches-the-domain-fair-shares-of-one-group](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

전역 역할이 막는 검색입니다. superadmin 이 도메인 fair share 를 한 리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다

Given

- 리소스 그룹 하나에 도메인 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 도메인의 fair share 를 기록했고, superadmin 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 resource-group-1: 도메인 other-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 elsewhere-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_domain: user-1 이 리소스 그룹 resource-group-1 필터, 도메인 이름 오름차순으로 앞에서 한 건을 조회합니다

Then

- 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 도메인의 기록 하나만 옵니다
  - total_count = 2
  - items.count = 1
  - items[0].id = 'resource-group-1:home-1'
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-regular-user-may-not-search-domain-fair-shares-across-groups"></a>

#### [a-regular-user-may-not-search-domain-fair-shares-across-groups](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

일반 사용자가 리소스 그룹을 가리지 않고 도메인 fair share 를 검색하면 역할 부족으로 거부됩니다

Given

- 리소스 그룹 하나에 도메인 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 도메인의 fair share 를 기록했고, 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 resource-group-1: 도메인 other-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 elsewhere-1: 도메인 home-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_domain: user-1 이 리소스 그룹 resource-group-1 필터, 도메인 이름 오름차순으로 앞에서 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### search_project

<a id="searching-the-superadmin-searches-the-project-fair-shares-of-one-group"></a>

#### [the-superadmin-searches-the-project-fair-shares-of-one-group](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

전역 역할이 막는 검색입니다. superadmin 이 프로젝트 fair share 를 한 리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다

Given

- 리소스 그룹 하나에 프로젝트 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 프로젝트의 fair share 를 기록했고, superadmin 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 alpha-1
  - 프로젝트 beta-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: 프로젝트 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 resource-group-1: 프로젝트 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 elsewhere-1: 프로젝트 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_project: user-1 이 리소스 그룹 resource-group-1 필터, 프로젝트 이름 오름차순으로 앞에서 한 건을 조회합니다

Then

- 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 프로젝트의 기록 하나만 옵니다
  - total_count = 2
  - items.count = 1
  - items[0].id: 리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값와 같다
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].project_id: 시드한 프로젝트의 id 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-regular-user-may-not-search-project-fair-shares-across-groups"></a>

#### [a-regular-user-may-not-search-project-fair-shares-across-groups](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

일반 사용자가 리소스 그룹을 가리지 않고 프로젝트 fair share 를 검색하면 역할 부족으로 거부됩니다

Given

- 리소스 그룹 하나에 프로젝트 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 프로젝트의 fair share 를 기록했고, 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 alpha-1
  - 프로젝트 beta-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: 프로젝트 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 resource-group-1: 프로젝트 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 elsewhere-1: 프로젝트 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_project: user-1 이 리소스 그룹 resource-group-1 필터, 프로젝트 이름 오름차순으로 앞에서 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### search_rg_domain

<a id="scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-domain-fair-shares"></a>

#### [a-user-granted-fair-share-read-on-the-group-searches-its-domain-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 도메인 fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 활성인 것 둘이 세어지고 둘째 것이 옵니다. 다른 리소스 그룹에만 기록한 도메인은 이 그룹의 기본값으로 오고 비활성 도메인은 오지 않습니다

Given

- 리소스 그룹 둘, 활성 도메인 둘과 비활성 도메인 하나, 그 가운데 한 활성 도메인의 fair share 는 다른 리소스 그룹에만 기록했고, 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 도메인 dormant-1: 비활성 상태
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 elsewhere-1: 도메인 other-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_domain: user-1 이 resource-group-1 안에서 도메인을 활성 필터, 도메인 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 활성 도메인 둘이 세어지고, 둘째 도메인은 다른 리소스 그룹의 기록이 아니라 이 그룹의 기본값으로 옵니다
  - total_count = 2
  - items.count = 1
  - items[0].id = 'resource-group-1:other-1'
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].domain_name = 'other-1'
  - items[0].spec.weight = Decimal('1.0')
  - items[0].spec.uses_default = True
  - items[0].spec.half_life_days = 7
  - items[0].spec.lookback_days = 28
  - items[0].spec.decay_unit_days = 1
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('1')
  - items[0].calculation_snapshot.total_decayed_usage = []
  - items[0].calculation_snapshot.normalized_usage = Decimal('0')
  - items[0].calculation_snapshot.lookback_start: 건너뜀: 요청한 날짜에 따라 달라집니다
  - items[0].calculation_snapshot.lookback_end: 건너뜀: 요청한 날짜에 따라 달라집니다
  - items[0].calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-only-fair-share-update-may-not-search-domain-fair-shares"></a>

#### [a-user-granted-only-fair-share-update-may-not-search-domain-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 도메인 fair share 를 검색하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 둘, 활성 도메인 둘과 비활성 도메인 하나, 그 가운데 한 활성 도메인의 fair share 는 다른 리소스 그룹에만 기록했고, 그 그룹 범위의 fair share UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 도메인 dormant-1: 비활성 상태
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share UPDATE 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 elsewhere-1: 도메인 other-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_domain: user-1 이 resource-group-1 안에서 도메인을 활성 필터, 도메인 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="scoped_searching-searching-domain-fair-shares-in-an-unknown-resource-group-fails"></a>

#### [searching-domain-fair-shares-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 도메인 fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다

Given

- 리소스 그룹 둘, 활성 도메인 둘과 비활성 도메인 하나, 그 가운데 한 활성 도메인의 fair share 는 다른 리소스 그룹에만 기록했고, 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 도메인 dormant-1: 비활성 상태
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 elsewhere-1: 도메인 other-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_domain: user-1 이 없는 리소스 그룹 이름으로 도메인을 활성 필터, 도메인 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### search_rg_project

<a id="scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-project-fair-shares"></a>

#### [a-user-granted-fair-share-read-on-the-group-searches-its-project-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 프로젝트 fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 활성인 것 둘이 세어지고 둘째 것이 옵니다. 다른 도메인의 프로젝트와 비활성 프로젝트는 오지 않습니다

Given

- 리소스 그룹 하나, 도메인 안 활성 프로젝트 둘과 비활성 프로젝트 하나, 다른 도메인의 프로젝트 하나, 활성 프로젝트 하나의 fair share 를 그 그룹에 기록했고, 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 far-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 alpha-1
  - 프로젝트 beta-1
  - 프로젝트 dormant-1: 비활성 상태
  - 프로젝트 aside-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_project: user-1 이 resource-group-1 안에서 도메인 home-1의 프로젝트를 활성 필터, 프로젝트 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 그 도메인의 활성 프로젝트 둘이 세어지고, 둘째 쪽에 fair share 를 기록한 프로젝트가 시드한 값 그대로 옵니다
  - total_count = 2
  - items.count = 1
  - items[0].id: 리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값와 같다
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].project_id: 시드한 프로젝트의 id 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-only-fair-share-update-may-not-search-project-fair-shares"></a>

#### [a-user-granted-only-fair-share-update-may-not-search-project-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 프로젝트 fair share 를 검색하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나, 도메인 안 활성 프로젝트 둘과 비활성 프로젝트 하나, 다른 도메인의 프로젝트 하나, 활성 프로젝트 하나의 fair share 를 그 그룹에 기록했고, 그 그룹 범위의 fair share UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 far-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 alpha-1
  - 프로젝트 beta-1
  - 프로젝트 dormant-1: 비활성 상태
  - 프로젝트 aside-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share UPDATE 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_project: user-1 이 resource-group-1 안에서 도메인 home-1의 프로젝트를 활성 필터, 프로젝트 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="scoped_searching-searching-project-fair-shares-in-an-unknown-resource-group-fails"></a>

#### [searching-project-fair-shares-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 프로젝트 fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다

Given

- 리소스 그룹 하나, 도메인 안 활성 프로젝트 둘과 비활성 프로젝트 하나, 다른 도메인의 프로젝트 하나, 활성 프로젝트 하나의 fair share 를 그 그룹에 기록했고, 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 far-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 alpha-1
  - 프로젝트 beta-1
  - 프로젝트 dormant-1: 비활성 상태
  - 프로젝트 aside-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_project: user-1 이 없는 리소스 그룹 이름으로 도메인 home-1의 프로젝트를 활성 필터, 프로젝트 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### search_rg_user

<a id="scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-user-fair-shares"></a>

#### [a-user-granted-fair-share-read-on-the-group-searches-its-user-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 사용자 fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 활성인 것 둘이 세어지고 둘째 것이 옵니다. 다른 프로젝트의 멤버와 비활성 멤버는 오지 않습니다

Given

- 리소스 그룹 하나, 프로젝트의 활성 멤버 둘과 비활성 멤버 하나, 다른 프로젝트의 멤버 하나, 활성 멤버 하나의 fair share 를 그 그룹에 기록했고, 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 aside-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 alpha-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 alpha-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 beta-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 beta-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 dormant-1: 상태 inactive, 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 dormant-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 outsider-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 outsider-1: 프로젝트 aside-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-5: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_user: user-1 이 resource-group-1 안에서 프로젝트 team-1의 멤버를 활성 필터, 사용자 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 그 프로젝트의 활성 멤버 둘이 세어지고, 둘째 쪽에 fair share 를 기록한 멤버가 시드한 값 그대로 옵니다
  - total_count = 2
  - items.count = 1
  - items[0].id: 리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값와 같다
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].user_uuid: 시드한 사용자의 id 와 같다
  - items[0].project_id: 시드한 프로젝트의 id 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-only-fair-share-update-may-not-search-user-fair-shares"></a>

#### [a-user-granted-only-fair-share-update-may-not-search-user-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 사용자 fair share 를 검색하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나, 프로젝트의 활성 멤버 둘과 비활성 멤버 하나, 다른 프로젝트의 멤버 하나, 활성 멤버 하나의 fair share 를 그 그룹에 기록했고, 그 그룹 범위의 fair share UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 aside-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 alpha-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 alpha-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 beta-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 beta-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 dormant-1: 상태 inactive, 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 dormant-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 outsider-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 outsider-1: 프로젝트 aside-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-5: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share UPDATE 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_user: user-1 이 resource-group-1 안에서 프로젝트 team-1의 멤버를 활성 필터, 사용자 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="scoped_searching-searching-user-fair-shares-in-an-unknown-resource-group-fails"></a>

#### [searching-user-fair-shares-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 사용자 fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다

Given

- 리소스 그룹 하나, 프로젝트의 활성 멤버 둘과 비활성 멤버 하나, 다른 프로젝트의 멤버 하나, 활성 멤버 하나의 fair share 를 그 그룹에 기록했고, 그 그룹 범위의 fair share READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 aside-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 alpha-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 alpha-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 beta-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 beta-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 dormant-1: 상태 inactive, 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 dormant-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-4: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 outsider-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 outsider-1: 프로젝트 aside-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-5: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 fair share READ 역할을 받은 사용자 준비
    - 역할 fair-share-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 fair-share-role-1: global 전체에 READ 허용
    - 일반 사용자 user-1: 역할 fair-share-role-1 보유
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_rg_user: user-1 이 없는 리소스 그룹 이름으로 프로젝트 team-1의 멤버를 활성 필터, 사용자 이름 오름차순으로 한 건을 건너뛰고 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### search_user

<a id="searching-the-superadmin-searches-the-user-fair-shares-of-one-group"></a>

#### [the-superadmin-searches-the-user-fair-shares-of-one-group](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

전역 역할이 막는 검색입니다. superadmin 이 사용자 fair share 를 한 리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다

Given

- 리소스 그룹 하나에 프로젝트 멤버 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 멤버의 fair share 를 기록했고, superadmin 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 alpha-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 alpha-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 beta-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 beta-1: 프로젝트 team-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 elsewhere-1: 프로젝트 team-1 안 사용자 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_user: user-1 이 리소스 그룹 resource-group-1 필터, 사용자 이름 오름차순으로 앞에서 한 건을 조회합니다

Then

- 그 그룹의 기록 둘이 세어지고 사용자 이름 순으로 앞선 멤버의 기록 하나만 옵니다
  - total_count = 2
  - items.count = 1
  - items[0].id: 리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값와 같다
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].user_uuid: 시드한 사용자의 id 와 같다
  - items[0].project_id: 시드한 프로젝트의 id 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-regular-user-may-not-search-user-fair-shares-across-groups"></a>

#### [a-regular-user-may-not-search-user-fair-shares-across-groups](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

일반 사용자가 리소스 그룹을 가리지 않고 사용자 fair share 를 검색하면 역할 부족으로 거부됩니다

Given

- 리소스 그룹 하나에 프로젝트 멤버 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 멤버의 fair share 를 기록했고, 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 멤버 목록에 오른 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 alpha-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 alpha-1: 프로젝트 team-1 멤버 목록에 추가됨
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 beta-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 일반 사용자 beta-1: 프로젝트 team-1 멤버 목록에 추가됨
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 resource-group-1: 프로젝트 team-1 안 사용자 beta-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5
  - 자원 그룹 elsewhere-1: 프로젝트 team-1 안 사용자 alpha-1의 fair share: 가중치 2.5, 반감기 14일, 돌아볼 기간 56일, 감쇠 단위 2일, 계산된 factor 0.5

When

- FairShareAdapter.search_user: user-1 이 리소스 그룹 resource-group-1 필터, 사용자 이름 오름차순으로 앞에서 한 건을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### upsert_domain

<a id="upserting-the-superadmin-sets-a-domain-weight"></a>

#### [the-superadmin-sets-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py): pass

superadmin 이 그룹 안 도메인의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다

Given

- 리소스 그룹 하나와 도메인 1개, 그리고 superadmin 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.upsert_domain: user-1 이 resource-group-1 안 home-1의 가중치를 정합니다

Then

- 정한 가중치를 담은 기록이 오고, 나머지 설정은 그룹 기본값입니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - resource_group_name = 'resource-group-1'
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: 건너뜀: 쓴 날짜에 따라 달라집니다
  - calculation_snapshot.lookback_end: 건너뜀: 쓴 날짜에 따라 달라집니다
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting-a-user-granted-nothing-may-not-set-a-domain-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py): pass

아무 권한도 받지 않은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 도메인 1개, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.upsert_domain: user-1 이 resource-group-1 안 home-1의 가중치를 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py): pass

그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다

Given

- 리소스 그룹 하나와 도메인 1개, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- FairShareAdapter.upsert_domain: user-1 이 resource-group-1 안 home-1의 가중치를 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### upsert_project

<a id="upserting_project-the-superadmin-sets-a-project-weight"></a>

#### [the-superadmin-sets-a-project-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_project.py): pass

superadmin 이 그룹 안 프로젝트의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다

Given

- 리소스 그룹 하나와 프로젝트 1개, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.upsert_project: user-1 이 resource-group-1 안 첫 프로젝트의 가중치를 정합니다

Then

- 정한 가중치를 담은 기록이 오고, 나머지 설정은 그룹 기본값입니다
  - id: 그룹 이름과 미리 만든 프로젝트의 id 를 잇은 값와 같다
  - resource_group_name = 'resource-group-1'
  - project_id: 미리 만든 프로젝트의 id 와 같다
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: 건너뜀: 쓴 날짜에 따라 달라집니다
  - calculation_snapshot.lookback_end: 건너뜀: 쓴 날짜에 따라 달라집니다
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting_project-a-user-granted-nothing-may-not-set-a-project-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-project-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_project.py): pass

아무 권한도 받지 않은 사용자가 프로젝트의 가중치를 정하려 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 프로젝트 1개, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- FairShareAdapter.upsert_project: user-1 이 resource-group-1 안 첫 프로젝트의 가중치를 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="upserting_project-a-user-granted-update-on-the-group-may-not-set-a-project-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-project-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_project.py): pass

그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 프로젝트의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다

Given

- 리소스 그룹 하나와 프로젝트 1개, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- FairShareAdapter.upsert_project: user-1 이 resource-group-1 안 첫 프로젝트의 가중치를 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### upsert_user

<a id="upserting_user-the-superadmin-sets-a-user-weight"></a>

#### [the-superadmin-sets-a-user-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_user.py): pass

superadmin 이 그룹 안 사용자의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 사용자 1명, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다

When

- FairShareAdapter.upsert_user: user-2 이 resource-group-1 안 첫 사용자의 가중치를 정합니다

Then

- 정한 가중치를 담은 기록이 오고, 나머지 설정은 그룹 기본값입니다
  - id: 그룹 이름, 미리 만든 사용자와 프로젝트의 id 를 잇은 값와 같다
  - resource_group_name = 'resource-group-1'
  - user_uuid: 미리 만든 사용자의 id 와 같다
  - project_id: 미리 만든 프로젝트의 id 와 같다
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: 건너뜀: 쓴 날짜에 따라 달라집니다
  - calculation_snapshot.lookback_end: 건너뜀: 쓴 날짜에 따라 달라집니다
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting_user-a-user-granted-nothing-may-not-set-a-user-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-user-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_user.py): pass

아무 권한도 받지 않은 사용자가 사용자의 가중치를 정하려 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 사용자 1명, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다

When

- FairShareAdapter.upsert_user: user-2 이 resource-group-1 안 첫 사용자의 가중치를 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="upserting_user-a-user-granted-update-on-the-group-may-not-set-a-user-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-user-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_user.py): pass

그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 사용자의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다

Given

- 리소스 그룹 하나와 프로젝트 하나, 사용자 1명, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 group-role-1 보유

When

- FairShareAdapter.upsert_user: user-2 이 resource-group-1 안 첫 사용자의 가중치를 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

