## vfolder_auto_mount

[어댑터](/src/ai/backend/manager/api/adapters/vfolder_auto_mount/adapter.py)

시나리오: 완성

- ops 구성 (4)
  - bulk_get_ids: 대표 성공 ✓ · 대표 거부 ✓
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (1)
  - create: 성공 있음 1 · 거부 있음 1 (scope)

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [자동 마운트 읽기 권한을 받은 사용자가 그 자동 마운트를 id 로 일괄 조회하면, 그 자동 마운트가 응답으로 옵니다](#batch_loading-a-user-granted-auto-mount-read-loads-it-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 자동 마운트를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-gets-a-rejection-for-an-auto-mount) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [자동 마운트 삭제 권한을 받은 사용자가 그 자동 마운트를 soft delete 하면, 삭제된 자동 마운트가 응답으로 옵니다](#deleting-a-user-granted-auto-mount-delete-soft-deletes-it) | 성공 |
| [아무 권한도 받지 않은 사용자가 자동 마운트를 soft delete 하려 하면 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-delete-an-auto-mount) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [자동 마운트가 하나도 등록되지 않은 프로젝트의 자동 마운트를 조회하면, 응답은 비어 있습니다](#searching-a-project-with-no-auto-mount-answers-an-empty-page) | 성공 |
| [프로젝트 범위에서 자동 마운트 읽기 권한을 받은 사용자가 주소 조각으로 걸러 주소 오름차순으로 한 페이지를 조회하면, 걸러진 자동 마운트 둘만 주소 순서로 실린 한 페이지가 응답으로 옵니다](#searching-a-user-granted-auto-mount-read-lists-the-project-auto-mounts) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트의 자동 마운트를 조회하려 하면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-list-project-auto-mounts) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [자동 마운트 수정 권한을 받은 사용자가 그 자동 마운트의 위치와 권한을 바꾸면, 바뀐 자동 마운트가 응답으로 옵니다](#editing-a-user-granted-auto-mount-update-changes-its-destination) | 성공 |
| [아무 권한도 받지 않은 사용자가 자동 마운트를 바꾸려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-change-an-auto-mount) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 자동 마운트 생성 권한을 받은 사용자가 그 프로젝트의 폴더를 자동 마운트로 등록하면, 그 폴더를 가리키는 자동 마운트가 응답으로 옵니다](#creating-a-user-granted-auto-mount-create-registers-a-project-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자동 마운트를 등록하려 하면 권한 부족으로 거부됩니다](#creating-a-user-granted-nothing-may-not-register-an-auto-mount) | 거부 |

### bulk_get_ids

<a id="batch_loading-a-user-granted-auto-mount-read-loads-it-by-id"></a>

#### [a-user-granted-auto-mount-read-loads-it-by-id](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_batch_loading.py): pass

자동 마운트 읽기 권한을 받은 사용자가 그 자동 마운트를 id 로 일괄 조회하면, 그 자동 마운트가 응답으로 옵니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 자동 마운트에 READ 권한을 받은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 프로젝트 범위에서 vfolder 자동 마운트 READ 권한을 받은 사용자 준비
    - 역할 auto-mount-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 auto-mount-user-1: vfolder_auto_mount 전체에 READ 허용
    - 일반 사용자 user-1: 역할 auto-mount-user-1 보유
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.bulk_get_ids: user-1이 자동 마운트를 id 로 일괄 조회합니다

Then

- 자동 마운트 하나가 응답으로 옵니다
  - length = 1
  - id: 응답의 entity_id 와 같다
  - scope_type = 'project'
  - scope_id: 폴더가 놓인 프로젝트와 같다
  - vfolder_id: 자동 마운트한 vfolder 와 같다
  - mount_destination = '/home/work/extra'
  - subpath = '.'
  - mount_permission = 'ro'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-for-an-auto-mount"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 자동 마운트를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 아무 권한도 받지 않은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.bulk_get_ids: user-1이 자동 마운트를 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### delete

<a id="deleting-a-user-granted-auto-mount-delete-soft-deletes-it"></a>

#### [a-user-granted-auto-mount-delete-soft-deletes-it](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_deleting.py): pass

자동 마운트 삭제 권한을 받은 사용자가 그 자동 마운트를 soft delete 하면, 삭제된 자동 마운트가 응답으로 옵니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 자동 마운트에 SOFT_DELETE 권한을 받은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 프로젝트 범위에서 vfolder 자동 마운트 SOFT_DELETE 권한을 받은 사용자 준비
    - 역할 auto-mount-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 auto-mount-user-1: vfolder_auto_mount 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 auto-mount-user-1 보유
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.delete: user-1이 자동 마운트를 soft delete 합니다

Then

- 삭제된 자동 마운트 전체가 응답으로 옵니다
  - id: 응답의 entity_id 와 같다
  - scope_type = 'project'
  - scope_id: 폴더가 놓인 프로젝트와 같다
  - vfolder_id: 자동 마운트한 vfolder 와 같다
  - mount_destination = '/home/work/extra'
  - subpath = '.'
  - mount_permission = 'ro'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-delete-an-auto-mount"></a>

#### [a-user-granted-nothing-may-not-delete-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 자동 마운트를 soft delete 하려 하면 권한 부족으로 거부됩니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 아무 권한도 받지 않은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.delete: user-1이 자동 마운트를 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="searching-a-project-with-no-auto-mount-answers-an-empty-page"></a>

#### [a-project-with-no-auto-mount-answers-an-empty-page](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_searching.py): pass

자동 마운트가 하나도 등록되지 않은 프로젝트의 자동 마운트를 조회하면, 응답은 비어 있습니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 자동 마운트에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 프로젝트 범위에서 vfolder 자동 마운트 READ 권한을 받은 사용자 준비
    - 역할 auto-mount-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 auto-mount-user-1: vfolder_auto_mount 전체에 READ 허용
    - 일반 사용자 user-1: 역할 auto-mount-user-1 보유

When

- VFolderAutoMountAdapter.scoped_search: user-1이 project-1 프로젝트 범위의 자동 마운트를 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-auto-mount-read-lists-the-project-auto-mounts"></a>

#### [a-user-granted-auto-mount-read-lists-the-project-auto-mounts](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_searching.py): pass

프로젝트 범위에서 자동 마운트 읽기 권한을 받은 사용자가 주소 조각으로 걸러 주소 오름차순으로 한 페이지를 조회하면, 걸러진 자동 마운트 둘만 주소 순서로 실린 한 페이지가 응답으로 옵니다

Given

- 주소에 match 가 든 자동 마운트 둘과 들지 않는 자동 마운트 하나를 가진 프로젝트 하나, 그 프로젝트 밖에서 주소에 match 가 든 자동 마운트 하나, 그리고 그 프로젝트 범위에서 자동 마운트 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-1: /home/work/match-one 에 ro 로 마운트됩니다
  - 프로젝트 vfolder folder-2: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-2: /home/work/match-two 에 ro 로 마운트됩니다
  - 프로젝트 vfolder folder-3: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-3: /home/work/other 에 ro 로 마운트됩니다
  - 개인 vfolder folder-4: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-4: /home/work/match-three 에 ro 로 마운트됩니다
  - 프로젝트 범위에서 vfolder 자동 마운트 READ 권한을 받은 사용자 준비
    - 역할 auto-mount-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 auto-mount-user-1: vfolder_auto_mount 전체에 READ 허용
    - 일반 사용자 user-1: 역할 auto-mount-user-1 보유

When

- VFolderAutoMountAdapter.scoped_search: user-1이 project-1 프로젝트 범위의 자동 마운트를 주소에 match 가 든 것만 주소 오름차순으로 2개까지 조회합니다

Then

- 걸러진 자동 마운트 둘만 주소 순서로 실린 한 페이지가 응답으로 옵니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 응답의 entity_id 와 같다
  - items[0].scope_type = 'project'
  - items[0].scope_id: 폴더가 놓인 프로젝트와 같다
  - items[0].vfolder_id: 자동 마운트한 vfolder 와 같다
  - items[0].mount_destination = '/home/work/match-one'
  - items[0].subpath = '.'
  - items[0].mount_permission = 'ro'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].deleted_at = None
  - items[1].id: 응답의 entity_id 와 같다
  - items[1].scope_type = 'project'
  - items[1].scope_id: 폴더가 놓인 프로젝트와 같다
  - items[1].vfolder_id: 자동 마운트한 vfolder 와 같다
  - items[1].mount_destination = '/home/work/match-two'
  - items[1].subpath = '.'
  - items[1].mount_permission = 'ro'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].deleted_at = None
  - items ids: 걸러진 자동 마운트 둘

<a id="searching-a-user-granted-nothing-may-not-list-project-auto-mounts"></a>

#### [a-user-granted-nothing-may-not-list-project-auto-mounts](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_searching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트의 자동 마운트를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 아무 권한도 받지 않은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.scoped_search: user-1이 project-1 프로젝트 범위의 자동 마운트를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-a-user-granted-auto-mount-update-changes-its-destination"></a>

#### [a-user-granted-auto-mount-update-changes-its-destination](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_editing.py): pass

자동 마운트 수정 권한을 받은 사용자가 그 자동 마운트의 위치와 권한을 바꾸면, 바뀐 자동 마운트가 응답으로 옵니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 자동 마운트에 UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 프로젝트 범위에서 vfolder 자동 마운트 UPDATE 권한을 받은 사용자 준비
    - 역할 auto-mount-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 auto-mount-user-1: vfolder_auto_mount 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 auto-mount-user-1 보유
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.update: user-1이 자동 마운트의 위치를 /home/work/edited 로, 권한을 읽기/쓰기로 바꿉니다

Then

- 살아 있는 자동 마운트 전체가 응답으로 옵니다
  - id: 응답의 entity_id 와 같다
  - scope_type = 'project'
  - scope_id: 폴더가 놓인 프로젝트와 같다
  - vfolder_id: 자동 마운트한 vfolder 와 같다
  - mount_destination = '/home/work/edited'
  - subpath = '.'
  - mount_permission = 'rw'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-change-an-auto-mount"></a>

#### [a-user-granted-nothing-may-not-change-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_editing.py): pass

아무 권한도 받지 않은 사용자가 자동 마운트를 바꾸려 하면 권한 부족으로 거부됩니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 아무 권한도 받지 않은 사용자 한 명, 그리고 그 폴더가 자동 마운트된 상태
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 자동 마운트 auto-mount-1: /home/work/extra 에 ro 로 마운트됩니다

When

- VFolderAutoMountAdapter.update: user-1이 자동 마운트의 위치를 /home/work/edited 로, 권한을 읽기/쓰기로 바꿉니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create

<a id="creating-a-user-granted-auto-mount-create-registers-a-project-folder"></a>

#### [a-user-granted-auto-mount-create-registers-a-project-folder](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_creating.py): pass

프로젝트에서 자동 마운트 생성 권한을 받은 사용자가 그 프로젝트의 폴더를 자동 마운트로 등록하면, 그 폴더를 가리키는 자동 마운트가 응답으로 옵니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 자동 마운트에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 프로젝트 범위에서 vfolder 자동 마운트 CREATE 권한을 받은 사용자 준비
    - 역할 auto-mount-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 auto-mount-user-1: vfolder_auto_mount 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 auto-mount-user-1 보유

When

- VFolderAutoMountAdapter.create: user-1이 project-1 프로젝트의 folder-1 vfolder 를 /home/work/extra 에 자동 마운트합니다

Then

- 살아 있는 자동 마운트 전체가 응답으로 옵니다
  - id: 응답의 entity_id 와 같다
  - scope_type = 'project'
  - scope_id: 폴더가 놓인 프로젝트와 같다
  - vfolder_id: 자동 마운트한 vfolder 와 같다
  - mount_destination = '/home/work/extra'
  - subpath = '.'
  - mount_permission = 'ro'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="creating-a-user-granted-nothing-may-not-register-an-auto-mount"></a>

#### [a-user-granted-nothing-may-not-register-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_creating.py): pass

아무 권한도 받지 않은 사용자가 자동 마운트를 등록하려 하면 권한 부족으로 거부됩니다

Given

- 프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAutoMountAdapter.create: user-1이 project-1 프로젝트의 folder-1 vfolder 를 /home/work/extra 에 자동 마운트합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

