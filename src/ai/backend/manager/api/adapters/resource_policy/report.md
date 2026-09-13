## resource_policy

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_policy/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_policy/adapter.py)

Not exercised by any scenario: admin_create_project_resource_policy, admin_create_user_resource_policy, admin_delete_project_resource_policy, admin_delete_user_resource_policy, admin_get_project_resource_policy, admin_get_user_resource_policy, admin_search_project_resource_policies, admin_search_user_resource_policies, admin_update_project_resource_policy, admin_update_user_resource_policy, batch_load_fields, get_my_user_resource_policy.

### creating

#### [a-monitor-may-not-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

모니터 역할 사용자가 키페어 정책을 생성하려 하면 역할 부족으로 거부된다. 역할 검사는 모니터에게 읽기만 허용한다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 모든 값을 지정해 키페어 정책을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-name-another-keypair-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

이미 다른 키페어 정책이 사용 중인 이름으로 생성하려 하면, 이름 중복으로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 이미 있는 이름으로 키페어 정책을 생성

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [a-priority-cap-outside-the-session-range-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해 키페어 정책을 생성하려 하면, 제약 위반으로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해 키페어 정책을 생성

Then

- 거부된다
  - 거부: CheckConstraintViolationError

#### [a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 키페어 정책을 생성하려 하면, 어떤 권한을 받았는지와 무관하게 역할 부족으로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 모든 값을 지정해 키페어 정책을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 한 자원의 전체 슬롯을 무제한으로 지정해 키페어 정책을 생성하면, 그 자원은 무제한으로 표시되고 수량은 비어 있다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 cpu 슬롯을 무제한으로 지정해 키페어 정책을 생성

Then

- 생성한 키페어 정책 전체가 반환된다
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', None, True)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = 2
  - max_priority = 10
  - max_pending_session_resource_slots = [('cpu', Decimal('2'), False)]
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

#### [leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 생략할 수 있는 항목을 모두 생략하고 키페어 정책을 생성하면, 생략한 필드가 비어 있는 노드 전체가 반환된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 대기 세션 수·우선순위 상한·대기 자원 슬롯을 생략하고 키페어 정책을 생성

Then

- 생성한 키페어 정책 전체가 반환된다
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', Decimal('4'), False)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

#### [the-superadmin-creates-a-keypair-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 모든 값을 지정해 키페어 정책을 생성하면, 지정한 값이 그대로 담긴 노드 전체가 반환된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 모든 값을 지정해 키페어 정책을 생성

Then

- 생성한 키페어 정책 전체가 반환된다
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', Decimal('4'), False)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = 2
  - max_priority = 10
  - max_pending_session_resource_slots = [('cpu', Decimal('2'), False)]
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

권한 검사를 꺼도 키페어 정책 생성은 여전히 거부된다. 생성은 권한 그래프가 아니라 역할로 보호되기 때문이다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy — user-1이 모든 값을 지정해 키페어 정책을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-granted-nothing-may-not-edit-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

같은 키페어 정책이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 keypair-policy-2 수정 (동시 세션 수 7로 변경)

Then

- 거부된다
  - 거부: GenericBadRequest

#### [clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 키페어 정책의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 아무것도 바뀌지 않은 노드가 반환된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 keypair-policy-2 수정 (동시 세션 수 비우기)

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [clearing-a-nullable-value-of-a-keypair-policy-empties-it](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

비울 수 있는 항목에 값이 설정된 키페어 정책을 슈퍼관리자가 그 항목을 비우도록 수정하면, 그 항목이 비어 있는 노드가 반환된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, 그중 대기 2개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 keypair-policy-2 수정 (대기 세션 수 비우기)

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [editing-a-keypair-policy-name-nothing-answers-to-is-unresolvable](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 어느 키페어 정책에도 없는 이름을 수정하려 하면, 정책을 찾을 수 없다는 이유로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 nobody 수정 (동시 세션 수 7로 변경)

Then

- 거부된다
  - 거부: GenericBadRequest

#### [giving-no-value-changes-nothing-of-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 키페어 정책을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 반환된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 keypair-policy-2 수정 (빈 요청)

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [moving-the-priority-cap-outside-the-session-range-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 키페어 정책의 우선순위 상한을 세션 우선순위 범위 밖으로 수정하려 하면, 제약 위반으로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 keypair-policy-2 수정 (우선순위 상한을 세션 우선순위 범위 밖으로 변경)

Then

- 거부된다
  - 거부: CheckConstraintViolationError

#### [the-superadmin-changes-one-limit-of-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

키페어 정책 하나가 있고 슈퍼관리자가 한도 하나만 수정하면, 그 한도만 새 값이 되고 나머지는 그대로 유지된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_update_keypair_resource_policy — user-1이 keypair-policy-2 수정 (동시 세션 수 7로 변경)

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 7
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

### reading

#### [a-keypair-policy-name-nothing-answers-to-is-unresolvable-even-for-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

슈퍼관리자가 어느 키페어 정책에도 없는 이름으로 조회하면, 권한 없음과 구분되지 않는 '정책을 찾을 수 없음'으로 거부된다. 거부 응답은 그 이름이 존재하는지 알려 주지 않는다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy — user-1이 nobody 이름으로 조회

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-cannot-resolve-a-keypair-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

같은 키페어 정책이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, 정책을 찾을 수 없다는 이유로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy — user-1이 keypair-policy-2 이름으로 조회

Then

- 거부된다
  - 거부: GenericBadRequest

#### [the-superadmin-reads-a-keypair-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

키페어 정책 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 정책 전체가 반환된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy — user-1이 keypair-policy-2 이름으로 조회

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 키페어 정책을 이름으로 조회할 수 있다. 이 호출은 역할이 아니라 권한 그래프로 보호되기 때문이다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy — user-1이 keypair-policy-2 이름으로 조회

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

### reading_own

#### [a-user-granted-nothing-may-not-read-their-own-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py) — pass

아무 권한도 없는 사용자가 자기 키페어 정책을 조회하면 권한 부족으로 거부된다. 자기 정책을 읽는 호출도 범위만 좁히는 것이 아니라 권한을 검사한다

Given

- 키페어 정책이 할당된 사용자 한 명, 아무 권한도 없음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy — user-1이 자기 키페어 정책을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-in-their-own-scope-reads-their-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py) — pass

자기 스코프에서 키페어 정책을 읽을 권한을 받은 사용자가 자기 정책을 조회하면, 그 사용자에게 할당된 정책 전체가 반환된다

Given

- 키페어 정책이 할당된 사용자 한 명, 자기 스코프에서 그 정책을 읽을 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy — user-1이 자기 키페어 정책을 조회

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-1'
  - name = 'keypair-policy-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [a-user-with-no-active-key-finds-no-keypair-policy-of-their-own](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py) — pass

활성 키페어가 없는 사용자가 자기 키페어 정책을 조회하면, 권한이 있어도 정책에 도달할 키페어가 없어 대상을 찾을 수 없다는 이유로 거부된다

Given

- 활성 키페어가 없는 사용자, 자기 스코프에서 키페어 정책 읽기 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy — user-1이 자기 키페어 정책을 조회

Then

- 거부된다
  - 거부: ObjectNotFound

#### [among-several-keys-the-default-one-names-the-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py) — pass

기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자가 자기 키페어 정책을 조회하면, 기본 키페어에 할당된 정책이 반환된다

Given

- 기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, 읽기 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 other-1: 동시 세션 5개까지
  - 일반 사용자 user-1: other-1 정책이 할당된 활성 키페어 하나 더
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy — user-1이 자기 키페어 정책을 조회

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-1'
  - name = 'keypair-policy-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [an-inactive-default-key-yields-to-the-active-one](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py) — pass

기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자가 자기 키페어 정책을 조회하면, 그 활성 키페어에 할당된 정책이 반환된다

Given

- 기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, 읽기 권한 있음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 other-1: 동시 세션 5개까지
  - 일반 사용자 user-1: other-1 정책이 할당된 활성 키페어 하나 더
  - 자기 스코프에서 keypair_resource_policy 읽기 권한을 주는 역할 부여
    - 역할 policy-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 policy-reader-1: keypair_resource_policy 전체에 READ 허용
    - 일반 사용자 user-1: 역할 policy-reader-1 보유

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy — user-1이 자기 키페어 정책을 조회

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'other-1'
  - name = 'other-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 자기 키페어 정책을 조회할 수 있다. 이 호출은 권한 그래프로 보호되기 때문이다

Given

- 키페어 정책이 할당된 사용자 한 명, 아무 권한도 없음
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy — user-1이 자기 키페어 정책을 조회

Then

- 미리 만들어 둔 키페어 정책 전체가 반환된다
  - id = 'keypair-policy-1'
  - name = 'keypair-policy-1'
  - created_at: 이 실행이 쓴 시각
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

### retiring

#### [a-user-granted-nothing-may-not-purge-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

같은 키페어 정책이 있고 아무 권한도 없는 사용자가 삭제하려 하면, 삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_delete_keypair_resource_policy — user-1이 keypair-policy-2 삭제 후 같은 이름으로 다시 검색

Then

- 거부된다
  - 거부: GenericBadRequest

#### [purging-a-keypair-policy-name-nothing-answers-to-is-unresolvable](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

슈퍼관리자가 어느 키페어 정책에도 없는 이름을 삭제하려 하면, 정책을 찾을 수 없다는 이유로 거부된다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_delete_keypair_resource_policy — user-1이 nobody 삭제 후 같은 이름으로 다시 검색

Then

- 거부된다
  - 거부: GenericBadRequest

#### [purging-a-keypair-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

아직 누군가에게 할당된 키페어 정책을 슈퍼관리자가 삭제하려 하면, 아직 참조 중이라는 이유로 거부된다. 막는 것은 삭제 spec이 아니라 외래 키다

Given

- superadmin 한 명과, 그 사용자에게 아직 할당된 키페어 정책
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePolicyAdapter.admin_delete_keypair_resource_policy — user-1이 keypair-policy-1 삭제 후 같은 이름으로 다시 검색

Then

- 거부된다
  - 거부: ForeignKeyViolationError

#### [the-superadmin-purges-a-keypair-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

아무도 사용하지 않는 키페어 정책을 슈퍼관리자가 삭제하면, 삭제한 이름이 반환되고 이어서 검색하면 없다

Given

- 아무도 사용하지 않는 키페어 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_delete_keypair_resource_policy — user-1이 keypair-policy-2 삭제 후 같은 이름으로 다시 검색

Then

- 삭제한 이름이 반환되고 다시 검색하면 없다
  - name = 'keypair-policy-2'
  - found afterwards = 0

### searching

#### [a-monitor-finds-every-keypair-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

모니터 역할 사용자가 키페어 정책 전체를 검색하면 슈퍼관리자와 같은 응답이 반환된다. 역할 검사가 읽기는 모니터에게도 허용하기 때문이다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 monitor 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies — user-1이 필터 없이 전체 검색

Then

- 미리 만들어 둔 키페어 정책이 모두, 그리고 그것만 반환된다
  - items = ['keypair-policy-1', 'other-1', 'wanted-1']
  - total_count = 3

#### [a-user-who-is-not-the-superadmin-may-not-search-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 키페어 정책 전체를 검색하려 하면 역할 부족으로 거부된다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 user 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies — user-1이 필터 없이 전체 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

키페어 정책 여럿이 있고 슈퍼관리자가 특정 사용자의 키페어를 필터로 검색하면, 그 사용자의 키페어에 할당된 정책만 반환된다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies — user-1이 자기 키페어 필터로 검색

Then

- 호출자의 키페어에 할당된 키페어 정책 하나만 반환된다
  - items = ['keypair-policy-1']
  - total_count = 1

#### [filtering-keypair-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

이름이 다른 키페어 정책 여럿이 있고 슈퍼관리자가 그중 한 이름을 필터로 검색하면, 그 이름의 정책만 반환된다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies — user-1이 wanted-1 이름 필터로 검색

Then

- 필터에 맞는 키페어 정책 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1

#### [the-superadmin-finds-every-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

키페어 정책 여럿이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 미리 만들어 둔 정책이 모두, 그리고 그것만 반환된다

Given

- 키페어 정책 3개와, 그중 하나가 할당된 superadmin 한 명
  - 도메인 home-1
  - 정책이 할당된 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 wanted-1: 동시 세션 5개까지
  - 키페어 정책 other-1: 동시 세션 5개까지

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies — user-1이 필터 없이 전체 검색

Then

- 미리 만들어 둔 키페어 정책이 모두, 그리고 그것만 반환된다
  - items = ['keypair-policy-1', 'other-1', 'wanted-1']
  - total_count = 3

