## session

[배경](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session/adapter.py)

시나리오: 미완성 28 / 30

- ops 구성 (7)
  - batch_load_kernel_group_environs_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_kernel_group_resource_slots_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_kernel_groups_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_main_kernel_groups: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - scoped_search_kernel_group_environs: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - scoped_search_kernel_group_resource_slots: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - scoped_search_kernel_groups: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
- ops + 직접 구현 (10)
  - admin_search: 성공 있음 3 · 거부 있음 1 (global_searcher_ops, partial_bulk)
  - admin_search_kernels: 성공 없음 · 거부 없음 (atomic_bulk_field, global_searcher_ops): SCENARIO-GAP
  - batch_load_by_ids: 성공 없음 · 거부 없음 (partial_bulk, partial_bulk_get_ops): SCENARIO-GAP
  - batch_load_kernels_by_ids: 성공 없음 · 거부 없음 (atomic_bulk_field, partial_bulk_get_ops): SCENARIO-GAP
  - gql_search_by_project: 성공 없음 · 거부 없음 (partial_bulk, scoped_search_ops): SCENARIO-GAP
  - project_search: 성공 없음 · 거부 없음 (partial_bulk, scoped_search_ops): SCENARIO-GAP
  - scoped_search: 성공 없음 · 거부 없음 (partial_bulk, scoped_search_ops): SCENARIO-GAP
  - search_kernels_by_agent: 성공 없음 · 거부 없음 (atomic_bulk_field, global_searcher_ops): SCENARIO-GAP
  - search_kernels_by_session: 성공 없음 · 거부 없음 (atomic_bulk_field, atomic_bulk_scoped_search_ops): SCENARIO-GAP
  - search_sessions_by_agent: 성공 없음 · 거부 없음 (global_searcher_ops, partial_bulk): SCENARIO-GAP
- 직접 구현 (13)
  - batch_resource_allocation_by_kernel: 성공 없음 · 거부 없음 (atomic_bulk_field): SCENARIO-GAP
  - batch_resource_allocation_by_session: 성공 없음 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - compute_schedule: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - enqueue: 성공 없음 · 거부 없음 (partial_bulk, scope): SCENARIO-GAP
  - exclude_idle_checks: 성공 없음 · 거부 없음 (legacy_partial_bulk): SCENARIO-GAP
  - get: 성공 없음 · 거부 없음 (partial_bulk, single_entity): SCENARIO-GAP
  - get_logs: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - include_idle_checks: 성공 없음 · 거부 없음 (legacy_partial_bulk): SCENARIO-GAP
  - partial_bulk_terminate: 성공 있음 3 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - shutdown_service: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - start_service: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - terminate: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - update: 성공 없음 · 거부 없음 (partial_bulk, single_entity): SCENARIO-GAP

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [세션을 하나도 미리 저장하지 않은 상태에서 superadmin 이 조회하면, 응답은 비어 있습니다](#session-a-scenario-that-laid-no-session-finds-none) | 성공 |
| [superadmin 이 지정된 세션 스케줄링 조건을 조회하면 기존 세션 정보와 함께 유지됩니다](#searching_details-session-scheduling-conditions-are-preserved-when-configured) | 성공 |
| [superadmin 이 미설정인 세션 스케줄링 조건을 조회하면 기존 세션 정보와 함께 유지됩니다](#searching_details-session-scheduling-conditions-are-preserved-when-unset) | 성공 |
| [필터 없는 전체 조회는 superadmin 역할로만 열리므로, 아무 권한도 받지 않은 사용자는 역할 부족으로 거부됩니다](#session-a-user-granted-nothing-may-not-search-sessions) | 거부 |

**partial_bulk_terminate**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 종료된 것 없이 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_terminating-a-user-granted-nothing-terminates-none) | 성공 |
| [프로젝트 범위에서 세션 soft delete 권한을 받은 사용자가 그 프로젝트의 대기 세션을 종료하면, 취소됨으로 처리된 목록에 옵니다](#partial_bulk_terminating-a-user-granted-session-soft-delete-in-the-project-terminates-its-session) | 성공 |
| [superadmin 이 대기 세션과 없는 id 하나를 한 번에 종료하면, 대기 세션은 취소됨, 없는 id 는 건너뜀으로 처리된 목록에 옵니다](#partial_bulk_terminating-terminating-several-skips-the-missing-one) | 성공 |

**terminate**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 대기 세션을 종료하면, 취소된 목록에 옵니다](#terminating-a-superadmin-terminates-a-pending-session) | 성공 |
| [아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 호출 전체가 거부됩니다](#terminating-a-user-granted-nothing-may-not-terminate) | 거부 |

### admin_search

<a id="session-a-scenario-that-laid-no-session-finds-none"></a>

#### [a-scenario-that-laid-no-session-finds-none](/tests/scenario/bai_scenario/manager/session/test_session.py): pass

세션을 하나도 미리 저장하지 않은 상태에서 superadmin 이 조회하면, 응답은 비어 있습니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SessionAdapter.admin_search: user-1이 필터 없이 전체를 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching_details-session-scheduling-conditions-are-preserved-when-configured"></a>

#### [session-scheduling-conditions-are-preserved-when-configured](/tests/scenario/bai_scenario/manager/session/test_searching_details.py): pass

superadmin 이 지정된 세션 스케줄링 조건을 조회하면 기존 세션 정보와 함께 유지됩니다

Given

- 세션 그룹, designated_agent_ids, requested_starts_at 세 값이 지정된 세션과 superadmin
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 그룹 session-group-1: 가능하면 세션들을 서로 다른 에이전트에 배치합니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-2: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 세션 session-1: 세션 그룹, requested_starts_at 을 지정한 대기 세션
  - 세션 session-1: 지정 에이전트 하나를 갖습니다
  - 세션 session-1: 지정 에이전트 하나를 갖습니다

When

- SessionAdapter.admin_search: user-2이 필터 없이 전체를 조회합니다

Then

- 스케줄링 조건을 포함한 세션 정보 전체가 저장된 그대로 반환됩니다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_details-session-scheduling-conditions-are-preserved-when-unset"></a>

#### [session-scheduling-conditions-are-preserved-when-unset](/tests/scenario/bai_scenario/manager/session/test_searching_details.py): pass

superadmin 이 미설정인 세션 스케줄링 조건을 조회하면 기존 세션 정보와 함께 유지됩니다

Given

- 세션 그룹, designated_agent_ids, requested_starts_at 세 값이 미설정인 세션과 superadmin
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다

When

- SessionAdapter.admin_search: user-2이 필터 없이 전체를 조회합니다

Then

- 스케줄링 조건을 포함한 세션 정보 전체가 저장된 그대로 반환됩니다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="session-a-user-granted-nothing-may-not-search-sessions"></a>

#### [a-user-granted-nothing-may-not-search-sessions](/tests/scenario/bai_scenario/manager/session/test_session.py): pass

필터 없는 전체 조회는 superadmin 역할로만 열리므로, 아무 권한도 받지 않은 사용자는 역할 부족으로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SessionAdapter.admin_search: user-1이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### partial_bulk_terminate

<a id="partial_bulk_terminating-a-user-granted-nothing-terminates-none"></a>

#### [a-user-granted-nothing-terminates-none](/tests/scenario/bai_scenario/manager/session/test_partial_bulk_terminating.py): pass

아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 종료된 것 없이 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 대기 세션 하나와 아무 권한도 받지 않은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다

When

- SessionAdapter.partial_bulk_terminate: user-2이 대기 세션를 한 번에 종료합니다

Then

- 종료된 세션 없이, 대상이 권한이 없다는 이유로 실패 목록에 옵니다
  - successes = []
  - failed count = 1
  - failed[0].id: 대기 세션의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_terminating-a-user-granted-session-soft-delete-in-the-project-terminates-its-session"></a>

#### [a-user-granted-session-soft-delete-in-the-project-terminates-its-session](/tests/scenario/bai_scenario/manager/session/test_partial_bulk_terminating.py): pass

프로젝트 범위에서 세션 soft delete 권한을 받은 사용자가 그 프로젝트의 대기 세션을 종료하면, 취소됨으로 처리된 목록에 옵니다

Given

- 대기 세션 하나와 그 프로젝트 범위에서 세션 soft delete 권한을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다
  - 프로젝트 범위의 세션 soft delete 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-terminator-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-terminator-1: session 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 session-terminator-1 보유

When

- SessionAdapter.partial_bulk_terminate: user-2이 대기 세션를 한 번에 종료합니다

Then

- 대기 세션이 취소됨으로 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 1
  - failed = []
  - successes[0].id: 대기 세션의 id 와 같다
  - successes[0].status = <SessionTerminationStatusEnum.CANCELLED: 'cancelled'>

<a id="partial_bulk_terminating-terminating-several-skips-the-missing-one"></a>

#### [terminating-several-skips-the-missing-one](/tests/scenario/bai_scenario/manager/session/test_partial_bulk_terminating.py): pass

superadmin 이 대기 세션과 없는 id 하나를 한 번에 종료하면, 대기 세션은 취소됨, 없는 id 는 건너뜀으로 처리된 목록에 옵니다

Given

- 대기 세션 하나와 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다

When

- SessionAdapter.partial_bulk_terminate: user-2이 대기 세션과 없는 id 하나를 한 번에 종료합니다

Then

- 대기 세션은 취소됨, 없는 id 는 건너뜀으로 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].id: 대기 세션의 id 와 같다
  - successes[0].status = <SessionTerminationStatusEnum.CANCELLED: 'cancelled'>
  - successes[1].id: 요청에 넣은 없는 id 와 같다
  - successes[1].status = <SessionTerminationStatusEnum.SKIPPED: 'skipped'>

### terminate

<a id="terminating-a-superadmin-terminates-a-pending-session"></a>

#### [a-superadmin-terminates-a-pending-session](/tests/scenario/bai_scenario/manager/session/test_terminating.py): pass

superadmin 이 대기 세션을 종료하면, 취소된 목록에 옵니다

Given

- 대기 세션 하나와 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다

When

- SessionAdapter.terminate: user-2이 대기 세션을 종료합니다

Then

- 대기 세션이 취소된 목록에 오고, 나머지 목록은 비어 있습니다
  - cancelled count = 1
  - terminating = []
  - force_terminated = []
  - skipped = []
  - cancelled[0]: 대기 세션의 id 와 같다

<a id="terminating-a-user-granted-nothing-may-not-terminate"></a>

#### [a-user-granted-nothing-may-not-terminate](/tests/scenario/bai_scenario/manager/session/test_terminating.py): pass

아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 호출 전체가 거부됩니다

Given

- 대기 세션 하나와 아무 권한도 받지 않은 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키페어 하나를 더 갖습니다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다립니다

When

- SessionAdapter.terminate: user-2이 대기 세션을 종료합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

