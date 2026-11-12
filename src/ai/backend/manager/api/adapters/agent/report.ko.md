## agent

[어댑터](/src/ai/backend/manager/api/adapters/agent/adapter.py)

시나리오: 완성

- ops + 직접 구현 (4)
  - admin_search: 성공 있음 1 · 거부 있음 1 (atomic_bulk_scoped_search_ops, global_searcher_ops, partial_bulk)
  - batch_load_by_ids: 성공 있음 2 · 거부 있음 1 (atomic_bulk_scoped_search_ops, partial_bulk, partial_bulk_get_ops)
  - batch_load_by_uuids: 성공 있음 1 · 거부 있음 2 (atomic_bulk_scoped_search_ops, partial_bulk, partial_bulk_get_ops)
  - batch_load_container_counts: 성공 있음 2 · 거부 있음 1 (partial_bulk, partial_bulk_get_ops)
- 직접 구현 (3)
  - get_total_resources: 성공 있음 1 · 거부 있음 1 (global_scope)
  - update_resource_group: 성공 있음 1 · 거부 있음 2 (global_scope)
  - update_resource_group_from_body: 성공 있음 1 · 거부 있음 1 (global_scope)

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 에이전트 하나만 남기는 조건과 순서를 걸어 검색하면 그 에이전트만 한 페이지로 옵니다](#searching-the-superadmin-picks-an-agent-by-its-name) | 성공 |
| [superadmin 만 부를 수 있는 검색이라, 아무 권한도 없는 일반 사용자가 부르면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-the-agents) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹의 에이전트를 읽을 수 있는 사용자가 이름으로 한 번에 조회하면 그 에이전트가 통째로 옵니다](#batch_loading-a-user-reading-the-group-loads-an-agent-by-name) | 성공 |
| [없는 이름은 빈 값으로 옵니다](#batch_loading-an-unknown-agent-name-answers-an-empty-value) | 성공 |
| [한 그룹만 읽을 수 있는 사용자가 다른 그룹의 에이전트를 함께 조회하면 그 자리는 권한 부족으로 옵니다](#batch_loading-a-user-reading-one-group-gets-a-denial-for-the-agent-of-another) | 거부 |

**batch_load_by_uuids**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹의 에이전트를 읽을 수 있는 사용자가 id 로 한 번에 조회하면 그 에이전트가 통째로 옵니다](#batch_loading-a-user-reading-the-group-loads-an-agent-by-entity-id) | 성공 |
| [아무 권한도 없는 사용자가 id 로 조회하면 그 자리는 권한 부족으로 옵니다](#batch_loading-a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id) | 거부 |
| [id 로 조회하면 권한 검사를 거치므로, 없는 id 는 빈 값이 아니라 권한 부족으로 옵니다](#batch_loading-an-unknown-agent-entity-id-answers-a-denial) | 거부 |

**batch_load_container_counts**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹의 에이전트를 읽을 수 있는 사용자가 컨테이너 수를 조회하면 아무것도 돌지 않는 에이전트이므로 0 이 옵니다](#batch_loading-a-user-reading-the-group-counts-no-container-on-the-agent) | 성공 |
| [없는 이름의 컨테이너 수는 0 으로 옵니다](#batch_loading-an-unknown-agent-name-counts-no-container) | 성공 |
| [아무 권한도 없는 사용자가 컨테이너 수를 조회하면 권한 부족으로 옵니다](#batch_loading-a-user-granted-nothing-gets-a-denial-for-the-container-count) | 거부 |

**get_total_resources**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 전체 자원 합을 조회하면 살아 있는 에이전트가 보고한 슬롯의 용량과 사용량의 합이 옵니다](#total_resources-the-superadmin-reads-the-total-of-the-slots-the-agents-report) | 성공 |
| [superadmin 만 부를 수 있는 조회라, 아무 권한도 없는 일반 사용자가 부르면 권한 부족으로 거부됩니다](#total_resources-a-user-granted-nothing-may-not-read-the-total) | 거부 |

**update_resource_group**

| 시나리오 | 판정 |
|---|---|
| [다른 그룹의 세션이 지정한 에이전트를 강제로 옮기면 지정을 지우고 바뀐 그룹을 담은 응답이 옵니다](#changing_resource_group-force-moves-an-agent-designated-by-another-groups-session) | 성공 |
| [superadmin 만 부를 수 있는 변경이라, 아무 권한도 없는 일반 사용자가 에이전트를 옮기면 권한 부족으로 거부됩니다](#changing_resource_group-a-user-granted-nothing-may-not-move-an-agent) | 거부 |
| [다른 그룹의 세션이 지정한 에이전트를 강제하지 않고 옮기면 충돌한다는 이유로 거부됩니다](#changing_resource_group-an-agent-designated-by-another-groups-session-needs-force) | 거부 |

**update_resource_group_from_body**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 REST 본문으로 에이전트를 옮겨도 바뀐 그룹을 담은 응답이 옵니다](#changing_resource_group-the-superadmin-moves-an-agent-through-the-rest-body) | 성공 |
| [superadmin 만 부를 수 있는 변경이라, 아무 권한도 없는 일반 사용자가 REST 본문으로 에이전트를 옮겨도 권한 부족으로 거부됩니다](#changing_resource_group-a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body) | 거부 |

### admin_search

<a id="searching-the-superadmin-picks-an-agent-by-its-name"></a>

#### [the-superadmin-picks-an-agent-by-its-name](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

superadmin 이 에이전트 하나만 남기는 조건과 순서를 걸어 검색하면 그 에이전트만 한 페이지로 옵니다

Given

- 에이전트 2개와, superadmin 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-2: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.admin_search: user-1이 에이전트 agent-1 하나만 남기는 조건과 id 오름차순을 걸어 한 건씩 검색합니다

Then

- 미리 등록한 에이전트 1개가 통째로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].id = 'agent-1'
  - items[0].entity_id: 미리 등록한 에이전트의 id 와 같다
  - items[0].uuid: 미리 등록한 에이전트의 id 와 같다
  - items[0].capacity = {}
  - items[0].used = {}
  - items[0].free = {}
  - items[0].status = 'ALIVE'
  - items[0].status_changed = None
  - items[0].first_contact: 이 실행이 쓴 시각
  - items[0].lost_at = None
  - items[0].schedulable = True
  - items[0].architecture = 'x86_64'
  - items[0].version = '0.0.0'
  - items[0].auto_terminate_abusing_kernel = False
  - items[0].compute_plugins = None
  - items[0].region = 'local'
  - items[0].addr = 'tcp://agent-1:6001'
  - items[0].scaling_group = 'mine-1'
  - items[0].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']

<a id="searching-a-user-granted-nothing-may-not-search-the-agents"></a>

#### [a-user-granted-nothing-may-not-search-the-agents](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

superadmin 만 부를 수 있는 검색이라, 아무 권한도 없는 일반 사용자가 부르면 권한 부족으로 거부됩니다

Given

- 에이전트 1개와, 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.admin_search: user-1이 에이전트 agent-1 하나만 남기는 조건과 id 오름차순을 걸어 한 건씩 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-reading-the-group-loads-an-agent-by-name"></a>

#### [a-user-reading-the-group-loads-an-agent-by-name](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

리소스 그룹의 에이전트를 읽을 수 있는 사용자가 이름으로 한 번에 조회하면 그 에이전트가 통째로 옵니다

Given

- 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_by_ids: user-1이 에이전트 1개의 이름을 한 번에 조회합니다

Then

- 미리 등록한 에이전트가 입력 순서대로 노드로 옵니다
  - length = 1
  - [0].id = 'agent-1'
  - [0].entity_id: 미리 등록한 에이전트의 id 와 같다
  - [0].uuid: 미리 등록한 에이전트의 id 와 같다
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: 이 실행이 쓴 시각
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']

<a id="batch_loading-an-unknown-agent-name-answers-an-empty-value"></a>

#### [an-unknown-agent-name-answers-an-empty-value](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

없는 이름은 빈 값으로 옵니다

Given

- 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_by_ids: user-1이 에이전트 1개의 이름과 없는 이름 하나를 한 번에 조회합니다

Then

- 미리 등록한 에이전트는 입력 순서대로 노드로, 없는 이름 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id = 'agent-1'
  - [0].entity_id: 미리 등록한 에이전트의 id 와 같다
  - [0].uuid: 미리 등록한 에이전트의 id 와 같다
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: 이 실행이 쓴 시각
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']
  - [1] = None

<a id="batch_loading-a-user-reading-one-group-gets-a-denial-for-the-agent-of-another"></a>

#### [a-user-reading-one-group-gets-a-denial-for-the-agent-of-another](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

한 그룹만 읽을 수 있는 사용자가 다른 그룹의 에이전트를 함께 조회하면 그 자리는 권한 부족으로 옵니다

Given

- 에이전트 1개, 다른 그룹의 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 자원 그룹 elsewhere-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-2: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_by_ids: user-1이 에이전트 2개의 이름을 한 번에 조회합니다

Then

- 읽을 수 있는 에이전트는 노드로, 나머지 자리는 권한 부족으로 옵니다
  - length = 2
  - [0].id = 'agent-1'
  - [0].entity_id: 미리 등록한 에이전트의 id 와 같다
  - [0].uuid: 미리 등록한 에이전트의 id 와 같다
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: 이 실행이 쓴 시각
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']
  - 거부: NotEnoughPermission

### batch_load_by_uuids

<a id="batch_loading-a-user-reading-the-group-loads-an-agent-by-entity-id"></a>

#### [a-user-reading-the-group-loads-an-agent-by-entity-id](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

리소스 그룹의 에이전트를 읽을 수 있는 사용자가 id 로 한 번에 조회하면 그 에이전트가 통째로 옵니다

Given

- 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_by_uuids: user-1이 에이전트 1개의 id 를 한 번에 조회합니다

Then

- 미리 등록한 에이전트가 입력 순서대로 노드로 옵니다
  - length = 1
  - [0].id = 'agent-1'
  - [0].entity_id: 미리 등록한 에이전트의 id 와 같다
  - [0].uuid: 미리 등록한 에이전트의 id 와 같다
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: 이 실행이 쓴 시각
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']

<a id="batch_loading-a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id"></a>

#### [a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

아무 권한도 없는 사용자가 id 로 조회하면 그 자리는 권한 부족으로 옵니다

Given

- 에이전트 1개와, 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.batch_load_by_uuids: user-1이 에이전트 1개의 id 를 한 번에 조회합니다

Then

- 읽을 수 있는 에이전트는 노드로, 나머지 자리는 권한 부족으로 옵니다
  - length = 1
  - 거부: NotEnoughPermission

<a id="batch_loading-an-unknown-agent-entity-id-answers-a-denial"></a>

#### [an-unknown-agent-entity-id-answers-a-denial](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

id 로 조회하면 권한 검사를 거치므로, 없는 id 는 빈 값이 아니라 권한 부족으로 옵니다

Given

- 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_by_uuids: user-1이 에이전트 1개의 id 와 없는 id 하나를 한 번에 조회합니다

Then

- 미리 등록한 에이전트는 입력 순서대로 노드로, 없는 id 자리는 권한 부족으로 옵니다
  - length = 2
  - [0].id = 'agent-1'
  - [0].entity_id: 미리 등록한 에이전트의 id 와 같다
  - [0].uuid: 미리 등록한 에이전트의 id 와 같다
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: 이 실행이 쓴 시각
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']
  - 거부: NotEnoughPermission

### batch_load_container_counts

<a id="batch_loading-a-user-reading-the-group-counts-no-container-on-the-agent"></a>

#### [a-user-reading-the-group-counts-no-container-on-the-agent](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

리소스 그룹의 에이전트를 읽을 수 있는 사용자가 컨테이너 수를 조회하면 아무것도 돌지 않는 에이전트이므로 0 이 옵니다

Given

- 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_container_counts: user-1이 에이전트 1개의 컨테이너 수를 한 번에 조회합니다

Then

- 에이전트마다 컨테이너 수가 입력 순서대로 옵니다
  - length = 1
  - [0] = 0

<a id="batch_loading-an-unknown-agent-name-counts-no-container"></a>

#### [an-unknown-agent-name-counts-no-container](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

없는 이름의 컨테이너 수는 0 으로 옵니다

Given

- 에이전트 1개와, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 agent-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 agent-reader-1: agent 전체에 READ 허용
    - 일반 사용자 user-1: 역할 agent-reader-1 보유

When

- AgentAdapter.batch_load_container_counts: user-1이 에이전트 1개의 컨테이너 수와 없는 이름 하나의 수를 한 번에 조회합니다

Then

- 읽을 수 있는 에이전트의 수는 0 으로, 없는 이름 자리도 0 으로 옵니다
  - length = 2
  - [0] = 0
  - [1] = 0

<a id="batch_loading-a-user-granted-nothing-gets-a-denial-for-the-container-count"></a>

#### [a-user-granted-nothing-gets-a-denial-for-the-container-count](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

아무 권한도 없는 사용자가 컨테이너 수를 조회하면 권한 부족으로 옵니다

Given

- 에이전트 1개와, 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.batch_load_container_counts: user-1이 에이전트 1개의 컨테이너 수를 한 번에 조회합니다

Then

- 읽을 수 없는 에이전트 자리는 권한 부족으로 옵니다
  - length = 1
  - 거부: NotEnoughPermission

### get_total_resources

<a id="total_resources-the-superadmin-reads-the-total-of-the-slots-the-agents-report"></a>

#### [the-superadmin-reads-the-total-of-the-slots-the-agents-report](/tests/scenario/bai_scenario/manager/agent/test_total_resources.py): pass

superadmin 이 전체 자원 합을 조회하면 살아 있는 에이전트가 보고한 슬롯의 용량과 사용량의 합이 옵니다

Given

- 에이전트 2개, 에이전트마다 슬롯 1개를 보고하고와, superadmin 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 자원 슬롯 유형 slot-1: count 유형
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-1: slot-1 슬롯 용량 10 보고, 1 사용 중
  - 에이전트 agent-2: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-2: slot-1 슬롯 용량 10 보고, 1 사용 중
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.get_total_resources: user-1이 클러스터 전체 자원 합을 조회합니다

Then

- 에이전트가 보고한 슬롯의 합이 옵니다
  - total_capacity_slots = {'slot-1': '20'}
  - total_used_slots = {'slot-1': '2'}
  - total_free_slots = {'slot-1': '18'}

<a id="total_resources-a-user-granted-nothing-may-not-read-the-total"></a>

#### [a-user-granted-nothing-may-not-read-the-total](/tests/scenario/bai_scenario/manager/agent/test_total_resources.py): pass

superadmin 만 부를 수 있는 조회라, 아무 권한도 없는 일반 사용자가 부르면 권한 부족으로 거부됩니다

Given

- 에이전트 1개와, 일반 사용자 한 명
  - 자원 그룹 mine-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.get_total_resources: user-1이 클러스터 전체 자원 합을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### update_resource_group

<a id="changing_resource_group-force-moves-an-agent-designated-by-another-groups-session"></a>

#### [force-moves-an-agent-designated-by-another-groups-session](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

다른 그룹의 세션이 지정한 에이전트를 강제로 옮기면 지정을 지우고 바뀐 그룹을 담은 응답이 옵니다

Given

- 다른 그룹의 세션이 지정한 에이전트 하나와 옮길 그룹, 그리고 superadmin 한 명
  - 자원 그룹 before-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 자원 그룹 after-1: fifo 스케줄러를 사용합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: 지정 에이전트 하나를 갖습니다

When

- AgentAdapter.update_resource_group: user-1이 강제로 에이전트 agent-1를 after-1 그룹으로 옮깁니다

Then

- 바뀐 리소스 그룹을 담은 응답이 옵니다
  - agent_id = 'agent-1'
  - resource_group_id: 미리 만든 옮길 그룹의 id 와 같다
  - policy = 'terminate'
  - conflicting_session_ids = []
  - terminating_session_ids = []

<a id="changing_resource_group-a-user-granted-nothing-may-not-move-an-agent"></a>

#### [a-user-granted-nothing-may-not-move-an-agent](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

superadmin 만 부를 수 있는 변경이라, 아무 권한도 없는 일반 사용자가 에이전트를 옮기면 권한 부족으로 거부됩니다

Given

- 에이전트 하나와 옮길 그룹, 그리고 일반 사용자 한 명
  - 자원 그룹 before-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 자원 그룹 after-1: fifo 스케줄러를 사용합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.update_resource_group: user-1이 에이전트 agent-1를 after-1 그룹으로 옮깁니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="changing_resource_group-an-agent-designated-by-another-groups-session-needs-force"></a>

#### [an-agent-designated-by-another-groups-session-needs-force](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

다른 그룹의 세션이 지정한 에이전트를 강제하지 않고 옮기면 충돌한다는 이유로 거부됩니다

Given

- 다른 그룹의 세션이 지정한 에이전트 하나와 옮길 그룹, 그리고 superadmin 한 명
  - 자원 그룹 before-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 자원 그룹 after-1: fifo 스케줄러를 사용합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: 지정 에이전트 하나를 갖습니다

When

- AgentAdapter.update_resource_group: user-1이 에이전트 agent-1를 after-1 그룹으로 옮깁니다

Then

- 거부됩니다
  - 거부: AgentHasConflictingSessions

### update_resource_group_from_body

<a id="changing_resource_group-the-superadmin-moves-an-agent-through-the-rest-body"></a>

#### [the-superadmin-moves-an-agent-through-the-rest-body](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

superadmin 이 REST 본문으로 에이전트를 옮겨도 바뀐 그룹을 담은 응답이 옵니다

Given

- 에이전트 하나와 옮길 그룹, 그리고 superadmin 한 명
  - 자원 그룹 before-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 자원 그룹 after-1: fifo 스케줄러를 사용합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.update_resource_group_from_body: user-1이 REST 본문으로 에이전트 agent-1를 after-1 그룹으로 옮깁니다

Then

- 바뀐 리소스 그룹을 담은 응답이 옵니다
  - agent_id = 'agent-1'
  - resource_group_id: 미리 만든 옮길 그룹의 id 와 같다
  - policy = 'terminate'
  - conflicting_session_ids = []
  - terminating_session_ids = []

<a id="changing_resource_group-a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body"></a>

#### [a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

superadmin 만 부를 수 있는 변경이라, 아무 권한도 없는 일반 사용자가 REST 본문으로 에이전트를 옮겨도 권한 부족으로 거부됩니다

Given

- 에이전트 하나와 옮길 그룹, 그리고 일반 사용자 한 명
  - 자원 그룹 before-1: fifo 스케줄러를 사용합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 자원 그룹 after-1: fifo 스케줄러를 사용합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AgentAdapter.update_resource_group_from_body: user-1이 REST 본문으로 에이전트 agent-1를 after-1 그룹으로 옮깁니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

