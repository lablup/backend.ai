## resource_slot

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_slot/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_slot/adapter.py)

Not exercised by any scenario: batch_load_fields, get_agent_resource, get_domain_resource_overview, get_kernel_allocation, get_project_resource_overview, scoped_search_agent_resources, search_agent_resources, search_allocations.

### creating

#### [a-slot-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py) — pass

같은 이름의 슬롯 종류가 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부된다. 이 행은 다섯 테이블의 참조 대상이라 덮어쓰지 않는다

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

권한 검사를 꺼도 슈퍼관리자가 아니면 슬롯 종류를 생성하지 못한다. 생성은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다

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

#### [a-user-without-the-role-editing-an-unknown-slot-name-hears-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py) — pass

슈퍼관리자가 아닌 사용자가 존재하지 않는 이름을 수정하면 역할 부족이 아니라 대상 없음으로 거부된다. 이름을 풀어내는 단계가 권한을 검사하지 않고 먼저 실행되기 때문이다

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

- ResourceSlotAdapter.admin_update_slot_type — user-1이 no-such-slot의 표시 이름 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

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

권한 검사를 꺼도 슈퍼관리자가 아니면 슬롯 종류를 수정하지 못한다. 수정은 삭제와 달리 역할로 보호되므로 스위치와 무관하다

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

### retiring

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

#### [a-user-granted-nothing-purging-an-unknown-slot-name-hears-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 이름을 삭제하면 권한 부족이 아니라 대상 없음으로 거부된다. 이름을 풀어내는 단계가 권한을 검사하지 않고 먼저 실행되기 때문이다

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

- ResourceSlotAdapter.admin_purge_slot_type — user-1이 no-such-slot 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

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

권한 검사를 끄면 아무 권한도 없는 사용자도 슬롯 종류를 삭제할 수 있다. 삭제는 수정과 달리 권한 그래프로 보호되므로 스위치가 영향을 준다

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

