## project

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/project/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/project/adapter.py)

시나리오: 미완 12 / 14

- ops 로 구성 (9)
  - admin_delete — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - admin_restore — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - admin_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - batch_load_image_commit_registries — 대표 성공 ✓ · 대표 실패 ✓
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - scoped_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - search_by_domain_name — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - search_by_user — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- ops + 직접 구현 (2)
  - assign_users — 성공 있음 1 · 실패 없음 (atomic_bulk_get_ops, scope) — SCENARIO-GAP
  - unassign_users — 성공 없음 · 실패 없음 (atomic_bulk_get_ops, scope) — SCENARIO-GAP
- 직접 구현 (3)
  - admin_create — 성공 있음 1 · 실패 있음 1 (scope)
  - admin_purge — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - admin_update — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP

**batch_load_image_commit_registries**

| 시나리오 | 판정 |
|---|---|
| [읽기 권한이 있으면 요청 순서대로 image commit을 위한 Container Registry를 응답한다](#image_commit_registry-read-targets-in-request-order) | 성공 |
| [읽기 권한이 있고 image commit을 위한 Container Registry가 설정되지 않았으면 빈 값을 응답한다](#image_commit_registry-read-unconfigured-targets) | 성공 |
| [읽기 권한이 없으면 image commit을 위한 Container Registry 조회를 거부한다](#image_commit_registry-target-read-requires-permission) | 거부 |

**assign_users**

| 시나리오 | 판정 |
|---|---|
| [프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, 그 사용자가 명부에 오른다](#project-assigning-a-user-to-a-project-puts-them-on-its-roster) | 성공 |

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생긴다](#project-the-superadmin-makes-a-project-in-a-domain) | 성공 |
| [프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다](#project-a-user-granted-nothing-may-not-make-a-project) | 거부 |

### batch_load_image_commit_registries

<a id="image_commit_registry-read-targets-in-request-order"></a>

#### [read-targets-in-request-order](/tests/scenario/bai_scenario/manager/project/test_image_commit_registry.py) — pass

읽기 권한이 있으면 요청 순서대로 image commit을 위한 Container Registry를 응답한다

Given

- image commit을 위한 Container Registry가 설정되어 있다. 일반 사용자는 프로젝트 읽기 권한이 있다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_image_commit_registries — 같은 프로젝트의 image commit을 위한 Container Registry를 두 번 요청한다

Then

- 요청마다 image commit을 위한 Container Registry나 빈 값 또는 권한 거부를 응답한다
  - targets = [ImageCommitRegistry(registry_name='registry.example.com', project_name='images'), ImageCommitRegistry(registry_name='registry.example.com', project_name='images')]

<a id="image_commit_registry-read-unconfigured-targets"></a>

#### [read-unconfigured-targets](/tests/scenario/bai_scenario/manager/project/test_image_commit_registry.py) — pass

읽기 권한이 있고 image commit을 위한 Container Registry가 설정되지 않았으면 빈 값을 응답한다

Given

- image commit을 위한 Container Registry가 설정되어 있지 않다. 일반 사용자는 프로젝트 읽기 권한이 있다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-1: project 전체에 READ 허용
  - 일반 사용자 user-1: 역할 role-1 보유

When

- ProjectAdapter.batch_load_image_commit_registries — 같은 프로젝트의 image commit을 위한 Container Registry를 두 번 요청한다

Then

- 요청마다 image commit을 위한 Container Registry나 빈 값 또는 권한 거부를 응답한다
  - targets = [None, None]

<a id="image_commit_registry-target-read-requires-permission"></a>

#### [target-read-requires-permission](/tests/scenario/bai_scenario/manager/project/test_image_commit_registry.py) — pass

읽기 권한이 없으면 image commit을 위한 Container Registry 조회를 거부한다

Given

- image commit을 위한 Container Registry가 설정되어 있지 않다. 일반 사용자는 프로젝트 읽기 권한이 없다.
  - 도메인 domain-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 project-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.batch_load_image_commit_registries — 같은 프로젝트의 image commit을 위한 Container Registry를 두 번 요청한다

Then

- 요청마다 image commit을 위한 Container Registry나 빈 값 또는 권한 거부를 응답한다
  - count = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### assign_users

<a id="project-assigning-a-user-to-a-project-puts-them-on-its-roster"></a>

#### [assigning-a-user-to-a-project-puts-them-on-its-roster](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, 그 사용자가 명부에 오른다

Given

- 프로젝트 하나와 그 프로젝트 스코프의 역할, 올릴 사용자, 그리고 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 project-member-1: 이 역할이 앉은 스코프 안에서만 통한다

When

- ProjectAdapter.assign_users — user-2이 user-1을 research-1에 배정

Then

- 명부에 배정한 사람만 올라 있다
  - items: 배정한 사람 하나와 같다

### admin_create

<a id="project-the-superadmin-makes-a-project-in-a-domain"></a>

#### [the-superadmin-makes-a-project-in-a-domain](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생긴다

Given

- 도메인 하나와 프로젝트 정책, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create — user-1이 home-1 아래에 research을 만듦

Then

- 만든 프로젝트 전체가 온다
  - basic_info.name = 'research'
  - basic_info.description = None
  - basic_info.integration_name = None
  - organization.domain_name = 'home-1'
  - organization.resource_policy = 'default'
  - storage.allowed_vfolder_hosts = []
  - lifecycle.is_active = True
  - id: 무시함 — 데이터베이스가 만든다
  - basic_info.type: 무시함 — 타입이 이미 값을 못박는다
  - lifecycle.created_at: 이 실행이 쓴 시각
  - lifecycle.modified_at: 이 실행이 쓴 시각

<a id="project-a-user-granted-nothing-may-not-make-a-project"></a>

#### [a-user-granted-nothing-may-not-make-a-project](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다

Given

- 도메인 하나와 프로젝트 정책, 그리고 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create — user-1이 home-1 아래에 refused을 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

