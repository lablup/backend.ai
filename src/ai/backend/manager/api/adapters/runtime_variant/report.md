## runtime_variant

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/runtime_variant/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/runtime_variant/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-user-who-is-not-the-superadmin-may-not-create-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 변형을 만들면 역할로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.create — user-1이 vllm 변형을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-variant-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py) — pass

슈퍼관리자가 이름과 설명을 함께 주고 만들면, 준 값이 그대로 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.create — user-1이 vllm 변형을 만듦

Then

- 만든 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'vllm'
  - description = '새로 적은 설명'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-variant-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py) — pass

같은 이름의 변형이 이미 있을 때 그 이름으로 다시 만들면, 이름이 겹친다는 이유로 거부된다

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

- RuntimeVariantAdapter.create — user-1이 이미 있는 variant-1으로 다시 만듦

Then

- 거부된다
  - 거부: RuntimeVariantConflict

#### [the-superadmin-makes-a-variant-with-a-name-alone](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py) — pass

슈퍼관리자가 이름만 주고 변형을 만들면, 설명은 비고 폴더 설정 파일은 읽지 않으며 모델 정의는 코드가 못박은 기본값인 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.create — user-1이 vllm 변형을 만듦

Then

- 만든 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'vllm'
  - description = None
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-does-not-let-a-user-create-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 변형을 만들지 못한다. 이 문은 권한 그래프가 아니라 역할이라 스위치와 무관하다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.create — user-1이 vllm 변형을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 없는 id를 고치면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 돌고 없는 행에는 걸린 권한도 없다

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

- RuntimeVariantAdapter.update — user-1이 없는 id의 이름 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-edit-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 변형을 고치면 권한 부족으로 거부된다. 변형은 어느 스코프에도 없어 그 권한을 받을 길이 없다

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

- RuntimeVariantAdapter.update — user-1이 variant-1의 이름 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다

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

- RuntimeVariantAdapter.update — user-1이 variant-1의 아무것도 고침

Then

- 심은 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'variant-1'
  - description = '심어둔 런타임 변형'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [clearing-a-variant-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

설명이 있는 변형의 설명을 비우는 수정을 하면, 설명이 없어진다

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

- RuntimeVariantAdapter.update — user-1이 variant-1의 설명 고침

Then

- 심은 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'variant-1'
  - description = None
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [renaming-a-variant-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

슈퍼관리자가 변형의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 남는다

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

- RuntimeVariantAdapter.update — user-1이 variant-1의 이름 고침

Then

- 심은 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = '심어둔 런타임 변형'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [renaming-a-variant-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

변형 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름이 겹친다는 이유로 거부된다. 만들 때와 달리 저장소의 제약 위반이 그대로 온다

Given

- 런타임 변형 2개와, 슈퍼관리자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.update — user-1이 wanted-1의 이름을 other-1으로 고침

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

슈퍼관리자가 아무 변형도 갖지 않은 id를 고치면 대상이 없다는 것으로 거부된다

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

- RuntimeVariantAdapter.update — user-1이 없는 id의 이름 고침

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [turning-enforcement-off-lets-a-user-edit-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 변형을 고친다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

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

- RuntimeVariantAdapter.update — user-1이 variant-1의 이름 고침

Then

- 심은 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = '심어둔 런타임 변형'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading

#### [a-user-granted-nothing-reads-a-variant-by-id](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 id로 조회하면, 그 변형 전체가 온다. 이 읽기는 인증만 본다

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

- RuntimeVariantAdapter.get — user-1이 variant-1로 조회

Then

- 심은 변형 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'variant-1'
  - description = '심어둔 런타임 변형'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-variant-name-resolves-to-its-id-for-any-user](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 이름을 해석하면 그 변형의 id가 온다

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

- RuntimeVariantAdapter.resolve_by_name — user-1이 variant-1을 id로 해석

Then

- 심은 변형의 id가 온다
  - id: 심은 변형와 같다

#### [an-empty-id-list-answers-empty-without-a-call](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py) — pass

빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다

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

- RuntimeVariantAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - items = []

#### [reading-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py) — pass

아무 변형도 갖지 않은 id로 조회하면 대상이 없다는 것으로 거부된다

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

- RuntimeVariantAdapter.get — user-1이 없는 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [resolving-a-variant-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py) — pass

아무 변형도 갖지 않은 이름을 해석하면 대상이 없다는 것으로 거부된다. 이 해석에는 뒤따르는 권한 검사가 없어 없다는 사실이 그대로 드러난다

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

- RuntimeVariantAdapter.resolve_by_name — user-1이 no-such-variant을 id로 해석

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [variants-read-by-many-ids-come-back-in-the-order-asked](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py) — pass

있는 id 둘과 없는 id 하나를 한 번에 읽으면, 준 순서대로 오고 없는 id 자리는 비어서 온다

Given

- 런타임 변형 2개와, 일반 사용자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.batch_load_by_ids — user-1이 심은 2개와 없는 id 하나를 한 번에 조회

Then

- 준 순서대로, 없는 id 자리는 비어서 온다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].name = 'wanted-1'
  - items[0].description = '심어둔 런타임 변형'
  - items[0].reads_vfolder_config_files = False
  - items[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].name = 'other-1'
  - items[1].description = '심어둔 런타임 변형'
  - items[1].reads_vfolder_config_files = False
  - items[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[2] = None

### retiring

#### [a-user-granted-nothing-may-not-delete-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 변형을 지우면 권한 부족으로 거부된다

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

- RuntimeVariantAdapter.delete — user-1이 variant-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-delete-many-variants](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 변형 둘을 한 번에 지우면 권한 부족으로 거부된다

Given

- 런타임 변형 2개와, 일반 사용자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.bulk_delete — user-1이 2개를 한 번에 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-unknown-id-in-a-bulk-delete-is-not-found-after-the-ones-before-it-are-gone](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

있는 id 뒤에 없는 id를 붙여 한 번에 지우면 대상이 없다는 것으로 거부된다. 한 트랜잭션이 아니라 앞의 것은 이미 지워져 있다

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

- RuntimeVariantAdapter.bulk_delete — user-1이 variant-1와 없는 id를 한 번에 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [deleting-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

슈퍼관리자가 아무 변형도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다

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

- RuntimeVariantAdapter.delete — user-1이 없는 id를 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-deletes-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

슈퍼관리자가 변형을 지우면 지운 변형의 id를 실은 답이 온다

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

- RuntimeVariantAdapter.delete — user-1이 variant-1를 지움

Then

- 지운 변형의 id가 온다
  - id: 심은 변형와 같다

#### [the-superadmin-deletes-many-variants-at-once](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

슈퍼관리자가 변형 둘을 한 번에 지우면, 답은 요청한 id의 수를 그대로 싣는다

Given

- 런타임 변형 2개와, 슈퍼관리자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.bulk_delete — user-1이 2개를 한 번에 지움

Then

- 요청한 id의 수가 온다
  - deleted_count = 2

#### [turning-enforcement-off-lets-a-user-delete-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 변형을 지운다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

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

- RuntimeVariantAdapter.delete — user-1이 variant-1를 지움

Then

- 지운 변형의 id가 온다
  - id: 심은 변형와 같다

### searching

#### [a-name-filter-narrows-the-answer-to-the-variant-it-names](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py) — pass

변형 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 변형만 남는다

Given

- 런타임 변형 3개와, 일반 사용자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 런타임 변형 other-2
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.search — user-1이 wanted-1으로 걸러 조회

Then

- 걸러낸 그 변형 하나만 남는다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-counts-every-variant-laid](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py) — pass

변형 둘이 있을 때 아무 권한도 받지 않은 사용자가 필터 없이 조회하면 둘을 모두 센다

Given

- 런타임 변형 2개와, 일반 사용자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.search — user-1이 필터 없이 전체 조회

Then

- 심은 변형이 모두 세어진다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-variants-and-a-next-page](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py) — pass

변형 열하나가 있을 때 크기 없이 조회하면 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 런타임 변형 11개와, 일반 사용자 한 명
  - 런타임 변형 wanted-1
  - 런타임 변형 other-1
  - 런타임 변형 other-2
  - 런타임 변형 other-3
  - 런타임 변형 other-4
  - 런타임 변형 other-5
  - 런타임 변형 other-6
  - 런타임 변형 other-7
  - 런타임 변형 other-8
  - 런타임 변형 other-9
  - 런타임 변형 other-10
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RuntimeVariantAdapter.search — user-1이 필터 없이 전체 조회

Then

- 기본 크기의 첫 쪽이 온다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

