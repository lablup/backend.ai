## app_config_fragment

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config_fragment/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_fragment/adapter.py)

Not exercised by any scenario: batch_load_fields.

### purging

#### [a-user-granted-hard-delete-on-their-own-scope-may-not-purge-another-users-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py) — pass

다른 사용자의 조각을 자기 스코프에만 지우기 권한을 받은 사용자가 지우면, 권한 부족으로 거부된다

Given

- 다른 사용자의 조각 하나와, 자기 스코프에서 조각에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 조각 anothers-fragment-1: 값 {'theme': 'theirs'}

When

- AppConfigFragmentAdapter.purge — user-1이 config-1의 조각을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-hard-delete-on-their-own-scope-purges-their-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py) — pass

자기 조각 하나가 있고 자기 스코프에 지우기 권한을 받은 사용자가 지우면, 지운 id를 실은 답이 온다

Given

- 자기 조각 하나와, 자기 스코프에서 조각에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'mine'}

When

- AppConfigFragmentAdapter.purge — user-1이 config-1의 조각을 지움

Then

- 지운 조각의 id를 답한다
  - id: 심은 조각와 같다

#### [a-user-granted-read-alone-may-not-purge-their-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py) — pass

자기 조각에 읽기 권한만 받은 사용자가 지우면, 권한 부족으로 거부된다. 지우기는 읽기와 다른 문이다

Given

- 자기 조각 하나와, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'mine'}

When

- AppConfigFragmentAdapter.purge — user-1이 config-1의 조각을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다

Given

- 자기 조각 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'mine'}

When

- AppConfigFragmentAdapter.purge — user-1이 아무것도 갖지 않은 id을 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [mine-anothers-and-a-missing-id-are-each-answered-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py) — pass

자기 스코프에만 지우기 권한을 받은 사용자가 자기 조각 둘, 다른 사용자의 조각, 없는 id를 한 번에 지우면, 자기 둘은 지워진 목록에, 남의 것과 없는 id는 실패 목록에 이유를 달고 온다

Given

- 자기 조각 2개와 다른 사용자의 조각 하나, 그리고 자기 스코프에서 조각에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 own-fragment-2: 값 {'mine': 1}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.bulk_purge — user-1이 자기 조각 2개, 다른 사용자의 조각, 아무것도 갖지 않은 id를 한 번에 지움

Then

- 자기 것은 지워진 목록에, 남의 것과 없는 id는 실패 목록에 온다
  - items: 심은 자기 조각들와 같다
  - failed = 2
  - failed[0].id: 심은 남의 조각와 같다
  - failed[*].message: 무시함 — 이유는 글로 오고, 글은 바뀌어도 되는 값이다

#### [the-superadmin-purges-both-and-a-missing-id-fails-alone](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py) — pass

슈퍼관리자가 조각 둘과 없는 id 하나를 한 번에 지우면, 둘은 지워진 목록에, 없는 id는 실패 목록에 온다

Given

- 자기 조각 1개와 다른 사용자의 조각 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.bulk_purge — user-1이 자기 조각 1개, 다른 사용자의 조각, 아무것도 갖지 않은 id를 한 번에 지움

Then

- 있는 둘은 지워진 목록에, 없는 id는 실패 목록에 온다
  - items: 심은 조각들와 같다
  - failed = 1
  - failed[*].message: 무시함 — 이유는 글로 오고, 글은 바뀌어도 되는 값이다

### reading

#### [a-user-granted-nothing-may-not-read-a-public-fragment-by-id](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py) — pass

공개 조각을 아무 권한도 없는 사용자가 id로 조회하면, 권한 부족으로 거부된다. 스코프로 읽을 때와 반대로, id 읽기는 그 조각 자체에 걸린 권한을 본다

Given

- 공개 조각 하나와, 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'theme': 'public'}

When

- AppConfigFragmentAdapter.get — user-1이 config-1의 조각으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-their-own-scope-may-not-read-another-users-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py) — pass

다른 사용자의 조각을 자기 스코프에만 읽기 권한을 받은 사용자가 id로 조회하면, 권한 부족으로 거부된다

Given

- 다른 사용자의 조각 하나와, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 조각 anothers-fragment-1: 값 {'theme': 'theirs'}

When

- AppConfigFragmentAdapter.get — user-1이 config-1의 조각으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-their-own-scope-reads-their-fragment-by-id](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py) — pass

자기 조각 하나가 있고 자기 스코프에 읽기 권한을 받은 사용자가 id로 조회하면, 그 조각 전체가 답으로 온다

Given

- 자기 조각 하나와, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'mine'}

When

- AppConfigFragmentAdapter.get — user-1이 config-1의 조각으로 조회

Then

- 심은 조각 전체가 온다
  - id: 심은 조각와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - scope_id: 심은 조각의 소유자와 같다
  - config = {'theme': 'mine'}
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. 권한 검사를 지나가는 사람만 이 답을 본다

Given

- 자기 조각 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'mine'}

When

- AppConfigFragmentAdapter.get — user-1이 아무것도 갖지 않은 id으로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py) — pass

자기 스코프에 읽기 권한을 받은 사용자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없기 때문이다

Given

- 자기 조각 하나와, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'mine'}

When

- AppConfigFragmentAdapter.get — user-1이 아무것도 갖지 않은 id으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

### reading_by_names

#### [a-domain-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

슈퍼관리자가 아무 도메인도 아닌 id를 지목해 읽으면, 대상이 없다는 것으로 거부된다. 권한 검사를 지나가는 사람만 이 답을 본다

Given

- 자기 도메인에 열린 이름 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names — user-1이 아무 도메인도 아닌 id를 지목해 config-1의 조각을 조회

Then

- 거부된다
  - 거부: DomainNotFound

#### [a-domain-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

자기 도메인에 읽기 권한을 받은 사용자가 아무 도메인도 아닌 id를 지목해 읽으면, 대상이 없다는 것이 아니라 권한 부족으로 거부된다

Given

- 자기 도메인에 열린 이름 하나, 그리고 자기 도메인에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인 home-1에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 seated-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 seated-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 seated-1 보유

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names — user-1이 아무 도메인도 아닌 id를 지목해 config-1의 조각을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-their-own-fragments](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

자기 조각이 있어도 아무 권한도 받지 않은 사용자가 이름으로 읽으면, 권한 부족으로 거부된다

Given

- 사용자 스코프에 열린 이름 1개 중 1개에 놓인 자기 조각과, 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'slot': 0}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names — user-1이 config-1의 자기 조각을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-the-domain-reads-its-fragment-by-name](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

도메인 조각이 있고 그 도메인 스코프에 읽기 권한을 받은 사용자가 도메인을 지목해 읽으면, 그 조각이 온다

Given

- 자기 도메인에 열린 이름 하나와 거기 놓인 조각 하나, 그리고 자기 도메인에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인 home-1에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 seated-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 seated-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 seated-1 보유
  - 조각 fragment-1: 값 {'theme': 'domain'}

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names — user-1이 도메인 스코프를 지목해 config-1의 조각을 조회

Then

- 지목한 자리의 조각 하나가 온다
  - items = 1
  - items[0].id: 심은 조각와 같다
  - items[0].scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - items[0].scope_id: 지목한 소유자와 같다
  - items[0].config = {'theme': 'domain'}

#### [a-user-granted-read-on-their-own-scope-may-not-read-another-users](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

자기 스코프에만 읽기 권한을 받은 사용자가 다른 사용자를 지목해 읽으면, 권한 부족으로 거부된다

Given

- 다른 사용자에 열린 이름 하나와 거기 놓인 조각 하나, 그리고 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 조각 fragment-1: 값 {'theme': 'theirs'}

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names — user-1이 사용자 스코프를 지목해 config-1의 조각을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [another-users-fragment-under-the-same-name-is-not-answered](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

같은 이름에 다른 사용자의 조각이 있어도, 자기 조각을 읽으면 자기 것만 온다

Given

- 사용자 스코프에 열린 이름 1개 중 1개에 놓인 자기 조각, 같은 이름의 다른 사용자 조각과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'slot': 0}
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 조각 anothers-fragment-1: 값 {'theirs': True}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names — user-1이 config-1의 자기 조각을 조회

Then

- 이름마다 자기 조각이 있으면 그 조각, 없으면 빈 자리가 요청 순서대로 온다
  - items = 1
  - items[0].id: 심은 자기 조각와 같다
  - items[0].config = {'slot': 0}

#### [anyone-signed-in-reads-a-public-fragment-by-name](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

공개 조각이 있고 아무 권한도 없는 사용자가 공개 스코프를 지목해 읽으면, 그 조각이 온다. 공개 조각에는 지킬 스코프가 없다

Given

- 공개 스코프에 열린 이름 하나와 거기 놓인 조각 하나, 그리고 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개 조각 public-fragment-1: 값 {'theme': 'public'}

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names — user-1이 공개 스코프를 지목해 config-1의 조각을 조회

Then

- 지목한 자리의 조각 하나가 온다
  - items = 1
  - items[0].id: 심은 조각와 같다
  - items[0].scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - items[0].scope_id: 소유자 없음와 같다
  - items[0].config = {'theme': 'public'}

#### [the-domains-fragment-under-the-same-name-is-not-answered](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

같은 이름에 자기 도메인의 조각이 있어도, 자기 조각을 읽으면 자기 것만 온다. 이 읽기는 사용자 스코프 하나만 본다

Given

- 사용자 스코프에 열린 이름 1개 중 1개에 놓인 자기 조각, 같은 이름의 자기 도메인 조각과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자·도메인 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 허용 항목 entry-2: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'slot': 0}
  - 조각 domain-fragment-1: 값 {'domains': True}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names — user-1이 config-1의 자기 조각을 조회

Then

- 이름마다 자기 조각이 있으면 그 조각, 없으면 빈 자리가 요청 순서대로 온다
  - items = 1
  - items[0].id: 심은 자기 조각와 같다
  - items[0].config = {'slot': 0}

#### [three-names-answer-a-fragment-or-an-empty-slot-each-in-request-order](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py) — pass

사용자 스코프에 열린 이름 셋 중 둘에 자기 조각이 있고 읽기 권한을 받은 사용자가 셋을 읽으면, 세 자리가 요청 순서대로 오고 조각이 없는 자리는 비어 있다

Given

- 사용자 스코프에 열린 이름 3개 중 2개에 놓인 자기 조각과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 config-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 config-3: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'slot': 0}
  - 조각 own-fragment-2: 값 {'slot': 2}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names — user-1이 config-1, config-2, config-3의 자기 조각을 조회

Then

- 이름마다 자기 조각이 있으면 그 조각, 없으면 빈 자리가 요청 순서대로 온다
  - items = 3
  - items[0].id: 심은 자기 조각와 같다
  - items[0].config = {'slot': 0}
  - items[1] = None
  - items[2].id: 심은 자기 조각와 같다
  - items[2].config = {'slot': 2}

### reading_many

#### [an-empty-id-list-answers-empty-without-calling-anything](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_many.py) — pass

빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다

Given

- 자기 조각 1개와 다른 사용자의 조각 하나, 그리고 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - items = []

#### [mine-anothers-and-a-missing-id-are-each-answered-in-order-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_many.py) — pass

자기 스코프에만 읽기 권한을 받은 사용자가 자기 조각, 다른 사용자의 조각, 없는 id를 한 번에 읽으면, 목록 순서대로 자기 것은 노드, 남의 것과 없는 id는 그 자리만 권한 부족으로 거부된다

Given

- 자기 조각 1개와 다른 사용자의 조각 하나, 그리고 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.batch_load_by_ids — user-1이 자기 조각, 다른 사용자의 조각, 아무것도 갖지 않은 id를 한 번에 조회

Then

- 자기 것은 노드, 남의 것과 없는 id는 그 자리만 거부된다
  - items = 3
  - items[0].id: 심은 자기 조각와 같다
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_many.py) — pass

슈퍼관리자가 조각 둘과 없는 id 하나를 한 번에 읽으면, 둘은 노드로 오고 없는 id 자리는 비어서 온다. 권한 검사를 지나가는 사람만 빈 자리를 본다

Given

- 자기 조각 1개와 다른 사용자의 조각 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.batch_load_by_ids — user-1이 자기 조각, 다른 사용자의 조각, 아무것도 갖지 않은 id를 한 번에 조회

Then

- 있는 둘은 노드로, 없는 id 자리는 비어서 온다
  - items = 3
  - items[0].id: 심은 자기 조각와 같다
  - items[1].id: 심은 남의 조각와 같다
  - items[2] = None

### searching

#### [a-domain-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

슈퍼관리자가 아무 도메인도 아닌 id를 지목해 훑으면, 대상이 없다는 것으로 거부된다

Given

- 아무 조각도 없음과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigFragmentAdapter.scoped_search — user-1이 도메인 스코프를 지목해 필터 없이 조회

Then

- 거부된다
  - 거부: DomainNotFound

#### [a-user-granted-read-may-not-search-every-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

자기 도메인 스코프에 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 거부된다. 한 스코프를 훑는 문과 전체를 훑는 문이 다르다

Given

- 자기 도메인의 조각 1개과, 자기 도메인에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인 home-1에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 seated-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 seated-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 seated-1 보유
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 domains-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 domain-fragment-1: 값 {'domains': 0}

When

- AppConfigFragmentAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-granted-read-on-their-own-scope-may-not-search-another-users](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

자기 스코프에만 읽기 권한을 받은 사용자가 다른 사용자를 지목해 훑으면, 권한 부족으로 거부된다

Given

- 자기 조각 1개, 다른 사용자의 조각 1개과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.scoped_search — user-1이 다른 사용자를 지목해 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [anyone-signed-in-searches-the-public-scope](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

공개 조각 둘이 있고 아무 권한도 없는 사용자가 공개 스코프를 지목해 훑으면, 둘을 모두 센다. 공개 조각에는 지킬 스코프가 없다

Given

- 공개 조각 2개과, 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 publics-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 publics-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'publics': 0}
  - 공개 조각 public-fragment-2: 값 {'publics': 1}

When

- AppConfigFragmentAdapter.scoped_search — user-1이 공개 스코프를 지목해 필터 없이 조회

Then

- 그 자리의 조각이 모두, 그리고 그것만 세어진다
  - items = ['publics-1', 'publics-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-a-scope-by-name-keeps-only-that-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

자기 조각 둘이 있고 읽기 권한을 받은 사용자가 이름으로 걸러 훑으면, 그 이름의 것만 남는다

Given

- 자기 조각 2개과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 own-fragment-2: 값 {'mine': 1}

When

- AppConfigFragmentAdapter.scoped_search — user-1이 사용자 스코프를 지목해 이름 mine-1으로 걸러 조회

Then

- 이름으로 고른 조각만 남는다
  - items = ['mine-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [filtering-everything-by-name-keeps-only-that-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

이름이 다른 조각 여럿이 있고 슈퍼관리자가 이름으로 걸러 훑으면, 그 이름의 것만 남는다

Given

- 자기 조각 2개, 공개 조각 1개과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 own-fragment-2: 값 {'mine': 1}
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 publics-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'publics': 0}

When

- AppConfigFragmentAdapter.admin_search — user-1이 이름 mine-1으로 걸러 전체 조회

Then

- 이름으로 고른 조각만 남는다
  - items = ['mine-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [filtering-everything-by-scope-kind-keeps-only-that-kinds-fragments](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

세 종류에 조각이 하나씩 있고 슈퍼관리자가 사용자 종류로 걸러 훑으면, 사용자 조각만 남는다

Given

- 자기 조각 1개, 자기 도메인의 조각 1개, 공개 조각 1개과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 domains-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 domain-fragment-1: 값 {'domains': 0}
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 publics-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'publics': 0}

When

- AppConfigFragmentAdapter.admin_search — user-1이 사용자 종류로 걸러 전체 조회

Then

- 사용자 종류의 조각만 남는다
  - items = [<AppConfigScopeType.USER: 'user'>]
  - total_count = 1

#### [leaving-the-page-size-out-answers-ten-with-a-next-page](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

자기 조각 열하나가 있고 읽기 권한을 받은 사용자가 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 자기 조각 11개과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-3: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-4: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-4: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-5: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-5: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-6: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-6: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-7: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-7: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-8: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-8: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-9: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-9: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-10: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-10: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-11: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-11: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 own-fragment-2: 값 {'mine': 1}
  - 조각 own-fragment-3: 값 {'mine': 2}
  - 조각 own-fragment-4: 값 {'mine': 3}
  - 조각 own-fragment-5: 값 {'mine': 4}
  - 조각 own-fragment-6: 값 {'mine': 5}
  - 조각 own-fragment-7: 값 {'mine': 6}
  - 조각 own-fragment-8: 값 {'mine': 7}
  - 조각 own-fragment-9: 값 {'mine': 8}
  - 조각 own-fragment-10: 값 {'mine': 9}
  - 조각 own-fragment-11: 값 {'mine': 10}

When

- AppConfigFragmentAdapter.scoped_search — user-1이 사용자 스코프를 지목해 필터 없이 조회

Then

- 열 건까지 오고 다음 쪽이 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [naming-two-scopes-at-once-is-refused-as-bad-input](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

읽기 권한을 받은 사용자가 도메인과 사용자를 함께 지목해 훑으면, 입력이 틀렸다는 이유로 거부된다. 이 훑기는 한 스코프에서만 돈다

Given

- 자기 조각 1개과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}

When

- AppConfigFragmentAdapter.scoped_search — user-1이 도메인과 사용자를 함께 지목해 조회

Then

- 거부된다
  - 거부: InvalidAPIParameters

#### [searching-my-own-scope-counts-only-my-fragments](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

자기 조각 둘과 다른 사용자의 조각 하나가 있고 자기 스코프에 읽기 권한을 받은 사용자가 자기 스코프를 훑으면, 자기 둘만 센다

Given

- 자기 조각 2개, 다른 사용자의 조각 1개과, 자기 스코프에서 조각에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 theirs-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 own-fragment-2: 값 {'mine': 1}
  - 조각 anothers-fragment-1: 값 {'theirs': 0}

When

- AppConfigFragmentAdapter.scoped_search — user-1이 사용자 스코프를 지목해 필터 없이 조회

Then

- 그 자리의 조각이 모두, 그리고 그것만 세어진다
  - items = ['mine-1', 'mine-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-counts-every-fragment-across-scopes](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py) — pass

공개·도메인·사용자 스코프에 조각 넷이 있고 슈퍼관리자가 전체를 훑으면, 넷을 모두 센다. 이 문은 전역 역할이다

Given

- 자기 조각 2개, 자기 도메인의 조각 1개, 공개 조각 1개과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 mine-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 mine-2: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'mine': 0}
  - 조각 own-fragment-2: 값 {'mine': 1}
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 domains-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-3: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 domain-fragment-1: 값 {'domains': 0}
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 publics-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-4: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'publics': 0}

When

- AppConfigFragmentAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 스코프를 가리지 않고 심은 조각이 모두 세어진다
  - items = 4
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

### writing

#### [a-name-nothing-registers-cannot-be-written](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

등록되지 않은 이름에 쓰기 권한을 받은 사용자가 쓰면, 쓰기 허용 안 됨으로 거부된다

Given

- 등록되지 않은 이름과, 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 unregistered에 자기 조각을 씀

Then

- 거부된다
  - 거부: AppConfigFragmentWriteNotAllowed

#### [a-name-opened-only-to-the-domain-kind-cannot-be-written-by-a-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

도메인 종류에만 열린 이름에 쓰기 권한을 받은 사용자가 자기 조각을 쓰면, 쓰기 허용 안 됨으로 거부된다. 등록되지 않은 이름과 같은 문이다

Given

- 도메인 스코프에 열린 이름 하나와, 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1에 자기 조각을 씀

Then

- 거부된다
  - 거부: AppConfigFragmentWriteNotAllowed

#### [a-user-granted-create-alone-may-not-write](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

자기 스코프에 만들기 권한만 있고 고치기 권한이 없는 사용자가 쓰면, 권한 부족으로 거부된다. 쓰기는 만들기와 고치기 둘 다를 요구한다

Given

- 사용자 스코프에 열린 이름 하나와, 자기 스코프에서 조각에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1에 자기 조각을 씀

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-write-their-own-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

사용자 종류에 열린 이름에 아무 권한도 받지 않은 사용자가 쓰면, 권한 부족으로 거부된다

Given

- 사용자 스코프에 열린 이름 하나와, 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1에 자기 조각을 씀

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-write-on-the-domain-writes-a-domain-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

자기 도메인 스코프에 쓰기 권한을 받은 사용자가 도메인을 지목해 쓰면, 스코프 종류는 도메인이고 소유자는 그 도메인이다

Given

- 자기 도메인에 열린 이름 하나, 그리고 자기 도메인에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인 home-1에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 seated-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 seated-1: app_config_fragment 전체에 CREATE 허용
    - 역할 seated-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 seated-1 보유

When

- AppConfigFragmentAdapter.scoped_upsert_app_config_fragments — user-1이 도메인 스코프를 지목해 config-1에 조각을 씀

Then

- 쓴 조각 전체가 요청 순서대로 온다
  - items = 1
  - failed = []
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].config_name: 요청한 이름와 같다
  - items[0].scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - items[0].scope_id: 지목한 소유자와 같다
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

#### [a-user-granted-write-on-their-own-scope-may-not-write-at-another-users](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

자기 스코프에만 쓰기 권한을 받은 사용자가 다른 사용자를 지목해 쓰면, 권한 부족으로 거부된다

Given

- 다른 사용자에 열린 이름 하나, 그리고 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigFragmentAdapter.scoped_upsert_app_config_fragments — user-1이 사용자 스코프를 지목해 config-1에 조각을 씀

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-write-writes-their-first-own-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

쓰기 권한을 받은 사용자가 자기 조각을 처음 쓰면, 요청이 주지 않은 소유자와 스코프 종류가 호출자에서 채워진 노드가 답으로 온다

Given

- 사용자 스코프에 열린 이름 하나와, 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1에 자기 조각을 씀

Then

- 쓴 조각 전체가 요청 순서대로 온다
  - items = 1
  - failed = []
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].config_name: 요청한 이름와 같다
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: 지목한 소유자와 같다
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-write-a-public-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

자기 도메인 스코프에 쓰기 권한을 받았어도 슈퍼관리자가 아닌 사용자가 공개 스코프를 지목해 쓰면, 역할로 거부된다. 공개 조각에는 답할 스코프가 없다

Given

- 공개 스코프에 열린 이름 하나, 그리고 자기 도메인에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인 home-1에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 seated-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 seated-1: app_config_fragment 전체에 CREATE 허용
    - 역할 seated-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 seated-1 보유

When

- AppConfigFragmentAdapter.scoped_upsert_app_config_fragments — user-1이 공개 스코프를 지목해 config-1에 조각을 씀

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [one-name-not-opened-to-the-user-kind-refuses-the-whole-write](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

열린 이름과 열리지 않은 이름을 함께 쓰면, 쓰기 허용 안 됨으로 거부된다. 쓰기는 전부 아니면 전무다

Given

- 사용자 스코프에 열린 이름 하나, 어느 스코프에도 열리지 않은 이름 1개와, 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 아무 스코프에도 열리지 않은 이름 준비
    - 설정 정의 unopened-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1, unopened-1에 자기 조각을 씀

Then

- 거부된다
  - 거부: AppConfigFragmentWriteNotAllowed

#### [several-names-are-written-at-once-in-request-order](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

사용자 스코프에 열린 이름 둘에 한 번에 쓰면, 둘 다 쓰이고 요청 순서대로 온다

Given

- 사용자 스코프에 열린 이름 하나, 사용자 스코프에 열린 이름 1개와, 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
    - 설정 정의 opened-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1, opened-1에 자기 조각을 씀

Then

- 쓴 조각 전체가 요청 순서대로 온다
  - items = 2
  - failed = []
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].config_name: 요청한 이름와 같다
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: 지목한 소유자와 같다
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 데이터베이스가 만든다
  - items[1].config_name: 요청한 이름와 같다
  - items[1].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[1].scope_id: 지목한 소유자와 같다
  - items[1].config = {'editor': {'wrap': True}}
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각

#### [the-superadmin-naming-an-owner-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

슈퍼관리자가 아무 사용자도 아닌 id를 소유자로 지목해 쓰면, 소유자 없음으로 거부된다. 소유자가 있는지는 권한 그래프에서 본다

Given

- 아무 사용자도 아닌 id에 열린 이름 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigFragmentAdapter.scoped_upsert_app_config_fragments — user-1이 사용자 스코프를 지목해 config-1에 조각을 씀

Then

- 거부된다
  - 거부: VirtualEntityNotFound

#### [the-superadmin-writes-a-public-fragment-owned-by-no-one](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

슈퍼관리자가 공개 스코프를 지목해 쓰면, 스코프 종류는 공개이고 소유자 자리는 비어 있다. 이 문은 전역 역할이다

Given

- 공개 스코프에 열린 이름 하나, 그리고 슈퍼관리자 한 명
  - 도메인 home-1
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigFragmentAdapter.scoped_upsert_app_config_fragments — user-1이 공개 스코프를 지목해 config-1에 조각을 씀

Then

- 쓴 조각 전체가 요청 순서대로 온다
  - items = 1
  - failed = []
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].config_name: 요청한 이름와 같다
  - items[0].scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - items[0].scope_id: 소유자 없음와 같다
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-user-granted-nothing-write](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 자기 조각을 쓴다. 이 문은 역할이 아니라 권한 그래프가 지키므로 스위치가 통한다

Given

- 사용자 스코프에 열린 이름 하나와, 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1에 자기 조각을 씀

Then

- 쓴 조각 전체가 요청 순서대로 온다
  - items = 1
  - failed = []
  - items[0].id: 무시함 — 데이터베이스가 만든다
  - items[0].config_name: 요청한 이름와 같다
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: 지목한 소유자와 같다
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-still-does-not-let-a-user-write-a-public-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 공개 조각을 못 쓴다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 공개 스코프에 열린 이름 하나, 그리고 조각 권한을 하나도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 공개 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigFragmentAdapter.scoped_upsert_app_config_fragments — user-1이 공개 스코프를 지목해 config-1에 조각을 씀

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [writing-the-same-name-again-replaces-the-value-whole](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py) — pass

이미 자기 조각이 있는 이름에 다른 키를 담아 다시 쓰면, id는 그대로인 채 값은 새것뿐이다. 이전 키가 남지 않는다

Given

- 사용자 스코프에 열린 이름 하나에 이미 있는 자기 조각와, 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 조각에 CREATE, UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config_fragment 전체에 CREATE 허용
    - 역할 own-scope-1: app_config_fragment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 열린 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 조각 own-fragment-1: 값 {'theme': 'light', 'menu': {'home': True}}

When

- AppConfigFragmentAdapter.my_upsert_app_config_fragments — user-1이 config-1에 자기 조각을 씀

Then

- 쓴 조각 전체가 요청 순서대로 온다
  - items = 1
  - failed = []
  - items[0].id: 이미 있던 조각와 같다
  - items[0].config_name: 요청한 이름와 같다
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: 지목한 소유자와 같다
  - items[0].config = {'menu': {'docs': True}}
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

