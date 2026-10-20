## role_preset

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/role_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/role_preset/adapter.py)

시나리오: 미완 16 / 21

- ops 로 구성 (14)
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - batch_load_permissions_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - bulk_delete — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - bulk_purge — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - bulk_restore — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - delete — 대표 성공 ✓ · 대표 실패 ✓
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_delete — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_purge — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_restore — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - purge — 대표 성공 ✓ · 대표 실패 ✓
  - restore — 대표 성공 ✓ · 대표 실패 ✓
  - search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - search_permission_presets — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- 직접 구현 (7)
  - atomic_bulk_add_permissions — 성공 있음 1 · 실패 있음 1 (single_entity)
  - bulk_add_permissions — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - bulk_remove_permissions — 성공 없음 · 실패 없음 (partial_bulk_field) — SCENARIO-GAP
  - create — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - partial_bulk_remove_permissions — 성공 있음 2 · 실패 없음 (partial_bulk_field) — SCENARIO-GAP
  - partial_bulk_update — 성공 있음 2 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - update — 성공 있음 1 · 실패 있음 1 (single_entity)

**delete**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 프리셋을 soft delete 하면, 삭제 표시가 켜진 프리셋 전체가 온다](#deleting-the-superadmin-soft-deletes-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 soft delete 하려 하면, 권한 부족으로 거부된다](#deleting-a-user-granted-nothing-may-not-soft-delete-a-preset) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-presets) | 성공 |
| [프리셋 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 표시가 켜진 채 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-presets) | 성공 |
| [프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 하기 전의 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-purging-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 프리셋 여럿을 한 번에 restore 하면, 모두 삭제 표시가 꺼진 채 온다](#partial_bulk_deleting-restoring-several-brings-them-back) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 프리셋을 purge 하면, purge 하기 전의 프리셋 전체가 온다](#deleting-the-superadmin-purges-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면, 권한 부족으로 거부된다](#deleting-a-user-granted-nothing-may-not-purge-a-preset) | 거부 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 프리셋을 restore 하면, 삭제 표시가 꺼진 프리셋 전체가 온다](#deleting-restoring-a-soft-deleted-preset-brings-it-back) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 restore 하려 하면, 권한 부족으로 거부된다](#deleting-a-user-granted-nothing-may-not-restore-a-preset) | 거부 |

**atomic_bulk_add_permissions**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 항목 없는 프리셋에 권한 항목 둘을 넣으면, 넣은 두 항목이 그 프리셋 아래에 온다](#permission_editing-the-superadmin-adds-entries-to-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋에 권한 항목을 넣으려 하면, 권한 부족으로 거부된다](#permission_editing-a-user-granted-nothing-may-not-add-entries) | 거부 |

**partial_bulk_remove_permissions**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 권한 항목 여럿을 한 번에 빼려 하면, 뺀 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#permission_editing-a-user-granted-nothing-removes-none-of-the-entries) | 성공 |
| [슈퍼관리자가 권한 항목 둘과 없는 id 하나를 한 번에 빼면, 둘은 처리된 목록에 오고 없는 id 는 실패 목록에 온다](#permission_editing-removing-entries-answers-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | 성공 |
| [슈퍼관리자가 프리셋 여럿의 자동 부여를 한 번에 켜면, 모두 새 값으로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 프리셋 이름을 바꾸면, 새 이름을 실은 프리셋 전체가 온다](#editing-the-superadmin-renames-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋 이름을 바꾸려 하면, 권한 부족으로 거부된다](#editing-a-user-granted-nothing-may-not-rename-a-preset) | 거부 |

### delete

<a id="deleting-the-superadmin-soft-deletes-a-preset"></a>

#### [the-superadmin-soft-deletes-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py) — pass

슈퍼관리자가 프리셋을 soft delete 하면, 삭제 표시가 켜진 프리셋 전체가 온다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.delete — user-1이 preset-1을 soft delete 함

Then

- 삭제 표시가 켜진 프리셋 전체가 온다
  - id: 미리 만든 프리셋의 id와 같다
  - entity_id: 미리 만든 프리셋의 id와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = True
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-preset"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py) — pass

아무 권한도 받지 않은 사용자가 프리셋을 soft delete 하려 하면, 권한 부족으로 거부된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.delete — user-1이 preset-1을 soft delete 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-presets"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py) — pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_delete — user-1이 프리셋 2개를 한 번에 soft delete 함

Then

- 처리된 것 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py) — pass

프리셋 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 표시가 켜진 채 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_delete — user-1이 프리셋 2개 와 없는 id 하나를 한 번에 soft delete 함

Then

- 대상 프리셋이 모두 삭제 표시가 켜진 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = True
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = True
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_purge

<a id="partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py) — pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_purge — user-1이 프리셋 2개를 한 번에 purge 함

Then

- 처리된 것 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py) — pass

프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 하기 전의 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_purge — user-1이 프리셋 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 대상 프리셋이 모두 삭제 표시가 꺼진 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py) — pass

soft delete 된 프리셋 여럿을 한 번에 restore 하면, 모두 삭제 표시가 꺼진 채 온다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_restore — user-1이 프리셋 2개를 한 번에 soft delete 했다가 한 번에 restore 함

Then

- 대상 프리셋이 모두 삭제 표시가 꺼진 채 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### purge

<a id="deleting-the-superadmin-purges-a-preset"></a>

#### [the-superadmin-purges-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py) — pass

슈퍼관리자가 프리셋을 purge 하면, purge 하기 전의 프리셋 전체가 온다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.purge — user-1이 preset-1을 purge 함

Then

- 삭제 표시가 꺼진 프리셋 전체가 온다
  - id: 미리 만든 프리셋의 id와 같다
  - entity_id: 미리 만든 프리셋의 id와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-purge-a-preset"></a>

#### [a-user-granted-nothing-may-not-purge-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py) — pass

아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면, 권한 부족으로 거부된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.purge — user-1이 preset-1을 purge 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### restore

<a id="deleting-restoring-a-soft-deleted-preset-brings-it-back"></a>

#### [restoring-a-soft-deleted-preset-brings-it-back](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py) — pass

soft delete 된 프리셋을 restore 하면, 삭제 표시가 꺼진 프리셋 전체가 온다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.restore — user-1이 preset-1을 soft delete 했다가 restore 함

Then

- 삭제 표시가 꺼진 프리셋 전체가 온다
  - id: 미리 만든 프리셋의 id와 같다
  - entity_id: 미리 만든 프리셋의 id와 같다
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-restore-a-preset"></a>

#### [a-user-granted-nothing-may-not-restore-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py) — pass

아무 권한도 받지 않은 사용자가 프리셋을 restore 하려 하면, 권한 부족으로 거부된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.restore — user-1이 preset-1을 restore 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### atomic_bulk_add_permissions

<a id="permission_editing-the-superadmin-adds-entries-to-a-preset"></a>

#### [the-superadmin-adds-entries-to-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py) — pass

슈퍼관리자가 항목 없는 프리셋에 권한 항목 둘을 넣으면, 넣은 두 항목이 그 프리셋 아래에 온다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.atomic_bulk_add_permissions — user-1이 preset-1에 권한 항목 2개를 넣음

Then

- 넣은 두 항목이 프리셋 아래에 온다
  - items count = 2
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].field_id: 무시함 — 데이터베이스가 만든다
  - items[0].role_preset_id: 미리 만든 프리셋의 id와 같다
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].field_id: 무시함 — 데이터베이스가 만든다
  - items[1].role_preset_id: 미리 만든 프리셋의 id와 같다
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: 이 실행이 쓴 시각

<a id="permission_editing-a-user-granted-nothing-may-not-add-entries"></a>

#### [a-user-granted-nothing-may-not-add-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py) — pass

아무 권한도 받지 않은 사용자가 프리셋에 권한 항목을 넣으려 하면, 권한 부족으로 거부된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.atomic_bulk_add_permissions — user-1이 preset-1에 권한 항목 2개를 넣음

Then

- 거부된다
  - 거부: NotEnoughPermission

### partial_bulk_remove_permissions

<a id="permission_editing-a-user-granted-nothing-removes-none-of-the-entries"></a>

#### [a-user-granted-nothing-removes-none-of-the-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py) — pass

아무 권한도 받지 않은 사용자가 권한 항목 여럿을 한 번에 빼려 하면, 뺀 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 권한 항목 둘을 가진 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용 항목
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용 항목
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_remove_permissions — user-1이 preset-1의 권한 항목 2개를 한 번에 뺌

Then

- 처리된 것 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="permission_editing-removing-entries-answers-for-the-missing-one"></a>

#### [removing-entries-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py) — pass

슈퍼관리자가 권한 항목 둘과 없는 id 하나를 한 번에 빼면, 둘은 처리된 목록에 오고 없는 id 는 실패 목록에 온다

Given

- 권한 항목 둘을 가진 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-1: domain 전체에 READ 허용 항목
  - 역할 프리셋 preset-1: project 전체에 UPDATE 허용 항목
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_remove_permissions — user-1이 preset-1의 권한 항목 2개 와 없는 id 하나를 한 번에 뺌

Then

- 뺀 두 항목이 처리된 목록에 오고, 없는 id 는 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만든 항목의 id와 같다
  - successes[0].field_id: 미리 만든 항목의 id와 같다
  - successes[0].role_preset_id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_type = 'domain'
  - successes[0].permission = <PermissionBitDTO.READ: 'read'>
  - successes[0].created_at: 미리 만든 항목의 시각와 같다
  - successes[1].id: 미리 만든 항목의 id와 같다
  - successes[1].field_id: 미리 만든 항목의 id와 같다
  - successes[1].role_preset_id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_type = 'project'
  - successes[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - successes[1].created_at: 미리 만든 항목의 시각와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_update — user-1이 프리셋 2개의 자동 부여를 한 번에 켬

Then

- 처리된 것 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py) — pass

슈퍼관리자가 프리셋 여럿의 자동 부여를 한 번에 켜면, 모두 새 값으로 오고 실패한 것은 없다

Given

- 프리셋 2개와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 역할 프리셋 preset-2: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.partial_bulk_update — user-1이 프리셋 2개의 자동 부여를 한 번에 켬

Then

- 대상 프리셋이 모두 새 값으로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = True
  - successes[0].deleted = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = True
  - successes[1].deleted = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### update

<a id="editing-the-superadmin-renames-a-preset"></a>

#### [the-superadmin-renames-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py) — pass

슈퍼관리자가 프리셋 이름을 바꾸면, 새 이름을 실은 프리셋 전체가 온다

Given

- 이미 있는 프리셋 하나와, superadmin 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.update — user-1이 preset-1의 이름을 renamed-preset(으)로 바꿈

Then

- 새 이름을 실은 프리셋 전체가 온다
  - id: 미리 만든 프리셋의 id와 같다
  - entity_id: 미리 만든 프리셋의 id와 같다
  - name = 'renamed-preset'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-rename-a-preset"></a>

#### [a-user-granted-nothing-may-not-rename-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 프리셋 이름을 바꾸려 하면, 권한 부족으로 거부된다

Given

- 이미 있는 프리셋 하나와, user 한 명
  - 역할 프리셋 preset-1: 프로젝트 스코프용이고 자동 부여는 꺼져 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RolePresetAdapter.update — user-1이 preset-1의 이름을 renamed-preset(으)로 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

