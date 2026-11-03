## project

[background](/src/ai/backend/manager/api/adapters/project/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/project/adapter.py)

Scenario: incomplete 15 / 17

- built from ops (10)
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_by_domain_name: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_by_user: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- ops + direct implementation (4)
  - assign_users: success present 1 · rejection absent (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - partial_bulk_update: success present 3 · rejection absent (partial_bulk, partial_bulk_delete_ops, partial_bulk_restore_ops): SCENARIO-GAP
  - unassign_users: success absent · rejection absent (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - update: success present 2 · rejection absent (single_delete_ops, single_entity, single_restore_ops): SCENARIO-GAP
- direct implementation (3)
  - admin_create: success present 1 · rejection present 1 (scope)
  - admin_purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - batch_load_registries: success present 3 · rejection present 1 (partial_bulk)

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects) | answered |
| [활성 프로젝트 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [soft delete 된 프로젝트 여럿을 한 번에 restore 하면, 모두 활성으로 온다](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**assign_users**

| scenario | verdict |
|---|---|
| [프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, 그 사용자가 명부에 오른다](#project-assigning-a-user-to-a-project-puts-them-on-its-roster) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-projects) | answered |
| [활성 플래그와 설명을 섞어 프로젝트 여럿을 한 번에 고치면, 플래그를 내린 것은 soft delete 되고 올린 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-projects) | answered |
| [슈퍼관리자가 프로젝트 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-edits-several-projects-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [활성 플래그를 내리는 수정은 프로젝트를 soft delete 하고, 답이 비활성 상태를 실어 온다](#editing-clearing-the-active-flag-soft-deletes-a-project) | answered |
| [soft delete 된 프로젝트의 활성 플래그를 올리는 수정은 그 프로젝트를 restore 하고, 답이 활성 상태를 실어 온다](#editing-raising-the-active-flag-restores-a-soft-deleted-project) | answered |

**admin_create**

| scenario | verdict |
|---|---|
| [도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생긴다](#project-the-superadmin-makes-a-project-in-a-domain) | answered |
| [프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다](#project-a-user-granted-nothing-may-not-make-a-project) | rejected |

**batch_load_registries**

| scenario | verdict |
|---|---|
| [읽기 권한이 있으면 default가 아닌 허용된 Container Registry도 default가 아니라는 표시와 함께 응답한다](#registries-read-allowed-registry) | answered |
| [읽기 권한이 있으면 default로 허용된 Container Registry를 default라는 표시와 함께 응답한다](#registries-read-default-registry) | answered |
| [읽기 권한이 있고 허용된 Container Registry가 없으면 빈 목록을 응답한다](#registries-read-no-registry) | answered |
| [읽기 권한이 없으면 허용된 Container Registry 조회를 거부한다](#registries-registries-read-requires-permission) | rejected |

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.partial_bulk_delete: user-1이 프로젝트 2개를 한 번에 soft delete 함

Then

- 처리된 프로젝트 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 프로젝트의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 프로젝트의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

활성 프로젝트 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.partial_bulk_delete: user-1이 프로젝트 2개 와 없는 id 하나를 한 번에 soft delete 함

Then

- 대상 프로젝트가 모두 비활성으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'team-1 was already here'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = False
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].type: 무시함: 타입이 이미 값을 못박는다
  - successes[0].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = 'team-2 was already here'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = False
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].type: 무시함: 타입이 이미 값을 못박는다
  - successes[1].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

soft delete 된 프로젝트 여럿을 한 번에 restore 하면, 모두 활성으로 온다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.partial_bulk_restore: user-1이 프로젝트 2개를 한 번에 soft delete 했다가 한 번에 restore 함

Then

- 대상 프로젝트가 모두 활성으로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'team-1 was already here'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = True
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].type: 무시함: 타입이 이미 값을 못박는다
  - successes[0].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = 'team-2 was already here'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].type: 무시함: 타입이 이미 값을 못박는다
  - successes[1].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed = []

### assign_users

<a id="project-assigning-a-user-to-a-project-puts-them-on-its-roster"></a>

#### [assigning-a-user-to-a-project-puts-them-on-its-roster](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, 그 사용자가 명부에 오른다

Given

- 프로젝트 하나와 그 프로젝트 스코프의 역할, 올릴 사용자, 그리고 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 project-member-1: 이 역할이 앉은 스코프 안에서만 통한다

When

- ProjectAdapter.assign_users: user-2이 user-1을 research-1에 배정

Then

- 명부에 배정한 사람만 올라 있다
  - items: 배정한 사람 하나와 같다

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-projects"></a>

#### [a-user-granted-nothing-edits-none-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.partial_bulk_update: user-1이 프로젝트 2개의 설명을 한 번에 고침

Then

- 처리된 프로젝트 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 프로젝트의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 프로젝트의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-projects"></a>

#### [the-active-flag-soft-deletes-or-restores-each-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

활성 플래그와 설명을 섞어 프로젝트 여럿을 한 번에 고치면, 플래그를 내린 것은 soft delete 되고 올린 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.partial_bulk_update: user-1이 둘째 프로젝트를 soft delete 한 뒤, 첫째는 활성 플래그를 내리고 둘째는 올리며 둘의 설명을 바꾸고, 없는 id 하나의 활성 플래그를 내림

Then

- 둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이며, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = '한 번에 고친 설명'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = False
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].type: 무시함: 타입이 이미 값을 못박는다
  - successes[0].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = '한 번에 고친 설명'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].type: 무시함: 타입이 이미 값을 못박는다
  - successes[1].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-projects-at-once"></a>

#### [the-superadmin-edits-several-projects-at-once](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

슈퍼관리자가 프로젝트 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.partial_bulk_update: user-1이 프로젝트 2개의 설명을 한 번에 고침

Then

- 대상 프로젝트가 모두 새 설명으로 오고, 실패한 것은 없다
  - successes count = 2
  - failed = []
  - successes[0].name = 'team-1'
  - successes[0].description = '한 번에 고친 설명'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = True
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].type: 무시함: 타입이 이미 값을 못박는다
  - successes[0].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = '한 번에 고친 설명'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].type: 무시함: 타입이 이미 값을 못박는다
  - successes[1].entity_id: 미리 만든 프로젝트의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각

### update

<a id="editing-clearing-the-active-flag-soft-deletes-a-project"></a>

#### [clearing-the-active-flag-soft-deletes-a-project](/tests/scenario/bai_scenario/manager/project/test_editing.py): pass

활성 플래그를 내리는 수정은 프로젝트를 soft delete 하고, 답이 비활성 상태를 실어 온다

Given

- 한 도메인 아래의 프로젝트 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.update: user-1이 team-1을 활성 플래그을 고침

Then

- 미리 만든 프로젝트 전체가 온다
  - name = 'team-1'
  - description = 'team-1 was already here'
  - integration_name = None
  - domain_name = 'target-1'
  - resource_policy = 'default'
  - allowed_vfolder_hosts = []
  - is_active = False
  - id: 무시함: 데이터베이스가 만든다
  - type: 무시함: 타입이 이미 값을 못박는다
  - entity_id: 미리 만든 프로젝트의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-raising-the-active-flag-restores-a-soft-deleted-project"></a>

#### [raising-the-active-flag-restores-a-soft-deleted-project](/tests/scenario/bai_scenario/manager/project/test_editing.py): pass

soft delete 된 프로젝트의 활성 플래그를 올리는 수정은 그 프로젝트를 restore 하고, 답이 활성 상태를 실어 온다

Given

- 한 도메인 아래의 프로젝트 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.update: user-1이 team-1을 soft delete 한 뒤 활성 플래그을 고침

Then

- 미리 만든 프로젝트 전체가 온다
  - name = 'team-1'
  - description = 'team-1 was already here'
  - integration_name = None
  - domain_name = 'target-1'
  - resource_policy = 'default'
  - allowed_vfolder_hosts = []
  - is_active = True
  - id: 무시함: 데이터베이스가 만든다
  - type: 무시함: 타입이 이미 값을 못박는다
  - entity_id: 미리 만든 프로젝트의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

### admin_create

<a id="project-the-superadmin-makes-a-project-in-a-domain"></a>

#### [the-superadmin-makes-a-project-in-a-domain](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생긴다

Given

- 도메인 하나와 프로젝트 정책, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create: user-1이 home-1 아래에 research을 만듦

Then

- 만든 프로젝트 전체가 온다
  - basic_info.name = 'research'
  - basic_info.description = None
  - basic_info.integration_name = None
  - organization.domain_name = 'home-1'
  - organization.resource_policy = 'default'
  - storage.allowed_vfolder_hosts = []
  - lifecycle.is_active = True
  - id: 무시함: 데이터베이스가 만든다
  - basic_info.type: 무시함: 타입이 이미 값을 못박는다
  - lifecycle.created_at: 이 실행이 쓴 시각
  - lifecycle.modified_at: 이 실행이 쓴 시각

<a id="project-a-user-granted-nothing-may-not-make-a-project"></a>

#### [a-user-granted-nothing-may-not-make-a-project](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다

Given

- 도메인 하나와 프로젝트 정책, 그리고 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create: user-1이 home-1 아래에 refused을 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

### batch_load_registries

<a id="registries-read-allowed-registry"></a>

#### [read-allowed-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 있으면 default가 아닌 허용된 Container Registry도 default가 아니라는 표시와 함께 응답한다

Given

- 프로젝트가 레지스트리에 허용돼 있지만 default는 아니다. 일반 사용자는 프로젝트 읽기 권한이 있다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 프로젝트 project-1 을 허용한 컨테이너 레지스트리 registry-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트가 허용된 Container Registry를 두 번 요청한다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답한다
  - count = 2
  - [0] count = 1
  - [0][0].registry: 심은 레지스트리와 같다
  - [0][0].is_default = False
  - [1] count = 1
  - [1][0].registry: 심은 레지스트리와 같다
  - [1][0].is_default = False

<a id="registries-read-default-registry"></a>

#### [read-default-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 있으면 default로 허용된 Container Registry를 default라는 표시와 함께 응답한다

Given

- 프로젝트가 레지스트리에 default로 허용돼 있다. 일반 사용자는 프로젝트 읽기 권한이 있다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 프로젝트 project-1 을 default 레지스트리로 허용한 컨테이너 레지스트리 registry-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트가 허용된 Container Registry를 두 번 요청한다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답한다
  - count = 2
  - [0] count = 1
  - [0][0].registry: 심은 레지스트리와 같다
  - [0][0].is_default = True
  - [1] count = 1
  - [1][0].registry: 심은 레지스트리와 같다
  - [1][0].is_default = True

<a id="registries-read-no-registry"></a>

#### [read-no-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 있고 허용된 Container Registry가 없으면 빈 목록을 응답한다

Given

- 프로젝트가 허용된 레지스트리가 없다. 일반 사용자는 프로젝트 읽기 권한이 있다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트가 허용된 Container Registry를 두 번 요청한다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답한다
  - count = 2
  - [0] count = 0
  - [1] count = 0

<a id="registries-registries-read-requires-permission"></a>

#### [registries-read-requires-permission](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 없으면 허용된 Container Registry 조회를 거부한다

Given

- 프로젝트가 허용된 레지스트리가 없다. 일반 사용자는 프로젝트 읽기 권한이 없다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트가 허용된 Container Registry를 두 번 요청한다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답한다
  - count = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

