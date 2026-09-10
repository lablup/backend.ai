## session

Not exercised by any scenario: admin_search_kernels, batch_load_by_ids, batch_load_fields, batch_load_kernels_by_ids, batch_resource_allocation_by_kernel, batch_resource_allocation_by_session, compute_schedule, enqueue, exclude_idle_checks, get, get_logs, gql_search_by_project, include_idle_checks, my_search, project_search, search_kernels_by_agent, search_kernels_by_session, search_sessions_by_agent, shutdown_service, start_service, terminate, update.

### session

#### a-scenario-that-laid-no-session-finds-none — pass

세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- 슈퍼관리자 user-1의 admin_search 호출
  - AdminSearchSessionsInput()

Then

- 답 전체 일치

#### a-user-granted-nothing-may-not-search-sessions — pass

세션 조회는 역할이 아니라 스코프 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- 일반 사용자 user-1의 admin_search 호출
  - AdminSearchSessionsInput()

Then

- 거부: NotEnoughPermission

