## domain

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/domain/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/domain/adapter.py)

시나리오: 완성

- ops 로 구성 (9)
  - bulk_get_ids — 대표 성공 ✓ · 대표 실패 ✓
  - bulk_lookup_names — 대표 성공 ✓ · 대표 실패 ✓
  - delete — 대표 성공 ✓ · 대표 실패 ✓
  - get — 대표 성공 ✓ · 대표 실패 ✓
  - global_search — 대표 성공 ✓ · 대표 실패 ✓
  - lookup_name — 대표 성공 ✓ · 대표 실패 ✓
  - restore — 대표 성공 ✓ · 대표 실패 ✓
  - scoped_search — 대표 성공 ✓ · 대표 실패 ✓
  - update — 대표 성공 ✓ · 대표 실패 ✓
- 직접 구현 (2)
  - create — 성공 있음 2 · 실패 있음 4 (global_scope)
  - purge — 성공 있음 1 · 실패 있음 4 (single_entity)

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 id로 도메인 여럿을 읽으면, 그 자리에 도메인이 온다](#bulk_reading-the-superadmin-reads-domains-by-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 id로 도메인 여럿을 읽으면, 그 자리가 권한 부족으로 거부된다](#bulk_reading-a-user-granted-nothing-may-not-read-domains-by-id) | 거부 |

**bulk_lookup_names**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 찾아도 슈퍼관리자와 같은 답이 온다. 이 호출은 인증만 보므로 이름이 있는지는 누구에게나 드러난다](#looking_up-a-user-granted-nothing-gets-the-same-ids-by-name) | 성공 |
| [슈퍼관리자가 있는 이름과 없는 이름으로 id를 여럿 찾으면, 있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 온다](#looking_up-the-superadmin-looks-up-domains-by-name) | 성공 |
| [로그인 문맥 없이 이름으로 id를 여럿 찾으면, 사용자를 찾을 수 없다는 것으로 거부된다](#looking_up-looking-up-domains-by-name-without-login-is-refused) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [이미 soft delete 된 도메인을 슈퍼관리자가 다시 soft delete 하면, soft delete 했다는 답이 온다](#deleting-soft-deleting-a-domain-already-soft-deleted) | 성공 |
| [슈퍼관리자가 도메인을 soft delete 하면, soft delete 했다는 답이 온다](#deleting-the-superadmin-soft-deletes-a-domain) | 성공 |
| [아무 권한도 받지 않은 사용자는 도메인을 soft delete 할 수 없다](#deleting-a-user-granted-nothing-may-not-soft-delete-a-domain) | 거부 |
| [아무 도메인도 갖지 않은 이름을 soft delete 하려 하면 대상이 없다는 것으로 거부된다](#deleting-soft-deleting-a-name-nothing-answers-to-is-not-found) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [도메인 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 도메인이 답으로 온다](#reading-the-superadmin-reads-a-domain-by-name) | 성공 |
| [슈퍼관리자가 도메인을 soft delete 한 뒤 이름으로 조회하면, 비활성 상태를 실은 그 도메인이 온다](#reading-the-superadmin-reads-a-soft-deleted-domain-by-name) | 성공 |
| [같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, 이름으로 조회하면 권한 부족으로 거부된다](#reading-a-user-granted-nothing-may-not-read-a-domain) | 거부 |
| [슈퍼관리자가 존재하지 않는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부된다](#reading-reading-a-name-nothing-answers-to-is-not-found) | 거부 |

**global_search**

| 시나리오 | 판정 |
|---|---|
| [도메인 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 도메인만 남는다](#searching-a-name-filter-narrows-the-answer-to-the-domain-it-names) | 성공 |
| [이 시나리오가 미리 만든 도메인이 넷일 때, 필터 없는 조회는 그 넷이 모두 나온다](#searching-the-answer-counts-every-domain-the-scenario-laid) | 성공 |
| [미리 만든 도메인 중 하나를 soft delete 한 뒤 필터 없이 search 하면, 그것까지 모두 나온다](#searching-the-answer-includes-soft-deleted-domains-too) | 성공 |
| [슈퍼관리자가 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 막힌다](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-domain) | 거부 |

**lookup_name**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자도 도메인 이름으로 id를 찾을 수 있다. 이 호출은 인증만 보고, 권한은 그 id를 받는 호출이 본다](#looking_up-a-user-granted-nothing-still-looks-up-a-domain-by-name) | 성공 |
| [슈퍼관리자가 도메인 이름으로 id를 찾으면, 그 도메인의 id가 온다](#looking_up-the-superadmin-looks-up-a-domain-by-name) | 성공 |
| [아무 도메인도 갖지 않은 이름으로 id를 찾으면 대상이 없다는 것으로 거부된다](#looking_up-looking-up-a-name-nothing-answers-to-is-not-found) | 거부 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 되지 않은 도메인을 슈퍼관리자가 restore 하면, restore 했다는 답이 온다](#deleting-restoring-a-domain-that-is-not-soft-deleted) | 성공 |
| [soft delete 된 도메인을 restore 하면, restore 했다는 답이 온다](#deleting-restoring-answers-that-it-restored) | 성공 |
| [아무 권한도 받지 않은 사용자는 도메인을 restore 할 수 없다](#deleting-a-user-granted-nothing-may-not-restore-a-domain) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [리소스 그룹 범위에서 도메인 읽기 역할을 받은 사용자가 그 범위에서 search 하면, 슈퍼관리자와 같은 도메인들이 온다](#scoped_searching-a-user-granted-read-in-the-group-searches-its-domains) | 성공 |
| [슈퍼관리자가 리소스 그룹 범위에서 search 하면, 그 그룹을 쓸 수 있는 도메인만 온다](#scoped_searching-the-superadmin-searches-the-domains-of-a-resource-group) | 성공 |
| [아무 권한도 받지 않은 사용자가 리소스 그룹 범위에서 search 하면 권한 부족으로 거부된다](#scoped_searching-a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [활성 플래그를 내리는 수정은 도메인을 비활성으로 만들고, 답이 그 상태를 실어 온다](#editing-clearing-the-active-flag-deactivates-a-domain) | 성공 |
| [슈퍼관리자가 도메인의 설명만 바꾸면, 설명은 새 값이 되고 이름은 그대로 남는다](#editing-editing-a-description-leaves-the-name-alone) | 성공 |
| [아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부된다](#editing-a-user-granted-nothing-may-not-edit-a-domain) | 거부 |
| [아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부된다](#editing-editing-a-name-nothing-answers-to-is-not-found) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 도메인을 만들면 model-store 프로젝트가 함께 생겨, 그 프로젝트를 가진 도메인으로 걸러 찾을 때 만든 도메인이 온다](#creating-creating-a-domain-also-creates-its-model-store-project) | 성공 |
| [슈퍼관리자가 이름과 설명만 주고 도메인을 만들면, 요청에 없던 값들은 기본값으로 채워진 노드 전체가 답으로 온다](#creating-creating-a-domain-answers-with-the-whole-node) | 성공 |
| [이름이 공백뿐이면 도메인을 만들 수 없다](#creating-a-blank-name-is-refused) | 거부 |
| [이미 어떤 도메인이 쓰고 있는 이름으로 만들려 하면, 권한이 있어도 이름이 겹친다는 이유로 거부된다](#creating-a-name-another-domain-already-holds-is-refused) | 거부 |
| [슈퍼관리자가 아닌 사용자가 도메인을 만들려 하면, 권한을 얼마나 받았는지와 무관하게 역할로 막힌다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-domain) | 거부 |
| [엔티티 권한 집행을 꺼도 도메인 생성은 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-domain) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [아무것도 딸려 있지 않은 도메인은 purge 할 수 있다](#deleting-purging-a-domain-nothing-else-refers-to-succeeds) | 성공 |
| [프로젝트가 딸린 도메인은 슈퍼관리자라도 purge 할 수 없다](#deleting-a-domain-holding-a-project-is-not-purged) | 거부 |
| [사용자가 딸린 도메인은 슈퍼관리자라도 purge 할 수 없다](#deleting-a-domain-holding-a-user-is-not-purged) | 거부 |
| [아무 권한도 받지 않은 사용자는 아무것도 딸리지 않은 도메인이라도 purge 할 수 없다](#deleting-a-user-granted-nothing-may-not-purge-a-domain) | 거부 |
| [아무 도메인도 갖지 않은 이름을 purge 하려 하면 대상이 없다는 것으로 거부된다](#deleting-purging-a-name-nothing-answers-to-is-not-found) | 거부 |

### bulk_get_ids

<a id="bulk_reading-the-superadmin-reads-domains-by-id"></a>

#### [the-superadmin-reads-domains-by-id](/tests/scenario/bai_scenario/manager/domain/test_bulk_reading.py) — pass

슈퍼관리자가 id로 도메인 여럿을 읽으면, 그 자리에 도메인이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.bulk_get_ids — user-1이 target-1의 id로 여럿 읽기

Then

- 물은 자리에 미리 만든 도메인 전체가 온다
  - [0].name = 'target-1'
  - [0].description = '이미 있던 도메인'
  - [0].integration_name = None
  - [0].allowed_docker_registries = []
  - [0].is_active = True
  - [0].is_default = False
  - [0].id: 무시함 — 데이터베이스가 만든다
  - [0].entity_id: 미리 만든 도메인의 id와 같다
  - [0].created_at: 이 실행이 쓴 시각
  - [0].modified_at: 이 실행이 쓴 시각

<a id="bulk_reading-a-user-granted-nothing-may-not-read-domains-by-id"></a>

#### [a-user-granted-nothing-may-not-read-domains-by-id](/tests/scenario/bai_scenario/manager/domain/test_bulk_reading.py) — pass

아무 권한도 받지 않은 사용자가 id로 도메인 여럿을 읽으면, 그 자리가 권한 부족으로 거부된다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.bulk_get_ids — user-1이 target-1의 id로 여럿 읽기

Then

- 물은 자리가 거부된다
  - 거부: NotEnoughPermission

### bulk_lookup_names

<a id="looking_up-a-user-granted-nothing-gets-the-same-ids-by-name"></a>

#### [a-user-granted-nothing-gets-the-same-ids-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py) — pass

아무 권한도 받지 않은 사용자가 찾아도 슈퍼관리자와 같은 답이 온다. 이 호출은 인증만 보므로 이름이 있는지는 누구에게나 드러난다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.bulk_lookup_names — user-1이 target-1과 no-such-domain의 id를 여럿 찾음

Then

- 있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 온다
  - [0]: 미리 만든 도메인의 id와 같다
  - [1] = None

<a id="looking_up-the-superadmin-looks-up-domains-by-name"></a>

#### [the-superadmin-looks-up-domains-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py) — pass

슈퍼관리자가 있는 이름과 없는 이름으로 id를 여럿 찾으면, 있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.bulk_lookup_names — user-1이 target-1과 no-such-domain의 id를 여럿 찾음

Then

- 있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 온다
  - [0]: 미리 만든 도메인의 id와 같다
  - [1] = None

<a id="looking_up-looking-up-domains-by-name-without-login-is-refused"></a>

#### [looking-up-domains-by-name-without-login-is-refused](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py) — pass

로그인 문맥 없이 이름으로 id를 여럿 찾으면, 사용자를 찾을 수 없다는 것으로 거부된다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.bulk_lookup_names — 로그인 문맥 없이 target-1의 id를 여럿 찾음

Then

- 거부된다
  - 거부: UserNotFound

### delete

<a id="deleting-soft-deleting-a-domain-already-soft-deleted"></a>

#### [soft-deleting-a-domain-already-soft-deleted](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

이미 soft delete 된 도메인을 슈퍼관리자가 다시 soft delete 하면, soft delete 했다는 답이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 twice-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.delete — user-1이 twice-1을 두 번 soft delete 함

Then

- 했다는 답이 온다
  - deleted = True

<a id="deleting-the-superadmin-soft-deletes-a-domain"></a>

#### [the-superadmin-soft-deletes-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

슈퍼관리자가 도메인을 soft delete 하면, soft delete 했다는 답이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 to-delete-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.delete — user-1이 to-delete-1을 soft delete 함

Then

- 했다는 답이 온다
  - deleted = True

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-domain"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

아무 권한도 받지 않은 사용자는 도메인을 soft delete 할 수 없다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 untouchable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.delete — user-1이 untouchable-1을 soft delete 함

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="deleting-soft-deleting-a-name-nothing-answers-to-is-not-found"></a>

#### [soft-deleting-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

아무 도메인도 갖지 않은 이름을 soft delete 하려 하면 대상이 없다는 것으로 거부된다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.delete — user-1이 no-such-domain을 soft delete 함

Then

- 거부된다
  - 거부: EntityNotFoundError

### get

<a id="reading-the-superadmin-reads-a-domain-by-name"></a>

#### [the-superadmin-reads-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_reading.py) — pass

도메인 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 도메인이 답으로 온다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.get — user-1이 host-1으로 조회

Then

- 미리 만든 도메인 전체가 온다
  - name = 'host-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - entity_id: 미리 만든 도메인의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="reading-the-superadmin-reads-a-soft-deleted-domain-by-name"></a>

#### [the-superadmin-reads-a-soft-deleted-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_reading.py) — pass

슈퍼관리자가 도메인을 soft delete 한 뒤 이름으로 조회하면, 비활성 상태를 실은 그 도메인이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 soft-deleted-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.get — user-1이 soft-deleted-1을 soft delete 한 뒤 이름으로 조회

Then

- 미리 만든 도메인 전체가 온다
  - name = 'soft-deleted-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - entity_id: 미리 만든 도메인의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="reading-a-user-granted-nothing-may-not-read-a-domain"></a>

#### [a-user-granted-nothing-may-not-read-a-domain](/tests/scenario/bai_scenario/manager/domain/test_reading.py) — pass

같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, 이름으로 조회하면 권한 부족으로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.get — user-1이 host-1으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="reading-reading-a-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_reading.py) — pass

슈퍼관리자가 존재하지 않는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.get — user-1이 no-such-domain으로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### global_search

<a id="searching-a-name-filter-narrows-the-answer-to-the-domain-it-names"></a>

#### [a-name-filter-narrows-the-answer-to-the-domain-it-names](/tests/scenario/bai_scenario/manager/domain/test_searching.py) — pass

도메인 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 도메인만 남는다

Given

- 도메인 4개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.global_search — user-1이 wanted-1으로 걸러 조회

Then

- 걸러낸 그 도메인 하나만 남는다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-answer-counts-every-domain-the-scenario-laid"></a>

#### [the-answer-counts-every-domain-the-scenario-laid](/tests/scenario/bai_scenario/manager/domain/test_searching.py) — pass

이 시나리오가 미리 만든 도메인이 넷일 때, 필터 없는 조회는 그 넷이 모두 나온다

Given

- 도메인 4개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.global_search — user-1이 필터 없이 전체 조회

Then

- 미리 만든 도메인이 모두 나온다
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-answer-includes-soft-deleted-domains-too"></a>

#### [the-answer-includes-soft-deleted-domains-too](/tests/scenario/bai_scenario/manager/domain/test_searching.py) — pass

미리 만든 도메인 중 하나를 soft delete 한 뒤 필터 없이 search 하면, 그것까지 모두 나온다

Given

- 도메인 4개와, 그중 하나에 속한 superadmin 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.global_search — user-1이 wanted-1을 soft delete 한 뒤 필터 없이 전체 조회

Then

- 미리 만든 도메인이 모두 나온다
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-domain](/tests/scenario/bai_scenario/manager/domain/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 막힌다

Given

- 도메인 4개와, 그중 하나에 속한 user 한 명
  - 도메인 home-1
  - 도메인 wanted-1
  - 도메인 other-1
  - 도메인 other-2
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.global_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

### lookup_name

<a id="looking_up-a-user-granted-nothing-still-looks-up-a-domain-by-name"></a>

#### [a-user-granted-nothing-still-looks-up-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py) — pass

아무 권한도 받지 않은 사용자도 도메인 이름으로 id를 찾을 수 있다. 이 호출은 인증만 보고, 권한은 그 id를 받는 호출이 본다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.lookup_name — user-1이 target-1의 id를 찾음

Then

- 그 도메인의 id가 온다
  - id: 미리 만든 도메인의 id와 같다

<a id="looking_up-the-superadmin-looks-up-a-domain-by-name"></a>

#### [the-superadmin-looks-up-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py) — pass

슈퍼관리자가 도메인 이름으로 id를 찾으면, 그 도메인의 id가 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.lookup_name — user-1이 target-1의 id를 찾음

Then

- 그 도메인의 id가 온다
  - id: 미리 만든 도메인의 id와 같다

<a id="looking_up-looking-up-a-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py) — pass

아무 도메인도 갖지 않은 이름으로 id를 찾으면 대상이 없다는 것으로 거부된다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.lookup_name — user-1이 no-such-domain의 id를 찾음

Then

- 거부된다
  - 거부: EntityNotFoundError

### restore

<a id="deleting-restoring-a-domain-that-is-not-soft-deleted"></a>

#### [restoring-a-domain-that-is-not-soft-deleted](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

soft delete 되지 않은 도메인을 슈퍼관리자가 restore 하면, restore 했다는 답이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 active-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.restore — user-1이 active-1을 restore 함

Then

- 했다는 답이 온다
  - restored = True

<a id="deleting-restoring-answers-that-it-restored"></a>

#### [restoring-answers-that-it-restored](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

soft delete 된 도메인을 restore 하면, restore 했다는 답이 온다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 to-restore-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.restore — user-1이 to-restore-1을 soft delete 했다가 restore 함

Then

- 했다는 답이 온다
  - restored = True

<a id="deleting-a-user-granted-nothing-may-not-restore-a-domain"></a>

#### [a-user-granted-nothing-may-not-restore-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

아무 권한도 받지 않은 사용자는 도메인을 restore 할 수 없다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 untouchable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.restore — user-1이 untouchable-1을 restore 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### scoped_search

<a id="scoped_searching-a-user-granted-read-in-the-group-searches-its-domains"></a>

#### [a-user-granted-read-in-the-group-searches-its-domains](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py) — pass

리소스 그룹 범위에서 도메인 읽기 역할을 받은 사용자가 그 범위에서 search 하면, 슈퍼관리자와 같은 도메인들이 온다

Given

- 리소스 그룹 하나, 그 그룹을 쓸 수 있는 도메인 둘과 쓸 수 없는 하나, 그리고 그 그룹 범위의 도메인 읽기 역할을 받은 user 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인 linked-1
  - 도메인 linked-2
  - 도메인 linked-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인 linked-2 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 리소스 그룹 범위의 도메인 읽기 역할을 받은 사용자 준비
    - 역할 domain-reader-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 domain-reader-1: domain 전체에 READ 허용
    - 일반 사용자 user-1: 역할 domain-reader-1 보유

When

- DomainAdapter.scoped_search — user-1이 리소스 그룹 resource-group-1 범위에서 조회

Then

- 그 그룹을 쓸 수 있는 도메인만 남는다
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-the-superadmin-searches-the-domains-of-a-resource-group"></a>

#### [the-superadmin-searches-the-domains-of-a-resource-group](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py) — pass

슈퍼관리자가 리소스 그룹 범위에서 search 하면, 그 그룹을 쓸 수 있는 도메인만 온다

Given

- 리소스 그룹 하나, 그 그룹을 쓸 수 있는 도메인 둘과 쓸 수 없는 하나, 그리고 superadmin 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인 linked-1
  - 도메인 linked-2
  - 도메인 linked-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인 linked-2 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.scoped_search — user-1이 리소스 그룹 resource-group-1 범위에서 조회

Then

- 그 그룹을 쓸 수 있는 도메인만 남는다
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py) — pass

아무 권한도 받지 않은 사용자가 리소스 그룹 범위에서 search 하면 권한 부족으로 거부된다

Given

- 리소스 그룹 하나, 그 그룹을 쓸 수 있는 도메인 둘과 쓸 수 없는 하나, 그리고 user 한 명
  - 도메인 home-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인 linked-1
  - 도메인 linked-2
  - 도메인 linked-1 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인 linked-2 의 세션이 쓸 수 있는 리소스 그룹 resource-group-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.scoped_search — user-1이 리소스 그룹 resource-group-1 범위에서 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

### update

<a id="editing-clearing-the-active-flag-deactivates-a-domain"></a>

#### [clearing-the-active-flag-deactivates-a-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py) — pass

활성 플래그를 내리는 수정은 도메인을 비활성으로 만들고, 답이 그 상태를 실어 온다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 to-deactivate-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.update — user-1이 to-deactivate-1의 활성 플래그을 고침

Then

- 미리 만든 도메인 전체가 온다
  - name = 'to-deactivate-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - entity_id: 미리 만든 도메인의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-editing-a-description-leaves-the-name-alone"></a>

#### [editing-a-description-leaves-the-name-alone](/tests/scenario/bai_scenario/manager/domain/test_editing.py) — pass

슈퍼관리자가 도메인의 설명만 바꾸면, 설명은 새 값이 되고 이름은 그대로 남는다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 editable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.update — user-1이 editable-1의 설명을 고침

Then

- 미리 만든 도메인 전체가 온다
  - name = 'editable-1'
  - description = '고쳐 쓴 설명'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - entity_id: 미리 만든 도메인의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-edit-a-domain"></a>

#### [a-user-granted-nothing-may-not-edit-a-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.update — user-1이 host-1의 설명을 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing-editing-a-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_editing.py) — pass

아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.update — user-1이 no-such-domain의 설명을 고침

Then

- 거부된다
  - 거부: EntityNotFoundError

### create

<a id="creating-creating-a-domain-also-creates-its-model-store-project"></a>

#### [creating-a-domain-also-creates-its-model-store-project](/tests/scenario/bai_scenario/manager/domain/test_creating.py) — pass

슈퍼관리자가 도메인을 만들면 model-store 프로젝트가 함께 생겨, 그 프로젝트를 가진 도메인으로 걸러 찾을 때 만든 도메인이 온다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.create — user-1이 with-model-store으로 만든 뒤, model-store 프로젝트를 가진 도메인으로 걸러 찾음

Then

- 만든 도메인 전체가 온다
  - name = 'with-model-store'
  - description = '새로 만든 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="creating-creating-a-domain-answers-with-the-whole-node"></a>

#### [creating-a-domain-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/domain/test_creating.py) — pass

슈퍼관리자가 이름과 설명만 주고 도메인을 만들면, 요청에 없던 값들은 기본값으로 채워진 노드 전체가 답으로 온다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.create — user-1이 new-domain으로 만듦

Then

- 만든 도메인 전체가 온다
  - name = 'new-domain'
  - description = '새로 만든 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="creating-a-blank-name-is-refused"></a>

#### [a-blank-name-is-refused](/tests/scenario/bai_scenario/manager/domain/test_creating.py) — pass

이름이 공백뿐이면 도메인을 만들 수 없다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.create — user-1이    으로 만듦

Then

- 거부된다
  - 거부: InvalidAPIParameters

<a id="creating-a-name-another-domain-already-holds-is-refused"></a>

#### [a-name-another-domain-already-holds-is-refused](/tests/scenario/bai_scenario/manager/domain/test_creating.py) — pass

이미 어떤 도메인이 쓰고 있는 이름으로 만들려 하면, 권한이 있어도 이름이 겹친다는 이유로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 taken-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.create — user-1이 taken-1으로 만듦

Then

- 거부된다
  - 거부: InvalidAPIParameters

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-domain](/tests/scenario/bai_scenario/manager/domain/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 도메인을 만들려 하면, 권한을 얼마나 받았는지와 무관하게 역할로 막힌다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.create — user-1이 by-a-user으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-domain"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-domain](/tests/scenario/bai_scenario/manager/domain/test_creating.py) — pass

엔티티 권한 집행을 꺼도 도메인 생성은 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.create — user-1이 by-a-user-again으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### purge

<a id="deleting-purging-a-domain-nothing-else-refers-to-succeeds"></a>

#### [purging-a-domain-nothing-else-refers-to-succeeds](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

아무것도 딸려 있지 않은 도메인은 purge 할 수 있다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 to-purge-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.purge — user-1이 to-purge-1을 purge 함

Then

- 했다는 답이 온다
  - purged = True

<a id="deleting-a-domain-holding-a-project-is-not-purged"></a>

#### [a-domain-holding-a-project-is-not-purged](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

프로젝트가 딸린 도메인은 슈퍼관리자라도 purge 할 수 없다

Given

- 프로젝트이 딸린 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.purge — user-1이 target-1을 purge 함

Then

- 거부된다
  - 거부: DomainHasGroups

<a id="deleting-a-domain-holding-a-user-is-not-purged"></a>

#### [a-domain-holding-a-user-is-not-purged](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

사용자가 딸린 도메인은 슈퍼관리자라도 purge 할 수 없다

Given

- 사용자이 딸린 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.purge — user-2이 target-1을 purge 함

Then

- 거부된다
  - 거부: DomainHasUsers

<a id="deleting-a-user-granted-nothing-may-not-purge-a-domain"></a>

#### [a-user-granted-nothing-may-not-purge-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

아무 권한도 받지 않은 사용자는 아무것도 딸리지 않은 도메인이라도 purge 할 수 없다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 untouchable-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.purge — user-1이 untouchable-1을 purge 함

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="deleting-purging-a-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_deleting.py) — pass

아무 도메인도 갖지 않은 이름을 purge 하려 하면 대상이 없다는 것으로 거부된다

Given

- 건드릴 도메인 하나와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.purge — user-1이 no-such-domain을 purge 함

Then

- 거부된다
  - 거부: EntityNotFoundError

