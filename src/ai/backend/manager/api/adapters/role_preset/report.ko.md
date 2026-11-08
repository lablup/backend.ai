## role_preset

[배경](/src/ai/backend/manager/api/adapters/role_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/role_preset/adapter.py)

시나리오: 미완성 11 / 21

- ops 구성 (14)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_permissions_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_delete: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - bulk_purge: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - bulk_restore: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_delete: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_restore: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - restore: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✓
  - search_permission_presets: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (7)
  - atomic_bulk_add_permissions: 성공 있음 1 · 거부 있음 1 (single_entity)
  - bulk_add_permissions: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - bulk_remove_permissions: 성공 없음 · 거부 없음 (partial_bulk_field): SCENARIO-GAP
  - create: 성공 있음 1 · 거부 없음 (scope): SCENARIO-GAP
  - partial_bulk_remove_permissions: 성공 있음 2 · 거부 없음 (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_update: 성공 있음 3 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - update: 성공 있음 2 · 거부 있음 2 (single_entity)

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [global 에서 조회 권한을 받은 사용자가 프리셋 둘의 id 를 한 번에 조회하면, 둘 다 요청한 순서대로 각각 전체가 반환됩니다](#reading-a-user-granted-read-loads-many-presets-in-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋 둘의 id 를 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#reading-a-user-granted-nothing-loading-many-presets-is-denied-on-every-id) | 거부 |

**batch_load_permissions_by_ids**

| 시나리오 | 판정 |
|---|---|
| [global 에서 조회 권한을 받은 사용자가 프리셋의 권한 항목 둘의 id 를 한 번에 조회하면, 둘 다 요청한 순서대로 각각 전체가 반환됩니다](#permission_reading-a-user-granted-read-loads-permission-entries-in-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 권한 항목 둘의 id 를 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#permission_reading-a-user-granted-nothing-loading-entries-is-denied-on-every-id) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 프리셋을 soft delete 하면, 삭제로 표시된 프리셋 전체가 응답으로 옵니다](#deleting-the-superadmin-soft-deletes-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 soft delete 하려 하면, 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-soft-delete-a-preset) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [global 에서 조회 권한을 받은 사용자가 id 로 조회하면, 미리 저장한 프리셋 전체가 반환됩니다](#reading-a-user-granted-read-reads-a-preset-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 id 로 조회하려 하면, 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-a-preset) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-presets) | 성공 |
| [프리셋 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제로 표시된 채 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-presets) | 성공 |
| [프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 하기 전의 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-purging-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 프리셋 여럿을 한 번에 restore 하면, 모두 삭제로 표시되지 않은 채 옵니다](#partial_bulk_deleting-restoring-several-brings-them-back) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 프리셋을 purge 하면, purge 하기 전의 프리셋 전체가 응답으로 옵니다](#deleting-the-superadmin-purges-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면, 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-purge-a-preset) | 거부 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 프리셋을 restore 하면, 삭제로 표시되지 않은 프리셋 전체가 응답으로 옵니다](#deleting-restoring-a-soft-deleted-preset-brings-it-back) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 restore 하려 하면, 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-restore-a-preset) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 검색하면, 맞는 프리셋 가운데 정렬상 첫 하나만 오고 나머지는 오지 않습니다. 이 호출은 global 역할이 막습니다](#searching-the-superadmin-finds-one-page-of-matching-presets) | 성공 |
| [global 역할이 없는 사용자가 프리셋을 검색하려 하면, 권한 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-presets) | 거부 |

**search_permission_presets**

| 시나리오 | 판정 |
|---|---|
| [global 에서 조회 권한을 받은 사용자가 권한 항목을 조회 비트 필터, 엔티티 타입 정렬, 한 페이지 크기로 검색하면, 맞는 항목 가운데 정렬상 첫 하나만 오고 나머지 맞는 항목, 필터에 걸리는 항목, 다른 프리셋의 항목은 오지 않습니다](#permission_reading-a-user-granted-read-finds-one-page-of-matching-entries) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋의 권한 항목을 검색하려 하면, 요청 전체가 권한 부족으로 거부됩니다](#permission_reading-a-user-granted-nothing-may-not-search-permission-entries) | 거부 |

**atomic_bulk_add_permissions**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 항목 없는 프리셋에 권한 항목 둘을 추가하면, 추가한 두 항목이 그 프리셋 아래에 옵니다](#permission_editing-the-superadmin-adds-entries-to-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋에 권한 항목을 추가하려 하면, 권한 부족으로 거부됩니다](#permission_editing-a-user-granted-nothing-may-not-add-entries) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 스코프 프리셋을 소유자 부여를 켜고 만들면, 켜진 프리셋이 응답으로 옵니다](#creating-a-project-preset-is-made-with-owner-assign) | 성공 |

**partial_bulk_remove_permissions**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 권한 항목 여럿을 한 번에 제거하려 하면, 제거된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#permission_editing-a-user-granted-nothing-removes-none-of-the-entries) | 성공 |
| [superadmin 이 권한 항목 둘과 없는 id 하나를 한 번에 제거하면, 둘은 처리된 목록에 오고 없는 id 는 실패 목록에 옵니다](#permission_editing-removing-entries-answers-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | 성공 |
| [프로젝트 스코프와 도메인 스코프 프리셋의 소유자 부여를 한 번에 켜면, 프로젝트 스코프 프리셋만 수정되고 도메인 스코프 프리셋은 실패 목록에 옵니다](#partial_bulk_editing-only-the-project-preset-takes-owner-assign) | 성공 |
| [superadmin 이 프리셋 여럿의 자동 부여를 한 번에 켜면, 모두 새 값으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [프로젝트 스코프 프리셋의 소유자 부여를 켜면, 켜진 프리셋 전체가 응답으로 옵니다](#editing-a-project-preset-takes-owner-assign) | 성공 |
| [superadmin 이 프리셋 이름을 변경하면, 새 이름을 담은 프리셋 전체가 응답으로 옵니다](#editing-the-superadmin-renames-a-preset) | 성공 |
| [프로젝트 외 스코프 프리셋의 소유자 부여를 켜려 하면, 소유자가 없어 거부됩니다](#editing-a-domain-preset-refuses-owner-assign) | 거부 |
| [아무 권한도 받지 않은 사용자가 프리셋 이름을 변경하려 하면, 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-rename-a-preset) | 거부 |

### batch_load_by_ids

<a id="reading-a-user-granted-read-loads-many-presets-in-order"></a>

#### [a-user-granted-read-loads-many-presets-in-order](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

global 에서 조회 권한을 받은 사용자가 프리셋 둘의 id 를 한 번에 조회하면, 둘 다 요청한 순서대로 각각 전체가 반환됩니다

Given

- 프리셋 2개와, global 에서 READ 권한을 받은 user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - global 에서 역할 프리셋 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 preset-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 preset-reader-1: role_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 preset-reader-1 보유

When

- RolePresetAdapter.batch_load_by_ids: user-1이 미리 저장한 프리셋 2개의 id 를 한 번에 조회합니다

Then

- 미리 저장한 프리셋이 요청한 순서대로 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 프리셋의 id 와 같다
  - [0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - [0].name = 'preset-1'
  - [0].scope_type = 'project'
  - [0].role_name_template = None
  - [0].auto_assign = False
  - [0].auto_assign_to_owner = False
  - [0].deleted = False
  - [0].deleted_at = None
  - [0].created_at: 미리 저장한 프리셋의 시각와 같다
  - [0].updated_at: 미리 저장한 프리셋의 시각와 같다
  - [1].id: 미리 저장한 프리셋의 id 와 같다
  - [1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - [1].name = 'preset-2'
  - [1].scope_type = 'project'
  - [1].role_name_template = None
  - [1].auto_assign = False
  - [1].auto_assign_to_owner = False
  - [1].deleted = False
  - [1].deleted_at = None
  - [1].created_at: 미리 저장한 프리셋의 시각와 같다
  - [1].updated_at: 미리 저장한 프리셋의 시각와 같다

<a id="reading-a-user-granted-nothing-loading-many-presets-is-denied-on-every-id"></a>

#### [a-user-granted-nothing-loading-many-presets-is-denied-on-every-id](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

아무 권한도 받지 않은 사용자가 프리셋 둘의 id 를 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.batch_load_by_ids: user-1이 미리 저장한 프리셋 2개의 id 를 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### batch_load_permissions_by_ids

<a id="permission_reading-a-user-granted-read-loads-permission-entries-in-order"></a>

#### [a-user-granted-read-loads-permission-entries-in-order](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

global 에서 조회 권한을 받은 사용자가 프리셋의 권한 항목 둘의 id 를 한 번에 조회하면, 둘 다 요청한 순서대로 각각 전체가 반환됩니다

Given

- 권한 항목 둘을 가진 프리셋 하나와, global 에서 READ 권한을 받은 user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용
  - 도메인 home-1
  - global 에서 역할 프리셋 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 preset-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 preset-reader-1: role_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 preset-reader-1 보유

When

- RolePresetAdapter.batch_load_permissions_by_ids: user-1이 preset-1의 권한 항목 2개의 id 를 한 번에 조회합니다

Then

- 미리 저장한 권한 항목이 요청한 순서대로 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 항목의 id 와 같다
  - [0].field_id: 미리 저장한 항목의 id 와 같다
  - [0].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - [0].entity_type = 'domain'
  - [0].permission = <PermissionBitDTO.READ: 'read'>
  - [0].created_at: 미리 저장한 항목의 시각와 같다
  - [1].id: 미리 저장한 항목의 id 와 같다
  - [1].field_id: 미리 저장한 항목의 id 와 같다
  - [1].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - [1].entity_type = 'project'
  - [1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - [1].created_at: 미리 저장한 항목의 시각와 같다

<a id="permission_reading-a-user-granted-nothing-loading-entries-is-denied-on-every-id"></a>

#### [a-user-granted-nothing-loading-entries-is-denied-on-every-id](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

아무 권한도 받지 않은 사용자가 권한 항목 둘의 id 를 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- 권한 항목 둘을 가진 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.batch_load_permissions_by_ids: user-1이 preset-1의 권한 항목 2개의 id 를 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### delete

<a id="deleting-the-superadmin-soft-deletes-a-preset"></a>

#### [the-superadmin-soft-deletes-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

superadmin 이 프리셋을 soft delete 하면, 삭제로 표시된 프리셋 전체가 응답으로 옵니다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.delete: user-1이 preset-1을 soft delete 합니다

Then

- 삭제로 표시된 프리셋 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = True
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-preset"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 프리셋을 soft delete 하려 하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.delete: user-1이 preset-1을 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-reads-a-preset-by-id"></a>

#### [a-user-granted-read-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

global 에서 조회 권한을 받은 사용자가 id 로 조회하면, 미리 저장한 프리셋 전체가 반환됩니다

Given

- 이미 있는 프리셋 하나와, global 에서 READ 권한을 받은 user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여를 켬, 소유자 부여를 켬, 역할 이름 템플릿을 가짐입니다
  - 도메인 home-1
  - global 에서 역할 프리셋 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 preset-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 preset-reader-1: role_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 preset-reader-1 보유

When

- RolePresetAdapter.get: user-1이 preset-1을 id 로 조회합니다

Then

- 미리 저장한 프리셋 전체가 반환됩니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - role_name_template = 'team-member'
  - auto_assign = True
  - auto_assign_to_owner = True
  - deleted = False
  - deleted_at = None
  - created_at: 미리 저장한 프리셋의 시각와 같다
  - updated_at: 미리 저장한 프리셋의 시각와 같다

<a id="reading-a-user-granted-nothing-may-not-read-a-preset"></a>

#### [a-user-granted-nothing-may-not-read-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

아무 권한도 받지 않은 사용자가 id 로 조회하려 하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.get: user-1이 preset-1을 id 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-presets"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_delete: user-1이 프리셋 2개를 한 번에 soft delete 합니다

Then

- 처리된 것 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

프리셋 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제로 표시된 채 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_delete: user-1이 프리셋 2개 와 없는 id 하나를 한 번에 soft delete 합니다

Then

- 대상 프리셋이 모두 삭제로 표시된 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = True
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = True
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_purge

<a id="partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_purge: user-1이 프리셋 2개를 한 번에 purge 합니다

Then

- 처리된 것 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 하기 전의 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_purge: user-1이 프리셋 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 대상 프리셋이 모두 삭제로 표시되지 않은 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

soft delete 된 프리셋 여럿을 한 번에 restore 하면, 모두 삭제로 표시되지 않은 채 옵니다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_restore: user-1이 프리셋 2개를 한 번에 soft delete 한 뒤 한 번에 restore 합니다

Then

- 대상 프리셋이 모두 삭제로 표시되지 않은 채 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### purge

<a id="deleting-the-superadmin-purges-a-preset"></a>

#### [the-superadmin-purges-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

superadmin 이 프리셋을 purge 하면, purge 하기 전의 프리셋 전체가 응답으로 옵니다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.purge: user-1이 preset-1을 purge 합니다

Then

- 삭제로 표시되지 않은 프리셋 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-purge-a-preset"></a>

#### [a-user-granted-nothing-may-not-purge-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.purge: user-1이 preset-1을 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### restore

<a id="deleting-restoring-a-soft-deleted-preset-brings-it-back"></a>

#### [restoring-a-soft-deleted-preset-brings-it-back](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

soft delete 된 프리셋을 restore 하면, 삭제로 표시되지 않은 프리셋 전체가 응답으로 옵니다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.restore: user-1이 preset-1을 soft delete 한 뒤 restore 합니다

Then

- 삭제로 표시되지 않은 프리셋 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-restore-a-preset"></a>

#### [a-user-granted-nothing-may-not-restore-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 프리셋을 restore 하려 하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.restore: user-1이 preset-1을 restore 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search

<a id="searching-the-superadmin-finds-one-page-of-matching-presets"></a>

#### [the-superadmin-finds-one-page-of-matching-presets](/tests/scenario/bai_scenario/manager/role_preset/test_searching.py): pass

superadmin 이 프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 검색하면, 맞는 프리셋 가운데 정렬상 첫 하나만 오고 나머지는 오지 않습니다. 이 호출은 global 역할이 막습니다

Given

- 프로젝트 스코프 프리셋 둘, 도메인 스코프 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-3: domain 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.search: user-1이 프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 조회합니다

Then

- 필터에 맞는 프리셋 가운데 정렬상 첫 하나만 한 페이지로 오고, 나머지 맞는 프리셋과 필터에 걸리는 프리셋은 오지 않습니다
  - items count = 1
  - items[0].id: 미리 저장한 프리셋의 id 와 같다
  - items[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - items[0].name = 'preset-1'
  - items[0].scope_type = 'project'
  - items[0].role_name_template = None
  - items[0].auto_assign = False
  - items[0].auto_assign_to_owner = False
  - items[0].deleted = False
  - items[0].deleted_at = None
  - items[0].created_at: 미리 저장한 프리셋의 시각와 같다
  - items[0].updated_at: 미리 저장한 프리셋의 시각와 같다
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-presets"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-presets](/tests/scenario/bai_scenario/manager/role_preset/test_searching.py): pass

global 역할이 없는 사용자가 프리셋을 검색하려 하면, 권한 부족으로 거부됩니다

Given

- 프로젝트 스코프 프리셋 둘, 도메인 스코프 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-3: domain 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.search: user-1이 프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### search_permission_presets

<a id="permission_reading-a-user-granted-read-finds-one-page-of-matching-entries"></a>

#### [a-user-granted-read-finds-one-page-of-matching-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

global 에서 조회 권한을 받은 사용자가 권한 항목을 조회 비트 필터, 엔티티 타입 정렬, 한 페이지 크기로 검색하면, 맞는 항목 가운데 정렬상 첫 하나만 오고 나머지 맞는 항목, 필터에 걸리는 항목, 다른 프리셋의 항목은 오지 않습니다

Given

- 권한 항목 여럿을 가진 프리셋 하나, 다른 프리셋 하나와, global 에서 READ 권한을 받은 user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: project 전체에 READ 허용
  - 도메인 home-1
  - global 에서 역할 프리셋 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 preset-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 preset-reader-1: role_preset 전체에 READ 허용
    - 일반 사용자 user-1: 역할 preset-reader-1 보유

When

- RolePresetAdapter.search_permission_presets: user-1이 preset-1의 권한 항목을 조회 비트 필터, 엔티티 타입 정렬, 한 페이지 크기로 검색합니다

Then

- 필터에 맞는 항목 가운데 정렬상 첫 하나만 한 페이지로 오고, 나머지 맞는 항목, 필터에 걸리는 항목, 다른 프리셋의 항목은 오지 않습니다
  - items count = 1
  - items[0].id: 미리 저장한 항목의 id 와 같다
  - items[0].field_id: 미리 저장한 항목의 id 와 같다
  - items[0].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: 미리 저장한 항목의 시각와 같다
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="permission_reading-a-user-granted-nothing-may-not-search-permission-entries"></a>

#### [a-user-granted-nothing-may-not-search-permission-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

아무 권한도 받지 않은 사용자가 프리셋의 권한 항목을 검색하려 하면, 요청 전체가 권한 부족으로 거부됩니다

Given

- 권한 항목 여럿을 가진 프리셋 하나, 다른 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: project 전체에 READ 허용
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.search_permission_presets: user-1이 preset-1의 권한 항목을 조회 비트 필터, 엔티티 타입 정렬, 한 페이지 크기로 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### atomic_bulk_add_permissions

<a id="permission_editing-the-superadmin-adds-entries-to-a-preset"></a>

#### [the-superadmin-adds-entries-to-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

superadmin 이 항목 없는 프리셋에 권한 항목 둘을 추가하면, 추가한 두 항목이 그 프리셋 아래에 옵니다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.atomic_bulk_add_permissions: user-1이 preset-1에 권한 항목 2개를 추가합니다

Then

- 추가한 두 항목이 프리셋 아래에 옵니다
  - items count = 2
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: 이 실행이 쓴 시각

<a id="permission_editing-a-user-granted-nothing-may-not-add-entries"></a>

#### [a-user-granted-nothing-may-not-add-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

아무 권한도 받지 않은 사용자가 프리셋에 권한 항목을 추가하려 하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.atomic_bulk_add_permissions: user-1이 preset-1에 권한 항목 2개를 추가합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create

<a id="creating-a-project-preset-is-made-with-owner-assign"></a>

#### [a-project-preset-is-made-with-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_creating.py): pass

프로젝트 스코프 프리셋을 소유자 부여를 켜고 만들면, 켜진 프리셋이 응답으로 옵니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.create: user-1 이 소유자 부여를 켠 프로젝트 스코프 프리셋을 만듭니다

Then

- 소유자 부여가 켜진 프리셋이 응답으로 옵니다
  - name = 'made-preset'
  - auto_assign_to_owner = True

### partial_bulk_remove_permissions

<a id="permission_editing-a-user-granted-nothing-removes-none-of-the-entries"></a>

#### [a-user-granted-nothing-removes-none-of-the-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

아무 권한도 받지 않은 사용자가 권한 항목 여럿을 한 번에 제거하려 하면, 제거된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 권한 항목 둘을 가진 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_remove_permissions: user-1이 preset-1의 권한 항목 2개를 한 번에 제거합니다

Then

- 처리된 것 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="permission_editing-removing-entries-answers-for-the-missing-one"></a>

#### [removing-entries-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

superadmin 이 권한 항목 둘과 없는 id 하나를 한 번에 제거하면, 둘은 처리된 목록에 오고 없는 id 는 실패 목록에 옵니다

Given

- 권한 항목 둘을 가진 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_remove_permissions: user-1이 preset-1의 권한 항목 2개 와 없는 id 하나를 한 번에 제거합니다

Then

- 제거한 두 항목이 처리된 목록에 오고, 없는 id 는 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 항목의 id 와 같다
  - successes[0].field_id: 미리 저장한 항목의 id 와 같다
  - successes[0].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].entity_type = 'domain'
  - successes[0].permission = <PermissionBitDTO.READ: 'read'>
  - successes[0].created_at: 미리 저장한 항목의 시각와 같다
  - successes[1].id: 미리 저장한 항목의 id 와 같다
  - successes[1].field_id: 미리 저장한 항목의 id 와 같다
  - successes[1].role_preset_id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].entity_type = 'project'
  - successes[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - successes[1].created_at: 미리 저장한 항목의 시각와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_update: user-1이 프리셋 2개의 자동 부여를 한 번에 켭니다

Then

- 처리된 것 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-only-the-project-preset-takes-owner-assign"></a>

#### [only-the-project-preset-takes-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py): pass

프로젝트 스코프와 도메인 스코프 프리셋의 소유자 부여를 한 번에 켜면, 프로젝트 스코프 프리셋만 수정되고 도메인 스코프 프리셋은 실패 목록에 옵니다

Given

- 프로젝트 스코프 프리셋과 도메인 스코프 프리셋 하나씩과, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: domain 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_update: user-1 이 프리셋 2개의 소유자 부여를 한 번에 켭니다

Then

- 프로젝트 스코프 프리셋만 수정되어 오고, 도메인 스코프 프리셋은 실패 목록에 옵니다
  - successes count = 1
  - failed count = 1
  - successes[0].auto_assign_to_owner = True
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - failed[0].id: 두 번째 프리셋의 id 와 같다

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py): pass

superadmin 이 프리셋 여럿의 자동 부여를 한 번에 켜면, 모두 새 값으로 오고 실패한 것은 없습니다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.partial_bulk_update: user-1이 프리셋 2개의 자동 부여를 한 번에 켭니다

Then

- 대상 프리셋이 모두 새 값으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = True
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].entity_id: 미리 저장한 프리셋의 id 와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = True
  - successes[1].deleted = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### update

<a id="editing-a-project-preset-takes-owner-assign"></a>

#### [a-project-preset-takes-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

프로젝트 스코프 프리셋의 소유자 부여를 켜면, 켜진 프리셋 전체가 응답으로 옵니다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.update: user-1 이 preset-1의 소유자 부여를 켭니다

Then

- 소유자 부여가 켜진 프리셋 전체가 응답으로 옵니다
  - auto_assign_to_owner = True
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-the-superadmin-renames-a-preset"></a>

#### [the-superadmin-renames-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

superadmin 이 프리셋 이름을 변경하면, 새 이름을 담은 프리셋 전체가 응답으로 옵니다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.update: user-1이 preset-1의 이름을 renamed-preset(으)로 변경합니다

Then

- 새 이름을 담은 프리셋 전체가 응답으로 옵니다
  - id: 미리 저장한 프리셋의 id 와 같다
  - entity_id: 미리 저장한 프리셋의 id 와 같다
  - name = 'renamed-preset'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-domain-preset-refuses-owner-assign"></a>

#### [a-domain-preset-refuses-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

프로젝트 외 스코프 프리셋의 소유자 부여를 켜려 하면, 소유자가 없어 거부됩니다

Given

- 이미 있는 domain 스코프 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: domain 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.update: user-1 이 preset-1의 소유자 부여를 켭니다

Then

- 거부됩니다
  - 거부: RolePresetOwnerAssignNotAllowed

<a id="editing-a-user-granted-nothing-may-not-rename-a-preset"></a>

#### [a-user-granted-nothing-may-not-rename-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

아무 권한도 받지 않은 사용자가 프리셋 이름을 변경하려 하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 비활성입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RolePresetAdapter.update: user-1이 preset-1의 이름을 renamed-preset(으)로 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

