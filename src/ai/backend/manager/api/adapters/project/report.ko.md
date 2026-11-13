## project

[배경](/src/ai/backend/manager/api/adapters/project/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/project/adapter.py)

시나리오: 미완성 14 / 17

- ops 구성 (10)
  - admin_search: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - delete: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - get: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_delete: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_restore: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - restore: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - scoped_search: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - search_by_domain_name: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - search_by_user: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
- ops + 직접 구현 (4)
  - assign_users: 성공 있음 1 · 거부 있음 1 (atomic_bulk_get_ops, partial_bulk_get_ops, relation)
  - partial_bulk_update: 성공 있음 3 · 거부 없음 (partial_bulk, partial_bulk_delete_ops, partial_bulk_restore_ops): SCENARIO-GAP
  - unassign_users: 성공 없음 · 거부 없음 (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - update: 성공 있음 2 · 거부 없음 (single_delete_ops, single_entity, single_restore_ops): SCENARIO-GAP
- 직접 구현 (3)
  - admin_create: 성공 있음 1 · 거부 있음 1 (scope)
  - admin_purge: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - batch_load_registries: 성공 있음 3 · 거부 있음 1 (partial_bulk)

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects) | 성공 |
| [활성 프로젝트 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 프로젝트 여럿을 한 번에 restore 하면, 모두 활성으로 옵니다](#partial_bulk_deleting-restoring-several-brings-them-back) | 성공 |

**assign_users**

| 시나리오 | 판정 |
|---|---|
| [사용자를 만들 권한과 지정한 역할을 부여할 권한을 모두 받은 호출자가 그 역할로 사용자를 배정하면, 그 사용자가 멤버 목록에 오릅니다](#project-assigning-a-user-to-a-project-puts-them-on-its-roster) | 성공 |
| [배정은 지정한 역할을 부여할 권한까지 요구하므로, 사용자를 만들 권한만 받은 호출자는 권한 부족으로 거부됩니다](#project-a-caller-who-may-not-grant-the-role-may-not-assign-a-user-with-it) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-projects) | 성공 |
| [활성 플래그와 설명을 섞어 프로젝트 여럿을 한 번에 수정하면, 플래그를 내린 것은 soft delete 되고 올린 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-projects) | 성공 |
| [superadmin 이 프로젝트 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-projects-at-once) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [활성 플래그를 내리는 수정은 프로젝트를 soft delete 하고, 응답이 비활성 상태를 담아 옵니다](#editing-clearing-the-active-flag-soft-deletes-a-project) | 성공 |
| [soft delete 된 프로젝트의 활성 플래그를 올리는 수정은 그 프로젝트를 restore 하고, 응답이 활성 상태를 담아 옵니다](#editing-raising-the-active-flag-restores-a-soft-deleted-project) | 성공 |

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [도메인과 프로젝트 정책이 있을 때 superadmin 이 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생깁니다](#project-the-superadmin-makes-a-project-in-a-domain) | 성공 |
| [프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부됩니다](#project-a-user-granted-nothing-may-not-make-a-project) | 거부 |

**batch_load_registries**

| 시나리오 | 판정 |
|---|---|
| [읽기 권한이 있으면 default 가 아닌 허용된 Container Registry 도 default 가 아니라는 표시와 함께 응답합니다](#registries-read-allowed-registry) | 성공 |
| [읽기 권한이 있으면 default 로 허용된 Container Registry 를 default 라는 표시와 함께 응답합니다](#registries-read-default-registry) | 성공 |
| [읽기 권한이 있고 허용된 Container Registry 가 없으면 빈 목록을 응답합니다](#registries-read-no-registry) | 성공 |
| [읽기 권한이 없으면 허용된 Container Registry 조회를 거부합니다](#registries-registries-read-requires-permission) | 거부 |

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.partial_bulk_delete: user-1이 프로젝트 2개를 한 번에 soft delete 합니다

Then

- 처리된 프로젝트 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 프로젝트의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 프로젝트의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

활성 프로젝트 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.partial_bulk_delete: user-1이 프로젝트 2개 와 없는 id 하나를 한 번에 soft delete 합니다

Then

- 대상 프로젝트가 모두 비활성으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'team-1 was already here'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = False
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = 'team-2 was already here'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = False
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

soft delete 된 프로젝트 여럿을 한 번에 restore 하면, 모두 활성으로 옵니다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.partial_bulk_restore: user-1이 프로젝트 2개를 한 번에 soft delete 했다가 한 번에 restore 합니다

Then

- 대상 프로젝트가 모두 활성으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'team-1 was already here'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = True
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = 'team-2 was already here'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed = []

### assign_users

<a id="project-assigning-a-user-to-a-project-puts-them-on-its-roster"></a>

#### [assigning-a-user-to-a-project-puts-them-on-its-roster](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

사용자를 만들 권한과 지정한 역할을 부여할 권한을 모두 받은 호출자가 그 역할로 사용자를 배정하면, 그 사용자가 멤버 목록에 오릅니다

Given

- 프로젝트 하나와 그 프로젝트 스코프의 역할, 배정할 사용자, 그리고 도메인 스코프의 사용자 READ 와 CREATE 를 받은 호출자. 호출자는 역할 CREATE 를 받았습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 project-member-1: 부여된 스코프 안에서만 적용됩니다
  - 사용자 READ, CREATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
  - 역할 role-granter-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-granter-1: role 전체에 CREATE 허용
  - 일반 사용자 user-2: 역할 role-granter-1 보유

When

- ProjectAdapter.assign_users: user-2이 user-1을 research-1에 배정합니다

Then

- 멤버 목록에 배정한 사람만 올라 있습니다
  - items: 배정한 사람 하나와 같다

<a id="project-a-caller-who-may-not-grant-the-role-may-not-assign-a-user-with-it"></a>

#### [a-caller-who-may-not-grant-the-role-may-not-assign-a-user-with-it](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

배정은 지정한 역할을 부여할 권한까지 요구하므로, 사용자를 만들 권한만 받은 호출자는 권한 부족으로 거부됩니다

Given

- 프로젝트 하나와 그 프로젝트 스코프의 역할, 배정할 사용자, 그리고 도메인 스코프의 사용자 READ 와 CREATE 를 받은 호출자. 호출자는 역할 CREATE 를 받지 않았습니다
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 project-member-1: 부여된 스코프 안에서만 적용됩니다
  - 사용자 READ, CREATE 권한을 부여한 역할 배정
    - 역할 user-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- ProjectAdapter.assign_users: user-2이 user-1을 research-1에 배정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-projects"></a>

#### [a-user-granted-nothing-edits-none-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.partial_bulk_update: user-1이 프로젝트 2개의 설명을 한 번에 수정합니다

Then

- 처리된 프로젝트 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 프로젝트의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 프로젝트의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-projects"></a>

#### [the-active-flag-soft-deletes-or-restores-each-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

활성 플래그와 설명을 섞어 프로젝트 여럿을 한 번에 수정하면, 플래그를 내린 것은 soft delete 되고 올린 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.partial_bulk_update: user-1이 둘째 프로젝트를 soft delete 한 뒤, 첫째는 활성 플래그를 내리고 둘째는 올리며 둘의 설명을 변경하고, 없는 id 하나의 활성 플래그를 내립니다

Then

- 둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이며, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = False
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-projects-at-once"></a>

#### [the-superadmin-edits-several-projects-at-once](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

superadmin 이 프로젝트 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 한 도메인 아래의 프로젝트 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 team-2
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.partial_bulk_update: user-1이 프로젝트 2개의 설명을 한 번에 수정합니다

Then

- 대상 프로젝트가 모두 새 설명으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].name = 'team-1'
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = True
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[0].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'team-2'
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].type: 건너뜀: 타입이 이미 값을 고정합니다
  - successes[1].entity_id: 미리 저장한 프로젝트의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각

### update

<a id="editing-clearing-the-active-flag-soft-deletes-a-project"></a>

#### [clearing-the-active-flag-soft-deletes-a-project](/tests/scenario/bai_scenario/manager/project/test_editing.py): pass

활성 플래그를 내리는 수정은 프로젝트를 soft delete 하고, 응답이 비활성 상태를 담아 옵니다

Given

- 한 도메인 아래의 프로젝트 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.update: user-1이 team-1의 활성 플래그를 수정합니다

Then

- 미리 저장한 프로젝트 전체가 응답으로 옵니다
  - name = 'team-1'
  - description = 'team-1 was already here'
  - integration_name = None
  - domain_name = 'target-1'
  - resource_policy = 'default'
  - allowed_vfolder_hosts = []
  - is_active = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - type: 건너뜀: 타입이 이미 값을 고정합니다
  - entity_id: 미리 저장한 프로젝트의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-raising-the-active-flag-restores-a-soft-deleted-project"></a>

#### [raising-the-active-flag-restores-a-soft-deleted-project](/tests/scenario/bai_scenario/manager/project/test_editing.py): pass

soft delete 된 프로젝트의 활성 플래그를 올리는 수정은 그 프로젝트를 restore 하고, 응답이 활성 상태를 담아 옵니다

Given

- 한 도메인 아래의 프로젝트 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.update: user-1이 team-1을 soft delete 한 뒤 활성 플래그를 수정합니다

Then

- 미리 저장한 프로젝트 전체가 응답으로 옵니다
  - name = 'team-1'
  - description = 'team-1 was already here'
  - integration_name = None
  - domain_name = 'target-1'
  - resource_policy = 'default'
  - allowed_vfolder_hosts = []
  - is_active = True
  - id: 건너뜀: 데이터베이스가 생성합니다
  - type: 건너뜀: 타입이 이미 값을 고정합니다
  - entity_id: 미리 저장한 프로젝트의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

### admin_create

<a id="project-the-superadmin-makes-a-project-in-a-domain"></a>

#### [the-superadmin-makes-a-project-in-a-domain](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

도메인과 프로젝트 정책이 있을 때 superadmin 이 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생깁니다

Given

- 도메인 하나와 프로젝트 정책, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.admin_create: user-1이 home-1 아래에 research 을 만듭니다

Then

- 만든 프로젝트 전체가 응답으로 옵니다
  - basic_info.name = 'research'
  - basic_info.description = None
  - basic_info.integration_name = None
  - organization.domain_name = 'home-1'
  - organization.resource_policy = 'default'
  - storage.allowed_vfolder_hosts = []
  - lifecycle.is_active = True
  - id: 건너뜀: 데이터베이스가 생성합니다
  - basic_info.type: 건너뜀: 타입이 이미 값을 고정합니다
  - lifecycle.created_at: 이 실행이 쓴 시각
  - lifecycle.modified_at: 이 실행이 쓴 시각

<a id="project-a-user-granted-nothing-may-not-make-a-project"></a>

#### [a-user-granted-nothing-may-not-make-a-project](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부됩니다

Given

- 도메인 하나와 프로젝트 정책, 그리고 user 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.admin_create: user-1이 home-1 아래에 refused 을 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### batch_load_registries

<a id="registries-read-allowed-registry"></a>

#### [read-allowed-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 있으면 default 가 아닌 허용된 Container Registry 도 default 가 아니라는 표시와 함께 응답합니다

Given

- 프로젝트가 레지스트리에 허용돼 있지만 default 는 아닙니다. 일반 사용자는 프로젝트 읽기 권한이 있습니다.
  - 도메인 domain-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 프로젝트 project-1 가 허용한 컨테이너 레지스트리 registry-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트의 허용된 Container Registry 를 두 번 요청합니다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답합니다
  - count = 2
  - [0] count = 1
  - [0][0].registry: 미리 저장한 레지스트리와 같다
  - [0][0].is_default = False
  - [1] count = 1
  - [1][0].registry: 미리 저장한 레지스트리와 같다
  - [1][0].is_default = False

<a id="registries-read-default-registry"></a>

#### [read-default-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 있으면 default 로 허용된 Container Registry 를 default 라는 표시와 함께 응답합니다

Given

- 프로젝트가 레지스트리에 default 로 허용돼 있습니다. 일반 사용자는 프로젝트 읽기 권한이 있습니다.
  - 도메인 domain-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 프로젝트 project-1 가 default 컨테이너 레지스트리로 허용한 컨테이너 레지스트리 registry-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트의 허용된 Container Registry 를 두 번 요청합니다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답합니다
  - count = 2
  - [0] count = 1
  - [0][0].registry: 미리 저장한 레지스트리와 같다
  - [0][0].is_default = True
  - [1] count = 1
  - [1][0].registry: 미리 저장한 레지스트리와 같다
  - [1][0].is_default = True

<a id="registries-read-no-registry"></a>

#### [read-no-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 있고 허용된 Container Registry 가 없으면 빈 목록을 응답합니다

Given

- 프로젝트에 허용된 레지스트리가 없습니다. 일반 사용자는 프로젝트 읽기 권한이 있습니다.
  - 도메인 domain-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트의 허용된 Container Registry 를 두 번 요청합니다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답합니다
  - count = 2
  - [0] count = 0
  - [1] count = 0

<a id="registries-registries-read-requires-permission"></a>

#### [registries-read-requires-permission](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

읽기 권한이 없으면 허용된 Container Registry 조회를 거부합니다

Given

- 프로젝트에 허용된 레지스트리가 없습니다. 일반 사용자는 프로젝트 읽기 권한이 없습니다.
  - 도메인 domain-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳, 프로젝트는 images
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ProjectAdapter.batch_load_registries: 같은 프로젝트의 허용된 Container Registry 를 두 번 요청합니다

Then

- 요청마다 허용된 Container Registry 목록이나 권한 거부를 응답합니다
  - count = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

