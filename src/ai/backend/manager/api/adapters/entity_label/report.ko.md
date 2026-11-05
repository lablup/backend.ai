## entity_label

[배경](/src/ai/backend/manager/api/adapters/entity_label/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/entity_label/adapter.py)

시나리오: 미완성 1 / 7

- ops 구성 (7)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_upsert: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✓
  - search_on: 대표 성공 ✓ · 대표 거부 ✓
  - upsert: 대표 성공 ✓ · 대표 거부 ✓

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 id 목록을 주면 권한 검사 없이 빈 목록이 옵니다](#batch_loading-a-batch-load-of-no-ids-answers-an-empty-list) | 성공 |
| [도메인을 읽을 수 있는 사용자가 라벨 둘과 없는 id 하나를 한 번에 조회하면, 입력 순서대로 라벨 둘과 빈 값이 옵니다](#batch_loading-a-reader-loads-two-labels-and-an-unknown-id-in-order) | 성공 |
| [아무 권한도 없는 사용자가 라벨을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-gets-a-rejection-for-the-label) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [있는 id 뒤에 없는 id 를 붙여 영구 삭제하면 있는 것은 영구 삭제되고 없는 id 는 실패 목록에 옵니다](#partial_bulk_purging-a-missing-id-beside-a-label-is-one-failed-item) | 성공 |
| [아무 권한도 없는 사용자가 라벨 둘을 영구 삭제하면 영구 삭제된 것 없이 둘 다 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-nothing) | 성공 |
| [엔티티 둘에 붙은 라벨을 하나씩 영구 삭제하면 둘 다 영구 삭제됩니다](#partial_bulk_purging-a-writer-purges-labels-of-two-entities) | 성공 |
| [수정 권한을 받은 사용자가 한 엔티티의 라벨 둘을 영구 삭제하면 둘 다 영구 삭제되고 실패한 것은 없습니다](#partial_bulk_purging-a-writer-purges-two-labels-of-one-entity) | 성공 |
| [없는 id 만 둘 영구 삭제하면 영구 삭제된 것 없이 둘 다 실패 목록에 옵니다](#partial_bulk_purging-every-id-missing-is-answered-per-id) | 성공 |
| [한 엔티티에만 수정 권한이 있으면 그 엔티티의 라벨만 영구 삭제되고 다른 쪽은 실패 목록에 옵니다](#partial_bulk_purging-only-the-label-of-the-writable-entity-is-purged) | 성공 |
| [RBAC 강제를 끄면 아무 권한도 없는 사용자도 라벨 둘을 영구 삭제합니다](#partial_bulk_purging-turning-enforcement-off-lets-anyone-purge) | 성공 |

**partial_bulk_upsert**

| 시나리오 | 판정 |
|---|---|
| [이미 붙은 키를 다시 추가하면 같은 라벨이 값만 바뀌어 옵니다](#partial_bulk_upserting-a-key-already-on-the-entity-takes-the-new-value) | 성공 |
| [아무 권한도 없는 사용자가 추가하면 라벨이 추가되지 않고 엔티티 둘 다 실패 목록에 옵니다](#partial_bulk_upserting-a-user-granted-nothing-labels-nothing) | 성공 |
| [수정 권한을 받은 사용자가 엔티티 둘에 키 둘을 추가하면 라벨 넷이 오고 실패한 것은 없습니다](#partial_bulk_upserting-a-writer-labels-two-entities-with-two-keys) | 성공 |
| [같은 엔티티가 여러 항목에 나오면 그 엔티티의 라벨이 키마다 오고 실패한 것은 없습니다](#partial_bulk_upserting-one-entity-in-several-items-gets-every-key) | 성공 |
| [한 엔티티에만 수정 권한이 있으면 그 엔티티의 라벨 둘이 오고, 다른 엔티티는 키마다 하나씩 실패 목록에 옵니다](#partial_bulk_upserting-only-the-writable-entity-is-labeled) | 성공 |
| [RBAC 강제를 끄면 아무 권한도 없는 사용자도 엔티티 둘에 라벨을 추가하고 실패한 것은 없습니다](#partial_bulk_upserting-turning-enforcement-off-lets-anyone-label) | 성공 |
| [연결 및 호출 경로로 처리되지 않는 타입이 하나라도 섞여 있으면 잘못된 요청으로 전체가 거부되고 아무것도 기록되지 않습니다](#partial_bulk_upserting-an-unwired-type-refuses-the-whole-call) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [수정 권한을 받은 사용자가 라벨 하나를 영구 삭제하면 그 라벨이 통째로 옵니다](#purging-a-writer-purges-one-label) | 성공 |
| [아무 권한도 없는 사용자가 라벨을 영구 삭제하면 요청이 거부됩니다](#purging-a-user-granted-nothing-cannot-purge-the-label) | 거부 |
| [수정 권한을 받은 사용자가 없는 라벨 id 를 영구 삭제하면 요청이 거부됩니다](#purging-an-unknown-label-id-is-refused) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [도메인 둘을 읽을 수 있는 사용자가 두 도메인의 라벨을 한 번에 훑으면, 붙인 라벨 둘이 모두 통째로 옵니다](#searching-a-reader-pages-through-the-labels-of-two-entities) | 성공 |
| [아무 권한도 없는 사용자가 도메인의 라벨을 훑으면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-cannot-page-through-the-named-scopes) | 거부 |

**search_on**

| 시나리오 | 판정 |
|---|---|
| [도메인 하나를 읽을 수 있는 사용자가 이미 쥔 그 도메인의 라벨을 키 하나로 좁혀 훑으면, 그 키의 라벨만 옵니다](#searching-a-reader-pages-through-one-entities-labels-under-a-key) | 성공 |
| [아무 권한도 없는 사용자가 이미 쥔 도메인의 라벨을 훑어도 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-cannot-page-through-a-held-scope) | 거부 |

**upsert**

| 시나리오 | 판정 |
|---|---|
| [수정 권한을 받은 사용자가 도메인에 새 키를 붙이면 그 라벨이 통째로 옵니다](#upserting-a-writer-puts-a-new-key-on-an-entity) | 성공 |
| [수정 권한을 받은 사용자가 이미 붙은 키를 다시 쓰면 같은 라벨의 값만 바뀌어 옵니다](#upserting-a-writer-replaces-the-value-of-an-existing-key) | 성공 |
| [아무 권한도 없는 사용자가 도메인에 라벨을 붙이면 권한 부족으로 거부됩니다](#upserting-a-user-granted-nothing-cannot-put-a-label-on-the-domain) | 거부 |

### batch_load_by_ids

<a id="batch_loading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/entity_label/test_batch_loading.py): pass

빈 id 목록을 주면 권한 검사 없이 빈 목록이 옵니다

Given

- 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.batch_load_by_ids: user-1이 빈 id 목록으로 일괄 조회합니다

Then

- 빈 목록이 옵니다
  - loaded = []

<a id="batch_loading-a-reader-loads-two-labels-and-an-unknown-id-in-order"></a>

#### [a-reader-loads-two-labels-and-an-unknown-id-in-order](/tests/scenario/bai_scenario/manager/entity_label/test_batch_loading.py): pass

도메인을 읽을 수 있는 사용자가 라벨 둘과 없는 id 하나를 한 번에 조회하면, 입력 순서대로 라벨 둘과 빈 값이 옵니다

Given

- 라벨 2개씩 붙은 도메인 1개와, 그중 1개를 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 조회 권한을 받은 사용자 준비
    - 역할 domain-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-reader-1: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 domain-reader-1 보유

When

- EntityLabelAdapter.batch_load_by_ids: user-1이 라벨 2개와 없는 id 하나를 한 번에 조회합니다

Then

- 미리 붙인 라벨은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 3
  - [0].entity_type = 'domain'
  - [0].entity_id: 대상 도메인의 id 와 같다
  - [0].key = 'team'
  - [0].value = 'before'
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [0].id: 미리 붙인 라벨의 id 와 같다
  - [0].field_id: 미리 붙인 라벨의 id 와 같다
  - [1].entity_type = 'domain'
  - [1].entity_id: 대상 도메인의 id 와 같다
  - [1].key = 'tier'
  - [1].value = 'before'
  - [1].created_at: 이 실행이 쓴 시각
  - [1].updated_at: 이 실행이 쓴 시각
  - [1].id: 미리 붙인 라벨의 id 와 같다
  - [1].field_id: 미리 붙인 라벨의 id 와 같다
  - [2] = None

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-for-the-label"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-the-label](/tests/scenario/bai_scenario/manager/entity_label/test_batch_loading.py): pass

아무 권한도 없는 사용자가 라벨을 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 라벨 1개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.batch_load_by_ids: user-1이 라벨 1개를 한 번에 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-missing-id-beside-a-label-is-one-failed-item"></a>

#### [a-missing-id-beside-a-label-is-one-failed-item](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

있는 id 뒤에 없는 id 를 붙여 영구 삭제하면 있는 것은 영구 삭제되고 없는 id 는 실패 목록에 옵니다

Given

- 라벨 1개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 1개와 없는 id 1개를 한 번에 영구 삭제합니다

Then

- 라벨 1개가 영구 삭제된 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0]: 미리 붙인 라벨의 id 와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-nothing-purges-nothing"></a>

#### [a-user-granted-nothing-purges-nothing](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

아무 권한도 없는 사용자가 라벨 둘을 영구 삭제하면 영구 삭제된 것 없이 둘 다 실패 목록에 옵니다

Given

- 라벨 2개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 2개를 한 번에 영구 삭제합니다

Then

- 라벨 0개가 영구 삭제된 채 오고, 나머지는 실패 목록에 옵니다
  - successes count = 0
  - failed count = 2
  - failed[0].id: 요청에 넣은 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 요청에 넣은 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-a-writer-purges-labels-of-two-entities"></a>

#### [a-writer-purges-labels-of-two-entities](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

엔티티 둘에 붙은 라벨을 하나씩 영구 삭제하면 둘 다 영구 삭제됩니다

Given

- 라벨 1개씩 붙은 도메인 2개와, 그중 2개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-2: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유
    - 역할 domain-writer-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-2: domain 전체에 READ 허용
    - 역할 domain-writer-2: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-2 보유

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 2개를 한 번에 영구 삭제합니다

Then

- 라벨 2개가 영구 삭제된 채 오고, 나머지는 실패 목록에 옵니다
  - successes count = 2
  - successes[0]: 미리 붙인 라벨의 id 와 같다
  - successes[1]: 미리 붙인 라벨의 id 와 같다
  - failed count = 0

<a id="partial_bulk_purging-a-writer-purges-two-labels-of-one-entity"></a>

#### [a-writer-purges-two-labels-of-one-entity](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

수정 권한을 받은 사용자가 한 엔티티의 라벨 둘을 영구 삭제하면 둘 다 영구 삭제되고 실패한 것은 없습니다

Given

- 라벨 2개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 2개를 한 번에 영구 삭제합니다

Then

- 라벨 2개가 영구 삭제된 채 오고, 나머지는 실패 목록에 옵니다
  - successes count = 2
  - successes[0]: 미리 붙인 라벨의 id 와 같다
  - successes[1]: 미리 붙인 라벨의 id 와 같다
  - failed count = 0

<a id="partial_bulk_purging-every-id-missing-is-answered-per-id"></a>

#### [every-id-missing-is-answered-per-id](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

없는 id 만 둘 영구 삭제하면 영구 삭제된 것 없이 둘 다 실패 목록에 옵니다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 0개와 없는 id 2개를 한 번에 영구 삭제합니다

Then

- 라벨 0개가 영구 삭제된 채 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 0
  - failed count = 2
  - failed[0].id: 요청에 넣은 id 와 같다
  - failed[0].message: 'not found'를 담은 이유
  - failed[1].id: 요청에 넣은 id 와 같다
  - failed[1].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-only-the-label-of-the-writable-entity-is-purged"></a>

#### [only-the-label-of-the-writable-entity-is-purged](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

한 엔티티에만 수정 권한이 있으면 그 엔티티의 라벨만 영구 삭제되고 다른 쪽은 실패 목록에 옵니다

Given

- 라벨 1개씩 붙은 도메인 2개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-2: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 2개를 한 번에 영구 삭제합니다

Then

- 라벨 1개가 영구 삭제된 채 오고, 나머지는 실패 목록에 옵니다
  - successes count = 1
  - successes[0]: 미리 붙인 라벨의 id 와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-turning-enforcement-off-lets-anyone-purge"></a>

#### [turning-enforcement-off-lets-anyone-purge](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

RBAC 강제를 끄면 아무 권한도 없는 사용자도 라벨 둘을 영구 삭제합니다

Given

- 라벨 2개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-1: 라벨 tier=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.partial_bulk_purge: user-1이 라벨 2개를 한 번에 영구 삭제합니다

Then

- 라벨 2개가 영구 삭제된 채 오고, 나머지는 실패 목록에 옵니다
  - successes count = 2
  - successes[0]: 미리 붙인 라벨의 id 와 같다
  - successes[1]: 미리 붙인 라벨의 id 와 같다
  - failed count = 0

### partial_bulk_upsert

<a id="partial_bulk_upserting-a-key-already-on-the-entity-takes-the-new-value"></a>

#### [a-key-already-on-the-entity-takes-the-new-value](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

이미 붙은 키를 다시 추가하면 같은 라벨이 값만 바뀌어 옵니다

Given

- 라벨 1개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 1개에 키 1개씩을 한 번에 추가합니다

Then

- 도메인 1개에 키 1개씩 추가된 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다
  - items count = 1
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 미리 붙인 라벨의 id 와 같다
  - items[0].field_id: 미리 붙인 라벨의 id 와 같다
  - failed count = 0

<a id="partial_bulk_upserting-a-user-granted-nothing-labels-nothing"></a>

#### [a-user-granted-nothing-labels-nothing](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

아무 권한도 없는 사용자가 추가하면 라벨이 추가되지 않고 엔티티 둘 다 실패 목록에 옵니다

Given

- 도메인 2개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 2개에 키 1개씩을 한 번에 추가합니다

Then

- 도메인 0개에 키 1개씩 추가된 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다
  - items count = 0
  - failed count = 2
  - failed[0].entity_type = 'domain'
  - failed[0].entity_id: 대상 도메인의 id 와 같다
  - failed[0].key = 'team'
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].entity_type = 'domain'
  - failed[1].entity_id: 대상 도메인의 id 와 같다
  - failed[1].key = 'team'
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_upserting-a-writer-labels-two-entities-with-two-keys"></a>

#### [a-writer-labels-two-entities-with-two-keys](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

수정 권한을 받은 사용자가 엔티티 둘에 키 둘을 추가하면 라벨 넷이 오고 실패한 것은 없습니다

Given

- 도메인 2개와, 그중 2개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유
    - 역할 domain-writer-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-2: domain 전체에 READ 허용
    - 역할 domain-writer-2: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-2 보유

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 2개에 키 2개씩을 한 번에 추가합니다

Then

- 도메인 2개에 키 2개씩 추가된 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다
  - items count = 4
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 라벨 id 와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id 와 같다
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 라벨 id 와 같다
  - items[2].entity_type = 'domain'
  - items[2].entity_id: 대상 도메인의 id 와 같다
  - items[2].key = 'team'
  - items[2].value = 'after'
  - items[2].created_at: 이 실행이 쓴 시각
  - items[2].updated_at: 이 실행이 쓴 시각
  - items[2].id: 건너뜀: 데이터베이스가 생성합니다
  - items[2].field_id: 라벨 id 와 같다
  - items[3].entity_type = 'domain'
  - items[3].entity_id: 대상 도메인의 id 와 같다
  - items[3].key = 'tier'
  - items[3].value = 'after'
  - items[3].created_at: 이 실행이 쓴 시각
  - items[3].updated_at: 이 실행이 쓴 시각
  - items[3].id: 건너뜀: 데이터베이스가 생성합니다
  - items[3].field_id: 라벨 id 와 같다
  - failed count = 0

<a id="partial_bulk_upserting-one-entity-in-several-items-gets-every-key"></a>

#### [one-entity-in-several-items-gets-every-key](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

같은 엔티티가 여러 항목에 나오면 그 엔티티의 라벨이 키마다 오고 실패한 것은 없습니다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 1개에 키 2개씩을 한 번에 추가합니다

Then

- 도메인 1개에 키 2개씩 추가된 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 라벨 id 와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id 와 같다
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 라벨 id 와 같다
  - failed count = 0

<a id="partial_bulk_upserting-only-the-writable-entity-is-labeled"></a>

#### [only-the-writable-entity-is-labeled](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

한 엔티티에만 수정 권한이 있으면 그 엔티티의 라벨 둘이 오고, 다른 엔티티는 키마다 하나씩 실패 목록에 옵니다

Given

- 도메인 2개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 2개에 키 2개씩을 한 번에 추가합니다

Then

- 도메인 1개에 키 2개씩 추가된 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 라벨 id 와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id 와 같다
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 라벨 id 와 같다
  - failed count = 2
  - failed[0].entity_type = 'domain'
  - failed[0].entity_id: 대상 도메인의 id 와 같다
  - failed[0].key = 'team'
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].entity_type = 'domain'
  - failed[1].entity_id: 대상 도메인의 id 와 같다
  - failed[1].key = 'tier'
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_upserting-turning-enforcement-off-lets-anyone-label"></a>

#### [turning-enforcement-off-lets-anyone-label](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

RBAC 강제를 끄면 아무 권한도 없는 사용자도 엔티티 둘에 라벨을 추가하고 실패한 것은 없습니다

Given

- 도메인 2개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 2개에 키 1개씩을 한 번에 추가합니다

Then

- 도메인 2개에 키 1개씩 추가된 라벨이 오고, 나머지 도메인은 키마다 권한이 없다는 이유로 실패 목록에 옵니다
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 라벨 id 와 같다
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id 와 같다
  - items[1].key = 'team'
  - items[1].value = 'after'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 라벨 id 와 같다
  - failed count = 0

<a id="partial_bulk_upserting-an-unwired-type-refuses-the-whole-call"></a>

#### [an-unwired-type-refuses-the-whole-call](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

연결 및 호출 경로로 처리되지 않는 타입이 하나라도 섞여 있으면 잘못된 요청으로 전체가 거부되고 아무것도 기록되지 않습니다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.partial_bulk_upsert: user-1이 도메인 1개와 없는 타입 하나에 키 1개씩을 한 번에 추가합니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

### purge

<a id="purging-a-writer-purges-one-label"></a>

#### [a-writer-purges-one-label](/tests/scenario/bai_scenario/manager/entity_label/test_purging.py): pass

수정 권한을 받은 사용자가 라벨 하나를 영구 삭제하면 그 라벨이 통째로 옵니다

Given

- 라벨 1개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.purge: user-1이 붙은 키 team 의 라벨을 영구 삭제합니다

Then

- 영구 삭제된 라벨이 통째로 옵니다
  - label.entity_type = 'domain'
  - label.entity_id: 대상 도메인의 id 와 같다
  - label.key = 'team'
  - label.value = 'before'
  - label.created_at: 이 실행이 쓴 시각
  - label.updated_at: 이 실행이 쓴 시각
  - label.id: 미리 붙인 라벨의 id 와 같다
  - label.field_id: 미리 붙인 라벨의 id 와 같다
  - field_id: 미리 붙인 라벨의 id 와 같다

<a id="purging-a-user-granted-nothing-cannot-purge-the-label"></a>

#### [a-user-granted-nothing-cannot-purge-the-label](/tests/scenario/bai_scenario/manager/entity_label/test_purging.py): pass

아무 권한도 없는 사용자가 라벨을 영구 삭제하면 요청이 거부됩니다

Given

- 라벨 1개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.purge: user-1이 붙은 키 team 의 라벨을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="purging-an-unknown-label-id-is-refused"></a>

#### [an-unknown-label-id-is-refused](/tests/scenario/bai_scenario/manager/entity_label/test_purging.py): pass

수정 권한을 받은 사용자가 없는 라벨 id 를 영구 삭제하면 요청이 거부됩니다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.purge: user-1이 없는 라벨 id 하나를 영구 삭제합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### search

<a id="searching-a-reader-pages-through-the-labels-of-two-entities"></a>

#### [a-reader-pages-through-the-labels-of-two-entities](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

도메인 둘을 읽을 수 있는 사용자가 두 도메인의 라벨을 한 번에 훑으면, 붙인 라벨 둘이 모두 통째로 옵니다

Given

- 라벨 1개씩 붙은 도메인 2개와, 그중 2개를 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-2
  - 도메인 target-1: 라벨 team=before
  - 도메인 target-2: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 조회 권한을 받은 사용자 준비
    - 역할 domain-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-reader-1: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 domain-reader-1 보유
    - 역할 domain-reader-2: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-reader-2: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 domain-reader-2 보유

When

- EntityLabelAdapter.search: user-1이 도메인 2개의 라벨을 한 번에 훑습니다

Then

- 미리 붙인 라벨 2개가 빠짐없이 통째로 옵니다
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'before'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 미리 붙인 라벨의 id 와 같다
  - items[0].field_id: 미리 붙인 라벨의 id 와 같다
  - items[1].present = True
  - items[1].entity_type = 'domain'
  - items[1].entity_id: 대상 도메인의 id 와 같다
  - items[1].key = 'team'
  - items[1].value = 'before'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].id: 미리 붙인 라벨의 id 와 같다
  - items[1].field_id: 미리 붙인 라벨의 id 와 같다

<a id="searching-a-user-granted-nothing-cannot-page-through-the-named-scopes"></a>

#### [a-user-granted-nothing-cannot-page-through-the-named-scopes](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

아무 권한도 없는 사용자가 도메인의 라벨을 훑으면 권한 부족으로 거부됩니다

Given

- 라벨 1개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.search: user-1이 도메인 1개의 라벨을 한 번에 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_on

<a id="searching-a-reader-pages-through-one-entities-labels-under-a-key"></a>

#### [a-reader-pages-through-one-entities-labels-under-a-key](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

도메인 하나를 읽을 수 있는 사용자가 이미 쥔 그 도메인의 라벨을 키 하나로 좁혀 훑으면, 그 키의 라벨만 옵니다

Given

- 라벨 2개씩 붙은 도메인 1개와, 그중 1개를 읽을 수 있는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 tier=before
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 조회 권한을 받은 사용자 준비
    - 역할 domain-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-reader-1: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 domain-reader-1 보유

When

- EntityLabelAdapter.search_on: user-1이 도메인 target-1의 라벨 중 team 키만 훑습니다

Then

- 미리 붙인 라벨 1개가 빠짐없이 통째로 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].entity_type = 'domain'
  - items[0].entity_id: 대상 도메인의 id 와 같다
  - items[0].key = 'team'
  - items[0].value = 'before'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].id: 미리 붙인 라벨의 id 와 같다
  - items[0].field_id: 미리 붙인 라벨의 id 와 같다

<a id="searching-a-user-granted-nothing-cannot-page-through-a-held-scope"></a>

#### [a-user-granted-nothing-cannot-page-through-a-held-scope](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

아무 권한도 없는 사용자가 이미 쥔 도메인의 라벨을 훑어도 권한 부족으로 거부됩니다

Given

- 라벨 1개씩 붙은 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.search_on: user-1이 도메인 target-1의 라벨 중 team 키만 훑습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### upsert

<a id="upserting-a-writer-puts-a-new-key-on-an-entity"></a>

#### [a-writer-puts-a-new-key-on-an-entity](/tests/scenario/bai_scenario/manager/entity_label/test_upserting.py): pass

수정 권한을 받은 사용자가 도메인에 새 키를 붙이면 그 라벨이 통째로 옵니다

Given

- 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.upsert: user-1이 도메인 target-1에 라벨 team=after 를 붙입니다

Then

- 붙은 라벨 하나가 통째로 옵니다
  - label.entity_type = 'domain'
  - label.entity_id: 대상 도메인의 id 와 같다
  - label.key = 'team'
  - label.value = 'after'
  - label.created_at: 이 실행이 쓴 시각
  - label.updated_at: 이 실행이 쓴 시각
  - label.id: 건너뜀: 데이터베이스가 생성합니다
  - label.field_id: 라벨 id 와 같다

<a id="upserting-a-writer-replaces-the-value-of-an-existing-key"></a>

#### [a-writer-replaces-the-value-of-an-existing-key](/tests/scenario/bai_scenario/manager/entity_label/test_upserting.py): pass

수정 권한을 받은 사용자가 이미 붙은 키를 다시 쓰면 같은 라벨의 값만 바뀌어 옵니다

Given

- 라벨 1개씩 붙은 도메인 1개와, 그중 1개에 수정 권한을 받은 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인 target-1: 라벨 team=before
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 수정 권한을 받은 사용자 준비
    - 역할 domain-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-writer-1: domain 전체에 READ 허용
    - 역할 domain-writer-1: domain 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 domain-writer-1 보유

When

- EntityLabelAdapter.upsert: user-1이 도메인 target-1에 라벨 team=after 를 붙입니다

Then

- 이미 붙은 같은 라벨의 값만 바뀌어 옵니다
  - label.entity_type = 'domain'
  - label.entity_id: 대상 도메인의 id 와 같다
  - label.key = 'team'
  - label.value = 'after'
  - label.created_at: 이 실행이 쓴 시각
  - label.updated_at: 이 실행이 쓴 시각
  - label.id: 미리 붙인 라벨의 id 와 같다
  - label.field_id: 미리 붙인 라벨의 id 와 같다

<a id="upserting-a-user-granted-nothing-cannot-put-a-label-on-the-domain"></a>

#### [a-user-granted-nothing-cannot-put-a-label-on-the-domain](/tests/scenario/bai_scenario/manager/entity_label/test_upserting.py): pass

아무 권한도 없는 사용자가 도메인에 라벨을 붙이면 권한 부족으로 거부됩니다

Given

- 도메인 1개와, user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- EntityLabelAdapter.upsert: user-1이 도메인 target-1에 라벨 team=after 를 붙입니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

