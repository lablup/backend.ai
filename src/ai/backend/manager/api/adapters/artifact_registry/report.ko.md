## artifact_registry

[어댑터](/src/ai/backend/manager/api/adapters/artifact_registry/adapter.py)

시나리오: 미완성 1 / 3

- ops 구성 (2)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - get_registry_metas: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
- 직접 구현 (1)
  - get_registry_meta: 성공 있음 1 · 거부 있음 2 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록으로 레지스트리를 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다](#reading_many-an-empty-registry-id-list-answers-empty) | 성공 |
| [global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 미리 저장한 레지스트리 둘을 한 번에 읽으면, 자리마다 미리 저장한 레지스트리 전체가 요청한 순서대로 옵니다](#reading_many-loading-many-registry-ids-keeps-the-positions) | 성공 |
| [아무 권한도 받지 않은 사용자가 레지스트리 id 여럿을 한 번에 읽으면, 항목마다 권한 부족 거부가 담겨 오고 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다](#reading_many-a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position) | 거부 |

**get_registry_metas**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 읽으면, 요청 전체가 거부되는 대신 읽을 수 있는 레지스트리가 없어 빈 목록이 옵니다](#reading_many-a-user-granted-nothing-reading-many-registries-gets-none) | 성공 |
| [global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 미리 저장한 레지스트리 둘과 없는 id 하나를 한 번에 읽으면, 읽을 수 있는 레지스트리 둘만 요청한 순서대로 옵니다](#reading_many-reading-many-registries-leaves-out-the-id-that-names-none) | 성공 |

**get_registry_meta**

| 시나리오 | 판정 |
|---|---|
| [global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 레지스트리를 id 로 읽으면, 미리 저장한 레지스트리 전체가 옵니다](#reading-a-user-granted-read-reads-a-registry-by-id) | 성공 |
| [어떤 레지스트리도 가리키지 않는 이름으로 읽으면, 그 이름을 풀 수 없다는 것으로 거부됩니다](#reading-a-name-naming-no-registry-is-refused) | 거부 |
| [아무 권한도 받지 않은 사용자가 레지스트리를 id 로 읽으려 하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-a-registry) | 거부 |

### batch_load_by_ids

<a id="reading_many-an-empty-registry-id-list-answers-empty"></a>

#### [an-empty-registry-id-list-answers-empty](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

빈 id 목록으로 레지스트리를 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다

Given

- HuggingFace 레지스트리 2개와, global 에서 아티팩트 레지스트리에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
  - 허깅 페이스 레지스트리 registry-2: https://huggingface.co 을 참조합니다
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

- ArtifactRegistryAdapter.batch_load_by_ids: user-1이 빈 id 목록으로 읽습니다

Then

- 빈 응답이 반환됩니다
  - items = []

<a id="reading_many-loading-many-registry-ids-keeps-the-positions"></a>

#### [loading-many-registry-ids-keeps-the-positions](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 미리 저장한 레지스트리 둘을 한 번에 읽으면, 자리마다 미리 저장한 레지스트리 전체가 요청한 순서대로 옵니다

Given

- HuggingFace 레지스트리 2개와, global 에서 아티팩트 레지스트리에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
  - 허깅 페이스 레지스트리 registry-2: https://huggingface.co 을 참조합니다
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

- ArtifactRegistryAdapter.batch_load_by_ids: user-1이 미리 저장한 레지스트리 둘을 한 번에 읽습니다

Then

- 자리마다 미리 저장한 레지스트리 전체가 요청한 순서대로 옵니다
  - length = 2
  - [0].id: 같은 응답의 entity id 와 같다
  - [0].entity_id: 같은 응답의 id 와 같다
  - [0].registry_id: 미리 저장한 레지스트리의 id 와 같다
  - [0].name = 'registry-1'
  - [0].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].id: 같은 응답의 entity id 와 같다
  - [1].entity_id: 같은 응답의 id 와 같다
  - [1].registry_id: 미리 저장한 레지스트리의 id 와 같다
  - [1].name = 'registry-2'
  - [1].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>

<a id="reading_many-a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position"></a>

#### [a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

아무 권한도 받지 않은 사용자가 레지스트리 id 여럿을 한 번에 읽으면, 항목마다 권한 부족 거부가 담겨 오고 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다

Given

- HuggingFace 레지스트리 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
  - 허깅 페이스 레지스트리 registry-2: https://huggingface.co 을 참조합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactRegistryAdapter.batch_load_by_ids: user-1이 미리 저장한 레지스트리 둘과 없는 id 하나를 한 번에 읽습니다

Then

- 자리마다 권한 부족 거부가 담겨 오고, 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다
  - length = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### get_registry_metas

<a id="reading_many-a-user-granted-nothing-reading-many-registries-gets-none"></a>

#### [a-user-granted-nothing-reading-many-registries-gets-none](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 읽으면, 요청 전체가 거부되는 대신 읽을 수 있는 레지스트리가 없어 빈 목록이 옵니다

Given

- HuggingFace 레지스트리 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
  - 허깅 페이스 레지스트리 registry-2: https://huggingface.co 을 참조합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactRegistryAdapter.get_registry_metas: user-1이 미리 저장한 레지스트리 2개를 한 번에 읽습니다

Then

- 읽을 수 있는 레지스트리가 없어 빈 목록이 옵니다
  - items = []

<a id="reading_many-reading-many-registries-leaves-out-the-id-that-names-none"></a>

#### [reading-many-registries-leaves-out-the-id-that-names-none](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 미리 저장한 레지스트리 둘과 없는 id 하나를 한 번에 읽으면, 읽을 수 있는 레지스트리 둘만 요청한 순서대로 옵니다

Given

- HuggingFace 레지스트리 2개와, global 에서 아티팩트 레지스트리에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
  - 허깅 페이스 레지스트리 registry-2: https://huggingface.co 을 참조합니다
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

- ArtifactRegistryAdapter.get_registry_metas: user-1이 미리 저장한 레지스트리 2개와 없는 id 하나를 한 번에 읽습니다

Then

- 읽을 수 있는 레지스트리만 요청한 순서대로 오고, 읽을 수 없거나 없는 id 는 빠집니다
  - count = 2
  - [0].id: 같은 응답의 entity id 와 같다
  - [0].entity_id: 같은 응답의 id 와 같다
  - [0].registry_id: 미리 저장한 레지스트리의 id 와 같다
  - [0].name = 'registry-1'
  - [0].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].id: 같은 응답의 entity id 와 같다
  - [1].entity_id: 같은 응답의 id 와 같다
  - [1].registry_id: 미리 저장한 레지스트리의 id 와 같다
  - [1].name = 'registry-2'
  - [1].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>

### get_registry_meta

<a id="reading-a-user-granted-read-reads-a-registry-by-id"></a>

#### [a-user-granted-read-reads-a-registry-by-id](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 레지스트리를 id 로 읽으면, 미리 저장한 레지스트리 전체가 옵니다

Given

- HuggingFace 레지스트리 하나와, global 에서 아티팩트 레지스트리에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
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

- ArtifactRegistryAdapter.get_registry_meta: user-1이 registry-1을 id 로 읽습니다

Then

- 미리 저장한 레지스트리 전체가 옵니다
  - id: 같은 응답의 entity id 와 같다
  - entity_id: 같은 응답의 id 와 같다
  - registry_id: 미리 저장한 레지스트리의 id 와 같다
  - name = 'registry-1'
  - type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>

<a id="reading-a-name-naming-no-registry-is-refused"></a>

#### [a-name-naming-no-registry-is-refused](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

어떤 레지스트리도 가리키지 않는 이름으로 읽으면, 그 이름을 풀 수 없다는 것으로 거부됩니다

Given

- HuggingFace 레지스트리 하나와, global 에서 아티팩트 레지스트리에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
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

- ArtifactRegistryAdapter.get_registry_meta: user-1이 어떤 레지스트리도 가리키지 않는 이름으로 읽습니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="reading-a-user-granted-nothing-may-not-read-a-registry"></a>

#### [a-user-granted-nothing-may-not-read-a-registry](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

아무 권한도 받지 않은 사용자가 레지스트리를 id 로 읽으려 하면 권한 부족으로 거부됩니다

Given

- HuggingFace 레지스트리 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 허깅 페이스 레지스트리 registry-1: https://huggingface.co 을 참조합니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactRegistryAdapter.get_registry_meta: user-1이 registry-1을 id 로 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

