## login_session

[adapter](/src/ai/backend/manager/api/adapters/login_session/adapter.py)

Scenario: complete

- built from ops (3)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - my_search: representative success ✓ · representative rejection ✓
- direct implementation (3)
  - admin_revoke: success present 1 · rejection present 1 (global_scope)
  - admin_unblock_user: success present 1 · rejection present 1 (global_scope)
  - my_revoke: success present 1 · rejection present 1 (single_field)

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches every session, gated by the global role, with a status filter, a status order and a page, the matching sessions of every user are counted and the session the filter excludes is left out](#searching-the-superadmin-searches-every-users-login-sessions) | answered |
| [a regular user granted READ on their own user is rejected by the global role gate when searching every login session](#searching-a-regular-user-may-not-search-every-login-session) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user loads two of their own sessions by id, both come back](#batch_loading-a-user-granted-read-on-themselves-loads-their-own-login-sessions) | answered |
| [when a user granted READ on their own user loads their own session together with another user's, only the other user's session is rejected](#batch_loading-a-user-granted-read-on-themselves-is-denied-another-users-login-session) | rejected |

**my_search**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user searches their own sessions with a status filter, a status order and a page, the session of another user and the session the filter excludes are left out](#searching-a-user-granted-read-on-themselves-searches-their-own-login-sessions) | answered |
| [a user granted only UPDATE on their own user is rejected by the permission check when searching their own sessions](#searching-a-user-granted-only-update-may-not-search-their-own-login-sessions) | rejected |

**admin_revoke**

| scenario | verdict |
|---|---|
| [in an admin revoke gated by the global role, the superadmin revokes the login session of another user](#revoking-the-superadmin-revokes-another-users-login-session) | answered |
| [a regular user granted READ and UPDATE on their own user is rejected by the global role gate when revoking their own login session through the admin call](#revoking-a-regular-user-may-not-revoke-a-login-session-as-admin) | rejected |

**admin_unblock_user**

| scenario | verdict |
|---|---|
| [in an unblock gated by the global role, the superadmin clears the block of a user by username](#unblocking-the-superadmin-unblocks-a-user) | answered |
| [a regular user granted READ and UPDATE on their own user is rejected by the global role gate when clearing their own block](#unblocking-a-regular-user-may-not-unblock-a-user) | rejected |

**my_revoke**

| scenario | verdict |
|---|---|
| [a user granted READ and UPDATE on their own user revokes their own login session](#revoking-a-user-granted-update-on-themselves-revokes-their-own-login-session) | answered |
| [a user granted only READ on their own user is rejected by the permission check when revoking their own login session](#revoking-a-user-granted-only-read-may-not-revoke-their-own-login-session) | rejected |

### admin_search

<a id="searching-the-superadmin-searches-every-users-login-sessions"></a>

#### [the-superadmin-searches-every-users-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

when the superadmin searches every session, gated by the global role, with a status filter, a status order and a page, the matching sessions of every user are counted and the session the filter excludes is left out

Given

- one domain, a superadmin caller, a user holding three sessions and a user holding one
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active
  - regular user user-2: has one login session in status revoked
  - regular user user-2: has one login session in status invalidated
  - Keypair policy keypair-policy-5: up to 5 concurrent sessions
  - regular user user-3: has one more active keypair besides the default one
  - regular user user-3: has one login session in status active

When

- LoginSessionAdapter.admin_search: user-1 searches every login session for active or revoked ones, by status descending, the first one only

Then

- of the 3 matching sessions the revoked one comes on the first page, and a next page follows
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as the session seeded in advance
  - items[0].field_id: same as the session seeded in advance
  - items[0].user_id: same as the session owner
  - items[0].access_key: same as the key that opened the session
  - items[0].status = 'revoked'
  - items[0].created_at: the time this run wrote
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

<a id="searching-a-regular-user-may-not-search-every-login-session"></a>

#### [a-regular-user-may-not-search-every-login-session](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

a regular user granted READ on their own user is rejected by the global role gate when searching every login session

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ permission on their own user
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
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.admin_search: user-1 searches every login session for active or revoked ones, by status descending, the first one only

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-granted-read-on-themselves-loads-their-own-login-sessions"></a>

#### [a-user-granted-read-on-themselves-loads-their-own-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_batch_loading.py): pass

when a user granted READ on their own user loads two of their own sessions by id, both come back

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ permission on their own user
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
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.batch_load_by_ids: user-1 loads their own active and revoked sessions by id together

Then

- both sessions come back in the order asked
  - length = 2
  - [0].id: same as the session seeded in advance
  - [0].field_id: same as the session seeded in advance
  - [0].user_id: same as the session owner
  - [0].access_key: same as the key that opened the session
  - [0].status = 'active'
  - [0].created_at: the time this run wrote
  - [0].last_accessed_at = None
  - [0].invalidated_at = None
  - [1].id: same as the session seeded in advance
  - [1].field_id: same as the session seeded in advance
  - [1].user_id: same as the session owner
  - [1].access_key: same as the key that opened the session
  - [1].status = 'revoked'
  - [1].created_at: the time this run wrote
  - [1].last_accessed_at = None
  - [1].invalidated_at = None

<a id="batch_loading-a-user-granted-read-on-themselves-is-denied-another-users-login-session"></a>

#### [a-user-granted-read-on-themselves-is-denied-another-users-login-session](/tests/scenario/bai_scenario/manager/login_session/test_batch_loading.py): pass

when a user granted READ on their own user loads their own session together with another user's, only the other user's session is rejected

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ permission on their own user
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
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.batch_load_by_ids: user-1 loads their own active session and the session of user-2 by id together

Then

- their own session comes back, and a rejection stands in the place of the other user's session
  - length = 2
  - [0].id: same as the session seeded in advance
  - [0].field_id: same as the session seeded in advance
  - [0].user_id: same as the session owner
  - [0].access_key: same as the key that opened the session
  - [0].status = 'active'
  - [0].created_at: the time this run wrote
  - [0].last_accessed_at = None
  - [0].invalidated_at = None
  - rejected: NotEnoughPermission

### my_search

<a id="searching-a-user-granted-read-on-themselves-searches-their-own-login-sessions"></a>

#### [a-user-granted-read-on-themselves-searches-their-own-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

when a user granted READ on their own user searches their own sessions with a status filter, a status order and a page, the session of another user and the session the filter excludes are left out

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ permission on their own user
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
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.my_search: user-1 searches their own login sessions for active or revoked ones, by status ascending, the first one only

Then

- of the 2 matching sessions the active one comes on the first page, and a next page follows
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as the session seeded in advance
  - items[0].field_id: same as the session seeded in advance
  - items[0].user_id: same as the session owner
  - items[0].access_key: same as the key that opened the session
  - items[0].status = 'active'
  - items[0].created_at: the time this run wrote
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

<a id="searching-a-user-granted-only-update-may-not-search-their-own-login-sessions"></a>

#### [a-user-granted-only-update-may-not-search-their-own-login-sessions](/tests/scenario/bai_scenario/manager/login_session/test_searching.py): pass

a user granted only UPDATE on their own user is rejected by the permission check when searching their own sessions

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.my_search: user-1 searches their own login sessions for active or revoked ones, by status ascending, the first one only

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_revoke

<a id="revoking-the-superadmin-revokes-another-users-login-session"></a>

#### [the-superadmin-revokes-another-users-login-session](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

in an admin revoke gated by the global role, the superadmin revokes the login session of another user

Given

- one domain, a superadmin caller, a user holding three sessions and a user holding one
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active
  - regular user user-2: has one login session in status revoked
  - regular user user-2: has one login session in status invalidated
  - Keypair policy keypair-policy-5: up to 5 concurrent sessions
  - regular user user-3: has one more active keypair besides the default one
  - regular user user-3: has one login session in status active

When

- LoginSessionAdapter.admin_revoke: user-1 revokes the active login session of user-2 through the admin call

Then

- the revoke succeeds
  - success = True

<a id="revoking-a-regular-user-may-not-revoke-a-login-session-as-admin"></a>

#### [a-regular-user-may-not-revoke-a-login-session-as-admin](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

a regular user granted READ and UPDATE on their own user is rejected by the global role gate when revoking their own login session through the admin call

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.admin_revoke: user-1 revokes the active login session of user-1 through the admin call

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_unblock_user

<a id="unblocking-the-superadmin-unblocks-a-user"></a>

#### [the-superadmin-unblocks-a-user](/tests/scenario/bai_scenario/manager/login_session/test_unblocking.py): pass

in an unblock gated by the global role, the superadmin clears the block of a user by username

Given

- one domain, a superadmin caller, a user holding three sessions and a user holding one
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active
  - regular user user-2: has one login session in status revoked
  - regular user user-2: has one login session in status invalidated
  - Keypair policy keypair-policy-5: up to 5 concurrent sessions
  - regular user user-3: has one more active keypair besides the default one
  - regular user user-3: has one login session in status active

When

- LoginSessionAdapter.admin_unblock_user: user-1 unblocks user-2

Then

- the unblock succeeds
  - success = True

<a id="unblocking-a-regular-user-may-not-unblock-a-user"></a>

#### [a-regular-user-may-not-unblock-a-user](/tests/scenario/bai_scenario/manager/login_session/test_unblocking.py): pass

a regular user granted READ and UPDATE on their own user is rejected by the global role gate when clearing their own block

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.admin_unblock_user: user-1 unblocks user-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### my_revoke

<a id="revoking-a-user-granted-update-on-themselves-revokes-their-own-login-session"></a>

#### [a-user-granted-update-on-themselves-revokes-their-own-login-session](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

a user granted READ and UPDATE on their own user revokes their own login session

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.my_revoke: user-1 revokes their own active login session

Then

- the revoke succeeds
  - success = True

<a id="revoking-a-user-granted-only-read-may-not-revoke-their-own-login-session"></a>

#### [a-user-granted-only-read-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/login_session/test_revoking.py): pass

a user granted only READ on their own user is rejected by the permission check when revoking their own login session

Given

- one domain, a caller holding three sessions and another user holding one, and the caller holds the READ permission on their own user
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
    - regular user user-1: holds Role user-role-1
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one login session in status active
  - regular user user-1: has one login session in status revoked
  - regular user user-1: has one login session in status invalidated
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one login session in status active

When

- LoginSessionAdapter.my_revoke: user-1 revokes their own active login session

Then

- the call is rejected
  - rejected: NotEnoughPermission

