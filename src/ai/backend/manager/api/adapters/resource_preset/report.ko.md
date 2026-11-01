## resource_preset

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_preset/adapter.py)

시나리오: 미완 6 / 9

- ops 로 구성 (5)
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_purge — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_update — 대표 성공 ✓ · 대표 실패 ✓
  - search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- 직접 구현 (4)
  - apply_resource_group — 성공 없음 · 실패 없음 (membership) — SCENARIO-GAP
  - create — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - purge — 성공 있음 1 · 실패 있음 2 (single_entity)
  - update — 성공 있음 2 · 실패 있음 2 (membership, single_entity)

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, 지워진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets) | 성공 |
| [프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지워진 노드로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | 성공 |
| [슈퍼관리자가 프리셋 여럿의 공유 메모리를 한 번에 바꾸면, 모두 새 공유 메모리로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | 성공 |
| [프리셋 여럿을 고치며 하나의 자원을 필수 슬롯 없이 바꾸면, 요청 전체가 입력 오류로 거부된다](#partial_bulk_editing-editing-several-with-slots-missing-intrinsic-ones-is-refused) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 프리셋을 purge 하면 지운 프리셋의 id 가 온다](#purging-the-superadmin-purges-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면 권한 부족으로 거부된다](#purging-a-user-granted-nothing-may-not-purge-a-preset) | 거부 |
| [슈퍼관리자가 없는 id 의 프리셋을 purge 하려 하면 대상이 없다는 것으로 거부된다](#purging-purging-an-id-nothing-answers-to-is-not-found) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [public 에서 수정 권한을 받은 사용자가 프리셋의 이름을 바꾸면, 새 이름의 프리셋이 온다](#editing-a-user-granted-update-in-public-renames-a-preset) | 성공 |
| [슈퍼관리자가 프리셋의 이름만 바꾸면, 이름은 새 값이 되고 나머지는 그대로 남는다](#editing-the-superadmin-renames-a-preset) | 성공 |
| [아무 권한도 받지 않은 사용자가 프리셋을 수정하려 하면 권한 부족으로 거부된다](#editing-a-user-granted-nothing-may-not-edit-a-preset) | 거부 |
| [슈퍼관리자가 없는 id 의 프리셋을 수정하려 하면 대상이 없다는 것으로 거부된다](#editing-editing-an-id-nothing-answers-to-is-not-found) | 거부 |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, 지워진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와 일반 사용자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 리소스 프리셋 preset-2: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.partial_bulk_purge — user-1이 프리셋 2개를 한 번에 purge 함

Then

- 처리된 프리셋 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 프리셋의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 프리셋의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_purging.py) — pass

프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지워진 노드로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 리소스 프리셋 preset-2: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.partial_bulk_purge — user-1이 프리셋 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 대상 프리셋이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[0].name = 'preset-1'
  - successes[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[0].shared_memory = None
  - successes[0].resource_group_name = None
  - successes[1].id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[1].name = 'preset-2'
  - successes[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[1].shared_memory = None
  - successes[1].resource_group_name = None
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 프리셋 2개와 일반 사용자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 리소스 프리셋 preset-2: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.partial_bulk_update — user-1이 프리셋 2개의 공유 메모리를 한 번에 바꿈

Then

- 처리된 프리셋 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 프리셋의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 프리셋의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_editing.py) — pass

슈퍼관리자가 프리셋 여럿의 공유 메모리를 한 번에 바꾸면, 모두 새 공유 메모리로 오고 실패한 것은 없다

Given

- 프리셋 2개와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 리소스 프리셋 preset-2: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.partial_bulk_update — user-1이 프리셋 2개의 공유 메모리를 한 번에 바꿈

Then

- 대상 프리셋이 모두 처리된 목록에 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만든 프리셋의 id와 같다
  - successes[0].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[0].name = 'preset-1'
  - successes[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[0].shared_memory = BinarySizeInfo(expr='1073741824', display='1g')
  - successes[0].resource_group_name = None
  - successes[1].id: 미리 만든 프리셋의 id와 같다
  - successes[1].entity_id: 미리 만든 프리셋의 id와 같다
  - successes[1].name = 'preset-2'
  - successes[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[1].shared_memory = BinarySizeInfo(expr='1073741824', display='1g')
  - successes[1].resource_group_name = None
  - failed = []

<a id="partial_bulk_editing-editing-several-with-slots-missing-intrinsic-ones-is-refused"></a>

#### [editing-several-with-slots-missing-intrinsic-ones-is-refused](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_editing.py) — pass

프리셋 여럿을 고치며 하나의 자원을 필수 슬롯 없이 바꾸면, 요청 전체가 입력 오류로 거부된다

Given

- 프리셋 2개와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 리소스 프리셋 preset-2: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.partial_bulk_update — user-1이 프리셋 2개를 한 번에 고치며 첫째의 자원을 필수 슬롯 없이 바꿈

Then

- 거부된다
  - 거부: InvalidAPIParameters

### purge

<a id="purging-the-superadmin-purges-a-preset"></a>

#### [the-superadmin-purges-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_purging.py) — pass

슈퍼관리자가 프리셋을 purge 하면 지운 프리셋의 id 가 온다

Given

- 프리셋 하나와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.purge — user-1이 preset-1을 purge 함

Then

- 지운 프리셋의 id 가 온다
  - id: 미리 만든 프리셋의 id와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-preset"></a>

#### [a-user-granted-nothing-may-not-purge-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_purging.py) — pass

아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면 권한 부족으로 거부된다

Given

- 프리셋 하나와 일반 사용자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.purge — user-1이 preset-1을 purge 함

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="purging-purging-an-id-nothing-answers-to-is-not-found"></a>

#### [purging-an-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_preset/test_purging.py) — pass

슈퍼관리자가 없는 id 의 프리셋을 purge 하려 하면 대상이 없다는 것으로 거부된다

Given

- 프리셋 하나와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.purge — user-1이 없는 id을 purge 함

Then

- 거부된다
  - 거부: ResourcePresetNotFound

### update

<a id="editing-a-user-granted-update-in-public-renames-a-preset"></a>

#### [a-user-granted-update-in-public-renames-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py) — pass

public 에서 수정 권한을 받은 사용자가 프리셋의 이름을 바꾸면, 새 이름의 프리셋이 온다

Given

- 프리셋 하나와 public 에서 UPDATE 권한을 받은 일반 사용자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - public 에서 리소스 프리셋 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 preset-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 preset-writer-1: resource_preset 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 preset-writer-1 보유

When

- ResourcePresetAdapter.update — user-1이 preset-1의 이름을 바꿈

Then

- 미리 만든 프리셋 전체가 온다
  - id: 미리 만든 프리셋의 id와 같다
  - entity_id: 미리 만든 프리셋의 id와 같다
  - name = 'renamed-preset'
  - resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - shared_memory = None
  - resource_group_name = None

<a id="editing-the-superadmin-renames-a-preset"></a>

#### [the-superadmin-renames-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py) — pass

슈퍼관리자가 프리셋의 이름만 바꾸면, 이름은 새 값이 되고 나머지는 그대로 남는다

Given

- 프리셋 하나와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.update — user-1이 preset-1의 이름을 바꿈

Then

- 미리 만든 프리셋 전체가 온다
  - id: 미리 만든 프리셋의 id와 같다
  - entity_id: 미리 만든 프리셋의 id와 같다
  - name = 'renamed-preset'
  - resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - shared_memory = None
  - resource_group_name = None

<a id="editing-a-user-granted-nothing-may-not-edit-a-preset"></a>

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 프리셋을 수정하려 하면 권한 부족으로 거부된다

Given

- 프리셋 하나와 일반 사용자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.update — user-1이 preset-1의 이름을 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing-editing-an-id-nothing-answers-to-is-not-found"></a>

#### [editing-an-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py) — pass

슈퍼관리자가 없는 id 의 프리셋을 수정하려 하면 대상이 없다는 것으로 거부된다

Given

- 프리셋 하나와 슈퍼관리자 한 명
  - 리소스 프리셋 preset-1: 리소스 그룹에 묶이지 않아 public 에 속한다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePresetAdapter.update — user-1이 없는 id의 이름을 바꿈

Then

- 거부된다
  - 거부: ResourcePresetNotFound

