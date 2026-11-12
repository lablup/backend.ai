## model_card

[배경](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

시나리오: 완성

- ops 구성 (8)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - min_resources: 대표 성공 ✓ · 대표 거부 ✓
  - ownership_search: 대표 성공 ✓ · 대표 거부 ✓
  - project_search: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
- ops + 직접 구현 (3)
  - deploy: 성공 있음 1 · 거부 있음 1 (scope, single_get_ops)
  - partial_bulk_update: 성공 있음 1 · 거부 있음 1 (atomic_bulk_scoped_search_ops, partial_bulk)
  - update: 성공 있음 1 · 거부 있음 1 (atomic_bulk_scoped_search_ops, single_entity)
- 직접 구현 (4)
  - admin_bulk_delete: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - partial_bulk_purge: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - purge: 성공 있음 1 · 거부 있음 1 (single_entity)
  - scan_project: 성공 있음 1 · 거부 있음 2 (global_scope)
- Action 없음 (1)
  - available_presets: 성공 있음 1 · 거부 없음

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [모델 카드를 하나도 미리 저장하지 않은 상태에서 superadmin 이 전체를 조회하면 응답이 비어 있습니다](#model_card-a-scenario-that-laid-no-model-card-finds-none) | 성공 |
| [superadmin 이 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 차단됩니다](#model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드 둘을 id 로 일괄 조회하면 입력 순서대로 두 카드가 응답으로 옵니다](#batch_loading-a-user-granted-model-card-read-loads-cards-by-id-in-order) | 성공 |
| [한 프로젝트에서만 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드와 다른 프로젝트의 카드를 함께 일괄 조회하면, 호출은 성공하되 다른 프로젝트의 카드 항목은 권한 부족으로 거부됩니다](#batch_loading-a-card-of-a-project-without-read-gets-a-rejection-in-the-batch) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 생성과 읽기 권한을 받은 사용자가 카드를 만들면, 그 프로젝트에 놓이고 그 사용자가 만든 카드가 요청한 값과 최소 자원으로 옵니다](#creating-a-user-granted-create-in-the-project-makes-a-model-card) | 성공 |
| [프로젝트에서 모델 카드 생성과 읽기 권한을 받은 사용자가 그 프로젝트에 이미 있는 카드와 같은 이름으로 카드를 만들려 하면 이름이 겹친다는 이유로 거부됩니다](#creating-a-name-taken-in-the-project-is-refused) | 거부 |
| [프로젝트에서 모델 카드 읽기 권한만 받은 사용자가 카드를 만들려 하면 권한이 없다는 이유로 거부됩니다](#creating-a-user-granted-only-read-may-not-make-a-model-card) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 카드를 id 로 조회하면 그 카드 전체가 응답으로 옵니다](#getting-a-user-granted-model-card-read-gets-a-card-by-id) | 성공 |
| [프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 카드를 id 로 조회하면 권한 부족으로 거부됩니다](#getting-a-user-without-model-card-read-may-not-get-a-card) | 거부 |

**min_resources**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드 둘의 최소 자원 요구를 조회하면 카드마다 심은 요구가 응답으로 옵니다](#min_resources-a-user-granted-model-card-read-reads-the-minimum-resources) | 성공 |
| [한 프로젝트에서만 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드와 다른 프로젝트의 카드의 최소 자원 요구를 함께 조회하면 호출 전체가 권한 부족으로 거부됩니다](#min_resources-a-card-of-a-project-without-read-refuses-the-whole-call) | 거부 |

**ownership_search**

| 시나리오 | 판정 |
|---|---|
| [첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 걸리는 카드만 요청한 순서와 페이지대로 옵니다](#searching-a-user-granted-model-card-read-finds-cards-by-vfolder-ownership) | 성공 |
| [첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 부족으로 거부됩니다](#searching-a-user-without-model-card-read-may-not-find-cards-by-vfolder-ownership) | 거부 |

**project_search**

| 시나리오 | 판정 |
|---|---|
| [첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 걸리는 카드만 요청한 순서와 페이지대로 옵니다](#searching-a-user-granted-model-card-read-finds-cards-by-project) | 성공 |
| [첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 부족으로 거부됩니다](#searching-a-user-without-model-card-read-may-not-find-cards-by-project) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 걸리는 카드만 요청한 순서와 페이지대로 옵니다](#searching-a-user-granted-model-card-read-finds-cards-by-scope) | 성공 |
| [첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 부족으로 거부됩니다](#searching-a-user-without-model-card-read-may-not-find-cards-by-scope) | 거부 |

**deploy**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 카드와 그 vfolder 를 읽을 수 있고 배포 생성 권한을 받은 사용자가 카드를 프리셋으로 배포하면 카드 이름을 딴 배포가 만들어집니다](#deploying-a-user-granted-deployment-create-deploys-a-model-card) | 성공 |
| [프로젝트에서 카드와 그 vfolder 는 읽을 수 있지만 배포 생성 권한은 받지 않은 사용자가 카드를 배포하려 하면 권한이 없다는 이유로 거부됩니다](#deploying-a-user-without-deployment-create-may-not-deploy-a-model-card) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드 여럿의 제목을 한 번에 변경하면 모두 새 제목으로 오고 실패한 것은 없습니다](#partial_bulk_editing-a-user-granted-update-edits-several-model-cards) | 성공 |
| [프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 않은 다른 프로젝트의 카드를 한 번에 수정하면, 그 프로젝트의 카드만 새 제목으로 오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-card-outside-the-granted-project-is-not-edited) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드의 제목을 변경하면 제목은 새 값이 되고 나머지는 그대로 남습니다](#editing-a-user-granted-update-in-the-project-edits-a-model-card) | 성공 |
| [아무 권한도 받지 않은 사용자가 모델 카드를 수정하려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-a-model-card) | 거부 |

**admin_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 삭제하면 둘의 id 가 처리된 목록에 오고 실패한 것은 없습니다](#bulk_deleting-a-user-granted-purge-deletes-several-model-cards) | 성공 |
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 않은 다른 프로젝트의 카드를 한 번에 삭제하면, 그 프로젝트의 카드만 처리된 목록에 오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다](#bulk_deleting-a-card-outside-the-granted-project-is-not-deleted) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 purge 하면 둘 다 처리된 목록에 오고 실패한 것은 없습니다](#partial_bulk_purging-a-user-granted-purge-purges-several-model-cards) | 성공 |
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 않은 다른 프로젝트의 카드를 한 번에 purge 하면, 그 프로젝트의 카드만 처리된 목록에 오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-card-outside-the-granted-project-is-not-purged) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드를 purge 하면 그 카드의 id 가 응답으로 옵니다](#purging-a-user-granted-purge-in-the-project-purges-a-model-card) | 성공 |
| [아무 권한도 받지 않은 사용자가 모델 카드를 purge 하려 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-nothing-may-not-purge-a-model-card) | 거부 |

**scan_project**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 모델 정의 파일을 담은 vfolder 하나가 놓인 model-store 프로젝트를 훑으면 카드 하나가 새로 만들어집니다. 전역 역할이 이 호출을 막으므로 superadmin 이 부릅니다](#scanning-the-superadmin-scans-a-model-store-into-a-card) | 성공 |
| [superadmin 이 model-store 가 아닌 프로젝트를 훑으려 하면 프로젝트 유형이 맞지 않는다는 이유로 거부됩니다](#scanning-a-project-that-is-not-a-model-store-is-refused) | 거부 |
| [일반 사용자가 model-store 프로젝트를 훑으려 하면 전역 역할이 막아 거부됩니다](#scanning-a-regular-user-may-not-scan-a-model-store) | 거부 |

**available_presets**

| 시나리오 | 판정 |
|---|---|
| [프리셋과 카드를 읽을 수 있는 사용자가 카드를 배포할 수 있는 프리셋을 이름으로 거르고 정렬해 한 쪽만 찾으면, 카드가 요구하는 최소 자원을 채우는 프리셋만 세어지고 모자란 프리셋과 필터에 걸리지 않는 프리셋은 오지 않습니다](#available_presets-a-reader-finds-the-presets-meeting-the-card) | 성공 |

### admin_search

<a id="model_card-a-scenario-that-laid-no-model-card-finds-none"></a>

#### [a-scenario-that-laid-no-model-card-finds-none](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py): pass

모델 카드를 하나도 미리 저장하지 않은 상태에서 superadmin 이 전체를 조회하면 응답이 비어 있습니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ModelCardAdapter.admin_search: user-1이 필터 없이 전체를 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-model-card](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py): pass

superadmin 이 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 차단됩니다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ModelCardAdapter.admin_search: user-1이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-granted-model-card-read-loads-cards-by-id-in-order"></a>

#### [a-user-granted-model-card-read-loads-cards-by-id-in-order](/tests/scenario/bai_scenario/manager/model_card/test_batch_loading.py): pass

프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드 둘을 id 로 일괄 조회하면 입력 순서대로 두 카드가 응답으로 옵니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.batch_load_by_ids: user-2이 card-1, card-2 카드를 id 로 일괄 조회합니다

Then

- 카드 둘이 입력 순서대로 선택 항목과 최소 자원 요구까지 채워져 옵니다
  - length = 2
  - [0].id: 미리 저장한 카드와 같다
  - [0].entity_id: 미리 저장한 카드와 같다
  - [0].name = 'card-1'
  - [0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - [0].domain_name = 'home-1'
  - [0].project_id: 카드가 놓인 프로젝트와 같다
  - [0].creator_id: 카드를 만든 사람와 같다
  - [0].metadata.author = 'the-author'
  - [0].metadata.title = '검색에 걸리는 카드'
  - [0].metadata.model_version = '1.0'
  - [0].metadata.description = 'the description'
  - [0].metadata.task = 'text-generation'
  - [0].metadata.category = 'llm'
  - [0].metadata.architecture = 'llama'
  - [0].metadata.framework = ['pytorch']
  - [0].metadata.label = ['chat']
  - [0].metadata.license = 'apache-2.0'
  - [0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - [0].readme = 'the readme'
  - [0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1].id: 미리 저장한 카드와 같다
  - [1].entity_id: 미리 저장한 카드와 같다
  - [1].name = 'card-2'
  - [1].vfolder_id: 카드가 놓인 vfolder 와 같다
  - [1].domain_name = 'home-1'
  - [1].project_id: 카드가 놓인 프로젝트와 같다
  - [1].creator_id: 카드를 만든 사람와 같다
  - [1].metadata.author = 'the-author'
  - [1].metadata.title = '검색에 걸리는 카드'
  - [1].metadata.model_version = '1.0'
  - [1].metadata.description = 'the description'
  - [1].metadata.task = 'text-generation'
  - [1].metadata.category = 'llm'
  - [1].metadata.architecture = 'llama'
  - [1].metadata.framework = ['pytorch']
  - [1].metadata.label = ['chat']
  - [1].metadata.license = 'apache-2.0'
  - [1].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - [1].readme = 'the readme'
  - [1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - [1].created_at: 이 실행이 쓴 시각
  - [1].updated_at: 이 실행이 쓴 시각

<a id="batch_loading-a-card-of-a-project-without-read-gets-a-rejection-in-the-batch"></a>

#### [a-card-of-a-project-without-read-gets-a-rejection-in-the-batch](/tests/scenario/bai_scenario/manager/model_card/test_batch_loading.py): pass

한 프로젝트에서만 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드와 다른 프로젝트의 카드를 함께 일괄 조회하면, 호출은 성공하되 다른 프로젝트의 카드 항목은 권한 부족으로 거부됩니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.batch_load_by_ids: user-2이 card-1, 다른 프로젝트의 card-5 카드를 id 로 일괄 조회합니다

Then

- 읽을 수 있는 카드는 노드로, 권한이 없는 카드 항목은 권한 부족 거부로 옵니다
  - length = 2
  - [0].id: 미리 저장한 카드와 같다
  - [0].entity_id: 미리 저장한 카드와 같다
  - [0].name = 'card-1'
  - [0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - [0].domain_name = 'home-1'
  - [0].project_id: 카드가 놓인 프로젝트와 같다
  - [0].creator_id: 카드를 만든 사람와 같다
  - [0].metadata.author = 'the-author'
  - [0].metadata.title = '검색에 걸리는 카드'
  - [0].metadata.model_version = '1.0'
  - [0].metadata.description = 'the description'
  - [0].metadata.task = 'text-generation'
  - [0].metadata.category = 'llm'
  - [0].metadata.architecture = 'llama'
  - [0].metadata.framework = ['pytorch']
  - [0].metadata.label = ['chat']
  - [0].metadata.license = 'apache-2.0'
  - [0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - [0].readme = 'the readme'
  - [0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission

### create

<a id="creating-a-user-granted-create-in-the-project-makes-a-model-card"></a>

#### [a-user-granted-create-in-the-project-makes-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_creating.py): pass

프로젝트에서 모델 카드 생성과 읽기 권한을 받은 사용자가 카드를 만들면, 그 프로젝트에 놓이고 그 사용자가 만든 카드가 요청한 값과 최소 자원으로 옵니다

Given

- vfolder 가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 CREATE, READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 model-store-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 CREATE 허용
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-1: 역할 card-handler-1 보유

When

- ModelCardAdapter.create: user-1이 선택 항목까지 모두 채워 카드를 만듭니다

Then

- 요청에 채운 값으로 프로젝트에 놓이고 요청한 사람이 만든 카드가 옵니다
  - id: 건너뜀: 데이터베이스가 만든다
  - entity_id: 응답의 id 와 같다
  - name = 'llama-card'
  - vfolder_id: 요청한 vfolder 와 같다
  - domain_name = 'home-1'
  - project_id: 요청한 프로젝트와 같다
  - creator_id: 요청한 사람와 같다
  - metadata.author = '모델을 만든 사람'
  - metadata.title = '새 카드'
  - metadata.model_version = '1.0'
  - metadata.description = '새로 등록한 카드'
  - metadata.task = 'text-generation'
  - metadata.category = 'llm'
  - metadata.architecture = 'transformer'
  - metadata.framework = ['pytorch']
  - metadata.label = ['chat']
  - metadata.license = 'apache-2.0'
  - min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - readme = '카드 설명서'
  - access_level = <ModelCardAccessLevel.PUBLIC: 'public'>
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating-a-name-taken-in-the-project-is-refused"></a>

#### [a-name-taken-in-the-project-is-refused](/tests/scenario/bai_scenario/manager/model_card/test_creating.py): pass

프로젝트에서 모델 카드 생성과 읽기 권한을 받은 사용자가 그 프로젝트에 이미 있는 카드와 같은 이름으로 카드를 만들려 하면 이름이 겹친다는 이유로 거부됩니다

Given

- vfolder 가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 CREATE, READ 권한을 받은 사용자 한 명, 그리고 그 프로젝트에 이미 놓인 카드 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 model-store-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 CREATE 허용
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-1: 역할 card-handler-1 보유

When

- ModelCardAdapter.create: user-1이 이미 놓인 카드와 같은 이름으로 카드를 만듭니다

Then

- 거부됩니다
  - 거부: ModelCardConflict

<a id="creating-a-user-granted-only-read-may-not-make-a-model-card"></a>

#### [a-user-granted-only-read-may-not-make-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_creating.py): pass

프로젝트에서 모델 카드 읽기 권한만 받은 사용자가 카드를 만들려 하면 권한이 없다는 이유로 거부됩니다

Given

- vfolder 가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 model-store-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-1: 역할 card-handler-1 보유

When

- ModelCardAdapter.create: user-1이 선택 항목까지 모두 채워 카드를 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get

<a id="getting-a-user-granted-model-card-read-gets-a-card-by-id"></a>

#### [a-user-granted-model-card-read-gets-a-card-by-id](/tests/scenario/bai_scenario/manager/model_card/test_getting.py): pass

프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 카드를 id 로 조회하면 그 카드 전체가 응답으로 옵니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.get: user-2이 card-1 카드를 id 로 조회합니다

Then

- 선택 항목과 최소 자원 요구까지 채워진 카드 전체가 응답으로 옵니다
  - id: 미리 저장한 카드와 같다
  - entity_id: 미리 저장한 카드와 같다
  - name = 'card-1'
  - vfolder_id: 카드가 놓인 vfolder 와 같다
  - domain_name = 'home-1'
  - project_id: 카드가 놓인 프로젝트와 같다
  - creator_id: 카드를 만든 사람와 같다
  - metadata.author = 'the-author'
  - metadata.title = '검색에 걸리는 카드'
  - metadata.model_version = '1.0'
  - metadata.description = 'the description'
  - metadata.task = 'text-generation'
  - metadata.category = 'llm'
  - metadata.architecture = 'llama'
  - metadata.framework = ['pytorch']
  - metadata.label = ['chat']
  - metadata.license = 'apache-2.0'
  - min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - readme = 'the readme'
  - access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="getting-a-user-without-model-card-read-may-not-get-a-card"></a>

#### [a-user-without-model-card-read-may-not-get-a-card](/tests/scenario/bai_scenario/manager/model_card/test_getting.py): pass

프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 카드를 id 로 조회하면 권한 부족으로 거부됩니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.get: user-2이 card-1 카드를 id 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### min_resources

<a id="min_resources-a-user-granted-model-card-read-reads-the-minimum-resources"></a>

#### [a-user-granted-model-card-read-reads-the-minimum-resources](/tests/scenario/bai_scenario/manager/model_card/test_min_resources.py): pass

프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드 둘의 최소 자원 요구를 조회하면 카드마다 심은 요구가 응답으로 옵니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.min_resources: user-2이 card-1, card-2 카드의 최소 자원 요구를 조회합니다

Then

- 요청한 카드마다 심은 최소 자원 요구가 옵니다
  - length = 2
  - card-1 = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - card-2 = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]

<a id="min_resources-a-card-of-a-project-without-read-refuses-the-whole-call"></a>

#### [a-card-of-a-project-without-read-refuses-the-whole-call](/tests/scenario/bai_scenario/manager/model_card/test_min_resources.py): pass

한 프로젝트에서만 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드와 다른 프로젝트의 카드의 최소 자원 요구를 함께 조회하면 호출 전체가 권한 부족으로 거부됩니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.min_resources: user-2이 card-1, 다른 프로젝트의 card-5 카드의 최소 자원 요구를 함께 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### ownership_search

<a id="searching-a-user-granted-model-card-read-finds-cards-by-vfolder-ownership"></a>

#### [a-user-granted-model-card-read-finds-cards-by-vfolder-ownership](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 걸리는 카드만 요청한 순서와 페이지대로 옵니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은, 그 프로젝트의 vfolder 읽기도 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- ModelCardAdapter.ownership_search: user-2이 model-store-1 프로젝트가 소유한 vfolder 하나를 쓰는 카드를 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다

Then

- 필터에 걸리고 범위 안에 있는 카드만 정렬 순서대로 한 페이지에 옵니다. 범위 밖 카드와 필터에 걸리지 않는 카드는 응답에도 건수에도 없습니다
  - items count = 1
  - items[0].id: 미리 저장한 카드와 같다
  - items[0].entity_id: 미리 저장한 카드와 같다
  - items[0].name = 'card-1'
  - items[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].project_id: 카드가 놓인 프로젝트와 같다
  - items[0].creator_id: 카드를 만든 사람와 같다
  - items[0].metadata.author = 'the-author'
  - items[0].metadata.title = '검색에 걸리는 카드'
  - items[0].metadata.model_version = '1.0'
  - items[0].metadata.description = 'the description'
  - items[0].metadata.task = 'text-generation'
  - items[0].metadata.category = 'llm'
  - items[0].metadata.architecture = 'llama'
  - items[0].metadata.framework = ['pytorch']
  - items[0].metadata.label = ['chat']
  - items[0].metadata.license = 'apache-2.0'
  - items[0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - items[0].readme = 'the readme'
  - items[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-without-model-card-read-may-not-find-cards-by-vfolder-ownership"></a>

#### [a-user-without-model-card-read-may-not-find-cards-by-vfolder-ownership](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 부족으로 거부됩니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 UPDATE 권한을 받은, 그 프로젝트의 vfolder 읽기도 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- ModelCardAdapter.ownership_search: user-2이 model-store-1 프로젝트가 소유한 vfolder 하나를 쓰는 카드를 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### project_search

<a id="searching-a-user-granted-model-card-read-finds-cards-by-project"></a>

#### [a-user-granted-model-card-read-finds-cards-by-project](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 걸리는 카드만 요청한 순서와 페이지대로 옵니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.project_search: user-2이 model-store-1 프로젝트에서 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다

Then

- 필터에 걸리고 범위 안에 있는 카드만 정렬 순서대로 한 페이지에 옵니다. 범위 밖 카드와 필터에 걸리지 않는 카드는 응답에도 건수에도 없습니다
  - items count = 2
  - items[0].id: 미리 저장한 카드와 같다
  - items[0].entity_id: 미리 저장한 카드와 같다
  - items[0].name = 'card-3'
  - items[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].project_id: 카드가 놓인 프로젝트와 같다
  - items[0].creator_id: 카드를 만든 사람와 같다
  - items[0].metadata.author = 'the-author'
  - items[0].metadata.title = '검색에 걸리는 카드'
  - items[0].metadata.model_version = '1.0'
  - items[0].metadata.description = 'the description'
  - items[0].metadata.task = 'text-generation'
  - items[0].metadata.category = 'llm'
  - items[0].metadata.architecture = 'llama'
  - items[0].metadata.framework = ['pytorch']
  - items[0].metadata.label = ['chat']
  - items[0].metadata.license = 'apache-2.0'
  - items[0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='3')]
  - items[0].readme = 'the readme'
  - items[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 미리 저장한 카드와 같다
  - items[1].entity_id: 미리 저장한 카드와 같다
  - items[1].name = 'card-2'
  - items[1].vfolder_id: 카드가 놓인 vfolder 와 같다
  - items[1].domain_name = 'home-1'
  - items[1].project_id: 카드가 놓인 프로젝트와 같다
  - items[1].creator_id: 카드를 만든 사람와 같다
  - items[1].metadata.author = 'the-author'
  - items[1].metadata.title = '검색에 걸리는 카드'
  - items[1].metadata.model_version = '1.0'
  - items[1].metadata.description = 'the description'
  - items[1].metadata.task = 'text-generation'
  - items[1].metadata.category = 'llm'
  - items[1].metadata.architecture = 'llama'
  - items[1].metadata.framework = ['pytorch']
  - items[1].metadata.label = ['chat']
  - items[1].metadata.license = 'apache-2.0'
  - items[1].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - items[1].readme = 'the readme'
  - items[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-without-model-card-read-may-not-find-cards-by-project"></a>

#### [a-user-without-model-card-read-may-not-find-cards-by-project](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 부족으로 거부됩니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.project_search: user-2이 model-store-1 프로젝트에서 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="searching-a-user-granted-model-card-read-finds-cards-by-scope"></a>

#### [a-user-granted-model-card-read-finds-cards-by-scope](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 걸리는 카드만 요청한 순서와 페이지대로 옵니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 READ 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.scoped_search: user-2이 model-store-1 프로젝트 범위에서 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다

Then

- 필터에 걸리고 범위 안에 있는 카드만 정렬 순서대로 한 페이지에 옵니다. 범위 밖 카드와 필터에 걸리지 않는 카드는 응답에도 건수에도 없습니다
  - items count = 2
  - items[0].id: 미리 저장한 카드와 같다
  - items[0].entity_id: 미리 저장한 카드와 같다
  - items[0].name = 'card-3'
  - items[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - items[0].domain_name = 'home-1'
  - items[0].project_id: 카드가 놓인 프로젝트와 같다
  - items[0].creator_id: 카드를 만든 사람와 같다
  - items[0].metadata.author = 'the-author'
  - items[0].metadata.title = '검색에 걸리는 카드'
  - items[0].metadata.model_version = '1.0'
  - items[0].metadata.description = 'the description'
  - items[0].metadata.task = 'text-generation'
  - items[0].metadata.category = 'llm'
  - items[0].metadata.architecture = 'llama'
  - items[0].metadata.framework = ['pytorch']
  - items[0].metadata.label = ['chat']
  - items[0].metadata.license = 'apache-2.0'
  - items[0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='3')]
  - items[0].readme = 'the readme'
  - items[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 미리 저장한 카드와 같다
  - items[1].entity_id: 미리 저장한 카드와 같다
  - items[1].name = 'card-2'
  - items[1].vfolder_id: 카드가 놓인 vfolder 와 같다
  - items[1].domain_name = 'home-1'
  - items[1].project_id: 카드가 놓인 프로젝트와 같다
  - items[1].creator_id: 카드를 만든 사람와 같다
  - items[1].metadata.author = 'the-author'
  - items[1].metadata.title = '검색에 걸리는 카드'
  - items[1].metadata.model_version = '1.0'
  - items[1].metadata.description = 'the description'
  - items[1].metadata.task = 'text-generation'
  - items[1].metadata.category = 'llm'
  - items[1].metadata.architecture = 'llama'
  - items[1].metadata.framework = ['pytorch']
  - items[1].metadata.label = ['chat']
  - items[1].metadata.license = 'apache-2.0'
  - items[1].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - items[1].readme = 'the readme'
  - items[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-without-model-card-read-may-not-find-cards-by-scope"></a>

#### [a-user-without-model-card-read-may-not-find-cards-by-scope](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 부족으로 거부됩니다

Given

- 모델 카드가 놓인 프로젝트 둘과, 첫 프로젝트에서 모델 카드에 UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 other-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-3: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-4: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-4: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리지 않는 카드'입니다, 선택 항목도 모두 채웁니다
  - 프로젝트 vfolder folder-5: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-5: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '검색에 걸리는 카드'입니다, 선택 항목도 모두 채웁니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: cpu 최소 1 요구
  - 모델 카드 card-2: cpu 최소 2 요구
  - 모델 카드 card-3: cpu 최소 3 요구
  - 모델 카드 card-4: cpu 최소 4 요구
  - 모델 카드 card-5: cpu 최소 5 요구
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.scoped_search: user-2이 model-store-1 프로젝트 범위에서 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### deploy

<a id="deploying-a-user-granted-deployment-create-deploys-a-model-card"></a>

#### [a-user-granted-deployment-create-deploys-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_deploying.py): pass

프로젝트에서 카드와 그 vfolder 를 읽을 수 있고 배포 생성 권한을 받은 사용자가 카드를 프리셋으로 배포하면 카드 이름을 딴 배포가 만들어집니다

Given

- 모델 카드 하나가 놓인 프로젝트와 배포할 프리셋, 그리고 그 프로젝트에서 카드와 vfolder 를 읽을 수 있고 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 이미지를 가리킵니다, 모델 'served' 하나를 서빙합니다, 단일 노드, 복제본 하나, 롤링 업데이트
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유
  - 배포 권한 부여
    - 역할 deployer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployer-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-2: 역할 deployer-1 보유

When

- ModelCardAdapter.deploy: user-2이 카드 card-1을 프리셋 preset-1으로 자원 그룹 resource-group-1에 배포합니다

Then

- 카드 이름을 딴 배포가 만들어집니다
  - deployment_id: 건너뜀: 데이터베이스가 만든 id 입니다
  - deployment_name: 'card-1-' 뒤에 16진수 여덟 자리가 붙은 이름

<a id="deploying-a-user-without-deployment-create-may-not-deploy-a-model-card"></a>

#### [a-user-without-deployment-create-may-not-deploy-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_deploying.py): pass

프로젝트에서 카드와 그 vfolder 는 읽을 수 있지만 배포 생성 권한은 받지 않은 사용자가 카드를 배포하려 하면 권한이 없다는 이유로 거부됩니다

Given

- 모델 카드 하나가 놓인 프로젝트와 배포할 프리셋, 그리고 그 프로젝트에서 카드와 vfolder 를 읽을 수 있고 배포 권한은 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 이미지를 가리킵니다, 모델 'served' 하나를 서빙합니다, 단일 노드, 복제본 하나, 롤링 업데이트
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- ModelCardAdapter.deploy: user-2이 카드 card-1을 프리셋 preset-1으로 자원 그룹 resource-group-1에 배포합니다

Then

- 권한이 없다는 이유로 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-update-edits-several-model-cards"></a>

#### [a-user-granted-update-edits-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py): pass

프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드 여럿의 제목을 한 번에 변경하면 모두 새 제목으로 오고 실패한 것은 없습니다

Given

- 모델 카드 2개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.partial_bulk_update: user-2이 카드 2개의 제목을 한 번에 수정합니다

Then

- 대상 카드가 모두 새 제목으로 오고 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 카드와 같다
  - successes[0].entity_id: 미리 저장한 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '수정한 제목'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 카드와 같다
  - successes[1].entity_id: 미리 저장한 카드와 같다
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: 카드가 놓인 vfolder 와 같다
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: 카드가 놓인 프로젝트와 같다
  - successes[1].creator_id: 카드를 만든 사람와 같다
  - successes[1].metadata.author = None
  - successes[1].metadata.title = '수정한 제목'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

<a id="partial_bulk_editing-a-card-outside-the-granted-project-is-not-edited"></a>

#### [a-card-outside-the-granted-project-is-not-edited](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py): pass

프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 않은 다른 프로젝트의 카드를 한 번에 수정하면, 그 프로젝트의 카드만 새 제목으로 오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 READ, UPDATE 권한을 받은 user 한 명, 그리고 그 사용자가 아무 권한도 받지 않은 다른 프로젝트의 카드 1개
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 프로젝트 model-store-2
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.partial_bulk_update: user-2이 카드 2개의 제목을 한 번에 수정합니다

Then

- 권한이 있는 카드는 모두 처리된 목록에 오고, 다른 프로젝트의 카드만 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id: 미리 저장한 카드와 같다
  - successes[0].entity_id: 미리 저장한 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '수정한 제목'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 다른 프로젝트의 카드와 같다
  - 거부: failed[0].message: NotEnoughPermission

### update

<a id="editing-a-user-granted-update-in-the-project-edits-a-model-card"></a>

#### [a-user-granted-update-in-the-project-edits-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_editing.py): pass

프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드의 제목을 변경하면 제목은 새 값이 되고 나머지는 그대로 남습니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.update: user-2이 card-1의 제목을 수정합니다

Then

- 제목은 새 값이 되고 나머지는 그대로인 카드 전체가 응답으로 옵니다
  - id: 미리 저장한 카드와 같다
  - entity_id: 미리 저장한 카드와 같다
  - name = 'card-1'
  - vfolder_id: 카드가 놓인 vfolder 와 같다
  - domain_name = 'home-1'
  - project_id: 카드가 놓인 프로젝트와 같다
  - creator_id: 카드를 만든 사람와 같다
  - metadata.author = None
  - metadata.title = '수정한 제목'
  - metadata.model_version = None
  - metadata.description = None
  - metadata.task = None
  - metadata.category = None
  - metadata.architecture = None
  - metadata.framework = []
  - metadata.label = []
  - metadata.license = None
  - min_resource = None
  - readme = None
  - access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-edit-a-model-card"></a>

#### [a-user-granted-nothing-may-not-edit-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_editing.py): pass

아무 권한도 받지 않은 사용자가 모델 카드를 수정하려 하면 권한 부족으로 거부됩니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다

When

- ModelCardAdapter.update: user-2이 card-1의 제목을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### admin_bulk_delete

<a id="bulk_deleting-a-user-granted-purge-deletes-several-model-cards"></a>

#### [a-user-granted-purge-deletes-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_bulk_deleting.py): pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 삭제하면 둘의 id 가 처리된 목록에 오고 실패한 것은 없습니다

Given

- 모델 카드 2개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.admin_bulk_delete: user-2이 카드 2개를 vfolder 는 남기고 한 번에 삭제합니다

Then

- 대상 카드의 id 가 모두 처리된 목록에 오고 실패한 것은 없습니다
  - successes count = 2
  - successes[0]: 대상 카드와 같다
  - successes[1]: 대상 카드와 같다
  - failed = []

<a id="bulk_deleting-a-card-outside-the-granted-project-is-not-deleted"></a>

#### [a-card-outside-the-granted-project-is-not-deleted](/tests/scenario/bai_scenario/manager/model_card/test_bulk_deleting.py): pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 않은 다른 프로젝트의 카드를 한 번에 삭제하면, 그 프로젝트의 카드만 처리된 목록에 오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명, 그리고 그 사용자가 아무 권한도 받지 않은 다른 프로젝트의 카드 1개
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 프로젝트 model-store-2
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.admin_bulk_delete: user-2이 카드 2개를 vfolder 는 남기고 한 번에 삭제합니다

Then

- 그 프로젝트의 카드 id 는 처리된 목록에 오고, 다른 프로젝트의 카드만 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0]: 대상 카드와 같다
  - failed count = 1
  - failed[0].card_id: 다른 프로젝트의 카드와 같다
  - 거부: failed[0].message: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-model-cards"></a>

#### [a-user-granted-purge-purges-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py): pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 purge 하면 둘 다 처리된 목록에 오고 실패한 것은 없습니다

Given

- 모델 카드 2개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.partial_bulk_purge: user-2이 카드 2개를 한 번에 purge 합니다

Then

- 대상 카드가 모두 처리된 목록에 오고 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 카드와 같다
  - successes[0].entity_id: 미리 저장한 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '이미 있던 카드'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 카드와 같다
  - successes[1].entity_id: 미리 저장한 카드와 같다
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: 카드가 놓인 vfolder 와 같다
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: 카드가 놓인 프로젝트와 같다
  - successes[1].creator_id: 카드를 만든 사람와 같다
  - successes[1].metadata.author = None
  - successes[1].metadata.title = '이미 있던 카드'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

<a id="partial_bulk_purging-a-card-outside-the-granted-project-is-not-purged"></a>

#### [a-card-outside-the-granted-project-is-not-purged](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py): pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 않은 다른 프로젝트의 카드를 한 번에 purge 하면, 그 프로젝트의 카드만 처리된 목록에 오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명, 그리고 그 사용자가 아무 권한도 받지 않은 다른 프로젝트의 카드 1개
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 프로젝트 model-store-2
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-2: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.partial_bulk_purge: user-2이 카드 2개를 한 번에 purge 합니다

Then

- 권한이 있는 카드는 모두 처리된 목록에 오고, 다른 프로젝트의 카드만 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id: 미리 저장한 카드와 같다
  - successes[0].entity_id: 미리 저장한 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 놓인 vfolder 와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '이미 있던 카드'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 다른 프로젝트의 카드와 같다
  - 거부: failed[0].message: NotEnoughPermission

### purge

<a id="purging-a-user-granted-purge-in-the-project-purges-a-model-card"></a>

#### [a-user-granted-purge-in-the-project-purges-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_purging.py): pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드를 purge 하면 그 카드의 id 가 응답으로 옵니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.purge: user-2이 card-1을 purge 하고 vfolder 는 그대로 둡니다

Then

- purge 한 카드의 id 가 응답으로 옵니다
  - id: 미리 저장한 카드와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-model-card"></a>

#### [a-user-granted-nothing-may-not-purge-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_purging.py): pass

아무 권한도 받지 않은 사용자가 모델 카드를 purge 하려 하면 권한 부족으로 거부됩니다

Given

- 모델 카드 1개가 놓인 프로젝트와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다

When

- ModelCardAdapter.purge: user-2이 card-1을 purge 하고 vfolder 는 그대로 둡니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scan_project

<a id="scanning-the-superadmin-scans-a-model-store-into-a-card"></a>

#### [the-superadmin-scans-a-model-store-into-a-card](/tests/scenario/bai_scenario/manager/model_card/test_scanning.py): pass

superadmin 이 모델 정의 파일을 담은 vfolder 하나가 놓인 model-store 프로젝트를 훑으면 카드 하나가 새로 만들어집니다. 전역 역할이 이 호출을 막으므로 superadmin 이 부릅니다

Given

- 모델 하나를 적은 모델 정의 파일을 담은 vfolder 하나가 놓인 model-store 프로젝트와 superadmin 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 model-store-1: 유형은 model-store 입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태이며, 용도는 model 입니다

When

- ModelCardAdapter.scan_project: user-1이 프로젝트 model-store-1의 vfolder 를 훑습니다

Then

- 카드 하나가 새로 만들어지고 고친 카드와 오류는 없습니다
  - created_count = 1
  - updated_count = 0
  - errors = []

<a id="scanning-a-project-that-is-not-a-model-store-is-refused"></a>

#### [a-project-that-is-not-a-model-store-is-refused](/tests/scenario/bai_scenario/manager/model_card/test_scanning.py): pass

superadmin 이 model-store 가 아닌 프로젝트를 훑으려 하면 프로젝트 유형이 맞지 않는다는 이유로 거부됩니다

Given

- 모델 하나를 적은 모델 정의 파일을 담은 vfolder 하나가 놓인 general 프로젝트와 superadmin 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 model-store-1: 유형은 general 입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- ModelCardAdapter.scan_project: user-1이 프로젝트 model-store-1의 vfolder 를 훑습니다

Then

- 거부됩니다
  - 거부: InvalidProjectTypeForModelCard

<a id="scanning-a-regular-user-may-not-scan-a-model-store"></a>

#### [a-regular-user-may-not-scan-a-model-store](/tests/scenario/bai_scenario/manager/model_card/test_scanning.py): pass

일반 사용자가 model-store 프로젝트를 훑으려 하면 전역 역할이 막아 거부됩니다

Given

- 모델 하나를 적은 모델 정의 파일을 담은 vfolder 하나가 놓인 model-store 프로젝트와 user 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 model-store-1: 유형은 model-store 입니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태이며, 용도는 model 입니다

When

- ModelCardAdapter.scan_project: user-1이 프로젝트 model-store-1의 vfolder 를 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### available_presets

<a id="available_presets-a-reader-finds-the-presets-meeting-the-card"></a>

#### [a-reader-finds-the-presets-meeting-the-card](/tests/scenario/bai_scenario/manager/model_card/test_available_presets.py): pass

프리셋과 카드를 읽을 수 있는 사용자가 카드를 배포할 수 있는 프리셋을 이름으로 거르고 정렬해 한 쪽만 찾으면, 카드가 요구하는 최소 자원을 채우는 프리셋만 세어지고 모자란 프리셋과 필터에 걸리지 않는 프리셋은 오지 않습니다

Given

- cpu 를 2 이상 요구하는 모델 카드 하나, 'fits' 로 시작하는 이름의 프리셋 셋(cpu 4, cpu 2, cpu 1), 다른 이름의 cpu 4 프리셋 하나, 그리고 public 에서 프리셋을 읽고 그 프로젝트에서 카드를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 model-store-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 모델 카드 card-1: 프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '이미 있던 카드'입니다
  - 모델 카드 card-1: cpu 최소 2 요구
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 fits-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 fits-1: cpu 슬롯 하나를 두려 한다
  - 배포 리비전 프리셋 fits-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 fits-2: cpu 슬롯 하나를 두려 한다
  - 배포 리비전 프리셋 fits-3: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 fits-3: cpu 슬롯 하나를 두려 한다
  - 배포 리비전 프리셋 other-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 other-1: cpu 슬롯 하나를 두려 한다
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-2: 역할 public-reader-1 보유
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.available_presets: user-2이 카드 card-1을 배포할 수 있는 프리셋을 이름이 'fits'로 시작하는 것만, 이름 역순으로 첫 한 개 찾습니다

Then

- 요구를 채우고 이름이 걸리는 프리셋 둘이 세어지고, 이름 역순 첫 쪽에는 그중 이름이 늦은 cpu 2 프리셋 하나가 옵니다. 모자란 프리셋과 다른 이름의 프리셋은 오지 않습니다
  - items count = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - items[0].id: 미리 저장한 프리셋와 같다
  - items[0].entity_id: 미리 저장한 프리셋와 같다
  - items[0].runtime_variant_id: 프리셋의 인퍼런스 런타임 종류와 같다
  - items[0].name = 'fits-2'
  - items[0].description = '미리 저장한 프리셋'
  - items[0].rank = 200
  - items[0].cluster.cluster_mode = 'single-node'
  - items[0].cluster.cluster_size = 1
  - items[0].resource.resource_opts = []
  - items[0].execution.image_id: 프리셋이 가리키는 이미지와 같다
  - items[0].execution.startup_command = None
  - items[0].execution.bootstrap_script = None
  - items[0].execution.environ = []
  - items[0].deployment_defaults.open_to_public = None
  - items[0].deployment_defaults.replica_count = 1
  - items[0].deployment_defaults.revision_history_limit = None
  - items[0].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - items[0].deployment_defaults.deployment_strategy_spec = {}
  - items[0].model_definition = None
  - items[0].preset_values = []
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

