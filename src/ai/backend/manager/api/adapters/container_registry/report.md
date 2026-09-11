## container_registry

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/container_registry/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/container_registry/adapter.py)

Not exercised by any scenario: batch_load_fields.

### allowing_projects

#### [a-superadmin-naming-a-project-that-does-not-exist-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

존재하지 않는 프로젝트를 허용 목록에 넣으려 하면 그 프로젝트가 없다는 이유로 거부된다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 슈퍼관리자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-project-1: container_registry 전체에 SOFT_DELETE 허용
    - 슈퍼관리자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 없는 프로젝트를 허용 목록에 넣음

Then

- 거부된다
  - 거부: ProjectNotFound

#### [a-superadmin-removing-a-project-that-was-never-allowed-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

지목한 프로젝트 중 실제로 허용된 것이 하나도 없으면, 뺄 것이 없다는 이유로 거부된다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 슈퍼관리자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-project-1: container_registry 전체에 SOFT_DELETE 허용
    - 슈퍼관리자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에서 뺌

Then

- 거부된다
  - 거부: ContainerRegistryGroupsAssociationNotFound

#### [a-user-granted-on-both-scopes-allows-a-project-on-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

레지스트리와 프로젝트 두 스코프 모두에 권한을 받은 사용자는 그 프로젝트를 허용 목록에 넣을 수 있다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-project-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 답이 없고 예외도 없다
  - 거부: NotEnoughPermission

#### [a-user-granted-on-the-registry-but-not-the-project-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

레지스트리에만 권한을 받고 프로젝트에는 받지 못한 사용자가 프로젝트를 허용하려 하면, 관계 동작은 지목한 스코프를 모두 보므로 권한 부족으로 막힌다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [allowing-a-project-that-is-already-allowed-is-not-an-error](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

이미 허용된 프로젝트를 다시 허용 목록에 넣어도 거부되지 않는다. 그 쌍은 데이터베이스에서 건너뛴다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 가 이미지를 볼 수 있는 컨테이너 레지스트리 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-project-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 답이 없고 예외도 없다
  - 거부: NotEnoughPermission

#### [an-allowed-project-is-removed-from-the-allowed-list](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

이미 허용된 프로젝트는 허용 목록에서 뺄 수 있다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 가 이미지를 볼 수 있는 컨테이너 레지스트리 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: container_registry 전체에 CREATE 허용
    - 역할 allow-on-project-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에서 뺌

Then

- 답이 없고 예외도 없다
  - 거부: NotEnoughPermission

#### [turning-enforcement-off-lets-an-ungranted-user-allow-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 프로젝트를 허용할 수 있다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 레지스트리 하나, 프로젝트 하나, 아무 권한도 없음인 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 답이 없고 예외도 없다
  - response = None

### creating

#### [a-project-named-while-creating-is-allowed-on-the-new-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

슈퍼관리자는 허용 프로젝트를 함께 주고 레지스트리를 만들 수 있다. 허용 목록이 함께 쓰이는 것은 답에 실리지 않아 이 행이 보지 못한다

Given

- 레지스트리 없음, 프로젝트 하나, 도메인 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_create — user-1이 심은 프로젝트를 허용 목록에 넣고 https://made.scenario.local로 만듦

Then

- 만든 레지스트리 전체가 온다
  - url = 'https://made.scenario.local'
  - registry_name = 'made-registry'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: 무시함 — 데이터베이스가 만든다

#### [a-project-that-does-not-exist-is-refused-while-creating](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

허용 목록에 없는 프로젝트를 넣고 레지스트리를 만들려 하면, 그 프로젝트가 없다는 이유로 거부된다

Given

- 레지스트리 없음, 프로젝트 하나, 도메인 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_create — user-1이 없는 프로젝트를 허용 목록에 넣고 https://made.scenario.local로 만듦

Then

- 거부된다
  - 거부: ProjectNotFound

#### [a-user-who-is-not-the-superadmin-may-not-create-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 만들려 하면 권한 부족으로 거부된다. 이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다

Given

- 레지스트리 없음, 프로젝트 하나, 도메인 하나에 속한 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_create — user-1이 허용 목록 없이 https://made.scenario.local로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [creating-a-registry-with-only-the-required-values-leaves-the-rest-empty](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

슈퍼관리자가 주소와 이름과 종류만 주고 레지스트리를 만들면, 나머지 자리가 모두 비어 있는 노드가 답으로 온다

Given

- 레지스트리 없음, 프로젝트 하나, 도메인 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_create — user-1이 허용 목록 없이 https://made.scenario.local로 만듦

Then

- 만든 레지스트리 전체가 온다
  - url = 'https://made.scenario.local'
  - registry_name = 'made-registry'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: 무시함 — 데이터베이스가 만든다

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아닌 사용자는 여전히 권한 부족으로 거부된다. 집행 스위치는 권한 그래프만 끄고, 부른 사람이 슈퍼관리자인지 보는 검사는 그대로 남기 때문이다

Given

- 레지스트리 없음, 프로젝트 하나, 도메인 하나에 속한 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_create — user-1이 허용 목록 없이 https://made.scenario.local로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-who-is-not-the-superadmin-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 고치려 하면 권한 부족으로 거부된다. 이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다

Given

- 레지스트리 하나, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 주소를 https://moved.scenario.local로 고침

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-address-whose-host-is-empty-is-refused-on-update](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 호스트 자리가 비는 주소로 고치려 하면, 고친 뒤의 행을 보는 검사가 주소 형식으로 막는다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 주소를 http://로 고침

Then

- 거부된다
  - 거부: InvalidContainerRegistryURL

#### [an-edit-that-names-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 아무 값도 주지 않고 고침

Then

- 심은 레지스트리 전체가 온다
  - url = 'https://host-1.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: 무시함 — 데이터베이스가 만든다

#### [changing-only-the-address-leaves-every-other-field-alone](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 주소만 고치면 주소만 새 값이 되고 나머지 자리는 그대로다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 주소를 https://moved.scenario.local로 고침

Then

- 심은 레지스트리 전체가 온다
  - url = 'https://moved.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: 무시함 — 데이터베이스가 만든다

#### [editing-an-id-that-holds-no-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

아무 레지스트리도 갖지 않은 id를 고치려 하면 대상이 없다는 이유로 거부된다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 아무것도 갖지 않은 id를 고침

Then

- 거부된다
  - 거부: ContainerRegistryNotFound

#### [turning-a-registry-into-harbor-without-a-project-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

프로젝트가 비어 있는 레지스트리를 harbor 종류로 고치려 하면, harbor는 프로젝트를 요구하므로 그 값으로 막힌다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 종류를 harbor2로 고침

Then

- 거부된다
  - 거부: InvalidContainerRegistryProject

### reading

#### [a-plain-user-loading-many-ids-is-refused-as-a-whole](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py) — pass

슈퍼관리자가 아닌 사용자가 id 여럿을 한 번에 읽으려 하면, 원소별로 갈리지 않고 요청 전체가 권한 부족으로 거부된다. 이 호출은 id를 보기 전에 부른 사람이 슈퍼관리자인지부터 본다

Given

- 레지스트리 2개, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.batch_load_by_ids — user-1이 심은 것 둘과 없는 id 하나를 한 번에 읽음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-empty-id-list-answers-empty-without-calling-the-wiring](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py) — pass

빈 id 목록으로 읽으면 배선을 부르지 않고 빈 답이 온다

Given

- 레지스트리 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 읽음

Then

- 빈 답이 온다
  - items = []

#### [loading-many-ids-keeps-the-order-and-leaves-a-hole-for-a-missing-one](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py) — pass

슈퍼관리자가 심은 레지스트리 둘과 아무것도 갖지 않은 id 하나를 한 번에 읽으면, 준 순서 그대로 오고 없는 id 자리만 비어서 온다

Given

- 레지스트리 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.batch_load_by_ids — user-1이 심은 것 둘과 없는 id 하나를 한 번에 읽음

Then

- 준 순서 그대로 오고 없는 id 자리는 비어 있다
  - length = 3
  - names = ['wanted-1', None, 'other-1']

### retiring

#### [a-user-who-is-not-the-superadmin-may-not-delete-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 지우려 하면 권한 부족으로 거부된다. 이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다

Given

- 레지스트리 하나, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_delete — user-1이 심은 레지스트리를 지움

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [deleting-a-registry-answers-with-the-id-it-removed](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

슈퍼관리자가 레지스트리를 지우면 지운 id가 답으로 온다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_delete — user-1이 심은 레지스트리를 지움

Then

- 지운 id가 답으로 온다
  - id: 심은 레지스트리의 id와 같다

#### [deleting-a-registry-takes-its-allowed-projects-with-it](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

허용 프로젝트가 딸린 레지스트리를 지우면, 외래 키를 통해 그 허용 목록까지 함께 사라진다

Given

- 레지스트리 하나, superadmin 한 명, 프로젝트 하나가 이미 허용돼 있음
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 프로젝트 project-1 가 이미지를 볼 수 있는 컨테이너 레지스트리 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_delete — user-1이 심은 레지스트리를 지움

Then

- 지운 id가 답으로 온다
  - id: 심은 레지스트리의 id와 같다

#### [deleting-an-id-that-holds-no-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

아무 레지스트리도 갖지 않은 id를 지우려 하면 대상이 없다는 이유로 거부된다

Given

- 레지스트리 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_delete — user-1이 아무것도 갖지 않은 id를 지움

Then

- 거부된다
  - 거부: ContainerRegistryNotFound

### searching

#### [a-user-who-is-not-the-superadmin-may-not-search-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 검색하려 하면 권한 부족으로 거부된다. 이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다

Given

- 레지스트리 2개, user 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 조건 없이 검색함

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-by-name-leaves-only-the-registry-that-holds-it](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 이름으로 걸러 검색하면 그 이름을 가진 레지스트리만 남는다

Given

- 레지스트리 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 wanted-1 이름으로 걸러 검색함

Then

- 걸러낸 그 레지스트리 하나만 남는다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-with-ten-and-says-there-is-more](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 페이지 크기를 생략하고 검색하면, 열 건까지만 오고 다음 쪽이 있다고 답한다

Given

- 레지스트리 11개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-2: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-3: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-4: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-5: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-6: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-7: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-8: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-9: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-10: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 크기를 생략하고 검색함

Then

- 한 쪽만 오고 다음 쪽이 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [searching-without-a-filter-counts-every-registry](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 조건 없이 검색하면 심어둔 레지스트리가 모두 답으로 온다

Given

- 레지스트리 2개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 조건 없이 검색함

Then

- 심은 레지스트리가 모두 세어진다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

