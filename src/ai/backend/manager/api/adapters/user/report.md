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

<<<<<<< HEAD
- 거부된다
  - 거부: InsufficientPrivilege
=======
- every user's key comes back in owner order
  - items.length = 3
  - items[0].id: skipped: it is a random key the seed made
  - items[0].access_key: skipped: it is a random key the seed made
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = None
  - items[0].num_queries = 0
  - items[0].last_used = None
  - items[0].user_id: same as the key owner
  - items[0].created_at: the time this run wrote
  - items[0].modified_at: the time this run wrote
  - items[1].id: skipped: it is a random key the seed made
  - items[1].access_key: skipped: it is a random key the seed made
  - items[1].is_active = True
  - items[1].is_admin = False
  - items[1].is_default = True
  - items[1].rate_limit = 10000
  - items[1].resource_policy = 'keypair-policy-2'
  - items[1].ssh_public_key = None
  - items[1].num_queries = 0
  - items[1].last_used = None
  - items[1].user_id: same as the key owner
  - items[1].created_at: the time this run wrote
  - items[1].modified_at: the time this run wrote
  - items[2].id: skipped: it is a random key the seed made
  - items[2].access_key: skipped: it is a random key the seed made
  - items[2].is_active = True
  - items[2].is_admin = True
  - items[2].is_default = True
  - items[2].rate_limit = 10000
  - items[2].resource_policy = 'keypair-policy-3'
  - items[2].ssh_public_key = None
  - items[2].num_queries = 0
  - items[2].last_used = None
  - items[2].user_id: same as the key owner
  - items[2].created_at: the time this run wrote
  - items[2].modified_at: the time this run wrote
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = None
>>>>>>> 07042686 (fix(BA-9042): stop generating an SSH keypair when a user is created (#17109))

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

<<<<<<< HEAD
- 수정 목록은 비고, 그 사용자가 실패 목록에 온다
=======
- an empty list comes back
  - loaded = []

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when the superadmin requests an existing id and a missing id together, it passes the permission gate and the missing element comes back empty

Given

- one domain and two users, and neither holds a permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project

When

- UserAdapter.batch_load_by_ids: user-2 batch reads user-1 and a missing id

Then

- the existing user comes back as a node and the missing id comes back empty
  - length = 2
  - [0].id: same as the user seeded in advance
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
  - [0].organization.main_access_key: the user's main access key is filled
  - [0].security.allowed_client_ip = None
  - [0].security.totp_activated = False
  - [0].security.totp_activated_at = None
  - [0].security.sudo_session_enabled = False
  - [0].container.container_uid = None
  - [0].container.container_main_gid = None
  - [0].container.container_gids = None
  - [0].timestamps.created_at: the time this run wrote
  - [0].timestamps.modified_at: the time this run wrote
  - [1] = None

<a id="reading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order"></a>

#### [a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when a user granted read on only one user requests a readable user, an unreadable user, and a missing id at once, a result comes back for each element in input order

Given

- one domain and three users, and the caller holds the user read permission on only one of them
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.batch_load_by_ids: user-3 batch reads user-1, user-2, and a missing id in that order

Then

- a result comes back for each element in input order
  - length = 3
  - [0].id: same as the user seeded in advance
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
  - [0].organization.main_access_key: the user's main access key is filled
  - [0].security.allowed_client_ip = None
  - [0].security.totp_activated = False
  - [0].security.totp_activated_at = None
  - [0].security.sudo_session_enabled = False
  - [0].container.container_uid = None
  - [0].container.container_main_gid = None
  - [0].container.container_gids = None
  - [0].timestamps.created_at: the time this run wrote
  - [0].timestamps.modified_at: the time this run wrote
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### UserAdapter.batch_lookup_by_emails

<a id="reading-a-user-granted-read-on-another-user-looks-up-their-id-by-email"></a>

#### [a-user-granted-read-on-another-user-looks-up-their-id-by-email](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when a user granted the user read permission in the target user scope looks up that user's email, the id of that user comes back

Given

- one domain and two users, and one of them holds the user read permission on the other
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.batch_lookup_by_emails: user-2 looks up the email of user-1

Then

- the id of the user found comes back
  - length = 1
  - [0]: same as the id of the target user

<a id="reading-an-email-lookup-of-no-emails-answers-an-empty-list"></a>

#### [an-email-lookup-of-no-emails-answers-an-empty-list](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when a user holding no permission gives an empty email list, no action is called and an empty list comes back

Given

- one domain and two users, and neither holds a permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- UserAdapter.batch_lookup_by_emails: user-2 looks up emails from an empty list

Then

- an empty list comes back
  - loaded = []

<a id="reading-an-unreadable-user-and-a-missing-email-are-refused-alike"></a>

#### [an-unreadable-user-and-a-missing-email-are-refused-alike](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when a user granted read on only one user looks up a readable user, an unreadable user, and a missing email at once, the first comes back as an id and the other two come back with the same rejection in input order

Given

- one domain and three users, and the caller holds the user read permission on only one of them
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.batch_lookup_by_emails: user-3 looks up the emails of user-1, user-2, and a missing email in that order

Then

- the readable user comes back as an id and the other two come back with the same rejection in input order
  - length = 3
  - [0]: same as the id of the readable user
  - rejected: GenericBadRequest
  - rejected: GenericBadRequest

### UserAdapter.bulk_get_keypair_ids

<a id="loading_keypairs-a-user-granted-read-on-another-loads-their-key-by-id"></a>

#### [a-user-granted-read-on-another-loads-their-key-by-id](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

when a user granted the user read permission in the target user scope reads that user's key and a missing id at once, the whole key and an empty value come back in that order

Given

- one domain and two users, the target holds one more keypair besides the default one, and the caller holds the user read permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.bulk_get_keypair_ids: user-2 batch reads the key of user-1 and a missing id

Then

- the key read comes back as a node and the missing id as an empty value
  - length = 2
  - id: same as the keypair seeded in advance
  - access_key: same as the keypair seeded in advance
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-2'
  - num_queries = 0
  - last_used = None
  - user_id: same as the keypair owner
  - created_at: the time this run wrote
  - modified_at: the time this run wrote
  - field_id: same as the keypair seeded in advance
  - [1] = None

<a id="loading_keypairs-a-user-granted-nothing-gets-a-rejection-for-anothers-key"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-anothers-key](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

when a user holding no permission reads another user's key and a missing id at once, that key entry is rejected for lack of permission and the missing id entry is empty

Given

- one domain and two users, the target holds one more keypair besides the default one, and the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.bulk_get_keypair_ids: user-2 batch reads the key of user-1 and a missing id

Then

- the unreadable key is rejected for lack of permission and the missing id comes back empty
  - length = 2
  - rejected: NotEnoughPermission
  - [1] = None

### UserAdapter.bulk_lookup_keypair_access_keys

<a id="loading_keypairs-a-user-looks-up-the-keypair-an-access-key-names"></a>

#### [a-user-looks-up-the-keypair-an-access-key-names](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

when a user looks up an access key and an access key nobody holds at once, the first comes back as that keypair's id and the second as an empty value

Given

- one domain and two users, the target holds one more keypair besides the default one, and the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.bulk_lookup_keypair_access_keys: user-2 looks up the access key of user-1 and an access key nobody holds

Then

- the key found comes back as its id and the access key nobody holds is empty
  - length = 2
  - [0]: same as the keypair seeded in advance
  - [1] = None

<a id="loading_keypairs-looking-up-an-access-key-without-login-is-refused"></a>

#### [looking-up-an-access-key-without-login-is-refused](/tests/scenario/bai_scenario/manager/user/test_loading_keypairs.py): pass

looking up a key by an access key without a login context is rejected as user not found

Given

- one domain and two users, the target holds one more keypair besides the default one, and the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.bulk_lookup_keypair_access_keys: without a login context, looks up an access key

Then

- the call is rejected
  - rejected: UserNotFound

### UserAdapter.domain_search

<a id="searching-a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users"></a>

#### [a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user granted user READ in the domain scope searches by domain name, the users of other domains are left out

Given

- one domain, one user in the same domain and one user in another domain, the caller holds the user READ permission in that domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Domain other-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.domain_search: user-3 searches by home-1

Then

- every user in reach comes back and the page information is carried
  - items(by name) = ['user-1', 'user-3']
  - pagination.total = 2
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-granted-nothing-may-not-search-a-domain-by-name"></a>

#### [a-user-granted-nothing-may-not-search-a-domain-by-name](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a user holding no role who tries to search by domain name is rejected by the scope permission gate

Given

- one domain, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.domain_search: user-1 searches by home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="searching-searching-a-domain-name-nothing-answers-to-is-not-found"></a>

#### [searching-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user holding the permission searches by a domain name nothing answers to, the name lookup step rejects it as not found before the scope check

Given

- one domain, the caller holds the user READ permission in that domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.domain_search: user-1 searches by no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### UserAdapter.gql_admin_search

<a id="searching-a-gql-search-without-page-arguments-answers-the-newest-ten"></a>

#### [a-gql-search-without-page-arguments-answers-the-newest-ten](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when the superadmin searches omitting both the cursor and the page arguments, up to ten users come back in descending creation time along with the next page flag

Given

- one domain, 11 users, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
    - User resource policy user-policy-4: up to 10 folders per user
    - Keypair policy keypair-policy-4: up to 5 concurrent sessions
    - regular user user-4: has their own keypair and personal project
    - User resource policy user-policy-5: up to 10 folders per user
    - Keypair policy keypair-policy-5: up to 5 concurrent sessions
    - regular user user-5: has their own keypair and personal project
    - User resource policy user-policy-6: up to 10 folders per user
    - Keypair policy keypair-policy-6: up to 5 concurrent sessions
    - regular user user-6: has their own keypair and personal project
    - User resource policy user-policy-7: up to 10 folders per user
    - Keypair policy keypair-policy-7: up to 5 concurrent sessions
    - regular user user-7: has their own keypair and personal project
    - User resource policy user-policy-8: up to 10 folders per user
    - Keypair policy keypair-policy-8: up to 5 concurrent sessions
    - regular user user-8: has their own keypair and personal project
    - User resource policy user-policy-9: up to 10 folders per user
    - Keypair policy keypair-policy-9: up to 5 concurrent sessions
    - regular user user-9: has their own keypair and personal project
    - User resource policy user-policy-10: up to 10 folders per user
    - Keypair policy keypair-policy-10: up to 5 concurrent sessions
    - regular user user-10: has their own keypair and personal project
    - User resource policy user-policy-11: up to 10 folders per user
    - Keypair policy keypair-policy-11: up to 5 concurrent sessions
    - regular user user-11: has their own keypair and personal project
    - User resource policy user-policy-12: up to 10 folders per user
    - Keypair policy keypair-policy-12: up to 5 concurrent sessions
    - superadmin user-12: has their own keypair and personal project

When

- UserAdapter.gql_admin_search: user-12 searches every user over GQL without page arguments

Then

- ten of the users seeded in advance come back newest first and there is a next page
  - items.length = 10
  - items(names): every name comes from the users seeded in advance
  - items(creation time): they come in descending creation time
  - total_count = 12
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-gql-search-every-user"></a>

#### [a-user-who-is-not-the-superadmin-may-not-gql-search-every-user](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a user holding the permission is rejected by the global role gate when searching every user over GQL

Given

- one domain, the caller holds the user READ permission in that domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.gql_admin_search: user-1 searches every user over GQL without page arguments

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.gql_admin_search_keypairs

<a id="managing_keypairs-the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only"></a>

#### [the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when the superadmin gives a policy name in a GQL key search gated by the global role, only the keys under that policy come back

Given

- one domain, two users, one superadmin, and a different keypair policy for each
  - Domain home-1
  - Prepare one user holding their own keypair policy
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project

When

- UserAdapter.gql_admin_search_keypairs: user-3 searches keys over GQL with a filter on keypair-policy-1

Then

- only the one key under that policy comes back
  - items.length = 1
  - items[0].id: skipped: it is a random key the seed made
  - items[0].access_key: skipped: it is a random key the seed made
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = None
  - items[0].num_queries = 0
  - items[0].last_used = None
  - items[0].user_id: same as the key owner
  - items[0].created_at: the time this run wrote
  - items[0].modified_at: the time this run wrote
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding the permission is rejected by the global role gate when searching keys over GQL

Given

- one domain and one user granted the user READ permission in the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.gql_admin_search_keypairs: user-1 searches every key over GQL

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.gql_scoped_search

<a id="searching-a-gql-scoped-search-over-two-granted-scopes-joins-their-users"></a>

#### [a-gql-scoped-search-over-two-granted-scopes-joins-their-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a GQL scoped search under the same permission brings back the users of both scopes in the cursor response

Given

- two domains, one project of the second domain and one user on its roster, and the caller holds the user READ permission in the first domain scope and in that project scope
  - Domain home-1
  - Domain other-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: added to the member list of Project research-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1
    - Role user-role-2: applies only within the scope it is granted in
    - Role user-role-2: READ allowed on every user
    - regular user user-2: holds Role user-role-2

When

- UserAdapter.gql_scoped_search: user-2 searches over GQL with two scopes: home-1 and research-1

Then

- every user in reach comes back on one page
  - items(by name) = ['user-1', 'user-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-one-scope-without-a-grant-refuses-the-whole-gql-scoped-search"></a>

#### [one-scope-without-a-grant-refuses-the-whole-gql-scoped-search](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user granted READ on only one scope gives two scopes to a GQL scoped search, the scope permission gate rejects all of them

Given

- two domains, one project of the second domain and one user on its roster, and the caller holds the user READ permission only in the first domain scope
  - Domain home-1
  - Domain other-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: added to the member list of Project research-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.gql_scoped_search: user-2 searches over GQL with two scopes: home-1 and research-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.gql_search_by_domain

<a id="searching-a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users"></a>

#### [a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a GQL domain search under the same permission brings back only the users of that domain in the cursor response

Given

- one domain, one user in the same domain and one user in another domain, the caller holds the user READ permission in that domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Domain other-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.gql_search_by_domain: user-3 searches over GQL by home-1

Then

- every user in reach comes back on one page
  - items(by name) = ['user-1', 'user-3']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-gql-search-a-domain"></a>

#### [a-user-granted-nothing-may-not-gql-search-a-domain](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a GQL domain search from a user holding no role is rejected by the scope permission gate

Given

- one domain, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.gql_search_by_domain: user-1 searches over GQL by home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.gql_search_by_project

<a id="searching-a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster"></a>

#### [a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a GQL project search under the same permission brings back only the users on the roster in the cursor response

Given

- one domain and one project, one user on its roster and one not, and the caller holds the user READ permission in that project scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-1: added to the member list of Project research-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.gql_search_by_project: user-3 searches over GQL by research-1

Then

- every user in reach comes back on one page
  - items(by name) = ['user-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-gql-search-a-project"></a>

#### [a-user-granted-nothing-may-not-gql-search-a-project](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a GQL project search from a user holding no role is rejected by the scope permission gate

Given

- one domain, one project, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.gql_search_by_project: user-1 searches over GQL by research-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.project_search

<a id="searching-a-user-granted-on-a-project-searching-it-finds-only-its-roster"></a>

#### [a-user-granted-on-a-project-searching-it-finds-only-its-roster](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user granted user READ in the project scope searches by that project, only the users on its roster come back

Given

- one domain and one project, one user on its roster and one not, and the caller holds the user READ permission in that project scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-1: added to the member list of Project research-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.project_search: user-3 searches by research-1

Then

- every user in reach comes back and the page information is carried
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-granted-nothing-may-not-search-a-project"></a>

#### [a-user-granted-nothing-may-not-search-a-project](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a project search from a user holding no role is rejected by the scope permission gate

Given

- one domain, one project, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.project_search: user-1 searches by research-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.resolve_domain_id

<a id="resolving_domain-a-user-resolves-the-id-of-a-domain-by-its-name"></a>

#### [a-user-resolves-the-id-of-a-domain-by-its-name](/tests/scenario/bai_scenario/manager/user/test_resolving_domain.py): pass

when a user in a domain resolves its name, the id of that domain comes back

Given

- one domain and one user in it
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.resolve_domain_id: user-1 resolves the id of home-1

Then

- the id of that domain comes back
  - id: same as the id of the domain seeded in advance

<a id="resolving_domain-resolving-a-domain-name-nothing-answers-to-is-not-found"></a>

#### [resolving-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/user/test_resolving_domain.py): pass

resolving a name no domain answers to is rejected as not found

Given

- one domain and one user in it
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.resolve_domain_id: user-1 resolves the id of no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### UserAdapter.role_search

<a id="searching-a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders"></a>

#### [a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user granted user READ in the scope that holds the role gives one role, only the user assigned that role comes back

Given

- one domain and two users, only the first holds a role, and the caller holds the user READ permission in that domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Role holder-role-1: applies only within the scope it is granted in
  - regular user user-1: holds Role holder-role-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.role_search: user-3 searches with a filter on the role

Then

- only the user holding the role comes back
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-the-superadmin-searching-by-role-finds-only-its-holders"></a>

#### [the-superadmin-searching-by-role-finds-only-its-holders](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when the superadmin gives one role in a role search gated by the global role, only the user assigned that role comes back

Given

- one domain and two users, only the first holds a role, and the caller is the superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Role holder-role-1: applies only within the scope it is granted in
  - regular user user-1: holds Role holder-role-1

When

- UserAdapter.role_search: user-3 searches with a filter on the role

Then

- only the user holding the role comes back
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-granted-nothing-may-not-search-by-role"></a>

#### [a-user-granted-nothing-may-not-search-by-role](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

a user holding no permission who tries to search by role is rejected by the scope permission gate

Given

- one domain and two users, only the first holds a role, and the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Role holder-role-1: applies only within the scope it is granted in
  - regular user user-1: holds Role holder-role-1

When

- UserAdapter.role_search: user-3 searches with a filter on the role

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.scoped_search

<a id="searching-a-scoped-search-over-two-granted-scopes-joins-their-users"></a>

#### [a-scoped-search-over-two-granted-scopes-joins-their-users](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user granted READ in both the domain scope and the project scope gives both scopes, the users of the two scopes are joined without duplicates

Given

- two domains, one project of the second domain and one user on its roster, and the caller holds the user READ permission in the first domain scope and in that project scope
  - Domain home-1
  - Domain other-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: added to the member list of Project research-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1
    - Role user-role-2: applies only within the scope it is granted in
    - Role user-role-2: READ allowed on every user
    - regular user user-2: holds Role user-role-2

When

- UserAdapter.scoped_search: user-2 searches with two scopes: home-1 and research-1

Then

- every user in reach comes back and the page information is carried
  - items(by name) = ['user-1', 'user-2']
  - pagination.total = 2
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-scoped-search-without-page-arguments-answers-up-to-fifty"></a>

#### [a-scoped-search-without-page-arguments-answers-up-to-fifty](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user holding the permission runs a scoped search without page arguments, limit 50 and offset 0 are carried in the response

Given

- one domain, the caller holds the user READ permission in that domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.scoped_search: user-1 searches in the home-1 scope without page arguments

Then

- every user in reach comes back and the page information is carried
  - items(by name) = ['user-1']
  - pagination.total = 1
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-one-scope-without-a-grant-refuses-the-whole-scoped-search"></a>

#### [one-scope-without-a-grant-refuses-the-whole-scoped-search](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when a user granted READ on only the first scope gives two scopes, the scope permission gate rejects all of them

Given

- two domains, one project of the second domain and one user on its roster, and the caller holds the user READ permission only in the first domain scope
  - Domain home-1
  - Domain other-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: added to the member list of Project research-1
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.scoped_search: user-2 searches with two scopes: home-1 and research-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.search_my_keypairs

<a id="own_keypairs-a-user-granted-read-searching-their-keys-sees-only-their-own"></a>

#### [a-user-granted-read-searching-their-keys-sees-only-their-own](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user granted READ in their own scope searches their own keys, the keys of other users are left out

Given

- one domain and one user holding 1 extra keys that are not the default, one other user holding an extra key that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-2: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.search_my_keypairs: user-1 searches their own keys without page arguments

Then

- only their own two keys come back
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.is_default(extra key first) = [False, True]
  - items[the extra key].id: same as the keypair seeded in advance
  - items[the extra key].access_key: same as the keypair seeded in advance
  - items[the extra key].is_active = True
  - items[the extra key].is_admin = False
  - items[the extra key].is_default = False
  - items[the extra key].rate_limit = 10000
  - items[the extra key].resource_policy = 'keypair-policy-1'
  - items[the extra key].num_queries = 0
  - items[the extra key].last_used = None
  - items[the extra key].user_id: same as the keypair owner
  - items[the extra key].created_at: the time this run wrote
  - items[the extra key].modified_at: the time this run wrote
  - items[the default key].id: skipped: it is an access key the seed makes anew every time
  - items[the default key].access_key: skipped: it is an access key the seed makes anew every time
  - items[the default key].is_active = True
  - items[the default key].is_admin = False
  - items[the default key].is_default = True
  - items[the default key].rate_limit = 10000
  - items[the default key].resource_policy = 'keypair-policy-1'
  - items[the default key].num_queries = 0
  - items[the default key].last_used = None
  - items[the default key].user_id: same as the key owner
  - items[the default key].created_at: the time this run wrote
  - items[the default key].modified_at: the time this run wrote

<a id="own_keypairs-searching-own-keys-without-page-arguments-answers-the-ten-newest"></a>

#### [searching-own-keys-without-page-arguments-answers-the-ten-newest](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission searches without page arguments, ten keys in descending creation time and the next page flag come back

Given

- one domain and one user holding 10 extra keys that are not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.search_my_keypairs: user-1 searches their own keys without page arguments

Then

- ten of their eleven keys come back newest first and there is a next page
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False
  - items.length = 10
  - items(created_at, field_id): descending creation time, then ascending field id for the same time
  - items.user_id: same as all the caller
  - items.created_at: the time this run wrote
  - the remaining item fields: skipped: this row looks at order and count; another row looks at the whole key node

<a id="own_keypairs-a-user-granted-nothing-may-not-search-their-own-keys"></a>

#### [a-user-granted-nothing-may-not-search-their-own-keys](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user holding no role who tries to search their own keys is rejected by the scope permission gate

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.search_my_keypairs: user-1 searches their own keys without page arguments

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserConfigAdapter.delete_default_auto_generated_file

<a id="config_files-a-user-granted-nothing-may-not-delete-a-config-file"></a>

#### [a-user-granted-nothing-may-not-delete-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

a user holding no permission who tries to delete their own config file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserConfigAdapter.delete_default_auto_generated_file: user-1 deletes one of their own config files

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="config_files-deleting-a-config-file-that-is-not-marked-default-is-not-found"></a>

#### [deleting-a-config-file-that-is-not-marked-default-is-not-found](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

when a user holding READ and UPDATE deletes a config file not marked as default, it is rejected as not found

Given

- one domain and one user, the user holds one config file not marked as default, the user holds the READ, UPDATE permission on themselves
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one config file that is not marked default
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserConfigAdapter.delete_default_auto_generated_file: user-1 deletes one of their own config files

Then

- the call is rejected
  - rejected: DotfileNotFound

### UserConfigAdapter.get_default_auto_generated_file

<a id="config_files-a-config-file-that-is-not-marked-default-is-not-found"></a>

#### [a-config-file-that-is-not-marked-default-is-not-found](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

when a user holding READ reads a config file not marked as default, it is rejected as not found

Given

- one domain and one user, the user holds one config file not marked as default, the user holds the READ permission on themselves
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one config file that is not marked default
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserConfigAdapter.get_default_auto_generated_file: user-1 reads one of their own config files

Then

- the call is rejected
  - rejected: DotfileNotFound

<a id="config_files-a-user-granted-nothing-may-not-read-a-config-file"></a>

#### [a-user-granted-nothing-may-not-read-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

a user holding no permission who tries to read their own config file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserConfigAdapter.get_default_auto_generated_file: user-1 reads one of their own config files

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserConfigAdapter.get_default_auto_generated_files

<a id="config_files-a-user-granted-read-on-themselves-lists-no-default-config-file"></a>

#### [a-user-granted-read-on-themselves-lists-no-default-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

when a user holding READ lists the config files of theirs marked as default, an empty list comes back

Given

- one domain and one user, the user holds the READ permission on themselves
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserConfigAdapter.get_default_auto_generated_files: user-1 lists the config files of theirs marked as default

Then

- no file is marked default, so an empty list comes back
  - files = []

<a id="config_files-a-user-granted-nothing-may-not-list-their-config-files"></a>

#### [a-user-granted-nothing-may-not-list-their-config-files](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

a user holding no permission who tries to list their own config files is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserConfigAdapter.get_default_auto_generated_files: user-1 lists the config files of theirs marked as default

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserConfigAdapter.update_default_auto_generated_file

<a id="config_files-a-user-granted-nothing-may-not-update-a-config-file"></a>

#### [a-user-granted-nothing-may-not-update-a-config-file](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

a user holding no permission who tries to change their own config file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserConfigAdapter.update_default_auto_generated_file: user-1 changes the permission and content of one of their config files

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="config_files-updating-a-config-file-that-is-not-marked-default-is-not-found"></a>

#### [updating-a-config-file-that-is-not-marked-default-is-not-found](/tests/scenario/bai_scenario/manager/user/test_config_files.py): pass

when a user holding READ and UPDATE changes a config file not marked as default, it is rejected as not found

Given

- one domain and one user, the user holds one config file not marked as default, the user holds the READ, UPDATE permission on themselves
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one config file that is not marked default
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserConfigAdapter.update_default_auto_generated_file: user-1 changes the permission and content of one of their config files

Then

- the call is rejected
  - rejected: DotfileNotFound

### UserAdapter.admin_create_keypair

<a id="managing_keypairs-a-key-may-not-be-made-under-a-policy-that-does-not-exist"></a>

#### [a-key-may-not-be-made-under-a-policy-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user holding the permission gives a policy name that does not exist, input validation rejects it

Given

- one domain and one target user, the caller holds the user UPDATE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_create_keypair: user-2 creates a key for user-1 under a policy that does not exist

Then

- the call is rejected
  - rejected: KeypairResourcePolicyNotFound

<a id="managing_keypairs-a-user-granted-nothing-may-not-make-a-key-for-another"></a>

#### [a-user-granted-nothing-may-not-make-a-key-for-another](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to create a key is rejected by the entity permission gate

Given

- one domain and one target user, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions

When

- UserAdapter.admin_create_keypair: user-2 creates a key for user-1 under granted-policy-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="managing_keypairs-a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy"></a>

#### [a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted UPDATE in the target user scope, not the superadmin, creates a key under a policy, a new key that is not the default and its secret come back

Given

- one domain and one target user, the caller holds the user UPDATE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_create_keypair: user-2 creates a key for user-1 under granted-policy-1

Then

- the whole key created and its secret come back
  - rejected: NotEnoughPermission

### UserAdapter.admin_get_keypair

<a id="managing_keypairs-a-granted-user-reads-another-users-key-by-access-key"></a>

#### [a-granted-user-reads-another-users-key-by-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted READ in the target scope reads a key, that whole key node comes back

Given

- one domain and one target user, the target holds one extra key that is not the default, the caller holds the user READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_get_keypair: user-2 reads the key of user-1 by access key

Then

- the whole key seeded in advance comes back
  - id: same as the key seeded in advance
  - access_key: same as the key seeded in advance
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key = None
  - num_queries = 0
  - last_used = None
  - user_id: same as the key owner
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="managing_keypairs-a-user-granted-nothing-may-not-read-another-users-key"></a>

#### [a-user-granted-nothing-may-not-read-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to read a key is rejected at the owner lookup step

Given

- one domain and one target user, the target holds one extra key that is not the default, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.admin_get_keypair: user-2 reads the key of user-1 by access key

Then

- the call is rejected
  - rejected: GenericBadRequest

### UserAdapter.admin_update_keypair

<a id="managing_keypairs-a-granted-user-changing-another-users-rate-limit-changes-only-that"></a>

#### [a-granted-user-changing-another-users-rate-limit-changes-only-that](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted READ and UPDATE in the target scope gives only a rate limit, the key node comes back with everything else unchanged and only the rate limit changed

Given

- one domain and one target user, the target holds one extra key that is not the default, the caller holds the user READ, UPDATE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_update_keypair: user-2 gives a rate limit to the key of user-1

Then

- the whole key with only the rate limit changed comes back
  - id: same as the key seeded in advance
  - access_key: same as the key seeded in advance
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 45000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key = None
  - num_queries = 0
  - last_used = None
  - user_id: same as the key owner
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="managing_keypairs-a-user-granted-nothing-may-not-change-another-users-key"></a>

#### [a-user-granted-nothing-may-not-change-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to change a key is rejected at the owner lookup step

Given

- one domain and one target user, the target holds one extra key that is not the default, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.admin_update_keypair: user-2 gives a rate limit to the key of user-1

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-change-another-users-key"></a>

#### [a-user-granted-only-read-may-not-change-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding only READ who tries to change a key is rejected by the entity permission gate

Given

- one domain and one target user, the target holds one extra key that is not the default, the caller holds the user READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_update_keypair: user-2 gives a rate limit to the key of user-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="managing_keypairs-another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist"></a>

#### [another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user holding the permission gives a policy name that does not exist, input validation rejects it

Given

- one domain and one target user, the target holds one extra key that is not the default, the caller holds the user READ, UPDATE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_update_keypair: user-2 gives a rate limit and a policy that does not exist to the key of user-1

Then

- the call is rejected
  - rejected: KeypairResourcePolicyNotFound

### UserAdapter.bulk_create_users

<a id="creating-the-superadmin-bulk-creates-a-user"></a>

#### [the-superadmin-bulk-creates-a-user](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

when the superadmin bulk creates one user, the user just created comes back and none failed

Given

- one domain and one superadmin, and the caller holds no permission
  - Domain home-1
  - User resource policy user-policy-1: up to 10 folders per user
  - Default keypair policy default-keypair-policy-1: a keypair that names no policy gets this one
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- UserAdapter.bulk_create_users: user-1 bulk creates made in home-1

Then

- the user just created comes back and none failed
  - created_users.length = 1
  - failed = []
  - user.id: skipped: the database generates it
  - user.entity_id: same as the user's own id
  - user.basic_info.username = 'made'
  - user.basic_info.email = 'made@scenario.local'
  - user.basic_info.full_name = None
  - user.basic_info.description = None
  - user.basic_info.integration_name = None
  - user.status.status = 'active'
  - user.status.status_info = None
  - user.status.need_password_change = False
  - user.organization.domain_name = 'home-1'
  - user.organization.domain_id: same as the id of the domain seeded in advance
  - user.organization.role = 'user'
  - user.organization.resource_policy = 'user-policy-1'
  - user.organization.main_access_key: the user's main access key is filled
  - user.security.allowed_client_ip = None
  - user.security.totp_activated = False
  - user.security.totp_activated_at = None
  - user.security.sudo_session_enabled = False
  - user.container.container_uid = None
  - user.container.container_main_gid = None
  - user.container.container_gids = None
  - user.timestamps.created_at: the time this run wrote
  - user.timestamps.modified_at: the time this run wrote

<a id="creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users"></a>

#### [a-user-who-is-not-the-superadmin-may-not-bulk-create-users](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

even a user granted CREATE in the domain scope is rejected by the global role gate when bulk creating users

Given

- one domain and one user granted the user create permission in the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the CREATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: CREATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.bulk_create_users: user-1 bulk creates made in home-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.bulk_create_users_with_keypair

<a id="creating-the-superadmin-bulk-creates-a-user-and-gets-its-keypair"></a>

#### [the-superadmin-bulk-creates-a-user-and-gets-its-keypair](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

when the superadmin bulk creates one user through the keypair-returning call, the user just created and its default keypair with the secret key come back and none failed

Given

- one domain and one superadmin, and the caller holds no permission
  - Domain home-1
  - User resource policy user-policy-1: up to 10 folders per user
  - Default keypair policy default-keypair-policy-1: a keypair that names no policy gets this one
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- UserAdapter.bulk_create_users_with_keypair: user-1 bulk creates made in home-1

Then

- the user just created and its default keypair with the secret key come back and none failed
  - created.length = 1
  - failed = []
  - user.id: skipped: the database generates it
  - user.entity_id: same as the user's own id
  - user.basic_info.username = 'made'
  - user.basic_info.email = 'made@scenario.local'
  - user.basic_info.full_name = None
  - user.basic_info.description = None
  - user.basic_info.integration_name = None
  - user.status.status = 'active'
  - user.status.status_info = None
  - user.status.need_password_change = False
  - user.organization.domain_name = 'home-1'
  - user.organization.domain_id: same as the id of the domain seeded in advance
  - user.organization.role = 'user'
  - user.organization.resource_policy = 'user-policy-1'
  - user.organization.main_access_key: same as the keypair this call made
  - user.security.allowed_client_ip = None
  - user.security.totp_activated = False
  - user.security.totp_activated_at = None
  - user.security.sudo_session_enabled = False
  - user.container.container_uid = None
  - user.container.container_main_gid = None
  - user.container.container_gids = None
  - user.timestamps.created_at: the time this run wrote
  - user.timestamps.modified_at: the time this run wrote
  - created[0].keypair.id: skipped: it is the access key the manager made
  - created[0].keypair.field_id: skipped: the database generates it
  - created[0].keypair.access_key: skipped: the manager creates it
  - created[0].keypair.is_active = True
  - created[0].keypair.is_admin = False
  - created[0].keypair.is_default = True
  - created[0].keypair.rate_limit = 10000
  - created[0].keypair.resource_policy = 'default-keypair-policy-1'
  - created[0].keypair.ssh_public_key = None
  - created[0].keypair.num_queries = 0
  - created[0].keypair.last_used = None
  - created[0].keypair.user_id: same as the user just created
  - created[0].keypair.created_at: the time this run wrote
  - created[0].keypair.modified_at: the time this run wrote
  - created[0].secret_key: the secret key the manager made is filled

<a id="creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs"></a>

#### [a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

a user holding the permission is rejected by the global role gate when calling this bulk create

Given

- one domain and one user granted the user create permission in the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the CREATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: CREATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.bulk_create_users_with_keypair: user-1 bulk creates made in home-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.bulk_update_users

<a id="retiring-a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit"></a>

#### [a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when the superadmin bulk edits with DELETED for an active user, ACTIVE for a deleted user, and a full name for another deleted user, the first two are deleted and restored and come back in the updated list, and the third comes back as failed

Given

- one domain, one superadmin, one active user, and two deleted users
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-4: up to 10 folders per user
    - Keypair policy keypair-policy-4: up to 5 concurrent sessions
    - superadmin user-4: has their own keypair and personal project
  - Prepare one deleted user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: status deleted, has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: status deleted, has their own keypair and personal project

When

- UserAdapter.bulk_update_users: user-4 bulk edits: DELETED for user-1, ACTIVE for user-2, and a full name for user-3

Then

- the deleted user and the restored user come back in the updated list and the remaining one in the failed list
  - updated_users.id: same as the users given DELETED and ACTIVE
  - failed.user_id: same as the deleted user whose full name alone was changed
  - failed.message: skipped: the exception message may change
  - updated_users[deleted user].id: same as the user seeded in advance
  - updated_users[deleted user].basic_info.username = 'user-1'
  - updated_users[deleted user].basic_info.email = 'user-1@scenario.local'
  - updated_users[deleted user].basic_info.full_name = None
  - updated_users[deleted user].basic_info.description = None
  - updated_users[deleted user].basic_info.integration_name = None
  - updated_users[deleted user].status.status = 'deleted'
  - updated_users[deleted user].status.status_info = 'admin-requested'
  - updated_users[deleted user].status.need_password_change = False
  - updated_users[deleted user].organization.domain_name = 'home-1'
  - updated_users[deleted user].organization.role = 'user'
  - updated_users[deleted user].organization.resource_policy = 'user-policy-1'
  - updated_users[deleted user].organization.main_access_key: the user's main access key is filled
  - updated_users[deleted user].security.allowed_client_ip = None
  - updated_users[deleted user].security.totp_activated = False
  - updated_users[deleted user].security.totp_activated_at = None
  - updated_users[deleted user].security.sudo_session_enabled = False
  - updated_users[deleted user].container.container_uid = None
  - updated_users[deleted user].container.container_main_gid = None
  - updated_users[deleted user].container.container_gids = None
  - updated_users[deleted user].timestamps.created_at: the time this run wrote
  - updated_users[deleted user].timestamps.modified_at: the time this run wrote
  - updated_users[restored user].id: same as the user seeded in advance
  - updated_users[restored user].basic_info.username = 'user-2'
  - updated_users[restored user].basic_info.email = 'user-2@scenario.local'
  - updated_users[restored user].basic_info.full_name = None
  - updated_users[restored user].basic_info.description = None
  - updated_users[restored user].basic_info.integration_name = None
  - updated_users[restored user].status.status = 'active'
  - updated_users[restored user].status.status_info = 'admin-requested'
  - updated_users[restored user].status.need_password_change = False
  - updated_users[restored user].organization.domain_name = 'home-1'
  - updated_users[restored user].organization.role = 'user'
  - updated_users[restored user].organization.resource_policy = 'user-policy-2'
  - updated_users[restored user].organization.main_access_key: it is empty because there is no active default key
  - updated_users[restored user].security.allowed_client_ip = None
  - updated_users[restored user].security.totp_activated = False
  - updated_users[restored user].security.totp_activated_at = None
  - updated_users[restored user].security.sudo_session_enabled = False
  - updated_users[restored user].container.container_uid = None
  - updated_users[restored user].container.container_main_gid = None
  - updated_users[restored user].container.container_gids = None
  - updated_users[restored user].timestamps.created_at: the time this run wrote
  - updated_users[restored user].timestamps.modified_at: the time this run wrote

<a id="editing-a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed"></a>

#### [a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when the superadmin gives a default key switch to another user's key along with a bulk edit, that user leaves the updated list and comes back as failed

Given

- one domain and one target user, 1 more user, the caller is a superadmin, one more user holds an extra key that is not the default
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
    - User resource policy user-policy-4: up to 10 folders per user
    - Keypair policy keypair-policy-4: up to 5 concurrent sessions
    - superadmin user-4: has their own keypair and personal project
  - Keypair policy keypair-policy-5: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one

When

- UserAdapter.bulk_update_users: user-3 bulk edits user-1 and moves the default key to the key of user-2

Then

- the updated list is empty and that user comes back in the failed list
>>>>>>> 07042686 (fix(BA-9042): stop generating an SSH keypair when a user is created (#17109))
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

<<<<<<< HEAD
- 성공이 오고, 다시 읽은 사용자는 허용 IP만 바뀌어 있다
=======
- the whole user just created and its default keypair with the secret key come back
  - user.id: skipped: the database generates it
  - user.entity_id: same as the user's own id
  - user.basic_info.username = 'made'
  - user.basic_info.email = 'made@scenario.local'
  - user.basic_info.full_name = None
  - user.basic_info.description = None
  - user.basic_info.integration_name = None
  - user.status.status = 'active'
  - user.status.status_info = None
  - user.status.need_password_change = False
  - user.organization.domain_name = 'home-1'
  - user.organization.domain_id: same as the id of the domain seeded in advance
  - user.organization.role = 'user'
  - user.organization.resource_policy = 'user-policy-1'
  - user.organization.main_access_key: same as the keypair this call made
  - user.security.allowed_client_ip = None
  - user.security.totp_activated = False
  - user.security.totp_activated_at = None
  - user.security.sudo_session_enabled = False
  - user.container.container_uid = None
  - user.container.container_main_gid = None
  - user.container.container_gids = None
  - user.timestamps.created_at: the time this run wrote
  - user.timestamps.modified_at: the time this run wrote
  - keypair.id: skipped: it is the access key the manager made
  - keypair.field_id: skipped: the database generates it
  - keypair.access_key: skipped: the manager creates it
  - keypair.is_active = True
  - keypair.is_admin = False
  - keypair.is_default = True
  - keypair.rate_limit = 10000
  - keypair.resource_policy = 'default-keypair-policy-1'
  - keypair.ssh_public_key = None
  - keypair.num_queries = 0
  - keypair.last_used = None
  - keypair.user_id: same as the user just created
  - keypair.created_at: the time this run wrote
  - keypair.modified_at: the time this run wrote
  - secret_key: the secret key the manager made is filled

<a id="creating-a-user-granted-nothing-may-not-create-a-user"></a>

#### [a-user-granted-nothing-may-not-create-a-user](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

a user holding no role who tries to create a user is rejected by the domain scope permission gate

Given

- one domain and one user granted no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.create_user: user-1 creates made in home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="creating-a-user-may-not-be-created-in-a-domain-name-nothing-answers-to"></a>

#### [a-user-may-not-be-created-in-a-domain-name-nothing-answers-to](/tests/scenario/bai_scenario/manager/user/test_creating.py): pass

when a user holding the permission gives a domain name nothing answers to, the domain name lookup step rejects it as not found

Given

- one domain and one user granted the user create permission in the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the CREATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: CREATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.create_user: user-1 creates made in no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### UserAdapter.delete_user_by_id

<a id="retiring-a-user-granted-soft-delete-marks-another-user-deleted"></a>

#### [a-user-granted-soft-delete-marks-another-user-deleted](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted SOFT_DELETE in the target user scope deletes the user, success comes back and the state of that user changes to deleted

Given

- one domain and one target user, with the caller holding the user SOFT_DELETE, READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the SOFT_DELETE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: SOFT_DELETE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.delete_user_by_id: user-2 deletes user-1 and reads it again

Then

- the call succeeds and the user read back is in the deleted state
>>>>>>> 07042686 (fix(BA-9042): stop generating an SSH keypair when a user is created (#17109))
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

#### [another-users-new-password-leaves-the-password-change-requirement](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

대상 사용자 스코프에서 UPDATE와 READ를 받은 다른 사용자가 비밀번호 변경을 요구받는 사용자에게 새 비밀번호만 주면, 요구가 남은 노드가 온다

Given

- 도메인 하나와 대상 사용자, 사용자 0명 더, 부르는 user 한 명, 부르는 사람은 대상 사용자 스코프에서 UPDATE, READ를 받았다, 대상 사용자는 비밀번호 변경을 요구받는다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다, 비밀번호 변경을 요구받는다
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

- UserAdapter.update_user_by_id — user-2이 user-1의 비밀번호만 바꿈

Then

- 비밀번호 변경 요구가 남은 사용자 전체가 온다
  - id: 심은 사용자와 같다
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = None
  - status.need_password_change = True
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

#### [setting-ones-own-new-password-lifts-the-password-change-requirement](/tests/scenario/bai_scenario/manager/user/test_editing.py) — pass

비밀번호 변경을 요구받는 사용자가 자기 사용자 스코프에서 UPDATE와 READ를 받고, 새 비밀번호와 요구 해제를 함께 주면, 요구가 풀린 노드가 온다

Given

- 도메인 하나와 비밀번호 변경을 요구받는 사용자 한 명, 그 사용자는 자기 사용자 스코프에서 UPDATE, READ를 받았다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다, 비밀번호 변경을 요구받는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 사용자 UPDATE, READ 권한을 준 역할 배정
    - 역할 user-role-1: 이 역할이 앉은 스코프 안에서만 통한다
    - 역할 user-role-1: user 전체에 UPDATE 허용
    - 역할 user-role-1: user 전체에 READ 허용
    - 일반 사용자 user-1: 역할 user-role-1 보유

When

- UserAdapter.update_user_by_id — user-1이 자기 비밀번호를 바꾸며 비밀번호 변경 요구를 풂

Then

- 비밀번호 변경 요구가 풀린 사용자 전체가 온다
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

<<<<<<< HEAD
- 회수가 성공하고 뒤이은 조회에 세션이 없다
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
=======
- the default key of the target comes back, and the public key is changed in the read that follows
  - access_key: same as the default key of the target
  - the ssh_public_key of the read that follows = None

<a id="managing_keypairs-a-user-granted-nothing-may-not-clear-another-users-ssh-key"></a>

#### [a-user-granted-nothing-may-not-clear-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to delete a key is rejected at the owner lookup step

Given

- one domain and one target user, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions

When

- UserAdapter.admin_delete_ssh_keypair: user-2 deletes the SSH key from the default key of user-1 and reads it

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-clear-another-users-ssh-key"></a>

#### [a-user-granted-only-read-may-not-clear-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding only READ who tries to delete a key is rejected by the entity permission gate

Given

- one domain and one target user, the caller holds the user READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_delete_ssh_keypair: user-2 deletes the SSH key from the default key of user-1 and reads it

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.admin_get_ssh_keypair

<a id="managing_keypairs-a-granted-user-reads-another-users-ssh-public-key-only"></a>

#### [a-granted-user-reads-another-users-ssh-public-key-only](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted READ in the target scope reads the SSH key, only the access key and the public key come back and the private key does not

Given

- one domain and one target user, the caller holds the user READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_get_ssh_keypair: user-2 reads the SSH public key of user-1

Then

- only the access key and the public key come back
  - keypair.access_key: same as the default key of the target
  - keypair.ssh_public_key = None

<a id="managing_keypairs-a-user-granted-nothing-may-not-read-another-users-ssh-public-key"></a>

#### [a-user-granted-nothing-may-not-read-another-users-ssh-public-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to read a key is rejected at the owner lookup step

Given

- one domain and one target user, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions

When

- UserAdapter.admin_get_ssh_keypair: user-2 reads the SSH public key of user-1

Then

- the call is rejected
  - rejected: GenericBadRequest

### UserAdapter.admin_register_ssh_keypair

<a id="managing_keypairs-a-granted-user-registering-another-users-ssh-key-gets-the-access-key"></a>

#### [a-granted-user-registering-another-users-ssh-key-gets-the-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted READ and UPDATE in the target scope gives a public key, it overwrites the stored public key without a format check and the access key comes back

Given

- one domain and one target user, the caller holds the user READ, UPDATE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_register_ssh_keypair: user-2 registers an SSH key on the default key of user-1 and reads it

Then

- the default key of the target comes back, and the public key is changed in the read that follows
  - access_key: same as the default key of the target
  - the ssh_public_key of the read that follows = 'ssh-rsa scenario-public-key'

<a id="managing_keypairs-a-user-granted-nothing-may-not-register-another-users-ssh-key"></a>

#### [a-user-granted-nothing-may-not-register-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to register an SSH key is rejected at the owner lookup step

Given

- one domain and one target user, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions

When

- UserAdapter.admin_register_ssh_keypair: user-2 registers an SSH key on the default key of user-1 and reads it

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-register-another-users-ssh-key"></a>

#### [a-user-granted-only-read-may-not-register-another-users-ssh-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding only READ who tries to register an SSH key is rejected by the entity permission gate

Given

- one domain and one target user, the caller holds the user READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy granted-policy-1: up to 5 concurrent sessions
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.admin_register_ssh_keypair: user-2 registers an SSH key on the default key of user-1 and reads it

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.bulk_purge_users

<a id="retiring-a-bulk-purge-records-a-missing-id-as-a-failure"></a>

#### [a-bulk-purge-records-a-missing-id-as-a-failure](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when the superadmin gives an existing user and a missing id together, one is purged and the missing id comes back as failed

Given

- one domain, one superadmin, 1 users, and an id that is no user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project

When

- UserAdapter.bulk_purge_users: user-2 bulk purges user-1 and an id that does not exist

Then

- the purged user ids, the count, and the failures come back
  - successes: same as every user seeded in advance
  - purged_count = 1
  - failed.user_id: same as an id that does not exist
  - failed.message: skipped: the exception message may change

<a id="retiring-the-superadmin-bulk-purge-answers-the-purged-ids-and-count"></a>

#### [the-superadmin-bulk-purge-answers-the-purged-ids-and-count](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when the superadmin gives two users in a bulk purge gated by the global role, the two ids and a count of two come back

Given

- one domain, one superadmin, and 2 users
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project

When

- UserAdapter.bulk_purge_users: user-3 bulk purges user-1, user-2

Then

- the purged user ids, the count, and the failures come back
  - successes: same as every user seeded in advance
  - purged_count = 2
  - failed = []

<a id="retiring-a-user-who-is-not-the-superadmin-may-not-purge-in-bulk"></a>

#### [a-user-who-is-not-the-superadmin-may-not-purge-in-bulk](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

even a user granted HARD_DELETE in the domain scope is rejected by the global role gate when purging in bulk

Given

- one domain and one user, and the caller holds the user HARD_DELETE permission in the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the HARD_DELETE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: HARD_DELETE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.bulk_purge_users: user-2 bulk purges user-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.purge_user_by_id

<a id="retiring-a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions"></a>

#### [a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted HARD_DELETE in the target user scope purges a user that was not deleted, success comes back and that user is no longer found

Given

- one domain and one target user, with the caller holding the user HARD_DELETE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - a role assignment granting the user the HARD_DELETE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: HARD_DELETE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.purge_user_by_id: user-2 purges user-1 handing it over to themselves, and user-3 batch reads it afterwards

Then

- the call succeeds and that user is no longer found
  - success = True
  - the batch read that follows: skipped: the response a superadmin gets for a missing id is not decided yet

<a id="retiring-a-user-granted-nothing-may-not-purge-another-user"></a>

#### [a-user-granted-nothing-may-not-purge-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

a user holding no role who tries to purge a user is rejected by the entity permission gate

Given

- one domain and one target user, with the caller holding no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- UserAdapter.purge_user_by_id: user-2 purges user-1 handing it over to themselves

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-purging-a-user-to-an-admin-who-does-not-exist-is-refused"></a>

#### [purging-a-user-to-an-admin-who-does-not-exist-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user holding the permission gives an admin id that does not exist as the heir, input validation rejects it

Given

- one domain and one target user, with the caller holding the user HARD_DELETE permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the HARD_DELETE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: HARD_DELETE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.purge_user_by_id: user-2 purges user-1 handing it over to an admin id that does not exist

Then

- the call is rejected
  - rejected: UserNotFound

### UserAdapter.restore_user_by_id

<a id="retiring-a-user-granted-soft-delete-restores-a-deleted-user-to-active"></a>

#### [a-user-granted-soft-delete-restores-a-deleted-user-to-active](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted SOFT_DELETE in the target user scope restores a deleted user, success comes back and the state changes to active

Given

- one domain and one target deleted user, with the caller holding the user SOFT_DELETE, READ permission on the target
  - Domain home-1
  - Prepare one deleted user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: status deleted, has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the SOFT_DELETE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: SOFT_DELETE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.restore_user_by_id: user-2 restores user-1 and reads it again

Then

- the call succeeds and the user read back is in the active state
  - success = True
  - the read that follows.id: same as the user seeded in advance
  - the read that follows.basic_info.username = 'user-1'
  - the read that follows.basic_info.email = 'user-1@scenario.local'
  - the read that follows.basic_info.full_name = None
  - the read that follows.basic_info.description = None
  - the read that follows.basic_info.integration_name = None
  - the read that follows.status.status = 'active'
  - the read that follows.status.status_info = 'admin-requested'
  - the read that follows.status.need_password_change = False
  - the read that follows.organization.domain_name = 'home-1'
  - the read that follows.organization.role = 'user'
  - the read that follows.organization.resource_policy = 'user-policy-1'
  - the read that follows.organization.main_access_key: it is empty because there is no active default key
  - the read that follows.security.allowed_client_ip = None
  - the read that follows.security.totp_activated = False
  - the read that follows.security.totp_activated_at = None
  - the read that follows.security.sudo_session_enabled = False
  - the read that follows.container.container_uid = None
  - the read that follows.container.container_main_gid = None
  - the read that follows.container.container_gids = None
  - the read that follows.timestamps.created_at: the time this run wrote
  - the read that follows.timestamps.modified_at: the time this run wrote

<a id="retiring-a-user-granted-nothing-may-not-restore-another-user"></a>

#### [a-user-granted-nothing-may-not-restore-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

a user holding no role who tries to restore a user is rejected by the entity permission gate

Given

- one domain and one target deleted user, with the caller holding no permission
  - Domain home-1
  - Prepare one deleted user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: status deleted, has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- UserAdapter.restore_user_by_id: user-2 restores user-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-restoring-a-user-who-was-not-deleted-is-refused"></a>

#### [restoring-a-user-who-was-not-deleted-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user holding the permission tries to restore an inactive user that was not deleted, it is rejected because the user is not deleted

Given

- one domain and one target inactive user, with the caller holding the user SOFT_DELETE, READ permission on the target
  - Domain home-1
  - Prepare one inactive user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: status inactive, has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the SOFT_DELETE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: SOFT_DELETE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.restore_user_by_id: user-2 restores user-1

Then

- the call is rejected
  - rejected: UserModificationBadRequest

### UserAdapter.revoke_my_keypair

<a id="own_keypairs-a-user-granted-read-and-update-revokes-a-non-default-key"></a>

#### [a-user-granted-read-and-update-revokes-a-non-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission revokes their own extra key, success comes back and that key leaves their own key search

Given

- one domain and one user holding 1 extra keys that are not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.revoke_my_keypair: user-1 revokes their own extra key and searches their own keys again

Then

- the revoke succeeds and only the default key is left in the own key search that follows
  - success = True
  - after.total_count = 1
>>>>>>> 07042686 (fix(BA-9042): stop generating an SSH keypair when a user is created (#17109))
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

대상 스코프에서 READ와 UPDATE를 받은 사용자가 공개키를 주면, 형식 검사 없이 공개키를 덮어쓰고 access key가 답으로 온다

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
  - items(created_at, field_id): 생성 시각 내림차순, 같은 시각이면 field id 오름차순
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
  - 뒤이은 일괄 읽기: 무시함 — 없는 id에 superadmin이 받는 답은 아직 정해지지 않았다

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

#### [a-user-granted-nothing-may-not-search-by-role](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

아무 권한도 받지 않은 사용자가 역할로 훑으려 하면, 스코프 권한 문이 막는다

Given

- 도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 부르는 사람은 아무 권한도 받지 않았다
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

When

- UserAdapter.role_search — user-3이 역할로 걸러 조회

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

#### [a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders](/tests/scenario/bai_scenario/manager/user/test_searching.py) — pass

역할이 걸린 스코프의 사용자 READ를 받은 사용자가 역할 하나를 주면, 그 역할을 배정받은 사용자만 온다

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

- 역할을 받은 사람만 온다
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

