## scheduling_history

[어댑터](/src/ai/backend/manager/api/adapters/scheduling_history/adapter.py)

시나리오: 완성

- ops 구성 (10)
  - admin_search_deployment_history: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_kernel_history: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_replica_group_history: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_route_history: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_session_history: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_deployment_histories_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_kernel_histories_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_replica_group_histories_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_route_histories_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_session_histories_by_ids: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (5)
  - deployment_scoped_search: 성공 있음 1 · 거부 있음 1 (scope)
  - route_scoped_search: 성공 있음 1 · 거부 있음 1 (scope)
  - scoped_search_kernel_history: 성공 있음 1 · 거부 있음 2 (scope)
  - scoped_search_replica_group_history: 성공 있음 1 · 거부 있음 2 (scope)
  - session_scoped_search: 성공 있음 1 · 거부 있음 1 (scope)

**admin_search_deployment_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 배포 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다](#searching-the-superadmin-pages-through-deployment-histories) | 성공 |
| [슈퍼관리자가 아닌 사용자가 배포 이력을 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-deployment-histories) | 거부 |

**admin_search_kernel_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 커널 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다](#searching-the-superadmin-pages-through-kernel-histories) | 성공 |
| [슈퍼관리자가 아닌 사용자가 커널 이력을 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-kernel-histories) | 거부 |

**admin_search_replica_group_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 복제본 그룹 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다](#searching-the-superadmin-pages-through-replica-group-histories) | 성공 |
| [슈퍼관리자가 아닌 사용자가 복제본 그룹 이력을 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-replica-group-histories) | 거부 |

**admin_search_route_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 라우트 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다](#searching-the-superadmin-pages-through-route-histories) | 성공 |
| [슈퍼관리자가 아닌 사용자가 라우트 이력을 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-route-histories) | 거부 |

**admin_search_session_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 세션 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다](#searching-the-superadmin-pages-through-session-histories) | 성공 |
| [슈퍼관리자가 아닌 사용자가 세션 이력을 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-page-through-session-histories) | 거부 |

**batch_load_deployment_histories_by_ids**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 배포 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다](#batch_loading-the-superadmin-loads-the-deployment-history) | 성공 |
| [슈퍼관리자가 있는 id 와 없는 id 로 배포 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다](#batch_loading-the-superadmin-loads-the-deployment-history-with-an-unknown-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 남의 배포 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-may-not-load-the-deployment-history) | 거부 |

**batch_load_kernel_histories_by_ids**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 커널 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다](#batch_loading-the-superadmin-loads-the-kernel-history) | 성공 |
| [슈퍼관리자가 있는 id 와 없는 id 로 커널 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다](#batch_loading-the-superadmin-loads-the-kernel-history-with-an-unknown-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 남의 커널 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-may-not-load-the-kernel-history) | 거부 |

**batch_load_replica_group_histories_by_ids**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 복제본 그룹 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다](#batch_loading-the-superadmin-loads-the-replica-group-history) | 성공 |
| [슈퍼관리자가 있는 id 와 없는 id 로 복제본 그룹 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다](#batch_loading-the-superadmin-loads-the-replica-group-history-with-an-unknown-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 남의 복제본 그룹 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-may-not-load-the-replica-group-history) | 거부 |

**batch_load_route_histories_by_ids**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 라우트 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다](#batch_loading-the-superadmin-loads-the-route-history) | 성공 |
| [슈퍼관리자가 있는 id 와 없는 id 로 라우트 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다](#batch_loading-the-superadmin-loads-the-route-history-with-an-unknown-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 남의 라우트 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-may-not-load-the-route-history) | 거부 |

**batch_load_session_histories_by_ids**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 세션 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다](#batch_loading-the-superadmin-loads-the-session-history) | 성공 |
| [슈퍼관리자가 있는 id 와 없는 id 로 세션 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다](#batch_loading-the-superadmin-loads-the-session-history-with-an-unknown-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 남의 세션 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-may-not-load-the-session-history) | 거부 |

**deployment_scoped_search**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 미리 만든 대상을 범위로 배포 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다](#scoped_searching-the-superadmin-pages-through-the-scoped-deployment-histories) | 성공 |
| [아무 권한도 받지 않은 사용자가 배포 이력을 범위로 훑으면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-deployment-histories) | 거부 |

**route_scoped_search**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 미리 만든 대상을 범위로 라우트 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다](#scoped_searching-the-superadmin-pages-through-the-scoped-route-histories) | 성공 |
| [아무 권한도 받지 않은 사용자가 라우트 이력을 범위로 훑으면 요청이 거부됩니다](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-route-histories) | 거부 |

**scoped_search_kernel_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 미리 만든 대상을 범위로 커널 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다](#scoped_searching-the-superadmin-pages-through-the-scoped-kernel-histories) | 성공 |
| [아무 권한도 받지 않은 사용자가 커널 이력을 범위로 훑으면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-kernel-histories) | 거부 |
| [슈퍼관리자가 범위 항목 둘을 대고 커널 이력을 훑으면 요청이 거부됩니다](#scoped_searching-kernel-history-scope-naming-two-items-is-refused) | 거부 |

**scoped_search_replica_group_history**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 미리 만든 대상을 범위로 복제본 그룹 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다](#scoped_searching-the-superadmin-pages-through-the-scoped-replica-group-histories) | 성공 |
| [아무 권한도 받지 않은 사용자가 복제본 그룹 이력을 범위로 훑으면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-replica-group-histories) | 거부 |
| [슈퍼관리자가 범위 항목 둘을 대고 복제본 그룹 이력을 훑으면 요청이 거부됩니다](#scoped_searching-replica-group-history-scope-naming-two-items-is-refused) | 거부 |

**session_scoped_search**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 미리 만든 대상을 범위로 세션 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다](#scoped_searching-the-superadmin-pages-through-the-scoped-session-histories) | 성공 |
| [아무 권한도 받지 않은 사용자가 세션 이력을 범위로 훑으면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-session-histories) | 거부 |

### admin_search_deployment_history

<a id="searching-the-superadmin-pages-through-deployment-histories"></a>

#### [the-superadmin-pages-through-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 배포 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_deployment_history: user-2 이 필터 없이 배포 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].deployment_id: 미리 만든 배포의 id 와 같다
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-page-through-deployment-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 배포 이력을 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_deployment_history: user-2 이 필터 없이 배포 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_kernel_history

<a id="searching-the-superadmin-pages-through-kernel-histories"></a>

#### [the-superadmin-pages-through-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 커널 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_kernel_history: user-2 이 필터 없이 커널 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].kernel_id: 미리 만든 커널의 id 와 같다
  - items[0].session_id: 미리 만든 세션의 id 와 같다
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PREPARING'
  - items[0].to_status = 'PULLING'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-page-through-kernel-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 커널 이력을 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_kernel_history: user-2 이 필터 없이 커널 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_replica_group_history

<a id="searching-the-superadmin-pages-through-replica-group-histories"></a>

#### [the-superadmin-pages-through-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 복제본 그룹 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_replica_group_history: user-2 이 필터 없이 복제본 그룹 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].deployment_id: 미리 만든 배포의 id 와 같다
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-page-through-replica-group-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 복제본 그룹 이력을 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_replica_group_history: user-2 이 필터 없이 복제본 그룹 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_route_history

<a id="searching-the-superadmin-pages-through-route-histories"></a>

#### [the-superadmin-pages-through-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 라우트 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_route_history: user-2 이 필터 없이 라우트 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].route_id: 미리 만든 복제본의 id 와 같다
  - items[0].deployment_id: 미리 만든 배포의 id 와 같다
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = 'provisioning'
  - items[0].to_status = 'running'
  - items[0].from_sub_status = 'pending'
  - items[0].to_sub_status = 'warming_up'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-page-through-route-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 라우트 이력을 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_route_history: user-2 이 필터 없이 라우트 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_session_history

<a id="searching-the-superadmin-pages-through-session-histories"></a>

#### [the-superadmin-pages-through-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 세션 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_session_history: user-2 이 필터 없이 세션 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].session_id: 미리 만든 세션의 id 와 같다
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PENDING'
  - items[0].to_status = 'SCHEDULED'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="searching-a-user-granted-nothing-may-not-page-through-session-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

슈퍼관리자가 아닌 사용자가 세션 이력을 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.admin_search_session_history: user-2 이 필터 없이 세션 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_deployment_histories_by_ids

<a id="batch_loading-the-superadmin-loads-the-deployment-history"></a>

#### [the-superadmin-loads-the-deployment-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 배포 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_deployment_histories_by_ids: user-2 이 미리 만든 id 로 배포 이력을 읽습니다

Then

- 미리 만든 이력이 노드로 옵니다
  - length = 1
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].deployment_id: 미리 만든 배포의 id 와 같다
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-loads-the-deployment-history-with-an-unknown-id"></a>

#### [the-superadmin-loads-the-deployment-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 있는 id 와 없는 id 로 배포 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_deployment_histories_by_ids: user-2 이 미리 만든 id 와 없는 id 로 배포 이력을 읽습니다

Then

- 미리 만든 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].deployment_id: 미리 만든 배포의 id 와 같다
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-deployment-history"></a>

#### [a-user-granted-nothing-may-not-load-the-deployment-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 남의 배포 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_deployment_histories_by_ids: user-2 이 미리 만든 id 로 배포 이력을 읽습니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_kernel_histories_by_ids

<a id="batch_loading-the-superadmin-loads-the-kernel-history"></a>

#### [the-superadmin-loads-the-kernel-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 커널 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_kernel_histories_by_ids: user-2 이 미리 만든 id 로 커널 이력을 읽습니다

Then

- 미리 만든 이력이 노드로 옵니다
  - length = 1
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].kernel_id: 미리 만든 커널의 id 와 같다
  - [0].session_id: 미리 만든 세션의 id 와 같다
  - [0].phase = 'scheduling'
  - [0].from_status = 'PREPARING'
  - [0].to_status = 'PULLING'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-loads-the-kernel-history-with-an-unknown-id"></a>

#### [the-superadmin-loads-the-kernel-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 있는 id 와 없는 id 로 커널 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_kernel_histories_by_ids: user-2 이 미리 만든 id 와 없는 id 로 커널 이력을 읽습니다

Then

- 미리 만든 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].kernel_id: 미리 만든 커널의 id 와 같다
  - [0].session_id: 미리 만든 세션의 id 와 같다
  - [0].phase = 'scheduling'
  - [0].from_status = 'PREPARING'
  - [0].to_status = 'PULLING'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-kernel-history"></a>

#### [a-user-granted-nothing-may-not-load-the-kernel-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 남의 커널 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_kernel_histories_by_ids: user-2 이 미리 만든 id 로 커널 이력을 읽습니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_replica_group_histories_by_ids

<a id="batch_loading-the-superadmin-loads-the-replica-group-history"></a>

#### [the-superadmin-loads-the-replica-group-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 복제본 그룹 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_replica_group_histories_by_ids: user-2 이 미리 만든 id 로 복제본 그룹 이력을 읽습니다

Then

- 미리 만든 이력이 노드로 옵니다
  - length = 1
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].deployment_id: 미리 만든 배포의 id 와 같다
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-loads-the-replica-group-history-with-an-unknown-id"></a>

#### [the-superadmin-loads-the-replica-group-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 있는 id 와 없는 id 로 복제본 그룹 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_replica_group_histories_by_ids: user-2 이 미리 만든 id 와 없는 id 로 복제본 그룹 이력을 읽습니다

Then

- 미리 만든 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].deployment_id: 미리 만든 배포의 id 와 같다
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-replica-group-history"></a>

#### [a-user-granted-nothing-may-not-load-the-replica-group-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 남의 복제본 그룹 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_replica_group_histories_by_ids: user-2 이 미리 만든 id 로 복제본 그룹 이력을 읽습니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_route_histories_by_ids

<a id="batch_loading-the-superadmin-loads-the-route-history"></a>

#### [the-superadmin-loads-the-route-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 라우트 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_route_histories_by_ids: user-2 이 미리 만든 id 로 라우트 이력을 읽습니다

Then

- 미리 만든 이력이 노드로 옵니다
  - length = 1
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].route_id: 미리 만든 복제본의 id 와 같다
  - [0].deployment_id: 미리 만든 배포의 id 와 같다
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = 'provisioning'
  - [0].to_status = 'running'
  - [0].from_sub_status = 'pending'
  - [0].to_sub_status = 'warming_up'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-loads-the-route-history-with-an-unknown-id"></a>

#### [the-superadmin-loads-the-route-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 있는 id 와 없는 id 로 라우트 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_route_histories_by_ids: user-2 이 미리 만든 id 와 없는 id 로 라우트 이력을 읽습니다

Then

- 미리 만든 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].route_id: 미리 만든 복제본의 id 와 같다
  - [0].deployment_id: 미리 만든 배포의 id 와 같다
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = 'provisioning'
  - [0].to_status = 'running'
  - [0].from_sub_status = 'pending'
  - [0].to_sub_status = 'warming_up'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-route-history"></a>

#### [a-user-granted-nothing-may-not-load-the-route-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 남의 라우트 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_route_histories_by_ids: user-2 이 미리 만든 id 로 라우트 이력을 읽습니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_session_histories_by_ids

<a id="batch_loading-the-superadmin-loads-the-session-history"></a>

#### [the-superadmin-loads-the-session-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 세션 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_session_histories_by_ids: user-2 이 미리 만든 id 로 세션 이력을 읽습니다

Then

- 미리 만든 이력이 노드로 옵니다
  - length = 1
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].session_id: 미리 만든 세션의 id 와 같다
  - [0].phase = 'scheduling'
  - [0].from_status = 'PENDING'
  - [0].to_status = 'SCHEDULED'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-loads-the-session-history-with-an-unknown-id"></a>

#### [the-superadmin-loads-the-session-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

슈퍼관리자가 있는 id 와 없는 id 로 세션 이력을 읽으면, 있는 것은 노드로 오고 없는 자리는 빈 값입니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_session_histories_by_ids: user-2 이 미리 만든 id 와 없는 id 로 세션 이력을 읽습니다

Then

- 미리 만든 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 만든 이력의 id 와 같다
  - [0].field_id: 미리 만든 이력의 id 와 같다
  - [0].session_id: 미리 만든 세션의 id 와 같다
  - [0].phase = 'scheduling'
  - [0].from_status = 'PENDING'
  - [0].to_status = 'SCHEDULED'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-session-history"></a>

#### [a-user-granted-nothing-may-not-load-the-session-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 남의 세션 이력을 id 로 읽으면 그 자리가 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.batch_load_session_histories_by_ids: user-2 이 미리 만든 id 로 세션 이력을 읽습니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### deployment_scoped_search

<a id="scoped_searching-the-superadmin-pages-through-the-scoped-deployment-histories"></a>

#### [the-superadmin-pages-through-the-scoped-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 미리 만든 대상을 범위로 배포 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.deployment_scoped_search: user-2 이 미리 만든 대상 하나를 범위로 배포 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].deployment_id: 미리 만든 배포의 id 와 같다
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-deployment-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

아무 권한도 받지 않은 사용자가 배포 이력을 범위로 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.deployment_scoped_search: user-2 이 미리 만든 대상 하나를 범위로 배포 이력을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### route_scoped_search

<a id="scoped_searching-the-superadmin-pages-through-the-scoped-route-histories"></a>

#### [the-superadmin-pages-through-the-scoped-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 미리 만든 대상을 범위로 라우트 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.route_scoped_search: user-2 이 미리 만든 대상 하나를 범위로 라우트 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].route_id: 미리 만든 복제본의 id 와 같다
  - items[0].deployment_id: 미리 만든 배포의 id 와 같다
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = 'provisioning'
  - items[0].to_status = 'running'
  - items[0].from_sub_status = 'pending'
  - items[0].to_sub_status = 'warming_up'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-route-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

아무 권한도 받지 않은 사용자가 라우트 이력을 범위로 훑으면 요청이 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.route_scoped_search: user-2 이 미리 만든 대상 하나를 범위로 라우트 이력을 훑습니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### scoped_search_kernel_history

<a id="scoped_searching-the-superadmin-pages-through-the-scoped-kernel-histories"></a>

#### [the-superadmin-pages-through-the-scoped-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 미리 만든 대상을 범위로 커널 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.scoped_search_kernel_history: user-2 이 미리 만든 대상 하나를 범위로 커널 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].kernel_id: 미리 만든 커널의 id 와 같다
  - items[0].session_id: 미리 만든 세션의 id 와 같다
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PREPARING'
  - items[0].to_status = 'PULLING'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-kernel-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

아무 권한도 받지 않은 사용자가 커널 이력을 범위로 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.scoped_search_kernel_history: user-2 이 미리 만든 대상 하나를 범위로 커널 이력을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="scoped_searching-kernel-history-scope-naming-two-items-is-refused"></a>

#### [kernel-history-scope-naming-two-items-is-refused](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 범위 항목 둘을 대고 커널 이력을 훑으면 요청이 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.scoped_search_kernel_history: user-2 이 범위 항목 둘을 대고 커널 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

### scoped_search_replica_group_history

<a id="scoped_searching-the-superadmin-pages-through-the-scoped-replica-group-histories"></a>

#### [the-superadmin-pages-through-the-scoped-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 미리 만든 대상을 범위로 복제본 그룹 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.scoped_search_replica_group_history: user-2 이 미리 만든 대상 하나를 범위로 복제본 그룹 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].deployment_id: 미리 만든 배포의 id 와 같다
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-replica-group-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

아무 권한도 받지 않은 사용자가 복제본 그룹 이력을 범위로 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.scoped_search_replica_group_history: user-2 이 미리 만든 대상 하나를 범위로 복제본 그룹 이력을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="scoped_searching-replica-group-history-scope-naming-two-items-is-refused"></a>

#### [replica-group-history-scope-naming-two-items-is-refused](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 범위 항목 둘을 대고 복제본 그룹 이력을 훑으면 요청이 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.scoped_search_replica_group_history: user-2 이 범위 항목 둘을 대고 복제본 그룹 이력을 훑습니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

### session_scoped_search

<a id="scoped_searching-the-superadmin-pages-through-the-scoped-session-histories"></a>

#### [the-superadmin-pages-through-the-scoped-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

슈퍼관리자가 미리 만든 대상을 범위로 세션 이력을 훑으면 그 이력 하나가 한 페이지로 옵니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 슈퍼관리자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.session_scoped_search: user-2 이 미리 만든 대상 하나를 범위로 세션 이력을 훑습니다

Then

- 미리 만든 이력 하나가 한 페이지로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 미리 만든 이력의 id 와 같다
  - items[0].field_id: 미리 만든 이력의 id 와 같다
  - items[0].session_id: 미리 만든 세션의 id 와 같다
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PENDING'
  - items[0].to_status = 'SCHEDULED'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-session-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

아무 권한도 받지 않은 사용자가 세션 이력을 범위로 훑으면 권한 부족으로 거부됩니다

Given

- 스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, 아무 권한도 받지 않은 일반 사용자
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
  - 세션 session-1: main 커널 그룹 하나를 갖습니다
  - 세션 session-1: 요구량이 인 커널 하나를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포의 세션 그룹 deployment-session-group-1: 배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다
  - 배포 deployment-1: 세션 그룹을 가진 복제본 그룹 하나를 갖습니다
  - 배포 deployment-1: 복제본 하나를 갖습니다
  - 세션 session-1: 스케줄링 시도 하나를 남깁니다
  - 세션 session-1: 커널의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 배포의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 라우트의 스케줄링 시도 하나를 남깁니다
  - 배포 deployment-1: 복제본 그룹의 스케줄링 시도 하나를 남깁니다

When

- SchedulingHistoryAdapter.session_scoped_search: user-2 이 미리 만든 대상 하나를 범위로 세션 이력을 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

