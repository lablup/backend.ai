## runtime_variant_preset

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/runtime_variant_preset/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/runtime_variant_preset/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-bool-default-value-that-fits-its-type-is-accepted](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

값 종류를 bool(으)로 두고 그에 맞는 기본값을 지정하면 생성된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

값 종류를 flag(으)로 두고 그에 맞는 기본값을 지정하면 생성된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

값 종류를 float(으)로 두고 그에 맞는 기본값을 지정하면 생성된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

값 종류를 int(으)로 두고 그에 맞는 기본값을 지정하면 생성된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

같은 변형에 같은 이름의 preset이 있을 때 다시 생성하면, 이름 중복으로 거부된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset preset-1 하나 더 생성

Then

- 거부된다
  - 거부: RuntimeVariantPresetConflict

#### [a-second-preset-in-the-same-variant-is-ranked-a-hundred-higher](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

preset이 하나 있는 변형에 슈퍼관리자가 하나 더 생성하면 순위가 앞의 것보다 100 크다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 하나 더 생성

Then

- 순위가 앞의 것보다 간격만큼 큰 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

값 종류를 str(으)로 두고 그에 맞는 기본값을 지정하면 생성된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

슬라이더 옵션을 붙여 생성하면, UI 종류가 옵션에서 읽혀 노드에 함께 담긴다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

슈퍼관리자가 아닌 사용자가 preset을 생성하면 역할 부족으로 거부된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [target-value-type-default-and-key-come-back-as-one-spec](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py) — pass

대상·값 종류·기본값·키를 따로 지정해 생성하면, 응답에서는 넷이 한 명세로 묶여 반환된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

preset이 없는 변형에 슈퍼관리자가 필수 항목만 지정해 생성하면, 순위는 100, 필수 여부는 거짓, 나머지 선택 항목은 비어 있는 노드가 반환된다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

유니크 제약이 변형과 이름의 조합에 걸려 있으므로, 다른 변형에는 같은 이름의 preset을 생성할 수 있다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 free-1에 preset preset-1 생성

Then

- 다른 변형 아래 생성한 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

권한 검사를 꺼도 슈퍼관리자가 아니면 preset을 생성하지 못한다. 생성은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다

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

- RuntimeVariantPresetAdapter.create — user-1이 변형 variant-1에 preset max-tokens 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-preset-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환된다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 아무것도 수정

Then

- 미리 만들어 둔 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 preset'
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

아무 권한도 없는 사용자가 preset을 수정하면 권한 부족으로 거부된다. preset은 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 name 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [changing-only-the-default-to-one-that-does-not-fit-the-stored-type-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

값 종류가 정수인 preset의 기본값만 숫자 아닌 문자열로 수정하면 잘못된 입력으로 거부된다. 서비스가 저장된 값 종류를 기준으로 새 기본값을 검사한다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 default_value 수정

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [changing-only-the-value-type-to-flag-on-an-env-preset-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

대상이 env인 preset의 값 종류만 flag로 수정하면 잘못된 입력으로 거부된다. 요청은 대상을 생략했으므로 요청 타입은 통과시키고, 서비스가 저장된 대상과 합쳐 검사한 뒤 막는다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 value_type 수정

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [clearing-a-preset-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

설명이 있는 preset에 설명을 비우는 수정을 하면, 설명이 없어진다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 description 수정

Then

- 미리 만들어 둔 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
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

슈퍼관리자가 preset의 순위를 바꾸면 순위가 새 값인 노드가 반환된다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 rank 수정

Then

- 미리 만들어 둔 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 preset'
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

슈퍼관리자가 preset의 이름만 바꾸면, 이름은 새 값이 되고 나머지는 그대로 유지된다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 name 수정

Then

- 미리 만들어 둔 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
  - name = 'renamed'
  - description = '미리 만들어 둔 preset'
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

슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다

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

- RuntimeVariantPresetAdapter.update — user-1이 존재하지 않는 id의 name 수정

Then

- 거부된다
  - 거부: RuntimeVariantPresetNotFound

#### [turning-enforcement-off-lets-a-user-edit-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 preset을 수정할 수 있다. 수정은 역할이 아니라 권한 그래프로 보호되기 때문이다

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

- RuntimeVariantPresetAdapter.update — user-1이 preset-1의 name 수정

Then

- 미리 만들어 둔 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
  - name = 'renamed'
  - description = '미리 만들어 둔 preset'
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

아무 권한도 없는 사용자가 id로 조회하면, 그 preset 전체가 반환된다. 이 조회는 인증만 확인한다

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

- RuntimeVariantPresetAdapter.get — user-1이 preset-1(으)로 조회

Then

- 미리 만들어 둔 preset 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - runtime_variant_id: 미리 만들어 둔 변형와 같다
  - name = 'preset-1'
  - description = '미리 만들어 둔 preset'
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

빈 id 목록을 주면 빈 응답이 반환된다. 하위 계층을 호출하지 않는다

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

- 빈 응답이 반환된다
  - items = []

#### [presets-read-by-many-ids-come-back-in-the-order-asked](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py) — pass

있는 id 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 자리는 비어 있다

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

- RuntimeVariantPresetAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 2개와 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로, 없는 id 자리는 비어서 반환된다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].runtime_variant_id: 미리 만들어 둔 변형와 같다
  - items[0].name = 'preset-1'
  - items[0].description = '미리 만들어 둔 preset'
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
  - items[1].runtime_variant_id: 미리 만들어 둔 변형와 같다
  - items[1].name = 'preset-2'
  - items[1].description = '미리 만들어 둔 preset'
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

존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

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

- RuntimeVariantPresetAdapter.get — user-1이 존재하지 않는 id(으)로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### retiring

#### [a-user-granted-nothing-may-not-delete-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

아무 권한도 없는 사용자가 preset을 삭제하면 권한 부족으로 거부된다

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

- RuntimeVariantPresetAdapter.delete — user-1이 preset-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [deleting-a-preset-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다

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

- RuntimeVariantPresetAdapter.delete — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-deletes-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

슈퍼관리자가 preset을 삭제하면 삭제한 preset의 id를 담은 응답이 반환된다

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

- RuntimeVariantPresetAdapter.delete — user-1이 preset-1 삭제

Then

- 삭제한 preset의 id가 반환된다
  - id: 미리 만들어 둔 preset와 같다

#### [turning-enforcement-off-lets-a-user-delete-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 preset을 삭제할 수 있다. 삭제는 역할이 아니라 권한 그래프로 보호되기 때문이다

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

- RuntimeVariantPresetAdapter.delete — user-1이 preset-1 삭제

Then

- 삭제한 preset의 id가 반환된다
  - id: 미리 만들어 둔 preset와 같다

### searching

#### [a-user-granted-nothing-counts-every-preset-laid](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

preset 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다

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

- 응답에 나와야 하는 preset만 반환된다
  - items = ['preset-1', 'preset-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-variant-filter-narrows-the-answer-to-that-variants-presets](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

두 변형에 preset이 나뉘어 있을 때 한 변형을 필터로 조회하면, 그 변형의 preset만 반환된다

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

- RuntimeVariantPresetAdapter.search — user-1이 변형 wanted-1 필터로 조회

Then

- 응답에 나와야 하는 preset만 반환된다
  - items = ['mine-1', 'mine-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-version-filter-keeps-only-the-presets-valid-at-that-version](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

추가 버전과 폐기 버전이 다른 preset들을 한 버전 필터로 조회하면, 추가 버전 이상이고 폐기 버전 미만인 preset만 반환된다. 비어 있는 쪽은 제한이 없다

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

- RuntimeVariantPresetAdapter.search — user-1이 버전 2.5.0에 유효한 preset만 조회

Then

- 응답에 나와야 하는 preset만 반환된다
  - items = ['open-1', 'unbounded-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-presets-and-a-next-page](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py) — pass

preset 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다

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

- 기본 크기의 첫 페이지가 반환된다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

