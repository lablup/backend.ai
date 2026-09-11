## app_config

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config/adapter.py)

Not exercised by any scenario: batch_load_fields.

### reading_mine

#### [a-list-is-replaced-whole-rather-than-appended](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

같은 키에 목록을 담은 두 조각을 조회하면, 뒤의 것의 목록만 남고 이어 붙지 않는다

Given

- 도메인·사용자 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 domain-fragment-1: 값 {'plugins': ['git', 'lint']}
  - 설정 조각 own-fragment-1: 값 {'plugins': ['spell']}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'plugins': ['spell']}

#### [a-name-asked-twice-is-answered-twice](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

같은 이름을 두 번 지정해 조회하면, 같은 값이 두 번 반환된다

Given

- 공개 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 공개 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1, config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 2
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}
  - app_configs[1].config_name: 요청한 이름와 같다
  - app_configs[1].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}

#### [a-name-holding-no-fragment-answers-an-empty-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

정의만 있고 허용 목록 항목도 조각도 없는 이름을 읽기 권한을 받은 사용자가 조회하면, 그 이름이 응답에서 빠지지 않고 빈 설정으로 반환된다

Given

- 어느 스코프에도 허용되지 않은 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 어느 스코프에도 허용되지 않은 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {}

#### [a-name-nothing-registers-answers-an-empty-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

정의조차 없는 이름을 읽기 권한을 받은 사용자가 조회하면, 정의가 없다고 거부되지 않고 빈 설정으로 반환된다. 이 조회는 정의를 확인하지 않고 조각만 본다

Given

- 등록되지 않은 설정 이름과, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유

When

- AppConfigAdapter.my_app_configs — user-1이 unregistered의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {}

#### [a-public-fragment-alone-answers-its-own-value](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

공개 스코프에만 조각이 있는 이름을 조회하면, 그 조각의 값이 그대로 반환된다

Given

- 공개 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 공개 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}

#### [a-rank-the-admin-flipped-lets-the-domains-fragment-override-mine](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

도메인 허용 목록 항목의 순위를 사용자 항목보다 크게 두면, 같은 조각들에서 겹치는 키의 우선순위가 도메인으로 뒤바뀐다. 순위는 허용 목록 항목에 있고 값의 소유자는 바꿀 수 없다

Given

- 도메인·사용자 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위 400
    - 허용 목록 항목 entry-2: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 domain-fragment-1: 값 {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}
  - 설정 조각 own-fragment-1: 값 {'theme': 'solar', 'menu': {'home': False}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'dark', 'menu': {'home': False, 'docs': False, 'billing': True}}

#### [a-user-granted-nothing-may-not-read-their-own-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

아무 권한도 없는 사용자가 자기 설정을 조회하면, 스코프 권한 검사에서 권한 부족으로 거부된다

Given

- 공개 스코프에 허용된 설정 이름 하나와, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-value-written-as-null-overrides-rather-than-being-skipped](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

앞 조각의 키에 값이 있고 뒤 조각이 같은 키를 비워 두면, 그 키는 비어 있는 채로 반환된다. 빈 값도 덮어쓴다

Given

- 도메인·사용자 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 domain-fragment-1: 값 {'banner': 'welcome'}
  - 설정 조각 own-fragment-1: 값 {'banner': None}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'banner': None}

#### [another-domains-fragment-does-not-merge-into-mine](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

다른 도메인이 같은 이름에 조각을 두었어도, 자기 설정을 조회하면 자기 도메인 조각의 값만 반환된다

Given

- 도메인 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 domain-fragment-1: 값 {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}
  - 도메인 away-1
  - 설정 조각 other-domains-fragment-1: 값 {'theme': 'elsewhere'}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}

#### [another-users-fragment-does-not-merge-into-mine](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

같은 도메인의 다른 사용자가 같은 이름에 조각을 두었어도, 자기 설정을 조회하면 자기 조각의 값만 반환된다

Given

- 사용자 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 own-fragment-1: 값 {'theme': 'solar', 'menu': {'home': False}}
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 설정 조각 anothers-fragment-1: 값 {'theme': 'theirs', 'secret': 1}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'solar', 'menu': {'home': False}}

#### [my-own-fragment-overrides-the-domains](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

같은 이름에 도메인 조각과 자기 조각이 모두 있고 허용 목록 항목이 기본 순위이면, 겹치는 키는 자기 값이 남고 겹치지 않는 키는 양쪽 모두 남는다

Given

- 도메인·사용자 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 domain-fragment-1: 값 {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}
  - 설정 조각 own-fragment-1: 값 {'theme': 'solar', 'menu': {'home': False}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'solar', 'menu': {'docs': False, 'billing': True, 'home': False}}

#### [nested-dicts-merge-key-by-key-inside](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

같은 키 아래 중첩 사전을 담은 두 조각을 조회하면, 겹치지 않는 안쪽 키는 양쪽 모두 남고 겹치는 안쪽 키만 뒤의 것이 남는다

Given

- 도메인·사용자 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 domain-fragment-1: 값 {'editor': {'font': {'size': 12, 'family': 'mono'}, 'wrap': True}}
  - 설정 조각 own-fragment-1: 값 {'editor': {'font': {'size': 14}, 'theme': 'night'}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'editor': {'font': {'size': 14, 'family': 'mono'}, 'wrap': True, 'theme': 'night'}}

#### [several-names-answer-one-each-in-request-order](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

이름 셋을 한 번에 조회하면, 각각의 병합 결과가 요청한 순서대로 반환된다

Given

- 공개 설정 조각을 하나씩 가진 설정 이름 3개와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 공개 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 설정 정의 config-2: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-2: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 설정 정의 config-3: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-3: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'n': 1}
  - 공개 설정 조각 public-fragment-2: 값 {'n': 2}
  - 공개 설정 조각 public-fragment-3: 값 {'n': 3}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1, config-2, config-3의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 3
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'n': 1}
  - app_configs[1].config_name: 요청한 이름와 같다
  - app_configs[1].config = {'n': 2}
  - app_configs[2].config_name: 요청한 이름와 같다
  - app_configs[2].config = {'n': 3}

#### [the-domains-fragment-overrides-the-public-one](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

같은 이름에 공개 조각과 도메인 조각이 모두 있고 허용 목록 항목이 기본 순위이면, 겹치는 키는 도메인 값이 남는다

Given

- 공개·도메인 스코프에 허용된 설정 이름 하나와, 자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 자기 스코프에서 설정에 대한 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 역할 own-scope-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 own-scope-1: app_config 전체에 READ 허용
    - 일반 사용자 user-1: 역할 own-scope-1 보유
  - 공개·도메인 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True, 'docs': True}}
  - 설정 조각 domain-fragment-1: 값 {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'dark', 'menu': {'home': True, 'docs': False, 'billing': True}}

#### [turning-enforcement-off-lets-a-user-granted-nothing-read](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 자기 설정을 조회할 수 있다. 이 조회는 역할이 아니라 권한 그래프로 보호되므로 스위치가 영향을 준다

Given

- 공개 스코프에 허용된 설정 이름 하나와, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs — user-1이 config-1의 자기 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}

### reading_public

#### [a-caller-not-signed-in-reads-the-public-value-only](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py) — pass

공개·도메인·사용자 조각이 모두 있는 이름을 로그인 없이 조회하면, 공개 조각의 값만 반환된다. 도메인과 사용자 조각은 섞이지 않는다

Given

- 공개·도메인·사용자 스코프에 허용된 설정 이름 하나와, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개·도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-3: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True}}
  - 설정 조각 domain-fragment-1: 값 {'theme': 'dark'}
  - 설정 조각 own-fragment-1: 값 {'theme': 'solar'}

When

- AppConfigAdapter.public_app_configs — 로그인하지 않은 호출자가 config-1의 공개 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True}}

#### [a-name-holding-no-public-fragment-answers-an-empty-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py) — pass

사용자 조각만 있는 이름을 로그인 없이 조회하면, 빈 설정이 반환된다

Given

- 사용자 스코프에 허용된 설정 이름 하나와, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 조각 own-fragment-1: 값 {'theme': 'solar'}

When

- AppConfigAdapter.public_app_configs — 로그인하지 않은 호출자가 config-1의 공개 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {}

#### [a-name-nothing-registers-answers-an-empty-config-too](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py) — pass

정의조차 없는 이름을 로그인 없이 조회하면, 공개 조각이 없는 이름과 같은 빈 설정이 반환된다. 이 조회로는 어떤 이름이 등록돼 있는지 알 수 없다

Given

- 등록되지 않은 설정 이름과, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAdapter.public_app_configs — 로그인하지 않은 호출자가 unregistered의 공개 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {}

#### [a-signed-in-user-granted-nothing-gets-the-same-public-answer](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py) — pass

같은 조각 셋을 아무 권한도 없는 사용자가 로그인한 채 공개 조회로 조회해도, 공개 조각의 값만 반환된다. 이 조회는 호출자를 아예 보지 않는다

Given

- 공개·도메인·사용자 스코프에 허용된 설정 이름 하나와, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개·도메인·사용자 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-2: 도메인 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 허용 목록 항목 entry-3: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light', 'menu': {'home': True}}
  - 설정 조각 domain-fragment-1: 값 {'theme': 'dark'}
  - 설정 조각 own-fragment-1: 값 {'theme': 'solar'}

When

- AppConfigAdapter.public_app_configs — user-1가 config-1의 공개 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 1
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True}}

#### [several-names-answer-one-each-in-request-order](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py) — pass

이름 셋을 한 번에 로그인 없이 조회하면, 각각의 공개 값이 요청한 순서대로 반환된다

Given

- 공개 설정 조각을 하나씩 가진 설정 이름 3개와, 설정 권한이 하나도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 권한이 하나도 없는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
      - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 공개 스코프에 허용된 설정 이름 준비
    - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 설정 정의 config-2: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-2: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
    - 설정 정의 config-3: 이 이름의 설정이 등록돼 있다
    - 허용 목록 항목 entry-3: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'n': 1}
  - 공개 설정 조각 public-fragment-2: 값 {'n': 2}
  - 공개 설정 조각 public-fragment-3: 값 {'n': 3}

When

- AppConfigAdapter.public_app_configs — 로그인하지 않은 호출자가 config-1, config-2, config-3의 공개 설정을 조회

Then

- 요청한 이름마다 병합된 설정이 반환된다
  - app_configs = 3
  - app_configs[0].config_name: 요청한 이름와 같다
  - app_configs[0].config = {'n': 1}
  - app_configs[1].config_name: 요청한 이름와 같다
  - app_configs[1].config = {'n': 2}
  - app_configs[2].config_name: 요청한 이름와 같다
  - app_configs[2].config = {'n': 3}

