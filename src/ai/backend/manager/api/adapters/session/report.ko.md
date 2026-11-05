## session

[배경](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session/adapter.py)

시나리오: 미완성 2 / 30

- ops 구성 (7)
  - batch_load_kernel_group_environs_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_kernel_group_resource_slots_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_kernel_groups_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_main_kernel_groups: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search_kernel_group_environs: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search_kernel_group_resource_slots: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search_kernel_groups: 대표 성공 ✓ · 대표 거부 ✓
- ops + 직접 구현 (10)
  - admin_search: 성공 있음 3 · 거부 있음 1 (global_searcher_ops, partial_bulk)
  - admin_search_kernels: 성공 있음 1 · 거부 있음 1 (atomic_bulk_field, global_searcher_ops)
  - batch_load_by_ids: 성공 있음 1 · 거부 있음 1 (partial_bulk, partial_bulk_get_ops)
  - batch_load_kernels_by_ids: 성공 있음 1 · 거부 있음 1 (atomic_bulk_field, partial_bulk_get_ops)
  - gql_search_by_project: 성공 있음 1 · 거부 있음 1 (partial_bulk, scoped_search_ops)
  - project_search: 성공 있음 1 · 거부 있음 1 (partial_bulk, scoped_search_ops)
  - scoped_search: 성공 있음 1 · 거부 있음 1 (partial_bulk, scoped_search_ops)
  - search_kernels_by_agent: 성공 있음 1 · 거부 있음 1 (atomic_bulk_field, global_searcher_ops)
  - search_kernels_by_session: 성공 있음 1 · 거부 있음 1 (atomic_bulk_field, atomic_bulk_scoped_search_ops)
  - search_sessions_by_agent: 성공 있음 1 · 거부 있음 1 (global_searcher_ops, partial_bulk)
- 직접 구현 (13)
  - batch_resource_allocation_by_kernel: 성공 있음 1 · 거부 있음 1 (atomic_bulk_field)
  - batch_resource_allocation_by_session: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - compute_schedule: 성공 있음 1 · 거부 있음 2 (single_entity)
  - enqueue: 성공 있음 1 · 거부 있음 1 (partial_bulk, scope)
  - exclude_idle_checks: 성공 있음 2 · 거부 있음 1 (legacy_partial_bulk)
  - get: 성공 있음 1 · 거부 있음 1 (partial_bulk, single_entity)
  - get_logs: 성공 있음 1 · 거부 있음 1 (single_entity)
  - include_idle_checks: 성공 있음 2 · 거부 있음 1 (legacy_partial_bulk)
  - partial_bulk_terminate: 성공 있음 3 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - shutdown_service: 성공 있음 1 · 거부 있음 1 (single_entity)
  - start_service: 성공 없음 · 거부 있음 2 (single_entity): SCENARIO-GAP
  - terminate: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - update: 성공 있음 1 · 거부 있음 2 (partial_bulk, single_entity)

**batch_load_kernel_group_environs_by_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널 그룹의 환경 변수를 id 로 일괄 조회하면, 저장된 그대로 반환됩니다](#reading-a-kernel-group-environ-is-batch-loaded-by-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 커널 그룹의 환경 변수를 id 로 일괄 조회하면, 권한 부족으로 거부됩니다](#reading-a-kernel-group-environ-is-batch-loaded-by-id-nothing) | 거부 |

**batch_load_kernel_group_resource_slots_by_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널 그룹의 자원 슬롯을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다](#reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 커널 그룹의 자원 슬롯을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다](#reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-nothing) | 거부 |

**batch_load_kernel_groups_by_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널 그룹을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다](#reading-a-kernel-group-is-batch-loaded-by-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 커널 그룹을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다](#reading-a-kernel-group-is-batch-loaded-by-id-nothing) | 거부 |

**batch_load_main_kernel_groups**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 주 커널 그룹을 일괄 조회하면, 저장된 그대로 반환됩니다](#reading-a-main-kernel-group-is-batch-loaded-by-session-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션의 주 커널 그룹을 일괄 조회하면, 권한 부족으로 거부됩니다](#reading-a-main-kernel-group-is-batch-loaded-by-session-id-nothing) | 거부 |

**scoped_search_kernel_group_environs**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션 커널 그룹의 환경 변수를 조회하면, 저장된 환경 변수 전체가 반환됩니다](#searching-the-kernel-group-environs-of-a-session-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션 커널 그룹의 환경 변수를 조회하면, 권한 부족으로 거부됩니다](#searching-the-kernel-group-environs-of-a-session-nothing) | 거부 |

**scoped_search_kernel_group_resource_slots**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션 커널 그룹의 자원 슬롯을 조회하면, 저장된 자원 슬롯 전체가 반환됩니다](#searching-the-kernel-group-resource-slots-of-a-session-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션 커널 그룹의 자원 슬롯을 조회하면, 권한 부족으로 거부됩니다](#searching-the-kernel-group-resource-slots-of-a-session-nothing) | 거부 |

**scoped_search_kernel_groups**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 커널 그룹을 조회하면, 저장된 커널 그룹 전체가 반환됩니다](#searching-the-kernel-groups-of-a-session-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션의 커널 그룹을 조회하면, 권한 부족으로 거부됩니다](#searching-the-kernel-groups-of-a-session-nothing) | 거부 |

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [세션을 하나도 미리 저장하지 않은 상태에서 superadmin 이 조회하면, 응답은 비어 있습니다](#session-a-scenario-that-laid-no-session-finds-none) | 성공 |
| [superadmin 이 지정된 세션 스케줄링 조건을 조회하면 기존 세션 정보와 함께 유지됩니다](#searching_details-session-scheduling-conditions-are-preserved-when-configured) | 성공 |
| [superadmin 이 미설정인 세션 스케줄링 조건을 조회하면 기존 세션 정보와 함께 유지됩니다](#searching_details-session-scheduling-conditions-are-preserved-when-unset) | 성공 |
| [필터 없는 전체 조회는 superadmin 역할로만 열리므로, 아무 권한도 받지 않은 사용자는 역할 부족으로 거부됩니다](#session-a-user-granted-nothing-may-not-search-sessions) | 거부 |

**admin_search_kernels**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 superadmin 이 커널을 전체 검색하면, 저장된 커널 전체가 반환됩니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다](#searching-superadmin-searches-every-kernel) | 성공 |
| [superadmin 이 아닌 사용자가 커널을 전체 검색하면, 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-a-superadmin-searches-every-kernel) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다](#reading-a-session-is-batch-loaded-by-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다](#reading-a-session-is-batch-loaded-by-id-nothing) | 거부 |

**batch_load_kernels_by_ids**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다](#reading-a-kernel-is-batch-loaded-by-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 커널을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다](#reading-a-kernel-is-batch-loaded-by-id-nothing) | 거부 |

**gql_search_by_project**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 조회하면, 저장된 세션 전체가 반환됩니다](#searching-gql_search_by_project-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 부족으로 거부됩니다](#searching-gql_search_by_project-nothing) | 거부 |

**project_search**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 조회하면, 저장된 세션 전체가 반환됩니다](#searching-project_search-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 부족으로 거부됩니다](#searching-project_search-nothing) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 조회하면, 저장된 세션 전체가 반환됩니다](#searching-scoped_search-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 부족으로 거부됩니다](#searching-scoped_search-nothing) | 거부 |

**search_kernels_by_agent**

| 시나리오 | 판정 |
|---|---|
| [아무 커널도 실행하지 않는 에이전트로 커널을 검색하면, 빈 답이 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다](#agent_searching-an-agent-that-runs-no-kernel-superadmin) | 성공 |
| [superadmin 이 아닌 사용자가 에이전트로 커널을 검색하면, 역할 부족으로 거부됩니다](#agent_searching-an-agent-that-runs-no-kernel-a-user-who-is-not-a-superadmin) | 거부 |

**search_kernels_by_session**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 커널을 조회하면, 저장된 커널 전체가 반환됩니다](#searching-the-kernels-of-a-session-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션의 커널을 조회하면, 권한 부족으로 거부됩니다](#searching-the-kernels-of-a-session-nothing) | 거부 |

**search_sessions_by_agent**

| 시나리오 | 판정 |
|---|---|
| [아무 세션도 실행하지 않는 에이전트로 세션을 검색하면, 빈 답이 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다](#agent_searching-an-agent-that-runs-no-session-superadmin) | 성공 |
| [superadmin 이 아닌 사용자가 에이전트로 세션을 검색하면, 역할 부족으로 거부됩니다](#agent_searching-an-agent-that-runs-no-session-a-user-who-is-not-a-superadmin) | 거부 |

**batch_resource_allocation_by_kernel**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널의 자원 할당을 일괄 조회하면, 요청한 양만큼의 할당이 반환됩니다](#loading_allocations-a-kernel-allocation-is-batch-loaded-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 커널의 자원 할당을 일괄 조회하면, 권한 부족으로 거부됩니다](#loading_allocations-a-kernel-allocation-is-batch-loaded-nothing) | 거부 |

**batch_resource_allocation_by_session**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 자원 할당을 일괄 조회하면, 요청한 양만큼의 할당이 반환됩니다](#loading_allocations-a-session-allocation-is-batch-loaded-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션의 자원 할당을 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#loading_allocations-a-session-allocation-is-batch-loaded-nothing) | 거부 |

**compute_schedule**

| 시나리오 | 판정 |
|---|---|
| [그 자원 그룹을 읽을 수 있는 사용자가 요구한 슬롯을 감당하는 에이전트가 있는 그룹에 커널이 들어갈 수 있는지 계산하면, 들어간다고 답합니다](#computing_schedule-computing-whether-a-kernel-fits-granted-with-an-agent) | 성공 |
| [그 자원 그룹을 읽을 권한이 없는 사용자가 커널이 들어갈 수 있는지 계산하면, 권한 부족으로 거부됩니다](#computing_schedule-computing-whether-a-kernel-fits-granted-nothing-with-an-agent) | 거부 |
| [그 자원 그룹을 읽을 수 있는 사용자가 에이전트가 하나도 없는 그룹에 커널이 들어갈 수 있는지 계산하면, 에이전트가 없어서 거부됩니다](#computing_schedule-computing-whether-a-kernel-fits-granted-without-an-agent) | 거부 |

**enqueue**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션을 만들 수 있는 사용자가 세션을 만들면, 대기 상태의 세션 전체가 반환됩니다](#enqueueing-creating-a-session-granted) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트에 세션을 만들려 하면, 권한 부족으로 거부됩니다](#enqueueing-creating-a-session-granted-nothing) | 거부 |

**exclude_idle_checks**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 수정 권한을 받은 사용자가 없는 검사기로 세션을 빼려 하면, 그 쌍이 실패 목록에 옵니다](#idle_checking-excluding-a-pair-from-idle-checks-granted-a-checker-that-is-not-there) | 성공 |
| [그 프로젝트에서 세션 수정 권한을 받은 사용자가 세션과 검사기 한 쌍을 빼면, 그 쌍이 빠졌다고 돌아옵니다](#idle_checking-excluding-a-pair-from-idle-checks-granted-the-laid-pair) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션을 유휴 검사에서 빼려 하면, 권한 부족으로 거부됩니다](#idle_checking-excluding-a-pair-from-idle-checks-granted-nothing-the-laid-pair) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션을 id 로 읽하면, 저장된 그대로 반환됩니다](#reading-a-session-is-read-by-id-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션을 id 로 읽하면, 권한 부족으로 거부됩니다](#reading-a-session-is-read-by-id-nothing) | 거부 |

**get_logs**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 컨테이너 로그를 읽으면, 에이전트가 준 로그가 반환됩니다](#logs_and_services-the-container-log-of-a-session-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션의 컨테이너 로그를 읽으면, 권한 부족으로 거부됩니다](#logs_and_services-the-container-log-of-a-session-nothing) | 거부 |

**include_idle_checks**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 수정 권한을 받은 사용자가 없는 검사기로 세션을 다시 넣으려 하면, 그 쌍이 실패 목록에 옵니다](#idle_checking-including-a-pair-in-idle-checks-granted-a-checker-that-is-not-there) | 성공 |
| [그 프로젝트에서 세션 수정 권한을 받은 사용자가 세션과 검사기 한 쌍을 다시 넣으면, 그 쌍이 들어왔다고 돌아옵니다](#idle_checking-including-a-pair-in-idle-checks-granted-the-laid-pair) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션을 유휴 검사에 다시 넣으려 하면, 권한 부족으로 거부됩니다](#idle_checking-including-a-pair-in-idle-checks-granted-nothing-the-laid-pair) | 거부 |

**partial_bulk_terminate**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 종료된 것 없이 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_terminating-a-user-granted-nothing-terminates-none) | 성공 |
| [프로젝트 범위에서 세션 soft delete 권한을 받은 사용자가 그 프로젝트의 대기 세션을 종료하면, 취소됨으로 처리된 목록에 옵니다](#partial_bulk_terminating-a-user-granted-session-soft-delete-in-the-project-terminates-its-session) | 성공 |
| [superadmin 이 대기 세션과 없는 id 하나를 한 번에 종료하면, 대기 세션은 취소됨, 없는 id 는 건너뜀으로 처리된 목록에 옵니다](#partial_bulk_terminating-terminating-several-skips-the-missing-one) | 성공 |

**shutdown_service**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 soft delete 권한을 받은 사용자가 세션의 서비스를 종료하면, 호출이 아무것도 반환하지 않고 끝납니다](#logs_and_services-shutting-down-a-service-granted) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션의 서비스를 종료하려 하면, 권한 부족으로 거부됩니다](#logs_and_services-shutting-down-a-service-granted-nothing) | 거부 |

**start_service**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 생성 권한을 받은 사용자가 프록시 주소가 없는 자원 그룹의 세션에서 서비스를 시작하려 하면, 프록시가 없어서 거부됩니다](#logs_and_services-starting-a-service-granted) | 거부 |
| [아무 권한도 받지 않은 사용자가 세션의 서비스를 시작하려 하면, 권한 부족으로 거부됩니다](#logs_and_services-starting-a-service-granted-nothing) | 거부 |

**terminate**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 대기 세션을 종료하면, 취소된 목록에 옵니다](#terminating-a-superadmin-terminates-a-pending-session) | 성공 |
| [아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 호출 전체가 거부됩니다](#terminating-a-user-granted-nothing-may-not-terminate) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 세션 읽기 권한을 받은 사용자가 바꿀 값 없이 세션을 수정 요청하면, 현재 세션 전체가 반환됩니다](#updating-a-session-update-with-no-field-project) | 성공 |
| [아무 권한도 받지 않은 사용자가 바꿀 값 없이 세션을 수정 요청하면, 권한 부족으로 거부됩니다](#updating-a-session-update-with-no-field-nothing) | 거부 |
| [그 프로젝트에서 세션 수정 권한을 받은 사용자가 아직 실행 중이 아닌 세션의 이름을 바꾸려 하면, 실행 중이 아니라서 거부됩니다](#updating-renaming-a-session-that-is-not-running-is-refused) | 거부 |

### batch_load_kernel_group_environs_by_ids

<a id="reading-a-kernel-group-environ-is-batch-loaded-by-id-project"></a>

#### [a-kernel-group-environ-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널 그룹의 환경 변수를 id 로 일괄 조회하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_load_kernel_group_environs_by_ids: user-2이 session-1 세션 커널 그룹의 환경 변수를 id 로 일괄 조회합니다

Then

- 환경 변수 하나가 저장된 그대로 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 환경 변수 행의 전체 정보와 같다

<a id="reading-a-kernel-group-environ-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-group-environ-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 커널 그룹의 환경 변수를 id 로 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_load_kernel_group_environs_by_ids: user-2이 session-1 세션 커널 그룹의 환경 변수를 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_kernel_group_resource_slots_by_ids

<a id="reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-project"></a>

#### [a-kernel-group-resource-slot-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널 그룹의 자원 슬롯을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_load_kernel_group_resource_slots_by_ids: user-2이 session-1 세션 커널 그룹의 자원 슬롯을 id 로 일괄 조회합니다

Then

- 자원 슬롯 행 하나가 저장된 그대로 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 자원 슬롯 행의 전체 정보와 같다

<a id="reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-group-resource-slot-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 커널 그룹의 자원 슬롯을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_load_kernel_group_resource_slots_by_ids: user-2이 session-1 세션 커널 그룹의 자원 슬롯을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_kernel_groups_by_ids

<a id="reading-a-kernel-group-is-batch-loaded-by-id-project"></a>

#### [a-kernel-group-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널 그룹을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_load_kernel_groups_by_ids: user-2이 session-1 세션의 커널 그룹을 id 로 일괄 조회합니다

Then

- 커널 그룹 하나가 저장된 그대로 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 커널 그룹의 전체 정보와 같다

<a id="reading-a-kernel-group-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-group-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 커널 그룹을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_load_kernel_groups_by_ids: user-2이 session-1 세션의 커널 그룹을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_main_kernel_groups

<a id="reading-a-main-kernel-group-is-batch-loaded-by-session-id-project"></a>

#### [a-main-kernel-group-is-batch-loaded-by-session-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 주 커널 그룹을 일괄 조회하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_load_main_kernel_groups: user-2이 session-1 세션의 주 커널 그룹을 세션 id 로 일괄 조회합니다

Then

- 세션의 주 커널 그룹이 저장된 그대로 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 커널 그룹의 전체 정보와 같다

<a id="reading-a-main-kernel-group-is-batch-loaded-by-session-id-nothing"></a>

#### [a-main-kernel-group-is-batch-loaded-by-session-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 세션의 주 커널 그룹을 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_load_main_kernel_groups: user-2이 session-1 세션의 주 커널 그룹을 세션 id 로 일괄 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search_kernel_group_environs

<a id="searching-the-kernel-group-environs-of-a-session-project"></a>

#### [the-kernel-group-environs-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션 커널 그룹의 환경 변수를 조회하면, 저장된 환경 변수 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.scoped_search_kernel_group_environs: user-2이 session-1 세션 커널 그룹의 환경 변수를 조회합니다

Then

- 세션 커널 그룹의 환경 변수 전체가 저장된 그대로 반환됩니다
  - items: 저장된 환경 변수 행의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernel-group-environs-of-a-session-nothing"></a>

#### [the-kernel-group-environs-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 세션 커널 그룹의 환경 변수를 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.scoped_search_kernel_group_environs: user-2이 session-1 세션 커널 그룹의 환경 변수를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search_kernel_group_resource_slots

<a id="searching-the-kernel-group-resource-slots-of-a-session-project"></a>

#### [the-kernel-group-resource-slots-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션 커널 그룹의 자원 슬롯을 조회하면, 저장된 자원 슬롯 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.scoped_search_kernel_group_resource_slots: user-2이 session-1 세션 커널 그룹의 자원 슬롯을 조회합니다

Then

- 세션 커널 그룹의 자원 슬롯 전체가 저장된 그대로 반환됩니다
  - items: 저장된 자원 슬롯 행의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernel-group-resource-slots-of-a-session-nothing"></a>

#### [the-kernel-group-resource-slots-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 세션 커널 그룹의 자원 슬롯을 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.scoped_search_kernel_group_resource_slots: user-2이 session-1 세션 커널 그룹의 자원 슬롯을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search_kernel_groups

<a id="searching-the-kernel-groups-of-a-session-project"></a>

#### [the-kernel-groups-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 커널 그룹을 조회하면, 저장된 커널 그룹 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.scoped_search_kernel_groups: user-2이 session-1 세션의 커널 그룹을 조회합니다

Then

- 세션의 커널 그룹 전체가 저장된 그대로 반환됩니다
  - items: 저장된 커널 그룹의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernel-groups-of-a-session-nothing"></a>

#### [the-kernel-groups-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 세션의 커널 그룹을 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.scoped_search_kernel_groups: user-2이 session-1 세션의 커널 그룹을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

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

### admin_search_kernels

<a id="searching-superadmin-searches-every-kernel"></a>

#### [superadmin-searches-every-kernel](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 superadmin 이 커널을 전체 검색하면, 저장된 커널 전체가 반환됩니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.admin_search_kernels: user-2이 필터 없이 모든 커널을 조회합니다

Then

- 세션의 커널 전체가 저장된 그대로 반환됩니다
  - items: 저장된 커널의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-a-superadmin-searches-every-kernel"></a>

#### [a-user-who-is-not-a-superadmin-searches-every-kernel](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

superadmin 이 아닌 사용자가 커널을 전체 검색하면, 역할 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.admin_search_kernels: user-2이 필터 없이 모든 커널을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-a-session-is-batch-loaded-by-id-project"></a>

#### [a-session-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_load_by_ids: user-2이 session-1 세션을 id 로 일괄 조회합니다

Then

- 세션 하나가 저장된 그대로 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 세션의 전체 정보와 같다

<a id="reading-a-session-is-batch-loaded-by-id-nothing"></a>

#### [a-session-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 세션을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_load_by_ids: user-2이 session-1 세션을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_kernels_by_ids

<a id="reading-a-kernel-is-batch-loaded-by-id-project"></a>

#### [a-kernel-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널을 id 로 일괄 조회하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_load_kernels_by_ids: user-2이 session-1 세션의 커널을 id 로 일괄 조회합니다

Then

- 커널 하나가 저장된 그대로 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 커널의 전체 정보와 같다

<a id="reading-a-kernel-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 커널을 id 로 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_load_kernels_by_ids: user-2이 session-1 세션의 커널을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### gql_search_by_project

<a id="searching-gql_search_by_project-project"></a>

#### [gql_search_by_project-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 조회하면, 저장된 세션 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.gql_search_by_project: user-2이 team-1 프로젝트의 세션을 조회합니다

Then

- 그 프로젝트의 세션 전체가 저장된 그대로 반환됩니다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-gql_search_by_project-nothing"></a>

#### [gql_search_by_project-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.gql_search_by_project: user-2이 team-1 프로젝트의 세션을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### project_search

<a id="searching-project_search-project"></a>

#### [project_search-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 조회하면, 저장된 세션 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.project_search: user-2이 team-1 프로젝트 id 로 세션을 조회합니다

Then

- 그 프로젝트의 세션 전체가 저장된 그대로 반환됩니다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-project_search-nothing"></a>

#### [project_search-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.project_search: user-2이 team-1 프로젝트 id 로 세션을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="searching-scoped_search-project"></a>

#### [scoped_search-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 조회하면, 저장된 세션 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.scoped_search: user-2이 team-1 프로젝트 스코프에서 세션을 조회합니다

Then

- 그 프로젝트의 세션 전체가 저장된 그대로 반환됩니다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-scoped_search-nothing"></a>

#### [scoped_search-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.scoped_search: user-2이 team-1 프로젝트 스코프에서 세션을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_kernels_by_agent

<a id="agent_searching-an-agent-that-runs-no-kernel-superadmin"></a>

#### [an-agent-that-runs-no-kernel-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

아무 커널도 실행하지 않는 에이전트로 커널을 검색하면, 빈 답이 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.search_kernels_by_agent: user-2이 에이전트 하나가 실행하는 커널을 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="agent_searching-an-agent-that-runs-no-kernel-a-user-who-is-not-a-superadmin"></a>

#### [an-agent-that-runs-no-kernel-a-user-who-is-not-a-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

superadmin 이 아닌 사용자가 에이전트로 커널을 검색하면, 역할 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.search_kernels_by_agent: user-2이 에이전트 하나가 실행하는 커널을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### search_kernels_by_session

<a id="searching-the-kernels-of-a-session-project"></a>

#### [the-kernels-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 커널을 조회하면, 저장된 커널 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.search_kernels_by_session: user-2이 session-1 세션의 커널을 조회합니다

Then

- 세션의 커널 전체가 저장된 그대로 반환됩니다
  - items: 저장된 커널의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernels-of-a-session-nothing"></a>

#### [the-kernels-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

아무 권한도 받지 않은 사용자가 세션의 커널을 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.search_kernels_by_session: user-2이 session-1 세션의 커널을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_sessions_by_agent

<a id="agent_searching-an-agent-that-runs-no-session-superadmin"></a>

#### [an-agent-that-runs-no-session-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

아무 세션도 실행하지 않는 에이전트로 세션을 검색하면, 빈 답이 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.search_sessions_by_agent: user-2이 에이전트 하나가 실행하는 세션을 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="agent_searching-an-agent-that-runs-no-session-a-user-who-is-not-a-superadmin"></a>

#### [an-agent-that-runs-no-session-a-user-who-is-not-a-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

superadmin 이 아닌 사용자가 에이전트로 세션을 검색하면, 역할 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.search_sessions_by_agent: user-2이 에이전트 하나가 실행하는 세션을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_resource_allocation_by_kernel

<a id="loading_allocations-a-kernel-allocation-is-batch-loaded-project"></a>

#### [a-kernel-allocation-is-batch-loaded-project](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널의 자원 할당을 일괄 조회하면, 요청한 양만큼의 할당이 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_resource_allocation_by_kernel: user-2이 session-1 세션 커널의 자원 할당을 id 로 일괄 조회합니다

Then

- 그 커널의 자원 할당이 요청한 양만큼 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 자원 할당와 같다

<a id="loading_allocations-a-kernel-allocation-is-batch-loaded-nothing"></a>

#### [a-kernel-allocation-is-batch-loaded-nothing](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

아무 권한도 받지 않은 사용자가 커널의 자원 할당을 일괄 조회하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_resource_allocation_by_kernel: user-2이 session-1 세션 커널의 자원 할당을 id 로 일괄 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### batch_resource_allocation_by_session

<a id="loading_allocations-a-session-allocation-is-batch-loaded-project"></a>

#### [a-session-allocation-is-batch-loaded-project](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 자원 할당을 일괄 조회하면, 요청한 양만큼의 할당이 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.batch_resource_allocation_by_session: user-2이 session-1 세션의 자원 할당을 id 로 일괄 조회합니다

Then

- 그 세션의 자원 할당이 요청한 양만큼 한 항목으로 반환됩니다
  - length = 1
  - [0]: 저장된 자원 할당와 같다

<a id="loading_allocations-a-session-allocation-is-batch-loaded-nothing"></a>

#### [a-session-allocation-is-batch-loaded-nothing](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

아무 권한도 받지 않은 사용자가 세션의 자원 할당을 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.batch_resource_allocation_by_session: user-2이 session-1 세션의 자원 할당을 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### compute_schedule

<a id="computing_schedule-computing-whether-a-kernel-fits-granted-with-an-agent"></a>

#### [computing-whether-a-kernel-fits-granted-with-an-agent](/tests/scenario/bai_scenario/manager/session/test_computing_schedule.py): pass

그 자원 그룹을 읽을 수 있는 사용자가 요구한 슬롯을 감당하는 에이전트가 있는 그룹에 커널이 들어갈 수 있는지 계산하면, 들어간다고 답합니다

Given

- 용량을 보고한 에이전트 하나를 가진 자원 그룹 하나와, 그 그룹을 읽을 수 있는 사용자 한 명
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
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-1: cpu 슬롯 용량 8 보고, 0 사용 중
  - 에이전트 agent-1: mem 슬롯 용량 34359738368 보고, 0 사용 중
  - 리소스 그룹 범위의 READ 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-2: 역할 group-role-1 보유

When

- SessionAdapter.compute_schedule: user-2이 그 자원 그룹에 cpu 와 mem 을 요구하는 커널이 들어갈 수 있는지 계산합니다

Then

- 요구한 슬롯과 아키텍처가 그대로 돌아오고, 커널 하나가 들어간다고 답합니다
  - results count = 1
  - requested_slots: cpu 1, mem 2147483648 를 요구한 슬롯
  - requested_architecture = 'x86_64'
  - success = True
  - reason_hint = None

<a id="computing_schedule-computing-whether-a-kernel-fits-granted-nothing-with-an-agent"></a>

#### [computing-whether-a-kernel-fits-granted-nothing-with-an-agent](/tests/scenario/bai_scenario/manager/session/test_computing_schedule.py): pass

그 자원 그룹을 읽을 권한이 없는 사용자가 커널이 들어갈 수 있는지 계산하면, 권한 부족으로 거부됩니다

Given

- 용량을 보고한 에이전트 하나를 가진 자원 그룹 하나와, 아무 권한도 받지 않은 사용자 한 명
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
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-1: cpu 슬롯 용량 8 보고, 0 사용 중
  - 에이전트 agent-1: mem 슬롯 용량 34359738368 보고, 0 사용 중

When

- SessionAdapter.compute_schedule: user-2이 그 자원 그룹에 cpu 와 mem 을 요구하는 커널이 들어갈 수 있는지 계산합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="computing_schedule-computing-whether-a-kernel-fits-granted-without-an-agent"></a>

#### [computing-whether-a-kernel-fits-granted-without-an-agent](/tests/scenario/bai_scenario/manager/session/test_computing_schedule.py): pass

그 자원 그룹을 읽을 수 있는 사용자가 에이전트가 하나도 없는 그룹에 커널이 들어갈 수 있는지 계산하면, 에이전트가 없어서 거부됩니다

Given

- 에이전트 없음를 가진 자원 그룹 하나와, 그 그룹을 읽을 수 있는 사용자 한 명
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
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 리소스 그룹 범위의 READ 역할을 받은 사용자 준비
    - 역할 group-role-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 group-role-1: resource_group 전체에 READ 허용
    - 일반 사용자 user-2: 역할 group-role-1 보유

When

- SessionAdapter.compute_schedule: user-2이 그 자원 그룹에 cpu 와 mem 을 요구하는 커널이 들어갈 수 있는지 계산합니다

Then

- 거부됩니다
  - 거부: NoAgentsInResourceGroupError

### enqueue

<a id="enqueueing-creating-a-session-granted"></a>

#### [creating-a-session-granted](/tests/scenario/bai_scenario/manager/session/test_enqueueing.py): pass

그 프로젝트에서 세션을 만들 수 있는 사용자가 세션을 만들면, 대기 상태의 세션 전체가 반환됩니다

Given

- 요구할 슬롯을 감당하는 에이전트가 있는 자원 그룹과 이미지, 그리고 그 프로젝트에서 세션을 만들 수 있는 사용자 한 명
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
  - 프로젝트 team-1 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-1: cpu 슬롯 용량 8 보고, 0 사용 중
  - 에이전트 agent-1: mem 슬롯 용량 34359738368 보고, 0 사용 중
  - 그 프로젝트에서 세션을 만들고 읽을 수 있는 사용자 준비
    - 역할 session-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-owner-1: session 전체에 CREATE 허용
    - 역할 session-owner-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-owner-1 보유

When

- SessionAdapter.enqueue: user-2이 그 프로젝트에 created-session 세션을 만듭니다

Then

- 만들어진 세션 전체가 저장된 그대로 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 그 id 와 같다
  - image_ids: 그 세션의 이미지와 같다
  - domain_name = 'home-1'
  - user_id: 요청한 사용자의 id 와 같다
  - project_id: 그 프로젝트의 id 와 같다
  - metadata.creation_id: 이 실행이 만든 비어 있지 않은 값
  - metadata.name = 'created-session'
  - metadata.session_type = 'interactive'
  - metadata.access_key = 'AKF5065012ED824071'
  - metadata.cluster_mode = 'SINGLE_NODE'
  - metadata.cluster_size = 1
  - metadata.tier = 10
  - metadata.priority = 10
  - metadata.job_priority = 0
  - metadata.is_preemptible = False
  - metadata.tag = None
  - resource.allocation: cpu 1, mem 2147483648 만큼의 할당
  - resource.resource_group_name = 'resource-group-1'
  - resource.session_group_id = None
  - resource.designated_agent_ids = None
  - lifecycle.status = 'PENDING'
  - lifecycle.result = 'undefined'
  - lifecycle.created_at: 이 실행이 쓴 시각
  - lifecycle.terminated_at = None
  - lifecycle.starts_at = None
  - lifecycle.requested_starts_at = None
  - lifecycle.batch_timeout = None
  - runtime.environ = None
  - runtime.bootstrap_script = None
  - runtime.startup_command = None
  - runtime.callback_url = None
  - network.use_host_network = False
  - network.network_type = 'volatile'
  - network.network_id = None
  - replica_id = None

<a id="enqueueing-creating-a-session-granted-nothing"></a>

#### [creating-a-session-granted-nothing](/tests/scenario/bai_scenario/manager/session/test_enqueueing.py): pass

아무 권한도 받지 않은 사용자가 프로젝트에 세션을 만들려 하면, 권한 부족으로 거부됩니다

Given

- 요구할 슬롯을 감당하는 에이전트가 있는 자원 그룹과 이미지, 그리고 아무 권한도 받지 않은 사용자 한 명
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
  - 프로젝트 team-1 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
  - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없습니다
  - 에이전트 agent-1: cpu 슬롯 용량 8 보고, 0 사용 중
  - 에이전트 agent-1: mem 슬롯 용량 34359738368 보고, 0 사용 중

When

- SessionAdapter.enqueue: user-2이 그 프로젝트에 created-session 세션을 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### exclude_idle_checks

<a id="idle_checking-excluding-a-pair-from-idle-checks-granted-a-checker-that-is-not-there"></a>

#### [excluding-a-pair-from-idle-checks-granted-a-checker-that-is-not-there](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

그 프로젝트에서 세션 수정 권한을 받은 사용자가 없는 검사기로 세션을 빼려 하면, 그 쌍이 실패 목록에 옵니다

Given

- 대기 세션 하나와 유휴 검사기 하나, 그리고 그 프로젝트에서 세션 수정 권한을 받은 사용자 한 명
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
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.exclude_idle_checks: user-2이 그 세션과 카탈로그에 없는 검사기 하나 를 유휴 검사에서 뺍니다

Then

- 어느 쌍도 빠지지 않고, 부른 그 쌍이 실패 목록에 옵니다
  - items = []
  - failed count = 1
  - failed[0].session_id: 그 세션의 id 와 같다
  - failed[0].checker_id: 부른 그 검사기의 id 와 같다
  - failed[0].message: 'Idle checker'를 담은 이유

<a id="idle_checking-excluding-a-pair-from-idle-checks-granted-the-laid-pair"></a>

#### [excluding-a-pair-from-idle-checks-granted-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

그 프로젝트에서 세션 수정 권한을 받은 사용자가 세션과 검사기 한 쌍을 빼면, 그 쌍이 빠졌다고 돌아옵니다

Given

- 대기 세션 하나와 유휴 검사기 하나, 그리고 그 프로젝트에서 세션 수정 권한을 받은 사용자 한 명
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
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.exclude_idle_checks: user-2이 그 세션과 그 검사기 를 유휴 검사에서 뺍니다

Then

- 그 쌍 하나가 빠졌다고 돌아오고, 실패는 없습니다
  - items count = 1
  - failed count = 0
  - items[0].checker_id: 그 검사기의 id 와 같다
  - items[0].session_id: 그 세션의 id 와 같다

<a id="idle_checking-excluding-a-pair-from-idle-checks-granted-nothing-the-laid-pair"></a>

#### [excluding-a-pair-from-idle-checks-granted-nothing-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

아무 권한도 받지 않은 사용자가 세션을 유휴 검사에서 빼려 하면, 권한 부족으로 거부됩니다

Given

- 대기 세션 하나와 유휴 검사기 하나, 그리고 아무 권한도 받지 않은 사용자 한 명
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
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다

When

- SessionAdapter.exclude_idle_checks: user-2이 그 세션과 그 검사기 를 유휴 검사에서 뺍니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get

<a id="reading-a-session-is-read-by-id-project"></a>

#### [a-session-is-read-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션을 id 로 읽하면, 저장된 그대로 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.get: user-2이 session-1 세션을 id 로 읽습니다

Then

- 세션 전체가 저장된 그대로 반환됩니다
  - session: 저장된 세션의 전체 정보와 같다

<a id="reading-a-session-is-read-by-id-nothing"></a>

#### [a-session-is-read-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

아무 권한도 받지 않은 사용자가 세션을 id 로 읽하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.get: user-2이 session-1 세션을 id 로 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_logs

<a id="logs_and_services-the-container-log-of-a-session-project"></a>

#### [the-container-log-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 컨테이너 로그를 읽으면, 에이전트가 준 로그가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.get_logs: user-2이 session-1 세션의 컨테이너 로그를 읽습니다

Then

- 에이전트가 준 컨테이너 로그가 그대로 반환됩니다
  - logs = 'the container log this run hands back'

<a id="logs_and_services-the-container-log-of-a-session-nothing"></a>

#### [the-container-log-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

아무 권한도 받지 않은 사용자가 세션의 컨테이너 로그를 읽으면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.get_logs: user-2이 session-1 세션의 컨테이너 로그를 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### include_idle_checks

<a id="idle_checking-including-a-pair-in-idle-checks-granted-a-checker-that-is-not-there"></a>

#### [including-a-pair-in-idle-checks-granted-a-checker-that-is-not-there](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

그 프로젝트에서 세션 수정 권한을 받은 사용자가 없는 검사기로 세션을 다시 넣으려 하면, 그 쌍이 실패 목록에 옵니다

Given

- 대기 세션 하나와 유휴 검사기 하나, 그리고 그 프로젝트에서 세션 수정 권한을 받은 사용자 한 명
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
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.include_idle_checks: user-2이 그 세션과 카탈로그에 없는 검사기 하나 를 유휴 검사에 다시 넣습니다

Then

- 어느 쌍도 다시 들어오지 않고, 부른 그 쌍이 실패 목록에 옵니다
  - items = []
  - failed count = 1
  - failed[0].session_id: 그 세션의 id 와 같다
  - failed[0].checker_id: 부른 그 검사기의 id 와 같다
  - failed[0].message: 'Idle checker'를 담은 이유

<a id="idle_checking-including-a-pair-in-idle-checks-granted-the-laid-pair"></a>

#### [including-a-pair-in-idle-checks-granted-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

그 프로젝트에서 세션 수정 권한을 받은 사용자가 세션과 검사기 한 쌍을 다시 넣으면, 그 쌍이 들어왔다고 돌아옵니다

Given

- 대기 세션 하나와 유휴 검사기 하나, 그리고 그 프로젝트에서 세션 수정 권한을 받은 사용자 한 명
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
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.include_idle_checks: user-2이 그 세션과 그 검사기 를 유휴 검사에 다시 넣습니다

Then

- 그 쌍 하나가 다시 들어왔다고 돌아오고, 실패는 없습니다
  - items count = 1
  - failed count = 0
  - items[0].checker_id: 그 검사기의 id 와 같다
  - items[0].session_id: 그 세션의 id 와 같다

<a id="idle_checking-including-a-pair-in-idle-checks-granted-nothing-the-laid-pair"></a>

#### [including-a-pair-in-idle-checks-granted-nothing-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

아무 권한도 받지 않은 사용자가 세션을 유휴 검사에 다시 넣으려 하면, 권한 부족으로 거부됩니다

Given

- 대기 세션 하나와 유휴 검사기 하나, 그리고 아무 권한도 받지 않은 사용자 한 명
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
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다

When

- SessionAdapter.include_idle_checks: user-2이 그 세션과 그 검사기 를 유휴 검사에 다시 넣습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

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

### shutdown_service

<a id="logs_and_services-shutting-down-a-service-granted"></a>

#### [shutting-down-a-service-granted](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

그 프로젝트에서 세션 soft delete 권한을 받은 사용자가 세션의 서비스를 종료하면, 호출이 아무것도 반환하지 않고 끝납니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.shutdown_service: user-2이 session-1 세션의 서비스를 종료합니다

Then

- 호출이 아무것도 반환하지 않고 예외도 없습니다
  - answered = None

<a id="logs_and_services-shutting-down-a-service-granted-nothing"></a>

#### [shutting-down-a-service-granted-nothing](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

아무 권한도 받지 않은 사용자가 세션의 서비스를 종료하려 하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.shutdown_service: user-2이 session-1 세션의 서비스를 종료합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### start_service

<a id="logs_and_services-starting-a-service-granted"></a>

#### [starting-a-service-granted](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

그 프로젝트에서 세션 생성 권한을 받은 사용자가 프록시 주소가 없는 자원 그룹의 세션에서 서비스를 시작하려 하면, 프록시가 없어서 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 CREATE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.start_service: user-2이 session-1 세션의 서비스를 시작합니다

Then

- 거부됩니다
  - 거부: ServiceUnavailable

<a id="logs_and_services-starting-a-service-granted-nothing"></a>

#### [starting-a-service-granted-nothing](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

아무 권한도 받지 않은 사용자가 세션의 서비스를 시작하려 하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.start_service: user-2이 session-1 세션의 서비스를 시작합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

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

### update

<a id="updating-a-session-update-with-no-field-project"></a>

#### [a-session-update-with-no-field-project](/tests/scenario/bai_scenario/manager/session/test_updating.py): pass

그 프로젝트에서 세션 읽기 권한을 받은 사용자가 바꿀 값 없이 세션을 수정 요청하면, 현재 세션 전체가 반환됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-2: 역할 session-reader-1 보유

When

- SessionAdapter.update: user-2이 바꿀 값 없이 세션을 수정 요청합니다

Then

- 현재 세션 전체가 저장된 그대로 반환됩니다
  - session: 저장된 세션의 전체 정보와 같다

<a id="updating-a-session-update-with-no-field-nothing"></a>

#### [a-session-update-with-no-field-nothing](/tests/scenario/bai_scenario/manager/session/test_updating.py): pass

아무 권한도 받지 않은 사용자가 바꿀 값 없이 세션을 수정 요청하면, 권한 부족으로 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다

When

- SessionAdapter.update: user-2이 바꿀 값 없이 세션을 수정 요청합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="updating-renaming-a-session-that-is-not-running-is-refused"></a>

#### [renaming-a-session-that-is-not-running-is-refused](/tests/scenario/bai_scenario/manager/session/test_updating.py): pass

그 프로젝트에서 세션 수정 권한을 받은 사용자가 아직 실행 중이 아닌 세션의 이름을 바꾸려 하면, 실행 중이 아니라서 거부됩니다

Given

- 커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명
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
  - 자원 슬롯 유형 slot-1: count 유형
  - 세션 session-1: 스케줄링을 기다립니다
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): 환경 변수 하나를 갖습니다
  - 세션 session-1(main 커널 그룹 하나를 갖습니다): slot-1 슬롯 요구량 하나를 갖습니다
  - 세션 session-1: 요구량이 slot-1 1인 커널 하나를 갖습니다
  - 프로젝트 범위의 세션 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 session-updater-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 session-updater-1: session 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 session-updater-1 보유

When

- SessionAdapter.update: user-2이 session-1 세션의 이름을 바꿉니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

