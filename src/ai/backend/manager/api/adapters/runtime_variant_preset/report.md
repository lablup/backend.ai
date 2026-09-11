## runtime_variant_preset

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/runtime_variant_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/runtime_variant_preset/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-bool-default-value-that-fits-its-type-is-accepted](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

값 종류를 bool로 두고 그에 맞는 기본값을 주면 만들어진다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.BOOL: 'bool'>, default_value='true', key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-flag-default-value-that-fits-its-type-is-accepted](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

값 종류를 flag로 두고 그에 맞는 기본값을 주면 만들어진다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ARGS: 'args'>, value_type=<PresetValueType.FLAG: 'flag'>, default_value='true', key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-float-default-value-that-fits-its-type-is-accepted](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

값 종류를 float로 두고 그에 맞는 기본값을 주면 만들어진다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.FLOAT: 'float'>, default_value='0.5', key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-int-default-value-that-fits-its-type-is-accepted](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

값 종류를 int로 두고 그에 맞는 기본값을 주면 만들어진다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.INT: 'int'>, default_value='4', key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-preset-name-taken-in-the-same-variant-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

같은 변형에 같은 이름의 preset이 있을 때 다시 만들면, 이름이 겹친다는 이유로 거부된다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 preset-1 preset을 하나 더 만듦

Then

- 거부된다
  - 거부: RuntimeVariantPresetConflict

#### [a-second-preset-in-the-same-variant-is-ranked-a-hundred-higher](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

preset이 하나 있는 변형에 슈퍼관리자가 하나 더 만들면 순위가 앞의 것보다 백 크다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 하나 더 만듦

Then

- 순위가 앞의 것보다 간격만큼 큰 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 200
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-str-default-value-that-fits-its-type-is-accepted](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

값 종류를 str로 두고 그에 맞는 기본값을 주면 만들어진다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value='abc', key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-ui-option-given-on-create-carries-its-type-into-the-node](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

슬라이더 옵션을 붙여 만들면, UI 종류가 옵션에서 읽혀 노드에 함께 실린다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = 'slider'
  - display_name = None
  - ui_option = UIOption(ui_type=<UIType.SLIDER: 'slider'>, slider=SliderOption(min=1.0, max=8.0, step=1.0), number=None, choices=None, text=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 preset을 만들면 역할로 거부된다

Given

- 런타임 변형 하나와, 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [target-value-type-default-and-key-come-back-as-one-spec](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

대상·값 종류·기본값·키를 따로 주고 만들면, 답에서는 넷이 한 명세로 묶여 온다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ARGS: 'args'>, value_type=<PresetValueType.INT: 'int'>, default_value='4', key='--workers')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-first-preset-of-a-variant-is-ranked-a-hundred](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

preset이 없는 변형에 슈퍼관리자가 필수 항목만 주고 만들면, 순위는 백, 필수 여부는 거짓, 나머지 선택 항목은 빈 노드가 온다

Given

- 런타임 변형 하나와, 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-same-preset-name-is-free-in-another-variant](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

유니크 제약이 변형과 이름의 짝에 걸려 있으므로, 다른 변형에는 같은 이름의 preset을 만들 수 있다

Given

- 변형 둘, 한쪽에만 있는 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 taken-1
  - 런타임 변형 free-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 free-1에 preset-1 preset을 만듦

Then

- 다른 변형 아래 만든 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'preset-1'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-does-not-let-a-user-create-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 preset을 만들지 못한다. 이 문은 권한 그래프가 아니라 역할이라 스위치와 무관하다

Given

- 런타임 변형 하나와, 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.create — user-1이 variant-1에 max-tokens preset을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-preset-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 아무것도 고침

Then

- 심은 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'preset-1'
  - description = '심어둔 preset'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 preset을 고치면 권한 부족으로 거부된다. preset은 어느 스코프에도 없어 그 권한을 받을 길이 없다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 name 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [changing-only-the-default-to-one-that-does-not-fit-the-stored-type-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

값 종류가 정수인 preset의 기본값만 숫자 아닌 문자열로 고치면 입력이 틀렸다는 이유로 거부된다. 서비스가 저장된 값 종류에 대고 새 기본값을 본다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 int, 기본값 4
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 default_value 고침

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [changing-only-the-value-type-to-flag-on-an-env-preset-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

대상이 env인 preset의 값 종류만 flag로 고치면 입력이 틀렸다는 이유로 거부된다. 요청은 대상을 생략했으므로 요청 타입은 통과시키고, 서비스가 저장된 대상과 합쳐 보고 막는다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 value_type 고침

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [clearing-a-preset-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

설명이 있는 preset의 설명을 비우는 수정을 하면, 설명이 없어진다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 description 고침

Then

- 심은 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'preset-1'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [editing-a-preset-rank-sets-the-new-rank](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

슈퍼관리자가 preset의 순위를 바꾸면 순위가 새 값인 노드가 온다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 rank 고침

Then

- 심은 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'preset-1'
  - description = '심어둔 preset'
  - rank = 7
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [renaming-a-preset-leaves-the-rest-alone](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

슈퍼관리자가 preset의 이름만 바꾸면, 이름은 새 값이 되고 나머지는 그대로 남는다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 name 고침

Then

- 심은 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'renamed'
  - description = '심어둔 preset'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-superadmin-editing-a-preset-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

슈퍼관리자가 아무 preset도 갖지 않은 id를 고치면 대상이 없다는 것으로 거부된다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 없는 id의 name 고침

Then

- 거부된다
  - 거부: RuntimeVariantPresetNotFound

#### [turning-enforcement-off-lets-a-user-edit-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 preset을 고친다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 name 고침

Then

- 심은 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'renamed'
  - description = '심어둔 preset'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading

#### [a-user-granted-nothing-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 id로 조회하면, 그 preset 전체가 온다. 이 읽기는 인증만 본다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.get — user-1이 preset-1로 조회

Then

- 심은 preset 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 심은 변형와 같다
  - name = 'preset-1'
  - description = '심어둔 preset'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-empty-preset-id-list-answers-empty-without-a-call](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py) — pass

빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - items = []

#### [presets-read-by-many-ids-come-back-in-the-order-asked](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py) — pass

있는 id 둘과 없는 id 하나를 한 번에 읽으면, 준 순서대로 오고 없는 id 자리는 비어서 온다

Given

- 한 변형의 preset 2개와, 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 런타임 변형 preset preset-2: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.batch_load_by_ids — user-1이 심은 2개와 없는 id 하나를 한 번에 조회

Then

- 준 순서대로, 없는 id 자리는 비어서 온다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].runtime_variant_id: 심은 변형와 같다
  - items[0].name = 'preset-1'
  - items[0].description = '심어둔 preset'
  - items[0].rank = 100
  - items[0].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - items[0].required = False
  - items[0].added_version = None
  - items[0].deprecated_version = None
  - items[0].category = None
  - items[0].ui_type = None
  - items[0].display_name = None
  - items[0].ui_option = None
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].runtime_variant_id: 심은 변형와 같다
  - items[1].name = 'preset-2'
  - items[1].description = '심어둔 preset'
  - items[1].rank = 200
  - items[1].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - items[1].required = False
  - items[1].added_version = None
  - items[1].deprecated_version = None
  - items[1].category = None
  - items[1].ui_type = None
  - items[1].display_name = None
  - items[1].ui_option = None
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[2] = None

#### [reading-a-preset-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py) — pass

아무 preset도 갖지 않은 id로 조회하면 대상이 없다는 것으로 거부된다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.get — user-1이 없는 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### retiring

#### [a-user-granted-nothing-may-not-delete-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 preset을 지우면 권한 부족으로 거부된다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.delete — user-1이 preset-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [deleting-a-preset-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

슈퍼관리자가 아무 preset도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.delete — user-1이 없는 id를 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-deletes-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

슈퍼관리자가 preset을 지우면 지운 preset의 id를 실은 답이 온다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 슈퍼관리자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.delete — user-1이 preset-1를 지움

Then

- 지운 preset의 id가 온다
  - id: 심은 preset와 같다

#### [turning-enforcement-off-lets-a-user-delete-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 preset을 지운다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 변형 하나와 그 변형의 preset 하나, 그리고 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.delete — user-1이 preset-1를 지움

Then

- 지운 preset의 id가 온다
  - id: 심은 preset와 같다

### searching

#### [a-user-granted-nothing-counts-every-preset-laid](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

preset 둘이 있을 때 아무 권한도 받지 않은 사용자가 필터 없이 조회하면 둘을 모두 센다

Given

- 한 변형의 preset 2개와, 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 런타임 변형 preset preset-2: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.search — user-1이 필터 없이 전체 조회

Then

- 답에 나와야 하는 preset만 남는다
  - items = ['preset-1', 'preset-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-variant-filter-narrows-the-answer-to-that-variants-presets](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

두 변형에 preset이 나뉘어 있을 때 한 변형으로 걸러 조회하면, 그 변형의 것만 남는다

Given

- 두 변형에 나뉜 preset 셋과, 일반 사용자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 런타임 변형 preset mine-1: env 대상, 값 종류 str
  - 런타임 변형 preset mine-2: env 대상, 값 종류 str
  - 런타임 변형 preset elsewhere-1: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.search — user-1이 wanted-1으로 걸러 조회

Then

- 답에 나와야 하는 preset만 남는다
  - items = ['mine-1', 'mine-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-version-filter-keeps-only-the-presets-valid-at-that-version](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

추가 버전과 폐기 버전이 다른 preset들을 한 버전으로 걸러 조회하면, 추가 버전 이상이고 폐기 버전 미만인 것만 남는다. 비어 있는 쪽은 열려 있다

Given

- 추가 버전과 폐기 버전이 다른 preset 다섯과, 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset open-1: env 대상, 값 종류 str, 버전 1.0.0부터 끝까지
  - 런타임 변형 preset unbounded-1: env 대상, 값 종류 str
  - 런타임 변형 preset closed-1: env 대상, 값 종류 str, 버전 1.0.0부터 2.0.0까지
  - 런타임 변형 preset retired-1: env 대상, 값 종류 str, 버전 처음부터 2.0.0까지
  - 런타임 변형 preset upcoming-1: env 대상, 값 종류 str, 버전 3.0.0부터 끝까지
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.search — user-1이 버전 2.5.0에 유효한 것만 조회

Then

- 답에 나와야 하는 preset만 남는다
  - items = ['open-1', 'unbounded-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-presets-and-a-next-page](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

preset 열하나가 있을 때 크기 없이 조회하면 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 한 변형의 preset 11개와, 일반 사용자 한 명
  - 런타임 변형 variant-1
  - 런타임 변형 preset preset-1: env 대상, 값 종류 str
  - 런타임 변형 preset preset-2: env 대상, 값 종류 str
  - 런타임 변형 preset preset-3: env 대상, 값 종류 str
  - 런타임 변형 preset preset-4: env 대상, 값 종류 str
  - 런타임 변형 preset preset-5: env 대상, 값 종류 str
  - 런타임 변형 preset preset-6: env 대상, 값 종류 str
  - 런타임 변형 preset preset-7: env 대상, 값 종류 str
  - 런타임 변형 preset preset-8: env 대상, 값 종류 str
  - 런타임 변형 preset preset-9: env 대상, 값 종류 str
  - 런타임 변형 preset preset-10: env 대상, 값 종류 str
  - 런타임 변형 preset preset-11: env 대상, 값 종류 str
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantPresetAdapter.search — user-1이 필터 없이 전체 조회

Then

- 기본 크기의 첫 쪽이 온다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

