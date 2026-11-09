## deployment_revision_preset

[배경](/src/ai/backend/manager/api/adapters/deployment_revision_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/deployment_revision_preset/adapter.py)

시나리오: 미완성 3 / 10

- ops 구성 (8)
  - available_presets: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✓
  - search_resource_slots: 대표 성공 ✓ · 대표 거부 ✓
- ops + 직접 구현 (2)
  - partial_bulk_update: 성공 있음 2 · 거부 없음 (partial_bulk, single_get_ops): SCENARIO-GAP
  - update: 성공 있음 1 · 거부 있음 1 (single_entity, single_get_ops)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [프리셋 조회 권한을 받은 사용자가 심은 프리셋 여럿을 id 로 일괄 조회하면, 입력 순서대로 그 프리셋들이 옵니다](#batch_loading-a-preset-reader-loads-the-presets-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 심은 프리셋 여럿을 id 로 일괄 조회하면, 호출은 성공하되 항목마다 권한 부족으로 거부가 옵니다](#batch_loading-a-user-granted-nothing-gets-a-rejection-for-each-preset) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [전역 권한으로만 만들 수 있는 프리셋을 superadmin 이 만들면, 만든 프리셋이 옵니다. 이 행의 요청 사용자는 전역 권한이 필요한 호출이라 superadmin 입니다](#creating-the-superadmin-makes-a-preset) | 성공 |
| [프리셋 조회 권한만 받은 사용자가 프리셋을 만들려 하면, 전역 권한이 없다는 이유로 거부됩니다](#creating-a-preset-reader-makes-no-preset) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [프리셋 조회 권한을 받은 사용자가 심은 프리셋 하나를 id 로 읽으면, 그 프리셋이 옵니다](#reading-a-preset-reader-reads-a-preset) | 성공 |
| [프리셋 조회 권한을 받은 사용자가 모델 정의와 런타임 파라미터 값이 채워진 프리셋을 id 로 읽으면, 그 프리셋이 옵니다](#reading-a-preset-reader-reads-a-preset-with-a-model-definition) | 성공 |
| [아무 권한도 받지 않은 사용자가 심은 프리셋 하나를 id 로 읽으려 하면, 권한이 없다는 이유로 거부됩니다](#reading-a-user-granted-nothing-reads-no-preset) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-a-preset-reader-purges-none-of-several-presets) | 성공 |
| [superadmin 이 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-purging-several-presets-answers-for-the-missing-one) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [프리셋 영구 삭제 권한을 받은 사용자가 심은 프리셋 하나를 purge 하면, 그 프리셋의 id 가 옵니다](#retiring-a-user-granted-hard-delete-purges-a-preset) | 성공 |
| [프리셋 조회 권한만 받은 사용자가 심은 프리셋 하나를 purge 하려 하면, 권한이 없다는 이유로 거부됩니다](#retiring-a-preset-reader-purges-no-preset) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [프리셋 조회 권한을 받은 사용자가 프리셋을 기준으로 걸러 훑으면, 심은 프리셋이 모두 옵니다](#searching-a-preset-reader-searches-every-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 훑으려 하면, 권한이 없다는 이유로 거부됩니다](#searching-a-user-granted-nothing-searches-no-preset) | 거부 |

**search_resource_slots**

| 시나리오 | 판정 |
|---|---|
| [프리셋 조회 권한을 받은 사용자가 프리셋이 두는 자원 슬롯을 기준으로 걸러 훑으면, 그 슬롯이 옵니다](#searching_slots-a-preset-reader-searches-the-slots-of-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋이 두는 자원 슬롯을 훑으려 하면, 권한이 없다는 이유로 거부됩니다](#searching_slots-a-user-granted-nothing-searches-no-slots) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-a-preset-reader-edits-none-of-several-presets) | 성공 |
| [superadmin 이 프리셋 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk-the-superadmin-edits-several-presets-at-once) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [프리셋 수정 권한을 받은 사용자가 심은 프리셋 하나의 설명을 고치면, 새 설명이 들어간 프리셋이 옵니다](#updating-a-user-granted-update-edits-a-preset) | 성공 |
| [프리셋 조회 권한만 받은 사용자가 심은 프리셋 하나의 설명을 고치려 하면, 권한이 없다는 이유로 거부됩니다](#updating-a-preset-reader-edits-no-preset) | 거부 |

### batch_load_by_ids

<a id="batch_loading-a-preset-reader-loads-the-presets-by-id"></a>

#### [a-preset-reader-loads-the-presets-by-id](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_batch_loading.py): pass

프리셋 조회 권한을 받은 사용자가 심은 프리셋 여럿을 id 로 일괄 조회하면, 입력 순서대로 그 프리셋들이 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.batch_load_by_ids: user-1 이 심은 프리셋 2개를 id 로 일괄 조회합니다

Then

- 심은 프리셋이 입력 순서대로 전체가 옵니다
  - length = 2
  - [0].id: 미리 저장한 프리셋의 id 와 같다
  - [0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - [0].runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - [0].name = 'preset-1'
  - [0].description = '미리 저장한 프리셋'
  - [0].rank = 100
  - [0].cluster.cluster_mode = 'single-node'
  - [0].cluster.cluster_size = 1
  - [0].resource.resource_opts = []
  - [0].execution.image_id: 미리 정한 이미지 id
  - [0].execution.startup_command = None
  - [0].execution.bootstrap_script = None
  - [0].execution.environ = []
  - [0].deployment_defaults.open_to_public = None
  - [0].deployment_defaults.replica_count = 1
  - [0].deployment_defaults.revision_history_limit = None
  - [0].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - [0].deployment_defaults.deployment_strategy_spec = {}
  - [0].model_definition = None
  - [0].preset_values count = 0
  - [0].created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - [0].updated_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - [1].id: 미리 저장한 프리셋의 id 와 같다
  - [1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - [1].runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - [1].name = 'preset-2'
  - [1].description = '미리 저장한 프리셋'
  - [1].rank = 200
  - [1].cluster.cluster_mode = 'single-node'
  - [1].cluster.cluster_size = 1
  - [1].resource.resource_opts = []
  - [1].execution.image_id: 미리 정한 이미지 id
  - [1].execution.startup_command = None
  - [1].execution.bootstrap_script = None
  - [1].execution.environ = []
  - [1].deployment_defaults.open_to_public = None
  - [1].deployment_defaults.replica_count = 1
  - [1].deployment_defaults.revision_history_limit = None
  - [1].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - [1].deployment_defaults.deployment_strategy_spec = {}
  - [1].model_definition = None
  - [1].preset_values count = 0
  - [1].created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - [1].updated_at: 미리 저장한 프리셋이 만들어진 시각와 같다

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-for-each-preset"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-each-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 심은 프리셋 여럿을 id 로 일괄 조회하면, 호출은 성공하되 항목마다 권한 부족으로 거부가 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 프리셋을 읽을 권한이 없는 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DeploymentRevisionPresetAdapter.batch_load_by_ids: user-1 이 심은 프리셋 2개를 id 로 일괄 조회합니다

Then

- 항목마다 권한 부족으로 거부가 옵니다
  - length = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### create

<a id="creating-the-superadmin-makes-a-preset"></a>

#### [the-superadmin-makes-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_creating.py): pass

전역 권한으로만 만들 수 있는 프리셋을 superadmin 이 만들면, 만든 프리셋이 옵니다. 이 행의 요청 사용자는 전역 권한이 필요한 호출이라 superadmin 입니다

Given

- 변형 하나와 그것으로 프리셋을 만들 superadmin 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.create: user-1 이 변형으로 프리셋 하나를 만듭니다

Then

- 만든 프리셋이 전체가 응답으로 옵니다
  - preset.id: 건너뜀: the database generates it
  - preset.entity_id: 건너뜀: the database generates it
  - preset.runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - preset.name = 'created-preset'
  - preset.description = 'a preset made by this run'
  - preset.rank: 순위가 매겨진 값
  - preset.cluster.cluster_mode = 'single-node'
  - preset.cluster.cluster_size = 1
  - preset.resource.resource_opts = []
  - preset.execution.image_id: 미리 정한 이미지 id
  - preset.execution.startup_command = None
  - preset.execution.bootstrap_script = None
  - preset.execution.environ = []
  - preset.deployment_defaults.open_to_public = None
  - preset.deployment_defaults.replica_count = 1
  - preset.deployment_defaults.revision_history_limit = None
  - preset.deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - preset.deployment_defaults.deployment_strategy_spec = {}
  - preset.model_definition = None
  - preset.preset_values = []
  - preset.created_at: 이 실행이 쓴 시각
  - preset.updated_at: 이 실행이 쓴 시각

<a id="creating-a-preset-reader-makes-no-preset"></a>

#### [a-preset-reader-makes-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_creating.py): pass

프리셋 조회 권한만 받은 사용자가 프리셋을 만들려 하면, 전역 권한이 없다는 이유로 거부됩니다

Given

- 변형 하나와 그것으로 프리셋을 만들 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.create: user-1 이 변형으로 프리셋 하나를 만듭니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### get

<a id="reading-a-preset-reader-reads-a-preset"></a>

#### [a-preset-reader-reads-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_reading.py): pass

프리셋 조회 권한을 받은 사용자가 심은 프리셋 하나를 id 로 읽으면, 그 프리셋이 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.get: user-1 이 심은 프리셋 하나를 id 로 읽습니다

Then

- 읽은 프리셋이 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - name = 'preset-1'
  - description = '미리 저장한 프리셋'
  - rank = 100
  - cluster.cluster_mode = 'single-node'
  - cluster.cluster_size = 1
  - resource.resource_opts = []
  - execution.image_id: 미리 정한 이미지 id
  - execution.startup_command = None
  - execution.bootstrap_script = None
  - execution.environ = []
  - deployment_defaults.open_to_public = None
  - deployment_defaults.replica_count = 1
  - deployment_defaults.revision_history_limit = None
  - deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - deployment_defaults.deployment_strategy_spec = {}
  - model_definition = None
  - preset_values count = 0
  - created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - updated_at: 미리 저장한 프리셋이 만들어진 시각와 같다

<a id="reading-a-preset-reader-reads-a-preset-with-a-model-definition"></a>

#### [a-preset-reader-reads-a-preset-with-a-model-definition](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_reading.py): pass

프리셋 조회 권한을 받은 사용자가 모델 정의와 런타임 파라미터 값이 채워진 프리셋을 id 로 읽으면, 그 프리셋이 옵니다

Given

- 모델 정의와 런타임 파라미터 값이 채워진 배포 리비전 프리셋 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 런타임 파라미터 preset-1: 대상 env, 값 종류 str
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트, 모델 정의가 채워져 있다, 런타임 파라미터 값이 채워져 있다
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.get: user-1 이 심은 프리셋 하나를 id 로 읽습니다

Then

- 읽은 프리셋이 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - name = 'preset-2'
  - description = '미리 저장한 프리셋'
  - rank = 100
  - cluster.cluster_mode = 'single-node'
  - cluster.cluster_size = 1
  - resource.resource_opts = []
  - execution.image_id: 미리 정한 이미지 id
  - execution.startup_command = None
  - execution.bootstrap_script = None
  - execution.environ = []
  - deployment_defaults.open_to_public = None
  - deployment_defaults.replica_count = 1
  - deployment_defaults.revision_history_limit = None
  - deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - deployment_defaults.deployment_strategy_spec = {}
  - model_definition = PresetModelDefinitionInfoDTO(models=[PresetModelConfigInfoDTO(name='preset-model', model_path='/models/preset-model', service=None, metadata=None)])
  - preset_values count = 1
  - preset_values[0].preset_id: 그 값이 걸린 런타임 파라미터의 id 와 같다
  - preset_values[0].value = 'preset-value'
  - created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - updated_at: 미리 저장한 프리셋이 만들어진 시각와 같다

<a id="reading-a-user-granted-nothing-reads-no-preset"></a>

#### [a-user-granted-nothing-reads-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_reading.py): pass

아무 권한도 받지 않은 사용자가 심은 프리셋 하나를 id 로 읽으려 하면, 권한이 없다는 이유로 거부됩니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 프리셋을 읽을 권한이 없는 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DeploymentRevisionPresetAdapter.get: user-1 이 심은 프리셋 하나를 id 로 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk-a-preset-reader-purges-none-of-several-presets"></a>

#### [a-preset-reader-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_purge: user-1 이 프리셋 2개를 한 번에 purge 합니다

Then

- 처리된 프리셋 없이 프리셋이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 프리셋의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 프리셋의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-purging-several-presets-answers-for-the-missing-one"></a>

#### [purging-several-presets-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

superadmin 이 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 superadmin 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_purge: user-1 이 프리셋 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 프리셋이 모두 설명 '미리 저장한 프리셋'으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].description = '미리 저장한 프리셋'
  - successes[1].id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].description = '미리 저장한 프리셋'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### purge

<a id="retiring-a-user-granted-hard-delete-purges-a-preset"></a>

#### [a-user-granted-hard-delete-purges-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_retiring.py): pass

프리셋 영구 삭제 권한을 받은 사용자가 심은 프리셋 하나를 purge 하면, 그 프리셋의 id 가 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.purge: user-1 이 심은 프리셋 하나를 purge 합니다

Then

- purge 한 프리셋의 id 가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다

<a id="retiring-a-preset-reader-purges-no-preset"></a>

#### [a-preset-reader-purges-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_retiring.py): pass

프리셋 조회 권한만 받은 사용자가 심은 프리셋 하나를 purge 하려 하면, 권한이 없다는 이유로 거부됩니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.purge: user-1 이 심은 프리셋 하나를 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search

<a id="searching-a-preset-reader-searches-every-preset"></a>

#### [a-preset-reader-searches-every-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching.py): pass

프리셋 조회 권한을 받은 사용자가 프리셋을 기준으로 걸러 훑으면, 심은 프리셋이 모두 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명, 이름이 다른 프리셋 하나가 더 있고
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 other-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.search: user-1 이 프리셋을 하나의 기준으로 걸러 순서와 함께 훑습니다

Then

- 기준이 제외하는 프리셋은 오지 않고, 심은 프리셋이 전체가 응답으로 옵니다
  - total_count = 2
  - items count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 저장한 프리셋의 id 와 같다
  - items[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - items[0].runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - items[0].name = 'preset-1'
  - items[0].description = '미리 저장한 프리셋'
  - items[0].rank = 100
  - items[0].cluster.cluster_mode = 'single-node'
  - items[0].cluster.cluster_size = 1
  - items[0].resource.resource_opts = []
  - items[0].execution.image_id: 미리 정한 이미지 id
  - items[0].execution.startup_command = None
  - items[0].execution.bootstrap_script = None
  - items[0].execution.environ = []
  - items[0].deployment_defaults.open_to_public = None
  - items[0].deployment_defaults.replica_count = 1
  - items[0].deployment_defaults.revision_history_limit = None
  - items[0].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - items[0].deployment_defaults.deployment_strategy_spec = {}
  - items[0].model_definition = None
  - items[0].preset_values count = 0
  - items[0].created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - items[0].updated_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - items[1].id: 미리 저장한 프리셋의 id 와 같다
  - items[1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - items[1].runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - items[1].name = 'preset-2'
  - items[1].description = '미리 저장한 프리셋'
  - items[1].rank = 200
  - items[1].cluster.cluster_mode = 'single-node'
  - items[1].cluster.cluster_size = 1
  - items[1].resource.resource_opts = []
  - items[1].execution.image_id: 미리 정한 이미지 id
  - items[1].execution.startup_command = None
  - items[1].execution.bootstrap_script = None
  - items[1].execution.environ = []
  - items[1].deployment_defaults.open_to_public = None
  - items[1].deployment_defaults.replica_count = 1
  - items[1].deployment_defaults.revision_history_limit = None
  - items[1].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - items[1].deployment_defaults.deployment_strategy_spec = {}
  - items[1].model_definition = None
  - items[1].preset_values count = 0
  - items[1].created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - items[1].updated_at: 미리 저장한 프리셋이 만들어진 시각와 같다

<a id="searching-a-user-granted-nothing-searches-no-preset"></a>

#### [a-user-granted-nothing-searches-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching.py): pass

아무 권한도 받지 않은 사용자가 프리셋을 훑으려 하면, 권한이 없다는 이유로 거부됩니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 프리셋을 읽을 권한이 없는 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DeploymentRevisionPresetAdapter.search: user-1 이 프리셋을 하나의 기준으로 걸러 순서와 함께 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_resource_slots

<a id="searching_slots-a-preset-reader-searches-the-slots-of-a-preset"></a>

#### [a-preset-reader-searches-the-slots-of-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching_slots.py): pass

프리셋 조회 권한을 받은 사용자가 프리셋이 두는 자원 슬롯을 기준으로 걸러 훑으면, 그 슬롯이 옵니다

Given

- 슬롯 유형 둘과 그 슬롯을 두는 프리셋 둘 (미리 저장한 프리셋), 그것을 읽을 수 있는 사용자 한 명, 같은 프리셋에 슬롯 유형이 다른 슬롯 하나가 더 걸려 있고, 슬롯 하나가 다른 프리셋에 걸려 있고
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-1: cpu 슬롯 하나를 두려 한다
  - 배포 리비전 프리셋 preset-1: mem 슬롯 하나를 두려 한다
  - 배포 리비전 프리셋 other-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 other-1: cpu 슬롯 하나를 두려 한다
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.search_resource_slots: user-1 이 프리셋이 두는 자원 슬롯을 하나의 기준으로 걸러 훑습니다

Then

- 기준이 제외하는 슬롯과 다른 프리셋에 걸린 슬롯은 오지 않고, 프리셋이 두는 슬롯이 양과 함께 옵니다
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].slot_name = 'cpu'
  - items[0].quantity = Decimal('4')

<a id="searching_slots-a-user-granted-nothing-searches-no-slots"></a>

#### [a-user-granted-nothing-searches-no-slots](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching_slots.py): pass

아무 권한도 받지 않은 사용자가 프리셋이 두는 자원 슬롯을 훑으려 하면, 권한이 없다는 이유로 거부됩니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 프리셋을 읽을 권한이 없는 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DeploymentRevisionPresetAdapter.search_resource_slots: user-1 이 프리셋이 두는 자원 슬롯을 하나의 기준으로 걸러 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk-a-preset-reader-edits-none-of-several-presets"></a>

#### [a-preset-reader-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_update: user-1 이 프리셋 2개의 설명을 한 번에 수정합니다

Then

- 처리된 프리셋 없이 프리셋이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 프리셋의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 프리셋의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

superadmin 이 프리셋 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 superadmin 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.partial_bulk_update: user-1 이 프리셋 2개의 설명을 한 번에 수정합니다

Then

- 프리셋이 모두 설명 '한 번에 수정한 설명'으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].description = '한 번에 수정한 설명'
  - successes[1].id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].description = '한 번에 수정한 설명'
  - failed = []

### update

<a id="updating-a-user-granted-update-edits-a-preset"></a>

#### [a-user-granted-update-edits-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_updating.py): pass

프리셋 수정 권한을 받은 사용자가 심은 프리셋 하나의 설명을 고치면, 새 설명이 들어간 프리셋이 옵니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.update: user-1 이 심은 프리셋 하나의 설명을 고칩니다

Then

- 고친 프리셋이 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - runtime_variant_id: 프리셋이 놓인 변형의 id 와 같다
  - name = 'preset-1'
  - description = '한 번에 수정한 설명'
  - rank = 100
  - cluster.cluster_mode = 'single-node'
  - cluster.cluster_size = 1
  - resource.resource_opts = []
  - execution.image_id: 미리 정한 이미지 id
  - execution.startup_command = None
  - execution.bootstrap_script = None
  - execution.environ = []
  - deployment_defaults.open_to_public = None
  - deployment_defaults.replica_count = 1
  - deployment_defaults.revision_history_limit = None
  - deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - deployment_defaults.deployment_strategy_spec = {}
  - model_definition = None
  - preset_values count = 0
  - created_at: 미리 저장한 프리셋이 만들어진 시각와 같다
  - updated_at: 이 실행이 쓴 시각

<a id="updating-a-preset-reader-edits-no-preset"></a>

#### [a-preset-reader-edits-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_updating.py): pass

프리셋 조회 권한만 받은 사용자가 심은 프리셋 하나의 설명을 고치려 하면, 권한이 없다는 이유로 거부됩니다

Given

- 변형 하나와 그 변형의 배포 리비전 프리셋 2개, 그리고 일반 사용자 한 명
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트
  - 배포 리비전 프리셋 preset-2: 단일 노드, 복제본 하나, 롤링 업데이트
  - 도메인 home-1
  - public 에서 deployment_preset 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: deployment_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- DeploymentRevisionPresetAdapter.update: user-1 이 심은 프리셋 하나의 설명을 고칩니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

