## artifact

[배경](/src/ai/backend/manager/api/adapters/artifact/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/artifact/adapter.py)

시나리오: 미완성 21 / 25

- ops 구성 (9)
  - batch_load_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_revisions_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - get_revision: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_delete: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_restore: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - restore: 대표 성공 ✓ · 대표 거부 ✓
  - search_revisions_of_artifact_gql: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
- 직접 구현 (16)
  - admin_search: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - admin_search_gql: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - approve_revision: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - cancel_import: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - cleanup_revision: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - delegate_import_batch: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - delegate_scan: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - delete_artifacts: 성공 있음 1 · 거부 있음 1 (global_scope)
  - get: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - import_revision: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - reject_revision: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - restore_artifacts: 성공 있음 1 · 거부 없음 (global_scope): SCENARIO-GAP
  - retrieve_models: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - scan: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - search_revisions_gql: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - update: 성공 있음 1 · 거부 있음 2 (single_entity)

**delete**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아티팩트를 soft delete 하면, 삭제됨 상태의 아티팩트가 옵니다](#deleting-the-superadmin-soft-deletes-an-artifact) | 성공 |
| [아무 권한도 받지 않은 사용자는 아티팩트를 soft delete 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-soft-delete-an-artifact) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-artifacts) | 성공 |
| [아티팩트 둘과 존재하지 않는 id 하나를 한 번에 soft delete 하면, 둘은 삭제됨 상태로 오고 존재하지 않는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 아티팩트 여럿을 한 번에 restore 하면, 모두 살아 있는 상태로 옵니다](#partial_bulk_deleting-restoring-several-brings-them-back) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-artifacts) | 성공 |
| [superadmin 이 아티팩트 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-artifacts-at-once) | 성공 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 아티팩트를 restore 하면, 살아 있는 상태의 아티팩트가 옵니다](#deleting-restoring-brings-an-artifact-back) | 성공 |
| [아무 권한도 받지 않은 사용자는 아티팩트를 restore 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-restore-an-artifact) | 거부 |

**delete_artifacts**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아티팩트 여럿을 id 목록으로 soft delete 하면, 모두 삭제됨 상태로 옵니다](#bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids) | 성공 |
| [superadmin 이 아닌 사용자는 아티팩트 여럿을 id 목록으로 soft delete 할 수 없고, 역할로 거부됩니다](#bulk_deleting-a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids) | 거부 |

**restore_artifacts**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 soft delete 된 아티팩트 여럿을 id 목록으로 restore 하면, 모두 살아 있는 상태로 옵니다](#bulk_deleting-the-superadmin-restores-artifacts-by-ids) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아티팩트의 설명을 변경하면, 새 설명을 담은 아티팩트가 응답으로 옵니다](#editing-the-superadmin-edits-an-artifact) | 성공 |
| [soft delete 된 아티팩트는 superadmin 이라도 수정할 수 없고, 대상이 없다는 것으로 거부됩니다](#editing-a-soft-deleted-artifact-is-not-edited) | 거부 |
| [아무 권한도 받지 않은 사용자는 아티팩트를 수정할 수 없습니다](#editing-a-user-granted-nothing-may-not-edit-an-artifact) | 거부 |

### delete

<a id="deleting-the-superadmin-soft-deletes-an-artifact"></a>

#### [the-superadmin-soft-deletes-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

superadmin 이 아티팩트를 soft delete 하면, 삭제됨 상태의 아티팩트가 옵니다

Given

- 아티팩트 하나와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delete: user-1이 artifact-1을 soft delete 합니다

Then

- 미리 저장한 아티팩트 전체가 반환됩니다
  - name = 'artifact-1'
  - type = <ArtifactType.MODEL: 'MODEL'>
  - description = '이미 있던 아티팩트'
  - registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - readonly = False
  - extra = None
  - revisions = []
  - id: 미리 저장한 아티팩트의 id 와 같다
  - entity_id: 미리 저장한 아티팩트의 id 와 같다
  - registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - scanned_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-an-artifact"></a>

#### [a-user-granted-nothing-may-not-soft-delete-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 아티팩트를 soft delete 할 수 없습니다

Given

- 아티팩트 하나와 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delete: user-1이 artifact-1을 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-artifacts"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아티팩트 2개와 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.partial_bulk_delete: user-1이 아티팩트 2개를 한 번에 soft delete 합니다

Then

- 처리된 아티팩트 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 아티팩트의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 아티팩트의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

아티팩트 둘과 존재하지 않는 id 하나를 한 번에 soft delete 하면, 둘은 삭제됨 상태로 오고 존재하지 않는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 아티팩트 2개와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.partial_bulk_delete: user-1이 아티팩트 2개와 존재하지 않는 id 하나를 한 번에 soft delete 합니다

Then

- 대상 아티팩트가 모두 처리된 모습으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].name = 'artifact-1'
  - successes[0].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[0].description = '이미 있던 아티팩트'
  - successes[0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - successes[0].readonly = False
  - successes[0].extra = None
  - successes[0].revisions = []
  - successes[0].id: 미리 저장한 아티팩트의 id 와 같다
  - successes[0].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - successes[0].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[0].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[0].scanned_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].name = 'artifact-2'
  - successes[1].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[1].description = '이미 있던 아티팩트'
  - successes[1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - successes[1].readonly = False
  - successes[1].extra = None
  - successes[1].revisions = []
  - successes[1].id: 미리 저장한 아티팩트의 id 와 같다
  - successes[1].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - successes[1].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[1].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[1].scanned_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

soft delete 된 아티팩트 여럿을 한 번에 restore 하면, 모두 살아 있는 상태로 옵니다

Given

- 아티팩트 2개와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.partial_bulk_restore: user-1이 아티팩트 2개를 한 번에 soft delete 했다가 한 번에 restore 합니다

Then

- 대상 아티팩트가 모두 처리된 모습으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].name = 'artifact-1'
  - successes[0].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[0].description = '이미 있던 아티팩트'
  - successes[0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[0].readonly = False
  - successes[0].extra = None
  - successes[0].revisions = []
  - successes[0].id: 미리 저장한 아티팩트의 id 와 같다
  - successes[0].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - successes[0].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[0].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[0].scanned_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].name = 'artifact-2'
  - successes[1].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[1].description = '이미 있던 아티팩트'
  - successes[1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[1].readonly = False
  - successes[1].extra = None
  - successes[1].revisions = []
  - successes[1].id: 미리 저장한 아티팩트의 id 와 같다
  - successes[1].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - successes[1].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[1].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[1].scanned_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-artifacts"></a>

#### [a-user-granted-nothing-edits-none-of-several-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아티팩트 2개와 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.partial_bulk_update: user-1이 아티팩트 2개의 설명을 한 번에 수정합니다

Then

- 처리된 아티팩트 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 아티팩트의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 아티팩트의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-artifacts-at-once"></a>

#### [the-superadmin-edits-several-artifacts-at-once](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_editing.py): pass

superadmin 이 아티팩트 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 아티팩트 2개와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.partial_bulk_update: user-1이 아티팩트 2개의 설명을 한 번에 수정합니다

Then

- 대상 아티팩트가 모두 처리된 모습으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].name = 'artifact-1'
  - successes[0].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[0].readonly = False
  - successes[0].extra = None
  - successes[0].revisions = []
  - successes[0].id: 미리 저장한 아티팩트의 id 와 같다
  - successes[0].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - successes[0].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[0].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[0].scanned_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].name = 'artifact-2'
  - successes[1].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[1].readonly = False
  - successes[1].extra = None
  - successes[1].revisions = []
  - successes[1].id: 미리 저장한 아티팩트의 id 와 같다
  - successes[1].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - successes[1].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[1].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - successes[1].scanned_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### restore

<a id="deleting-restoring-brings-an-artifact-back"></a>

#### [restoring-brings-an-artifact-back](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

soft delete 된 아티팩트를 restore 하면, 살아 있는 상태의 아티팩트가 옵니다

Given

- 아티팩트 하나와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.restore: user-1이 artifact-1을 soft delete 했다가 restore 합니다

Then

- 미리 저장한 아티팩트 전체가 반환됩니다
  - name = 'artifact-1'
  - type = <ArtifactType.MODEL: 'MODEL'>
  - description = '이미 있던 아티팩트'
  - registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - readonly = False
  - extra = None
  - revisions = []
  - id: 미리 저장한 아티팩트의 id 와 같다
  - entity_id: 미리 저장한 아티팩트의 id 와 같다
  - registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - scanned_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-restore-an-artifact"></a>

#### [a-user-granted-nothing-may-not-restore-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 아티팩트를 restore 할 수 없습니다

Given

- 아티팩트 하나와 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.restore: user-1이 artifact-1을 restore 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### delete_artifacts

<a id="bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids"></a>

#### [the-superadmin-soft-deletes-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

superadmin 이 아티팩트 여럿을 id 목록으로 soft delete 하면, 모두 삭제됨 상태로 옵니다

Given

- 아티팩트 2개와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delete_artifacts: user-1이 아티팩트 2개를 id 목록으로 soft delete 합니다

Then

- 대상 아티팩트가 모두 처리된 모습으로 옵니다
  - count = 2
  - [0].name = 'artifact-1'
  - [0].type = <ArtifactType.MODEL: 'MODEL'>
  - [0].description = '이미 있던 아티팩트'
  - [0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - [0].readonly = False
  - [0].extra = None
  - [0].revisions = []
  - [0].id: 미리 저장한 아티팩트의 id 와 같다
  - [0].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [0].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [0].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [0].scanned_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1].name = 'artifact-2'
  - [1].type = <ArtifactType.MODEL: 'MODEL'>
  - [1].description = '이미 있던 아티팩트'
  - [1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - [1].readonly = False
  - [1].extra = None
  - [1].revisions = []
  - [1].id: 미리 저장한 아티팩트의 id 와 같다
  - [1].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [1].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [1].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [1].scanned_at: 이 실행이 쓴 시각
  - [1].updated_at: 이 실행이 쓴 시각

<a id="bulk_deleting-a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids"></a>

#### [a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

superadmin 이 아닌 사용자는 아티팩트 여럿을 id 목록으로 soft delete 할 수 없고, 역할로 거부됩니다

Given

- 아티팩트 2개와 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delete_artifacts: user-1이 아티팩트 2개를 id 목록으로 soft delete 합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### restore_artifacts

<a id="bulk_deleting-the-superadmin-restores-artifacts-by-ids"></a>

#### [the-superadmin-restores-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

superadmin 이 soft delete 된 아티팩트 여럿을 id 목록으로 restore 하면, 모두 살아 있는 상태로 옵니다

Given

- 아티팩트 2개와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.restore_artifacts: user-1이 아티팩트 2개를 id 목록으로 soft delete 했다가 restore 합니다

Then

- 대상 아티팩트가 모두 처리된 모습으로 옵니다
  - count = 2
  - [0].name = 'artifact-1'
  - [0].type = <ArtifactType.MODEL: 'MODEL'>
  - [0].description = '이미 있던 아티팩트'
  - [0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [0].readonly = False
  - [0].extra = None
  - [0].revisions = []
  - [0].id: 미리 저장한 아티팩트의 id 와 같다
  - [0].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [0].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [0].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [0].scanned_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1].name = 'artifact-2'
  - [1].type = <ArtifactType.MODEL: 'MODEL'>
  - [1].description = '이미 있던 아티팩트'
  - [1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [1].readonly = False
  - [1].extra = None
  - [1].revisions = []
  - [1].id: 미리 저장한 아티팩트의 id 와 같다
  - [1].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [1].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [1].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [1].scanned_at: 이 실행이 쓴 시각
  - [1].updated_at: 이 실행이 쓴 시각

### update

<a id="editing-the-superadmin-edits-an-artifact"></a>

#### [the-superadmin-edits-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

superadmin 이 아티팩트의 설명을 변경하면, 새 설명을 담은 아티팩트가 응답으로 옵니다

Given

- 아티팩트 하나와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.update: user-1이 artifact-1의 설명을 수정합니다

Then

- 미리 저장한 아티팩트 전체가 반환됩니다
  - name = 'artifact-1'
  - type = <ArtifactType.MODEL: 'MODEL'>
  - description = '수정한 설명'
  - registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - readonly = False
  - extra = None
  - revisions = []
  - id: 미리 저장한 아티팩트의 id 와 같다
  - entity_id: 미리 저장한 아티팩트의 id 와 같다
  - registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - scanned_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-soft-deleted-artifact-is-not-edited"></a>

#### [a-soft-deleted-artifact-is-not-edited](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

soft delete 된 아티팩트는 superadmin 이라도 수정할 수 없고, 대상이 없다는 것으로 거부됩니다

Given

- 아티팩트 하나와 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.update: user-1이 artifact-1을 soft delete 한 뒤 설명을 수정합니다

Then

- 거부됩니다
  - 거부: ArtifactNotFoundError

<a id="editing-a-user-granted-nothing-may-not-edit-an-artifact"></a>

#### [a-user-granted-nothing-may-not-edit-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

아무 권한도 받지 않은 사용자는 아티팩트를 수정할 수 없습니다

Given

- 아티팩트 하나와 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.update: user-1이 artifact-1의 설명을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

