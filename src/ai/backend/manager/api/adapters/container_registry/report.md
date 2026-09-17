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

- ContainerRegistryAdapter.apply_allowed_groups — user-1이 존재하지 않는 프로젝트를 허용 목록에 넣음

Then

- 거부된다
  - 거부: ProjectNotFound

#### [a-superadmin-removing-a-project-that-was-never-allowed-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

지정한 프로젝트 중 실제로 허용된 것이 하나도 없으면, 제거할 관계가 없다는 이유로 거부된다

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

- 반환값이 없고 예외도 발생하지 않는다
  - response = None

#### [a-user-granted-on-the-project-but-not-the-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

프로젝트에만 권한을 받고 레지스트리에는 받지 못한 사용자가 프로젝트를 허용하려 하면, 관계 연산은 지정한 스코프 모두의 권한을 검사하므로 권한 부족으로 거부된다

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

레지스트리에만 권한을 받고 프로젝트에는 받지 못한 사용자가 프로젝트를 허용하려 하면, 관계 연산은 지정한 스코프 모두의 권한을 검사하므로 권한 부족으로 거부된다

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
  - 프로젝트 project-1 을 허용한 컨테이너 레지스트리 host-1
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

- 반환값이 없고 예외도 발생하지 않는다
  - response = None

#### [an-allowed-project-is-removed-from-the-allowed-list](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

이미 허용된 프로젝트는 허용 목록에서 뺄 수 있다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 을 허용한 컨테이너 레지스트리 host-1
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

- 반환값이 없고 예외도 발생하지 않는다
  - response = None

#### [create-permission-does-not-allow-removing-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

양쪽 스코프에 생성 권한만 받은 사용자가 프로젝트를 제거하면 권한 부족으로 거부된다

Given

- 레지스트리 하나, 프로젝트 하나, 레지스트리, 프로젝트에 권한 있음인 사용자 한 명, 프로젝트는 이미 허용돼 있음
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 project-1 을 허용한 컨테이너 레지스트리 host-1
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

- 반환값이 없고 예외도 발생하지 않는다
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
  - 프로젝트 project-1 을 허용한 컨테이너 레지스트리 host-1
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

- 반환값이 없고 예외도 발생하지 않는다
  - response = None

#### [turning-enforcement-off-lets-an-ungranted-user-allow-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py) — pass

권한 검사를 끄면 아무 권한도 받지 않은 사용자도 프로젝트를 허용할 수 있다

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

- 반환값이 없고 예외도 발생하지 않는다
  - response = None

### creating

#### [a-project-named-while-creating-is-allowed-on-the-new-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

슈퍼관리자가 허용 프로젝트를 함께 지정해 레지스트리를 생성하면 그 관계도 생성된다

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

- ContainerRegistryAdapter.admin_create — user-1이 미리 만들어 둔 프로젝트를 허용 목록에 넣고 https://made.scenario.local로 생성

Then

- 생성한 레지스트리 전체가 반환된다
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

존재하지 않는 프로젝트를 허용 목록에 넣고 레지스트리를 생성하려 하면, 그 프로젝트를 찾을 수 없어 거부된다

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

- ContainerRegistryAdapter.admin_create — user-1이 존재하지 않는 프로젝트를 허용 목록에 넣고 https://made.scenario.local로 생성

Then

- 거부된다
  - 거부: ProjectNotFound

#### [a-user-who-is-not-the-superadmin-may-not-create-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 생성하려 하면 권한 부족으로 거부된다. 이 호출은 호출자가 슈퍼관리자인지만 검사하고, 부여된 권한은 보지 않는다

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

- ContainerRegistryAdapter.admin_create — user-1이 허용 목록 없이 https://made.scenario.local로 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [creating-a-registry-with-only-the-required-values-leaves-the-rest-empty](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py) — pass

슈퍼관리자가 주소·이름·종류만 지정해 레지스트리를 생성하면, 나머지 필드가 모두 비어 있는 노드가 반환된다

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

- ContainerRegistryAdapter.admin_create — user-1이 허용 목록 없이 https://made.scenario.local로 생성

Then

- 생성한 레지스트리 전체가 반환된다
  - url = 'https://made.scenario.local'
  - registry_name = 'made-registry'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: 무시함 — 데이터베이스가 만든다

### editing

#### [a-user-who-is-not-the-superadmin-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 수정하려 하면 권한 부족으로 거부된다. 이 호출은 호출자가 슈퍼관리자인지만 검사하고, 부여된 권한은 보지 않는다

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

- ContainerRegistryAdapter.admin_update — user-1이 주소를 https://moved.scenario.local로 수정

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-address-whose-host-is-empty-is-refused-on-update](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 호스트가 없는 주소로 수정하려 하면, 수정 후의 행을 검사하는 단계에서 주소 형식 오류로 거부된다

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

- ContainerRegistryAdapter.admin_update — user-1이 주소를 http://로 수정

Then

- 거부된다
  - 거부: InvalidContainerRegistryURL

#### [an-edit-that-names-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

슈퍼관리자가 값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환된다

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

- ContainerRegistryAdapter.admin_update — user-1이 아무 값도 지정하지 않고 수정

Then

- 미리 만들어 둔 레지스트리 전체가 반환된다
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

슈퍼관리자가 주소만 수정하면 주소만 새 값이 되고 나머지 필드는 그대로다

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

- ContainerRegistryAdapter.admin_update — user-1이 주소를 https://moved.scenario.local로 수정

Then

- 미리 만들어 둔 레지스트리 전체가 반환된다
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

슈퍼관리자가 레지스트리를 수정하며 프로젝트를 허용하면 그 관계가 생성된다

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

- ContainerRegistryAdapter.admin_update — user-1이 미리 만들어 둔 프로젝트를 허용 목록에 넣으며 수정

Then

- 미리 만들어 둔 레지스트리 전체가 반환된다
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

존재하지 않는 id를 수정하려 하면 대상을 찾을 수 없어 거부된다

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

- ContainerRegistryAdapter.admin_update — user-1이 존재하지 않는 id를 수정

Then

- 거부된다
  - 거부: ContainerRegistryNotFound

#### [turning-a-registry-into-harbor-without-a-project-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py) — pass

프로젝트가 비어 있는 레지스트리를 harbor 종류로 수정하려 하면, harbor는 프로젝트를 요구하므로 거부된다

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

- ContainerRegistryAdapter.admin_update — user-1이 종류를 harbor2로 수정

Then

- 거부된다
  - 거부: InvalidContainerRegistryProject

### reading

#### [a-plain-user-loading-many-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py) — pass

권한을 받지 않은 사용자가 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환된다. 존재하지 않는 id도 같은 거부로 반환되어 있는지 없는지가 드러나지 않는다

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

- ContainerRegistryAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 조회

Then

- 항목마다 권한 부족 거부가 담겨 반환된다
  - length = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [an-empty-id-list-answers-empty-without-calling-the-wiring](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py) — pass

빈 id 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환된다

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

- ContainerRegistryAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

#### [loading-many-ids-keeps-the-order](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py) — pass

슈퍼관리자가 미리 만들어 둔 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 조회하면, 미리 만들어 둔 레지스트리는 요청한 순서대로 반환된다. 존재하지 않는 id의 항목에 무엇이 반환되는지는 아직 정해지지 않았다

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

- ContainerRegistryAdapter.batch_load_by_ids — user-1이 미리 만들어 둔 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 조회

Then

- 미리 만들어 둔 레지스트리는 요청한 순서대로 반환되고, 존재하지 않는 id의 항목은 검사하지 않는다
  - length = 3
  - [0].registry_name = 'wanted-1'
  - [1]: 무시함 — 존재하지 않는 id에 슈퍼관리자가 받는 응답은 아직 정해지지 않았다
  - [2].registry_name = 'other-1'

### retiring

#### [a-user-who-is-not-the-superadmin-may-not-delete-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 삭제하려 하면 권한 부족으로 거부된다. 이 호출은 호출자가 슈퍼관리자인지만 검사하고, 부여된 권한은 보지 않는다

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

- ContainerRegistryAdapter.admin_delete — user-1이 미리 만들어 둔 레지스트리를 삭제

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [deleting-a-registry-answers-with-the-id-it-removed](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

슈퍼관리자가 레지스트리를 삭제하면 삭제한 id를 담은 응답이 반환된다

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

- ContainerRegistryAdapter.admin_delete — user-1이 미리 만들어 둔 레지스트리를 삭제

Then

- 삭제한 id가 반환된다
  - id: 미리 만들어 둔 레지스트리의 id와 같다

#### [deleting-a-registry-takes-its-allowed-projects-with-it](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

허용 프로젝트가 있는 레지스트리를 삭제하면, 외래 키를 통해 그 허용 목록까지 함께 삭제된다

Given

- 레지스트리 하나, 프로젝트 하나가 이미 허용돼 있음, superadmin 한 명
  - 도메인 home-1
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 프로젝트 project-1 을 허용한 컨테이너 레지스트리 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ContainerRegistryAdapter.admin_delete — user-1이 미리 만들어 둔 레지스트리를 삭제

Then

- 삭제한 id가 반환된다
  - id: 미리 만들어 둔 레지스트리의 id와 같다

#### [deleting-an-id-that-holds-no-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py) — pass

존재하지 않는 id를 삭제하려 하면 대상을 찾을 수 없어 거부된다

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

- ContainerRegistryAdapter.admin_delete — user-1이 존재하지 않는 id를 삭제

Then

- 거부된다
  - 거부: ContainerRegistryNotFound

### searching

#### [a-user-who-is-not-the-superadmin-may-not-search-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 레지스트리를 검색하려 하면 권한 부족으로 거부된다. 이 호출은 호출자가 슈퍼관리자인지만 검사하고, 부여된 권한은 보지 않는다

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

- ContainerRegistryAdapter.admin_search — user-1이 조건 없이 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-by-global-visibility-leaves-only-non-global-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 전역 여부 필터로 검색하면 전역이 아닌 레지스트리만 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 non-global 필터로 검색

Then

- 전역이 아닌 레지스트리만 반환된다
  - items: 미리 만들어 둔 레지스트리와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-type-leaves-only-matching-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 종류 필터로 검색하면 그 종류의 레지스트리만 남는다

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

- ContainerRegistryAdapter.admin_search — user-1이 type 필터로 검색

Then

- 필터와 일치하는 레지스트리 하나만 남는다
  - items: 미리 만들어 둔 레지스트리와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [searching-without-a-filter-counts-every-registry](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py) — pass

슈퍼관리자가 조건 없이 검색하면 미리 만들어 둔 레지스트리가 모두 반환된다

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

- ContainerRegistryAdapter.admin_search — user-1이 조건 없이 검색

Then

- 미리 만들어 둔 레지스트리가 모두 집계된다
  - items: 미리 만들어 둔 레지스트리와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

