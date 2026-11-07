## runtime_variant

[배경](/src/ai/backend/manager/api/adapters/runtime_variant/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/runtime_variant/adapter.py)

시나리오: 미완성 3 / 10

- ops 구성 (7)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - resolve_by_name: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (3)
  - bulk_delete: 성공 있음 3 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - partial_bulk_purge: 성공 있음 2 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - purge: 성공 있음 2 · 거부 있음 2 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록을 주면 빈 응답이 반환됩니다. 하위 계층을 호출하지 않습니다](#reading-an-empty-id-list-answers-empty-without-a-call) | 성공 |
| [있는 id 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다](#reading-variants-read-by-many-ids-come-back-in-the-order-asked) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 이름과 설명을 함께 지정해 생성하면, 지정한 값이 그대로 담긴 노드가 반환됩니다](#creating-a-variant-made-with-a-description-carries-it-back) | 성공 |
| [superadmin 이 이름만 지정해 인퍼런스 런타임 종류를 생성하면, 설명은 비고 vfolder 설정 파일은 읽지 않으며 모델 정의는 코드가 정해 둔 기본값인 노드가 반환됩니다](#creating-the-superadmin-makes-a-variant-with-a-name-alone) | 성공 |
| [superadmin 이 아닌 사용자가 인퍼런스 런타임 종류를 생성하면 역할 부족으로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-variant) | 거부 |
| [같은 이름의 인퍼런스 런타임 종류가 이미 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부됩니다](#creating-a-variant-name-already-taken-is-refused) | 거부 |
| [권한 검사를 꺼도 superadmin 이 아니면 인퍼런스 런타임 종류를 생성하지 못합니다](#creating-turning-enforcement-off-does-not-let-a-user-create-a-variant) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 id 로 조회하면, 그 인퍼런스 런타임 종류 전체가 반환됩니다. 이 조회는 인증만 확인합니다](#reading-a-user-granted-nothing-reads-a-variant-by-id) | 성공 |
| [존재하지 않는 id 로 조회하면 거부됩니다. 권한을 요구할 대상이 없으므로, 없는 것인지 접근하지 못하는 것인지는 응답으로 드러나지 않습니다](#reading-reading-a-variant-id-nothing-answers-to-is-refused) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 인퍼런스 런타임 종류 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-variants) | 성공 |
| [superadmin 이 인퍼런스 런타임 종류 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-variants-at-once) | 성공 |

**resolve_by_name**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 이름을 id 로 변환하면 그 인퍼런스 런타임 종류의 id 가 반환됩니다](#reading-a-variant-name-resolves-to-its-id-for-any-user) | 성공 |
| [존재하지 않는 이름을 id 로 변환하면 거부됩니다. 변환한 대상에 권한 검사가 뒤따르므로 존재하지 않는 이름과 접근하지 못하는 이름이 같은 방식으로 거부됩니다](#reading-resolving-a-variant-name-nothing-answers-to-is-refused) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [인퍼런스 런타임 종류 여럿 중 하나의 이름을 필터로 조회하면, 응답에는 그 이름의 인퍼런스 런타임 종류만 남습니다](#searching-a-name-filter-narrows-the-answer-to-the-variant-it-names) | 성공 |
| [인퍼런스 런타임 종류 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계됩니다](#searching-a-user-granted-nothing-counts-every-variant-laid) | 성공 |
| [인퍼런스 런타임 종류 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답합니다](#searching-omitting-the-page-size-answers-ten-variants-and-a-next-page) | 성공 |
| [인퍼런스 런타임 종류를 읽을 수 있는 사용자가 읽을 수 없는 배포를 사용 필터로 지정해 조회하면, 권한 부족으로 거부됩니다](#searching-naming-a-deployment-the-caller-cannot-read-is-refused) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환됩니다](#editing-an-edit-giving-no-value-changes-nothing) | 성공 |
| [설명이 있는 인퍼런스 런타임 종류에 설명을 비우는 수정을 하면, 설명이 없어집니다](#editing-clearing-a-variant-description-leaves-it-empty) | 성공 |
| [superadmin 이 인퍼런스 런타임 종류의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 유지됩니다](#editing-renaming-a-variant-leaves-its-description-alone) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 인퍼런스 런타임 종류를 수정할 수 있습니다](#editing-turning-enforcement-off-lets-a-user-edit-a-variant) | 성공 |
| [아무 권한도 없는 사용자가 존재하지 않는 id 를 수정하면 대상 없음이 아니라 권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문입니다](#editing-a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission) | 거부 |
| [아무 권한도 없는 사용자가 인퍼런스 런타임 종류를 수정하면 권한 부족으로 거부됩니다. 인퍼런스 런타임 종류는 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없습니다](#editing-a-user-granted-nothing-may-not-edit-a-variant) | 거부 |
| [인퍼런스 런타임 종류 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름 중복으로 거부됩니다. 생성할 때와 달리 저장소의 제약 위반이 그대로 전파됩니다](#editing-renaming-a-variant-to-a-name-already-taken-is-refused) | 거부 |
| [superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다](#editing-the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found) | 거부 |

**bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 인퍼런스 런타임 종류 둘을 한 번에 삭제하면, 둘 다 실패 목록에 반환되고 아무것도 삭제되지 않습니다](#retiring-a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete) | 성공 |
| [있는 id 뒤에 없는 id 를 붙여 한 번에 삭제하면, 있는 것은 삭제된 목록에, 없는 id 는 실패 목록에 반환됩니다](#retiring-an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted) | 성공 |
| [superadmin 이 인퍼런스 런타임 종류 둘을 한 번에 삭제하면, 둘 다 삭제된 목록에 반환되고 실패 목록은 비어 있습니다](#retiring-the-superadmin-deletes-many-variants-at-once) | 성공 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 인퍼런스 런타임 종류 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-variants) | 성공 |
| [superadmin 이 인퍼런스 런타임 종류 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 처리된 목록에 오고 없는 id 는 실패 목록에 옵니다](#partial_bulk_purging-purging-several-variants-answers-for-the-missing-one) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 인퍼런스 런타임 종류를 삭제하면 삭제한 인퍼런스 런타임 종류의 id 를 담은 응답이 반환됩니다](#retiring-the-superadmin-deletes-a-variant) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 인퍼런스 런타임 종류를 삭제할 수 있습니다](#retiring-turning-enforcement-off-lets-a-user-delete-a-variant) | 성공 |
| [아무 권한도 없는 사용자가 인퍼런스 런타임 종류를 삭제하면 권한 부족으로 거부됩니다](#retiring-a-user-granted-nothing-may-not-delete-a-variant) | 거부 |
| [superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다](#retiring-deleting-a-variant-id-nothing-answers-to-is-not-found) | 거부 |

### batch_load_by_ids

<a id="reading-an-empty-id-list-answers-empty-without-a-call"></a>

#### [an-empty-id-list-answers-empty-without-a-call](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

빈 id 목록을 주면 빈 응답이 반환됩니다. 하위 계층을 호출하지 않습니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.batch_load_by_ids: user-1이 빈 id 목록으로 조회합니다

Then

- 빈 응답이 반환됩니다
  - items = []

<a id="reading-variants-read-by-many-ids-come-back-in-the-order-asked"></a>

#### [variants-read-by-many-ids-come-back-in-the-order-asked](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

있는 id 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다

Given

- 인퍼런스 런타임 종류 2개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.batch_load_by_ids: user-1이 미리 저장한 2개와 없는 id 하나를 한 번에 조회합니다

Then

- 요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 거부가 담깁니다
  - len(items) = 3
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].name = 'wanted-1'
  - items[0].description = '미리 저장한 인퍼런스 런타임 종류'
  - items[0].reads_vfolder_config_files = False
  - items[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].name = 'other-1'
  - items[1].description = '미리 저장한 인퍼런스 런타임 종류'
  - items[1].reads_vfolder_config_files = False
  - items[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission

### create

<a id="creating-a-variant-made-with-a-description-carries-it-back"></a>

#### [a-variant-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

superadmin 이 이름과 설명을 함께 지정해 생성하면, 지정한 값이 그대로 담긴 노드가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RuntimeVariantAdapter.create: user-1이 vllm 인퍼런스 런타임 종류를 생성합니다

Then

- 생성한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'vllm'
  - description = '새로 지정한 설명'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating-the-superadmin-makes-a-variant-with-a-name-alone"></a>

#### [the-superadmin-makes-a-variant-with-a-name-alone](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

superadmin 이 이름만 지정해 인퍼런스 런타임 종류를 생성하면, 설명은 비고 vfolder 설정 파일은 읽지 않으며 모델 정의는 코드가 정해 둔 기본값인 노드가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RuntimeVariantAdapter.create: user-1이 vllm 인퍼런스 런타임 종류를 생성합니다

Then

- 생성한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'vllm'
  - description = None
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-variant"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

superadmin 이 아닌 사용자가 인퍼런스 런타임 종류를 생성하면 역할 부족으로 거부됩니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RuntimeVariantAdapter.create: user-1이 vllm 인퍼런스 런타임 종류를 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-a-variant-name-already-taken-is-refused"></a>

#### [a-variant-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

같은 이름의 인퍼런스 런타임 종류가 이미 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.create: user-1이 이미 있는 이름 variant-1(으)로 다시 생성합니다

Then

- 거부됩니다
  - 거부: RuntimeVariantConflict

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-variant"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

권한 검사를 꺼도 superadmin 이 아니면 인퍼런스 런타임 종류를 생성하지 못합니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RuntimeVariantAdapter.create: user-1이 vllm 인퍼런스 런타임 종류를 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### get

<a id="reading-a-user-granted-nothing-reads-a-variant-by-id"></a>

#### [a-user-granted-nothing-reads-a-variant-by-id](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

아무 권한도 없는 사용자가 id 로 조회하면, 그 인퍼런스 런타임 종류 전체가 반환됩니다. 이 조회는 인증만 확인합니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.get: user-1이 variant-1(으)로 조회합니다

Then

- 미리 저장한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'variant-1'
  - description = '미리 저장한 인퍼런스 런타임 종류'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading-reading-a-variant-id-nothing-answers-to-is-refused"></a>

#### [reading-a-variant-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

존재하지 않는 id 로 조회하면 거부됩니다. 권한을 요구할 대상이 없으므로, 없는 것인지 접근하지 못하는 것인지는 응답으로 드러나지 않습니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.get: user-1이 존재하지 않는 id 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-variants"></a>

#### [a-user-granted-nothing-edits-none-of-several-variants](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_editing.py): pass

아무 권한도 없는 사용자가 인퍼런스 런타임 종류 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 인퍼런스 런타임 종류 2개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.partial_bulk_update: user-1이 인퍼런스 런타임 종류 2개의 설명을 한 번에 수정합니다

Then

- 처리된 변형 없이 미리 저장한 변형이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 변형의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 변형의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-variants-at-once"></a>

#### [the-superadmin-edits-several-variants-at-once](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_editing.py): pass

superadmin 이 인퍼런스 런타임 종류 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 인퍼런스 런타임 종류 2개와, superadmin 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.partial_bulk_update: user-1이 인퍼런스 런타임 종류 2개의 설명을 한 번에 수정합니다

Then

- 미리 저장한 변형이 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].name = 'wanted-1'
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].reads_vfolder_config_files = False
  - successes[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].name = 'other-1'
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].reads_vfolder_config_files = False
  - successes[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### resolve_by_name

<a id="reading-a-variant-name-resolves-to-its-id-for-any-user"></a>

#### [a-variant-name-resolves-to-its-id-for-any-user](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

아무 권한도 없는 사용자가 이름을 id 로 변환하면 그 인퍼런스 런타임 종류의 id 가 반환됩니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.resolve_by_name: user-1이 이름 variant-1(을)를 id 로 변환합니다

Then

- 미리 저장한 인퍼런스 런타임 종류의 id 가 반환됩니다
  - id: 미리 저장한 인퍼런스 런타임 종류와 같다

<a id="reading-resolving-a-variant-name-nothing-answers-to-is-refused"></a>

#### [resolving-a-variant-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

존재하지 않는 이름을 id 로 변환하면 거부됩니다. 변환한 대상에 권한 검사가 뒤따르므로 존재하지 않는 이름과 접근하지 못하는 이름이 같은 방식으로 거부됩니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.resolve_by_name: user-1이 이름 no-such-variant(을)를 id 로 변환합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### search

<a id="searching-a-name-filter-narrows-the-answer-to-the-variant-it-names"></a>

#### [a-name-filter-narrows-the-answer-to-the-variant-it-names](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

인퍼런스 런타임 종류 여럿 중 하나의 이름을 필터로 조회하면, 응답에는 그 이름의 인퍼런스 런타임 종류만 남습니다

Given

- 인퍼런스 런타임 종류 3개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-2: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.search: user-1이 wanted-1 이름 필터로 조회합니다

Then

- 필터에 맞는 변형 하나만 반환됩니다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-counts-every-variant-laid"></a>

#### [a-user-granted-nothing-counts-every-variant-laid](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

인퍼런스 런타임 종류 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계됩니다

Given

- 인퍼런스 런타임 종류 2개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.search: user-1이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 변형이 모두 집계됩니다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-variants-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-variants-and-a-next-page](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

인퍼런스 런타임 종류 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답합니다

Given

- 인퍼런스 런타임 종류 11개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-2: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-3: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-4: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-5: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-6: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-7: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-8: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-9: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-10: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.search: user-1이 필터 없이 전체를 조회합니다

Then

- 기본 크기의 첫 페이지가 반환됩니다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-naming-a-deployment-the-caller-cannot-read-is-refused"></a>

#### [naming-a-deployment-the-caller-cannot-read-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

인퍼런스 런타임 종류를 읽을 수 있는 사용자가 읽을 수 없는 배포를 사용 필터로 지정해 조회하면, 권한 부족으로 거부됩니다

Given

- 인퍼런스 런타임 종류 2개와, 다른 프로젝트의 배포 하나, 그 배포를 읽을 수 없는 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유
  - 도메인 home-2
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- RuntimeVariantAdapter.search: user-1이 읽을 수 없는 배포를 사용 필터로 지정해 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-an-edit-giving-no-value-changes-nothing"></a>

#### [an-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 variant-1을 변경 값 없이 수정합니다

Then

- 미리 저장한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'variant-1'
  - description = '미리 저장한 인퍼런스 런타임 종류'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-clearing-a-variant-description-leaves-it-empty"></a>

#### [clearing-a-variant-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

설명이 있는 인퍼런스 런타임 종류에 설명을 비우는 수정을 하면, 설명이 없어집니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 variant-1의 설명을 수정합니다

Then

- 미리 저장한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'variant-1'
  - description = None
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-renaming-a-variant-leaves-its-description-alone"></a>

#### [renaming-a-variant-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

superadmin 이 인퍼런스 런타임 종류의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 유지됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 variant-1의 이름을 수정합니다

Then

- 미리 저장한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'renamed'
  - description = '미리 저장한 인퍼런스 런타임 종류'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-variant"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 인퍼런스 런타임 종류를 수정할 수 있습니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 variant-1의 이름을 수정합니다

Then

- 미리 저장한 변형 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'renamed'
  - description = '미리 저장한 인퍼런스 런타임 종류'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

아무 권한도 없는 사용자가 존재하지 않는 id 를 수정하면 대상 없음이 아니라 권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문입니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 존재하지 않는 id 의 이름을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-a-user-granted-nothing-may-not-edit-a-variant"></a>

#### [a-user-granted-nothing-may-not-edit-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

아무 권한도 없는 사용자가 인퍼런스 런타임 종류를 수정하면 권한 부족으로 거부됩니다. 인퍼런스 런타임 종류는 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없습니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 variant-1의 이름을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-renaming-a-variant-to-a-name-already-taken-is-refused"></a>

#### [renaming-a-variant-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

인퍼런스 런타임 종류 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름 중복으로 거부됩니다. 생성할 때와 달리 저장소의 제약 위반이 그대로 전파됩니다

Given

- 인퍼런스 런타임 종류 2개와, superadmin 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 wanted-1의 이름을 other-1(으)로 수정합니다

Then

- 거부됩니다
  - 거부: UniqueConstraintViolationError

<a id="editing-the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.update: user-1이 존재하지 않는 id 의 이름을 수정합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### bulk_delete

<a id="retiring-a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete"></a>

#### [a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

아무 권한도 없는 사용자가 인퍼런스 런타임 종류 둘을 한 번에 삭제하면, 둘 다 실패 목록에 반환되고 아무것도 삭제되지 않습니다

Given

- 인퍼런스 런타임 종류 2개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.bulk_delete: user-1이 2개를 한 번에 삭제합니다

Then

- 미리 저장한 변형 전부가 실패 목록에 반환되고, 삭제된 목록은 비어 있습니다
  - items = []
  - failed[*].id: 미리 저장한 변형들와 같다
  - failed[*].message: 건너뜀: 이유는 문자열로 오고, 문자열은 변경되어도 되는 값입니다
  - deleted_count = 0

<a id="retiring-an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted"></a>

#### [an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

있는 id 뒤에 없는 id 를 붙여 한 번에 삭제하면, 있는 것은 삭제된 목록에, 없는 id 는 실패 목록에 반환됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.bulk_delete: user-1이 variant-1 와 없는 id 를 한 번에 삭제합니다

Then

- 미리 저장한 변형은 삭제된 목록에, 없는 id 는 실패 목록에 반환됩니다
  - items: 미리 저장한 변형와 같다
  - len(failed) = 1
  - failed[0].id: 건너뜀: 호출이 생성한 없는 id 라 미리 알 수 없습니다
  - failed[0].message: 건너뜀: 이유는 문자열로 오고, 문자열은 변경되어도 되는 값입니다
  - deleted_count = 1

<a id="retiring-the-superadmin-deletes-many-variants-at-once"></a>

#### [the-superadmin-deletes-many-variants-at-once](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

superadmin 이 인퍼런스 런타임 종류 둘을 한 번에 삭제하면, 둘 다 삭제된 목록에 반환되고 실패 목록은 비어 있습니다

Given

- 인퍼런스 런타임 종류 2개와, superadmin 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.bulk_delete: user-1이 2개를 한 번에 삭제합니다

Then

- 미리 저장한 변형 전부가 삭제된 목록에 반환되고, 실패 목록은 비어 있습니다
  - items: 미리 저장한 변형들와 같다
  - failed = []
  - deleted_count = 2

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-variants"></a>

#### [a-user-granted-nothing-purges-none-of-several-variants](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_purging.py): pass

아무 권한도 없는 사용자가 인퍼런스 런타임 종류 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 인퍼런스 런타임 종류 2개와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.partial_bulk_purge: user-1이 인퍼런스 런타임 종류 2개를 한 번에 purge 합니다

Then

- 처리된 변형 없이 미리 저장한 변형이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 변형의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 변형의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-variants-answers-for-the-missing-one"></a>

#### [purging-several-variants-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_purging.py): pass

superadmin 이 인퍼런스 런타임 종류 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 처리된 목록에 오고 없는 id 는 실패 목록에 옵니다

Given

- 인퍼런스 런타임 종류 2개와, superadmin 한 명
  - 인퍼런스 런타임 종류 wanted-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 인퍼런스 런타임 종류 other-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.partial_bulk_purge: user-1이 인퍼런스 런타임 종류 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 미리 저장한 변형이 모두 처리된 목록에 오고, 없는 id 는 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].name = 'wanted-1'
  - successes[0].description = '미리 저장한 인퍼런스 런타임 종류'
  - successes[0].reads_vfolder_config_files = False
  - successes[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].name = 'other-1'
  - successes[1].description = '미리 저장한 인퍼런스 런타임 종류'
  - successes[1].reads_vfolder_config_files = False
  - successes[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 건너뜀: 이유는 문자열로 오고, 문자열은 변경되어도 되는 값입니다

### purge

<a id="retiring-the-superadmin-deletes-a-variant"></a>

#### [the-superadmin-deletes-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

superadmin 이 인퍼런스 런타임 종류를 삭제하면 삭제한 인퍼런스 런타임 종류의 id 를 담은 응답이 반환됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.purge: user-1이 variant-1 를 삭제합니다

Then

- 삭제한 변형의 id 가 반환됩니다
  - id: 미리 저장한 변형와 같다

<a id="retiring-turning-enforcement-off-lets-a-user-delete-a-variant"></a>

#### [turning-enforcement-off-lets-a-user-delete-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 인퍼런스 런타임 종류를 삭제할 수 있습니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.purge: user-1이 variant-1 를 삭제합니다

Then

- 삭제한 변형의 id 가 반환됩니다
  - id: 미리 저장한 변형와 같다

<a id="retiring-a-user-granted-nothing-may-not-delete-a-variant"></a>

#### [a-user-granted-nothing-may-not-delete-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

아무 권한도 없는 사용자가 인퍼런스 런타임 종류를 삭제하면 권한 부족으로 거부됩니다

Given

- 인퍼런스 런타임 종류 하나와, 일반 사용자 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.purge: user-1이 variant-1 를 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-deleting-a-variant-id-nothing-answers-to-is-not-found"></a>

#### [deleting-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 인퍼런스 런타임 종류 하나와, superadmin 한 명
  - 인퍼런스 런타임 종류 variant-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 도메인 home-1
  - public 에서 runtime_variant 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: runtime_variant 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- RuntimeVariantAdapter.purge: user-1이 존재하지 않는 id 를 삭제합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

