## user

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/user/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/user/adapter.py)

Not exercised by any scenario: batch_load_fields, resolve_domain_id.

### creating

#### [a-user-granted-nothing-may-not-create-a-user](/tests/scenario/bai_scenario/manager/user/test_creating.py) — pass

역할을 받지 않은 사용자가 만들려 하면, 도메인 스코프 권한 문이 막는다

Given

- 도메인 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.create_user — user-1이 home-1에 made을 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-may-not-be-created-in-a-domain-name-nothing-answers-to](/tests/scenario/bai_scenario/manager/user/test_creating.py) — pass

권한 받은 사용자가 없는 도메인 이름을 주면, 도메인 이름 조회 단계가 대상 없음으로 막는다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 CREATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.create_user — user-1이 no-such-domain에 made을 만듦

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [a-user-who-is-not-the-superadmin-may-not-bulk-create-users](/tests/scenario/bai_scenario/manager/user/test_creating.py) — pass

도메인 스코프에서 CREATE를 받은 사용자라도 일괄 생성을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 CREATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.bulk_create_users — user-1이 home-1에 made을 일괄 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs](/tests/scenario/bai_scenario/manager/user/test_creating.py) — pass

권한 받은 사용자가 이 일괄 생성을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 CREATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.bulk_create_users_with_keypair — user-1이 home-1에 made을 일괄 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

슈퍼관리자가 일괄 수정과 함께 남의 키로 기본 키 전환을 주면, 그 사용자는 수정 목록에서 빠지고 실패로 담긴다

Given

- 도메인 하나와 대상 사용자, 사용자 1명 더, 부르는 superadmin 한 명, 한 사람에게 기본이 아닌 키가 하나 더 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-4: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 슈퍼관리자 user-4: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.bulk_modify_users — user-3이 user-1을 일괄 수정하며 user-2의 키로 기본 키를 옮김

Then

- 수정 목록은 비고, 그 사용자가 실패 목록에 온다
  - updated_users = []
  - failed.length = 1
  - failed[0].user_id: 기본 키를 옮기려던 사용자와 같다
  - failed[0].message: 무시함 — 예외 메시지는 바뀌어도 되는 값이다

#### [a-user-granted-nothing-may-not-change-the-allowed-client-ip](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

역할 없이 허용 IP 수정을 보내면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 사용자 0명 더, 부르는 user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.update_user — user-2이 user-1의 허용 IP를 바꾸고, user-3이 다시 읽음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-edit-another-user](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

역할을 받지 않은 사용자가 수정하려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 사용자 0명 더, 부르는 user 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.update_user_by_id — user-2이 user-1의 전체 이름을 renamed로 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-changes-the-allowed-client-ip](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

대상 사용자 스코프에서 UPDATE를 받은 사용자가 허용 IP만 담은 수정을 보내면, 성공 표시가 오고 그 사용자의 허용 IP가 바뀐다

Given

- 도메인 하나와 대상 사용자, 사용자 0명 더, 부르는 user 한 명, 부르는 사람은 대상 사용자 스코프에서 UPDATE를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user — user-2이 user-1의 허용 IP를 바꾸고, user-3이 다시 읽음

Then

- 성공이 오고, 다시 읽은 사용자는 허용 IP만 바뀌어 있다
  - success = True
  - 뒤이은 읽기.id: 심은 사용자와 같다
  - 뒤이은 읽기.basic_info.username = 'user-1'
  - 뒤이은 읽기.basic_info.email = 'user-1@scenario.local'
  - 뒤이은 읽기.basic_info.full_name = None
  - 뒤이은 읽기.basic_info.description = None
  - 뒤이은 읽기.basic_info.integration_name = None
  - 뒤이은 읽기.status.status = 'active'
  - 뒤이은 읽기.status.status_info = None
  - 뒤이은 읽기.status.need_password_change = False
  - 뒤이은 읽기.organization.domain_name = 'home-1'
  - 뒤이은 읽기.organization.role = 'user'
  - 뒤이은 읽기.organization.resource_policy = 'user-policy-1'
  - 뒤이은 읽기.organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - 뒤이은 읽기.security.allowed_client_ip = ['10.0.0.1/32']
  - 뒤이은 읽기.security.totp_activated = False
  - 뒤이은 읽기.security.totp_activated_at = None
  - 뒤이은 읽기.security.sudo_session_enabled = False
  - 뒤이은 읽기.container.container_uid = None
  - 뒤이은 읽기.container.container_main_gid = None
  - 뒤이은 읽기.container.container_gids = None
  - 뒤이은 읽기.timestamps.created_at: 이 실행이 쓴 시각
  - 뒤이은 읽기.timestamps.modified_at: 이 실행이 쓴 시각

#### [a-user-granted-update-changing-only-the-full-name-leaves-the-rest](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

대상 사용자 스코프에서 UPDATE와 READ를 받은 사용자가 전체 이름만 주면, 전체 이름만 바뀐 노드가 온다

Given

- 도메인 하나와 대상 사용자, 사용자 0명 더, 부르는 user 한 명, 부르는 사람은 대상 사용자 스코프에서 UPDATE, READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id — user-2이 user-1의 전체 이름을 renamed로 바꿈

Then

- 전체 이름만 바뀐 사용자 전체가 온다
  - id: 심은 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = 'renamed'
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-bulk-edit-users](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

도메인 스코프에서 UPDATE를 받은 사용자라도 일괄 수정을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 대상 사용자, 사용자 2명 더, 부르는 user 한 명, 부르는 사람은 도메인 스코프에서 UPDATE를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-4: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 user-4: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-5: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 슈퍼관리자 user-5: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-4: 역할 user-role-1 보유

When

- UserAdapter.bulk_modify_users — user-4이 user-1의 전체 이름을 바꾸고 user-3의 이름을 user-2로 일괄 수정

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-username-another-user-holds-may-not-be-taken](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

권한 받은 사용자가 이미 쓰이는 사용자 이름을 주면, 입력 검증이 막는다

Given

- 도메인 하나와 대상 사용자, 사용자 1명 더, 부르는 user 한 명, 부르는 사람은 대상 사용자 스코프에서 UPDATE를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-4: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 슈퍼관리자 user-4: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id — user-3이 user-1의 이름을 user-2로 바꿈

Then

- 거부된다
  - 거부: UserModificationBadRequest

#### [naming-a-default-key-in-an-edit-moves-the-default-to-it](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

권한 받은 사용자가 대상 사용자의 다른 키를 기본 키로 주면, 수정이 반영된 뒤 기본 키가 옮겨간 노드가 온다

Given

- 도메인 하나와 대상 사용자, 사용자 0명 더, 부르는 user 한 명, 부르는 사람은 대상 사용자 스코프에서 UPDATE, READ를 받았다, 한 사람에게 기본이 아닌 키가 하나 더 있다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.update_user_by_id — user-2이 user-1의 추가한 키를 기본 키로 줌

Then

- 기본 키가 추가한 키로 옮겨간 사용자 전체가 온다
  - id: 심은 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 추가한 키와 같다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

#### [null-project-ids-in-an-edit-leave-the-membership-as-it-is](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

권한 받은 사용자가 소속 프로젝트 자리에 빈 값을 주면, 소속을 건드리지 않고 나머지 수정만 반영된다

Given

- 도메인 하나와 프로젝트 하나, 그 명부에 오른 대상 사용자, 대상 사용자 스코프에서 UPDATE와 READ를 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 프로젝트 team-1
  - 일반 사용자 user-1: 프로젝트 team-1 명부에 오름
  - 사용자 UPDATE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id — user-2이 user-1의 소속 프로젝트에 빈 값을 주고, user-3이 team-1으로 훑음

Then

- 사용자는 그대로이고 프로젝트 명부에 남아 있다
  - id: 심은 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각
  - 뒤이은 프로젝트 검색.items: 명부에 올린 대상 사용자 하나와 같다
  - 뒤이은 프로젝트 검색.pagination.total = 1
  - 뒤이은 프로젝트 검색.pagination.offset = 0
  - 뒤이은 프로젝트 검색.pagination.limit = 50

#### [the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

전역 역할이 문인 일괄 수정에서 슈퍼관리자가 있는 사용자와 이름이 겹치게 바꾸는 사용자를 함께 주면, 하나는 수정되고 하나는 사용자 id와 함께 실패로 담긴다

Given

- 도메인 하나와 대상 사용자, 사용자 2명 더, 부르는 superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-4: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 슈퍼관리자 user-4: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-5: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 슈퍼관리자 user-5: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.bulk_modify_users — user-4이 user-1의 전체 이름을 바꾸고 user-3의 이름을 user-2로 일괄 수정

Then

- 하나는 수정 목록에, 하나는 실패 목록에 온다
  - updated_users.length = 1
  - failed.length = 1
  - updated_users[0].id: 심은 사용자와 같다
  - updated_users[0].basic_info.username = 'user-1'
  - updated_users[0].basic_info.email = 'user-1@scenario.local'
  - updated_users[0].basic_info.full_name = 'renamed'
  - updated_users[0].basic_info.description = None
  - updated_users[0].basic_info.integration_name = None
  - updated_users[0].status.status = 'active'
  - updated_users[0].status.status_info = None
  - updated_users[0].status.need_password_change = False
  - updated_users[0].organization.domain_name = 'home-1'
  - updated_users[0].organization.role = 'user'
  - updated_users[0].organization.resource_policy = 'user-policy-1'
  - updated_users[0].organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - updated_users[0].security.allowed_client_ip = None
  - updated_users[0].security.totp_activated = False
  - updated_users[0].security.totp_activated_at = None
  - updated_users[0].security.sudo_session_enabled = False
  - updated_users[0].container.container_uid = None
  - updated_users[0].container.container_main_gid = None
  - updated_users[0].container.container_gids = None
  - updated_users[0].timestamps.created_at: 이 실행이 쓴 시각
  - updated_users[0].timestamps.modified_at: 이 실행이 쓴 시각
  - failed[0].user_id: 이름이 겹치게 바꾼 사용자와 같다
  - failed[0].message: 무시함 — 예외 메시지는 바뀌어도 되는 값이다

### login_history

#### [a-user-granted-nothing-may-not-search-their-own-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py) — pass

역할 없이 자기 이력을 훑으려 하면, 본인이어도 스코프 권한 문이 막는다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 성공한 로그인 기록 하나를 갖는다

When

- LoginHistoryAdapter.my_search — user-1이 자기 로그인 기록을 훑음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-themselves-searches-only-their-own-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py) — pass

자기 스코프에서 READ를 받은 사용자가 훑으면, 다른 사용자의 이력은 빠진다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 성공한 로그인 기록 하나를 갖는다
  - 일반 사용자 user-2: 성공한 로그인 기록 하나를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.my_search — user-1이 자기 로그인 기록을 훑음

Then

- 자기 기록 하나만 온다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 심은 기록와 같다
  - items[0].user_id: 기록의 주인와 같다
  - items[0].domain_name = 'home-1'
  - items[0].result = 'success'
  - items[0].fail_reason = None
  - items[0].client_ip = None
  - items[0].created_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-search-every-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py) — pass

권한 받은 사용자가 이력 전체 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나, 부르는 사람은 도메인 스코프에서 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginHistoryAdapter.admin_search — user-1이 로그인 기록 전체를 훑음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-searches-every-users-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py) — pass

전역 역할이 문인 이력 검색에서 슈퍼관리자가 훑으면, 사용자와 무관하게 심은 이력이 생성 시각 내림차순으로 온다

Given

- 도메인 하나와 슈퍼관리자, 성공 기록을 하나씩 가진 사용자 둘
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 성공한 로그인 기록 하나를 갖는다
  - 일반 사용자 user-2: 성공한 로그인 기록 하나를 갖는다

When

- LoginHistoryAdapter.admin_search — user-3이 로그인 기록 전체를 훑음

Then

- 심은 기록이 모두 순서대로 온다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 심은 기록와 같다
  - items[0].user_id: 기록의 주인와 같다
  - items[0].domain_name = 'home-1'
  - items[0].result = 'success'
  - items[0].fail_reason = None
  - items[0].client_ip = None
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 심은 기록와 같다
  - items[1].user_id: 기록의 주인와 같다
  - items[1].domain_name = 'home-1'
  - items[1].result = 'success'
  - items[1].fail_reason = None
  - items[1].client_ip = None
  - items[1].created_at: 이 실행이 쓴 시각

### login_sessions

#### [a-user-granted-nothing-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

역할 없이 회수하려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.my_revoke — user-1이 자기 세션을 회수

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-search-their-own-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

역할 없이 자기 세션을 훑으려 하면, 본인이어도 스코프 권한 문이 막는다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.my_search — user-1이 자기 세션을 훑음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

자기 스코프에서만 READ와 UPDATE를 받은 사용자가 다른 사용자의 세션을 주면, 그 소유자에 대한 조회 단계가 막는다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_revoke — user-1이 user-2 세션을 회수

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-only-read-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

READ만 받고 회수하려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_revoke — user-1이 자기 세션을 회수

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-themselves-searches-only-their-own-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

자기 스코프에서 READ를 받은 사용자가 훑으면, 다른 사용자의 세션은 빠진다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_search — user-1이 자기 세션을 훑음

Then

- 자기 세션 하나만 온다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 심은 세션와 같다
  - items[0].user_id: 세션의 주인와 같다
  - items[0].access_key: 세션을 연 키와 같다
  - items[0].status = 'active'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

#### [a-user-granted-update-on-themselves-revokes-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

자기 스코프에서 READ와 UPDATE를 받은 사용자가 자기 세션을 회수하면, 성공이 오고 그 세션은 더 조회되지 않으며 사용자가 회수했다는 이력이 생긴다

Given

- 도메인 하나와 사용자 둘, 부르는 사람은 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- LoginSessionAdapter.my_revoke — user-1이 자기 세션을 회수

Then

- 회수가 성공하고 뒤이은 조회에 세션이 없다
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
  - after.has_next_page = False
  - after.has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

권한 받은 사용자가 관리자 회수를 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 세션을 가진 사용자 하나, 부르는 사람은 도메인 스코프에서 사용자 UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginSessionAdapter.admin_revoke — user-2이 관리자 경로로 user-1의 세션을 회수

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-search-every-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

권한 받은 사용자가 세션 전체 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 세션을 가진 사용자 하나, 부르는 사람은 도메인 스코프에서 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginSessionAdapter.admin_search — user-2이 세션 전체를 훑음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-unblock-a-user](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

권한 받은 사용자가 차단을 풀려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 세션을 가진 사용자 하나, 부르는 사람은 도메인 스코프에서 사용자 UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- LoginSessionAdapter.admin_unblock_user — user-2이 user-1의 차단을 풂

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

슈퍼관리자가 없는 세션 id를 주면, 입력 검증이 막는다

Given

- 도메인 하나와 슈퍼관리자, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.admin_revoke — user-2이 관리자 경로로 없는 세션을 회수

Then

- 거부된다
  - 거부: LoginSessionNotFoundError

#### [the-superadmin-revokes-another-users-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

전역 역할이 문인 관리자 회수에서 슈퍼관리자가 다른 사용자의 세션을 회수하면, 성공이 오고 세션 전체 검색에서 빠지며 관리자가 회수했다는 이력이 생긴다

Given

- 도메인 하나와 슈퍼관리자, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.admin_revoke — user-2이 관리자 경로로 user-1의 세션을 회수

Then

- 회수가 성공하고 뒤이은 조회에 세션이 없다
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
  - after.has_next_page = False
  - after.has_previous_page = False

#### [the-superadmin-searches-every-users-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

전역 역할이 문인 세션 검색에서 슈퍼관리자가 페이지 인자 없이 훑으면, 사용자와 무관하게 심은 세션이 생성 시각 내림차순으로 온다

Given

- 도메인 하나와 슈퍼관리자, 세션을 하나씩 가진 사용자 둘
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다
  - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-2: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.admin_search — user-3이 세션 전체를 훑음

Then

- 심은 세션이 모두 순서대로 온다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 심은 세션와 같다
  - items[0].user_id: 세션의 주인와 같다
  - items[0].access_key: 세션을 연 키와 같다
  - items[0].status = 'active'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None
  - items[1].id: 심은 세션와 같다
  - items[1].user_id: 세션의 주인와 같다
  - items[1].access_key: 세션을 연 키와 같다
  - items[1].status = 'active'
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].last_accessed_at = None
  - items[1].invalidated_at = None

#### [the-superadmin-unblocks-a-user](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

전역 역할이 문인 차단 해제에서 슈퍼관리자가 사용자 이름을 주면, 성공이 오고 그 이름의 차단 기록이 사라진다

Given

- 도메인 하나와 슈퍼관리자, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.admin_unblock_user — user-2이 user-1의 차단을 풂

Then

- 차단 해제가 성공한다
  - success = True

#### [unblocking-a-username-nobody-holds-still-succeeds](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py) — pass

슈퍼관리자가 어떤 사용자도 아닌 이름을 주면, 존재를 확인하지 않고 성공이 온다

Given

- 도메인 하나와 슈퍼관리자, 세션 하나를 가진 사용자 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 활성 로그인 세션 하나를 갖는다

When

- LoginSessionAdapter.admin_unblock_user — user-2이 없는 이름의 차단을 풂

Then

- 차단 해제가 성공한다
  - success = True

### managing_keypairs

#### [a-granted-user-changing-another-users-rate-limit-changes-only-that](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

대상 스코프에서 READ와 UPDATE를 받은 사용자가 요청 한도만 주면, 나머지는 그대로이고 한도만 바뀐 키 노드가 온다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 대상에 대한 사용자 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_update_keypair — user-2이 user-1의 키에 요청 한도를 줌

Then

- 요청 한도만 바뀐 키 전체가 온다
  - id: 심은 키와 같다
  - access_key: 심은 키와 같다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 45000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키의 주인와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-granted-user-clearing-another-users-ssh-key-empties-the-public-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

대상 스코프에서 READ와 UPDATE를 받은 사용자가 지우면, access key가 오고 공개키가 비워진다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_ssh_keypair — user-2이 user-1의 기본 키에서 SSH 키를 지우고 읽음

Then

- 대상 기본 키가 오고, 뒤이은 읽기에서 공개키가 바뀌어 있다
  - access_key: 대상의 기본 키와 같다
  - 뒤이은 읽기의 ssh_public_key = None

#### [a-granted-user-deleting-another-users-extra-key-gets-its-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

대상 스코프에서 READ와 UPDATE를 받은 사용자가 지우면, 지운 키의 access key가 답으로 온다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 대상에 대한 사용자 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_keypair — user-2이 user-1의 기본 아닌 키를 지움

Then

- 지운 키의 access key가 온다
  - access_key: 심은 키와 같다

#### [a-granted-user-reads-another-users-key-by-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

대상 스코프에서 READ를 받은 사용자가 읽으면, 그 키 노드 전체가 온다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 대상에 대한 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_get_keypair — user-2이 user-1의 키를 access key로 읽음

Then

- 심은 키 전체가 온다
  - id: 심은 키와 같다
  - access_key: 심은 키와 같다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키의 주인와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-granted-user-reads-another-users-ssh-public-key-only](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

대상 스코프에서 READ를 받은 사용자가 읽으면, access key와 공개키만 오고 개인키는 오지 않는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_get_ssh_keypair — user-2이 user-1의 SSH 공개키를 읽음

Then

- access key와 공개키만 온다
  - keypair.access_key: 대상의 기본 키와 같다
  - keypair.ssh_public_key = ''

#### [a-granted-user-registering-another-users-ssh-key-gets-the-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

대상 스코프에서 READ와 UPDATE를 받은 사용자가 공개키와 개인키를 주면, 형식 검사 없이 덮어쓰고 access key가 답으로 온다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_register_ssh_keypair — user-2이 user-1의 기본 키에 SSH 키를 등록하고 읽음

Then

- 대상 기본 키가 오고, 뒤이은 읽기에서 공개키가 바뀌어 있다
  - access_key: 대상의 기본 키와 같다
  - 뒤이은 읽기의 ssh_public_key = 'ssh-rsa scenario-public-key'

#### [a-key-may-not-be-made-under-a-policy-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_create_keypair — user-2이 user-1에게 없는 정책으로 키를 만듦

Then

- 거부된다
  - 거부: KeypairResourcePolicyNotFound

#### [a-user-granted-nothing-may-not-change-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 바꾸려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.admin_update_keypair — user-2이 user-1의 키에 요청 한도를 줌

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-clear-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 지우려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_delete_ssh_keypair — user-2이 user-1의 기본 키에서 SSH 키를 지우고 읽음

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-delete-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 지우려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.admin_delete_keypair — user-2이 user-1의 기본 아닌 키를 지움

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-make-a-key-for-another](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 키를 만들려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_create_keypair — user-2이 user-1에게 granted-policy-1으로 키를 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-read-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 읽으려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.admin_get_keypair — user-2이 user-1의 키를 access key로 읽음

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-read-another-users-ssh-public-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 읽으려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_get_ssh_keypair — user-2이 user-1의 SSH 공개키를 읽음

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-register-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

역할 없이 등록하려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지

When

- UserAdapter.admin_register_ssh_keypair — user-2이 user-1의 기본 키에 SSH 키를 등록하고 읽음

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-only-read-may-not-change-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

READ만 받고 바꾸려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 대상에 대한 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_update_keypair — user-2이 user-1의 키에 요청 한도를 줌

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-only-read-may-not-clear-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

READ만 받고 지우려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_ssh_keypair — user-2이 user-1의 기본 키에서 SSH 키를 지우고 읽음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-only-read-may-not-delete-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

READ만 받고 지우려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 대상에 대한 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_keypair — user-2이 user-1의 기본 아닌 키를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-only-read-may-not-register-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

READ만 받고 등록하려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_register_ssh_keypair — user-2이 user-1의 기본 키에 SSH 키를 등록하고 읽음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

슈퍼관리자가 아니어도 대상 사용자 스코프에서 UPDATE를 받은 사용자가 정책을 주고 키를 만들면, 기본 아닌 새 키와 secret이 온다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_create_keypair — user-2이 user-1에게 granted-policy-1으로 키를 만듦

Then

- 만든 키 전체와 secret이 온다
  - id: 무시함 — 매니저가 만든 access key다
  - access_key: 무시함 — 매니저가 만든다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 30000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key: 무시함 — 매니저가 만든 RSA 키다
  - num_queries = 0
  - last_used = None
  - user_id: 키의 주인와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - secret_key: 무시함 — 매니저가 만든다

#### [a-user-who-is-not-the-superadmin-may-not-search-every-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

권한 받은 사용자가 키 전체 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.admin_search_keypairs — user-1이 페이지 인자 없이 모든 키를 훑음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

권한 받은 사용자가 GQL 키 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와, 그 도메인 스코프에서 사용자 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.gql_admin_search_keypairs — user-1이 GQL로 모든 키를 훑음

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [another-users-default-key-may-not-be-deleted](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

권한 받은 사용자가 대상의 기본 키를 지우려 하면, 입력 검증이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 부르는 사람은 대상에 대한 사용자 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_delete_keypair — user-2이 user-1의 기본 키를 지움

Then

- 거부된다
  - 거부: KeyPairForbidden

#### [another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막는다

Given

- 도메인 하나와 대상 사용자, 부르는 사용자, 대상에게 기본 아닌 키 하나, 부르는 사람은 대상에 대한 사용자 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 granted-policy-1: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.admin_update_keypair — user-2이 user-1의 키에 요청 한도와 없는 정책를 줌

Then

- 거부된다
  - 거부: KeypairResourcePolicyNotFound

#### [the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

전역 역할이 문인 GQL 키 검색에서 슈퍼관리자가 정책 이름을 주면, 그 정책을 쓰는 키만 온다

Given

- 도메인 하나와 사용자 둘, 슈퍼관리자 한 명, 저마다 다른 키페어 정책
  - 도메인 home-1
  - 자기 키페어 정책을 가진 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.gql_admin_search_keypairs — user-3이 keypair-policy-1으로 걸러 GQL 키 검색

Then

- 그 정책을 쓰는 키 하나만 온다
  - items.length = 1
  - items[0].id: 무시함 — 시드가 만든 난수 키다
  - items[0].access_key: 무시함 — 시드가 만든 난수 키다
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = ''
  - items[0].num_queries = 0
  - items[0].last_used = None
  - items[0].user_id: 키의 주인와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].modified_at: 이 실행이 쓴 시각
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [the-superadmin-searching-every-key-gets-every-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py) — pass

전역 역할이 문인 키 검색에서 슈퍼관리자가 페이지 인자 없이 훑으면, 모든 사용자의 키가 오고 limit 자리는 비어서 온다

Given

- 도메인 하나와 사용자 둘, 슈퍼관리자 한 명, 저마다 다른 키페어 정책
  - 도메인 home-1
  - 자기 키페어 정책을 가진 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.admin_search_keypairs — user-3이 페이지 인자 없이 모든 키를 훑음

Then

- 모든 사용자의 키가 주인 순으로 온다
  - items.length = 3
  - items[0].id: 무시함 — 시드가 만든 난수 키다
  - items[0].access_key: 무시함 — 시드가 만든 난수 키다
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = ''
  - items[0].num_queries = 0
  - items[0].last_used = None
  - items[0].user_id: 키의 주인와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].modified_at: 이 실행이 쓴 시각
  - items[1].id: 무시함 — 시드가 만든 난수 키다
  - items[1].access_key: 무시함 — 시드가 만든 난수 키다
  - items[1].is_active = True
  - items[1].is_admin = False
  - items[1].is_default = True
  - items[1].rate_limit = 10000
  - items[1].resource_policy = 'keypair-policy-2'
  - items[1].ssh_public_key = ''
  - items[1].num_queries = 0
  - items[1].last_used = None
  - items[1].user_id: 키의 주인와 같다
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].modified_at: 이 실행이 쓴 시각
  - items[2].id: 무시함 — 시드가 만든 난수 키다
  - items[2].access_key: 무시함 — 시드가 만든 난수 키다
  - items[2].is_active = True
  - items[2].is_admin = True
  - items[2].is_default = True
  - items[2].rate_limit = 10000
  - items[2].resource_policy = 'keypair-policy-3'
  - items[2].ssh_public_key = ''
  - items[2].num_queries = 0
  - items[2].last_used = None
  - items[2].user_id: 키의 주인와 같다
  - items[2].created_at: 이 실행이 쓴 시각
  - items[2].modified_at: 이 실행이 쓴 시각
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = None

### own_keypairs

#### [a-user-granted-nothing-may-not-issue-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

역할을 받지 않은 사용자가 자기 키를 발급하려 하면, 본인이어도 엔티티 권한 문이 막는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.issue_my_keypair — user-1이 자기 키를 발급

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-move-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

역할 없이 기본 키를 옮기려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.switch_default_access_key — user-1이 기본 아닌 자기 키로 기본 키를 옮김

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-revoke-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

역할을 받지 않은 사용자가 회수하려 하면, 소유자 조회 단계가 없는 키와 같은 예외로 막는다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.revoke_my_keypair — user-1이 기본 아닌 자기 키를 회수하고 자기 키를 다시 훑음

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-nothing-may-not-search-their-own-keys](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

역할 없이 자기 키를 훑으려 하면, 스코프 권한 문이 막는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.search_my_keypairs — user-1이 페이지 인자 없이 자기 키를 훑음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-turn-off-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

역할 없이 키를 끄려 하면, 소유자 조회 단계가 막는다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 아무 권한도 받지 않았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다

When

- UserAdapter.update_my_keypair — user-1이 기본 아닌 자기 키를 비활성으로 바꿈

Then

- 거부된다
  - 거부: GenericBadRequest

#### [a-user-granted-only-read-may-not-revoke-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

자기 스코프에서 READ만 받은 사용자가 회수하려 하면, 소유자 조회는 지나고 엔티티 권한 문이 막는다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair — user-1이 기본 아닌 자기 키를 회수하고 자기 키를 다시 훑음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-only-read-may-not-turn-off-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

READ만 받고 키를 끄려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_my_keypair — user-1이 기본 아닌 자기 키를 비활성으로 바꿈

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-and-update-moves-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

자기 스코프에서 UPDATE를 받은 사용자가 기본 아닌 활성 키로 기본 키를 옮기면, 성공이 오고 사용자 노드의 기본 키가 그 키가 된다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.switch_default_access_key — user-1이 기본 아닌 자기 키로 기본 키를 옮기고 자기 사용자를 다시 읽음

Then

- 전환에 성공하고, 뒤이은 읽기에서 기본 키가 추가한 키다
  - success = True
  - node.id: 심은 사용자와 같다
  - node.basic_info.username = 'user-1'
  - node.basic_info.email = 'user-1@scenario.local'
  - node.basic_info.full_name = None
  - node.basic_info.description = None
  - node.basic_info.integration_name = None
  - node.status.status = 'active'
  - node.status.status_info = None
  - node.status.need_password_change = False
  - node.organization.domain_name = 'home-1'
  - node.organization.role = 'user'
  - node.organization.resource_policy = 'user-policy-1'
  - node.organization.main_access_key: 추가한 키와 같다
  - node.security.allowed_client_ip = None
  - node.security.totp_activated = False
  - node.security.totp_activated_at = None
  - node.security.sudo_session_enabled = False
  - node.container.container_uid = None
  - node.container.container_main_gid = None
  - node.container.container_gids = None
  - node.timestamps.created_at: 이 실행이 쓴 시각
  - node.timestamps.modified_at: 이 실행이 쓴 시각

#### [a-user-granted-read-and-update-revokes-a-non-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 자기의 기본 아닌 키를 회수하면, 성공이 오고 자기 키 검색에서 그 키가 빠진다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair — user-1이 기본 아닌 자기 키를 회수하고 자기 키를 다시 훑음

Then

- 회수에 성공하고, 뒤이은 자기 키 검색에 기본 키만 남는다
  - success = True
  - after.total_count = 1
  - after.has_next_page = False
  - after.has_previous_page = False
  - after.items.length = 1
  - after.items[0].id: 무시함 — 시드가 매번 새로 만든 access key다
  - after.items[0].access_key: 무시함 — 시드가 매번 새로 만든다
  - after.items[0].is_active = True
  - after.items[0].is_admin = False
  - after.items[0].is_default = True
  - after.items[0].rate_limit = 10000
  - after.items[0].resource_policy = 'keypair-policy-1'
  - after.items[0].ssh_public_key = ''
  - after.items[0].num_queries = 0
  - after.items[0].last_used = None
  - after.items[0].user_id: 키의 주인와 같다
  - after.items[0].created_at: 이 실행이 쓴 시각
  - after.items[0].modified_at: 이 실행이 쓴 시각

#### [a-user-granted-read-and-update-turns-off-a-non-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

자기 스코프에서 READ와 UPDATE를 받은 사용자가 기본 아닌 키를 비활성으로 바꾸면, 활성만 바뀐 키 노드가 온다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_my_keypair — user-1이 기본 아닌 자기 키를 비활성으로 바꿈

Then

- 활성만 바뀐 키 노드 전체가 온다
  - id: 심은 키와 같다
  - access_key: 심은 키와 같다
  - is_active = False
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: 키의 주인와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-user-granted-read-searching-their-keys-sees-only-their-own](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

자기 스코프에서 READ를 받은 사용자가 자기 키를 훑으면, 다른 사용자의 키는 빠진다

Given

- 도메인 하나와 기본 아닌 키 1개를 가진 사용자 한 명, 기본 아닌 키를 가진 다른 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.search_my_keypairs — user-1이 페이지 인자 없이 자기 키를 훑음

Then

- 자기 키 둘만 온다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.is_default(기본 아닌 키 먼저) = [False, True]
  - items[추가한 키].id: 심은 키와 같다
  - items[추가한 키].access_key: 심은 키와 같다
  - items[추가한 키].is_active = True
  - items[추가한 키].is_admin = False
  - items[추가한 키].is_default = False
  - items[추가한 키].rate_limit = 10000
  - items[추가한 키].resource_policy = 'keypair-policy-1'
  - items[추가한 키].ssh_public_key = ''
  - items[추가한 키].num_queries = 0
  - items[추가한 키].last_used = None
  - items[추가한 키].user_id: 키의 주인와 같다
  - items[추가한 키].created_at: 이 실행이 쓴 시각
  - items[추가한 키].modified_at: 이 실행이 쓴 시각
  - items[기본 키].id: 무시함 — 시드가 매번 새로 만든 access key다
  - items[기본 키].access_key: 무시함 — 시드가 매번 새로 만든다
  - items[기본 키].is_active = True
  - items[기본 키].is_admin = False
  - items[기본 키].is_default = True
  - items[기본 키].rate_limit = 10000
  - items[기본 키].resource_policy = 'keypair-policy-1'
  - items[기본 키].ssh_public_key = ''
  - items[기본 키].num_queries = 0
  - items[기본 키].last_used = None
  - items[기본 키].user_id: 키의 주인와 같다
  - items[기본 키].created_at: 이 실행이 쓴 시각
  - items[기본 키].modified_at: 이 실행이 쓴 시각

#### [a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

자기 사용자 스코프에서 UPDATE를 받은 사용자가 발급하면, 기본 키의 관리자 표시, 정책, 요청 한도를 따르고 기본 표시는 없는 키와 secret이 온다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.issue_my_keypair — user-1이 자기 키를 발급

Then

- 기본 키를 따르는 기본 아닌 새 키와 secret이 온다
  - id: 무시함 — 매니저가 만든 access key다
  - access_key: 무시함 — 매니저가 만든다
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-1'
  - ssh_public_key: 무시함 — 매니저가 만든 RSA 키다
  - num_queries = 0
  - last_used = None
  - user_id: 키의 주인와 같다
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - secret_key: 무시함 — 매번 새로 만든다

#### [an-access-key-nobody-holds-may-not-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 어떤 키도 아닌 값을 주면, 소유자 조회 단계가 권한 없음과 같은 예외로 막는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair — user-1이 어떤 키도 아닌 값으로 회수

Then

- 거부된다
  - 거부: GenericBadRequest

#### [an-issued-key-made-default-lets-the-original-default-key-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 키를 발급하고 그 키로 기본 키를 옮긴 다음 원래 기본 키를 회수하면, 세 호출이 차례로 통과하고 발급한 키 하나만 남는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.issue_my_keypair — user-1이 자기 키 검색으로 기본 키를 찾고, 키를 발급해 그 키로 기본 키를 옮긴 다음 원래 기본 키를 회수하고 자기 키를 다시 훑음

Then

- 세 호출이 통과하고 발급한 키 하나만 남는다
  - issued.id: 무시함 — 매니저가 만든 access key다
  - issued.access_key: 무시함 — 매니저가 만든다
  - issued.is_active = True
  - issued.is_admin = False
  - issued.is_default = False
  - issued.rate_limit = 10000
  - issued.resource_policy = 'keypair-policy-1'
  - issued.ssh_public_key: 무시함 — 매니저가 만든 RSA 키다
  - issued.num_queries = 0
  - issued.last_used = None
  - issued.user_id: 키의 주인와 같다
  - issued.created_at: 이 실행이 쓴 시각
  - issued.modified_at: 이 실행이 쓴 시각
  - issued.secret_key: 무시함 — 매번 새로 만든다
  - switched = True
  - revoked = True
  - after.total_count = 1
  - after.has_next_page = False
  - after.has_previous_page = False
  - after.items.access_key: 발급한 키와 같다
  - after.items[0].is_active = True
  - after.items[0].is_admin = False
  - after.items[0].is_default = True
  - after.items[0].rate_limit = 10000
  - after.items[0].resource_policy = 'keypair-policy-1'
  - after.items[0].ssh_public_key: 무시함 — 매니저가 만든 RSA 키다
  - after.items[0].num_queries = 0
  - after.items[0].last_used = None
  - after.items[0].user_id: 키의 주인와 같다
  - after.items[0].created_at: 이 실행이 쓴 시각
  - after.items[0].modified_at: 이 실행이 쓴 시각

#### [searching-own-keys-without-page-arguments-answers-the-ten-newest](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 페이지 인자 없이 훑으면, 생성 시각 내림차순 열 개와 다음 페이지 여부가 온다

Given

- 도메인 하나와 기본 아닌 키 10개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.search_my_keypairs — user-1이 페이지 인자 없이 자기 키를 훑음

Then

- 자기 키 열한 개 중 열 개가 최근순으로 오고 다음 페이지가 있다
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False
  - items.length = 10
  - items(created_at, access_key): 생성 시각 내림차순, 같은 시각이면 access key 오름차순
  - items.user_id: 모두 부른 사람와 같다
  - items.created_at: 이 실행이 쓴 시각
  - items의 나머지 자리: 무시함 — 순서와 개수를 보는 행이다. 키 노드 전체는 다른 행이 본다

#### [someone-elses-key-may-not-become-the-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 다른 사용자의 키를 주면, 입력 검증이 막는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 기본 아닌 키를 가진 다른 사용자 한 명, 그 사용자는 자기 사용자에 UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-2: 기본이 아닌 활성 키 하나를 더 갖는다
  - 사용자 UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.switch_default_access_key — user-1이 다른 사용자의 키로 기본 키를 옮김

Then

- 거부된다
  - 거부: KeyPairForbidden

#### [the-default-key-may-not-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 자기 기본 키를 회수하려 하면, 입력 검증이 막는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.revoke_my_keypair — user-1이 자기 키 검색으로 기본 키를 찾아 그 키를 회수

Then

- 거부된다
  - 거부: KeyPairForbidden

#### [the-default-key-may-not-be-turned-off](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py) — pass

권한 받은 사용자가 자기 기본 키를 비활성으로 바꾸려 하면, 입력 검증이 막는다

Given

- 도메인 하나와 기본 아닌 키 0개를 가진 사용자 한 명, 그 사용자는 자기 사용자에 READ, UPDATE 권한을 받았다
  - 도메인 home-1
  - 키 정책을 아는 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ, UPDATE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_my_keypair — user-1이 자기 키 검색으로 기본 키를 찾아 비활성으로 바꿈

Then

- 거부된다
  - 거부: KeyPairForbidden

### reading

#### [a-batch-load-answers-a-node-or-a-refusal-for-each-id-in-order](/tests/scenario/bai_scenario/manager/user/test_reading.py) — pass

한 사용자에게만 읽기 권한을 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, 없는 id를 한 번에 요청하면, 입력 순서대로 원소별 결과가 온다

Given

- 도메인 하나와 사용자 셋, 부르는 사람은 한 사람에 대한 사용자 읽기 권한만 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.batch_load_by_ids — user-3이 user-1, user-2, 없는 id 순으로 일괄 읽음

Then

- 원소마다 결과가 입력 순서대로 온다
  - length = 3
  - [0].id: 심은 사용자와 같다
  - [0].basic_info.username = 'user-1'
  - [0].basic_info.email = 'user-1@scenario.local'
  - [0].basic_info.full_name = None
  - [0].basic_info.description = None
  - [0].basic_info.integration_name = None
  - [0].status.status = 'active'
  - [0].status.status_info = None
  - [0].status.need_password_change = False
  - [0].organization.domain_name = 'home-1'
  - [0].organization.role = 'user'
  - [0].organization.resource_policy = 'user-policy-1'
  - [0].organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - [0].security.allowed_client_ip = None
  - [0].security.totp_activated = False
  - [0].security.totp_activated_at = None
  - [0].security.sudo_session_enabled = False
  - [0].container.container_uid = None
  - [0].container.container_main_gid = None
  - [0].container.container_gids = None
  - [0].timestamps.created_at: 이 실행이 쓴 시각
  - [0].timestamps.modified_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/user/test_reading.py) — pass

권한 없는 사용자가 빈 id 목록을 주면, 어떤 액션도 부르지 않고 빈 목록이 답으로 온다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.batch_load_by_ids — user-2이 빈 목록으로 일괄 읽음

Then

- 빈 목록이 온다
  - loaded = []

#### [a-user-granted-nothing-may-not-read-another-user](/tests/scenario/bai_scenario/manager/user/test_reading.py) — pass

아무 역할도 받지 않은 사용자가 다른 사용자를 읽으려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.get — user-2이 user-1을 읽음

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-read-on-another-user-reads-their-whole-node](/tests/scenario/bai_scenario/manager/user/test_reading.py) — pass

대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 읽으면, 기본 키까지 채운 노드 전체가 답으로 온다

Given

- 도메인 하나와 사용자 둘, 한 사람은 다른 사람에 대한 사용자 읽기 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.get — user-2이 user-1을 읽음

Then

- 읽힌 사용자 전체가 온다
  - id: 심은 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: 이 실행이 쓴 시각
  - timestamps.modified_at: 이 실행이 쓴 시각

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/user/test_reading.py) — pass

슈퍼관리자가 있는 id와 없는 id를 함께 요청하면, 권한 문을 지나 없는 원소 자리에 빈 값이 온다

Given

- 도메인 하나와 사용자 둘, 아무도 권한을 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.batch_load_by_ids — user-2이 user-1과 없는 id를 일괄 읽음

Then

- 있는 사람은 노드, 없는 id 자리는 비어서 온다
  - length = 2
  - [0].id: 심은 사용자와 같다
  - [0].basic_info.username = 'user-1'
  - [0].basic_info.email = 'user-1@scenario.local'
  - [0].basic_info.full_name = None
  - [0].basic_info.description = None
  - [0].basic_info.integration_name = None
  - [0].status.status = 'active'
  - [0].status.status_info = None
  - [0].status.need_password_change = False
  - [0].organization.domain_name = 'home-1'
  - [0].organization.role = 'user'
  - [0].organization.resource_policy = 'user-policy-1'
  - [0].organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - [0].security.allowed_client_ip = None
  - [0].security.totp_activated = False
  - [0].security.totp_activated_at = None
  - [0].security.sudo_session_enabled = False
  - [0].container.container_uid = None
  - [0].container.container_main_gid = None
  - [0].container.container_gids = None
  - [0].timestamps.created_at: 이 실행이 쓴 시각
  - [0].timestamps.modified_at: 이 실행이 쓴 시각
  - [1] = None

### retiring

#### [a-bulk-purge-records-a-missing-id-as-a-failure](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

슈퍼관리자가 있는 사용자와 없는 id를 함께 주면, 하나는 지워지고 없는 id는 실패로 담긴다

Given

- 도메인 하나와 슈퍼관리자 하나, 사용자 1명, 그리고 어떤 사용자도 아닌 id 하나
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.bulk_purge_users — user-2이 user-1와 없는 id를 일괄로 지움

Then

- 지운 사용자 id와 개수, 그리고 실패가 온다
  - successes: 심은 사용자 전부와 같다
  - purged_count = 1
  - failed.user_id: 없는 id와 같다
  - failed.message: 무시함 — 예외 문장은 바뀌어도 되는 값이다

#### [a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

대상 사용자 스코프에서 HARD_DELETE를 받은 사용자가 물리지 않은 사용자를 지워도, 성공이 오고 그 사용자를 더 찾을 수 없다

Given

- 도메인 하나와 대상 사용자 하나, 부르는 사람 하나, 부르는 사람은 대상에 대한 사용자 HARD_DELETE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 HARD_DELETE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.purge_user_by_id — user-2이 자기에게 넘기며 user-1을 지움, 뒤이어 user-3이 일괄 읽음

Then

- 성공이 오고, 그 사용자를 더 찾을 수 없다
  - success = True
  - 뒤이은 일괄 읽기 = [None]

#### [a-user-granted-nothing-may-not-delete-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

역할 없이 물리려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자 하나, 부르는 사람 하나, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.delete_user_by_id — user-2이 user-1을 물림

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-purge-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

역할 없이 지우려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 사용자 하나, 부르는 사람 하나, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.purge_user_by_id — user-2이 자기에게 넘기며 user-1을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-restore-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

역할 없이 되살리려 하면, 엔티티 권한 문이 막는다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 부르는 사람 하나, 부르는 사람은 아무 권한도 받지 않았다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.restore_user_by_id — user-2이 user-1을 되살림

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-soft-delete-marks-another-user-deleted](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

대상 사용자 스코프에서 SOFT_DELETE를 받은 사용자가 물리면, 성공이 오고 그 사용자 상태가 삭제로 바뀐다

Given

- 도메인 하나와 대상 사용자 하나, 부르는 사람 하나, 부르는 사람은 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 SOFT_DELETE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.delete_user_by_id — user-2이 user-1을 물림 뒤 다시 읽음

Then

- 성공이 오고, 다시 읽은 사용자는 deleted 상태다
  - success = True
  - 뒤이은 읽기.id: 심은 사용자와 같다
  - 뒤이은 읽기.basic_info.username = 'user-1'
  - 뒤이은 읽기.basic_info.email = 'user-1@scenario.local'
  - 뒤이은 읽기.basic_info.full_name = None
  - 뒤이은 읽기.basic_info.description = None
  - 뒤이은 읽기.basic_info.integration_name = None
  - 뒤이은 읽기.status.status = 'deleted'
  - 뒤이은 읽기.status.status_info = 'admin-requested'
  - 뒤이은 읽기.status.need_password_change = False
  - 뒤이은 읽기.organization.domain_name = 'home-1'
  - 뒤이은 읽기.organization.role = 'user'
  - 뒤이은 읽기.organization.resource_policy = 'user-policy-1'
  - 뒤이은 읽기.organization.main_access_key: 그 사용자의 기본 키가 채워져 있다
  - 뒤이은 읽기.security.allowed_client_ip = None
  - 뒤이은 읽기.security.totp_activated = False
  - 뒤이은 읽기.security.totp_activated_at = None
  - 뒤이은 읽기.security.sudo_session_enabled = False
  - 뒤이은 읽기.container.container_uid = None
  - 뒤이은 읽기.container.container_main_gid = None
  - 뒤이은 읽기.container.container_gids = None
  - 뒤이은 읽기.timestamps.created_at: 이 실행이 쓴 시각
  - 뒤이은 읽기.timestamps.modified_at: 이 실행이 쓴 시각

#### [a-user-granted-soft-delete-restores-a-deleted-user-to-active](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

대상 사용자 스코프에서 SOFT_DELETE를 받은 사용자가 삭제 상태 사용자를 되살리면, 성공이 오고 상태가 활성으로 바뀐다

Given

- 도메인 하나와 대상 deleted 상태 사용자 하나, 부르는 사람 하나, 부르는 사람은 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 deleted 상태 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 deleted, 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 SOFT_DELETE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.restore_user_by_id — user-2이 user-1을 되살림 뒤 다시 읽음

Then

- 성공이 오고, 다시 읽은 사용자는 active 상태다
  - success = True
  - 뒤이은 읽기.id: 심은 사용자와 같다
  - 뒤이은 읽기.basic_info.username = 'user-1'
  - 뒤이은 읽기.basic_info.email = 'user-1@scenario.local'
  - 뒤이은 읽기.basic_info.full_name = None
  - 뒤이은 읽기.basic_info.description = None
  - 뒤이은 읽기.basic_info.integration_name = None
  - 뒤이은 읽기.status.status = 'active'
  - 뒤이은 읽기.status.status_info = 'admin-requested'
  - 뒤이은 읽기.status.need_password_change = False
  - 뒤이은 읽기.organization.domain_name = 'home-1'
  - 뒤이은 읽기.organization.role = 'user'
  - 뒤이은 읽기.organization.resource_policy = 'user-policy-1'
  - 뒤이은 읽기.organization.main_access_key: 활성 기본 키가 없어 비어 있다
  - 뒤이은 읽기.security.allowed_client_ip = None
  - 뒤이은 읽기.security.totp_activated = False
  - 뒤이은 읽기.security.totp_activated_at = None
  - 뒤이은 읽기.security.sudo_session_enabled = False
  - 뒤이은 읽기.container.container_uid = None
  - 뒤이은 읽기.container.container_main_gid = None
  - 뒤이은 읽기.container.container_gids = None
  - 뒤이은 읽기.timestamps.created_at: 이 실행이 쓴 시각
  - 뒤이은 읽기.timestamps.modified_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-purge-in-bulk](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

도메인 스코프에서 HARD_DELETE를 받은 사용자라도 일괄 지우기를 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 사용자 하나, 부르는 사람은 도메인 스코프의 사용자 HARD_DELETE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 HARD_DELETE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.bulk_purge_users — user-2이 user-1를 일괄로 지움

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [purging-a-user-to-an-admin-who-does-not-exist-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

권한 받은 사용자가 넘겨받을 관리자로 없는 id를 주면, 입력 검증이 막는다

Given

- 도메인 하나와 대상 사용자 하나, 부르는 사람 하나, 부르는 사람은 대상에 대한 사용자 HARD_DELETE 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 HARD_DELETE 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 HARD_DELETE 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.purge_user_by_id — user-2이 없는 관리자 id에게 넘기며 user-1을 지움

Then

- 거부된다
  - 거부: UserNotFound

#### [restoring-a-user-who-was-never-deleted-still-makes-them-active](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

권한 받은 사용자가 비활성 사용자를 되살리면, 현재 상태와 무관하게 활성이 된다

Given

- 도메인 하나와 대상 inactive 상태 사용자 하나, 부르는 사람 하나, 부르는 사람은 대상에 대한 사용자 SOFT_DELETE, READ 권한을 받았다
  - 도메인 home-1
  - 도메인에 속한 inactive 상태 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 상태 inactive, 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 SOFT_DELETE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 SOFT_DELETE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.restore_user_by_id — user-2이 user-1을 되살림 뒤 다시 읽음

Then

- 성공이 오고, 다시 읽은 사용자는 active 상태다
  - success = True
  - 뒤이은 읽기.id: 심은 사용자와 같다
  - 뒤이은 읽기.basic_info.username = 'user-1'
  - 뒤이은 읽기.basic_info.email = 'user-1@scenario.local'
  - 뒤이은 읽기.basic_info.full_name = None
  - 뒤이은 읽기.basic_info.description = None
  - 뒤이은 읽기.basic_info.integration_name = None
  - 뒤이은 읽기.status.status = 'active'
  - 뒤이은 읽기.status.status_info = 'admin-requested'
  - 뒤이은 읽기.status.need_password_change = False
  - 뒤이은 읽기.organization.domain_name = 'home-1'
  - 뒤이은 읽기.organization.role = 'user'
  - 뒤이은 읽기.organization.resource_policy = 'user-policy-1'
  - 뒤이은 읽기.organization.main_access_key: 활성 기본 키가 없어 비어 있다
  - 뒤이은 읽기.security.allowed_client_ip = None
  - 뒤이은 읽기.security.totp_activated = False
  - 뒤이은 읽기.security.totp_activated_at = None
  - 뒤이은 읽기.security.sudo_session_enabled = False
  - 뒤이은 읽기.container.container_uid = None
  - 뒤이은 읽기.container.container_main_gid = None
  - 뒤이은 읽기.container.container_gids = None
  - 뒤이은 읽기.timestamps.created_at: 이 실행이 쓴 시각
  - 뒤이은 읽기.timestamps.modified_at: 이 실행이 쓴 시각

#### [the-superadmin-bulk-purge-answers-the-purged-ids-and-count](/tests/scenario/bai_scenario/manager/user/test_retiring.py) — pass

전역 역할이 문인 일괄 지우기에서 슈퍼관리자가 사용자 둘을 주면, 두 id와 개수 둘이 온다

Given

- 도메인 하나와 슈퍼관리자 하나, 사용자 2명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.bulk_purge_users — user-3이 user-1, user-2를 일괄로 지움

Then

- 지운 사용자 id와 개수, 그리고 실패가 온다
  - successes: 심은 사용자 전부와 같다
  - purged_count = 2
  - failed = []

### searching

#### [a-gql-scoped-search-over-two-granted-scopes-joins-their-users](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

같은 권한으로 GQL 스코프 검색을 하면, 두 스코프 사용자가 커서 답으로 온다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나, 부르는 사람은 첫 도메인 스코프와 그 프로젝트 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 프로젝트 research-1 명부에 오름
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
    - 역할 user-role-2: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-2: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-2 보유

When

- UserAdapter.gql_scoped_search — user-2이 home-1과 research-1 두 스코프로 GQL 조회

Then

- 닿는 사용자가 모두 한 페이지로 온다
  - items(이름순) = ['user-1', 'user-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-gql-search-without-page-arguments-answers-the-newest-ten](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

슈퍼관리자가 커서와 페이지 인자를 모두 생략하고 훑으면, 생성 시각 내림차순으로 열 명까지 오고 다음 페이지 여부가 함께 온다

Given

- 도메인 하나와 사용자 11명, 그리고 슈퍼관리자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-4: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-4: 동시 세션 5개까지
    - 일반 사용자 user-4: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-5: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-5: 동시 세션 5개까지
    - 일반 사용자 user-5: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-6: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-6: 동시 세션 5개까지
    - 일반 사용자 user-6: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-7: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-7: 동시 세션 5개까지
    - 일반 사용자 user-7: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-8: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-8: 동시 세션 5개까지
    - 일반 사용자 user-8: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-9: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-9: 동시 세션 5개까지
    - 일반 사용자 user-9: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-10: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-10: 동시 세션 5개까지
    - 일반 사용자 user-10: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-11: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-11: 동시 세션 5개까지
    - 일반 사용자 user-11: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-12: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-12: 동시 세션 5개까지
    - 슈퍼관리자 user-12: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.gql_admin_search — user-12이 페이지 인자 없이 GQL 전체 조회

Then

- 심은 사용자 중 열 명이 최근순으로 오고 다음 페이지가 있다
  - items.length = 10
  - items(이름): 모두 심은 사용자 중에서 온다
  - items(생성 시각): 생성 시각 내림차순
  - total_count = 12
  - has_next_page = True
  - has_previous_page = False

#### [a-scoped-search-over-two-granted-scopes-joins-their-users](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

도메인과 프로젝트 스코프 모두에서 READ를 받은 사용자가 두 스코프를 함께 주면, 두 스코프의 사용자가 중복 없이 합쳐진다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나, 부르는 사람은 첫 도메인 스코프와 그 프로젝트 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 프로젝트 research-1 명부에 오름
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유
    - 역할 user-role-2: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-2: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-2 보유

When

- UserAdapter.scoped_search — user-2이 home-1과 research-1 두 스코프로 조회

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실린다
  - items(이름순) = ['user-1', 'user-2']
  - pagination.total = 2
  - pagination.offset = 0
  - pagination.limit = 50

#### [a-scoped-search-without-page-arguments-answers-up-to-fifty](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

권한 받은 사용자가 페이지 인자 없이 스코프 검색을 하면, limit 50 offset 0이 답에 실린다

Given

- 도메인 하나와 부르는 사람, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.scoped_search — user-1이 페이지 인자 없이 home-1 스코프로 조회

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실린다
  - items(이름순) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

#### [a-user-granted-nothing-may-not-gql-search-a-domain](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

역할 없이 GQL 도메인 검색을 하면, 스코프 권한 문이 막는다

Given

- 도메인 하나와 부르는 사람
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.gql_search_by_domain — user-1이 home-1으로 GQL 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-gql-search-a-project](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

역할 없이 GQL 프로젝트 검색을 하면, 스코프 권한 문이 막는다

Given

- 도메인 하나와 프로젝트 하나, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.gql_search_by_project — user-1이 research-1으로 GQL 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-search-a-domain-by-name](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

역할을 받지 않은 사용자가 도메인 이름으로 훑으려 하면, 스코프 권한 문이 막는다

Given

- 도메인 하나와 부르는 사람
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.domain_search — user-1이 home-1으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-search-a-project](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

역할 없이 프로젝트 검색을 하면, 스코프 권한 문이 막는다

Given

- 도메인 하나와 프로젝트 하나, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.project_search — user-1이 research-1으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

같은 권한으로 GQL 도메인 검색을 하면, 그 도메인 사용자만 커서 답으로 온다

Given

- 도메인 하나와 부르는 사람, 같은 도메인 사용자 하나와 다른 도메인 사용자 하나, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 other-1
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.gql_search_by_domain — user-3이 home-1으로 GQL 조회

Then

- 닿는 사용자가 모두 한 페이지로 온다
  - items(이름순) = ['user-1', 'user-3']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

도메인 스코프에서 사용자 READ를 받은 사용자가 도메인 이름으로 훑으면, 다른 도메인 사용자는 빠진다

Given

- 도메인 하나와 부르는 사람, 같은 도메인 사용자 하나와 다른 도메인 사용자 하나, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 other-1
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.domain_search — user-3이 home-1으로 조회

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실린다
  - items(이름순) = ['user-1', 'user-3']
  - pagination.total = 2
  - pagination.offset = 0
  - pagination.limit = 50

#### [a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

같은 권한으로 GQL 프로젝트 검색을 하면, 명부의 사용자만 커서 답으로 온다

Given

- 도메인 하나와 프로젝트 하나, 명부에 오른 사용자 하나와 오르지 않은 사용자 하나, 부르는 사람은 그 프로젝트 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 프로젝트 research-1 명부에 오름
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.gql_search_by_project — user-3이 research-1으로 GQL 조회

Then

- 닿는 사용자가 모두 한 페이지로 온다
  - items(이름순) = ['user-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-on-a-project-searching-it-finds-only-its-roster](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

프로젝트 스코프에서 사용자 READ를 받은 사용자가 그 프로젝트로 훑으면, 명부에 오른 사용자만 온다

Given

- 도메인 하나와 프로젝트 하나, 명부에 오른 사용자 하나와 오르지 않은 사용자 하나, 부르는 사람은 그 프로젝트 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 프로젝트 research-1 명부에 오름
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.project_search — user-3이 research-1으로 조회

Then

- 닿는 사용자가 모두 오고 페이지 정보가 실린다
  - items(이름순) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

#### [a-user-who-is-not-the-superadmin-may-not-gql-search-every-user](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

권한 받은 사용자가 GQL 전체 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 부르는 사람, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.gql_admin_search — user-1이 페이지 인자 없이 GQL 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-search-by-role](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

그 역할의 스코프 권한을 받은 사용자라도 역할 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 역할 holder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 일반 사용자 user-1: 역할 holder-role-1 보유
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-3: 역할 user-role-1 보유

When

- UserAdapter.role_search — user-3이 역할로 걸러 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [a-user-who-is-not-the-superadmin-may-not-search-every-user](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

도메인 스코프 권한을 받은 사용자라도 전체 검색을 하려 하면, 전역 역할 문이 막는다

Given

- 도메인 하나와 부르는 사람, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [one-scope-without-a-grant-refuses-the-whole-gql-scoped-search](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

한 스코프에만 READ를 받고 GQL 스코프 검색에 둘을 주면, 스코프 권한 문이 전체를 막는다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나, 부르는 사람은 첫 도메인 스코프의 사용자 READ만 받았다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 프로젝트 research-1 명부에 오름
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.gql_scoped_search — user-2이 home-1과 research-1 두 스코프로 GQL 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [one-scope-without-a-grant-refuses-the-whole-scoped-search](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

첫 스코프에만 READ를 받은 사용자가 두 스코프를 함께 주면, 스코프 권한 문이 전체를 막는다

Given

- 도메인 둘과 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나, 부르는 사람은 첫 도메인 스코프의 사용자 READ만 받았다
  - 도메인 home-1
  - 도메인 other-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 일반 사용자 user-1: 프로젝트 research-1 명부에 오름
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-2: 역할 user-role-1 보유

When

- UserAdapter.scoped_search — user-2이 home-1과 research-1 두 스코프로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [searching-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

권한 받은 사용자가 없는 도메인 이름으로 훑으려 하면, 스코프 검사 전에 이름 조회 단계가 대상 없음으로 막는다

Given

- 도메인 하나와 부르는 사람, 부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.domain_search — user-1이 no-such-domain으로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-searching-by-role-finds-only-its-holders](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

전역 역할이 문인 역할 검색에서 슈퍼관리자가 역할 하나를 주면, 그 역할을 배정받은 사용자만 온다

Given

- 도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 부르는 사람은 슈퍼관리자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 역할 holder-role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 일반 사용자 user-1: 역할 holder-role-1 보유

When

- UserAdapter.role_search — user-3이 역할로 걸러 조회

Then

- 역할을 받은 사람만 온다
  - items(이름순) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

#### [the-superadmin-searching-every-user-counts-deleted-ones-too](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

전역 역할이 문인 검색에서 슈퍼관리자가 필터 없이 훑으면, 삭제 상태 사용자를 포함해 심은 사용자가 모두 온다

Given

- 도메인 하나와 활성 사용자 하나, 삭제 상태 사용자 하나, 그리고 슈퍼관리자
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-3: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-3: 자기 키와 개인 프로젝트를 갖는다
  - 도메인에 속한 삭제 상태 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 상태 deleted, 자기 키와 개인 프로젝트를 갖는다

When

- UserAdapter.admin_search — user-3이 필터 없이 전체 조회

Then

- 삭제 상태를 포함해 심은 사용자가 모두 온다
  - items(이름순, 이름과 상태) = [('user-1', 'active'), ('user-2', 'deleted'), ('user-3', 'active')]
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = 50

