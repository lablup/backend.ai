## resource_group

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_group/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_group/adapter.py)

Not exercised by any scenario: batch_load_fields.

### allowing

#### [a-user-granted-nothing-may-not-allow-a-domain-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

아무 권한도 없는 사용자가 그룹의 허용 도메인에 도메인을 더하려 하면 권한 부족으로 거부된다. 관계를 쓰는 자리가 양쪽 스코프의 권한을 검사한다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group — user-1이 other-1의 허용 도메인에 home-1 추가

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-allow-a-project-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

아무 권한도 없는 사용자가 그룹의 허용 프로젝트에 프로젝트를 더하려 하면 권한 부족으로 거부된다

Given

- 프로젝트 하나와 리소스 그룹 하나, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_projects_for_resource_group — user-1이 resource-group-1의 허용 프로젝트에 team-1 추가

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-the-domains-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

아무 권한도 없는 사용자가 그룹의 허용 도메인을 읽으려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_domains_for_resource_group — user-1이 resource-group-1의 허용 도메인 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

아무 권한도 없는 사용자가 자기 도메인의 허용 목록을 읽으려 하면 권한 부족으로 거부된다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

아무 권한도 없는 사용자가 프로젝트의 허용 목록을 읽으려 하면 권한 부족으로 거부된다. 자기 도메인, 그 프로젝트, 자기 자신 세 스코프 모두에서 읽을 수 있어야 한다

Given

- 프로젝트 하나와 프로젝트에 건 리소스 그룹 하나, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 프로젝트 team-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_project — user-1이 프로젝트 team-1의 허용 목록 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-the-projects-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

아무 권한도 없는 사용자가 그룹의 허용 프로젝트를 읽으려 하면 권한 부족으로 거부된다

Given

- 프로젝트 하나와 프로젝트에 건 리소스 그룹 하나, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 프로젝트 team-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_projects_for_resource_group — user-1이 resource-group-1의 허용 프로젝트 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-in-the-domain-reads-the-groups-allowed-for-it](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

도메인 범위에서 리소스 그룹 읽기 역할을 받은 사용자가 그 도메인의 허용 목록을 읽으면 건 그룹 이름만 담긴다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 그 도메인 범위의 리소스 그룹 읽기 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 범위의 리소스 그룹 읽기 역할을 받은 사용자 준비
    - 역할 group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-reader-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 group-reader-1 보유

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록 조회

Then

- 허용 목록에 건 리소스 그룹 이름만 담긴다
  - items = ['linked-1']

#### [a-user-granted-read-on-the-group-reads-the-domains-allowed-for-it](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

그 그룹에 앉힌 역할로 읽기 권한을 받은 사용자가 그룹의 허용 도메인을 읽으면 걸린 도메인이 없어 빈 목록이 반환된다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 READ 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.get_allowed_domains_for_resource_group — user-1이 resource-group-1의 허용 도메인 조회

Then

- 허용 목록이 비어 있다
  - items = []

#### [a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

슈퍼관리자가 아닌 사용자가 도메인의 허용 목록에 그룹을 더하려 하면 역할 부족으로 거부된다. 그룹 이름을 id로 바꾸는 자리가 슈퍼관리자 검사를 거친다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록에 other-1 추가

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

슈퍼관리자가 아닌 사용자가 프로젝트의 허용 목록에 그룹을 더하려 하면 역할 부족으로 거부된다

Given

- 프로젝트 하나와 리소스 그룹 하나, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_project — user-1이 프로젝트 team-1의 허용 목록에 resource-group-1 추가

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [allowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

존재하지 않는 도메인 이름을 그룹의 허용 도메인에 더하려 하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group — user-1이 other-1의 허용 도메인에 없는 도메인 이름 추가

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [allowing-a-group-name-nothing-answers-to-for-a-domain-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

존재하지 않는 그룹 이름을 도메인의 허용 목록에 더하려 하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록에 없는 그룹 이름 추가

Then

- 거부된다
  - 거부: ResourceGroupNotFound

#### [disallowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

존재하지 않는 도메인 이름을 그룹의 허용 도메인에서 빼려 하면 건너뛰지 않고 대상을 찾을 수 없다는 이유로 거부된다. 도메인 쪽에서 없는 그룹 이름을 빼는 것은 건너뛴다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group — user-1이 other-1의 허용 도메인에 없는 도메인 이름 제거

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [disallowing-a-group-name-nothing-answers-to-for-a-domain-is-skipped](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

존재하지 않는 그룹 이름을 도메인의 허용 목록에서 빼려 하면 그 이름은 건너뛰고 빈 목록이 반환된다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록에 없는 그룹 이름 제거

Then

- 허용 목록이 비어 있다
  - items = []

#### [reading-the-groups-allowed-for-a-domain-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

존재하지 않는 도메인 이름의 허용 목록을 읽으려 하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain — user-1이 존재하지 않는 도메인의 허용 목록 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-allows-a-domain-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

슈퍼관리자가 그룹의 허용 도메인에 도메인을 더하면 그 도메인 이름이 담긴 목록이 반환된다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group — user-1이 other-1의 허용 도메인에 home-1 추가

Then

- 허용 도메인에 건 도메인 이름만 담긴다
  - items = ['home-1']

#### [the-superadmin-allows-a-project-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

슈퍼관리자가 그룹의 허용 프로젝트에 프로젝트를 더하면 그 프로젝트 id가 담긴 목록이 반환된다

Given

- 프로젝트 하나와 리소스 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_projects_for_resource_group — user-1이 resource-group-1의 허용 프로젝트에 team-1 추가

Then

- 허용 프로젝트에 건 프로젝트 id만 담긴다
  - items: 건 프로젝트와 같다

#### [the-superadmin-allows-a-resource-group-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

슈퍼관리자가 도메인의 허용 목록에 그룹을 더하면 그 그룹 이름이 담긴 목록이 반환된다

Given

- 도메인 하나, 어느 것도 도메인에 걸지 않은 리소스 그룹 둘, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록에 other-1 추가

Then

- 허용 목록에 방금 건 리소스 그룹 이름만 담긴다
  - items = ['other-1']

#### [the-superadmin-allows-a-resource-group-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

슈퍼관리자가 프로젝트의 허용 목록에 그룹을 더하면 그 그룹 이름이 담긴 목록이 반환된다

Given

- 프로젝트 하나와 리소스 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_project — user-1이 프로젝트 team-1의 허용 목록에 resource-group-1 추가

Then

- 허용 목록에 건 리소스 그룹 이름만 담긴다
  - items = ['resource-group-1']

#### [the-superadmin-disallows-a-resource-group-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

도메인에 건 그룹을 슈퍼관리자가 허용 목록에서 빼면 빈 목록이 반환된다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록에 linked-1 제거

Then

- 허용 목록이 비어 있다
  - items = []

#### [the-superadmin-reads-the-domains-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

도메인에 건 그룹의 허용 도메인을 슈퍼관리자가 읽으면 그 도메인 이름이 담긴다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_domains_for_resource_group — user-1이 linked-1의 허용 도메인 조회

Then

- 허용 도메인에 건 도메인 이름만 담긴다
  - items = ['home-1']

#### [the-superadmin-reads-the-groups-allowed-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

도메인에 건 그룹과 걸지 않은 그룹이 있을 때 슈퍼관리자가 도메인의 허용 목록을 읽으면 건 그룹 이름만 담긴다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain — user-1이 도메인 home-1의 허용 목록 조회

Then

- 허용 목록에 건 리소스 그룹 이름만 담긴다
  - items = ['linked-1']

#### [the-superadmin-reads-the-groups-allowed-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

프로젝트에 건 그룹이 있을 때 슈퍼관리자가 프로젝트의 허용 목록을 읽으면 건 그룹 이름이 담긴다

Given

- 프로젝트 하나와 프로젝트에 건 리소스 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 프로젝트 team-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_project — user-1이 프로젝트 team-1의 허용 목록 조회

Then

- 허용 목록에 건 리소스 그룹 이름만 담긴다
  - items = ['resource-group-1']

#### [the-superadmin-reads-the-projects-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py) — pass

프로젝트에 건 그룹의 허용 프로젝트를 슈퍼관리자가 읽으면 그 프로젝트 id가 담긴다

Given

- 프로젝트 하나와 프로젝트에 건 리소스 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 프로젝트 team-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_allowed_projects_for_resource_group — user-1이 resource-group-1의 허용 프로젝트 조회

Then

- 허용 프로젝트에 건 프로젝트 id만 담긴다
  - items: 건 프로젝트와 같다

### creating

#### [a-name-another-resource-group-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py) — pass

이미 어떤 그룹이 쓰고 있는 이름으로 만들려 하면 이름 중복으로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 resource-group-1을 생성

Then

- 거부된다
  - 거부: ResourceGroupConflict

#### [a-resource-group-made-as-the-default-answers-default](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py) — pass

기본 그룹이 없을 때 슈퍼관리자가 기본으로 지정해 만들면 기본인 그룹이 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 primary을 기본 그룹으로 생성

Then

- 만든 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'primary'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = True
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [a-second-default-resource-group-is-refused-as-a-name-conflict](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py) — pass

기본 그룹이 이미 있을 때 다른 이름으로 또 기본 그룹을 만들려 하면 거부된다. 생성 경로는 기본 그룹 제약을 이름 중복과 구분하지 않으므로 이름 중복으로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다, 기본 그룹
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 another-default을 기본 그룹으로 생성

Then

- 거부된다
  - 거부: ResourceGroupConflict

#### [a-user-who-is-not-the-superadmin-may-not-make-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 리소스 그룹을 만들려 하면 역할 부족으로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 by-a-user을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-monitor-may-not-make-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py) — pass

모니터가 리소스 그룹을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다

Given

- 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 by-the-monitor을 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-makes-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py) — pass

슈퍼관리자가 이름만 주고 리소스 그룹을 만들면, 활성이고 공개이며 기본이 아닌 그룹 전체가 코드의 기본값으로 채워져 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 compute을 생성

Then

- 만든 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'compute'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

### editing

#### [a-user-granted-nothing-may-not-edit-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

아무 권한도 없는 사용자가 설명을 바꾸려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 설명을 새것으로 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-edit-the-config](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

아무 권한도 없는 사용자가 설정을 바꾸려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_config — user-1이 resource-group-1의 스케줄러·공개·네트워크 설정을 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-on-the-group-changes-its-description](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 설명을 바꾸면 설명이 새 값인 그룹이 반환된다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 설명을 새것으로 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = 'moved to the second rack'
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [an-edit-naming-no-field-changes-nothing](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 그룹이 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 아무것도 지정하지 않고 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [deactivating-a-resource-group-answers-it-inactive](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

활성 그룹을 비활성으로 바꾸면 비활성인 그룹이 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 활성을 False로 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = False
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [making-a-resource-group-the-default-answers-it-default](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

기본 그룹이 없을 때 그룹을 기본으로 바꾸면 기본인 그룹이 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 기본을 True로 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = True
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [making-a-second-resource-group-the-default-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

기본 그룹이 따로 있을 때 다른 그룹을 기본으로 바꾸려 하면 기본 그룹이 이미 있다는 이유로 거부된다

Given

- 기본 리소스 그룹 하나와 기본이 아닌 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 default-group-1: fifo 스케줄러를 쓴다, 기본 그룹
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 기본을 True로 수정

Then

- 거부된다
  - 거부: DefaultResourceGroupAlreadyExists

#### [the-superadmin-changes-the-preemption-config](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

슈퍼관리자가 선점 설정을 바꾸면 선점 설정이 새 값인 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_config — user-1이 resource-group-1의 선점 설정을 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = True
  - scheduler.preemption.preemptible_priority = 3
  - scheduler.preemption.order = <PreemptionOrder.NEWEST: 'newest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.RESCHEDULE: 'reschedule'>
  - scheduler.preemption.preemption_min_runtime = 60.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.PROJECT: 'project'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [the-superadmin-changes-the-scheduler-visibility-and-network-config](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

슈퍼관리자가 스케줄러를 후입선출로, 비공개로, 호스트 네트워크로, 프록시 주소를 지정해 설정을 바꾸면 그 값들이 새 값인 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_config — user-1이 resource-group-1의 스케줄러·공개·네트워크 설정을 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = False
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = 'https://proxy.example.test'
  - network.use_host_network = True
  - scheduler.type = <SchedulerTypeDTO.LIFO: 'lifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [the-superadmin-changing-the-description-leaves-the-rest](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

슈퍼관리자가 설명만 바꾸면 설명은 새 값이고 나머지는 그대로인 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 resource-group-1을 설명을 새것으로 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = 'moved to the second rack'
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [the-superadmin-editing-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 이름을 수정하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update — user-1이 존재하지 않는 이름을 설명을 새것으로 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

### fair_share

#### [a-user-granted-nothing-may-not-change-the-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

아무 권한도 없는 사용자가 반감기를 바꾸려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_fair_share_spec — user-1이 resource-group-1의 fair share 설정에서 반감기를 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-the-group-may-not-read-its-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

그 그룹에 앉힌 역할로 읽기 권한을 받은 사용자가 fair share 설정을 읽으려 하면 역할 부족으로 거부된다. 설정 조회는 그룹을 전체 검색으로 찾으므로 슈퍼관리자 검사를 먼저 거친다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 READ 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.get_fair_share_spec — user-1이 resource-group-1의 fair share 설정 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-granted-update-on-the-group-changes-its-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 반감기를 바꾸면 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.update_fair_share_spec — user-1이 resource-group-1의 fair share 설정에서 반감기를 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [changing-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

슈퍼관리자가 존재하지 않는 이름의 반감기를 바꾸면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_fair_share_spec — user-1이 존재하지 않는 이름의 fair share 설정에서 반감기를 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [reading-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

슈퍼관리자가 존재하지 않는 이름의 fair share 설정을 읽으면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_fair_share_spec — user-1이 존재하지 않는 이름의 fair share 설정 조회

Then

- 거부된다
  - 거부: ResourceGroupNotFound

#### [the-superadmin-changes-the-fair-share-half-life](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

슈퍼관리자가 반감기를 바꾸면 그룹 전체가 반환된다. 반환되는 노드에는 이 설정이 실리지 않는다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.update_fair_share_spec — user-1이 resource-group-1의 fair share 설정에서 반감기를 수정

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [the-superadmin-reads-the-default-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py) — pass

에이전트가 없는 그룹의 fair share 설정을 슈퍼관리자가 읽으면 코드가 정한 기본값이 반환되고 가중치 목록은 비어 있다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_fair_share_spec — user-1이 resource-group-1의 fair share 설정 조회

Then

- 기본 fair share 설정이 반환되고 가중치 목록은 비어 있다
  - half_life_days = 7
  - lookback_days = 28
  - decay_unit_days = 1
  - default_weight = '1.0'
  - resource_weights = []

### options

#### [a-user-granted-nothing-may-not-replace-the-default-deployment-options](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

아무 권한도 없는 사용자가 기본 배포 옵션을 갈아끼우려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.admin_replace_default_deployment_options — user-1이 resource-group-1의 기본 배포 옵션을 처리기 check-replica-deployments의 설정을 담아 갈아끼움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-replace-the-default-session-options](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

아무 권한도 없는 사용자가 기본 세션 옵션을 갈아끼우려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.admin_replace_default_session_options — user-1이 resource-group-1의 기본 세션 옵션을 우선순위와 처리기 terminate-sessions의 설정을 담아 갈아끼움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-on-the-group-replaces-the-default-deployment-options](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 기본 배포 옵션을 갈아끼우면 준 옵션이 통째로 반환된다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.admin_replace_default_deployment_options — user-1이 resource-group-1의 기본 배포 옵션을 처리기 check-replica-deployments의 설정을 담아 갈아끼움

Then

- 갈아끼운 배포 옵션만 반환된다
  - resource_group_name = 'resource-group-1'
  - default_deployment_options.handler_options.default.timeout_sec = 600
  - default_deployment_options.handler_options.default.max_retry_count = 3
  - default_deployment_options.handler_options.by_handler = [('check-replica-deployments', 60, None)]

#### [naming-an-unregistered-deployment-handler-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

등록되지 않은 배포 처리기 이름을 담아 갈아끼우려 하면 잘못된 입력으로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.admin_replace_default_deployment_options — user-1이 resource-group-1의 기본 배포 옵션을 처리기 no-such-handler의 설정을 담아 갈아끼움

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [naming-an-unregistered-session-handler-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

등록되지 않은 세션 처리기 이름을 담아 갈아끼우려 하면 잘못된 입력으로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.admin_replace_default_session_options — user-1이 resource-group-1의 기본 세션 옵션을 우선순위와 처리기 no-such-handler의 설정을 담아 갈아끼움

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [the-superadmin-replaces-the-default-deployment-options-whole](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

슈퍼관리자가 등록된 처리기 하나의 설정을 담아 기본 배포 옵션을 갈아끼우면 준 옵션이 통째로 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.admin_replace_default_deployment_options — user-1이 resource-group-1의 기본 배포 옵션을 처리기 check-replica-deployments의 설정을 담아 갈아끼움

Then

- 갈아끼운 배포 옵션만 반환된다
  - resource_group_name = 'resource-group-1'
  - default_deployment_options.handler_options.default.timeout_sec = 600
  - default_deployment_options.handler_options.default.max_retry_count = 3
  - default_deployment_options.handler_options.by_handler = [('check-replica-deployments', 60, None)]

#### [the-superadmin-replaces-the-default-session-options-whole](/tests/scenario/bai_scenario/manager/resource_group/test_options.py) — pass

슈퍼관리자가 우선순위와 등록된 처리기 하나의 설정을 담아 기본 세션 옵션을 갈아끼우면 준 옵션이 통째로 반환되고 주지 않은 자리는 코드의 기본값이다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.admin_replace_default_session_options — user-1이 resource-group-1의 기본 세션 옵션을 우선순위와 처리기 terminate-sessions의 설정을 담아 갈아끼움

Then

- 갈아끼운 세션 옵션만 반환된다
  - resource_group_name = 'resource-group-1'
  - default_session_options.priority = 20
  - default_session_options.is_preemptible = True
  - default_session_options.cluster_mode = <ClusterModeEnum.SINGLE_NODE: 'single-node'>
  - default_session_options.default_failure_policy = <FailurePolicyEnum.STRICT: 'strict'>
  - default_session_options.default_kernel_execution_spec = None
  - default_session_options.handler_options.default.timeout_sec = 600
  - default_session_options.handler_options.default.max_retry_count = 3
  - default_session_options.handler_options.by_handler = [('terminate-sessions', 60, None)]
  - default_session_options.agent_selection_policy = <AgentSelectionPolicyEnum.PREFERRED: 'preferred'>

### reading

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다

Given

- 리소스 그룹 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

#### [a-batch-load-of-no-names-answers-an-empty-list](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

빈 이름 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다

Given

- 리소스 그룹 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.batch_load_by_names — user-1이 빈 이름 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

#### [a-user-granted-nothing-batch-loading-by-ids-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

아무 권한도 없는 사용자가 그룹 둘을 id로 한 번에 조회하면, 호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다

Given

- 리소스 그룹 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 2개를 id로 한 번에 조회

Then

- 항목마다 권한 부족 거부가 담긴다
  - len(items) = 2
  - items[0] = 'NotEnoughPermission'
  - items[1] = 'NotEnoughPermission'

#### [a-user-granted-nothing-batch-loading-by-names-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

아무 권한도 없는 사용자가 그룹 둘을 이름으로 한 번에 조회하면, 호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다

Given

- 리소스 그룹 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.batch_load_by_names — user-1이 미리 만들어 둔 2개를 이름으로 한 번에 조회

Then

- 항목마다 권한 부족 거부가 담긴다
  - len(items) = 2
  - items[0] = 'NotEnoughPermission'
  - items[1] = 'NotEnoughPermission'

#### [a-user-granted-nothing-may-not-read-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

아무 권한도 없는 사용자가 이름으로 조회하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get — user-1이 resource-group-1으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-the-resource-info](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

아무 권한도 없는 사용자가 리소스 현황을 조회하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_resource_info — user-1이 resource-group-1의 리소스 현황 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-reading-a-name-nothing-answers-to-is-not-found-too](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 이름으로 조회해도 권한 부족이 아니라 대상을 찾을 수 없다는 이유로 거부된다. 이름으로 id를 찾는 자리는 인증만 확인하고 권한 검사는 찾은 뒤에 온다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get — user-1이 존재하지 않는 이름으로 조회

Then

- 거부된다
  - 거부: ResourceGroupNotFound

#### [a-user-granted-read-on-the-group-reads-it-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

그 그룹에 앉힌 역할로 읽기 권한을 받은 사용자가 이름으로 조회하면 그 그룹 전체가 반환된다. 그룹이 자기 스코프이므로 그룹에 앉힌 역할이 닿는다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 READ 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.get — user-1이 resource-group-1으로 조회

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [a-user-granted-read-on-the-group-reads-its-resource-info](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

그 그룹에 앉힌 역할로 읽기 권한을 받은 사용자가 리소스 현황을 조회하면 슈퍼관리자와 같은 응답을 받는다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 READ 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 READ 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.get_resource_info — user-1이 resource-group-1의 리소스 현황 조회

Then

- 용량·사용량·여유가 모두 비어 있다
  - capacity.entries = []
  - used.entries = []
  - free.entries = []

#### [the-resource-info-of-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

슈퍼관리자가 존재하지 않는 이름의 리소스 현황을 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_resource_info — user-1이 존재하지 않는 이름의 리소스 현황 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-batch-load-by-ids-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

슈퍼관리자가 미리 만들어 둔 그룹 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다

Given

- 리소스 그룹 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 2개와 없는 id 하나를 한 번에 조회

Then

- 요청한 순서대로 반환되고, 없는 것에 해당하는 항목은 비어 있다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].name = 'wanted-1'
  - items[0].status.is_active = True
  - items[0].status.is_public = True
  - items[0].status.is_default = False
  - items[0].metadata.description = None
  - items[0].metadata.created_at: 이 실행이 쓴 시각
  - items[0].network.wsproxy_addr = None
  - items[0].network.use_host_network = False
  - items[0].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[0].scheduler.preemption.enabled = False
  - items[0].scheduler.preemption.preemptible_priority = 5
  - items[0].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[0].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[0].scheduler.preemption.preemption_min_runtime = 0.0
  - items[0].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[0].default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - items[0].default_session_options: 무시함 — 설치본이 정한 기본값이다
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].name = 'other-1'
  - items[1].status.is_active = True
  - items[1].status.is_public = True
  - items[1].status.is_default = False
  - items[1].metadata.description = None
  - items[1].metadata.created_at: 이 실행이 쓴 시각
  - items[1].network.wsproxy_addr = None
  - items[1].network.use_host_network = False
  - items[1].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[1].scheduler.preemption.enabled = False
  - items[1].scheduler.preemption.preemptible_priority = 5
  - items[1].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[1].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[1].scheduler.preemption.preemption_min_runtime = 0.0
  - items[1].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[1].default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - items[1].default_session_options: 무시함 — 설치본이 정한 기본값이다
  - items[2] = None

#### [the-superadmin-batch-load-by-names-leaves-a-missing-name-empty](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

슈퍼관리자가 미리 만들어 둔 그룹 둘과 없는 이름 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 이름에 해당하는 항목은 비어 있다

Given

- 리소스 그룹 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.batch_load_by_names — user-1이 미리 만들어 둔 2개와 없는 이름 하나를 한 번에 조회

Then

- 요청한 순서대로 반환되고, 없는 것에 해당하는 항목은 비어 있다
  - len(items) = 3
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].name = 'wanted-1'
  - items[0].status.is_active = True
  - items[0].status.is_public = True
  - items[0].status.is_default = False
  - items[0].metadata.description = None
  - items[0].metadata.created_at: 이 실행이 쓴 시각
  - items[0].network.wsproxy_addr = None
  - items[0].network.use_host_network = False
  - items[0].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[0].scheduler.preemption.enabled = False
  - items[0].scheduler.preemption.preemptible_priority = 5
  - items[0].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[0].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[0].scheduler.preemption.preemption_min_runtime = 0.0
  - items[0].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[0].default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - items[0].default_session_options: 무시함 — 설치본이 정한 기본값이다
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].name = 'other-1'
  - items[1].status.is_active = True
  - items[1].status.is_public = True
  - items[1].status.is_default = False
  - items[1].metadata.description = None
  - items[1].metadata.created_at: 이 실행이 쓴 시각
  - items[1].network.wsproxy_addr = None
  - items[1].network.use_host_network = False
  - items[1].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[1].scheduler.preemption.enabled = False
  - items[1].scheduler.preemption.preemptible_priority = 5
  - items[1].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[1].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[1].scheduler.preemption.preemption_min_runtime = 0.0
  - items[1].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[1].default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - items[1].default_session_options: 무시함 — 설치본이 정한 기본값이다
  - items[2] = None

#### [the-superadmin-reading-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

슈퍼관리자가 존재하지 않는 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get — user-1이 존재하지 않는 이름으로 조회

Then

- 거부된다
  - 거부: ResourceGroupNotFound

#### [the-superadmin-reads-a-resource-group-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

리소스 그룹 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get — user-1이 resource-group-1으로 조회

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [the-superadmin-reads-an-empty-resource-info-of-a-group-without-agents](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py) — pass

에이전트가 없는 그룹의 리소스 현황을 슈퍼관리자가 조회하면 용량·사용량·여유가 모두 비어 있다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get_resource_info — user-1이 resource-group-1의 리소스 현황 조회

Then

- 용량·사용량·여유가 모두 비어 있다
  - capacity.entries = []
  - used.entries = []
  - free.entries = []

### retiring

#### [a-user-granted-hard-delete-on-the-group-purges-it](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py) — pass

그 그룹에 앉힌 역할로 완전 삭제 권한을 받은 사용자가 완전 삭제하면 지운 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 그 그룹 범위의 HARD_DELETE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 HARD_DELETE 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- ResourceGroupAdapter.purge — user-1이 resource-group-1 완전 삭제

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [a-user-granted-nothing-may-not-purge-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py) — pass

아무 권한도 없는 사용자가 완전 삭제하려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.purge — user-1이 resource-group-1 완전 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-superadmin-purges-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py) — pass

리소스 그룹 하나가 있고 슈퍼관리자가 완전 삭제하면 지운 그룹 전체가 반환된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.purge — user-1이 resource-group-1 완전 삭제

Then

- 미리 만들어 둔 리소스 그룹 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: 이 실행이 쓴 시각
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다

#### [the-superadmin-purging-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py) — pass

슈퍼관리자가 존재하지 않는 이름을 완전 삭제하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- 리소스 그룹 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.purge — user-1이 존재하지 않는 이름 완전 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

### searching

#### [a-name-filter-narrows-the-answer-to-that-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

리소스 그룹 둘 중 한쪽 이름을 필터로 조회하면 그 그룹 하나만 반환된다

Given

- 리소스 그룹 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.search — user-1이 이름 wanted-1 필터로 조회

Then

- 필터에 맞는 리소스 그룹 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-may-not-search-a-domain-scope](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

아무 권한도 없는 사용자가 자기 도메인 스코프로 조회하면 권한 부족으로 거부된다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.scoped_search — user-1이 도메인 home-1 스코프로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-in-the-domain-searches-the-groups-linked-to-it](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

도메인 범위에서 리소스 그룹 읽기 역할을 받은 사용자가 그 도메인 스코프로 조회하면, 도메인에 건 그룹 하나만 반환되고 걸지 않은 그룹은 나오지 않는다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 그 도메인 범위의 리소스 그룹 읽기 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 범위의 리소스 그룹 읽기 역할을 받은 사용자 준비
    - 역할 group-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-reader-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-1: 역할 group-reader-1 보유

When

- ResourceGroupAdapter.scoped_search — user-1이 도메인 home-1 스코프로 조회

Then

- 도메인에 건 리소스 그룹 하나만 반환된다
  - items = ['linked-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-every-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 필터 없이 전체를 조회하면 역할 부족으로 거부된다

Given

- 리소스 그룹 둘과, 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-active-filter-leaves-only-the-active-resource-groups](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

활성 그룹과 비활성 그룹이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다

Given

- 활성 리소스 그룹 하나와 비활성 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 active-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 inactive-1: fifo 스케줄러를 쓴다, 비활성
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.search — user-1이 활성 필터로 조회

Then

- 응답에 나와야 하는 리소스 그룹만 반환된다
  - items = ['active-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [asking-for-the-first-resource-group-only-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

리소스 그룹 둘이 있을 때 앞에서 한 건만 요청하면 한 건이 반환되고 다음 페이지가 있다고 응답한다

Given

- 리소스 그룹 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.search — user-1이 앞에서 한 건만 조회

Then

- 한 건짜리 첫 페이지가 반환된다
  - len(items) = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

#### [the-monitor-searches-resource-groups-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다

Given

- 리소스 그룹 둘과, 모니터 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.search — user-1이 필터 없이 전체 조회

Then

- 응답에 나와야 하는 리소스 그룹만 반환된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-counts-every-resource-group-laid](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

리소스 그룹 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다

Given

- 리소스 그룹 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 wanted-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.search — user-1이 필터 없이 전체 조회

Then

- 응답에 나와야 하는 리소스 그룹만 반환된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-searching-a-domain-scope-sees-only-the-groups-linked-to-it](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py) — pass

슈퍼관리자가 도메인 스코프로 조회해도 그 도메인에 건 그룹 하나만 반환된다

Given

- 도메인 하나, 도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 linked-1: fifo 스케줄러를 쓴다
  - 리소스 그룹 other-1: fifo 스케줄러를 쓴다
  - 도메인 home-1 의 세션이 쓸 수 있는 리소스 그룹 linked-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.scoped_search — user-1이 도메인 home-1 스코프로 조회

Then

- 도메인에 건 리소스 그룹 하나만 반환된다
  - items = ['linked-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

