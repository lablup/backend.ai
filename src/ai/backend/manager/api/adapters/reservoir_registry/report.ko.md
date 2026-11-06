## reservoir_registry

[배경](/src/ai/backend/manager/api/adapters/reservoir_registry/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/reservoir_registry/adapter.py)

시나리오: 완성

- ops 구성 (1)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (8)
  - create: 성공 있음 1 · 거부 있음 1 (global_scope)
  - get: 성공 있음 1 · 거부 있음 1 (single_entity)
  - get_many: 성공 있음 1 · 거부 있음 1 (global_scope)
  - partial_bulk_purge: 성공 있음 2 · 거부 있음 1 (partial_bulk)
  - partial_bulk_update: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - purge: 성공 있음 1 · 거부 있음 1 (single_entity)
  - search: 성공 있음 1 · 거부 있음 1 (global_scope)
  - update: 성공 있음 1 · 거부 있음 1 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [Reservoir 레지스트리 조회 권한을 받은 사용자가 미리 저장한 레지스트리 둘을 한 번에 조회하면, 둘은 요청한 순서대로 반환됩니다](#reading-a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 레지스트리 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#reading-a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 Reservoir 레지스트리를 만들면 만든 레지스트리 전체가 반환됩니다. 이 호출은 전역 역할을 검사합니다](#creating-the-superadmin-creates-a-reservoir-registry) | 성공 |
| [superadmin 이 아닌 사용자가 Reservoir 레지스트리를 만들려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-reservoir-registry) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [Reservoir 레지스트리 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 레지스트리 전체가 반환됩니다](#reading-a-user-granted-read-gets-a-registry) | 성공 |
| [아무 권한도 받지 않은 사용자가 레지스트리를 조회하려 하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-get-a-registry) | 거부 |

**get_many**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 레지스트리 둘을 id 로 한 번에 조회하면 둘 다 반환됩니다. 이 호출은 전역 역할을 검사합니다](#reading-the-superadmin-reads-several-reservoir-registries-by-id) | 성공 |
| [superadmin 이 아닌 사용자가 레지스트리를 id 로 한 번에 조회하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#reading-a-user-who-is-not-the-superadmin-may-not-read-several-registries) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [Reservoir 레지스트리 purge 권한을 받은 사용자가 여럿을 한 번에 purge 하면, 모두의 id 가 처리된 목록에 오고 실패한 것은 없습니다](#partial_bulk_purging-a-user-granted-purge-purges-several-registries) | 성공 |
| [superadmin 이 Reservoir 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 purge 하면, 둘의 id 는 처리된 목록에, 존재하지 않는 id 는 대상이 없다는 이유로 실패 목록에 옵니다. superadmin 은 검사를 모두 통과하므로 대상 없음이 그대로 드러납니다](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | 성공 |
| [아무 권한도 받지 않은 사용자가 Reservoir 레지스트리 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [Reservoir 레지스트리 수정 권한을 받은 사용자가 여럿의 엔드포인트를 한 번에 변경하면, 모두 새 엔드포인트로 오고 실패한 것은 없습니다](#partial_bulk_editing-a-user-granted-update-edits-several-registries) | 성공 |
| [아무 권한도 받지 않은 사용자가 Reservoir 레지스트리 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [Reservoir 레지스트리 purge 권한을 받은 사용자가 purge 하면, purge 한 Reservoir 레지스트리의 id 가 옵니다](#purging-a-user-granted-purge-purges-a-registry) | 성공 |
| [아무 권한도 받지 않은 사용자가 purge 하려 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-nothing-may-not-purge-a-registry) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 Reservoir 레지스트리를 검색해 한 쪽을 요청하면 미리 저장한 레지스트리 둘 가운데 하나만 오고, 전체 개수는 둘입니다. 이 호출은 전역 역할을 검사합니다](#searching-the-superadmin-searching-reservoir-registries-gets-one-page) | 성공 |
| [superadmin 이 아닌 사용자가 Reservoir 레지스트리를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [Reservoir 레지스트리 수정 권한을 받은 사용자가 엔드포인트를 변경하면, 그 Reservoir 레지스트리가 새 엔드포인트로 옵니다](#editing-a-user-granted-update-edits-a-registry) | 성공 |
| [아무 권한도 받지 않은 사용자가 엔드포인트를 변경하려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-a-registry) | 거부 |

### batch_load_by_ids

<a id="reading-a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order"></a>

#### [a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

Reservoir 레지스트리 조회 권한을 받은 사용자가 미리 저장한 레지스트리 둘을 한 번에 조회하면, 둘은 요청한 순서대로 반환됩니다

Given

- Reservoir 레지스트리 2개와, 레지스트리에 READ 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 registry-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 registry-keeper-1: artifact_registry 전체에 READ 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.batch_load_by_ids: user-1이 미리 저장한 레지스트리 둘을 id 로 한 번에 조회합니다

Then

- 미리 저장한 레지스트리는 요청한 순서대로 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 레지스트리의 id 와 같다
  - [0].entity_id: 미리 저장한 레지스트리의 id 와 같다
  - [0].name = 'registry-1'
  - [0].endpoint = 'https://reservoir.example.com'
  - [0].access_key = 'access-key'
  - [0].secret_key = 'secret-key'
  - [0].api_version = 'v1'
  - [1].id: 미리 저장한 레지스트리의 id 와 같다
  - [1].entity_id: 미리 저장한 레지스트리의 id 와 같다
  - [1].name = 'registry-2'
  - [1].endpoint = 'https://reservoir.example.com'
  - [1].access_key = 'access-key'
  - [1].secret_key = 'secret-key'
  - [1].api_version = 'v1'

<a id="reading-a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

아무 권한도 받지 않은 사용자가 레지스트리 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.batch_load_by_ids: user-1이 미리 저장한 레지스트리 둘을 id 로 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-a-reservoir-registry"></a>

#### [the-superadmin-creates-a-reservoir-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_creating.py): pass

superadmin 이 Reservoir 레지스트리를 만들면 만든 레지스트리 전체가 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.create: user-1이 Reservoir 레지스트리를 만듭니다

Then

- 만든 레지스트리 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'made-reservoir'
  - endpoint = 'https://made.reservoir.example.com'
  - access_key = 'made-access-key'
  - secret_key = 'made-secret-key'
  - api_version = 'v1'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-reservoir-registry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-reservoir-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_creating.py): pass

superadmin 이 아닌 사용자가 Reservoir 레지스트리를 만들려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.create: user-1이 Reservoir 레지스트리를 만듭니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### get

<a id="reading-a-user-granted-read-gets-a-registry"></a>

#### [a-user-granted-read-gets-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

Reservoir 레지스트리 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 레지스트리 전체가 반환됩니다

Given

- Reservoir 레지스트리 하나와, 레지스트리에 READ 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 registry-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 registry-keeper-1: artifact_registry 전체에 READ 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.get: user-1이 registry-1을 조회합니다

Then

- 미리 저장한 레지스트리 전체가 반환됩니다
  - id: 미리 저장한 레지스트리의 id 와 같다
  - entity_id: 미리 저장한 레지스트리의 id 와 같다
  - name = 'registry-1'
  - endpoint = 'https://reservoir.example.com'
  - access_key = 'access-key'
  - secret_key = 'secret-key'
  - api_version = 'v1'

<a id="reading-a-user-granted-nothing-may-not-get-a-registry"></a>

#### [a-user-granted-nothing-may-not-get-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

아무 권한도 받지 않은 사용자가 레지스트리를 조회하려 하면 권한 부족으로 거부됩니다

Given

- Reservoir 레지스트리 하나와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.get: user-1이 registry-1을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_many

<a id="reading-the-superadmin-reads-several-reservoir-registries-by-id"></a>

#### [the-superadmin-reads-several-reservoir-registries-by-id](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

superadmin 이 레지스트리 둘을 id 로 한 번에 조회하면 둘 다 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- Reservoir 레지스트리 2개와, superadmin 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.get_many: user-1이 미리 저장한 레지스트리 둘을 id 로 한 번에 조회합니다

Then

- 미리 저장한 레지스트리가 모두 반환됩니다
  - items: 미리 저장한 레지스트리와 같다

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-several-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

superadmin 이 아닌 사용자가 레지스트리를 id 로 한 번에 조회하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.get_many: user-1이 미리 저장한 레지스트리 둘을 id 로 한 번에 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-registries"></a>

#### [a-user-granted-purge-purges-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py): pass

Reservoir 레지스트리 purge 권한을 받은 사용자가 여럿을 한 번에 purge 하면, 모두의 id 가 처리된 목록에 오고 실패한 것은 없습니다

Given

- Reservoir 레지스트리 2개와, 레지스트리에 HARD_DELETE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 registry-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 registry-keeper-1: artifact_registry 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.partial_bulk_purge: user-1이 Reservoir 레지스트리 2개를 한 번에 purge 합니다

Then

- 대상 레지스트리의 id 가 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 레지스트리의 id 와 같다
  - successes[1].id: 미리 저장한 레지스트리의 id 와 같다
  - failed = []

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py): pass

superadmin 이 Reservoir 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 purge 하면, 둘의 id 는 처리된 목록에, 존재하지 않는 id 는 대상이 없다는 이유로 실패 목록에 옵니다. superadmin 은 검사를 모두 통과하므로 대상 없음이 그대로 드러납니다

Given

- Reservoir 레지스트리 2개와, superadmin 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.partial_bulk_purge: user-1이 Reservoir 레지스트리 2개와 존재하지 않는 id 하나를 한 번에 purge 합니다

Then

- 대상 레지스트리의 id 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 레지스트리의 id 와 같다
  - successes[1].id: 미리 저장한 레지스트리의 id 와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries"></a>

#### [a-user-granted-nothing-purges-none-of-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 Reservoir 레지스트리 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.partial_bulk_purge: user-1이 Reservoir 레지스트리 2개를 한 번에 purge 합니다

Then

- 처리된 레지스트리 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 레지스트리의 id 와 같다
  - 거부: failed[0]: Insufficient permission
  - failed[1].id: 대상 레지스트리의 id 와 같다
  - 거부: failed[1]: Insufficient permission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-update-edits-several-registries"></a>

#### [a-user-granted-update-edits-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_editing.py): pass

Reservoir 레지스트리 수정 권한을 받은 사용자가 여럿의 엔드포인트를 한 번에 변경하면, 모두 새 엔드포인트로 오고 실패한 것은 없습니다

Given

- Reservoir 레지스트리 2개와, 레지스트리에 UPDATE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 registry-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 registry-keeper-1: artifact_registry 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.partial_bulk_update: user-1이 Reservoir 레지스트리 2개의 엔드포인트를 한 번에 변경합니다

Then

- 대상 레지스트리가 모두 새 엔드포인트로 반환되고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].id: 미리 저장한 레지스트리의 id 와 같다
  - successes[0].entity_id: 미리 저장한 레지스트리의 id 와 같다
  - successes[0].name = 'registry-1'
  - successes[0].endpoint = 'https://storage.example.com'
  - successes[0].access_key = 'access-key'
  - successes[0].secret_key = '*****'
  - successes[0].api_version = 'v1'
  - successes[1].id: 미리 저장한 레지스트리의 id 와 같다
  - successes[1].entity_id: 미리 저장한 레지스트리의 id 와 같다
  - successes[1].name = 'registry-2'
  - successes[1].endpoint = 'https://storage.example.com'
  - successes[1].access_key = 'access-key'
  - successes[1].secret_key = '*****'
  - successes[1].api_version = 'v1'

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries"></a>

#### [a-user-granted-nothing-edits-none-of-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 Reservoir 레지스트리 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.partial_bulk_update: user-1이 Reservoir 레지스트리 2개의 엔드포인트를 한 번에 변경합니다

Then

- 처리된 레지스트리 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 레지스트리의 id 와 같다
  - 거부: failed[0]: Insufficient permission
  - failed[1].id: 대상 레지스트리의 id 와 같다
  - 거부: failed[1]: Insufficient permission

### purge

<a id="purging-a-user-granted-purge-purges-a-registry"></a>

#### [a-user-granted-purge-purges-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_purging.py): pass

Reservoir 레지스트리 purge 권한을 받은 사용자가 purge 하면, purge 한 Reservoir 레지스트리의 id 가 옵니다

Given

- Reservoir 레지스트리 하나와, 레지스트리에 HARD_DELETE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 registry-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 registry-keeper-1: artifact_registry 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.purge: user-1이 registry-1을 purge 합니다

Then

- purge 한 레지스트리의 id 가 반환됩니다
  - id: 미리 저장한 레지스트리의 id 와 같다
  - entity_id: 미리 저장한 레지스트리의 id 와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-registry"></a>

#### [a-user-granted-nothing-may-not-purge-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_purging.py): pass

아무 권한도 받지 않은 사용자가 purge 하려 하면 권한 부족으로 거부됩니다

Given

- Reservoir 레지스트리 하나와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.purge: user-1이 registry-1을 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search

<a id="searching-the-superadmin-searching-reservoir-registries-gets-one-page"></a>

#### [the-superadmin-searching-reservoir-registries-gets-one-page](/tests/scenario/bai_scenario/manager/reservoir_registry/test_searching.py): pass

superadmin 이 Reservoir 레지스트리를 검색해 한 쪽을 요청하면 미리 저장한 레지스트리 둘 가운데 하나만 오고, 전체 개수는 둘입니다. 이 호출은 전역 역할을 검사합니다

Given

- Reservoir 레지스트리 2개와, superadmin 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.search: user-1이 Reservoir 레지스트리를 검색해 한 쪽을 요청합니다

Then

- 미리 저장한 레지스트리 둘 가운데 하나만 한 쪽에 오고, 남은 하나는 다음 쪽에 있습니다
  - length = 1
  - items: 미리 저장한 레지스트리 가운데 하나
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_searching.py): pass

superadmin 이 아닌 사용자가 Reservoir 레지스트리를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.search: user-1이 Reservoir 레지스트리를 검색해 한 쪽을 요청합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### update

<a id="editing-a-user-granted-update-edits-a-registry"></a>

#### [a-user-granted-update-edits-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_editing.py): pass

Reservoir 레지스트리 수정 권한을 받은 사용자가 엔드포인트를 변경하면, 그 Reservoir 레지스트리가 새 엔드포인트로 옵니다

Given

- Reservoir 레지스트리 하나와, 레지스트리에 UPDATE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 registry-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 registry-keeper-1: artifact_registry 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.update: user-1이 registry-1의 엔드포인트를 변경합니다

Then

- 미리 저장한 레지스트리가 새 엔드포인트로 반환됩니다
  - id: 미리 저장한 레지스트리의 id 와 같다
  - entity_id: 미리 저장한 레지스트리의 id 와 같다
  - name = 'registry-1'
  - endpoint = 'https://storage.example.com'
  - access_key = 'access-key'
  - secret_key = '*****'
  - api_version = 'v1'

<a id="editing-a-user-granted-nothing-may-not-edit-a-registry"></a>

#### [a-user-granted-nothing-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_editing.py): pass

아무 권한도 받지 않은 사용자가 엔드포인트를 변경하려 하면 권한 부족으로 거부됩니다

Given

- Reservoir 레지스트리 하나와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 참조합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ReservoirRegistryAdapter.update: user-1이 registry-1의 엔드포인트를 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

