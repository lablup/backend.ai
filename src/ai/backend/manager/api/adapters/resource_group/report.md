## resource_group

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/resource_group/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/resource_group/adapter.py)

Not exercised by any scenario: admin_replace_default_deployment_options, admin_replace_default_session_options, batch_load_by_ids, batch_load_by_names, batch_load_fields, get_allowed_domains_for_resource_group, get_allowed_projects_for_resource_group, get_allowed_resource_groups_for_domain, get_allowed_resource_groups_for_project, get_fair_share_spec, get_resource_info, purge, scoped_search, search, update, update_allowed_domains_for_resource_group, update_allowed_projects_for_resource_group, update_allowed_resource_groups_for_domain, update_allowed_resource_groups_for_project, update_config, update_fair_share_spec.

### resource_group

#### [a-resource-group-already-there-is-read-back-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_resource_group.py) — pass

리소스 그룹이 이미 있을 때 이름으로 조회하면, 그 그룹이 답으로 온다

Given

- 이미 있는 리소스 그룹과, superadmin 한 명
  - 도메인 home-1
  - 리소스 그룹 compute-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.get — user-1이 compute-1으로 조회

Then

- 리소스 그룹 전체가 온다
  - name = 'compute-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - id: 무시함 — 데이터베이스가 만든다
  - scheduler: 무시함 — 설치본이 정한 기본값이라 시나리오가 말할 수 없다
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다
  - metadata.created_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-make-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_resource_group.py) — pass

리소스 그룹 생성은 도메인 생성과 같이 전역 역할이 지키므로, 슈퍼관리자가 아닌 사용자는 권한을 얼마나 받았는지와 무관하게 막힌다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 home-1 아래에 refused을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-makes-a-resource-group-in-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_resource_group.py) — pass

슈퍼관리자가 도메인 아래에 리소스 그룹을 만들면, 그 이름의 그룹이 답으로 온다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ResourceGroupAdapter.create — user-1이 home-1 아래에 compute을 만듦

Then

- 리소스 그룹 전체가 온다
  - name = 'compute'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - id: 무시함 — 데이터베이스가 만든다
  - scheduler: 무시함 — 설치본이 정한 기본값이라 시나리오가 말할 수 없다
  - default_deployment_options: 무시함 — 설치본이 정한 기본값이다
  - default_session_options: 무시함 — 설치본이 정한 기본값이다
  - metadata.created_at: 이 실행이 쓴 시각

