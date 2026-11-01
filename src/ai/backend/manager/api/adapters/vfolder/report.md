## vfolder

[background](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

Scenario: incomplete 25 / 30

- built from ops (4)
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - project_search: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✗: SCENARIO-GAP
- direct implementation (26)
  - batch_load_mount_permissions: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - batch_load_permissions: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - bulk_delete: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - bulk_purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - clone: success absent · rejection absent (single_entity): SCENARIO-GAP
  - create: success present 1 · rejection present 1 (scope)
  - create_download_session: success absent · rejection absent (single_entity): SCENARIO-GAP
  - create_in_project: success absent · rejection absent (scope): SCENARIO-GAP
  - create_upload_session: success absent · rejection absent (single_entity): SCENARIO-GAP
  - delete: success absent · rejection absent (single_entity): SCENARIO-GAP
  - delete_files: success absent · rejection absent (single_entity): SCENARIO-GAP
  - deploy: success absent · rejection absent (scope, single_entity): SCENARIO-GAP
  - get: success present 2 · rejection present 2 (single_entity)
  - get_folder_usage: success absent · rejection absent (single_entity): SCENARIO-GAP
  - list_files: success absent · rejection absent (single_entity): SCENARIO-GAP
  - list_mount_policies: success absent · rejection absent (single_entity): SCENARIO-GAP
  - mkdir: success absent · rejection absent (single_entity): SCENARIO-GAP
  - move_file: success absent · rejection absent (single_entity): SCENARIO-GAP
  - partial_bulk_delete: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_restore: success present 1 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - restore: success absent · rejection absent (single_entity): SCENARIO-GAP
  - set_mount_policy: success absent · rejection absent (single_entity): SCENARIO-GAP
  - unset_mount_policy: success absent · rejection absent (single_entity): SCENARIO-GAP
  - update: success present 1 · rejection present 2 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 온다](#batch_loading-a-batch-load-of-no-ids-answers-an-empty-list) | answered |
| [자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더 id로 일괄 읽기를 하면, 그 폴더가 온다](#batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id) | answered |
| [남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더 id로 일괄 읽기를 하면, 그 폴더가 온다](#batch_loading-an-accepted-share-loads-someone-elses-folder-by-id) | answered |
| [슈퍼관리자가 남의 폴더와 없는 id를 함께 요청하면, 그 폴더는 노드로, 없는 id 자리는 빈 값으로 온다](#batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |
| [자기 폴더만 읽을 수 있는 사용자가 자기 폴더, 공유받지 않은 남의 폴더, 없는 id를 한 번에 요청하면, 입력 순서대로 그 폴더, 거부, 거부가 온다](#batch_loading-a-batch-load-answers-a-node-or-a-refusal-for-each-id-in-order) | rejected |
| [아무 권한도 받지 않은 사용자가 자기 폴더 id로 일괄 읽기를 하면, 호출은 성공하되 그 자리는 권한 부족으로 거부된다](#batch_loading-a-user-granted-nothing-gets-a-refusal-in-place-of-their-own-folder) | rejected |
| [남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더 id로 일괄 읽기를 하면, 호출은 성공하되 그 자리는 권한 부족으로 거부된다](#batch_loading-an-unanswered-offer-gets-a-refusal-in-place-of-someone-elses-folder) | rejected |

**project_search**

| scenario | verdict |
|---|---|
| [프로젝트에서 폴더 읽기 권한을 받은 사용자가 그 프로젝트의 폴더를 조회하면, 그 프로젝트의 폴더가 온다](#reaching-a-user-granted-folder-read-in-a-project-lists-its-folder) | answered |
| [아무 권한도 받지 않은 사용자가 프로젝트의 폴더를 조회하려 하면 권한 부족으로 거부된다](#reaching-a-user-granted-nothing-may-not-list-a-projects-folders) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다](#vfolder-a-user-who-has-made-no-folder-lists-none) | answered |

**create**

| scenario | verdict |
|---|---|
| [자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, 그 폴더의 소유는 그 사용자에게 있다](#vfolder-a-user-granted-folder-create-makes-one-of-their-own) | answered |
| [아무 권한도 받지 않은 사용자가 폴더를 만들려 하면 권한 부족으로 거부된다](#vfolder-a-user-granted-nothing-may-not-make-a-folder) | rejected |

**get**

| scenario | verdict |
|---|---|
| [자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더를 읽으면, 그 폴더가 온다](#reaching-a-user-granted-folder-read-reads-their-own-folder) | answered |
| [남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더를 읽으면, 그 폴더가 온다](#reaching-an-accepted-share-reads-someone-elses-folder) | answered |
| [아무 권한도 받지 않은 사용자가 자기 폴더를 읽으려 하면 권한 부족으로 거부된다](#reaching-a-user-granted-nothing-may-not-read-their-own-folder) | rejected |
| [남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더를 읽으려 하면 권한 부족으로 거부된다](#reaching-an-unanswered-offer-may-not-read-someone-elses-folder) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [자기 개인 프로젝트에서 폴더 soft delete 권한을 받은 사용자가 자기 폴더 둘과 남의 폴더 하나를 한 번에 soft delete 하면, 자기 폴더 둘은 삭제 대기로 오고 남의 폴더는 권한 부족으로 실패 목록에 온다](#partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several) | answered |
| [아무 권한도 받지 않은 사용자가 폴더 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [폴더 soft delete 권한을 받은 사용자가 soft delete 한 자기 폴더 둘을 한 번에 restore 하면, 둘 다 쓸 수 있는 상태로 온다](#partial_bulk-restoring-several-folders-brings-them-back) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [자기 개인 프로젝트에서 폴더 수정 권한을 받은 사용자가 자기 폴더 둘과 남의 폴더 하나를 한 번에 수정하면, 자기 폴더 둘은 수정되어 오고 남의 폴더는 권한 부족으로 실패 목록에 온다](#partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several) | answered |
| [아무 권한도 받지 않은 사용자가 폴더 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk-a-user-granted-nothing-updates-none-of-several-folders) | answered |

**update**

| scenario | verdict |
|---|---|
| [자기 개인 프로젝트에서 폴더 수정 권한을 받은 사용자가 자기 폴더의 이름과 옵션을 바꾸면, 바뀐 폴더가 온다](#editing-a-user-granted-folder-update-renames-their-folder) | answered |
| [아무 권한도 받지 않은 사용자가 자기 폴더를 바꾸려 하면 권한 부족으로 거부된다](#editing-a-user-granted-nothing-may-not-update-their-folder) | rejected |
| [자기 다른 폴더가 이미 쓰는 이름으로 바꾸려 하면, 잘못된 값으로 거부된다](#editing-renaming-to-a-name-the-owner-already-uses-is-refused) | rejected |

### batch_load_by_ids

<a id="batch_loading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 온다

Given

- 폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.batch_load_by_ids: user-1이 빈 목록으로 일괄 읽음

Then

- 빈 목록이 온다
  - loaded = []

<a id="batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id"></a>

#### [a-user-granted-folder-read-loads-their-own-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더 id로 일괄 읽기를 하면, 그 폴더가 온다

Given

- 자기 개인 폴더 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1 폴더 id로 일괄 읽음

Then

- 심은 폴더 하나가 통째로 온다
  - length = 1
  - [0].id: 심은 폴더와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: 폴더 주인와 같다
  - [0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 만든 사람와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - [0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - [0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - [0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - [0].metadata.created_at: 이 실행이 쓴 시각

<a id="batch_loading-an-accepted-share-loads-someone-elses-folder-by-id"></a>

#### [an-accepted-share-loads-someone-elses-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더 id로 일괄 읽기를 하면, 그 폴더가 온다

Given

- 남의 개인 폴더를 읽기로 공유 제안받아 받아들인, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 공유 제안 share-1: READ 권한으로 제안되고, 아직 답하지 않았다
  - 폴더 공유 제안 share-1: 받는 사람이 받아들임
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 폴더 id로 일괄 읽음

Then

- 심은 폴더 하나가 통째로 온다
  - length = 1
  - [0].id: 심은 폴더와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: 폴더 주인와 같다
  - [0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 만든 사람와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - [0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - [0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - [0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - [0].metadata.created_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

슈퍼관리자가 남의 폴더와 없는 id를 함께 요청하면, 그 폴더는 노드로, 없는 id 자리는 빈 값으로 온다

Given

- 남의 개인 폴더 하나와, 아무 역할도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 폴더와 없는 id를 일괄 읽음

Then

- 있는 폴더는 노드로, 없는 id 자리는 빈 값으로 온다
  - length = 2
  - [0].id: 심은 폴더와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: 폴더 주인와 같다
  - [0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 만든 사람와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - [0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - [0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - [0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - [0].metadata.created_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-batch-load-answers-a-node-or-a-refusal-for-each-id-in-order"></a>

#### [a-batch-load-answers-a-node-or-a-refusal-for-each-id-in-order](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

자기 폴더만 읽을 수 있는 사용자가 자기 폴더, 공유받지 않은 남의 폴더, 없는 id를 한 번에 요청하면, 입력 순서대로 그 폴더, 거부, 거부가 온다

Given

- 자기 개인 폴더 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-2: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1, folder-2, 없는 id 순으로 일괄 읽음

Then

- 입력 순서대로 자리마다 폴더 또는 거부가 온다
  - length = 3
  - [0].id: 심은 폴더와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: 폴더 주인와 같다
  - [0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 만든 사람와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - [0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - [0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - [0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - [0].metadata.created_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

<a id="batch_loading-a-user-granted-nothing-gets-a-refusal-in-place-of-their-own-folder"></a>

#### [a-user-granted-nothing-gets-a-refusal-in-place-of-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 자기 폴더 id로 일괄 읽기를 하면, 호출은 성공하되 그 자리는 권한 부족으로 거부된다

Given

- 자기 개인 폴더 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1 폴더 id로 일괄 읽음

Then

- 그 자리는 권한 부족으로 거부된다
  - length = 1
  - 거부: NotEnoughPermission

<a id="batch_loading-an-unanswered-offer-gets-a-refusal-in-place-of-someone-elses-folder"></a>

#### [an-unanswered-offer-gets-a-refusal-in-place-of-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더 id로 일괄 읽기를 하면, 호출은 성공하되 그 자리는 권한 부족으로 거부된다

Given

- 남의 개인 폴더를 읽기로 공유 제안받아 아직 답하지 않은, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 공유 제안 share-1: READ 권한으로 제안되고, 아직 답하지 않았다
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 폴더 id로 일괄 읽음

Then

- 그 자리는 권한 부족으로 거부된다
  - length = 1
  - 거부: NotEnoughPermission

### project_search

<a id="reaching-a-user-granted-folder-read-in-a-project-lists-its-folder"></a>

#### [a-user-granted-folder-read-in-a-project-lists-its-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

프로젝트에서 폴더 읽기 권한을 받은 사용자가 그 프로젝트의 폴더를 조회하면, 그 프로젝트의 폴더가 온다

Given

- 폴더 하나를 가진 프로젝트와, 그 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 project-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.project_search: user-1이 folder-1 폴더가 놓인 프로젝트의 폴더를 조회

Then

- 심은 폴더 전체가 온다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 심은 폴더와 같다
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'folder-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'group'
  - items[0].ownership.user_id: 폴더 주인와 같다
  - items[0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - items[0].ownership.creator_id: 만든 사람와 같다
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - items[0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - items[0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - items[0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - items[0].metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-a-user-granted-nothing-may-not-list-a-projects-folders"></a>

#### [a-user-granted-nothing-may-not-list-a-projects-folders](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트의 폴더를 조회하려 하면 권한 부족으로 거부된다

Given

- 폴더 하나를 가진 프로젝트와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 project-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.project_search: user-1이 folder-1 폴더가 놓인 프로젝트의 폴더를 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

### scoped_search

<a id="vfolder-a-user-who-has-made-no-folder-lists-none"></a>

#### [a-user-who-has-made-no-folder-lists-none](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다

Given

- 폴더를 놓을 수 있는 도메인과, 거기서 폴더를 만들 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 폴더를 만들 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 folder-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.scoped_search: user-1이 자기 폴더를 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

### create

<a id="vfolder-a-user-granted-folder-create-makes-one-of-their-own"></a>

#### [a-user-granted-folder-create-makes-one-of-their-own](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, 그 폴더의 소유는 그 사용자에게 있다

Given

- 폴더를 놓을 수 있는 도메인과, 거기서 폴더를 만들 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 폴더를 만들 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 folder-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.create: user-1이 work이라는 폴더를 만듦

Then

- 만든 폴더 전체가 오고, 소유는 만든 사람에게 있다
  - host = 'local:volume1'
  - metadata.name = 'work'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 만든 사람와 같다
  - ownership.project_id: 무시함: 개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 무시함: 데이터베이스가 만든다
  - status: 무시함: 폴더가 만들어지는 동안 오가는 값이다
  - metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함: 저장소가 정한다
  - access_control.permission: 무시함: 만든 사람에게는 물어볼 것이 없다
  - quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="vfolder-a-user-granted-nothing-may-not-make-a-folder"></a>

#### [a-user-granted-nothing-may-not-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

아무 권한도 받지 않은 사용자가 폴더를 만들려 하면 권한 부족으로 거부된다

Given

- 폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFolderAdapter.create: user-1이 denied이라는 폴더를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

### get

<a id="reaching-a-user-granted-folder-read-reads-their-own-folder"></a>

#### [a-user-granted-folder-read-reads-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더를 읽으면, 그 폴더가 온다

Given

- 자기 개인 폴더 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-1이 folder-1 폴더를 읽음

Then

- 심은 폴더 전체가 온다
  - id: 심은 폴더와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 폴더 주인와 같다
  - ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-an-accepted-share-reads-someone-elses-folder"></a>

#### [an-accepted-share-reads-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더를 읽으면, 그 폴더가 온다

Given

- 남의 개인 폴더를 읽기로 공유 제안받아 받아들인, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 공유 제안 share-1: READ 권한으로 제안되고, 아직 답하지 않았다
  - 폴더 공유 제안 share-1: 받는 사람이 받아들임
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-2이 folder-1 폴더를 읽음

Then

- 심은 폴더 전체가 온다
  - id: 심은 폴더와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 폴더 주인와 같다
  - ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-a-user-granted-nothing-may-not-read-their-own-folder"></a>

#### [a-user-granted-nothing-may-not-read-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

아무 권한도 받지 않은 사용자가 자기 폴더를 읽으려 하면 권한 부족으로 거부된다

Given

- 자기 개인 폴더 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.get: user-1이 folder-1 폴더를 읽음

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="reaching-an-unanswered-offer-may-not-read-someone-elses-folder"></a>

#### [an-unanswered-offer-may-not-read-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더를 읽으려 하면 권한 부족으로 거부된다

Given

- 남의 개인 폴더를 읽기로 공유 제안받아 아직 답하지 않은, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 공유 제안 share-1: READ 권한으로 제안되고, 아직 답하지 않았다
  - 폴더 읽기 권한 부여
    - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-2이 folder-1 폴더를 읽음

Then

- 거부된다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several"></a>

#### [a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

자기 개인 프로젝트에서 폴더 soft delete 권한을 받은 사용자가 자기 폴더 둘과 남의 폴더 하나를 한 번에 soft delete 하면, 자기 폴더 둘은 삭제 대기로 오고 남의 폴더는 권한 부족으로 실패 목록에 온다

Given

- 자기 개인 폴더 둘을 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 권한 부여
    - 역할 folder-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_delete: user-1이 자기 폴더 둘과 남의 폴더 하나를 한 번에 soft delete 함

Then

- 자기 폴더 둘이 delete-pending 상태로 오고, 남의 폴더는 권한이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 심은 폴더와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'delete-pending'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: 폴더 주인와 같다
  - successes[0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 만든 사람와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - successes[0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - successes[0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - successes[0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 심은 폴더와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'delete-pending'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: 폴더 주인와 같다
  - successes[1].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 만든 사람와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - successes[1].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - successes[1].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - successes[1].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 폴더의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

아무 권한도 받지 않은 사용자가 폴더 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 자기 개인 폴더 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.partial_bulk_delete: user-1이 자기 폴더 둘과 남의 폴더 하나를 한 번에 soft delete 함

Then

- 처리된 폴더 없이 셋 모두 권한이 없다는 이유로 실패 목록에 온다
  - successes = []
  - failed count = 3
  - failed[0].id: 대상 폴더의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 폴더의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유
  - failed[2].id: 대상 폴더의 id와 같다
  - failed[2].message: 'Insufficient permission'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk-restoring-several-folders-brings-them-back"></a>

#### [restoring-several-folders-brings-them-back](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

폴더 soft delete 권한을 받은 사용자가 soft delete 한 자기 폴더 둘을 한 번에 restore 하면, 둘 다 쓸 수 있는 상태로 온다

Given

- 자기 개인 폴더 둘을 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 권한 부여
    - 역할 folder-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_restore: user-1이 자기 폴더 둘을 한 번에 soft delete 했다가 한 번에 restore 함

Then

- 자기 폴더 둘이 ready 상태로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 심은 폴더와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: 폴더 주인와 같다
  - successes[0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 만든 사람와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - successes[0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - successes[0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - successes[0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 심은 폴더와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: 폴더 주인와 같다
  - successes[1].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 만든 사람와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - successes[1].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - successes[1].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - successes[1].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed = []

### partial_bulk_update

<a id="partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several"></a>

#### [a-user-granted-folder-update-updates-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

자기 개인 프로젝트에서 폴더 수정 권한을 받은 사용자가 자기 폴더 둘과 남의 폴더 하나를 한 번에 수정하면, 자기 폴더 둘은 수정되어 오고 남의 폴더는 권한 부족으로 실패 목록에 온다

Given

- 자기 개인 폴더 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 권한 부여
    - 역할 folder-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_update: user-1이 자기 폴더 둘과 남의 폴더 하나를 한 번에 복제 가능으로 바꿈

Then

- 자기 폴더 둘이 복제 가능으로 오고, 남의 폴더는 권한이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 심은 폴더와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = True
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: 폴더 주인와 같다
  - successes[0].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 만든 사람와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - successes[0].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - successes[0].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - successes[0].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 심은 폴더와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = True
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: 폴더 주인와 같다
  - successes[1].ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 만든 사람와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - successes[1].metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - successes[1].access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - successes[1].quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 폴더의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-a-user-granted-nothing-updates-none-of-several-folders"></a>

#### [a-user-granted-nothing-updates-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

아무 권한도 받지 않은 사용자가 폴더 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 자기 개인 폴더 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.partial_bulk_update: user-1이 자기 폴더 둘과 남의 폴더 하나를 한 번에 복제 가능으로 바꿈

Then

- 처리된 폴더 없이 셋 모두 권한이 없다는 이유로 실패 목록에 온다
  - successes = []
  - failed count = 3
  - failed[0].id: 대상 폴더의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 폴더의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유
  - failed[2].id: 대상 폴더의 id와 같다
  - failed[2].message: 'Insufficient permission'를 담은 이유

### update

<a id="editing-a-user-granted-folder-update-renames-their-folder"></a>

#### [a-user-granted-folder-update-renames-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

자기 개인 프로젝트에서 폴더 수정 권한을 받은 사용자가 자기 폴더의 이름과 옵션을 바꾸면, 바뀐 폴더가 온다

Given

- 자기 개인 폴더 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 권한 부여
    - 역할 folder-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.update: user-1이 자기 첫 폴더를 renamed으로 바꾸고 복제 가능으로 바꿈

Then

- 첫 폴더가 renamed이라는 이름과 복제 가능으로 온다
  - vfolder.id: 심은 폴더와 같다
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'ready'
  - vfolder.metadata.name = 'renamed'
  - vfolder.metadata.cloneable = True
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: 폴더 주인와 같다
  - vfolder.ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - vfolder.ownership.creator_id: 만든 사람와 같다
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode: 무시함: 타입이 이미 값을 못박는다
  - vfolder.metadata.quota_scope_id: 무시함: 주인의 id로 만들어져 실행마다 다르다
  - vfolder.access_control.permission: 무시함: 마운트 권한이라 이 표가 묻는 것이 아니다
  - vfolder.quota: 무시함: 저장소가 답하는 값이라 여기서 말할 수 없다
  - vfolder.metadata.created_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-update-their-folder"></a>

#### [a-user-granted-nothing-may-not-update-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

아무 권한도 받지 않은 사용자가 자기 폴더를 바꾸려 하면 권한 부족으로 거부된다

Given

- 자기 개인 폴더 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다

When

- VFolderAdapter.update: user-1이 자기 첫 폴더를 renamed으로 바꾸고 복제 가능으로 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing-renaming-to-a-name-the-owner-already-uses-is-refused"></a>

#### [renaming-to-a-name-the-owner-already-uses-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

자기 다른 폴더가 이미 쓰는 이름으로 바꾸려 하면, 잘못된 값으로 거부된다

Given

- 자기 개인 폴더 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 폴더 하나
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 개인 폴더 first-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 second-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 폴더 권한 부여
    - 역할 folder-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.update: user-1이 자기 첫 폴더를 둘째 폴더의 이름으로 바꾸고 복제 가능으로 바꿈

Then

- 거부된다
  - 거부: VFolderInvalidParameter

