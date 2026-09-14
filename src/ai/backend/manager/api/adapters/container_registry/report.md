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
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
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
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
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
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 답이 없고 예외도 없다
  - response = None

#### [a-user-granted-on-the-project-but-not-the-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

프로젝트에만 권한을 받고 레지스트리에는 받지 못한 사용자가 프로젝트를 허용하려 하면, 관계 동작은 지목한 스코프를 모두 보므로 권한 부족으로 막힌다

Given

- 레지스트리 하나, 프로젝트 하나, 프로젝트에 권한 있음인 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 거부된다
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
  - 프로젝트 project-1 이 허용된 컨테이너 레지스트리 host-1
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
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 답이 없고 예외도 없다
  - response = None

#### [an-allowed-project-is-removed-from-the-allowed-list](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

이미 허용된 프로젝트는 허용 목록에서 뺄 수 있다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 이 허용된 컨테이너 레지스트리 host-1
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
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에서 뺌

Then

- 답이 없고 예외도 없다
  - response = None

#### [create-permission-does-not-allow-removing-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

양쪽 스코프에 생성 권한만 받은 사용자가 프로젝트를 제거하면 권한 부족으로 거부된다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 이 허용된 컨테이너 레지스트리 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에서 뺌

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [create-permission-on-both-scopes-is-enough-to-allow-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

양쪽 스코프에 생성 권한만 받은 사용자는 프로젝트를 허용 목록에 넣을 수 있다

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
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: project 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 답이 없고 예외도 없다
  - response = None

#### [soft-delete-permission-does-not-allow-adding-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

양쪽 스코프에 삭제 권한만 받은 사용자가 프로젝트를 추가하면 권한 부족으로 거부된다

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
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에 넣음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [soft-delete-permission-on-both-scopes-is-enough-to-remove-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

양쪽 스코프에 삭제 권한만 받은 사용자는 허용 프로젝트를 제거할 수 있다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 이 허용된 컨테이너 레지스트리 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - allow-on-registry 권한을 받은 사용자 준비
    - 역할 allow-on-registry-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-registry-1: container_registry 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-registry-1 보유
  - allow-on-project 권한을 받은 사용자 준비
    - 역할 allow-on-project-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 allow-on-project-1: project 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 allow-on-project-1 보유

When

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 허용 목록에서 뺌

Then

- 답이 없고 예외도 없다
  - response = None

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

슈퍼관리자가 허용 프로젝트를 함께 주고 레지스트리를 만들면 그 관계도 생성된다

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

#### [editing-a-registry-can-add-an-allowed-project](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 레지스트리를 고치며 프로젝트를 허용하면 그 관계가 생성된다

Given

- 레지스트리 하나, 프로젝트 하나, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_update — user-1이 심은 프로젝트를 허용 목록에 넣으며 고침

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

- 레지스트리 하나, 프로젝트 하나가 이미 허용돼 있음, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 프로젝트 project-1 이 허용된 컨테이너 레지스트리 host-1
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

#### [a-backward-cursor-selects-the-previous-page](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

마지막 레지스트리 앞의 커서로 한 건을 요청하면 이전 레지스트리와 양쪽 페이지 표시가 온다

Given

- 레지스트리 3개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-2: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 마지막 레지스트리 앞을 커서로 검색함

Then

- 커서 이전 레지스트리와 양쪽 페이지 표시가 온다
  - items = [(ContainerRegistryID('546f4f2d-1577-4bb1-8297-1c98ea25c355'), 'https://other-2.scenario.local', 'other-2', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None)]
  - total_count = 3
  - has_next_page = True
  - has_previous_page = True

#### [a-forward-cursor-selects-the-next-page](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

첫 레지스트리 뒤의 커서로 한 건을 요청하면 다음 레지스트리와 양쪽 페이지 표시가 온다

Given

- 레지스트리 3개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-2: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 첫 레지스트리 뒤를 커서로 검색함

Then

- 커서 다음 레지스트리와 양쪽 페이지 표시가 온다
  - items = [(ContainerRegistryID('2f8bb995-e63a-47bb-b4bf-e187ed1c2b12'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 3
  - has_next_page = True
  - has_previous_page = True

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

#### [and-combines-container-registry-filters](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

AND로 종류와 전역 여부를 묶으면 두 조건을 모두 만족하는 레지스트리만 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 and 조건으로 걸러 검색함

Then

- 걸러낸 그 레지스트리 하나만 남는다
  - items = [(ContainerRegistryID('2b7f179b-d546-405c-af93-a9a59742db1b'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-global-visibility-leaves-only-non-global-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 전역 여부로 걸러 검색하면 전역이 아닌 레지스트리만 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 non-global 조건으로 걸러 검색함

Then

- 전역이 아닌 레지스트리만 온다
  - items = [(ContainerRegistryID('5fb5a50c-8204-4a37-b70b-09a26f8752d7'), 'https://other-1.scenario.local', 'other-1', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None)]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

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
  - items = [(ContainerRegistryID('86f5a24e-9493-44e6-ad05-fddb0c9332ac'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-type-leaves-only-matching-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 종류로 걸러 검색하면 그 종류를 가진 레지스트리만 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 type 조건으로 걸러 검색함

Then

- 걸러낸 그 레지스트리 하나만 남는다
  - items = [(ContainerRegistryID('703d5f93-6449-4b69-a9c6-6a71bc928a1a'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [mixing-cursor-and-offset-pagination-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

커서와 오프셋 페이지네이션을 한 요청에 함께 지정하면 잘못된 인자로 거부된다

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

- 거부된다
  - 거부: InvalidGraphQLParameters

#### [not-negates-a-container-registry-filter](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

NOT으로 전역이 아닌 조건을 뒤집으면 전역 레지스트리만 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 not 조건으로 걸러 검색함

Then

- 걸러낸 그 레지스트리 하나만 남는다
  - items = [(ContainerRegistryID('f3a380c7-2e93-4541-9925-9014fb333b5e'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [offset-pagination-selects-a-middle-page](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

이름순 검색에서 한 건을 건너뛰면 가운데 레지스트리와 양쪽 페이지 표시가 온다

Given

- 레지스트리 3개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-2: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 이름순으로 1건을 건너뛰고 검색함

Then

- 건너뛴 위치의 한 쪽이 온다
  - items = [(ContainerRegistryID('59fa625f-328c-4057-b7c4-1650f00e86ba'), 'https://other-2.scenario.local', 'other-2', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None)]
  - total_count = 3
  - has_next_page = True
  - has_previous_page = True

#### [offset-past-the-end-returns-an-empty-page](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

전체 개수만큼 건너뛰면 빈 목록과 이전 페이지 표시가 온다

Given

- 레지스트리 3개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-2: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 이름순으로 3건을 건너뛰고 검색함

Then

- 건너뛴 위치의 한 쪽이 온다
  - items = []
  - total_count = 3
  - has_next_page = False
  - has_previous_page = True

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
  - items = [(ContainerRegistryID('dd90a01a-2a7e-4c31-86d0-41787e5144b2'), 'https://other-4.scenario.local', 'other-4', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('cbd3f454-5bdd-44be-bb69-a13df2feea3f'), 'https://other-9.scenario.local', 'other-9', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('c2740d50-eabb-4df1-8845-c7282b37458f'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None), (ContainerRegistryID('94efd8b8-20a3-4b5d-8388-3069a335c318'), 'https://other-10.scenario.local', 'other-10', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('827792f3-cdc5-48e9-9a0d-12017d39e75f'), 'https://other-6.scenario.local', 'other-6', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('4da73fa5-3739-4d9c-800d-a28bcdfda04d'), 'https://other-8.scenario.local', 'other-8', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('4812d017-b4e3-4c07-9990-36f0e31829bb'), 'https://other-3.scenario.local', 'other-3', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('42334961-9555-40d2-928e-1a8d7bd3a999'), 'https://other-5.scenario.local', 'other-5', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('355657e6-8171-42a2-b5b9-8a8b6d90f620'), 'https://other-2.scenario.local', 'other-2', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('16ec59d5-ad22-4fe8-b644-ca6dd83085bb'), 'https://other-1.scenario.local', 'other-1', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None)]
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [or-combines-container-registry-filters](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

OR로 종류와 전역 여부를 묶으면 어느 한 조건을 만족하는 레지스트리가 모두 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 or 조건으로 걸러 검색함

Then

- 심은 레지스트리가 모두 세어진다
  - items = [(ContainerRegistryID('111c595f-a255-4624-a113-69207e8712c6'), 'https://other-1.scenario.local', 'other-1', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('cc5570f7-2cba-41c3-b420-1eababc8b516'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [ordering-by-name-returns-registries-in-the-requested-direction](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 이름 오름차순을 요청하면 레지스트리가 그 순서로 온다

Given

- 레지스트리 3개, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 wanted-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-1: 이미지를 가져오는 곳
  - 컨테이너 레지스트리 other-2: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_search — user-1이 이름을 ASC 순서로 검색함

Then

- 요청한 이름 순서로 온다
  - items = [(ContainerRegistryID('b73cfd4e-1b7e-4452-8ef4-c89ddf8be9b7'), 'https://other-1.scenario.local', 'other-1', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('b13442c0-5a9a-45d7-97ad-a0ac3c77aa0a'), 'https://other-2.scenario.local', 'other-2', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None), (ContainerRegistryID('7e84acd6-0778-4c80-9b28-a3bc712e8787'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None)]
  - total_count = 3
  - has_next_page = False
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
  - items = [(ContainerRegistryID('4237b28f-ca5f-4aa2-bdbe-b8f33b060ed3'), 'https://wanted-1.scenario.local', 'wanted-1', <ContainerRegistryType.DOCKER: 'docker'>, None, None, True, True, None), (ContainerRegistryID('5f92db0e-61f1-44ed-b4c3-d141e303e613'), 'https://other-1.scenario.local', 'other-1', <ContainerRegistryType.HARBOR2: 'harbor2'>, None, None, True, False, None)]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

