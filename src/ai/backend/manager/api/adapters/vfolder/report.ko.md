## vfolder

[배경](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

시나리오: 미완성 25 / 30

- ops 구성 (4)
  - admin_search: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - project_search: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
- 직접 구현 (26)
  - batch_load_mount_permissions: 성공 없음 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - batch_load_permissions: 성공 없음 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - bulk_delete: 성공 없음 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - bulk_purge: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - clone: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - create: 성공 있음 1 · 거부 있음 1 (scope)
  - create_download_session: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - create_in_project: 성공 없음 · 거부 없음 (scope): SCENARIO-GAP
  - create_upload_session: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - delete: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - delete_files: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - deploy: 성공 없음 · 거부 없음 (scope, single_entity): SCENARIO-GAP
  - get: 성공 있음 2 · 거부 있음 2 (single_entity)
  - get_folder_usage: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - list_files: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - list_mount_policies: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - mkdir: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - move_file: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - partial_bulk_delete: 성공 있음 2 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - partial_bulk_restore: 성공 있음 1 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - partial_bulk_update: 성공 있음 2 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - purge: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - restore: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - set_mount_policy: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - unset_mount_policy: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - update: 성공 있음 1 · 거부 있음 2 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 옵니다](#batch_loading-a-batch-load-of-no-ids-answers-an-empty-list) | 성공 |
| [자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다](#batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id) | 성공 |
| [다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다](#batch_loading-an-accepted-share-loads-someone-elses-folder-by-id) | 성공 |
| [superadmin 이 다른 사용자의 vfolder 와 없는 id 를 함께 요청하면, 그 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다](#batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |
| [자기 vfolder 만 읽을 수 있는 사용자가 자기 vfolder, 공유받지 않은 다른 사용자의 vfolder, 없는 id 를 한 번에 요청하면, 입력 순서대로 그 vfolder, 거부, 거부가 옵니다](#batch_loading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order) | 거부 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder) | 거부 |
| [다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_loading-an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder) | 거부 |

**project_search**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트의 vfolder 를 조회하면, 그 프로젝트의 vfolder 가 응답으로 옵니다](#reaching-a-user-granted-folder-read-in-a-project-lists-its-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트의 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#reaching-a-user-granted-nothing-may-not-list-a-projects-folders) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [vfolder 를 하나도 생성하지 않은 사용자가 자기 vfolder 를 조회하면, 응답은 비어 있습니다](#vfolder-a-user-who-has-made-no-folder-lists-none) | 성공 |

**create**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 vfolder 생성 권한을 받은 사용자가 vfolder 를 생성하면, 그 vfolder 의 소유는 그 사용자에게 있습니다](#vfolder-a-user-granted-folder-create-makes-one-of-their-own) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다](#vfolder-a-user-granted-nothing-may-not-make-a-folder) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다](#reaching-a-user-granted-folder-read-reads-their-own-folder) | 성공 |
| [다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다](#reaching-an-accepted-share-reads-someone-elses-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#reaching-a-user-granted-nothing-may-not-read-their-own-folder) | 거부 |
| [다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#reaching-an-unanswered-offer-may-not-read-someone-elses-folder) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 하면, 자기 vfolder 둘은 삭제 대기로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다](#partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [vfolder soft delete 권한을 받은 사용자가 soft delete 한 자기 vfolder 둘을 한 번에 restore 하면, 둘 다 사용할 수 있는 상태로 옵니다](#partial_bulk-restoring-several-folders-brings-them-back) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 수정하면, 자기 vfolder 둘은 수정되어 응답으로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다](#partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-a-user-granted-nothing-updates-none-of-several-folders) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 의 이름과 옵션을 변경하면, 바뀐 vfolder 가 응답으로 옵니다](#editing-a-user-granted-folder-update-renames-their-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 변경하려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-update-their-folder) | 거부 |
| [자기 다른 vfolder 가 이미 사용하는 이름으로 변경하려 하면, 잘못된 값으로 거부됩니다](#editing-renaming-to-a-name-the-owner-already-uses-is-refused) | 거부 |

### batch_load_by_ids

<a id="batch_loading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 옵니다

Given

- vfolder 를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFolderAdapter.batch_load_by_ids: user-1이 빈 목록으로 일괄 조회합니다

Then

- 빈 목록이 옵니다
  - loaded = []

<a id="batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id"></a>

#### [a-user-granted-folder-read-loads-their-own-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 미리 저장한 vfolder 하나가 전체가 응답으로 옵니다
  - length = 1
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - [0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - [0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - [0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - [0].metadata.created_at: 이 실행이 쓴 시각

<a id="batch_loading-an-accepted-share-loads-someone-elses-folder-by-id"></a>

#### [an-accepted-share-loads-someone-elses-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 받아들인, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 미리 저장한 vfolder 하나가 전체가 응답으로 옵니다
  - length = 1
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - [0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - [0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - [0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - [0].metadata.created_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

superadmin 이 다른 사용자의 vfolder 와 없는 id 를 함께 요청하면, 그 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다

Given

- 남의 개인 vfolder 하나와, 아무 역할도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 vfolder 와 없는 id 를 일괄 조회합니다

Then

- 있는 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - [0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - [0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - [0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - [0].metadata.created_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order"></a>

#### [a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

자기 vfolder 만 읽을 수 있는 사용자가 자기 vfolder, 공유받지 않은 다른 사용자의 vfolder, 없는 id 를 한 번에 요청하면, 입력 순서대로 그 vfolder, 거부, 거부가 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-2: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1, folder-2, 없는 id 순으로 일괄 조회합니다

Then

- 입력 순서대로 각 항목에 vfolder 또는 거부가 옵니다
  - length = 3
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - [0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - [0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - [0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - [0].metadata.created_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

<a id="batch_loading-an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder"></a>

#### [an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 아직 응답하지 않은, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### project_search

<a id="reaching-a-user-granted-folder-read-in-a-project-lists-its-folder"></a>

#### [a-user-granted-folder-read-in-a-project-lists-its-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트의 vfolder 를 조회하면, 그 프로젝트의 vfolder 가 응답으로 옵니다

Given

- vfolder 하나를 가진 프로젝트와, 그 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.project_search: user-1이 folder-1 vfolder 가 놓인 프로젝트의 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 전체가 응답으로 옵니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 vfolder 와 같다
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'folder-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'group'
  - items[0].ownership.user_id: vfolder 소유자와 같다
  - items[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - items[0].ownership.creator_id: 생성한 사용자와 같다
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - items[0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - items[0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - items[0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - items[0].metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-a-user-granted-nothing-may-not-list-a-projects-folders"></a>

#### [a-user-granted-nothing-may-not-list-a-projects-folders](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트의 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- vfolder 하나를 가진 프로젝트와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.project_search: user-1이 folder-1 vfolder 가 놓인 프로젝트의 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="vfolder-a-user-who-has-made-no-folder-lists-none"></a>

#### [a-user-who-has-made-no-folder-lists-none](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

vfolder 를 하나도 생성하지 않은 사용자가 자기 vfolder 를 조회하면, 응답은 비어 있습니다

Given

- vfolder 를 놓을 수 있는 도메인과, 거기서 vfolder 를 생성할 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - vfolder 를 생성할 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 folder-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.scoped_search: user-1이 자기 vfolder 를 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

### create

<a id="vfolder-a-user-granted-folder-create-makes-one-of-their-own"></a>

#### [a-user-granted-folder-create-makes-one-of-their-own](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

자기 스코프에서 vfolder 생성 권한을 받은 사용자가 vfolder 를 생성하면, 그 vfolder 의 소유는 그 사용자에게 있습니다

Given

- vfolder 를 놓을 수 있는 도메인과, 거기서 vfolder 를 생성할 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - vfolder 를 생성할 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 folder-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.create: user-1이 work 이라는 이름으로 vfolder 를 생성합니다

Then

- 만든 vfolder 전체가 응답으로 오고, 그 소유는 만든 사람에게 있습니다
  - host = 'local:volume1'
  - metadata.name = 'work'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 만든 사람와 같다
  - ownership.project_id: 건너뜀: 개인 vfolder 는 그 사용자의 개인 프로젝트에 붙습니다. 그 id 는 사용자를 생성할 때 생깁니다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 건너뜀: 데이터베이스가 생성합니다
  - status: 건너뜀: vfolder 가 생성되는 동안 오가는 값입니다
  - metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - metadata.quota_scope_id: 건너뜀: 저장소가 정합니다
  - access_control.permission: 건너뜀: 만든 사람에게는 확인할 것이 없습니다
  - quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="vfolder-a-user-granted-nothing-may-not-make-a-folder"></a>

#### [a-user-granted-nothing-may-not-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

아무 권한도 받지 않은 사용자가 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다

Given

- vfolder 를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFolderAdapter.create: user-1이 denied 이라는 이름으로 vfolder 를 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get

<a id="reaching-a-user-granted-folder-read-reads-their-own-folder"></a>

#### [a-user-granted-folder-read-reads-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-1이 folder-1 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 전체가 응답으로 옵니다
  - id: 미리 저장한 vfolder 와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: vfolder 소유자와 같다
  - ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - ownership.creator_id: 생성한 사용자와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-an-accepted-share-reads-someone-elses-folder"></a>

#### [an-accepted-share-reads-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 받아들인, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-2이 folder-1 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 전체가 응답으로 옵니다
  - id: 미리 저장한 vfolder 와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: vfolder 소유자와 같다
  - ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - ownership.creator_id: 생성한 사용자와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-a-user-granted-nothing-may-not-read-their-own-folder"></a>

#### [a-user-granted-nothing-may-not-read-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.get: user-1이 folder-1 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="reaching-an-unanswered-offer-may-not-read-someone-elses-folder"></a>

#### [an-unanswered-offer-may-not-read-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 아직 응답하지 않은, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-2이 folder-1 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several"></a>

#### [a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 하면, 자기 vfolder 둘은 삭제 대기로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_delete: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 합니다

Then

- 자기 vfolder 둘이 delete-pending 상태로 오고, 다른 사용자의 vfolder 는 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'delete-pending'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - successes[0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - successes[0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 vfolder 와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'delete-pending'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: vfolder 소유자와 같다
  - successes[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 생성한 사용자와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - successes[1].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - successes[1].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.partial_bulk_delete: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 합니다

Then

- 처리된 vfolder 없이, 셋 모두 권한이 없다는 이유로 실패 목록에 옵니다
  - successes = []
  - failed count = 3
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 vfolder 의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유
  - failed[2].id: 대상 vfolder 의 id 와 같다
  - failed[2].message: 'Insufficient permission'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk-restoring-several-folders-brings-them-back"></a>

#### [restoring-several-folders-brings-them-back](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

vfolder soft delete 권한을 받은 사용자가 soft delete 한 자기 vfolder 둘을 한 번에 restore 하면, 둘 다 사용할 수 있는 상태로 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_restore: user-1이 자기 vfolder 둘을 한 번에 soft delete 했다가 한 번에 restore 합니다. restore 의 응답을 반환합니다

Then

- 자기 vfolder 둘이 ready 상태로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - successes[0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - successes[0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 vfolder 와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: vfolder 소유자와 같다
  - successes[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 생성한 사용자와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - successes[1].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - successes[1].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed = []

### partial_bulk_update

<a id="partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several"></a>

#### [a-user-granted-folder-update-updates-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 수정하면, 자기 vfolder 둘은 수정되어 응답으로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_update: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 복제 가능으로 변경합니다

Then

- 자기 vfolder 둘이 복제 가능으로 오고, 다른 사용자의 vfolder 는 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = True
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - successes[0].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - successes[0].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 vfolder 와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = True
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: vfolder 소유자와 같다
  - successes[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 생성한 사용자와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - successes[1].access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - successes[1].quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-a-user-granted-nothing-updates-none-of-several-folders"></a>

#### [a-user-granted-nothing-updates-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.partial_bulk_update: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 복제 가능으로 변경합니다

Then

- 처리된 vfolder 없이, 셋 모두 권한이 없다는 이유로 실패 목록에 옵니다
  - successes = []
  - failed count = 3
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 vfolder 의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유
  - failed[2].id: 대상 vfolder 의 id 와 같다
  - failed[2].message: 'Insufficient permission'를 담은 이유

### update

<a id="editing-a-user-granted-folder-update-renames-their-folder"></a>

#### [a-user-granted-folder-update-renames-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 의 이름과 옵션을 변경하면, 바뀐 vfolder 가 응답으로 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.update: user-1이 자기 첫 vfolder 를 renamed 으로 변경하고 복제 가능으로 변경합니다

Then

- 첫 vfolder 가 renamed 이라는 이름과 복제 가능으로 응답으로 옵니다
  - vfolder.id: 미리 저장한 vfolder 와 같다
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'ready'
  - vfolder.metadata.name = 'renamed'
  - vfolder.metadata.cloneable = True
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: vfolder 소유자와 같다
  - vfolder.ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - vfolder.ownership.creator_id: 생성한 사용자와 같다
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - vfolder.metadata.quota_scope_id: 건너뜀: 소유자의 id 로 생성되어 실행마다 다릅니다
  - vfolder.access_control.permission: 건너뜀: 마운트 권한이라 이 표가 확인하는 값이 아닙니다
  - vfolder.quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - vfolder.metadata.created_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-update-their-folder"></a>

#### [a-user-granted-nothing-may-not-update-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 변경하려 하면 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.update: user-1이 자기 첫 vfolder 를 renamed 으로 변경하고 복제 가능으로 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-renaming-to-a-name-the-owner-already-uses-is-refused"></a>

#### [renaming-to-a-name-the-owner-already-uses-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

자기 다른 vfolder 가 이미 사용하는 이름으로 변경하려 하면, 잘못된 값으로 거부됩니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.update: user-1이 자기 첫 vfolder 를 둘째 vfolder 의 이름으로 변경하고 복제 가능으로 변경합니다

Then

- 거부됩니다
  - 거부: VFolderInvalidParameter

