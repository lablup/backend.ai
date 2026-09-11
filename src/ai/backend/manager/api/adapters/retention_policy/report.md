## retention_policy

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/retention_policy/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/retention_policy/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-policy-for-the-deployments-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 deployments 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 deployments 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.DEPLOYMENTS: 'deployments'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-login-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 login 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 login 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGIN: 'login'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-logs-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 logs 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 logs 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-reconcile-history-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 reconcile_history 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 reconcile_history 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.RECONCILE_HISTORY: 'reconcile_history'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-roles-invitations-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 roles_invitations 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 roles_invitations 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.ROLES_INVITATIONS: 'roles_invitations'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-sessions-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 sessions 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 sessions 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.SESSIONS: 'sessions'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-usage-buckets-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 usage_buckets 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 usage_buckets 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.USAGE_BUCKETS: 'usage_buckets'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-for-the-usage-records-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 usage_records 카테고리의 정책을 만들면 그 카테고리가 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 usage_records 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.USAGE_RECORDS: 'usage_records'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-policy-made-inactive-comes-back-inactive](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

활성 여부를 거짓으로 주고 만들면 비활성 상태를 실은 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 sessions 정책을 비활성으로 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.SESSIONS: 'sessions'>
  - retention_period_days = 90
  - enabled = False
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-second-policy-for-the-same-category-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

어떤 카테고리의 정책이 이미 있을 때 같은 카테고리로 다시 만들면, 카테고리가 겹친다는 이유로 거부된다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 이미 있는 logs 정책을 다시 만듦

Then

- 거부된다
  - 거부: RetentionPolicyConflict

#### [a-user-who-is-not-the-superadmin-may-not-create-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 정책을 만들면 역할로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 sessions 정책을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-monitor-may-not-create-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

모니터 역할이 정책을 만들면 역할로 거부된다. 모니터는 전역 역할 문의 읽기만 지난다

Given

- 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 sessions 정책을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-makes-a-policy-that-is-active-and-never-swept](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

슈퍼관리자가 카테고리와 보존 일수만 주고 만들면, 활성 여부는 참이고 마지막 청소 시각은 비어 있는 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 sessions 정책을 만듦

Then

- 만든 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.SESSIONS: 'sessions'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-does-not-let-a-user-create-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 정책을 만들지 못한다. 이 문은 권한 그래프가 아니라 역할이라 스위치와 무관하다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.create — user-1이 sessions 정책을 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-policy-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 logs 정책의 아무것도 고침

Then

- 심은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-user-granted-nothing-may-not-edit-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 정책을 고치면 권한 부족으로 거부된다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 logs 정책의 보존 일수 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [disabling-a-policy-answers-it-inactive](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

활성 정책의 활성 여부를 내리면 비활성 상태를 실은 노드가 온다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 logs 정책의 활성 여부 고침

Then

- 심은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = False
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [editing-the-retention-days-leaves-the-rest-alone](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

슈퍼관리자가 보존 일수만 고치면, 일수는 새 값이 되고 카테고리와 활성 여부는 그대로 남는다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 logs 정책의 보존 일수 고침

Then

- 심은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 180
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [moving-a-policy-to-a-category-already-taken-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

정책 둘 중 한쪽의 카테고리를 다른 쪽 것으로 바꾸면, 카테고리가 겹친다는 이유로 거부된다. 만들 때와 달리 저장소의 제약 위반이 그대로 온다

Given

- 카테고리가 다른 보존 정책 둘과, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 보존 정책 login: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 logs 정책의 카테고리를 login로 고침

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [the-superadmin-editing-a-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

슈퍼관리자가 아무 정책도 갖지 않은 id를 고치면 대상이 없다는 것으로 거부된다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 없는 id의 보존 일수 고침

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [turning-enforcement-off-lets-a-user-edit-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정책을 고친다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.update — user-1이 logs 정책의 보존 일수 고침

Then

- 심은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 180
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading

#### [a-user-granted-nothing-may-not-read-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 id로 조회하면 권한 부족으로 거부된다. 인증만으로 읽히는 다른 카탈로그와 달리 이 읽기는 권한 문을 지난다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.get — user-1이 logs 정책을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-reading-an-unknown-policy-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 없는 id로 조회하면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 돌고 없는 행에는 걸린 권한도 없다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.get — user-1이 없는 id을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [the-superadmin-reading-a-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py) — pass

슈퍼관리자가 아무 정책도 갖지 않은 id로 조회하면 대상이 없다는 것으로 거부된다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.get — user-1이 없는 id을 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-reads-a-policy-by-id](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py) — pass

정책 하나가 있고 슈퍼관리자가 id로 조회하면, 그 정책 전체가 온다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.get — user-1이 logs 정책을 조회

Then

- 심은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-user-read-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정책을 읽는다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.get — user-1이 logs 정책을 조회

Then

- 심은 정책 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### retiring

#### [a-user-granted-nothing-may-not-delete-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 정책을 지우면 권한 부족으로 거부된다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.delete — user-1이 logs 정책을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-purge-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 정책을 완전히 지우면 권한 부족으로 거부된다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.purge — user-1이 logs 정책을 완전히 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [deleting-a-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py) — pass

슈퍼관리자가 아무 정책도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.delete — user-1이 없는 id을 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [purging-a-policy-answers-like-deleting-it](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py) — pass

슈퍼관리자가 정책을 완전히 지우면 지우기와 같은 답이 온다. 둘 다 행을 없애고 soft delete는 없다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.purge — user-1이 logs 정책을 완전히 지움

Then

- 지운 정책의 id가 온다
  - id: 심은 정책와 같다

#### [the-superadmin-deletes-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py) — pass

슈퍼관리자가 정책을 지우면 지운 정책의 id를 실은 답이 온다

Given

- 보존 정책 하나와, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.delete — user-1이 logs 정책을 지움

Then

- 지운 정책의 id가 온다
  - id: 심은 정책와 같다

#### [turning-enforcement-off-lets-a-user-delete-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정책을 지운다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 보존 정책 하나와, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.delete — user-1이 logs 정책을 지움

Then

- 지운 정책의 id가 온다
  - id: 심은 정책와 같다

### searching

#### [a-category-filter-narrows-the-answer-to-that-category](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py) — pass

카테고리가 다른 정책 여럿 중 하나의 카테고리로 걸러 조회하면 그 카테고리의 것 하나만 남는다

Given

- 카테고리가 다른 보존 정책 둘과, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 보존 정책 login: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.search — user-1이 logs로 걸러 조회

Then

- 걸러낸 그 정책 하나만 남는다
  - items = ['logs']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-policies](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체 조회를 요청하면 역할로 거부된다

Given

- 카테고리가 다른 보존 정책 둘과, 일반 사용자 한 명
  - 보존 정책 logs: 30일 보존
  - 보존 정책 login: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [an-enabled-filter-keeps-only-the-active-policies](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py) — pass

활성과 비활성이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 남는다

Given

- 활성 보존 정책 하나와 비활성 하나, 그리고 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 보존 정책 login: 30일 보존, 비활성
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.search — user-1이 활성인 것만 조회

Then

- 답에 나와야 하는 정책만 남는다
  - items = ['logs']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [the-monitor-searches-policies-like-the-superadmin](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py) — pass

모니터 역할이 필터 없이 조회하면 슈퍼관리자와 같은 답이 온다. 전역 역할 문은 모니터의 읽기를 지나게 한다

Given

- 카테고리가 다른 보존 정책 둘과, 모니터 한 명
  - 보존 정책 logs: 30일 보존
  - 보존 정책 login: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.search — user-1이 필터 없이 전체 조회

Then

- 답에 나와야 하는 정책만 남는다
  - items = ['login', 'logs']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-counts-every-policy-laid](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py) — pass

카테고리가 다른 정책 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘을 모두 센다

Given

- 카테고리가 다른 보존 정책 둘과, 슈퍼관리자 한 명
  - 보존 정책 logs: 30일 보존
  - 보존 정책 login: 30일 보존
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RetentionPolicyAdapter.search — user-1이 필터 없이 전체 조회

Then

- 답에 나와야 하는 정책만 남는다
  - items = ['login', 'logs']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

