## domain

Not exercised by any scenario: batch_load_by_ids, batch_load_by_names, batch_load_fields, scoped_search, search_rg_domains.

### creating

#### a-blank-name-is-refused — pass

이름이 공백뿐이면 도메인을 만들 수 없다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_create 호출
  - CreateDomainInput(name='   ')
  - UserInfo(id=UserID('01a08a05-0380-764d-9958-cefe8b996dd8'), role=<UserRole.SUPERADMIN: 'superadmin'>, domain_name='home-1')

Then

- 거부: InvalidAPIParameters

#### a-name-another-domain-already-holds-is-refused — pass

이미 어떤 도메인이 쓰고 있는 이름으로 만들려 하면, 권한이 있어도 이름이 겹친다는 이유로 거부된다

Given

- 도메인 home-1
- 도메인 taken-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_create 호출
  - CreateDomainInput(name='taken-1')
  - UserInfo(id=UserID('01a08a05-01e0-75b2-98be-c03e8752a05b'), role=<UserRole.SUPERADMIN: 'superadmin'>, domain_name='home-1')

Then

- 거부: InvalidAPIParameters

#### a-user-who-is-not-the-superadmin-may-not-create-a-domain — pass

슈퍼관리자가 아닌 사용자가 도메인을 만들려 하면, 권한을 얼마나 받았는지와 무관하게 역할로 막힌다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 일반 사용자 user-1의 admin_create 호출
  - CreateDomainInput(name='by-a-user')
  - UserInfo(id=UserID('01a08a05-0545-7d37-8588-24ae88ceffa6'), role=<UserRole.USER: 'user'>, domain_name='home-1')

Then

- 거부: InsufficientPrivilege

#### creating-a-domain-answers-with-the-whole-node — pass

슈퍼관리자가 이름과 설명만 주고 도메인을 만들면, 요청에 없던 값들은 기본값으로 채워진 노드 전체가 답으로 온다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_create 호출
  - CreateDomainInput(name='new-domain', description='a fresh one')
  - UserInfo(id=UserID('01a08a05-0032-719d-8e4c-49ffc0f00b78'), role=<UserRole.SUPERADMIN: 'superadmin'>, domain_name='home-1')

Then

- 답 전체 일치, 다만 domain.id, domain.lifecycle.created_at, domain.lifecycle.modified_at 제외

#### turning-enforcement-off-still-does-not-let-a-user-create-a-domain — pass

엔티티 권한 집행을 꺼도 도메인 생성은 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자
- manager.rbac.enforcement_enabled 설정됨

When

- 일반 사용자 user-1의 admin_create 호출
  - CreateDomainInput(name='by-a-user-again')
  - UserInfo(id=UserID('01a08a05-06f0-7e76-b44d-9d27dd0b00ab'), role=<UserRole.USER: 'user'>, domain_name='home-1')

Then

- 거부: InsufficientPrivilege

### editing

#### a-user-granted-nothing-may-not-edit-a-domain — pass

아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부된다

Given

- 도메인 home-1
- 도메인 untouchable-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 일반 사용자 user-1의 admin_update 호출
  - 'untouchable-1'
  - UpdateDomainInput(description='x')
  - UserInfo(id=UserID('01a08a05-04ce-79a5-9317-8a29f925987d'), role=<UserRole.USER: 'user'>, domain_name='home-1')

Then

- 거부: NotEnoughPermission

#### clearing-the-active-flag-is-how-a-domain-retires — pass

활성 플래그를 내리는 수정으로 도메인을 물릴 수 있고, 답이 그 상태를 실어 온다

Given

- 도메인 home-1
- 도메인 to-retire-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_update 호출
  - 'to-retire-1'
  - UpdateDomainInput(is_active=False)
  - UserInfo(id=UserID('01a08a05-0148-7543-9260-6aba147a4c54'), role=<UserRole.SUPERADMIN: 'superadmin'>, domain_name='home-1')

Then

- domain.lifecycle.is_active = False

#### editing-a-description-leaves-the-name-alone — pass

슈퍼관리자가 도메인의 설명만 바꾸면, 설명은 새 값이 되고 이름은 그대로 남는다

Given

- 도메인 home-1
- 도메인 editable-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_update 호출
  - 'editable-1'
  - UpdateDomainInput(description='edited')
  - UserInfo(id=UserID('01a08a04-ffd3-7595-ae21-6d6c0b8dff06'), role=<UserRole.SUPERADMIN: 'superadmin'>, domain_name='home-1')

Then

- domain.basic_info.description = 'edited'

#### editing-a-name-nothing-answers-to-is-not-found — pass

아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부된다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_update 호출
  - 'no-such-domain'
  - UpdateDomainInput(description='x')
  - UserInfo(id=UserID('01a08a05-02fa-75ce-acaa-8424e920783d'), role=<UserRole.SUPERADMIN: 'superadmin'>, domain_name='home-1')

Then

- 거부: EntityNotFoundError

### reading

#### a-user-granted-nothing-may-not-read-a-domain — pass

같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, 이름으로 조회하면 권한 부족으로 거부된다

Given

- 도메인 host-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 일반 사용자 user-1의 get 호출
  - 'host-1'

Then

- 거부: NotEnoughPermission

#### reading-a-name-nothing-answers-to-is-not-found — pass

슈퍼관리자가 존재하지 않는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부된다

Given

- 도메인 host-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 get 호출
  - 'no-such-domain'

Then

- 거부: EntityNotFoundError

#### the-superadmin-reads-a-domain-by-name — pass

도메인 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 도메인이 답으로 온다

Given

- 도메인 host-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 get 호출
  - 'host-1'

Then

- basic_info.name = 'host-1'

### retiring

#### a-user-granted-nothing-may-not-retire-a-domain — pass

아무 권한도 받지 않은 사용자는 도메인을 물릴 수 없다

Given

- 도메인 home-1
- 도메인 untouchable-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 일반 사용자 user-1의 admin_delete 호출
  - DeleteDomainInput(name='untouchable-1')

Then

- 거부: NotEnoughPermission

#### purging-a-domain-nothing-else-refers-to-succeeds — pass

아무것도 딸려 있지 않은 도메인은 완전히 지울 수 있다

Given

- 도메인 home-1
- 도메인 to-purge-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_purge 호출
  - PurgeDomainInput(name='to-purge-1')

Then

- purged = True

#### restoring-answers-that-it-restored — pass

물렸던 도메인을 되살리면, 되살렸다는 답이 온다

Given

- 도메인 home-1
- 도메인 to-restore-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_restore 호출
  - RestoreDomainInput(name='to-restore-1')

Then

- restored = True

#### retiring-a-name-nothing-answers-to-is-not-found — pass

아무 도메인도 갖지 않은 이름을 물리려 하면 대상이 없다는 것으로 거부된다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_delete 호출
  - DeleteDomainInput(name='no-such-domain')

Then

- 거부: EntityNotFoundError

#### the-superadmin-retires-a-domain — pass

슈퍼관리자가 도메인을 물리면, 물렸다는 답이 온다

Given

- 도메인 home-1
- 도메인 to-delete-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_delete 호출
  - DeleteDomainInput(name='to-delete-1')

Then

- deleted = True

### searching

#### a-name-filter-narrows-the-answer-to-the-domain-it-names — pass

도메인 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 도메인만 남는다

Given

- 도메인 home-1
- 도메인 wanted-1
- 도메인 other-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_search 호출
  - AdminSearchDomainsInput(filter=DomainFilter(name=StringFilter(equals='wanted-1')))

Then

- items 전부: basic_info.name = 'wanted-1'

#### a-user-who-is-not-the-superadmin-may-not-search-every-domain — pass

슈퍼관리자가 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 막힌다

Given

- 도메인 home-1
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 일반 사용자 user-1의 admin_search 호출
  - AdminSearchDomainsInput()

Then

- 거부: InsufficientPrivilege

#### the-answer-counts-every-domain-the-scenario-laid — pass

이 시나리오가 심은 도메인이 넷일 때, 필터 없는 조회는 그 넷을 모두 센다

Given

- 도메인 home-1
- 도메인 other-1
- 도메인 other-2
- 도메인 other-3
- 도메인에 속한 사용자 한 명 준비
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
  - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
  - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다  ← 행위자

When

- 슈퍼관리자 user-1의 admin_search 호출
  - AdminSearchDomainsInput()

Then

- total_count = 4

