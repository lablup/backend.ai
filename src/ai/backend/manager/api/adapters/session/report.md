## session

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session/adapter.py)

Not exercised by any scenario: admin_search_kernels, batch_load_by_ids, batch_load_fields, batch_load_kernels_by_ids, batch_resource_allocation_by_kernel, compute_schedule, enqueue, exclude_idle_checks, get, get_logs, gql_search_by_project, include_idle_checks, my_search, project_search, scoped_search, search_kernels_by_agent, search_kernels_by_session, search_sessions_by_agent, shutdown_service, start_service, update.

### loading

#### [loading-allocations-answers-the-own-session-and-refuses-the-others-alone](/tests/scenario/bai_scenario/manager/session/test_loading.py) — pass

첫 프로젝트 범위에서만 세션을 읽을 수 있는 사용자가 두 프로젝트의 세션 할당을 한 번에 읽으면, 자기 프로젝트의 세션은 빈 할당으로, 다른 프로젝트의 세션은 권한 부족의 거부로 답하고 호출 자체는 거부되지 않는다

Given

- 서로 다른 프로젝트에서 기다리는 세션 둘과, 첫 프로젝트 범위에서만 세션을 읽을 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인 home-2
  - 프로젝트 team-2
  - 리소스 그룹 resource-group-2: fifo 스케줄러를 쓴다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-2: 이미지를 가져오는 곳
  - 이미지 image-2: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-2: 스케줄링을 기다리고 있다
  - 프로젝트 범위의 세션 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-reader-1: session 전체에 READ 허용
    - 일반 사용자 user-3: 역할 session-reader-1 보유

When

- SessionAdapter.batch_resource_allocation_by_session — user-3이 session-1(와)과 session-2의 할당을 한 번에 읽음

Then

- 자기 프로젝트의 세션은 빈 할당으로, 다른 프로젝트의 세션은 권한 부족의 거부로, 요청한 순서대로 답한다
  - len(items) = 2
  - items[0].requested.entries = []
  - items[0].used.entries = []
  - items[0].allocated.entries = []
  - 거부: NotEnoughPermission

### session

#### [a-scenario-that-laid-no-session-finds-none](/tests/scenario/bai_scenario/manager/session/test_session.py) — pass

세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SessionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-may-not-search-sessions](/tests/scenario/bai_scenario/manager/session/test_session.py) — pass

필터 없는 전체 조회는 슈퍼관리자 역할로만 열리므로, 아무 권한도 받지 않은 사용자는 역할 부족으로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SessionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### terminating

#### [a-user-granted-nothing-has-the-session-refused-in-a-terminate](/tests/scenario/bai_scenario/manager/session/test_terminating.py) — pass

아무 권한도 없는 사용자가 세션을 종료하면, 그 세션이 실패 목록에 담겨 반환되고 아무것도 종료되지 않는다

Given

- 스케줄링을 기다리는 세션 하나와, 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다리고 있다

When

- SessionAdapter.terminate — user-2이 session-1 종료

Then

- 미리 만들어 둔 세션이 실패 목록에 반환되고, 결과 목록은 전부 비어 있다
  - cancelled = []
  - terminating = []
  - force_terminated = []
  - skipped = []
  - failed[*].session_id: 미리 만들어 둔 세션와 같다
  - failed[*].message: 무시함 — 이유는 문자열로 오고, 문자열은 바뀌어도 되는 값이다

#### [a-user-granted-termination-cancels-their-pending-session](/tests/scenario/bai_scenario/manager/session/test_terminating.py) — pass

그 프로젝트에서 세션을 종료할 수 있는 사용자가 기다리던 세션을 종료하면, 취소된 목록에 담겨 반환된다

Given

- 스케줄링을 기다리는 세션 하나와, 그 프로젝트에서 세션을 종료할 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 그 프로젝트의 세션을 종료할 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
      - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-terminator-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-terminator-1: session 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-2: 역할 session-terminator-1 보유

When

- SessionAdapter.terminate — user-2이 session-1 종료

Then

- 미리 만들어 둔 세션이 취소된 목록에 반환되고, 실패 목록은 비어 있다
  - cancelled: 미리 만들어 둔 세션와 같다
  - terminating = []
  - force_terminated = []
  - skipped = []
  - failed = []

#### [an-unknown-id-in-a-terminate-is-skipped-beside-a-cancelled-one](/tests/scenario/bai_scenario/manager/session/test_terminating.py) — pass

슈퍼관리자가 기다리던 세션과 없는 id를 한 번에 종료하면, 세션은 취소된 목록에, 없는 id는 건너뛴 목록에 담겨 반환된다

Given

- 스케줄링을 기다리는 세션 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다리고 있다

When

- SessionAdapter.terminate — user-2이 session-1(와)과 없는 id를 종료

Then

- 미리 만들어 둔 세션은 취소된 목록에, 없는 id는 건너뛴 목록에 반환된다
  - cancelled: 미리 만들어 둔 세션와 같다
  - terminating = []
  - force_terminated = []
  - len(skipped) = 1
  - skipped[0]: 무시함 — 호출이 만든 없는 id라 미리 알 수 없다
  - failed = []

#### [the-other-projects-session-is-refused-alone-while-the-own-one-is-cancelled](/tests/scenario/bai_scenario/manager/session/test_terminating.py) — pass

첫 프로젝트에서만 세션을 종료할 수 있는 사용자가 두 프로젝트의 세션을 한 번에 종료하면, 자기 프로젝트의 세션은 취소된 목록에, 다른 프로젝트의 세션은 실패 목록에 담겨 반환된다

Given

- 서로 다른 프로젝트에서 기다리는 세션 둘과, 첫 프로젝트에서만 세션을 종료할 수 있는 일반 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 도메인 home-2
  - 프로젝트 team-2
  - 리소스 그룹 resource-group-2: fifo 스케줄러를 쓴다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-2: 이미지를 가져오는 곳
  - 이미지 image-2: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다리고 있다
  - 세션 session-2: 스케줄링을 기다리고 있다
  - 그 프로젝트의 세션을 종료할 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
      - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 역할 session-terminator-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 session-terminator-1: session 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-3: 역할 session-terminator-1 보유

When

- SessionAdapter.terminate — user-3이 session-1(와)과 session-2을 한 번에 종료

Then

- 자기 프로젝트의 세션은 취소된 목록에, 다른 프로젝트의 세션은 실패 목록에 반환된다
  - cancelled: 자기 프로젝트의 세션와 같다
  - terminating = []
  - force_terminated = []
  - skipped = []
  - failed[*].session_id: 다른 프로젝트의 세션와 같다
  - failed[*].message: 무시함 — 이유는 문자열로 오고, 문자열은 바뀌어도 되는 값이다

