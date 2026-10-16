## reservoir_registry

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/reservoir_registry/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/reservoir_registry/adapter.py)

시나리오: 미완 7 / 9

- ops 로 구성 (1)
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- 직접 구현 (8)
  - create — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - get — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - get_many — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - partial_bulk_purge — 성공 있음 3 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - partial_bulk_update — 성공 있음 2 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - purge — 성공 있음 1 · 실패 있음 1 (single_entity)
  - search — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - update — 성공 있음 1 · 실패 있음 1 (single_entity)

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries) | 성공 |
| [레지스트리 purge 권한을 받은 사용자가 여럿을 한 번에 purge 하면, 모두의 id 가 처리된 목록에 오고 실패한 것은 없다](#partial_bulk_purging-a-user-granted-purge-purges-several-registries) | 성공 |
| [슈퍼관리자가 레지스트리 둘과 없는 id 하나를 한 번에 purge 하면, 둘의 id 는 처리된 목록에, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다. 슈퍼관리자는 검사를 모두 통과하므로 대상 없음이 그대로 드러난다](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries) | 성공 |
| [레지스트리 수정 권한을 받은 사용자가 여럿의 엔드포인트를 한 번에 바꾸면, 모두 새 엔드포인트로 오고 실패한 것은 없다](#partial_bulk_editing-a-user-granted-update-edits-several-registries) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [레지스트리 purge 권한을 받은 사용자가 purge 하면, purge 한 레지스트리의 id 가 온다](#purging-a-user-granted-purge-purges-a-registry) | 성공 |
| [아무 권한도 받지 않은 사용자가 purge 하려 하면 권한 부족으로 거부된다](#purging-a-user-granted-nothing-may-not-purge-a-registry) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [레지스트리 수정 권한을 받은 사용자가 엔드포인트를 바꾸면, 그 레지스트리가 새 엔드포인트로 온다](#editing-a-user-granted-update-edits-a-registry) | 성공 |
| [아무 권한도 받지 않은 사용자가 엔드포인트를 바꾸려 하면 권한 부족으로 거부된다](#editing-a-user-granted-nothing-may-not-edit-a-registry) | 거부 |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries"></a>

#### [a-user-granted-nothing-purges-none-of-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ReservoirRegistryAdapter.partial_bulk_purge — user-1이 레지스트리 2개를 한 번에 purge 함

Then

- 처리된 레지스트리 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 레지스트리의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 레지스트리의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-registries"></a>

#### [a-user-granted-purge-purges-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py) — pass

레지스트리 purge 권한을 받은 사용자가 여럿을 한 번에 purge 하면, 모두의 id 가 처리된 목록에 오고 실패한 것은 없다

Given

- Reservoir 레지스트리 2개와, 레지스트리에 HARD_DELETE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 registry-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 registry-keeper-1: artifact_registry 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.partial_bulk_purge — user-1이 레지스트리 2개를 한 번에 purge 함

Then

- 대상 레지스트리의 id 가 모두 처리된 목록에 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만들어 둔 레지스트리의 id와 같다
  - successes[1].id: 미리 만들어 둔 레지스트리의 id와 같다
  - failed = []

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py) — pass

슈퍼관리자가 레지스트리 둘과 없는 id 하나를 한 번에 purge 하면, 둘의 id 는 처리된 목록에, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다. 슈퍼관리자는 검사를 모두 통과하므로 대상 없음이 그대로 드러난다

Given

- Reservoir 레지스트리 2개와, 슈퍼관리자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ReservoirRegistryAdapter.partial_bulk_purge — user-1이 레지스트리 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 대상 레지스트리의 id 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만들어 둔 레지스트리의 id와 같다
  - successes[1].id: 미리 만들어 둔 레지스트리의 id와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries"></a>

#### [a-user-granted-nothing-edits-none-of-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- Reservoir 레지스트리 2개와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ReservoirRegistryAdapter.partial_bulk_update — user-1이 레지스트리 2개의 엔드포인트를 한 번에 바꿈

Then

- 처리된 레지스트리 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 레지스트리의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 레지스트리의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-a-user-granted-update-edits-several-registries"></a>

#### [a-user-granted-update-edits-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_editing.py) — pass

레지스트리 수정 권한을 받은 사용자가 여럿의 엔드포인트를 한 번에 바꾸면, 모두 새 엔드포인트로 오고 실패한 것은 없다

Given

- Reservoir 레지스트리 2개와, 레지스트리에 UPDATE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - Reservoir 레지스트리 registry-2: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 registry-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 registry-keeper-1: artifact_registry 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.partial_bulk_update — user-1이 레지스트리 2개의 엔드포인트를 한 번에 바꿈

Then

- 대상 레지스트리가 모두 새 엔드포인트로 오고, 실패한 것은 없다
  - successes count = 2
  - failed = []
  - successes[0].id: 미리 만들어 둔 레지스트리의 id와 같다
  - successes[0].entity_id: 미리 만들어 둔 레지스트리의 id와 같다
  - successes[0].name = 'registry-1'
  - successes[0].endpoint = 'https://storage.example.com'
  - successes[0].access_key = 'access-key'
  - successes[0].secret_key = 'secret-key'
  - successes[0].api_version = 'v1'
  - successes[1].id: 미리 만들어 둔 레지스트리의 id와 같다
  - successes[1].entity_id: 미리 만들어 둔 레지스트리의 id와 같다
  - successes[1].name = 'registry-2'
  - successes[1].endpoint = 'https://storage.example.com'
  - successes[1].access_key = 'access-key'
  - successes[1].secret_key = 'secret-key'
  - successes[1].api_version = 'v1'

### purge

<a id="purging-a-user-granted-purge-purges-a-registry"></a>

#### [a-user-granted-purge-purges-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_purging.py) — pass

레지스트리 purge 권한을 받은 사용자가 purge 하면, purge 한 레지스트리의 id 가 온다

Given

- Reservoir 레지스트리 하나와, 레지스트리에 HARD_DELETE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 registry-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 registry-keeper-1: artifact_registry 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.purge — user-1이 registry-1을 purge 함

Then

- purge 한 레지스트리의 id 가 온다
  - id: 미리 만들어 둔 레지스트리의 id와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-registry"></a>

#### [a-user-granted-nothing-may-not-purge-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_purging.py) — pass

아무 권한도 받지 않은 사용자가 purge 하려 하면 권한 부족으로 거부된다

Given

- Reservoir 레지스트리 하나와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ReservoirRegistryAdapter.purge — user-1이 registry-1을 purge 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### update

<a id="editing-a-user-granted-update-edits-a-registry"></a>

#### [a-user-granted-update-edits-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_editing.py) — pass

레지스트리 수정 권한을 받은 사용자가 엔드포인트를 바꾸면, 그 레지스트리가 새 엔드포인트로 온다

Given

- Reservoir 레지스트리 하나와, 레지스트리에 UPDATE 권한을 받은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 registry-keeper-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 registry-keeper-1: artifact_registry 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 registry-keeper-1 보유

When

- ReservoirRegistryAdapter.update — user-1이 registry-1의 엔드포인트를 바꿈

Then

- 미리 만들어 둔 레지스트리가 새 엔드포인트로 온다
  - id: 미리 만들어 둔 레지스트리의 id와 같다
  - entity_id: 미리 만들어 둔 레지스트리의 id와 같다
  - name = 'registry-1'
  - endpoint = 'https://storage.example.com'
  - access_key = 'access-key'
  - secret_key = 'secret-key'
  - api_version = 'v1'

<a id="editing-a-user-granted-nothing-may-not-edit-a-registry"></a>

#### [a-user-granted-nothing-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 엔드포인트를 바꾸려 하면 권한 부족으로 거부된다

Given

- Reservoir 레지스트리 하나와, 아무 권한도 받지 않은 일반 사용자 한 명
  - Reservoir 레지스트리 registry-1: https://reservoir.example.com 을 가리킨다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ReservoirRegistryAdapter.update — user-1이 registry-1의 엔드포인트를 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

