## entity_label

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/entity_label/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/entity_label/adapter.py)

시나리오: 미완 6 / 7

- ops 로 구성 (7)
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_purge — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_upsert — 대표 성공 ✓ · 대표 실패 ✓
  - purge — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - search_on — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - upsert — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [있는 id 뒤에 없는 id 를 붙여 떼면, 있는 것은 떼어지고 없는 id 는 실패 목록에 온다](#partial_bulk_purging-a-missing-id-beside-a-label-is-one-failed-item) | 성공 |
| [아무 권한도 없는 사용자가 라벨 둘을 떼면, 떼어진 것 없이 둘 다 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-nothing) | 성공 |
| [엔티티 둘에 붙은 라벨을 하나씩 떼면, 둘 다 떼어진다](#partial_bulk_purging-a-writer-purges-labels-of-two-entities) | 성공 |
| [수정 권한을 받은 사용자가 한 엔티티의 라벨 둘을 떼면, 둘 다 떼어지고 실패한 것은 없다](#partial_bulk_purging-a-writer-purges-two-labels-of-one-entity) | 성공 |
| [없는 id 만 둘 떼면, 떼어진 것 없이 둘 다 실패 목록에 온다](#partial_bulk_purging-every-id-missing-is-answered-per-id) | 성공 |
| [한 엔티티에만 수정 권한이 있으면, 그 엔티티의 라벨만 떼어지고 다른 쪽은 실패 목록에 온다](#partial_bulk_purging-only-the-label-of-the-writable-entity-is-purged) | 성공 |
| [RBAC 강제를 끄면 아무 권한도 없는 사용자도 라벨 둘을 뗀다](#partial_bulk_purging-turning-enforcement-off-lets-anyone-purge) | 성공 |

**partial_bulk_upsert**

| 시나리오 | 판정 |
|---|---|
| [이미 붙은 키를 다시 붙이면, 같은 라벨이 값만 바뀌어 온다](#partial_bulk_upserting-a-key-already-on-the-entity-takes-the-new-value) | 성공 |
| [아무 권한도 없는 사용자가 붙이면, 붙은 라벨 없이 엔티티 둘 다 실패 목록에 온다](#partial_bulk_upserting-a-user-granted-nothing-labels-nothing) | 성공 |
| [수정 권한을 받은 사용자가 엔티티 둘에 키 둘을 붙이면, 라벨 넷이 오고 실패한 것은 없다](#partial_bulk_upserting-a-writer-labels-two-entities-with-two-keys) | 성공 |
| [같은 엔티티가 여러 항목에 나오면, 그 엔티티의 라벨이 키마다 오고 실패한 것은 없다](#partial_bulk_upserting-one-entity-in-several-items-gets-every-key) | 성공 |
| [한 엔티티에만 수정 권한이 있으면, 그 엔티티의 라벨 둘이 오고 다른 엔티티는 키마다 하나씩 실패 목록에 온다](#partial_bulk_upserting-only-the-writable-entity-is-labeled) | 성공 |
| [RBAC 강제를 끄면 아무 권한도 없는 사용자도 엔티티 둘에 라벨을 붙이고 실패한 것은 없다](#partial_bulk_upserting-turning-enforcement-off-lets-anyone-label) | 성공 |
| [배선되지 않은 타입이 하나라도 섞여 있으면 잘못된 요청으로 통째로 거부되고 아무것도 쓰이지 않는다](#partial_bulk_upserting-an-unwired-type-refuses-the-whole-call) | 거부 |

### partial_bulk_purge

<a id="partial_bulk_purging-a-missing-id-beside-a-label-is-one-failed-item"></a>

#### [a-missing-id-beside-a-label-is-one-failed-item](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

있는 id 뒤에 없는 id 를 붙여 떼면, 있는 것은 떼어지고 없는 id 는 실패 목록에 온다

Given

- 라벨 1개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 1개 와 없는 id 1개를 한 번에 뗌

Then

- 라벨 1개가 떼어진 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 1
  - successes[0]: 미리 붙인 라벨의 id와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 id와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-nothing-purges-nothing"></a>

#### [a-user-granted-nothing-purges-nothing](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

아무 권한도 없는 사용자가 라벨 둘을 떼면, 떼어진 것 없이 둘 다 실패 목록에 온다

Given

- 라벨 2개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 2개를 한 번에 뗌

Then

- 라벨 0개가 떼어진 채 오고, 나머지는 실패 목록에 온다
  - successes count = 0
  - failed count = 2
  - failed[0].id: 요청에 넣은 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 요청에 넣은 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-a-writer-purges-labels-of-two-entities"></a>

#### [a-writer-purges-labels-of-two-entities](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

엔티티 둘에 붙은 라벨을 하나씩 떼면, 둘 다 떼어진다

Given

- 라벨 1개씩 붙은 도메인 2개와, 그중 2개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-2: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유
    - 역할 domain-writer-2: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-2: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-2 보유

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 2개를 한 번에 뗌

Then

- 라벨 2개가 떼어진 채 오고, 나머지는 실패 목록에 온다
  - successes count = 2
  - successes[0]: 미리 붙인 라벨의 id와 같다
  - successes[1]: 미리 붙인 라벨의 id와 같다
  - failed count = 0

<a id="partial_bulk_purging-a-writer-purges-two-labels-of-one-entity"></a>

#### [a-writer-purges-two-labels-of-one-entity](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

수정 권한을 받은 사용자가 한 엔티티의 라벨 둘을 떼면, 둘 다 떼어지고 실패한 것은 없다

Given

- 라벨 2개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 2개를 한 번에 뗌

Then

- 라벨 2개가 떼어진 채 오고, 나머지는 실패 목록에 온다
  - successes count = 2
  - successes[0]: 미리 붙인 라벨의 id와 같다
  - successes[1]: 미리 붙인 라벨의 id와 같다
  - failed count = 0

<a id="partial_bulk_purging-every-id-missing-is-answered-per-id"></a>

#### [every-id-missing-is-answered-per-id](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

없는 id 만 둘 떼면, 떼어진 것 없이 둘 다 실패 목록에 온다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 0개 와 없는 id 2개를 한 번에 뗌

Then

- 라벨 0개가 떼어진 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 0
  - failed count = 2
  - failed[0].id: 요청에 넣은 id와 같다
  - failed[0].message: 'not found'를 담은 이유
  - failed[1].id: 요청에 넣은 id와 같다
  - failed[1].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-only-the-label-of-the-writable-entity-is-purged"></a>

#### [only-the-label-of-the-writable-entity-is-purged](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

한 엔티티에만 수정 권한이 있으면, 그 엔티티의 라벨만 떼어지고 다른 쪽은 실패 목록에 온다

Given

- 라벨 1개씩 붙은 도메인 2개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-2: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 2개를 한 번에 뗌

Then

- 라벨 1개가 떼어진 채 오고, 나머지는 실패 목록에 온다
  - successes count = 1
  - successes[0]: 미리 붙인 라벨의 id와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-turning-enforcement-off-lets-anyone-purge"></a>

#### [turning-enforcement-off-lets-anyone-purge](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py) — pass

RBAC 강제를 끄면 아무 권한도 없는 사용자도 라벨 둘을 뗀다

Given

- 라벨 2개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- EntityLabelAdapter.partial_bulk_purge — user-1이 라벨 2개를 한 번에 뗌

Then

- 라벨 2개가 떼어진 채 오고, 나머지는 실패 목록에 온다
  - successes count = 2
  - successes[0]: 미리 붙인 라벨의 id와 같다
  - successes[1]: 미리 붙인 라벨의 id와 같다
  - failed count = 0

### partial_bulk_upsert

<a id="partial_bulk_upserting-a-key-already-on-the-entity-takes-the-new-value"></a>

#### [a-key-already-on-the-entity-takes-the-new-value](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

이미 붙은 키를 다시 붙이면, 같은 라벨이 값만 바뀌어 온다

Given

- 라벨 1개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 1개에 키 1개씩을 한 번에 붙임

Then

- 도메인 1개에 키 1개씩 붙은 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 온다
  - items count = 1
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 미리 붙인 라벨의 id와 같다
  - items[0].field_id: 미리 붙인 라벨의 id와 같다
  - failed count = 0

<a id="partial_bulk_upserting-a-user-granted-nothing-labels-nothing"></a>

#### [a-user-granted-nothing-labels-nothing](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

아무 권한도 없는 사용자가 붙이면, 붙은 라벨 없이 엔티티 둘 다 실패 목록에 온다

Given

- 도메인 2개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 2개에 키 1개씩을 한 번에 붙임

Then

- 도메인 0개에 키 1개씩 붙은 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 온다
  - items count = 0
  - failed count = 2
  - failed[0].entity_type = 'domain'
  - failed[0].entity_id: 대상 도메인의 id와 같다
  - failed[0].key = 'team'
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].entity_type = 'domain'
  - failed[1].entity_id: 대상 도메인의 id와 같다
  - failed[1].key = 'team'
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_upserting-a-writer-labels-two-entities-with-two-keys"></a>

#### [a-writer-labels-two-entities-with-two-keys](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

수정 권한을 받은 사용자가 엔티티 둘에 키 둘을 붙이면, 라벨 넷이 오고 실패한 것은 없다

Given

- 도메인 2개와, 그중 2개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유
    - 역할 domain-writer-2: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-2: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-2 보유

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 2개에 키 2개씩을 한 번에 붙임

Then

- 도메인 2개에 키 2개씩 붙은 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 온다
  - items count = 4
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].field_id: 라벨 id와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id와 같다
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].field_id: 라벨 id와 같다
  - items[2].entity_type = 'domain'
  - items[2].entity_id: 대상 도메인의 id와 같다
  - items[2].key = 'team'
  - items[2].value = 'after'
  - items[2].created_at: 이 실행이 쓴 시각
  - items[2].updated_at: 이 실행이 쓴 시각
  - items[2].id: 무시함 — 데이터베이스가 만든다
  - items[2].field_id: 라벨 id와 같다
  - items[3].entity_type = 'domain'
  - items[3].entity_id: 대상 도메인의 id와 같다
  - items[3].key = 'tier'
  - items[3].value = 'after'
  - items[3].created_at: 이 실행이 쓴 시각
  - items[3].updated_at: 이 실행이 쓴 시각
  - items[3].id: 무시함 — 데이터베이스가 만든다
  - items[3].field_id: 라벨 id와 같다
  - failed count = 0

<a id="partial_bulk_upserting-one-entity-in-several-items-gets-every-key"></a>

#### [one-entity-in-several-items-gets-every-key](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

같은 엔티티가 여러 항목에 나오면, 그 엔티티의 라벨이 키마다 오고 실패한 것은 없다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 1개에 키 2개씩을 한 번에 붙임

Then

- 도메인 1개에 키 2개씩 붙은 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 온다
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].field_id: 라벨 id와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id와 같다
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].field_id: 라벨 id와 같다
  - failed count = 0

<a id="partial_bulk_upserting-only-the-writable-entity-is-labeled"></a>

#### [only-the-writable-entity-is-labeled](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

한 엔티티에만 수정 권한이 있으면, 그 엔티티의 라벨 둘이 오고 다른 엔티티는 키마다 하나씩 실패 목록에 온다

Given

- 도메인 2개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 2개에 키 2개씩을 한 번에 붙임

Then

- 도메인 1개에 키 2개씩 붙은 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 온다
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].field_id: 라벨 id와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id와 같다
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].field_id: 라벨 id와 같다
  - failed count = 2
  - failed[0].entity_type = 'domain'
  - failed[0].entity_id: 대상 도메인의 id와 같다
  - failed[0].key = 'team'
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].entity_type = 'domain'
  - failed[1].entity_id: 대상 도메인의 id와 같다
  - failed[1].key = 'tier'
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_upserting-turning-enforcement-off-lets-anyone-label"></a>

#### [turning-enforcement-off-lets-anyone-label](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

RBAC 강제를 끄면 아무 권한도 없는 사용자도 엔티티 둘에 라벨을 붙이고 실패한 것은 없다

Given

- 도메인 2개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 2개에 키 1개씩을 한 번에 붙임

Then

- 도메인 2개에 키 1개씩 붙은 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 온다
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].field_id: 라벨 id와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id와 같다
  - items[1].key = 'team'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].field_id: 라벨 id와 같다
  - failed count = 0

<a id="partial_bulk_upserting-an-unwired-type-refuses-the-whole-call"></a>

#### [an-unwired-type-refuses-the-whole-call](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py) — pass

배선되지 않은 타입이 하나라도 섞여 있으면 잘못된 요청으로 통째로 거부되고 아무것도 쓰이지 않는다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert — user-1이 도메인 1개 와 없는 타입 하나에 키 1개씩을 한 번에 붙임

Then

- 거부된다
  - 거부: InvalidAPIParameters

