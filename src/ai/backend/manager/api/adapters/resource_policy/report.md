## resource_policy

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_policy/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_policy/adapter.py)

Not exercised by any scenario: admin_create_keypair_resource_policy, admin_create_user_resource_policy, admin_delete_keypair_resource_policy, admin_delete_user_resource_policy, admin_get_keypair_resource_policy, admin_get_user_resource_policy, admin_search_keypair_resource_policies, admin_search_user_resource_policies, admin_update_keypair_resource_policy, admin_update_user_resource_policy, batch_load_fields, get_my_keypair_resource_policy, get_my_user_resource_policy.

### creating

#### [a-monitor-may-not-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

모니터 역할 사용자가 프로젝트 정책을 만들려 하면 역할로 막힌다. 역할 문은 모니터에게 읽기만 열어 준다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, monitor 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy — user-1이 모든 값을 주고 프로젝트 정책을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-name-another-project-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

이미 어떤 프로젝트 정책이 쓰고 있는 이름으로 만들려 하면, 이름이 겹친다는 이유로 거부된다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy — user-1이 이미 있는 이름으로 프로젝트 정책을 만듦

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [a-user-who-is-not-the-superadmin-may-not-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 프로젝트 정책을 만들려 하면, 권한을 얼마나 받았는지와 무관하게 역할로 막힌다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy — user-1이 모든 값을 주고 프로젝트 정책을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-creates-a-project-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

슈퍼관리자가 모든 값을 주고 프로젝트 정책을 만들면, 준 값이 그대로 실린 노드 전체가 답으로 온다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy — user-1이 모든 값을 주고 프로젝트 정책을 만듦

Then

- 만든 프로젝트 정책 전체가 온다
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_quota_scope_size = ('1073741824', '1g')
  - max_network_count = 5

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py) — pass

엔티티 권한 집행을 꺼도 프로젝트 정책 만들기는 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_create_project_resource_policy — user-1이 모든 값을 주고 프로젝트 정책을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-granted-nothing-may-not-edit-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

같은 프로젝트 정책이 있고 아무 권한도 받지 않은 사용자가 고치려 하면, 고치기 문에 닿기 전에 이름을 해석할 수 없다는 이유로 거부된다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_update_project_resource_policy — user-1이 project-policy-1을 폴더 수를 20으로 수정

Then

- 거부된다
  - 거부: GenericBadRequest

#### [clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 프로젝트 정책의 비울 수 없는 항목을 비우도록 고치면, 그 요청은 없던 것으로 읽혀 아무것도 바뀌지 않은 노드가 답으로 온다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_update_project_resource_policy — user-1이 project-policy-1을 폴더 수를 비우도록 수정

Then

- 심은 프로젝트 정책 전체가 온다
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

#### [editing-a-project-policy-name-nothing-answers-to-is-unresolvable](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 어느 프로젝트 정책도 갖지 않은 이름을 고치려 하면, 이름을 해석할 수 없다는 이유로 거부된다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_update_project_resource_policy — user-1이 nobody을 폴더 수를 20으로 수정

Then

- 거부된다
  - 거부: GenericBadRequest

#### [giving-no-value-changes-nothing-of-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

슈퍼관리자가 프로젝트 정책을 지목만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 노드가 답으로 온다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_update_project_resource_policy — user-1이 project-policy-1을 아무것도 대지 않고 수정

Then

- 심은 프로젝트 정책 전체가 온다
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

#### [the-superadmin-changes-one-limit-of-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py) — pass

프로젝트 정책 하나가 있고 슈퍼관리자가 한도 하나만 고치면, 그 한도는 새 값이 되고 나머지는 그대로다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_update_project_resource_policy — user-1이 project-policy-1을 폴더 수를 20으로 수정

Then

- 심은 프로젝트 정책 전체가 온다
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 20
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

### reading

#### [a-project-policy-name-nothing-answers-to-is-unresolvable-even-for-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

슈퍼관리자가 어느 프로젝트 정책도 갖지 않은 이름으로 조회하면, 대상이 없다는 것이 아니라 이름을 해석할 수 없다는 이유로 거부된다. 그 이름이 있는지를 거부가 말하지 않는다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy — user-1이 nobody으로 조회

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-cannot-resolve-a-project-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

같은 프로젝트 정책이 있고 아무 권한도 받지 않은 사용자가 이름으로 조회하면, 이름을 해석할 수 없다는 이유로 거부된다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy — user-1이 project-policy-1으로 조회

Then

- 거부된다
  - 거부: GenericBadRequest

#### [the-superadmin-reads-a-project-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

프로젝트 정책 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 정책 전체가 답으로 온다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy — user-1이 project-policy-1으로 조회

Then

- 심은 프로젝트 정책 전체가 온다
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 프로젝트 정책을 이름으로 읽을 수 있다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_get_project_resource_policy — user-1이 project-policy-1으로 조회

Then

- 심은 프로젝트 정책 전체가 온다
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: 이 실행이 쓴 시각
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

### retiring

#### [a-user-granted-nothing-may-not-purge-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

같은 프로젝트 정책이 있고 아무 권한도 받지 않은 사용자가 지우려 하면, 지우기 문에 닿기 전에 이름을 해석할 수 없다는 이유로 거부된다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_delete_project_resource_policy — user-1이 project-policy-1을 지우고 다시 검색

Then

- 거부된다
  - 거부: GenericBadRequest

#### [purging-a-project-policy-name-nothing-answers-to-is-unresolvable](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

슈퍼관리자가 어느 프로젝트 정책도 갖지 않은 이름을 지우려 하면, 이름을 해석할 수 없다는 이유로 거부된다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_delete_project_resource_policy — user-1이 nobody을 지우고 다시 검색

Then

- 거부된다
  - 거부: GenericBadRequest

#### [purging-a-project-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

누군가 아직 매여 있는 프로젝트 정책을 슈퍼관리자가 지우려 하면, 아직 참조된다는 이유로 거부된다. 막는 것은 지우기 spec이 아니라 외래 키다

Given

- superadmin 한 명과, 그 사람이 아직 매여 있는 프로젝트 정책
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourcePolicyAdapter.admin_delete_project_resource_policy — user-1이 default을 지우고 다시 검색

Then

- 거부된다
  - 거부: ForeignKeyViolationError

#### [the-superadmin-purges-a-project-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py) — pass

아무도 쓰지 않는 프로젝트 정책을 슈퍼관리자가 지우면, 지운 이름이 답으로 오고 이어서 검색하면 없다

Given

- 아무도 쓰지 않는 프로젝트 정책 하나와, superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 project-policy-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_delete_project_resource_policy — user-1이 project-policy-1을 지우고 다시 검색

Then

- 지운 이름이 답으로 오고 다시 검색하면 없다
  - name = 'project-policy-1'
  - found afterwards = 0

### searching

#### [a-monitor-finds-every-project-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

모니터 역할 사용자가 프로젝트 정책 전체를 검색하면 슈퍼관리자와 같은 답이 온다. 역할 문이 읽기는 모니터에게도 열어 주기 때문이다

Given

- 프로젝트 정책 3개와, 그중 하나에 매인 monitor 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 wanted-1: 프로젝트 하나당 폴더 10개까지
  - 프로젝트 정책 other-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies — user-1이 필터 없이 전체 검색

Then

- 심은 프로젝트 정책이 모두, 그리고 그것만 온다
  - items = ['default', 'other-1', 'wanted-1']
  - total_count = 3

#### [a-user-who-is-not-the-superadmin-may-not-search-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 프로젝트 정책 전체를 검색하려 하면 역할로 막힌다

Given

- 프로젝트 정책 3개와, 그중 하나에 매인 user 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 wanted-1: 프로젝트 하나당 폴더 10개까지
  - 프로젝트 정책 other-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies — user-1이 필터 없이 전체 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-project-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

이름이 다른 프로젝트 정책 여럿이 있고 슈퍼관리자가 그중 한 이름으로 걸러 검색하면, 그 이름의 것만 온다

Given

- 프로젝트 정책 3개와, 그중 하나에 매인 superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 wanted-1: 프로젝트 하나당 폴더 10개까지
  - 프로젝트 정책 other-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies — user-1이 wanted-1으로 걸러 검색

Then

- 걸러낸 프로젝트 정책 하나만 온다
  - items = ['wanted-1']
  - total_count = 1

#### [the-superadmin-finds-every-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py) — pass

프로젝트 정책 여럿이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 심은 것이 모두, 그리고 그것만 온다

Given

- 프로젝트 정책 3개와, 그중 하나에 매인 superadmin 한 명
  - 도메인 home-1
  - 정책에 매인 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 정책 wanted-1: 프로젝트 하나당 폴더 10개까지
  - 프로젝트 정책 other-1: 프로젝트 하나당 폴더 10개까지

When

- ResourcePolicyAdapter.admin_search_project_resource_policies — user-1이 필터 없이 전체 검색

Then

- 심은 프로젝트 정책이 모두, 그리고 그것만 온다
  - items = ['default', 'other-1', 'wanted-1']
  - total_count = 3

