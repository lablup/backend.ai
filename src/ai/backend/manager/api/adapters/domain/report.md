## domain

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/domain/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/domain/adapter.py)

Not exercised by any scenario: batch_load_by_ids, batch_load_by_names, batch_load_fields, scoped_search, search_rg_domains.

### creating

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

- DomainAdapter.admin_create — user-1이    으로 만듦

Then

- 거부된다
  - 거부: InvalidAPIParameters

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

- DomainAdapter.admin_create — user-1이 taken-1으로 만듦

Then

- 거부된다
  - 거부: InvalidAPIParameters

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

- DomainAdapter.admin_create — user-1이 by-a-user으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

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

- DomainAdapter.admin_create — user-1이 new-domain으로 만듦

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

- DomainAdapter.admin_create — user-1이 by-a-user-again으로 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

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

- DomainAdapter.admin_update — user-1이 host-1의 설명을 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [clearing-the-active-flag-is-how-a-domain-retires](/tests/scenario/bai_scenario/manager/domain/test_editing.py) — pass

활성 플래그를 내리는 수정으로 도메인을 물릴 수 있고, 답이 그 상태를 실어 온다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 to-retire-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- DomainAdapter.admin_update — user-1이 to-retire-1의 활성 플래그을 고침

Then

- 심은 도메인 전체가 온다
  - name = 'to-retire-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

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

- DomainAdapter.admin_update — user-1이 editable-1의 설명을 고침

Then

- 심은 도메인 전체가 온다
  - name = 'editable-1'
  - description = '고쳐 쓴 설명'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

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

- DomainAdapter.admin_update — user-1이 no-such-domain의 설명을 고침

Then

- 거부된다
  - 거부: EntityNotFoundError

### reading

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

- 심은 도메인 전체가 온다
  - name = 'host-1'
  - description = '이미 있던 도메인'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: 무시함 — 데이터베이스가 만든다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

### retiring

#### [a-user-granted-nothing-may-not-retire-a-domain](/tests/scenario/bai_scenario/manager/domain/test_retiring.py) — pass

아무 권한도 받지 않은 사용자는 도메인을 물릴 수 없다

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

- DomainAdapter.admin_delete — user-1이 untouchable-1을 물림

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [purging-a-domain-nothing-else-refers-to-succeeds](/tests/scenario/bai_scenario/manager/domain/test_retiring.py) — pass

아무것도 딸려 있지 않은 도메인은 완전히 지울 수 있다

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

- DomainAdapter.admin_purge — user-1이 to-purge-1을 완전히 지움

Then

- 했다는 답이 온다
  - purged = True

#### [restoring-answers-that-it-restored](/tests/scenario/bai_scenario/manager/domain/test_retiring.py) — pass

물렸던 도메인을 되살리면, 되살렸다는 답이 온다

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

- DomainAdapter.admin_restore — user-1이 to-restore-1을 물렸다가 되살림

Then

- 했다는 답이 온다
  - restored = True

#### [retiring-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_retiring.py) — pass

아무 도메인도 갖지 않은 이름을 물리려 하면 대상이 없다는 것으로 거부된다

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

- DomainAdapter.admin_delete — user-1이 no-such-domain을 물림

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-retires-a-domain](/tests/scenario/bai_scenario/manager/domain/test_retiring.py) — pass

슈퍼관리자가 도메인을 물리면, 물렸다는 답이 온다

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

- DomainAdapter.admin_delete — user-1이 to-delete-1을 물림

Then

- 했다는 답이 온다
  - deleted = True

### searching

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

- DomainAdapter.admin_search — user-1이 wanted-1으로 걸러 조회

Then

- 걸러낸 그 도메인 하나만 남는다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

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

- DomainAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-answer-counts-every-domain-the-scenario-laid](/tests/scenario/bai_scenario/manager/domain/test_searching.py) — pass

이 시나리오가 심은 도메인이 넷일 때, 필터 없는 조회는 그 넷을 모두 센다

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

- DomainAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 심은 도메인이 모두 세어진다
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

