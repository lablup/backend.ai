## client_ip_masking

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/client_ip_masking/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/client_ip_masking/adapter.py)

Not exercised by any scenario: batch_load_fields.

### retiring

#### [a-user-granted-nothing-may-not-purge-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 정책을 지우면 권한 부족으로 거부된다. 넣기가 역할로 거부되는 것과 다른 문이다

Given

- 클라이언트 IP 마스킹 정책 하나와, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_purge — user-1이 default 정책을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 없는 id를 지우면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 돌고 없는 행에는 걸린 권한도 없다

Given

- 클라이언트 IP 마스킹 정책 하나와, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_purge — user-1이 없는 id을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [purging-a-masking-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py) — pass

슈퍼관리자가 아무 정책도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다

Given

- 클라이언트 IP 마스킹 정책 하나와, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_purge — user-1이 없는 id을 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-purges-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py) — pass

슈퍼관리자가 정책을 id로 지우면 지운 정책 전체를 실은 답이 온다

Given

- 클라이언트 IP 마스킹 정책 하나와, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_purge — user-1이 default 정책을 지움

Then

- 지운 정책 전체가 온다
  - id: 심은 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-user-purge-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정책을 지운다. 지우기의 문은 넣기와 달리 권한 그래프라 스위치가 통한다

Given

- 클라이언트 IP 마스킹 정책 하나와, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_purge — user-1이 default 정책을 지움

Then

- 지운 정책 전체가 온다
  - id: 심은 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### searching

#### [a-mode-filter-keeps-only-the-policies-of-that-mode](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py) — pass

모드가 다른 정책 여럿이 있을 때 한 모드로 걸러 조회하면 그 모드의 것만 남는다

Given

- 모드가 다른 클라이언트 IP 마스킹 정책 셋과, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 audit_logs: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: drop 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_search — user-1이 truncate 모드로 걸러 조회

Then

- 답에 나와야 하는 정책만 남는다
  - items = ['audit_logs', 'default']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-target-filter-narrows-the-answer-to-that-targets-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py) — pass

세 대상의 정책이 있을 때 한 대상으로 걸러 조회하면 그 대상의 것 하나만 남는다

Given

- 세 대상의 클라이언트 IP 마스킹 정책과, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 audit_logs: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_search — user-1이 default 대상으로 걸러 조회

Then

- 걸러낸 그 정책 하나만 남는다
  - items = ['default']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-masking-policies](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체 조회를 요청하면 역할로 거부된다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, 일반 사용자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-monitor-searches-masking-policies-like-the-superadmin](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py) — pass

모니터 역할이 필터 없이 조회하면 슈퍼관리자와 같은 답이 온다. 전역 역할 문은 모니터의 읽기를 지나게 한다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, 모니터 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답에 나와야 하는 정책만 남는다
  - items = ['default', 'login_history']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-counts-every-masking-policy-laid](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py) — pass

대상이 다른 정책 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘을 모두 센다

Given

- 대상이 다른 클라이언트 IP 마스킹 정책 둘과, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 클라이언트 IP 마스킹 정책 login_history: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답에 나와야 하는 정책만 남는다
  - items = ['default', 'login_history']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

### upserting

#### [a-masking-policy-is-put-on-the-audit-logs-target](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 audit_logs 대상에 넣으면 그 대상이 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 audit_logs 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'audit_logs'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-masking-policy-is-put-on-the-default-target](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 default 대상에 넣으면 그 대상이 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-masking-policy-is-put-on-the-login-history-target](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 login_history 대상에 넣으면 그 대상이 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 login_history 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'login_history'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-masking-policy-of-the-drop-mode-is-put](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 drop 모드로 넣으면 그 모드가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 drop 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'default'
  - mode = 'drop'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-masking-policy-of-the-none-mode-is-put](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 none 모드로 넣으면 그 모드가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 none 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'default'
  - mode = 'none'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-masking-policy-of-the-truncate-mode-is-put](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 truncate 모드로 넣으면 그 모드가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-masking-policy-put-without-prefixes-carries-empty-prefixes](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

대상과 모드만 주고 넣으면 두 접두 길이가 빈 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = None
  - ipv6_prefix = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

슈퍼관리자가 아닌 사용자가 정책을 넣으면 역할로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [putting-a-policy-again-without-prefixes-clears-the-stored-prefixes](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

접두 길이가 있는 정책의 대상에 대상과 모드만 주고 다시 넣으면 접두 길이가 비워진다. 넣기는 합치지 않고 행을 통째로 바꾼다

Given

- 클라이언트 IP 마스킹 정책 하나와, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 다시 넣음

Then

- 같은 id의 행이 준 값으로 바뀌어 온다
  - id: 심은 정책와 같다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = None
  - ipv6_prefix = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

이미 정책이 있는 대상에 다른 모드로 넣으면, 새 행이 아니라 같은 id의 행이 새 모드로 바뀐 노드가 온다

Given

- 클라이언트 IP 마스킹 정책 하나와, 슈퍼관리자 한 명
  - 클라이언트 IP 마스킹 정책 default: truncate 모드, 접두 길이 v4 24, v6 48
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 drop 정책을 접두 길이와 함께 다시 넣음

Then

- 같은 id의 행이 준 값으로 바뀌어 온다
  - id: 심은 정책와 같다
  - target_type = 'default'
  - mode = 'drop'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [the-monitor-may-not-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

모니터 역할이 정책을 넣으면 역할로 거부된다. 모니터는 전역 역할 문의 읽기만 지난다

Given

- 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-puts-a-masking-policy-on-a-target](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

정책이 없을 때 슈퍼관리자가 대상·모드·두 접두 길이로 넣으면 준 값이 그대로 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 넣은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-does-not-let-a-user-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 정책을 넣지 못한다. 이 문은 권한 그래프가 아니라 역할이라 스위치와 무관하다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ClientIPMaskingAdapter.admin_upsert — user-1이 default 대상에 truncate 정책을 접두 길이와 함께 넣음

Then

- 거부된다
  - 거부: InsufficientPrivilege

