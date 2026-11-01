## fair_share

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/fair_share/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/fair_share/adapter.py)

시나리오: 미완 13 / 15

- 직접 구현 (15)
  - atomic_bulk_upsert_domain — 성공 있음 1 · 실패 있음 2 (scope)
  - atomic_bulk_upsert_project — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - atomic_bulk_upsert_user — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - get_domain — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - get_project — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - get_user — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - search_domain — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - search_project — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - search_rg_domain — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - search_rg_project — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - search_rg_user — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - search_user — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - upsert_domain — 성공 있음 1 · 실패 있음 2 (scope)
  - upsert_project — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - upsert_user — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP

**atomic_bulk_upsert_domain**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 도메인 둘의 가중치를 한 번에 정하면, 둘을 정했다는 개수가 온다](#atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부된다](#atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights) | 거부 |
| [그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부된다. 가중치 쓰기는 그룹이 아니라 전역 대상으로 권한을 본다](#atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights) | 거부 |

**upsert_domain**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 그룹 안 도메인의 가중치를 정하면, 그 가중치를 실은 기록이 오고 나머지 설정은 그룹 기본값이다](#upserting-the-superadmin-sets-a-domain-weight) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부된다](#upserting-a-user-granted-nothing-may-not-set-a-domain-weight) | 거부 |
| [그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부된다. 가중치 쓰기는 그룹이 아니라 전역 대상으로 권한을 본다](#upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight) | 거부 |

### atomic_bulk_upsert_domain

<a id="atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once"></a>

#### [the-superadmin-sets-several-domain-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py) — pass

슈퍼관리자가 도메인 둘의 가중치를 한 번에 정하면, 둘을 정했다는 개수가 온다

Given

- 리소스 그룹 하나와 도메인 2개, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- FairShareAdapter.atomic_bulk_upsert_domain — user-1이 resource-group-1 안 도메인 2개의 가중치를 한 번에 정함

Then

- 도메인 수만큼 정했다는 개수가 온다
  - upserted_count = 2

<a id="atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-domain-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py) — pass

아무 권한도 받지 않은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와 도메인 2개, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- FairShareAdapter.atomic_bulk_upsert_domain — user-1이 resource-group-1 안 도메인 2개의 가중치를 한 번에 정함

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-domain-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py) — pass

그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부된다. 가중치 쓰기는 그룹이 아니라 전역 대상으로 권한을 본다

Given

- 리소스 그룹 하나와 도메인 2개, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 도메인 other-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- FairShareAdapter.atomic_bulk_upsert_domain — user-1이 resource-group-1 안 도메인 2개의 가중치를 한 번에 정함

Then

- 거부된다
  - 거부: NotEnoughPermission

### upsert_domain

<a id="upserting-the-superadmin-sets-a-domain-weight"></a>

#### [the-superadmin-sets-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py) — pass

슈퍼관리자가 그룹 안 도메인의 가중치를 정하면, 그 가중치를 실은 기록이 오고 나머지 설정은 그룹 기본값이다

Given

- 리소스 그룹 하나와 도메인 1개, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- FairShareAdapter.upsert_domain — user-1이 resource-group-1 안 home-1의 가중치를 정함

Then

- 정한 가중치를 실은 기록이 오고, 나머지 설정은 그룹 기본값이다
  - id: 무시함 — 데이터베이스가 만든다
  - resource_group_name = 'resource-group-1'
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: 무시함 — 쓴 날짜에 따라 달라진다
  - calculation_snapshot.lookback_end: 무시함 — 쓴 날짜에 따라 달라진다
  - calculation_snapshot.last_calculated_at: 이 실행이 쓴 시각
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="upserting-a-user-granted-nothing-may-not-set-a-domain-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py) — pass

아무 권한도 받지 않은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나와 도메인 1개, 그리고 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- FairShareAdapter.upsert_domain — user-1이 resource-group-1 안 home-1의 가중치를 정함

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py) — pass

그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 거부된다. 가중치 쓰기는 그룹이 아니라 전역 대상으로 권한을 본다

Given

- 리소스 그룹 하나와 도메인 1개, 그리고 그 그룹 범위의 UPDATE 역할을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 UPDATE 역할을 받은 사용자 준비
    - 역할 group-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 group-role-1: resource_group 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 group-role-1 보유

When

- FairShareAdapter.upsert_domain — user-1이 resource-group-1 안 home-1의 가중치를 정함

Then

- 거부된다
  - 거부: NotEnoughPermission

