## model_card

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

시나리오: 미완 13 / 16

- ops 로 구성 (8)
  - admin_search — 대표 성공 ✓ · 대표 실패 ✓
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - create — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - min_resources — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - ownership_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - project_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - scoped_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- ops + 직접 구현 (3)
  - deploy — 성공 없음 · 실패 없음 (scope, single_get_ops) — SCENARIO-GAP
  - partial_bulk_update — 성공 있음 2 · 실패 없음 (atomic_bulk_scoped_search_ops, partial_bulk) — SCENARIO-GAP
  - update — 성공 있음 1 · 실패 있음 1 (atomic_bulk_scoped_search_ops, single_entity)
- 직접 구현 (4)
  - admin_bulk_delete — 성공 없음 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - partial_bulk_purge — 성공 있음 3 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - purge — 성공 있음 1 · 실패 있음 1 (single_entity)
  - scan_project — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
- Action 없음 (1)
  - available_presets — 성공 없음 · 실패 없음 — SCENARIO-GAP

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [모델 카드를 하나도 심지 않은 상태에서 슈퍼관리자가 전체 조회를 하면, 답은 비어 있다](#model_card-a-scenario-that-laid-no-model-card-finds-none) | 성공 |
| [슈퍼관리자가 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 막힌다](#model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 카드 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-model-cards) | 성공 |
| [프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드 여럿의 제목을 한 번에 바꾸면, 모두 새 제목으로 오고 실패한 것은 없다](#partial_bulk_editing-a-user-granted-update-edits-several-model-cards) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드의 제목을 바꾸면, 제목은 새 값이 되고 나머지는 그대로 남는다](#editing-a-user-granted-update-in-the-project-edits-a-model-card) | 성공 |
| [아무 권한도 받지 않은 사용자가 모델 카드를 수정하려 하면 권한 부족으로 거부된다](#editing-a-user-granted-nothing-may-not-edit-a-model-card) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 카드 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-model-cards) | 성공 |
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 purge 하면, 둘 다 처리된 목록에 오고 실패한 것은 없다](#partial_bulk_purging-a-user-granted-purge-purges-several-model-cards) | 성공 |
| [슈퍼관리자가 카드 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다. 권한 검사는 슈퍼관리자를 먼저 통과시키므로 없는 id 가 purge 까지 간다](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드를 purge 하면, 그 카드의 id 가 온다](#purging-a-user-granted-purge-in-the-project-purges-a-model-card) | 성공 |
| [아무 권한도 받지 않은 사용자가 모델 카드를 purge 하려 하면 권한 부족으로 거부된다](#purging-a-user-granted-nothing-may-not-purge-a-model-card) | 거부 |

### admin_search

<a id="model_card-a-scenario-that-laid-no-model-card-finds-none"></a>

#### [a-scenario-that-laid-no-model-card-finds-none](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

모델 카드를 하나도 심지 않은 상태에서 슈퍼관리자가 전체 조회를 하면, 답은 비어 있다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-model-card](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

슈퍼관리자가 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 막힌다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-model-cards"></a>

#### [a-user-granted-nothing-edits-none-of-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 카드 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 모델 카드 2개가 놓인 프로젝트와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 프로젝트 폴더 folder-2: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-2: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'

When

- ModelCardAdapter.partial_bulk_update — user-2이 카드 2개의 제목을 한 번에 고침

Then

- 처리된 카드 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 카드의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 카드의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-a-user-granted-update-edits-several-model-cards"></a>

#### [a-user-granted-update-edits-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py) — pass

프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드 여럿의 제목을 한 번에 바꾸면, 모두 새 제목으로 오고 실패한 것은 없다

Given

- 모델 카드 2개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 프로젝트 폴더 folder-2: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-2: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.partial_bulk_update — user-2이 카드 2개의 제목을 한 번에 고침

Then

- 대상 카드가 모두 새 제목으로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만든 카드와 같다
  - successes[0].entity_id: 미리 만든 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 얹힌 폴더와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '고쳐 쓴 제목'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 카드와 같다
  - successes[1].entity_id: 미리 만든 카드와 같다
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: 카드가 얹힌 폴더와 같다
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: 카드가 놓인 프로젝트와 같다
  - successes[1].creator_id: 카드를 만든 사람와 같다
  - successes[1].metadata.author = None
  - successes[1].metadata.title = '고쳐 쓴 제목'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### update

<a id="editing-a-user-granted-update-in-the-project-edits-a-model-card"></a>

#### [a-user-granted-update-in-the-project-edits-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_editing.py) — pass

프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드의 제목을 바꾸면, 제목은 새 값이 되고 나머지는 그대로 남는다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 READ, UPDATE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 card-handler-1: model_card 전체에 READ 허용
    - 역할 card-handler-1: model_card 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.update — user-2이 card-1의 제목을 고침

Then

- 제목은 새 값이 되고 나머지는 그대로인 카드 전체
  - id: 미리 만든 카드와 같다
  - entity_id: 미리 만든 카드와 같다
  - name = 'card-1'
  - vfolder_id: 카드가 얹힌 폴더와 같다
  - domain_name = 'home-1'
  - project_id: 카드가 놓인 프로젝트와 같다
  - creator_id: 카드를 만든 사람와 같다
  - metadata.author = None
  - metadata.title = '고쳐 쓴 제목'
  - metadata.model_version = None
  - metadata.description = None
  - metadata.task = None
  - metadata.category = None
  - metadata.architecture = None
  - metadata.framework = []
  - metadata.label = []
  - metadata.license = None
  - min_resource = None
  - readme = None
  - access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-edit-a-model-card"></a>

#### [a-user-granted-nothing-may-not-edit-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 모델 카드를 수정하려 하면 권한 부족으로 거부된다

Given

- 모델 카드 1개가 놓인 프로젝트와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'

When

- ModelCardAdapter.update — user-2이 card-1의 제목을 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-model-cards"></a>

#### [a-user-granted-nothing-purges-none-of-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 카드 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 모델 카드 2개가 놓인 프로젝트와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 프로젝트 폴더 folder-2: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-2: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'

When

- ModelCardAdapter.partial_bulk_purge — user-2이 카드 2개를 한 번에 purge 함

Then

- 처리된 카드 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 카드의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 카드의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-model-cards"></a>

#### [a-user-granted-purge-purges-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py) — pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 purge 하면, 둘 다 처리된 목록에 오고 실패한 것은 없다

Given

- 모델 카드 2개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 프로젝트 폴더 folder-2: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-2: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.partial_bulk_purge — user-2이 카드 2개를 한 번에 purge 함

Then

- 대상 카드가 모두 처리된 목록에 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만든 카드와 같다
  - successes[0].entity_id: 미리 만든 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 얹힌 폴더와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '이미 있던 카드'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 카드와 같다
  - successes[1].entity_id: 미리 만든 카드와 같다
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: 카드가 얹힌 폴더와 같다
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: 카드가 놓인 프로젝트와 같다
  - successes[1].creator_id: 카드를 만든 사람와 같다
  - successes[1].metadata.author = None
  - successes[1].metadata.title = '이미 있던 카드'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py) — pass

슈퍼관리자가 카드 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다. 권한 검사는 슈퍼관리자를 먼저 통과시키므로 없는 id 가 purge 까지 간다

Given

- 모델 카드 2개가 놓인 프로젝트와, 아무 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 프로젝트 폴더 folder-2: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-2: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'

When

- ModelCardAdapter.partial_bulk_purge — user-2이 카드 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 대상 카드가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만든 카드와 같다
  - successes[0].entity_id: 미리 만든 카드와 같다
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: 카드가 얹힌 폴더와 같다
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: 카드가 놓인 프로젝트와 같다
  - successes[0].creator_id: 카드를 만든 사람와 같다
  - successes[0].metadata.author = None
  - successes[0].metadata.title = '이미 있던 카드'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 만든 카드와 같다
  - successes[1].entity_id: 미리 만든 카드와 같다
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: 카드가 얹힌 폴더와 같다
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: 카드가 놓인 프로젝트와 같다
  - successes[1].creator_id: 카드를 만든 사람와 같다
  - successes[1].metadata.author = None
  - successes[1].metadata.title = '이미 있던 카드'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'No such model card'를 담은 이유

### purge

<a id="purging-a-user-granted-purge-in-the-project-purges-a-model-card"></a>

#### [a-user-granted-purge-in-the-project-purges-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_purging.py) — pass

프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드를 purge 하면, 그 카드의 id 가 온다

Given

- 모델 카드 1개가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 HARD_DELETE 권한을 받은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'
  - 모델 카드 권한 부여
    - 역할 card-handler-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 card-handler-1: model_card 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 card-handler-1 보유

When

- ModelCardAdapter.purge — user-2이 card-1을 purge 함, 폴더는 그대로 둠

Then

- purge 한 카드의 id
  - id: 미리 만든 카드와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-model-card"></a>

#### [a-user-granted-nothing-may-not-purge-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_purging.py) — pass

아무 권한도 받지 않은 사용자가 모델 카드를 purge 하려 하면 권한 부족으로 거부된다

Given

- 모델 카드 1개가 놓인 프로젝트와, 아무 권한도 받지 않은 user 한 명
  - 도메인 home-1: 이 도메인의 폴더는 local:volume1에 놓을 수 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 model-store-1
  - 프로젝트 폴더 folder-1: 프로젝트에 놓이고, 쓸 수 있는 상태다
  - 모델 카드 card-1: 프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '이미 있던 카드'

When

- ModelCardAdapter.purge — user-2이 card-1을 purge 함, 폴더는 그대로 둠

Then

- 거부된다
  - 거부: NotEnoughPermission

