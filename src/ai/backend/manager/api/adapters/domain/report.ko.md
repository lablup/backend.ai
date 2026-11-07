## domain

[배경](/src/ai/backend/manager/api/adapters/domain/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/domain/adapter.py)

시나리오: 미완성 3 / 15

- ops 구성 (12)
  - bulk_get_ids: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_lookup_names: 대표 성공 ✓ · 대표 거부 ✓
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - global_search: 대표 성공 ✓ · 대표 거부 ✓
  - lookup_name: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_delete: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_restore: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - restore: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
- ops + 직접 구현 (1)
  - sync_registry_relations: 성공 있음 3 · 거부 있음 1 (global_searcher_ops, relation, scope)
- 직접 구현 (2)
  - create: 성공 있음 2 · 거부 있음 4 (global_scope)
  - purge: 성공 있음 1 · 거부 있음 4 (single_entity)

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 id 로 도메인 여럿을 읽으면, 그 항목에 도메인이 응답으로 옵니다](#bulk_reading-the-superadmin-reads-domains-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 id 로 도메인 여럿을 읽으면, 그 항목이 권한 부족으로 거부됩니다](#bulk_reading-a-user-granted-nothing-may-not-read-domains-by-id) | 거부 |

**bulk_lookup_names**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 조회해도 superadmin 과 같은 응답이 옵니다. 이 호출은 인증만 확인하므로 이름이 있는지는 누구에게나 드러납니다](#looking_up-a-user-granted-nothing-gets-the-same-ids-by-name) | 성공 |
| [superadmin 이 있는 이름과 없는 이름으로 id 를 여럿 조회하면, 있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 응답으로 옵니다](#looking_up-the-superadmin-looks-up-domains-by-name) | 성공 |
| [로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다](#looking_up-looking-up-domains-by-name-without-login-is-refused) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [이미 soft delete 된 도메인을 superadmin 이 다시 soft delete 하면, soft delete 했다는 응답이 옵니다](#deleting-soft-deleting-a-domain-already-soft-deleted) | 성공 |
| [superadmin 이 도메인을 soft delete 하면, soft delete 했다는 응답이 옵니다](#deleting-the-superadmin-soft-deletes-a-domain) | 성공 |
| [아무 권한도 받지 않은 사용자는 도메인을 soft delete 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-soft-delete-a-domain) | 거부 |
| [아무 도메인도 갖지 않은 이름을 soft delete 하려 하면 대상이 없다는 것으로 거부됩니다](#deleting-soft-deleting-a-name-nothing-answers-to-is-not-found) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [도메인 하나가 있고 superadmin 이 이름으로 조회하면, 그 도메인이 응답으로 옵니다](#reading-the-superadmin-reads-a-domain-by-name) | 성공 |
| [superadmin 이 도메인을 soft delete 한 뒤 이름으로 조회하면, 비활성 상태를 담은 그 도메인이 응답으로 옵니다](#reading-the-superadmin-reads-a-soft-deleted-domain-by-name) | 성공 |
| [같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, 이름으로 조회하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-a-domain) | 거부 |
| [superadmin 이 존재하지 않는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다](#reading-reading-a-name-nothing-answers-to-is-not-found) | 거부 |

**global_search**

| 시나리오 | 판정 |
|---|---|
| [도메인 여럿 중 하나의 이름으로 필터 기반 조회하면, 응답에는 그 이름의 도메인만 남습니다](#searching-a-name-filter-narrows-the-answer-to-the-domain-it-names) | 성공 |
| [이 시나리오가 미리 저장한 도메인이 넷일 때, 필터 없는 조회는 그 넷이 모두 나옵니다](#searching-the-answer-counts-every-domain-the-scenario-laid) | 성공 |
| [미리 저장한 도메인 중 하나를 soft delete 한 뒤 필터 없이 search 하면, 그것까지 모두 나옵니다](#searching-the-answer-includes-soft-deleted-domains-too) | 성공 |
| [superadmin 이 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-domain) | 거부 |

**lookup_name**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자도 도메인 이름으로 id 를 조회할 수 있습니다. 이 호출은 인증만 확인하고, 권한은 그 id 를 받는 호출이 확인합니다](#looking_up-a-user-granted-nothing-still-looks-up-a-domain-by-name) | 성공 |
| [superadmin 이 도메인 이름으로 id 를 조회하면, 그 도메인의 id 가 응답으로 옵니다](#looking_up-the-superadmin-looks-up-a-domain-by-name) | 성공 |
| [아무 도메인도 갖지 않은 이름으로 id 를 조회하면 대상이 없다는 것으로 거부됩니다](#looking_up-looking-up-a-name-nothing-answers-to-is-not-found) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-domains) | 성공 |
| [활성 도메인 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성 상태로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 도메인 여럿을 한 번에 restore 하면, 모두 활성 상태로 옵니다](#partial_bulk_deleting-restoring-several-brings-them-back) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-domains) | 성공 |
| [활성 플래그와 설명을 섞어 도메인 여럿을 한 번에 수정하면, 플래그를 비활성화한 것은 soft delete 되고 활성화한 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-domains) | 성공 |
| [superadmin 이 도메인 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-domains-at-once) | 성공 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 되지 않은 도메인을 superadmin 이 restore 하면, restore 했다는 응답이 옵니다](#deleting-restoring-a-domain-that-is-not-soft-deleted) | 성공 |
| [soft delete 된 도메인을 restore 하면, restore 했다는 응답이 옵니다](#deleting-restoring-answers-that-it-restored) | 성공 |
| [아무 권한도 받지 않은 사용자는 도메인을 restore 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-restore-a-domain) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹 범위에서 도메인 읽기 역할을 받은 사용자가 그 범위에서 search 하면, superadmin 과 같은 도메인들이 응답으로 옵니다](#scoped_searching-a-user-granted-read-in-the-group-searches-its-domains) | 성공 |
| [superadmin 이 리소스 그룹 범위에서 search 하면, 그 그룹을 쓸 수 있는 도메인만 응답으로 옵니다](#scoped_searching-the-superadmin-searches-the-domains-of-a-resource-group) | 성공 |
| [아무 권한도 받지 않은 사용자가 리소스 그룹 범위에서 search 하면 권한 부족으로 거부됩니다](#scoped_searching-a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [활성 플래그를 비활성화하는 수정은 도메인을 soft delete 하고, 응답이 비활성 상태를 담아 옵니다](#editing-clearing-the-active-flag-soft-deletes-a-domain) | 성공 |
| [superadmin 이 도메인의 설명만 변경하면, 설명은 새 값이 되고 이름은 그대로 남습니다](#editing-editing-a-description-leaves-the-name-alone) | 성공 |
| [soft delete 된 도메인의 활성 플래그를 비활성화하며 설명을 변경하면, 설명은 새 값이 되고 비활성 상태는 그대로입니다](#editing-lowering-the-active-flag-of-a-soft-deleted-domain-edits-only-the-rest) | 성공 |
| [soft delete 된 도메인의 활성 플래그를 활성화하는 수정은 그 도메인을 restore 하고, 응답이 활성 상태를 담아 옵니다](#editing-raising-the-active-flag-restores-a-soft-deleted-domain) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-a-domain) | 거부 |
| [아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부됩니다](#editing-editing-a-name-nothing-answers-to-is-not-found) | 거부 |

**sync_registry_relations**

| 시나리오 | 판정 |
|---|---|
| [어떤 레지스트리와도 맞지 않는 이름으로 맞추면 오류 없이 relation 이 생기지 않습니다 (이름으로 레지스트리를 찾는 일은 전역 역할로 막혀 있어 슈퍼관리자가 호출합니다)](#syncing_registry_relations-a-name-no-registry-carries-links-nothing) | 성공 |
| [relation 이 있는 레지스트리를 빼고 빈 목록으로 맞추면 그 relation 이 지워집니다 (이름으로 레지스트리를 찾는 일은 전역 역할로 막혀 있어 슈퍼관리자가 호출합니다)](#syncing_registry_relations-leaving-a-linked-registry-out-unlinks-it) | 성공 |
| [슈퍼관리자가 레지스트리의 이름으로 맞추면 도메인과 그 레지스트리 사이에 relation 이 생깁니다 (이름으로 레지스트리를 찾는 일은 전역 역할로 막혀 있어 슈퍼관리자가 호출합니다)](#syncing_registry_relations-naming-a-registry-links-the-domain-to-it) | 성공 |
| [슈퍼관리자가 아닌 사용자가 relation 을 맞추려 하면 거부됩니다. 이름으로 레지스트리를 찾는 일은 슈퍼관리자 역할이 있어야만 실행됩니다](#syncing_registry_relations-a-user-granted-nothing-may-not-sync-registry-relations) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 도메인을 생성하면 model-store 프로젝트가 함께 생성되어, 그 프로젝트를 가진 도메인으로 필터 기반 조회할 때 생성한 도메인이 응답으로 옵니다](#creating-creating-a-domain-also-creates-its-model-store-project) | 성공 |
| [superadmin 이 이름과 설명만 지정하고 도메인을 생성하면, 요청에 없던 값들은 기본값으로 채워진 노드 전체가 응답으로 옵니다](#creating-creating-a-domain-answers-with-the-whole-node) | 성공 |
| [이름이 공백뿐이면 도메인을 생성할 수 없습니다](#creating-a-blank-name-is-refused) | 거부 |
| [이미 어떤 도메인이 쓰고 있는 이름으로 생성하려 하면, 권한이 있어도 이름이 겹친다는 이유로 거부됩니다](#creating-a-name-another-domain-already-holds-is-refused) | 거부 |
| [superadmin 이 아닌 사용자가 도메인을 생성하려 하면, 권한을 얼마나 받았는지와 무관하게 역할로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-domain) | 거부 |
| [엔티티 권한 집행을 꺼도 도메인 생성은 여전히 거부됩니다. 이 동작은 권한 그래프가 아니라 역할이 검사하기 때문입니다](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-domain) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [아무것도 딸려 있지 않은 도메인은 purge 할 수 있습니다](#deleting-purging-a-domain-nothing-else-refers-to-succeeds) | 성공 |
| [프로젝트가 딸린 도메인은 superadmin 이라도 purge 할 수 없습니다](#deleting-a-domain-holding-a-project-is-not-purged) | 거부 |
| [사용자가 딸린 도메인은 superadmin 이라도 purge 할 수 없습니다](#deleting-a-domain-holding-a-user-is-not-purged) | 거부 |
| [아무 권한도 받지 않은 사용자는 아무것도 딸리지 않은 도메인이라도 purge 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-purge-a-domain) | 거부 |
| [아무 도메인도 갖지 않은 이름을 purge 하려 하면 대상이 없다는 것으로 거부됩니다](#deleting-purging-a-name-nothing-answers-to-is-not-found) | 거부 |

### bulk_get_ids

<a id="bulk_reading-the-superadmin-reads-domains-by-id"></a>

#### [the-superadmin-reads-domains-by-id](/tests/scenario/bai_scenario/manager/domain/test_bulk_reading.py): pass

superadmin 이 id 로 도메인 여럿을 읽으면, 그 항목에 도메인이 응답으로 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.bulk_get_ids: user-1이 target-1의 id 로 여럿을 읽습니다

Then

- 물은 항목에 미리 저장한 도메인 전체가 응답으로 옵니다
  - [0].name = 'target-1'
  - [0].description = '이미 있던 도메인'
  - [0].integration_name = None
  - [0].allowed_docker_registries = []
  - [0].is_active = True
  - [0].is_default = False
  - [0].id: 건너뜀: 데이터베이스가 생성합니다
  - [0].entity_id: 미리 저장한 도메인의 id 와 같다
  - [0].created_at: 이 실행이 쓴 시각
  - [0].modified_at: 이 실행이 쓴 시각

<a id="bulk_reading-a-user-granted-nothing-may-not-read-domains-by-id"></a>

#### [a-user-granted-nothing-may-not-read-domains-by-id](/tests/scenario/bai_scenario/manager/domain/test_bulk_reading.py): pass

아무 권한도 받지 않은 사용자가 id 로 도메인 여럿을 읽으면, 그 항목이 권한 부족으로 거부됩니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.bulk_get_ids: user-1이 target-1의 id 로 여럿을 읽습니다

Then

- 물은 항목이 거부됩니다
  - 거부: NotEnoughPermission

### bulk_lookup_names

<a id="looking_up-a-user-granted-nothing-gets-the-same-ids-by-name"></a>

#### [a-user-granted-nothing-gets-the-same-ids-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

아무 권한도 받지 않은 사용자가 조회해도 superadmin 과 같은 응답이 옵니다. 이 호출은 인증만 확인하므로 이름이 있는지는 누구에게나 드러납니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.bulk_lookup_names: user-1이 target-1과 no-such-domain 의 id 를 여럿을 조회합니다

Then

- 있는 이름의 항목에 그 도메인의 id 가, 없는 이름의 항목에 빈 값이 응답으로 옵니다
  - [0]: 미리 저장한 도메인의 id 와 같다
  - [1] = None

<a id="looking_up-the-superadmin-looks-up-domains-by-name"></a>

#### [the-superadmin-looks-up-domains-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

superadmin 이 있는 이름과 없는 이름으로 id 를 여럿 조회하면, 있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 응답으로 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.bulk_lookup_names: user-1이 target-1과 no-such-domain 의 id 를 여럿을 조회합니다

Then

- 있는 이름의 항목에 그 도메인의 id 가, 없는 이름의 항목에 빈 값이 응답으로 옵니다
  - [0]: 미리 저장한 도메인의 id 와 같다
  - [1] = None

<a id="looking_up-looking-up-domains-by-name-without-login-is-refused"></a>

#### [looking-up-domains-by-name-without-login-is-refused](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 거부됩니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.bulk_lookup_names: 로그인 문맥 없이 target-1의 id 를 여럿을 조회합니다

Then

- 거부됩니다
  - 거부: UserNotFound

### delete

<a id="deleting-soft-deleting-a-domain-already-soft-deleted"></a>

#### [soft-deleting-a-domain-already-soft-deleted](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

이미 soft delete 된 도메인을 superadmin 이 다시 soft delete 하면, soft delete 했다는 응답이 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 twice-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.delete: user-1이 twice-1을 두 번 soft delete 합니다

Then

- 했다는 응답이 옵니다
  - deleted = True

<a id="deleting-the-superadmin-soft-deletes-a-domain"></a>

#### [the-superadmin-soft-deletes-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

superadmin 이 도메인을 soft delete 하면, soft delete 했다는 응답이 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 to-delete-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.delete: user-1이 to-delete-1을 soft delete 합니다

Then

- 했다는 응답이 옵니다
  - deleted = True

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-domain"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 도메인을 soft delete 할 수 없습니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 untouchable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.delete: user-1이 untouchable-1을 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deleting-soft-deleting-a-name-nothing-answers-to-is-not-found"></a>

#### [soft-deleting-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

아무 도메인도 갖지 않은 이름을 soft delete 하려 하면 대상이 없다는 것으로 거부됩니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.delete: user-1이 no-such-domain 을 soft delete 합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### get

<a id="reading-the-superadmin-reads-a-domain-by-name"></a>

#### [the-superadmin-reads-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

도메인 하나가 있고 superadmin 이 이름으로 조회하면, 그 도메인이 응답으로 옵니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.get: user-1이 host-1으로 조회합니다

Then

- 미리 저장한 도메인 전체가 응답으로 옵니다
  - name = 'host-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 도메인의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="reading-the-superadmin-reads-a-soft-deleted-domain-by-name"></a>

#### [the-superadmin-reads-a-soft-deleted-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

superadmin 이 도메인을 soft delete 한 뒤 이름으로 조회하면, 비활성 상태를 담은 그 도메인이 응답으로 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 soft-deleted-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.get: user-1이 soft-deleted-1을 soft delete 한 뒤 이름으로 조회합니다

Then

- 미리 저장한 도메인 전체가 응답으로 옵니다
  - name = 'soft-deleted-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 도메인의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="reading-a-user-granted-nothing-may-not-read-a-domain"></a>

#### [a-user-granted-nothing-may-not-read-a-domain](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, 이름으로 조회하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.get: user-1이 host-1으로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="reading-reading-a-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

superadmin 이 존재하지 않는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.get: user-1이 no-such-domain 으로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### global_search

<a id="searching-a-name-filter-narrows-the-answer-to-the-domain-it-names"></a>

#### [a-name-filter-narrows-the-answer-to-the-domain-it-names](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

도메인 여럿 중 하나의 이름으로 필터 기반 조회하면, 응답에는 그 이름의 도메인만 남습니다

Given

- 도메인 4개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.global_search: user-1이 wanted-1으로 필터 기반 조회합니다

Then

- 필터로 걸러낸 그 도메인 하나만 남습니다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-answer-counts-every-domain-the-scenario-laid"></a>

#### [the-answer-counts-every-domain-the-scenario-laid](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

이 시나리오가 미리 저장한 도메인이 넷일 때, 필터 없는 조회는 그 넷이 모두 나옵니다

Given

- 도메인 4개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.global_search: user-1이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 도메인이 모두 나옵니다
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-answer-includes-soft-deleted-domains-too"></a>

#### [the-answer-includes-soft-deleted-domains-too](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

미리 저장한 도메인 중 하나를 soft delete 한 뒤 필터 없이 search 하면, 그것까지 모두 나옵니다

Given

- 도메인 4개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.global_search: user-1이 wanted-1을 soft delete 한 뒤 필터 없이 전체를 조회합니다

Then

- 미리 저장한 도메인이 모두 나옵니다
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-domain](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

superadmin 이 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 거부됩니다

Given

- 도메인 4개와, 그중 하나에 속한 user 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.global_search: user-1이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### lookup_name

<a id="looking_up-a-user-granted-nothing-still-looks-up-a-domain-by-name"></a>

#### [a-user-granted-nothing-still-looks-up-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

아무 권한도 받지 않은 사용자도 도메인 이름으로 id 를 조회할 수 있습니다. 이 호출은 인증만 확인하고, 권한은 그 id 를 받는 호출이 확인합니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.lookup_name: user-1이 target-1의 id 를 조회합니다

Then

- 그 도메인의 id 가 응답으로 옵니다
  - id: 미리 저장한 도메인의 id 와 같다

<a id="looking_up-the-superadmin-looks-up-a-domain-by-name"></a>

#### [the-superadmin-looks-up-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

superadmin 이 도메인 이름으로 id 를 조회하면, 그 도메인의 id 가 응답으로 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.lookup_name: user-1이 target-1의 id 를 조회합니다

Then

- 그 도메인의 id 가 응답으로 옵니다
  - id: 미리 저장한 도메인의 id 와 같다

<a id="looking_up-looking-up-a-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

아무 도메인도 갖지 않은 이름으로 id 를 조회하면 대상이 없다는 것으로 거부됩니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.lookup_name: user-1이 no-such-domain 의 id 를 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-domains"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-domains](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 3개와, 그중 하나에 속한 user 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.partial_bulk_delete: user-1이 도메인 2개를 한 번에 soft delete 합니다

Then

- 처리된 도메인 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 도메인의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 도메인의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

활성 도메인 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 비활성 상태로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 3개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.partial_bulk_delete: user-1이 도메인 2개 와 없는 id 하나를 한 번에 soft delete 합니다

Then

- 대상 도메인이 모두 비활성 상태로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].name = 'wanted-1'
  - successes[0].description = '이미 있던 도메인'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = False
  - successes[0].is_default = False
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'other-1'
  - successes[1].description = '이미 있던 도메인'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = False
  - successes[1].is_default = False
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

soft delete 된 도메인 여럿을 한 번에 restore 하면, 모두 활성 상태로 옵니다

Given

- 도메인 3개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.partial_bulk_restore: user-1이 도메인 2개를 한 번에 soft delete 한 뒤 한 번에 restore 합니다

Then

- 대상 도메인이 모두 활성 상태로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].name = 'wanted-1'
  - successes[0].description = '이미 있던 도메인'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = True
  - successes[0].is_default = False
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'other-1'
  - successes[1].description = '이미 있던 도메인'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = True
  - successes[1].is_default = False
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-domains"></a>

#### [a-user-granted-nothing-edits-none-of-several-domains](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 3개와, 그중 하나에 속한 user 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.partial_bulk_update: user-1이 도메인 2개의 설명을 한 번에 수정합니다

Then

- 처리된 도메인 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 도메인의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 도메인의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-domains"></a>

#### [the-active-flag-soft-deletes-or-restores-each-of-several-domains](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

활성 플래그와 설명을 섞어 도메인 여럿을 한 번에 수정하면, 플래그를 비활성화한 것은 soft delete 되고 활성화한 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 3개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.partial_bulk_update: user-1이 둘째 도메인을 soft delete 한 뒤, 첫째는 활성 플래그를 비활성화하고 둘째는 활성화하며 둘의 설명을 변경하고, 없는 id 하나의 활성 플래그를 비활성화합니다

Then

- 둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이며, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].name = 'wanted-1'
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = False
  - successes[0].is_default = False
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'other-1'
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = True
  - successes[1].is_default = False
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-domains-at-once"></a>

#### [the-superadmin-edits-several-domains-at-once](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

superadmin 이 도메인 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 도메인 3개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.partial_bulk_update: user-1이 도메인 2개의 설명을 한 번에 수정합니다

Then

- 대상 도메인이 모두 새 설명으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].name = 'wanted-1'
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = True
  - successes[0].is_default = False
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].modified_at: 이 실행이 쓴 시각
  - successes[1].name = 'other-1'
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = True
  - successes[1].is_default = False
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 도메인의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].modified_at: 이 실행이 쓴 시각

### restore

<a id="deleting-restoring-a-domain-that-is-not-soft-deleted"></a>

#### [restoring-a-domain-that-is-not-soft-deleted](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

soft delete 되지 않은 도메인을 superadmin 이 restore 하면, restore 했다는 응답이 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 active-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.restore: user-1이 active-1을 restore 합니다

Then

- 했다는 응답이 옵니다
  - restored = True

<a id="deleting-restoring-answers-that-it-restored"></a>

#### [restoring-answers-that-it-restored](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

soft delete 된 도메인을 restore 하면, restore 했다는 응답이 옵니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 to-restore-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.restore: user-1이 to-restore-1을 soft delete 한 뒤 restore 합니다

Then

- 했다는 응답이 옵니다
  - restored = True

<a id="deleting-a-user-granted-nothing-may-not-restore-a-domain"></a>

#### [a-user-granted-nothing-may-not-restore-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 도메인을 restore 할 수 없습니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 untouchable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.restore: user-1이 untouchable-1을 restore 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="scoped_searching-a-user-granted-read-in-the-group-searches-its-domains"></a>

#### [a-user-granted-read-in-the-group-searches-its-domains](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py): pass

리소스 그룹 범위에서 도메인 읽기 역할을 받은 사용자가 그 범위에서 search 하면, superadmin 과 같은 도메인들이 응답으로 옵니다

Given

- 리소스 그룹 하나, 그 그룹을 쓸 수 있는 도메인 둘과 쓸 수 없는 하나, 그리고 그 그룹 범위의 도메인 읽기 역할을 받은 user 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인 linked-1
  - 도메인 linked-2
  - 도메인 linked-1 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 도메인 linked-2 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리소스 그룹 범위의 도메인 읽기 역할을 받은 사용자 준비
    - 역할 domain-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 domain-reader-1: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 domain-reader-1 보유

When

- DomainAdapter.scoped_search: user-1이 리소스 그룹 resource-group-1 범위에서 search 합니다

Then

- 그 그룹을 쓸 수 있는 도메인만 남습니다
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-the-superadmin-searches-the-domains-of-a-resource-group"></a>

#### [the-superadmin-searches-the-domains-of-a-resource-group](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py): pass

superadmin 이 리소스 그룹 범위에서 search 하면, 그 그룹을 쓸 수 있는 도메인만 응답으로 옵니다

Given

- 리소스 그룹 하나, 그 그룹을 쓸 수 있는 도메인 둘과 쓸 수 없는 하나, 그리고 superadmin 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인 linked-1
  - 도메인 linked-2
  - 도메인 linked-1 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 도메인 linked-2 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.scoped_search: user-1이 리소스 그룹 resource-group-1 범위에서 search 합니다

Then

- 그 그룹을 쓸 수 있는 도메인만 남습니다
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py): pass

아무 권한도 받지 않은 사용자가 리소스 그룹 범위에서 search 하면 권한 부족으로 거부됩니다

Given

- 리소스 그룹 하나, 그 그룹을 쓸 수 있는 도메인 둘과 쓸 수 없는 하나, 그리고 user 한 명
  - 도메인 home-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인 linked-1
  - 도메인 linked-2
  - 도메인 linked-1 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 도메인 linked-2 의 세션이 사용할 수 있는 자원 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.scoped_search: user-1이 리소스 그룹 resource-group-1 범위에서 search 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-clearing-the-active-flag-soft-deletes-a-domain"></a>

#### [clearing-the-active-flag-soft-deletes-a-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

활성 플래그를 비활성화하는 수정은 도메인을 soft delete 하고, 응답이 비활성 상태를 담아 옵니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 to-deactivate-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.update: user-1이 to-deactivate-1의 활성 플래그을 수정합니다

Then

- 미리 저장한 도메인 전체가 응답으로 옵니다
  - name = 'to-deactivate-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 도메인의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-editing-a-description-leaves-the-name-alone"></a>

#### [editing-a-description-leaves-the-name-alone](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

superadmin 이 도메인의 설명만 변경하면, 설명은 새 값이 되고 이름은 그대로 남습니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 editable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.update: user-1이 editable-1의 설명을 수정합니다

Then

- 미리 저장한 도메인 전체가 응답으로 옵니다
  - name = 'editable-1'
  - description = '수정한 설명'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 도메인의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-lowering-the-active-flag-of-a-soft-deleted-domain-edits-only-the-rest"></a>

#### [lowering-the-active-flag-of-a-soft-deleted-domain-edits-only-the-rest](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

soft delete 된 도메인의 활성 플래그를 비활성화하며 설명을 변경하면, 설명은 새 값이 되고 비활성 상태는 그대로입니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 already-deleted-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.update: user-1이 already-deleted-1을 soft delete 한 뒤 활성 플래그와 설명을 수정합니다

Then

- 미리 저장한 도메인 전체가 응답으로 옵니다
  - name = 'already-deleted-1'
  - description = '수정한 설명'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 도메인의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-raising-the-active-flag-restores-a-soft-deleted-domain"></a>

#### [raising-the-active-flag-restores-a-soft-deleted-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

soft delete 된 도메인의 활성 플래그를 활성화하는 수정은 그 도메인을 restore 하고, 응답이 활성 상태를 담아 옵니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 to-restore-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.update: user-1이 to-restore-1을 soft delete 한 뒤 활성 플래그을 수정합니다

Then

- 미리 저장한 도메인 전체가 응답으로 옵니다
  - name = 'to-restore-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 도메인의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-edit-a-domain"></a>

#### [a-user-granted-nothing-may-not-edit-a-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.update: user-1이 host-1의 설명을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-editing-a-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.update: user-1이 no-such-domain 의 설명을 수정합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### sync_registry_relations

<a id="syncing_registry_relations-a-name-no-registry-carries-links-nothing"></a>

#### [a-name-no-registry-carries-links-nothing](/tests/scenario/bai_scenario/manager/domain/test_syncing_registry_relations.py): pass

어떤 레지스트리와도 맞지 않는 이름으로 맞추면 오류 없이 relation 이 생기지 않습니다 (이름으로 레지스트리를 찾는 일은 전역 역할로 막혀 있어 슈퍼관리자가 호출합니다)

Given

- 도메인 하나와 레지스트리 하나, 그 도메인에 속한 superadmin 한 명이 있습니다
  - 도메인 allowing-1
  - 컨테이너 레지스트리 allowed-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.sync_registry_relations: user-1이 allowing-1의 relation 을 어떤 레지스트리와도 맞지 않는 이름에 맞춥니다

Then

- 반환값이 없고 예외도 발생하지 않습니다
  - response = None

<a id="syncing_registry_relations-leaving-a-linked-registry-out-unlinks-it"></a>

#### [leaving-a-linked-registry-out-unlinks-it](/tests/scenario/bai_scenario/manager/domain/test_syncing_registry_relations.py): pass

relation 이 있는 레지스트리를 빼고 빈 목록으로 맞추면 그 relation 이 지워집니다 (이름으로 레지스트리를 찾는 일은 전역 역할로 막혀 있어 슈퍼관리자가 호출합니다)

Given

- 도메인 하나와 레지스트리 하나, 둘 사이에 relation 이 이미 있고, 그 도메인에 속한 superadmin 한 명이 있습니다
  - 도메인 allowing-1
  - 컨테이너 레지스트리 allowed-1: 이미지를 가져오는 곳
  - 도메인 allowing-1 가 허용한 컨테이너 레지스트리 allowed-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.sync_registry_relations: user-1이 allowing-1의 relation 을 빈 목록에 맞춥니다

Then

- 반환값이 없고 예외도 발생하지 않습니다
  - response = None

<a id="syncing_registry_relations-naming-a-registry-links-the-domain-to-it"></a>

#### [naming-a-registry-links-the-domain-to-it](/tests/scenario/bai_scenario/manager/domain/test_syncing_registry_relations.py): pass

슈퍼관리자가 레지스트리의 이름으로 맞추면 도메인과 그 레지스트리 사이에 relation 이 생깁니다 (이름으로 레지스트리를 찾는 일은 전역 역할로 막혀 있어 슈퍼관리자가 호출합니다)

Given

- 도메인 하나와 레지스트리 하나, 그 도메인에 속한 superadmin 한 명이 있습니다
  - 도메인 allowing-1
  - 컨테이너 레지스트리 allowed-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.sync_registry_relations: user-1이 allowing-1의 relation 을 그 레지스트리의 이름에 맞춥니다

Then

- 반환값이 없고 예외도 발생하지 않습니다
  - response = None

<a id="syncing_registry_relations-a-user-granted-nothing-may-not-sync-registry-relations"></a>

#### [a-user-granted-nothing-may-not-sync-registry-relations](/tests/scenario/bai_scenario/manager/domain/test_syncing_registry_relations.py): pass

슈퍼관리자가 아닌 사용자가 relation 을 맞추려 하면 거부됩니다. 이름으로 레지스트리를 찾는 일은 슈퍼관리자 역할이 있어야만 실행됩니다

Given

- 도메인 하나와 레지스트리 하나, 그 도메인에 속한 user 한 명이 있습니다
  - 도메인 allowing-1
  - 컨테이너 레지스트리 allowed-1: 이미지를 가져오는 곳
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.sync_registry_relations: user-1이 allowing-1의 relation 을 그 레지스트리의 이름에 맞춥니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### create

<a id="creating-creating-a-domain-also-creates-its-model-store-project"></a>

#### [creating-a-domain-also-creates-its-model-store-project](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

superadmin 이 도메인을 생성하면 model-store 프로젝트가 함께 생성되어, 그 프로젝트를 가진 도메인으로 필터 기반 조회할 때 생성한 도메인이 응답으로 옵니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.create: user-1이 with-model-store 으로 생성한 뒤, model-store 프로젝트를 가진 도메인으로 필터 기반 조회합니다

Then

- 만든 도메인 전체가 응답으로 옵니다
  - name = 'with-model-store'
  - description = '새로 생성한 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="creating-creating-a-domain-answers-with-the-whole-node"></a>

#### [creating-a-domain-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

superadmin 이 이름과 설명만 지정하고 도메인을 생성하면, 요청에 없던 값들은 기본값으로 채워진 노드 전체가 응답으로 옵니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.create: user-1이 new-domain 으로 생성합니다

Then

- 만든 도메인 전체가 응답으로 옵니다
  - name = 'new-domain'
  - description = '새로 생성한 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 건너뜀: 데이터베이스가 생성합니다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="creating-a-blank-name-is-refused"></a>

#### [a-blank-name-is-refused](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

이름이 공백뿐이면 도메인을 생성할 수 없습니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.create: user-1이    으로 생성합니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

<a id="creating-a-name-another-domain-already-holds-is-refused"></a>

#### [a-name-another-domain-already-holds-is-refused](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

이미 어떤 도메인이 쓰고 있는 이름으로 생성하려 하면, 권한이 있어도 이름이 겹친다는 이유로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 taken-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.create: user-1이 taken-1으로 생성합니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-domain](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

superadmin 이 아닌 사용자가 도메인을 생성하려 하면, 권한을 얼마나 받았는지와 무관하게 역할로 거부됩니다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.create: user-1이 by-a-user 으로 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-domain"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-domain](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

엔티티 권한 집행을 꺼도 도메인 생성은 여전히 거부됩니다. 이 동작은 권한 그래프가 아니라 역할이 검사하기 때문입니다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.create: user-1이 by-a-user-again 으로 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### purge

<a id="deleting-purging-a-domain-nothing-else-refers-to-succeeds"></a>

#### [purging-a-domain-nothing-else-refers-to-succeeds](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

아무것도 딸려 있지 않은 도메인은 purge 할 수 있습니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 to-purge-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.purge: user-1이 to-purge-1을 purge 합니다

Then

- 했다는 응답이 옵니다
  - purged = True

<a id="deleting-a-domain-holding-a-project-is-not-purged"></a>

#### [a-domain-holding-a-project-is-not-purged](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

프로젝트가 딸린 도메인은 superadmin 이라도 purge 할 수 없습니다

Given

- 프로젝트이 딸린 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.purge: user-1이 target-1을 purge 합니다

Then

- 거부됩니다
  - 거부: DomainHasGroups

<a id="deleting-a-domain-holding-a-user-is-not-purged"></a>

#### [a-domain-holding-a-user-is-not-purged](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

사용자가 딸린 도메인은 superadmin 이라도 purge 할 수 없습니다

Given

- 사용자이 딸린 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.purge: user-2이 target-1을 purge 합니다

Then

- 거부됩니다
  - 거부: DomainHasUsers

<a id="deleting-a-user-granted-nothing-may-not-purge-a-domain"></a>

#### [a-user-granted-nothing-may-not-purge-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 아무것도 딸리지 않은 도메인이라도 purge 할 수 없습니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 untouchable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.purge: user-1이 untouchable-1을 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deleting-purging-a-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

아무 도메인도 갖지 않은 이름을 purge 하려 하면 대상이 없다는 것으로 거부됩니다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DomainAdapter.purge: user-1이 no-such-domain 을 purge 합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

