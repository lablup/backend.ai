## artifact

[배경](/src/ai/backend/manager/api/adapters/artifact/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/artifact/adapter.py)

시나리오: 미완성 9 / 25

- ops 구성 (9)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_revisions_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - get_revision: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_delete: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_restore: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - restore: 대표 성공 ✓ · 대표 거부 ✓
  - search_revisions_of_artifact_gql: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (16)
  - admin_search: 성공 있음 2 · 거부 있음 1 (global_scope)
  - admin_search_gql: 성공 있음 2 · 거부 있음 1 (global_scope)
  - approve_revision: 성공 있음 1 · 거부 있음 2 (single_field)
  - cancel_import: 성공 있음 2 · 거부 있음 1 (single_field)
  - cleanup_revision: 성공 없음 · 거부 있음 2 (single_field): SCENARIO-GAP
  - delegate_import_batch: 성공 없음 · 거부 있음 2 (global_scope): SCENARIO-GAP
  - delegate_scan: 성공 없음 · 거부 있음 1 (global_scope): SCENARIO-GAP
  - delete_artifacts: 성공 있음 1 · 거부 있음 1 (global_scope)
  - get: 성공 있음 1 · 거부 있음 1 (single_entity)
  - import_revision: 성공 없음 · 거부 있음 2 (single_field): SCENARIO-GAP
  - reject_revision: 성공 있음 2 · 거부 있음 1 (single_field)
  - restore_artifacts: 성공 있음 1 · 거부 있음 1 (global_scope)
  - retrieve_models: 성공 없음 · 거부 있음 1 (global_scope): SCENARIO-GAP
  - scan: 성공 없음 · 거부 있음 1 (global_scope): SCENARIO-GAP
  - search_revisions_gql: 성공 있음 2 · 거부 있음 1 (global_scope)
  - update: 성공 있음 1 · 거부 있음 2 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록으로 아티팩트를 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다](#reading-an-empty-artifact-id-list-answers-empty) | 성공 |
| [superadmin 이 미리 저장한 아티팩트 둘과 없는 id 하나를 한 번에 읽으면, 자리마다 미리 저장한 아티팩트 전체가 오고 없는 id 자리는 비어 있습니다](#reading-loading-many-artifact-ids-keeps-the-positions) | 성공 |
| [아무 권한도 받지 않은 사용자가 아티팩트 id 여럿을 한 번에 읽으면, 항목마다 권한 부족 거부가 담겨 오고 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다](#reading-a-user-granted-nothing-loading-artifacts-is-refused-on-every-position) | 거부 |

**batch_load_revisions_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록으로 리비전을 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다](#reading-an-empty-revision-id-list-answers-empty) | 성공 |
| [superadmin 이 미리 저장한 리비전 둘과 없는 id 하나를 한 번에 읽으면, 자리마다 미리 저장한 리비전 전체가 오고 없는 id 자리는 비어 있습니다](#reading-loading-many-revision-ids-keeps-the-positions) | 성공 |
| [아무 권한도 받지 않은 사용자가 리비전 id 여럿을 한 번에 읽으면, 읽을 수 없는 리비전 자리마다 권한 부족 거부가 담기고 없는 id 자리는 비어 있습니다](#reading-a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아티팩트를 soft delete 하면, 삭제됨 상태의 아티팩트가 옵니다](#deleting-the-superadmin-soft-deletes-an-artifact) | 성공 |
| [아무 권한도 받지 않은 사용자는 아티팩트를 soft delete 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-soft-delete-an-artifact) | 거부 |

**get_revision**

| 시나리오 | 판정 |
|---|---|
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 리비전을 id 로 읽으면, 미리 저장한 리비전 전체가 옵니다](#reading-a-user-granted-read-gets-a-revision) | 성공 |
| [아무 권한도 받지 않은 사용자가 리비전을 id 로 읽으려 하면, 그 리비전을 가진 아티팩트를 찾을 수 없다는 것으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-a-revision) | 거부 |

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

**search_revisions_of_artifact_gql**

| 시나리오 | 판정 |
|---|---|
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 아티팩트 하나의 리비전을 검색하면, 그 아티팩트가 가진 리비전만 한 페이지로 옵니다](#revision_searching-searching-one-artifacts-revisions-returns-only-the-ones-it-holds) | 성공 |
| [아무 권한도 받지 않은 사용자가 아티팩트 하나의 리비전을 검색하려 하면, 그 아티팩트에 대한 권한이 없어 요청 전체가 거부됩니다](#revision_searching-a-user-granted-nothing-may-not-search-one-artifacts-revisions) | 거부 |

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 모델 종류로 좁혀 검색하면, 모델 아티팩트만 남습니다](#searching-narrowing-to-the-model-type-leaves-only-model-artifacts) | 성공 |
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 조건 없이 검색하면, 미리 저장한 아티팩트가 모두 한 페이지로 옵니다](#searching-searching-without-a-condition-returns-every-artifact) | 성공 |
| [아무 권한도 받지 않은 사용자가 아티팩트를 검색하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-artifacts) | 거부 |

**admin_search_gql**

| 시나리오 | 판정 |
|---|---|
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 GQL 종류 필터로 좁혀 검색하면, 모델 아티팩트만 남습니다](#searching_gql-gql-narrowing-to-the-model-type-leaves-only-model-artifacts) | 성공 |
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 GQL 조건 없이 검색하면, 미리 저장한 아티팩트가 모두 한 페이지로 옵니다](#searching_gql-gql-searching-without-a-condition-returns-every-artifact) | 성공 |
| [아무 권한도 받지 않은 사용자가 GQL 검색을 하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#searching_gql-a-user-granted-nothing-may-not-search-artifacts-with-gql-filters) | 거부 |

**approve_revision**

| 시나리오 | 판정 |
|---|---|
| [승인 대기 중인 리비전을 승인하면, 사용 가능 상태의 리비전이 옵니다](#revision_transitions-approving-a-revision-waiting-for-approval-makes-it-available) | 성공 |
| [승인 대기 상태가 아닌 리비전은 승인할 수 없고, 검증되지 않았다는 것으로 거부됩니다](#revision_transitions-a-revision-not-waiting-for-approval-is-not-approved) | 거부 |
| [이미 사용 가능한 리비전은 다시 승인할 수 없고, 검증되지 않았다는 것으로 거부됩니다](#revision_transitions-an-already-available-revision-is-not-approved-again) | 거부 |

**cancel_import**

| 시나리오 | 판정 |
|---|---|
| [이미 사용 가능한 리비전의 가져오기를 취소해도 스캔됨 상태로 돌아옵니다. 취소는 상태를 가리지 않습니다](#revision_transitions-cancelling-a-finished-import-puts-the-revision-back-to-scanned) | 성공 |
| [가져오는 중인 리비전의 가져오기를 취소하면, 스캔됨 상태의 리비전이 옵니다](#revision_transitions-cancelling-a-running-import-puts-the-revision-back-to-scanned) | 성공 |
| [superadmin 이 없는 리비전의 가져오기를 취소하려 하면, 그 리비전이 없다는 것으로 거부됩니다](#revision_transitions-cancelling-the-import-of-a-missing-revision-is-refused) | 거부 |

**cleanup_revision**

| 시나리오 | 판정 |
|---|---|
| [가져오는 중인 리비전은 정리할 수 없고, 정리할 준비가 되지 않았다는 것으로 거부됩니다](#revision_transitions-cleaning-up-a-revision-being-pulled-is-refused) | 거부 |
| [스캔만 된 리비전은 정리할 수 없고, 정리할 준비가 되지 않았다는 것으로 거부됩니다](#revision_transitions-cleaning-up-a-scanned-revision-is-refused) | 거부 |

**delegate_import_batch**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 가져오기를 위임하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#revision_transitions-a-user-granted-nothing-may-not-delegate-an-import) | 거부 |
| [Reservoir 설정 없이 가져오기를 위임하려 하면, 서버가 설정되지 않았다는 것으로 거부됩니다](#revision_transitions-delegating-an-import-without-reservoir-configuration-is-refused) | 거부 |

**delegate_scan**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 바깥 레지스트리 스캔을 위임하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#scanning-a-user-granted-nothing-may-not-delegate-a-scan) | 거부 |

**delete_artifacts**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아티팩트 여럿을 id 목록으로 soft delete 하면, 모두 삭제됨 상태로 옵니다](#bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids) | 성공 |
| [superadmin 이 아닌 사용자는 아티팩트 여럿을 id 목록으로 soft delete 할 수 없고, 역할로 거부됩니다](#bulk_deleting-a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [global 에서 아티팩트 읽기 권한을 받은 사용자가 아티팩트를 id 로 읽으면, 미리 저장한 아티팩트 전체가 옵니다](#reading-a-user-granted-read-gets-an-artifact) | 성공 |
| [아무 권한도 받지 않은 사용자가 아티팩트를 id 로 읽으려 하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-get-an-artifact) | 거부 |

**import_revision**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 없는 리비전을 가져오려 하면, 그 리비전이 없다는 것으로 거부됩니다](#revision_transitions-importing-a-missing-revision-is-refused) | 거부 |
| [Reservoir 설정 없이 리비전을 가져오려 하면, 서버가 설정되지 않았다는 것으로 거부됩니다](#revision_transitions-importing-without-reservoir-configuration-is-refused) | 거부 |

**reject_revision**

| 시나리오 | 판정 |
|---|---|
| [승인 대기 중인 리비전도 거절하면 거절됨 상태로 옵니다](#revision_transitions-rejecting-a-revision-waiting-for-approval-makes-it-rejected) | 성공 |
| [사용 가능한 리비전을 거절하면, 거절됨 상태의 리비전이 옵니다. 거절은 상태를 가리지 않습니다](#revision_transitions-rejecting-an-available-revision-makes-it-rejected) | 성공 |
| [아무 권한도 받지 않은 사용자가 리비전을 거절하려 하면, 그 리비전을 가진 아티팩트를 찾을 수 없다는 것으로 거부됩니다](#revision_transitions-a-user-granted-nothing-may-not-reject-a-revision) | 거부 |

**restore_artifacts**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 soft delete 된 아티팩트 여럿을 id 목록으로 restore 하면, 모두 살아 있는 상태로 옵니다](#bulk_deleting-the-superadmin-restores-artifacts-by-ids) | 성공 |
| [superadmin 이 아닌 사용자는 아티팩트를 id 목록으로 restore 할 수 없습니다](#bulk_deleting-a-user-who-is-not-superadmin-may-not-restore-artifacts-by-ids) | 거부 |

**retrieve_models**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 바깥 레지스트리에서 모델 상세를 읽으려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#scanning-a-user-granted-nothing-may-not-retrieve-models) | 거부 |

**scan**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 바깥 레지스트리를 스캔하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#scanning-a-user-granted-nothing-may-not-scan-external-registries) | 거부 |

**search_revisions_gql**

| 시나리오 | 판정 |
|---|---|
| [읽기만 하는 monitor 가 승인 대기 상태로 좁혀 검색하면, 그 상태의 리비전만 남습니다](#revision_searching-filtering-revisions-by-status-leaves-only-that-status) | 성공 |
| [읽기만 하는 monitor 가 리비전을 조건 없이 검색하면, 미리 저장한 리비전이 모두 한 페이지로 옵니다](#revision_searching-searching-revisions-without-a-condition-returns-every) | 성공 |
| [아무 권한도 받지 않은 사용자가 리비전을 검색하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다](#revision_searching-a-user-granted-nothing-may-not-search-revisions) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 아티팩트의 설명을 변경하면, 새 설명을 담은 아티팩트가 응답으로 옵니다](#editing-the-superadmin-edits-an-artifact) | 성공 |
| [soft delete 된 아티팩트는 superadmin 이라도 수정할 수 없고, 대상이 없다는 것으로 거부됩니다](#editing-a-soft-deleted-artifact-is-not-edited) | 거부 |
| [아무 권한도 받지 않은 사용자는 아티팩트를 수정할 수 없습니다](#editing-a-user-granted-nothing-may-not-edit-an-artifact) | 거부 |

### batch_load_by_ids

<a id="reading-an-empty-artifact-id-list-answers-empty"></a>

#### [an-empty-artifact-id-list-answers-empty](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

빈 id 목록으로 아티팩트를 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다

Given

- 아티팩트 2개와, superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.batch_load_by_ids: user-1이 빈 id 목록으로 읽습니다

Then

- 빈 응답이 반환됩니다
  - items = []

<a id="reading-loading-many-artifact-ids-keeps-the-positions"></a>

#### [loading-many-artifact-ids-keeps-the-positions](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

superadmin 이 미리 저장한 아티팩트 둘과 없는 id 하나를 한 번에 읽으면, 자리마다 미리 저장한 아티팩트 전체가 오고 없는 id 자리는 비어 있습니다

Given

- 아티팩트 2개와, superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.batch_load_by_ids: user-1이 미리 저장한 아티팩트 2개와 없는 id 하나를 한 번에 읽습니다

Then

- 자리마다 미리 저장한 아티팩트 전체가 오고, 없는 id 자리는 비어 있습니다
  - length = 3
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
  - [1] = None
  - [2].name = 'artifact-2'
  - [2].type = <ArtifactType.MODEL: 'MODEL'>
  - [2].description = '이미 있던 아티팩트'
  - [2].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [2].readonly = False
  - [2].extra = None
  - [2].revisions = []
  - [2].id: 미리 저장한 아티팩트의 id 와 같다
  - [2].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [2].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [2].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [2].scanned_at: 이 실행이 쓴 시각
  - [2].updated_at: 이 실행이 쓴 시각

<a id="reading-a-user-granted-nothing-loading-artifacts-is-refused-on-every-position"></a>

#### [a-user-granted-nothing-loading-artifacts-is-refused-on-every-position](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

아무 권한도 받지 않은 사용자가 아티팩트 id 여럿을 한 번에 읽으면, 항목마다 권한 부족 거부가 담겨 오고 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다

Given

- 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.batch_load_by_ids: user-1이 미리 저장한 아티팩트 2개와 없는 id 하나를 한 번에 읽습니다

Then

- 자리마다 권한 부족 거부가 담겨 오고, 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다
  - length = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### batch_load_revisions_by_ids

<a id="reading-an-empty-revision-id-list-answers-empty"></a>

#### [an-empty-revision-id-list-answers-empty](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

빈 id 목록으로 리비전을 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다

Given

- 리비전 1개를 가진 아티팩트 2개와, superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.batch_load_revisions_by_ids: user-1이 빈 id 목록으로 읽습니다

Then

- 빈 응답이 반환됩니다
  - items = []

<a id="reading-loading-many-revision-ids-keeps-the-positions"></a>

#### [loading-many-revision-ids-keeps-the-positions](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

superadmin 이 미리 저장한 리비전 둘과 없는 id 하나를 한 번에 읽으면, 자리마다 미리 저장한 리비전 전체가 오고 없는 id 자리는 비어 있습니다

Given

- 리비전 1개를 가진 아티팩트 2개와, superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.batch_load_revisions_by_ids: user-1이 미리 저장한 리비전 둘과 없는 id 하나를 한 번에 읽습니다

Then

- 자리마다 미리 저장한 리비전 전체가 오고, 없는 id 자리는 비어 있습니다
  - length = 3
  - [0].id: 미리 저장한 리비전의 id 와 같다
  - [0].field_id: 미리 저장한 리비전의 id 와 같다
  - [0].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [0].version = '1.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [0].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [0].readme = 'the revision readme'
  - [1] = None
  - [2].id: 미리 저장한 리비전의 id 와 같다
  - [2].field_id: 미리 저장한 리비전의 id 와 같다
  - [2].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [2].version = '1.0'
  - [2].size = '1024'
  - [2].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [2].remote_status = None
  - [2].created_at = None
  - [2].updated_at = None
  - [2].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [2].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [2].readme = 'the revision readme'

<a id="reading-a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one"></a>

#### [a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

아무 권한도 받지 않은 사용자가 리비전 id 여럿을 한 번에 읽으면, 읽을 수 없는 리비전 자리마다 권한 부족 거부가 담기고 없는 id 자리는 비어 있습니다

Given

- 리비전 1개를 가진 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.batch_load_revisions_by_ids: user-1이 미리 저장한 리비전 둘과 없는 id 하나를 한 번에 읽습니다

Then

- 읽을 수 없는 리비전 자리마다 권한 부족 거부가 담기고, 없는 id 자리는 비어 있습니다
  - length = 3
  - 거부: NotEnoughPermission
  - [1] = None
  - 거부: NotEnoughPermission

### delete

<a id="deleting-the-superadmin-soft-deletes-an-artifact"></a>

#### [the-superadmin-soft-deletes-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

superadmin 이 아티팩트를 soft delete 하면, 삭제됨 상태의 아티팩트가 옵니다

Given

- 아티팩트 하나와, superadmin 한 명
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

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
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

### get_revision

<a id="reading-a-user-granted-read-gets-a-revision"></a>

#### [a-user-granted-read-gets-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 리비전을 id 로 읽으면, 미리 저장한 리비전 전체가 옵니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.get_revision: user-1이 artifact-1의 리비전 1.0을 id 로 읽습니다

Then

- 미리 저장한 리비전 전체가 반환됩니다
  - id: 미리 저장한 리비전의 id 와 같다
  - field_id: 미리 저장한 리비전의 id 와 같다
  - artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - readme = 'the revision readme'

<a id="reading-a-user-granted-nothing-may-not-read-a-revision"></a>

#### [a-user-granted-nothing-may-not-read-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

아무 권한도 받지 않은 사용자가 리비전을 id 로 읽으려 하면, 그 리비전을 가진 아티팩트를 찾을 수 없다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.get_revision: user-1이 artifact-1의 리비전 1.0을 id 로 읽습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-artifacts"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
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

- 아티팩트 2개와, superadmin 한 명
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

- 아티팩트 2개와, superadmin 한 명
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

- 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
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

- 아티팩트 2개와, superadmin 한 명
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

- 아티팩트 하나와, superadmin 한 명
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

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
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

### search_revisions_of_artifact_gql

<a id="revision_searching-searching-one-artifacts-revisions-returns-only-the-ones-it-holds"></a>

#### [searching-one-artifacts-revisions-returns-only-the-ones-it-holds](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 아티팩트 하나의 리비전을 검색하면, 그 아티팩트가 가진 리비전만 한 페이지로 옵니다

Given

- 리비전 2개를 가진 아티팩트 2개와, 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-1: 리비전 2.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 아티팩트 artifact-2: 리비전 2.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.search_revisions_of_artifact_gql: user-1이 artifact-1이 가진 리비전을 검색합니다

Then

- 그 아티팩트가 가진 리비전이 모두 한 페이지로 옵니다
  - count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: 미리 저장한 리비전의 id 와 같다
  - [0].field_id: 미리 저장한 리비전의 id 와 같다
  - [0].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [0].version = '1.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [0].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [0].readme = 'the revision readme'
  - [1].id: 미리 저장한 리비전의 id 와 같다
  - [1].field_id: 미리 저장한 리비전의 id 와 같다
  - [1].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [1].version = '2.0'
  - [1].size = '1024'
  - [1].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [1].remote_status = None
  - [1].created_at = None
  - [1].updated_at = None
  - [1].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [1].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [1].readme = 'the revision readme'

<a id="revision_searching-a-user-granted-nothing-may-not-search-one-artifacts-revisions"></a>

#### [a-user-granted-nothing-may-not-search-one-artifacts-revisions](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

아무 권한도 받지 않은 사용자가 아티팩트 하나의 리비전을 검색하려 하면, 그 아티팩트에 대한 권한이 없어 요청 전체가 거부됩니다

Given

- 리비전 2개를 가진 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-1: 리비전 2.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 아티팩트 artifact-2: 리비전 2.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.search_revisions_of_artifact_gql: user-1이 artifact-1이 가진 리비전을 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### admin_search

<a id="searching-narrowing-to-the-model-type-leaves-only-model-artifacts"></a>

#### [narrowing-to-the-model-type-leaves-only-model-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_searching.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 모델 종류로 좁혀 검색하면, 모델 아티팩트만 남습니다

Given

- 모델 아티팩트 2개와 패키지 아티팩트 1개, 그리고 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-3: 허깅 페이스 레지스트리에서 스캔한 모델
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.admin_search: user-1이 모델 종류로 좁혀 검색합니다

Then

- 모델 아티팩트가 모두 한 페이지로 옵니다
  - count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
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

<a id="searching-searching-without-a-condition-returns-every-artifact"></a>

#### [searching-without-a-condition-returns-every-artifact](/tests/scenario/bai_scenario/manager/artifact/test_searching.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 조건 없이 검색하면, 미리 저장한 아티팩트가 모두 한 페이지로 옵니다

Given

- 모델 아티팩트 2개와 패키지 아티팩트 1개, 그리고 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-3: 허깅 페이스 레지스트리에서 스캔한 모델
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.admin_search: user-1이 조건 없이 검색합니다

Then

- 미리 저장한 아티팩트가 모두 한 페이지로 옵니다
  - count = 3
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False
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
  - [2].name = 'artifact-3'
  - [2].type = <ArtifactType.PACKAGE: 'PACKAGE'>
  - [2].description = '이미 있던 아티팩트'
  - [2].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [2].readonly = False
  - [2].extra = None
  - [2].revisions = []
  - [2].id: 미리 저장한 아티팩트의 id 와 같다
  - [2].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [2].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [2].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [2].scanned_at: 이 실행이 쓴 시각
  - [2].updated_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-search-artifacts"></a>

#### [a-user-granted-nothing-may-not-search-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_searching.py): pass

아무 권한도 받지 않은 사용자가 아티팩트를 검색하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 모델 아티팩트 2개와 패키지 아티팩트 1개, 그리고 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-3: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.admin_search: user-1이 조건 없이 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_gql

<a id="searching_gql-gql-narrowing-to-the-model-type-leaves-only-model-artifacts"></a>

#### [gql-narrowing-to-the-model-type-leaves-only-model-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_searching_gql.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 GQL 종류 필터로 좁혀 검색하면, 모델 아티팩트만 남습니다

Given

- 모델 아티팩트 2개와 패키지 아티팩트 1개, 그리고 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-3: 허깅 페이스 레지스트리에서 스캔한 모델
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.admin_search_gql: user-1이 모델 종류로 좁혀 검색합니다

Then

- 모델 아티팩트가 모두 한 페이지로 옵니다
  - count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
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

<a id="searching_gql-gql-searching-without-a-condition-returns-every-artifact"></a>

#### [gql-searching-without-a-condition-returns-every-artifact](/tests/scenario/bai_scenario/manager/artifact/test_searching_gql.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 GQL 조건 없이 검색하면, 미리 저장한 아티팩트가 모두 한 페이지로 옵니다

Given

- 모델 아티팩트 2개와 패키지 아티팩트 1개, 그리고 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-3: 허깅 페이스 레지스트리에서 스캔한 모델
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.admin_search_gql: user-1이 조건 없이 검색합니다

Then

- 미리 저장한 아티팩트가 모두 한 페이지로 옵니다
  - count = 3
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False
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
  - [2].name = 'artifact-3'
  - [2].type = <ArtifactType.PACKAGE: 'PACKAGE'>
  - [2].description = '이미 있던 아티팩트'
  - [2].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [2].readonly = False
  - [2].extra = None
  - [2].revisions = []
  - [2].id: 미리 저장한 아티팩트의 id 와 같다
  - [2].entity_id: 미리 저장한 아티팩트의 id 와 같다
  - [2].registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [2].source_registry_id: 미리 저장한 아티팩트의 레지스트리 id 와 같다
  - [2].scanned_at: 이 실행이 쓴 시각
  - [2].updated_at: 이 실행이 쓴 시각

<a id="searching_gql-a-user-granted-nothing-may-not-search-artifacts-with-gql-filters"></a>

#### [a-user-granted-nothing-may-not-search-artifacts-with-gql-filters](/tests/scenario/bai_scenario/manager/artifact/test_searching_gql.py): pass

아무 권한도 받지 않은 사용자가 GQL 검색을 하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 모델 아티팩트 2개와 패키지 아티팩트 1개, 그리고 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-3: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.admin_search_gql: user-1이 조건 없이 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### approve_revision

<a id="revision_transitions-approving-a-revision-waiting-for-approval-makes-it-available"></a>

#### [approving-a-revision-waiting-for-approval-makes-it-available](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

승인 대기 중인 리비전을 승인하면, 사용 가능 상태의 리비전이 옵니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.approve_revision: user-1이 리비전 1.0을 승인합니다

Then

- 미리 저장한 리비전 전체가 반환됩니다
  - id: 미리 저장한 리비전의 id 와 같다
  - field_id: 미리 저장한 리비전의 id 와 같다
  - artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.AVAILABLE: 'AVAILABLE'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - readme = 'the revision readme'

<a id="revision_transitions-a-revision-not-waiting-for-approval-is-not-approved"></a>

#### [a-revision-not-waiting-for-approval-is-not-approved](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

승인 대기 상태가 아닌 리비전은 승인할 수 없고, 검증되지 않았다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.approve_revision: user-1이 리비전 1.0을 승인합니다

Then

- 거부됩니다
  - 거부: ArtifactRevisionNotVerified

<a id="revision_transitions-an-already-available-revision-is-not-approved-again"></a>

#### [an-already-available-revision-is-not-approved-again](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

이미 사용 가능한 리비전은 다시 승인할 수 없고, 검증되지 않았다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.approve_revision: user-1이 리비전 1.0을 승인합니다

Then

- 거부됩니다
  - 거부: ArtifactRevisionNotVerified

### cancel_import

<a id="revision_transitions-cancelling-a-finished-import-puts-the-revision-back-to-scanned"></a>

#### [cancelling-a-finished-import-puts-the-revision-back-to-scanned](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

이미 사용 가능한 리비전의 가져오기를 취소해도 스캔됨 상태로 돌아옵니다. 취소는 상태를 가리지 않습니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.cancel_import: user-1이 리비전 1.0의 가져오기를 취소합니다

Then

- 미리 저장한 리비전 전체가 반환됩니다
  - id: 미리 저장한 리비전의 id 와 같다
  - field_id: 미리 저장한 리비전의 id 와 같다
  - artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - readme = 'the revision readme'

<a id="revision_transitions-cancelling-a-running-import-puts-the-revision-back-to-scanned"></a>

#### [cancelling-a-running-import-puts-the-revision-back-to-scanned](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

가져오는 중인 리비전의 가져오기를 취소하면, 스캔됨 상태의 리비전이 옵니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.cancel_import: user-1이 리비전 1.0의 가져오기를 취소합니다

Then

- 미리 저장한 리비전 전체가 반환됩니다
  - id: 미리 저장한 리비전의 id 와 같다
  - field_id: 미리 저장한 리비전의 id 와 같다
  - artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - readme = 'the revision readme'

<a id="revision_transitions-cancelling-the-import-of-a-missing-revision-is-refused"></a>

#### [cancelling-the-import-of-a-missing-revision-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

superadmin 이 없는 리비전의 가져오기를 취소하려 하면, 그 리비전이 없다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.cancel_import: user-1이 없는 리비전 id 로 가져오기 취소를 시도합니다

Then

- 거부됩니다
  - 거부: FieldNotFoundError

### cleanup_revision

<a id="revision_transitions-cleaning-up-a-revision-being-pulled-is-refused"></a>

#### [cleaning-up-a-revision-being-pulled-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

가져오는 중인 리비전은 정리할 수 없고, 정리할 준비가 되지 않았다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, SOFT_DELETE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.cleanup_revision: user-1이 리비전 1.0을 정리합니다

Then

- 거부됩니다
  - 거부: ArtifactRevisionDeletionBadRequestError

<a id="revision_transitions-cleaning-up-a-scanned-revision-is-refused"></a>

#### [cleaning-up-a-scanned-revision-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

스캔만 된 리비전은 정리할 수 없고, 정리할 준비가 되지 않았다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, SOFT_DELETE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.cleanup_revision: user-1이 리비전 1.0을 정리합니다

Then

- 거부됩니다
  - 거부: ArtifactRevisionDeletionBadRequestError

### delegate_import_batch

<a id="revision_transitions-a-user-granted-nothing-may-not-delegate-an-import"></a>

#### [a-user-granted-nothing-may-not-delegate-an-import](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

아무 권한도 받지 않은 사용자가 가져오기를 위임하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 리비전 1개를 가진 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delegate_import_batch: user-1이 리비전 둘의 가져오기를 다른 레지스트리에 위임합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="revision_transitions-delegating-an-import-without-reservoir-configuration-is-refused"></a>

#### [delegating-an-import-without-reservoir-configuration-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

Reservoir 설정 없이 가져오기를 위임하려 하면, 서버가 설정되지 않았다는 것으로 거부됩니다

Given

- 리비전 1개를 가진 아티팩트 2개와, superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delegate_import_batch: user-1이 리비전 둘의 가져오기를 다른 레지스트리에 위임합니다

Then

- 거부됩니다
  - 거부: ServerMisconfiguredError

### delegate_scan

<a id="scanning-a-user-granted-nothing-may-not-delegate-a-scan"></a>

#### [a-user-granted-nothing-may-not-delegate-a-scan](/tests/scenario/bai_scenario/manager/artifact/test_scanning.py): pass

아무 권한도 받지 않은 사용자가 바깥 레지스트리 스캔을 위임하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.delegate_scan: user-1이 조건 없이 바깥 레지스트리 스캔을 위임합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### delete_artifacts

<a id="bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids"></a>

#### [the-superadmin-soft-deletes-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

superadmin 이 아티팩트 여럿을 id 목록으로 soft delete 하면, 모두 삭제됨 상태로 옵니다

Given

- 아티팩트 2개와, superadmin 한 명
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

- 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
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

### get

<a id="reading-a-user-granted-read-gets-an-artifact"></a>

#### [a-user-granted-read-gets-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

global 에서 아티팩트 읽기 권한을 받은 사용자가 아티팩트를 id 로 읽으면, 미리 저장한 아티팩트 전체가 옵니다

Given

- 아티팩트 하나와, 아티팩트에 READ 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.get: user-1이 artifact-1을 id 로 읽습니다

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

<a id="reading-a-user-granted-nothing-may-not-get-an-artifact"></a>

#### [a-user-granted-nothing-may-not-get-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

아무 권한도 받지 않은 사용자가 아티팩트를 id 로 읽으려 하면 권한 부족으로 거부됩니다

Given

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.get: user-1이 artifact-1을 id 로 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### import_revision

<a id="revision_transitions-importing-a-missing-revision-is-refused"></a>

#### [importing-a-missing-revision-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

superadmin 이 없는 리비전을 가져오려 하면, 그 리비전이 없다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 superadmin 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.import_revision: user-1이 없는 리비전 id 로 가져오기를 시도합니다

Then

- 거부됩니다
  - 거부: FieldNotFoundError

<a id="revision_transitions-importing-without-reservoir-configuration-is-refused"></a>

#### [importing-without-reservoir-configuration-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

Reservoir 설정 없이 리비전을 가져오려 하면, 서버가 설정되지 않았다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, CREATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.import_revision: user-1이 리비전 1.0을 가져옵니다

Then

- 거부됩니다
  - 거부: ServerMisconfiguredError

### reject_revision

<a id="revision_transitions-rejecting-a-revision-waiting-for-approval-makes-it-rejected"></a>

#### [rejecting-a-revision-waiting-for-approval-makes-it-rejected](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

승인 대기 중인 리비전도 거절하면 거절됨 상태로 옵니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.reject_revision: user-1이 리비전 1.0을 거절합니다

Then

- 미리 저장한 리비전 전체가 반환됩니다
  - id: 미리 저장한 리비전의 id 와 같다
  - field_id: 미리 저장한 리비전의 id 와 같다
  - artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.REJECTED: 'REJECTED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - readme = 'the revision readme'

<a id="revision_transitions-rejecting-an-available-revision-makes-it-rejected"></a>

#### [rejecting-an-available-revision-makes-it-rejected](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

사용 가능한 리비전을 거절하면, 거절됨 상태의 리비전이 옵니다. 거절은 상태를 가리지 않습니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아티팩트에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - global 에서 아티팩트 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 artifact-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 artifact-keeper-1: artifact 전체에 READ 허용
    - 역할 artifact-keeper-1: artifact 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 artifact-keeper-1 보유

When

- ArtifactAdapter.reject_revision: user-1이 리비전 1.0을 거절합니다

Then

- 미리 저장한 리비전 전체가 반환됩니다
  - id: 미리 저장한 리비전의 id 와 같다
  - field_id: 미리 저장한 리비전의 id 와 같다
  - artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.REJECTED: 'REJECTED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - readme = 'the revision readme'

<a id="revision_transitions-a-user-granted-nothing-may-not-reject-a-revision"></a>

#### [a-user-granted-nothing-may-not-reject-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

아무 권한도 받지 않은 사용자가 리비전을 거절하려 하면, 그 리비전을 가진 아티팩트를 찾을 수 없다는 것으로 거부됩니다

Given

- 아티팩트 하나와 리비전 1개, 그리고 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.reject_revision: user-1이 리비전 1.0을 거절합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### restore_artifacts

<a id="bulk_deleting-the-superadmin-restores-artifacts-by-ids"></a>

#### [the-superadmin-restores-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

superadmin 이 soft delete 된 아티팩트 여럿을 id 목록으로 restore 하면, 모두 살아 있는 상태로 옵니다

Given

- 아티팩트 2개와, superadmin 한 명
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

<a id="bulk_deleting-a-user-who-is-not-superadmin-may-not-restore-artifacts-by-ids"></a>

#### [a-user-who-is-not-superadmin-may-not-restore-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

superadmin 이 아닌 사용자는 아티팩트를 id 목록으로 restore 할 수 없습니다

Given

- 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.restore_artifacts: user-1이 아티팩트 2개를 id 목록으로 restore 합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### retrieve_models

<a id="scanning-a-user-granted-nothing-may-not-retrieve-models"></a>

#### [a-user-granted-nothing-may-not-retrieve-models](/tests/scenario/bai_scenario/manager/artifact/test_scanning.py): pass

아무 권한도 받지 않은 사용자가 바깥 레지스트리에서 모델 상세를 읽으려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.retrieve_models: user-1이 바깥 레지스트리에서 모델 상세를 다시 읽습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### scan

<a id="scanning-a-user-granted-nothing-may-not-scan-external-registries"></a>

#### [a-user-granted-nothing-may-not-scan-external-registries](/tests/scenario/bai_scenario/manager/artifact/test_scanning.py): pass

아무 권한도 받지 않은 사용자가 바깥 레지스트리를 스캔하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.scan: user-1이 조건 없이 바깥 레지스트리를 스캔합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### search_revisions_gql

<a id="revision_searching-filtering-revisions-by-status-leaves-only-that-status"></a>

#### [filtering-revisions-by-status-leaves-only-that-status](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

읽기만 하는 monitor 가 승인 대기 상태로 좁혀 검색하면, 그 상태의 리비전만 남습니다

Given

- 리비전 2개를 가진 아티팩트 2개와, 아무 권한도 받지 않은 monitor 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-1: 리비전 2.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 아티팩트 artifact-2: 리비전 2.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.search_revisions_gql: user-1이 NEEDS_APPROVAL 상태로 좁혀 검색합니다

Then

- 그 상태의 리비전이 모두 한 페이지로 옵니다
  - count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: 미리 저장한 리비전의 id 와 같다
  - [0].field_id: 미리 저장한 리비전의 id 와 같다
  - [0].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [0].version = '2.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [0].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [0].readme = 'the revision readme'
  - [1].id: 미리 저장한 리비전의 id 와 같다
  - [1].field_id: 미리 저장한 리비전의 id 와 같다
  - [1].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [1].version = '2.0'
  - [1].size = '1024'
  - [1].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [1].remote_status = None
  - [1].created_at = None
  - [1].updated_at = None
  - [1].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [1].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [1].readme = 'the revision readme'

<a id="revision_searching-searching-revisions-without-a-condition-returns-every"></a>

#### [searching-revisions-without-a-condition-returns-every](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

읽기만 하는 monitor 가 리비전을 조건 없이 검색하면, 미리 저장한 리비전이 모두 한 페이지로 옵니다

Given

- 리비전 2개를 가진 아티팩트 2개와, 아무 권한도 받지 않은 monitor 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-1: 리비전 2.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 아티팩트 artifact-2: 리비전 2.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.search_revisions_gql: user-1이 조건 없이 검색합니다

Then

- 미리 저장한 리비전이 모두 한 페이지로 옵니다
  - count = 4
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False
  - [0].id: 미리 저장한 리비전의 id 와 같다
  - [0].field_id: 미리 저장한 리비전의 id 와 같다
  - [0].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [0].version = '1.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [0].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [0].readme = 'the revision readme'
  - [1].id: 미리 저장한 리비전의 id 와 같다
  - [1].field_id: 미리 저장한 리비전의 id 와 같다
  - [1].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [1].version = '2.0'
  - [1].size = '1024'
  - [1].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [1].remote_status = None
  - [1].created_at = None
  - [1].updated_at = None
  - [1].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [1].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [1].readme = 'the revision readme'
  - [2].id: 미리 저장한 리비전의 id 와 같다
  - [2].field_id: 미리 저장한 리비전의 id 와 같다
  - [2].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [2].version = '1.0'
  - [2].size = '1024'
  - [2].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [2].remote_status = None
  - [2].created_at = None
  - [2].updated_at = None
  - [2].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [2].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [2].readme = 'the revision readme'
  - [3].id: 미리 저장한 리비전의 id 와 같다
  - [3].field_id: 미리 저장한 리비전의 id 와 같다
  - [3].artifact_id: 미리 저장한 아티팩트의 id 와 같다
  - [3].version = '2.0'
  - [3].size = '1024'
  - [3].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [3].remote_status = None
  - [3].created_at = None
  - [3].updated_at = None
  - [3].digest: 건너뜀: 어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다
  - [3].verification_result: 건너뜀: 어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다
  - [3].readme = 'the revision readme'

<a id="revision_searching-a-user-granted-nothing-may-not-search-revisions"></a>

#### [a-user-granted-nothing-may-not-search-revisions](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

아무 권한도 받지 않은 사용자가 리비전을 검색하려 하면, 전역 역할이 없어 권한 부족으로 거부됩니다

Given

- 리비전 2개를 가진 아티팩트 2개와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 리비전 1.0
  - 아티팩트 artifact-1: 리비전 2.0
  - 아티팩트 artifact-2: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-2: 리비전 1.0
  - 아티팩트 artifact-2: 리비전 2.0
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ArtifactAdapter.search_revisions_gql: user-1이 조건 없이 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### update

<a id="editing-the-superadmin-edits-an-artifact"></a>

#### [the-superadmin-edits-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

superadmin 이 아티팩트의 설명을 변경하면, 새 설명을 담은 아티팩트가 응답으로 옵니다

Given

- 아티팩트 하나와, superadmin 한 명
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

- 아티팩트 하나와, superadmin 한 명
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

- 아티팩트 하나와, 아무 권한도 받지 않은 user 한 명
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

