## project

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/project/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/project/adapter.py)

Not exercised by any scenario: admin_delete, admin_purge, admin_restore, admin_search, admin_update, batch_load_by_ids, batch_load_fields, get, scoped_search, search_by_domain_name, search_by_user, unassign_users.

### project

#### [a-user-granted-nothing-may-not-make-a-project](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다

Given

- 도메인 home-1
- 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
- 도메인에 속한 사용자 한 명 준비
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create — 일반 사용자 user-1
  - CreateProjectInput(name='refused', domain_name=도메인: home-1, resource_policy=프로젝트 정책: default)

Then

- 거부: NotEnoughPermission

#### [assigning-a-user-to-a-project-puts-them-on-its-roster](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, 그 사용자가 명부에 오른다

Given

- 도메인 home-1
- 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
- 프로젝트 research-1
- 도메인에 속한 사용자 한 명 준비
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
- 역할 project-member-1: 이 역할이 앉은 스코프 안에서만 통한다
- 도메인에 속한 사용자 한 명 준비
  - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.assign_users — 슈퍼관리자 user-2
  - 프로젝트: research-1
  - AssignUsersToProjectInput(user_ids=[일반 사용자: user-1], role_id=역할: project-member-1)

Then

- <computed> = 1

#### [the-superadmin-makes-a-project-in-a-domain](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생긴다

Given

- 도메인 home-1
- 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
- 도메인에 속한 사용자 한 명 준비
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create — 슈퍼관리자 user-1
  - CreateProjectInput(name='research', domain_name=도메인: home-1, resource_policy=프로젝트 정책: default)

Then

- project.basic_info.name = 'research'

