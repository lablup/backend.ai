## deployment

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/deployment/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/deployment/adapter.py)

Not exercised by any scenario: activate_revision, add_revision, admin_refresh_deployment_revisions, admin_search_replicas, admin_search_revisions, batch_load_access_tokens_by_ids, batch_load_auto_scaling_rules_by_ids, batch_load_by_ids, batch_load_fields, batch_load_policies_by_endpoint_ids, batch_load_replicas_by_ids, batch_load_revisions_by_ids, batch_load_routes_by_ids, bulk_delete_access_tokens, bulk_delete_rules, create_access_token, create_rule, delete_access_token, delete_rule, get_access_token, get_policy, get_replica, get_revision, get_rule, search_access_tokens, search_policies, search_replicas, search_revision_resource_slots, search_revisions, search_routes, search_rules, update_route_traffic, update_rule, upsert_policy.

### creating

#### [a-create-grant-in-another-project-does-not-reach-this-one](/tests/scenario/bai_scenario/manager/deployment/test_creating.py) — pass

생성 권한을 받은 프로젝트가 아닌 다른 프로젝트에 배포를 만들면, 권한 부족으로 거부된다

Given

- 배포를 놓을 프로젝트와, 다른 프로젝트에서 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유

When

- DeploymentAdapter.create — user-1이 team-1에 serving 배포를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-deployment-made-without-a-name-is-named-after-its-maker](/tests/scenario/bai_scenario/manager/deployment/test_creating.py) — pass

이름을 대지 않고 배포를 만들면, 만든 사람에게서 이름이 지어진다

Given

- 배포를 놓을 수 있는 프로젝트와, 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유

When

- DeploymentAdapter.create — user-1이 team-1에 이름 없이 배포를 만듦

Then

- 만든 배포 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name: 만든 사람에게서 지어진 이름
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 만든 사람와 같다
  - options: 리소스 그룹의 기본값와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

#### [a-user-granted-create-in-a-project-makes-a-deployment-there](/tests/scenario/bai_scenario/manager/deployment/test_creating.py) — pass

프로젝트에서 배포 생성 권한을 받은 사용자가 배포를 만들면, 그 프로젝트에 속하고 부른 사람이 소유하는 배포가 리비전 없이 만들어진다

Given

- 배포를 놓을 수 있는 프로젝트와, 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유

When

- DeploymentAdapter.create — user-1이 team-1에 serving 배포를 만듦

Then

- 만든 배포 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'serving'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 2
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 만든 사람와 같다
  - options: 리소스 그룹의 기본값와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

#### [a-user-granted-nothing-may-not-create-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_creating.py) — pass

아무 배포 권한도 받지 않은 사용자가 배포를 만들면, 권한 부족으로 거부된다

Given

- 배포를 놓을 수 있는 프로젝트와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DeploymentAdapter.create — user-1이 team-1에 serving 배포를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [turning-enforcement-off-lets-a-user-create-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_creating.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 배포를 만든다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 배포를 놓을 수 있는 프로젝트와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DeploymentAdapter.create — user-1이 team-1에 serving 배포를 만듦

Then

- 만든 배포 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'serving'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 만든 사람와 같다
  - options: 리소스 그룹의 기본값와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

### editing

#### [a-user-granted-only-read-may-not-update-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

읽기 권한만 받은 사용자가 배포를 수정하면, 권한 부족으로 거부된다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update — user-1이 deployment-1를 이름을 renamed으로 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-opens-a-deployment-to-the-public](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

공개가 아닌 배포를 수정 권한을 받은 사용자가 공개로 바꾸면, 공개로 바뀐 상태가 온다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update — user-1이 deployment-1를 바깥에 열도록 수정

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = True
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

#### [a-user-granted-update-raises-the-replica-count](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

수정 권한을 받은 사용자가 복제 수를 올리면, 두려는 복제 수가 새 값이 된다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update — user-1이 deployment-1를 복제 수를 3으로 수정

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 3
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

#### [a-user-granted-update-renames-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

수정 권한을 받은 사용자가 이름을 바꾸면, 이름만 새 값이 되고 나머지는 그대로다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update — user-1이 deployment-1를 이름을 renamed으로 수정

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'renamed'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

#### [clearing-the-tags-of-a-deployment-leaves-none](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

태그가 붙은 배포의 태그를 비우면, 태그가 하나도 남지 않는다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다, keep 태그가 붙어 있다

When

- DeploymentAdapter.update — user-1이 deployment-1를 태그를 비우도록 수정

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

#### [the-superadmin-renames-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

다른 사람이 만든 배포의 이름을 아무 권한도 받지 않은 슈퍼관리자가 바꾸면, 이름만 새 값이 된다. 역할이 권한 그래프를 지나간다

Given

- 다른 사람이 만든 배포 하나와, 아무 배포 권한도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 배포 theirs-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update — user-1이 theirs-1를 이름을 renamed으로 수정

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'renamed'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

#### [updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_editing.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 수정하면, 대상이 없다는 것으로 거부된다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update — user-1이 아무것도 갖지 않은 id를 이름을 renamed으로 수정

Then

- 거부된다
  - 거부: EndpointNotFound

### options

#### [a-user-granted-only-read-may-not-replace-the-options](/tests/scenario/bai_scenario/manager/deployment/test_options.py) — pass

읽기 권한만 받은 사용자가 옵션을 갈아끼우면, 권한 부족으로 거부된다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options — user-1이 deployment-1의 옵션을 처리기별 설정 check-replica-deployments을 담아 갈아끼움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-replaces-the-options-whole](/tests/scenario/bai_scenario/manager/deployment/test_options.py) — pass

수정 권한을 받은 사용자가 기본값과 처리기별 설정을 담아 옵션을 갈아끼우면, 준 것이 통째로 새 옵션이 되고 답은 그 옵션만 싣는다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options — user-1이 deployment-1의 옵션을 처리기별 설정 check-replica-deployments을 담아 갈아끼움

Then

- 갈아끼운 옵션만 온다
  - deployment_id: 심은 배포와 같다
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = [('check-replica-deployments', None, 1)]

#### [naming-a-handler-twice-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_options.py) — pass

같은 처리기 이름을 두 번 담아 옵션을 갈아끼우면, 입력이 틀렸다는 이유로 거부된다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options — user-1이 deployment-1의 옵션을 처리기별 설정 check-replica-deployments, check-replica-deployments을 담아 갈아끼움

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [naming-an-unregistered-handler-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_options.py) — pass

등록되지 않은 처리기 이름을 담아 옵션을 갈아끼우면, 입력이 틀렸다는 이유로 거부된다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options — user-1이 deployment-1의 옵션을 처리기별 설정 no-such-handler을 담아 갈아끼움

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [replacing-with-no-handler-entry-drops-the-inherited-ones](/tests/scenario/bai_scenario/manager/deployment/test_options.py) — pass

물려받은 처리기별 설정이 있는 배포에 기본값만 담아 옵션을 갈아끼우면, 물려받은 설정이 하나도 남지 않는다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options — user-1이 deployment-1의 옵션을 기본값만 담아 갈아끼움

Then

- 갈아끼운 옵션만 온다
  - deployment_id: 심은 배포와 같다
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []

### reading

#### [a-deployment-holding-no-revision-answers-nothing-as-its-current-one](/tests/scenario/bai_scenario/manager/deployment/test_reading.py) — pass

리비전이 딸리지 않은 배포의 현재 리비전을 조회하면, 현재 리비전이 없다는 이유로 거부된다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get_current_revision — user-1이 deployment-1의 현재 리비전을 조회

Then

- 거부된다
  - 거부: DeploymentRevisionNotFound

#### [a-user-granted-nothing-may-not-read-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_reading.py) — pass

같은 배포가 있고 아무 권한도 받지 않은 사용자가 조회하면, 권한 부족으로 거부된다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get — user-1이 deployment-1로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-reads-a-deployment-by-id](/tests/scenario/bai_scenario/manager/deployment/test_reading.py) — pass

배포 하나가 있고 읽기 권한을 받은 사용자가 id로 조회하면, 그 배포가 답으로 온다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get — user-1이 deployment-1로 조회

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_reading.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. 권한 검사를 지나가는 사람만 이 답을 본다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get — user-1이 아무것도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: EndpointNotFound

#### [an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/deployment/test_reading.py) — pass

읽기 권한을 받은 사용자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없기 때문이다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get — user-1이 아무것도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-superadmin-reads-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_reading.py) — pass

다른 사람이 만든 배포를 아무 권한도 받지 않은 슈퍼관리자가 id로 조회하면, 그 배포가 답으로 온다. 역할이 권한 그래프를 지나간다

Given

- 다른 사람이 만든 배포 하나와, 아무 배포 권한도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 배포 theirs-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get — user-1이 theirs-1로 조회

Then

- 심은 배포 전체가 온다
  - id: 심은 배포와 같다
  - metadata.project_id: 심은 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'theirs-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 심은 배포를 가진 사람와 같다
  - options: 심은 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

### retiring

#### [a-user-granted-only-update-may-not-retire-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py) — pass

수정 권한만 받고 soft-delete 권한은 받지 않은 사용자가 배포를 지우면, 권한 부족으로 거부된다. 지우기는 수정과 다른 문이다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete — user-1이 deployment-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-soft-delete-retires-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py) — pass

soft-delete 권한을 받은 사용자가 배포를 지우면, 그 배포를 지우기 시작했다고 답한다

Given

- 이미 있는 배포 하나와, 배포에 SOFT_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 SOFT_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete — user-1이 deployment-1를 지움

Then

- 지우기 시작한 배포를 답한다
  - id: 심은 배포와 같다

#### [retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete — user-1이 아무것도 갖지 않은 id를 지움

Then

- 거부된다
  - 거부: EndpointNotFound

#### [the-superadmin-retires-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py) — pass

다른 사람이 만든 배포를 아무 권한도 받지 않은 슈퍼관리자가 지우면, 그 배포를 지우기 시작했다고 답한다. 역할이 권한 그래프를 지나간다

Given

- 다른 사람이 만든 배포 하나와, 아무 배포 권한도 받지 않은 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 배포 theirs-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete — user-1이 theirs-1를 지움

Then

- 지우기 시작한 배포를 답한다
  - id: 심은 배포와 같다

### searching

#### [a-user-granted-nothing-may-not-search-a-project](/tests/scenario/bai_scenario/manager/deployment/test_searching.py) — pass

그 프로젝트에 읽기 권한이 없는 사용자가 프로젝트를 훑으면, 권한 부족으로 거부된다

Given

- 같은 프로젝트의 배포 3개와, 그 프로젝트의 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 wanted-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 other-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 other-2: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.project_search — user-1이 team-1 안을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-search-even-their-own](/tests/scenario/bai_scenario/manager/deployment/test_searching.py) — pass

자기 스코프에서 읽기 권한을 받지 않은 사람이 자기 것을 훑으면, 권한 부족으로 거부된다. 이 문도 범위를 좁히기만 하지 않고 권한이 지킨다

Given

- 두 사람이 각자 만든 배포와, 아무 배포 권한도 받지 않은 그중 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 배포 mine-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 theirs-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.my_search — user-1이 자기 것을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-may-not-search-every-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching.py) — pass

배포 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 거부된다. 이 문은 권한 그래프가 아니라 역할이 지킨다

Given

- 같은 프로젝트의 배포 3개와, 그 프로젝트의 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 wanted-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 other-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 other-2: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [searching-a-project-finds-only-its-own-deployments](/tests/scenario/bai_scenario/manager/deployment/test_searching.py) — pass

두 프로젝트에 배포가 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 그 프로젝트를 훑으면, 그 프로젝트의 것만 나온다

Given

- 두 프로젝트에 나뉜 배포들과, 한쪽 프로젝트에서만 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 프로젝트 other-1
  - 배포 wanted-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 beside-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 elsewhere-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.project_search — user-1이 team-1 안을 조회

Then

- 심은 배포가 모두, 그리고 그것만 세어진다
  - items = ['beside-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [searching-my-own-finds-only-what-i-made](/tests/scenario/bai_scenario/manager/deployment/test_searching.py) — pass

같은 프로젝트에 두 사람이 각자 배포를 만들었고 자기 스코프에서 읽기 권한을 받은 사람이 자기 것을 훑으면, 자기가 만든 것만 나온다

Given

- 두 사람이 각자 만든 배포와, 자기 스코프에서 배포 읽기 권한을 받은 그중 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 자기 스코프에서 배포를 읽을 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-owner-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-owner-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 배포 mine-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 theirs-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.my_search — user-1이 자기 것을 조회

Then

- 심은 배포가 모두, 그리고 그것만 세어진다
  - items = ['mine-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-counts-every-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching.py) — pass

배포 셋이 있고 슈퍼관리자가 필터 없이 전체를 훑으면, 셋을 모두 센다

Given

- 같은 프로젝트의 배포 3개와, 그 프로젝트의 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 배포 wanted-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 other-1: 복제를 1개 두려 한다, 아직 리비전이 없다
  - 배포 other-2: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 심은 배포가 모두, 그리고 그것만 세어진다
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

### syncing

#### [a-user-granted-only-read-may-not-sync-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_syncing.py) — pass

읽기 권한만 받은 사용자가 복제 맞추기를 요청하면, 권한 부족으로 거부된다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 1개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.sync_replicas — user-1이 deployment-1의 복제 맞추기를 요청

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-starts-syncing-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_syncing.py) — pass

수정 권한을 받은 사용자가 복제 맞추기를 요청하면, 맞추기를 시작했다고 답한다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 deployment-user-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제를 2개 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.sync_replicas — user-1이 deployment-1의 복제 맞추기를 요청

Then

- 맞추기를 시작했다고 답한다
  - success = True

