## resource_slot

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_slot/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_slot/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-slot-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

같은 이름의 슬롯 종류가 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부된다. 이 행은 에이전트 자원·커널 할당·모델 카드 자원 요구·배포 preset 자원 슬롯·배포 리비전 자원 슬롯 테이블이 참조하므로 덮어쓰지 않는다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 이미 있는 이름 slot-1(으)로 다시 생성

Then

- 거부된다
  - 거부: ResourceSlotTypeAlreadyExists

#### [a-slot-type-made-with-every-display-value-carries-them-back](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 표시 이름·설명·단위·아이콘·서식·순위까지 지정해 생성하면, 지정한 값이 그대로 담긴 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 count 종류 슬롯 cuda.shares(을)를 표시 항목까지 지정해 생성

Then

- 생성한 슬롯 종류 전체가 반환된다
  - id = 'cuda.shares'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'cuda.shares'
  - slot_type = 'count'
  - required = True
  - enabled = False
  - display_name = 'GPU shares'
  - description = 'fractional GPU'
  - display_unit = 'share'
  - display_icon = 'gpu'
  - number_format = NumberFormatInfo(binary=True, round_length=2)
  - rank = 3

#### [a-slot-type-of-the-bytes-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 bytes 종류로 생성하면 그 종류가 담긴 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 bytes 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 생성한 슬롯 종류 전체가 반환된다
  - id = 'cuda.shares'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'cuda.shares'
  - slot_type = 'bytes'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [a-slot-type-of-the-count-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 count 종류로 생성하면 그 종류가 담긴 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 count 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 생성한 슬롯 종류 전체가 반환된다
  - id = 'cuda.shares'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'cuda.shares'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [a-slot-type-of-the-unified-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 unified 종류로 생성하면 그 종류가 담긴 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 unified 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 생성한 슬롯 종류 전체가 반환된다
  - id = 'cuda.shares'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'cuda.shares'
  - slot_type = 'unified'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [a-slot-type-of-the-unique-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 unique 종류로 생성하면 그 종류가 담긴 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 unique 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 생성한 슬롯 종류 전체가 반환된다
  - id = 'cuda.shares'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'cuda.shares'
  - slot_type = 'unique'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [a-user-who-is-not-the-superadmin-may-not-create-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 슬롯 종류를 생성하면 역할 부족으로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 count 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-makes-a-slot-type-with-a-name-and-a-kind-alone](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

슈퍼관리자가 슬롯 이름과 종류만 지정해 생성하면, 표시용 문자열은 모두 비고 필수 여부는 거짓, 사용 여부는 참, 순위는 0, 숫자 서식은 십진에 반올림 없음인 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 count 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 생성한 슬롯 종류 전체가 반환된다
  - id = 'cuda.shares'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'cuda.shares'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [turning-enforcement-off-does-not-let-a-user-create-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

권한 검사를 꺼도 슈퍼관리자가 아니면 슬롯 종류를 생성하지 못한다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_create_slot_type — user-1이 count 종류 슬롯 cuda.shares(을)를 이름과 종류만 지정해 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-slot-type-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

슬롯 이름만 지정하고 나머지를 모두 생략해 수정하면 아무것도 바뀌지 않은 노드가 반환된다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_update_slot_type — user-1이 slot-1의 아무것도 수정

Then

- 미리 만들어 둔 슬롯 종류 전체가 반환된다
  - id = 'slot-1'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = '미리 만들어 둔 슬롯'
  - description = '미리 만들어 둔 슬롯 종류'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [a-user-who-is-not-the-superadmin-may-not-edit-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

슈퍼관리자가 아닌 사용자가 슬롯 종류를 수정하면 역할 부족으로 거부된다

Given

- 자원 슬롯 종류 하나와, 일반 사용자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_update_slot_type — user-1이 slot-1의 표시 이름 수정

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [disabling-a-slot-type-answers-it-disabled](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

사용 중인 슬롯 종류의 사용 여부를 끄면, 사용하지 않는 상태가 담긴 노드가 반환된다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_update_slot_type — user-1이 slot-1의 사용 여부 수정

Then

- 미리 만들어 둔 슬롯 종류 전체가 반환된다
  - id = 'slot-1'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = False
  - display_name = '미리 만들어 둔 슬롯'
  - description = '미리 만들어 둔 슬롯 종류'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [editing-a-slot-type-display-name-leaves-the-rest-alone](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

슈퍼관리자가 이름으로 지정해 표시 이름만 수정하면, 표시 이름은 새 값이 되고 나머지는 그대로 유지된다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_update_slot_type — user-1이 slot-1의 표시 이름 수정

Then

- 미리 만들어 둔 슬롯 종류 전체가 반환된다
  - id = 'slot-1'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = 'GPU shares'
  - description = '미리 만들어 둔 슬롯 종류'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [the-superadmin-editing-a-slot-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 이름을 수정하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_update_slot_type — user-1이 no-such-slot의 표시 이름 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [turning-enforcement-off-does-not-let-a-user-edit-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

권한 검사를 꺼도 슈퍼관리자가 아니면 슬롯 종류를 수정하지 못한다

Given

- 자원 슬롯 종류 하나와, 일반 사용자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_update_slot_type — user-1이 slot-1의 표시 이름 수정

Then

- 거부된다
  - 거부: InsufficientPrivilege

### reading

#### [a-user-granted-nothing-reads-a-slot-type-by-name](/tests/scenario/bai_scenario/manager/resource_slot/test_reading.py) — pass

아무 권한도 없는 사용자가 이름으로 조회하면 그 슬롯 종류 전체가 반환된다. 이름을 풀어내는 단계도 그 뒤의 조회도 인증만 확인한다

Given

- 자원 슬롯 종류 하나와, 일반 사용자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_slot_type — user-1이 slot-1 이름으로 조회

Then

- 미리 만들어 둔 슬롯 종류 전체가 반환된다
  - id = 'slot-1'
  - uuid: 무시함 — 데이터베이스가 만든다
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = '미리 만들어 둔 슬롯'
  - description = '미리 만들어 둔 슬롯 종류'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

#### [reading-a-slot-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading.py) — pass

존재하지 않는 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 자원 슬롯 종류 하나와, 일반 사용자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_slot_type — user-1이 no-such-slot 이름으로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### reading_agent_resources

#### [a-user-granted-nothing-may-not-read-an-agent-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py) — pass

아무 권한도 없는 사용자가 조회하면 권한 부족으로 거부된다. 에이전트에 대한 권한을 슬롯을 찾기 전에 검사한다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_agent_resource — user-1이 agent-1 에이전트의 cpu 슬롯 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-reading-an-unknown-agent-name-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 에이전트 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다. 이름을 풀어내는 단계는 인증만 확인하고, 권한은 풀어낸 에이전트에 대해 검사한다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_agent_resource — user-1이 no-such-agent 에이전트의 cpu 슬롯 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [a-user-reading-agents-in-the-group-reaches-the-slot-the-agent-does-not-report](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py) — pass

리소스 그룹의 에이전트를 읽을 수 있는 사용자가 에이전트가 보고하지 않는 슬롯을 조회하면 권한 검사를 통과한 뒤 대상을 찾을 수 없다는 이유로 거부된다

Given

- 에이전트 하나와, 그것을 읽을 수 있는 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 agent-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- ResourceSlotAdapter.get_agent_resource — user-1이 agent-1 에이전트의 cpu 슬롯 조회

Then

- 거부된다
  - 거부: AgentResourceNotFound

#### [reading-a-slot-the-agent-does-not-report-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py) — pass

슈퍼관리자가 에이전트가 보고하지 않는 슬롯을 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 에이전트 하나와, 슈퍼관리자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_agent_resource — user-1이 agent-1 에이전트의 cpu 슬롯 조회

Then

- 거부된다
  - 거부: AgentResourceNotFound

#### [reading-an-agent-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py) — pass

슈퍼관리자가 존재하지 않는 에이전트 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 에이전트 하나와, 슈퍼관리자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_agent_resource — user-1이 no-such-agent 에이전트의 cpu 슬롯 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [turning-enforcement-off-lets-a-user-pass-the-gate-to-the-slot-the-agent-does-not-report](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 권한 검사를 통과하고, 에이전트가 보고하지 않는 슬롯이므로 대상을 찾을 수 없다는 이유로 거부된다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.get_agent_resource — user-1이 agent-1 에이전트의 cpu 슬롯 조회

Then

- 거부된다
  - 거부: AgentResourceNotFound

### reading_allocations

#### [a-user-granted-nothing-may-not-read-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

아무 권한도 없는 사용자가 조회하면 커널 id를 풀어낼 수 없다는 이유로 거부된다. 커널 id를 세션으로 풀어내는 단계가 그 세션에 대한 권한을 검사하고, 권한이 없을 때와 커널이 없을 때 같은 답을 한다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 미리 만들어 둔 커널의 id와 slot-1 슬롯 이름으로 조회

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-reading-an-unknown-kernel-id-is-refused-the-same-way](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 커널 id로 조회해도 커널 id를 풀어낼 수 없다는 같은 이유로 거부된다. 답으로는 그 커널이 있는지 알 수 없다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 존재하지 않는 커널 id와 slot-1 슬롯 이름으로 조회

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-reading-sessions-in-the-project-reads-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

프로젝트 범위에서 세션을 읽을 수 있는 사용자가 조회하면 그 할당 전체가 반환된다. 할당은 커널이 속한 세션의 것이므로, 세션에 대한 권한이 할당을 읽게 한다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 프로젝트 범위에서 세션을 읽을 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 미리 만들어 둔 커널의 id와 slot-1 슬롯 이름으로 조회

Then

- 그 커널의 할당 전체가 반환된다
  - id: 미리 만들어 둔 커널의 id와 슬롯 이름와 같다
  - kernel_id: 미리 만들어 둔 커널의 id와 같다
  - slot_name = 'slot-1'
  - requested: 수로 보아 1
  - used = None

#### [reading-a-kernel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

슈퍼관리자가 존재하지 않는 커널 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다. 모든 검사를 통과하는 슈퍼관리자에게는 없다는 사실을 그대로 답한다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 존재하지 않는 커널 id와 slot-1 슬롯 이름으로 조회

Then

- 거부된다
  - 거부: FieldNotFoundError

#### [reading-a-slot-the-kernel-did-not-ask-for-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

슈퍼관리자가 그 커널이 요구하지 않은 슬롯 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 미리 만들어 둔 커널의 id와 no-such-slot 슬롯 이름으로 조회

Then

- 거부된다
  - 거부: ResourceAllocationNotFound

#### [the-superadmin-reads-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

슈퍼관리자가 커널 id와 슬롯 이름으로 조회하면 그 할당 전체가 반환된다. 커널은 아직 스케줄링되지 않았으므로 요구한 양만 있고 실제 사용량은 없다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 미리 만들어 둔 커널의 id와 slot-1 슬롯 이름으로 조회

Then

- 그 커널의 할당 전체가 반환된다
  - id: 미리 만들어 둔 커널의 id와 슬롯 이름와 같다
  - kernel_id: 미리 만들어 둔 커널의 id와 같다
  - slot_name = 'slot-1'
  - requested: 수로 보아 1
  - used = None

#### [turning-enforcement-off-lets-a-user-read-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 할당을 조회할 수 있다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_kernel_allocation — user-2이 미리 만들어 둔 커널의 id와 slot-1 슬롯 이름으로 조회

Then

- 그 커널의 할당 전체가 반환된다
  - id: 미리 만들어 둔 커널의 id와 슬롯 이름와 같다
  - kernel_id: 미리 만들어 둔 커널의 id와 같다
  - slot_name = 'slot-1'
  - requested: 수로 보아 1
  - used = None

### reading_domain_overview

#### [a-user-granted-nothing-may-not-read-a-domain-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py) — pass

아무 권한도 없는 사용자가 조회하면 권한 부족으로 거부된다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_domain_resource_overview — user-2이 home-1 도메인의 개요 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-reading-sessions-in-the-domain-reads-its-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py) — pass

도메인 범위에서 세션을 읽을 수 있는 사용자가 그 도메인의 개요를 조회하면 개요가 반환된다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 도메인 범위에서 세션을 읽을 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다
  - 도메인 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- ResourceSlotAdapter.get_domain_resource_overview — user-2이 home-1 도메인의 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

#### [a-user-reading-sessions-in-the-project-may-not-read-the-domain-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py) — pass

프로젝트 범위에서만 세션을 읽을 수 있는 사용자가 그 프로젝트가 속한 도메인의 개요를 조회하면 권한 부족으로 거부된다. 도메인 개요는 도메인 범위의 권한을 검사한다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 프로젝트 범위에서 세션을 읽을 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- ResourceSlotAdapter.get_domain_resource_overview — user-2이 home-1 도메인의 개요 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [reading-the-overview-of-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py) — pass

존재하지 않는 도메인 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_domain_resource_overview — user-2이 no-such-domain 도메인의 개요 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-reads-a-domain-overview-that-counts-no-pending-kernel](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py) — pass

대기 중인 커널만 있는 도메인의 개요를 슈퍼관리자가 조회하면 점유된 슬롯이 없고 세션 수가 0이다. 개요는 자원을 점유했거나 배정받은 커널만 세고, 요구만 한 커널은 세지 않는다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_domain_resource_overview — user-2이 home-1 도메인의 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

#### [turning-enforcement-off-lets-a-user-read-a-domain-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 도메인의 개요를 조회할 수 있다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_domain_resource_overview — user-2이 home-1 도메인의 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

### reading_project_overview

#### [a-user-granted-nothing-may-not-read-a-project-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py) — pass

아무 권한도 없는 사용자가 조회하면 권한 부족으로 거부된다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_project_resource_overview — user-2이 team-1 프로젝트의 id로 개요 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-reading-sessions-in-the-domain-reads-a-project-overview-in-it](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py) — pass

도메인 범위에서 세션을 읽을 수 있는 사용자가 그 도메인에 속한 프로젝트의 개요를 조회하면 개요가 반환된다. 도메인 범위의 권한은 그 안의 프로젝트에도 미친다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 도메인 범위에서 세션을 읽을 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다
  - 도메인 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- ResourceSlotAdapter.get_project_resource_overview — user-2이 team-1 프로젝트의 id로 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

#### [a-user-reading-sessions-in-the-project-reads-its-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py) — pass

프로젝트 범위에서 세션을 읽을 수 있는 사용자가 그 프로젝트의 개요를 조회하면 개요가 반환된다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 프로젝트 범위에서 세션을 읽을 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- ResourceSlotAdapter.get_project_resource_overview — user-2이 team-1 프로젝트의 id로 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

#### [reading-the-overview-of-a-project-id-nothing-answers-to-answers-an-empty-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py) — pass

슈퍼관리자가 존재하지 않는 프로젝트 id로 조회하면 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다. 도메인 개요와 달리 프로젝트는 id로 지정하므로 풀어내는 단계가 없고, 프로젝트가 있는지 확인하지 않는다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_project_resource_overview — user-2이 존재하지 않는 프로젝트 id로 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

#### [the-superadmin-reads-a-project-overview-that-counts-no-pending-kernel](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py) — pass

대기 중인 커널만 있는 프로젝트의 개요를 슈퍼관리자가 조회하면 점유된 슬롯이 없고 세션 수가 0이다. 개요는 자원을 점유했거나 배정받은 커널만 세고, 요구만 한 커널은 세지 않는다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_project_resource_overview — user-2이 team-1 프로젝트의 id로 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

#### [turning-enforcement-off-lets-a-user-read-a-project-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 프로젝트의 개요를 조회할 수 있다

Given

- 슬롯 둘을 요구하며 대기 중인 커널 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.get_project_resource_overview — user-2이 team-1 프로젝트의 id로 개요 조회

Then

- 점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다
  - slots.entries = []
  - session_count = 0

### retiring

#### [a-slot-type-a-deployment-revision-still-uses-may-not-be-purged](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

배포 리비전이 아직 사용하는 슬롯 종류를 슈퍼관리자가 삭제하면 아직 사용 중이라는 이유로 거부된다

Given

- 배포 리비전 하나가 사용하는 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 폴더, 런타임 변형, 자원 슬롯 타입 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 폴더 folder-1: 그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다
    - 폴더 읽기 권한 부여
      - 역할 folder-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 슈퍼관리자 user-1: 역할 folder-reader-1 보유
    - 런타임 변형 runtime-1: 기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다
    - 자원 슬롯 타입 cpu: 리비전이 채우지 않아도 된다
    - 자원 슬롯 타입 mem: 리비전이 채우지 않아도 된다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- ResourceSlotAdapter.admin_purge_slot_type — user-1이 cpu 삭제

Then

- 거부된다
  - 거부: ResourceSlotTypeInUse

#### [a-slot-type-a-kernel-still-asks-for-may-not-be-purged](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

커널이 아직 할당받은 슬롯 종류를 슈퍼관리자가 삭제하면 아직 사용 중이라는 이유로 거부된다

Given

- 대기 중인 커널 하나가 요구하는 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖는다

When

- ResourceSlotAdapter.admin_purge_slot_type — user-2이 slot-1 삭제

Then

- 거부된다
  - 거부: ResourceSlotTypeInUse

#### [a-user-granted-nothing-may-not-purge-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

아무 권한도 없는 사용자가 슬롯 종류를 삭제하면 권한 부족으로 거부된다. 수정이 역할 부족으로 거부되는 것과는 다른 검사다

Given

- 자원 슬롯 종류 하나와, 일반 사용자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_purge_slot_type — user-1이 slot-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [purging-a-slot-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

슈퍼관리자가 존재하지 않는 이름을 삭제하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_purge_slot_type — user-1이 no-such-slot 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-purges-a-slot-type-nothing-refers-to](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

아무것도 참조하지 않는 슬롯 종류를 슈퍼관리자가 이름으로 삭제하면 삭제한 이름을 담은 응답이 반환된다

Given

- 자원 슬롯 종류 하나와, 슈퍼관리자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_purge_slot_type — user-1이 slot-1 삭제

Then

- 삭제한 슬롯 종류의 이름이 반환된다
  - slot_name = 'slot-1'

#### [turning-enforcement-off-lets-a-user-purge-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 슬롯 종류를 삭제할 수 있다

Given

- 자원 슬롯 종류 하나와, 일반 사용자 한 명
  - 자원 슬롯 종류 slot-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.admin_purge_slot_type — user-1이 slot-1 삭제

Then

- 삭제한 슬롯 종류의 이름이 반환된다
  - slot_name = 'slot-1'

### scoped_searching_agent_resources

#### [a-user-granted-nothing-may-not-search-an-agent-s-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py) — pass

아무 권한도 없는 사용자가 에이전트를 지정해 조회하면 권한 부족으로 거부된다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.scoped_search_agent_resources — user-1이 agent-1 에이전트를 지정해 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-reading-agents-in-the-group-searches-the-agent-and-finds-no-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py) — pass

리소스 그룹의 에이전트를 읽을 수 있는 사용자가 아직 슬롯을 보고하지 않은 그 에이전트를 지정해 조회하면 응답이 비어 있다

Given

- 에이전트 하나와, 그것을 읽을 수 있는 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 agent-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- ResourceSlotAdapter.scoped_search_agent_resources — user-1이 agent-1 에이전트를 지정해 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [one-agent-the-caller-may-not-read-refuses-the-whole-search](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py) — pass

둘 중 한 에이전트만 읽을 수 있는 사용자가 둘을 함께 지정해 조회하면 전체가 권한 부족으로 거부된다. 읽을 수 있는 쪽만 골라 답하지 않는다

Given

- 리소스 그룹이 다른 에이전트 둘과, 한쪽 그룹의 에이전트만 읽을 수 있는 일반 사용자 한 명
  - 리소스 그룹 mine-1: fifo 스케줄러를 쓴다
  - 에이전트 readable-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 리소스 그룹 elsewhere-1: fifo 스케줄러를 쓴다
  - 에이전트 other-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 agent-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- ResourceSlotAdapter.scoped_search_agent_resources — user-1이 readable-1와 other-1 에이전트를 함께 지정해 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-superadmin-searches-the-agent-and-finds-no-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py) — pass

슈퍼관리자가 아직 슬롯을 보고하지 않은 에이전트를 지정해 조회하면 응답이 비어 있다

Given

- 에이전트 하나와, 슈퍼관리자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.scoped_search_agent_resources — user-1이 agent-1 에이전트를 지정해 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-lets-a-user-search-an-agent-s-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 에이전트를 지정해 조회할 수 있다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.scoped_search_agent_resources — user-1이 agent-1 에이전트를 지정해 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

### searching

#### [a-name-filter-narrows-the-answer-to-the-slot-type-it-names](/tests/scenario/bai_scenario/manager/resource_slot/test_searching.py) — pass

슬롯 종류 여럿 중 하나의 이름을 필터로 조회하면, 응답에는 그 이름의 슬롯 종류만 남는다

Given

- 자원 슬롯 종류 3개와, 일반 사용자 한 명
  - 자원 슬롯 종류 wanted-1: count 종류
  - 자원 슬롯 종류 other-1: count 종류
  - 자원 슬롯 종류 other-2: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_slot_types — user-1이 wanted-1 이름 필터로 조회

Then

- 필터에 맞는 슬롯 종류 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-counts-every-slot-type-laid](/tests/scenario/bai_scenario/manager/resource_slot/test_searching.py) — pass

슬롯 종류 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다

Given

- 자원 슬롯 종류 2개와, 일반 사용자 한 명
  - 자원 슬롯 종류 wanted-1: count 종류
  - 자원 슬롯 종류 other-1: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_slot_types — user-1이 필터 없이 전체 조회

Then

- 미리 만들어 둔 슬롯 종류가 모두 집계된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-ten-slot-types-and-a-next-page](/tests/scenario/bai_scenario/manager/resource_slot/test_searching.py) — pass

슬롯 종류 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다

Given

- 자원 슬롯 종류 11개와, 일반 사용자 한 명
  - 자원 슬롯 종류 wanted-1: count 종류
  - 자원 슬롯 종류 other-1: count 종류
  - 자원 슬롯 종류 other-2: count 종류
  - 자원 슬롯 종류 other-3: count 종류
  - 자원 슬롯 종류 other-4: count 종류
  - 자원 슬롯 종류 other-5: count 종류
  - 자원 슬롯 종류 other-6: count 종류
  - 자원 슬롯 종류 other-7: count 종류
  - 자원 슬롯 종류 other-8: count 종류
  - 자원 슬롯 종류 other-9: count 종류
  - 자원 슬롯 종류 other-10: count 종류
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_slot_types — user-1이 필터 없이 전체 조회

Then

- 기본 크기의 첫 페이지가 반환된다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

### searching_agent_resources

#### [a-monitor-may-search-agent-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py) — pass

모니터가 필터 없이 조회하면 응답이 반환된다. 슈퍼관리자인지 검사하는 조회는 모니터도 통과한다

Given

- 에이전트 하나와, 모니터 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_agent_resources — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-may-not-search-agent-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py) — pass

아무 권한도 없는 사용자가 조회하면 역할 부족으로 거부된다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_agent_resources — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-agent-reporting-no-slot-means-none-is-found](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py) — pass

아직 슬롯을 보고하지 않은 에이전트만 있을 때 슈퍼관리자가 필터 없이 조회하면 응답이 비어 있다

Given

- 에이전트 하나와, 슈퍼관리자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_agent_resources — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-still-refuses-a-user-searching-agent-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py) — pass

권한 검사를 꺼도 슈퍼관리자나 모니터가 아니면 조회할 수 없다. 슈퍼관리자 검사는 그 설정을 읽지 않는다

Given

- 에이전트 하나와, 일반 사용자 한 명
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceSlotAdapter.search_agent_resources — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### searching_allocations

#### [a-kernel-id-filter-narrows-the-answer-to-that-kernel-s-allocations](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

슬롯 하나씩 요구하는 커널 둘이 있을 때 한 커널의 id를 필터로 조회하면, 응답에는 그 커널의 할당만 남는다

Given

- 슬롯 1개씩 요구하는 커널 2개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖는다
  - 세션 session-2: 스케줄링을 기다리고 있다
  - 세션 session-2: 요구량이 slot-1 1인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 미리 만들어 둔 커널 중 하나의 id 필터로 조회

Then

- 필터에 맞는 커널의 할당만 반환된다
  - items: 골라낼 커널의 id와 그 슬롯 이름와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-monitor-counts-every-allocation-laid](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

모니터가 필터 없이 조회하면 할당이 다 집계된다. 슈퍼관리자인지 검사하는 조회는 모니터도 통과한다

Given

- 슬롯 2개씩 요구하는 커널 1개와, 모니터 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 모니터 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 필터 없이 전체 조회

Then

- 미리 만들어 둔 할당이 모두 집계된다
  - items: 미리 만들어 둔 커널들의 id와 슬롯 이름와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-slot-name-filter-narrows-the-answer-to-that-slot-s-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

슬롯 둘을 요구하는 커널 하나가 있을 때 한 슬롯의 이름을 필터로 조회하면, 응답에는 그 슬롯의 할당만 남는다

Given

- 슬롯 2개씩 요구하는 커널 1개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 slot-1 슬롯 이름 필터로 조회

Then

- 필터에 맞는 슬롯의 할당 하나만 반환된다
  - items = ['slot-1']
  - items[0].kernel_id: 골라낼 커널의 id와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-may-not-search-allocations](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

아무 권한도 없는 사용자가 조회하면 역할 부족으로 거부된다

Given

- 슬롯 2개씩 요구하는 커널 1개와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [omitting-the-page-size-answers-ten-allocations-and-a-next-page](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

할당 11건이 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다

Given

- 슬롯 11개씩 요구하는 커널 1개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 자원 슬롯 종류 slot-3: count 종류
  - 자원 슬롯 종류 slot-4: count 종류
  - 자원 슬롯 종류 slot-5: count 종류
  - 자원 슬롯 종류 slot-6: count 종류
  - 자원 슬롯 종류 slot-7: count 종류
  - 자원 슬롯 종류 slot-8: count 종류
  - 자원 슬롯 종류 slot-9: count 종류
  - 자원 슬롯 종류 slot-10: count 종류
  - 자원 슬롯 종류 slot-11: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2, slot-3 3, slot-4 4, slot-5 5, slot-6 6, slot-7 7, slot-8 8, slot-9 9, slot-10 10, slot-11 11인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 필터 없이 전체 조회

Then

- 기본 크기의 첫 페이지가 반환된다
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [the-superadmin-counts-every-allocation-laid](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

슬롯 둘을 요구하는 커널 하나가 있을 때 슈퍼관리자가 필터 없이 조회하면 할당 둘이 다 집계된다

Given

- 슬롯 2개씩 요구하는 커널 1개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 필터 없이 전체 조회

Then

- 미리 만들어 둔 할당이 모두 집계된다
  - items: 미리 만들어 둔 커널들의 id와 슬롯 이름와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [turning-enforcement-off-still-refuses-a-user-searching-allocations](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py) — pass

권한 검사를 꺼도 슈퍼관리자나 모니터가 아니면 조회할 수 없다. 슈퍼관리자 검사는 그 설정을 읽지 않는다

Given

- 슬롯 2개씩 요구하는 커널 1개와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 자원 슬롯 종류 slot-1: count 종류
  - 자원 슬롯 종류 slot-2: count 종류
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-1: 요구량이 slot-1 1, slot-2 2인 커널 하나를 갖는다

When

- ResourceSlotAdapter.search_allocations — user-2이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

