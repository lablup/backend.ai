---
name: user-adapter-scenarios
type: reference
description: what the user adapter and the login session and login history adapters it owns guarantee: gates, graph position, dependencies, external boundaries and response contents
scope: src/ai/backend/manager/api/adapters/user
keywords: [user, keypair, login session, login history, scenario, adapter, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-15
status: draft
---
# user adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. Login session and login history have their own adapters but are fields the user owns, so they are in this document.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

Paths are relative to `src/ai/backend/manager/` unless stated otherwise. The investigation base is main `a42719cb67`. The connection and call path reflect BA-7885 (assignment and role read moved to the scope) and BA-7889 (bulk user read as a partial bulk get).

## What the adapter provides

`./backend.ai mgr ops list --concern organization` yields 97 entries: user 46, domain 16, project 15, auth 7, and the field entries error_log 4, keypair 4, login_session 3, login_history 2. One project entry was added to the 96 at the time BA-7799 was written.

### The user adapter (`api/adapters/user/adapter.py`)

| Method | Line | Request | Response | Argument outside the request | Action |
|---|---|---|---|---|---|
| resolve_domain_id | 217 | — | `DomainID` | domain name | `LookupDomainAction` |
| batch_load_by_ids | 224 | — | `list[UserNode \| Exception \| None]` | user id list | `BulkGetUsersAction` |
| batch_lookup_by_emails | 240 | — | `list[UserID \| Exception]` | email list | `BulkLookupUsersAction` |
| gql_admin_search | 240 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | — | `GlobalSearchUsersAction` |
| gql_search_by_domain | 267 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | domain name | `LookupDomainAction`, `ScopedSearchUsersAction` |
| gql_search_by_project | 300 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | project id | `ScopedSearchUsersAction` |
| admin_search | 335 | `SearchUsersRequest` | `SearchUsersPayload` | — | `GlobalSearchUsersAction` |
| scoped_search | 362 | `ScopedSearchUsersInput` | `SearchUsersPayload` | — | `ScopedSearchUsersAction` |
| gql_scoped_search | 388 | `AdminSearchUsersInput` | `AdminSearchUsersPayload` | `UserScope` | `ScopedSearchUsersAction` |
| domain_search | 418 | `SearchUsersRequest` | `SearchUsersPayload` | domain name | `LookupDomainAction`, `ScopedSearchUsersAction` |
| project_search | 440 | `SearchUsersRequest` | `SearchUsersPayload` | project id | `ScopedSearchUsersAction` |
| role_search | 462 | `SearchUsersRequest` | `SearchUsersPayload` | role id | `GlobalSearchUsersAction` |
| get | 482 | — | `UserPayload` | user id | `GetUserAction` |
| create_user | 489 | `CreateUserInput` | `CreateUserPayload` | — | `LookupDomainAction`, `CreateUserAction` |
| update_user_by_id | 595 | `UpdateUserInput` | `UpdateUserPayload` | user id | `UpdateUserAction`, `SwitchDefaultAccessKeyAction` when a default key is given, and `GetUserAction`, `DeleteUserAction`, `RestoreUserAction` depending on `status` (table below) |
| delete_user_by_id | 626 | `DeleteUserInput` | `DeleteUserPayload` | — | `DeleteUserAction` |
| restore_user_by_id | 631 | `RestoreUserInput` | `RestoreUserPayload` | — | `RestoreUserAction` |
| purge_user_by_id | 636 | `PurgeUserInput` | `PurgeUserPayload` | admin user id | `PurgeUserAction` |
| bulk_create_users | 660 | `BulkCreateUserAction` | `BulkCreateUsersPayload` | — | `BulkCreateUserAction` |
| bulk_create_users_with_keypair | 679 | `BulkCreateUserAction` | `BulkCreateUsersWithKeypairPayload` | — | `BulkCreateUserAction` |
| bulk_update_users | 771 | `BulkUpdateUsersInput` | `BulkUpdateUsersPayload` | — | `BulkUpdateUserAction`, `SwitchDefaultAccessKeyAction`, and `BulkGetUsersAction`, `DeleteUserAction`, `RestoreUserAction`, `GetUserAction` depending on `status` |
| bulk_purge_users | 736 | `BulkPurgeUserAction` | `BulkPurgeUsersPayload` | — | `BulkPurgeUserAction` |
| update_user | 752 | `UpdateUserAction` | `UpdateMyAllowedClientIPPayload` | — | `UpdateUserAction` |
| issue_my_keypair | 759 | — | `IssueMyKeypairPayload` | user id | `IssueMyKeypairAction` |
| revoke_my_keypair | 769 | — | `RevokeMyKeypairPayload` | access key | `LookupKeypairByAccessKeyAction`, `PurgeKeypairAction` |
| update_my_keypair | 774 | — | `UpdateMyKeypairPayload` | access key, active flag | `LookupKeypairByAccessKeyAction`, `UpdateKeypairAction` |
| switch_default_access_key | 784 | — | `SwitchMyMainAccessKeyPayload` | user id, access key | `SwitchDefaultAccessKeyAction` |
| search_my_keypairs | 793 | `SearchMyKeypairsRequest` | `SearchResult[KeypairNode]` | current user context | `SearchMyKeypairsAction` |
| admin_create_keypair | 864 | `AdminCreateKeypairInput` | `AdminCreateKeypairPayload` | — | `AdminCreateKeypairAction` |
| admin_update_keypair | 902 | `AdminUpdateKeypairInput` | `AdminUpdateKeypairPayload` | — | `LookupKeypairByAccessKeyAction`, `UpdateKeypairAction` |
| admin_delete_keypair | 917 | — | `AdminDeleteKeypairPayload` | access key | `LookupKeypairByAccessKeyAction`, `PurgeKeypairAction` |
| admin_get_keypair | 921 | — | `KeypairNode` | access key | `LookupKeypairByAccessKeyAction`, `GetKeypairAction` |
| admin_register_ssh_keypair | 928 | `AdminRegisterSSHKeypairInput` | `AdminRegisterSSHKeypairPayload` | — | `LookupKeypairOwnerByAccessKeyAction`, `AdminRegisterSSHKeypairAction` |
| admin_delete_ssh_keypair | 942 | — | `AdminDeleteSSHKeypairPayload` | access key | `LookupKeypairOwnerByAccessKeyAction`, `AdminDeleteSSHKeypairAction` |
| admin_get_ssh_keypair | 951 | — | `AdminGetSSHKeypairPayload` | access key | `LookupKeypairOwnerByAccessKeyAction`, `AdminGetSSHKeypairAction` |
| admin_search_keypairs | 965 | `AdminSearchKeypairsInput` | `AdminSearchKeypairsPayload` | — | `AdminSearchKeypairsAction` |
| gql_admin_search_keypairs | 995 | `AdminSearchKeypairsInput` | `SearchResult[KeypairNode]` | resource policy name (optional) | `AdminSearchKeypairsAction` |

Every method that returns a user node calls `GetDefaultKeypairsAction` one more time at the end (`adapter.py:1633-1649`). The gate in the next section applies there too.

`bulk_*` and `update_user` receive the action as the request. Converting it is the job of the GQL resolver (`api/gql/user/resolver/mutation.py:178,210,369,561,645`).

### `status` in an update request

update_user_by_id and bulk_update_users split `status` by the same rule (`adapter.py:626-641`). The rule is the three members `deletes_from`, `restores_from` and `is_updater_value_from` of `UserStatus` (`data/user/types.py:57-67`). The legacy GQL `modify_user` and the legacy REST `PATCH /admin/users/{user_id}` use the same three in the same order. The bulk splits per entry and puts a failure in the `failed` of that entry.

| Given `status` | Current status | Behavior |
|---|---|---|
| DELETED | not DELETED | update the other fields, then `DeleteUserAction` after switching the default key. The response is the user read afterwards |
| DELETED | DELETED | nothing is applied. When other fields are present, the update is blocked by `UserDeleted` |
| ACTIVE | DELETED | `RestoreUserAction`, then update the other fields |
| ACTIVE, INACTIVE | other | `UserUpdater` writes |
| BEFORE_VERIFICATION | any | `UserUpdater` blocks it with `UserModificationBadRequest` (`models/user/updaters.py:54-59`) |

- DELETED is deprecated. The input description says it is handled as delete and restore. It is removed in the next LTS.
- Delete and restore receive the permission of each action (user SOFT_DELETE) separately. A user who received only UPDATE and gives DELETED gets `NotEnoughPermission`.
- `UserUpdater` holds two guards that block a deleted status and a user being purged (`models/user/updaters.py:75-87`). The repository loads the guards on the update call and raises the exception of the first blocking guard (`db_source.py:360-371`).

### The login session adapter (`api/adapters/login_session/adapter.py`)

| Method | Line | Request | Response | Argument outside the request | Action |
|---|---|---|---|---|---|
| admin_search | 67 | `AdminSearchLoginSessionsInput` | `AdminSearchLoginSessionsPayload` | — | `GlobalSearchLoginSessionsAction` |
| my_search | 96 | `MySearchLoginSessionsInput` | `MySearchLoginSessionsPayload` | current user context | `SearchLoginSessionsAction` |
| my_revoke | 127 | `MyRevokeLoginSessionInput` | `RevokeLoginSessionPayload` | — | `RevokeLoginSessionAction` |
| admin_revoke | 134 | `AdminRevokeLoginSessionInput` | `RevokeLoginSessionPayload` | — | `GlobalRevokeLoginSessionAction` |
| admin_unblock_user | 143 | `AdminUnblockUserInput` | `UnblockUserPayload` | — | `GlobalUnblockUserAction` |

### The login history adapter (`api/adapters/login_history/adapter.py`)

| Method | Request | Response | Argument outside the request | Action |
|---|---|---|---|---|
| admin_search | `AdminSearchLoginHistoryInput` | `AdminSearchLoginHistoryPayload` | — | `GlobalSearchLoginHistoryAction` |
| my_search | `MySearchLoginHistoryInput` | `MySearchLoginHistoryPayload` | current user context | `SearchLoginHistoryAction` |

## What blocks a call

### Gates and exceptions

| Gate | Connection kind | Rejection | Superadmin | With enforcement off | Source |
|---|---|---|---|---|---|
| global role | `global_scope`, `global_search_ops` | `InsufficientPrivilege` | passes. A monitor passes GET, SEARCH and LOOKUP only | blocks as before | `actions/v2/global_scope/processor.py:51`, `superadmin.py:22-34`, `actions/types.py:106` |
| entity permission | `single_entity`, field `single_field` | `NotEnoughPermission` | passes | passes | `actions/v2/single_entity/validator/rbac.py:33-54` |
| entity permission, owner lookup step | `key_field_lookup_ops`, `key_owner_lookup_ops` | `GenericBadRequest`. A missing key and no permission give the same exception | passes. A missing key is `FieldNotFoundError` | the permission passes, a missing key is still `GenericBadRequest` | `actions/v2/lookup/processor.py:99-110,132-146` |
| scope permission | `scope`, `scope_search_ops`, field `search_ops` | `NotEnoughPermission`. When even one of several scopes is blocked, all are rejected | passes | passes | `actions/v2/scope/validator/rbac.py:38-66` |
| input validation | none. The service and the repository raise it while running | differs per case | not applicable | not applicable | the table below |

- The enforcement switch is `manager.rbac.enforcement_enabled`, True by default (`config/unified.py:630-650`).
- A permission maps GET, SEARCH and LOOKUP to READ, DELETE and RESTORE to SOFT_DELETE, and PURGE to HARD_DELETE (`actions/types.py:160-182`).
- The permission check runs before execution. A user who is not superadmin receives `NotEnoughPermission` even when the target is missing. A row that sees a missing target must be run by superadmin or with enforcement off.
- There is no exception for the user themself. The only conditions the checker skips are superadmin and enforcement off (`single_entity/validator/rbac.py:35-54`). A user who issues their own key must also hold the permission on their own user.
- The permission of a keypair, a login session and a login history is read as the user entity permission on the owning user. The permission query reads only rows with `entity_type == user` applied to every field (`repositories/ops/v2/permission/read.py:212-215`).

### Per method

| Method | Gates (in order) | Permission target | Rejection |
|---|---|---|---|
| resolve_domain_id | authentication only | — | an unknown name is `EntityNotFoundError` (`repositories/ops/repository.py:127-132`). It is not a user scenario, so the scenario table has no row (open questions) |
| batch_load_by_ids | entity permission, per element | READ on each user | per element. The table under the values section |
| batch_lookup_by_emails | authentication, then entity permission per key (`bulk_lookup_ops`) | READ on each found user | a missing email and the email of an unreadable user are both a `GenericBadRequest` element. For superadmin a missing email is an `EntityNotFoundError` element |
| gql_admin_search, admin_search | global role | — | `InsufficientPrivilege` |
| role_search | global role | — | `InsufficientPrivilege`. Unlike its name it is not a scope search but a global search with a role condition (`adapter.py:469-470`) |
| gql_search_by_domain, domain_search | authentication (domain name lookup), then scope permission | user READ on the domain scope | `EntityNotFoundError`, `NotEnoughPermission` |
| gql_search_by_project, project_search | scope permission | user READ on the project scope | `NotEnoughPermission` |
| scoped_search, gql_scoped_search | scope permission, per item | user READ on each of the domain, project and role scopes (`services/user/actions/scoped_search.py:40-77,106-107`) | `NotEnoughPermission` |
| get | entity permission | user READ | `NotEnoughPermission` |
| create_user | authentication (domain name lookup), then scope permission, then input validation | user CREATE on the domain scope (`create_user.py:39-40`) | `EntityNotFoundError`, `NotEnoughPermission`, `UserConflict` |
| update_user_by_id | entity permission, then input validation | user UPDATE. Giving DELETED, or ACTIVE to a deleted user, also needs user SOFT_DELETE, and READ to read the status then | `NotEnoughPermission`, `UserModificationBadRequest`, `UserNotFound`, `UserDeleted`, `UserPurgeInProgress`, and `KeyPairNotFound` or `KeyPairForbidden` on the default key switch |
| delete_user_by_id, restore_user_by_id | entity permission, then input validation | user SOFT_DELETE | `NotEnoughPermission`, and restore_user_by_id gives `UserModificationBadRequest` to a user not in the deleted status |
| purge_user_by_id | entity permission, then input validation | user HARD_DELETE | `NotEnoughPermission`, `UserNotFound` without the admin id (`services/user/service.py:186`), and `UserPurgeFailure` when a vfolder is attached to an active kernel |
| bulk_create_users, bulk_create_users_with_keypair | global role, then input validation | superadmin only (a monitor cannot write) | `InsufficientPrivilege`; a per-entry failure goes into the response |
| bulk_update_users, bulk_purge_users | global role, then input validation | superadmin only | `InsufficientPrivilege`; a per-entry failure goes into the response. The delete and restore of bulk_update_users check the entity permission separately per entry |
| update_user | entity permission | user UPDATE | `NotEnoughPermission` |
| issue_my_keypair | entity permission | user UPDATE | `NotEnoughPermission` |
| switch_default_access_key | entity permission, then input validation | user UPDATE | `NotEnoughPermission`, `KeyPairForbidden` for another user's key or an inactive key, `KeyPairNotFound` for a missing key (`repositories/user/db_source/db_source.py:920-929`) |
| search_my_keypairs | scope permission | user READ on the user's own scope (`keypair_ops.py:183-188`) | `NotEnoughPermission` |
| admin_create_keypair | entity permission, then input validation | UPDATE on the target user. Unlike its name it is not a global role gate | `NotEnoughPermission`, `KeypairResourcePolicyNotFound` |
| revoke_my_keypair, admin_delete_keypair | owner lookup, then entity permission, then input validation | owner READ, then owner UPDATE | `GenericBadRequest`, `NotEnoughPermission`, `KeyPairForbidden` for the default key (`models/keypair/purgers.py:43-51`) |
| update_my_keypair, admin_update_keypair | owner lookup, then entity permission, then input validation | owner READ, then owner UPDATE | `GenericBadRequest`, `NotEnoughPermission`, `KeyPairForbidden` when the default key is deactivated (`models/keypair/updaters.py:121-131`), `KeypairResourcePolicyNotFound` for a missing policy |
| admin_get_keypair | owner lookup, then entity permission | owner READ twice | `GenericBadRequest` |
| admin_register_ssh_keypair, admin_delete_ssh_keypair | owner lookup, then entity permission | owner READ, then owner UPDATE | `GenericBadRequest`, `NotEnoughPermission` |
| admin_get_ssh_keypair | owner lookup, then entity permission | owner READ twice | `GenericBadRequest` |
| admin_search_keypairs, gql_admin_search_keypairs | global role | — | `InsufficientPrivilege` |
| login_session.admin_search, login_history.admin_search | global role | — | `InsufficientPrivilege` |
| login_session.my_search, login_history.my_search | scope permission | user READ on the user's own scope (`services/auth/actions/search_login_sessions.py:47-53`) | `NotEnoughPermission` |
| login_session.my_revoke | owner lookup, then entity permission | owner READ, then owner UPDATE | `GenericBadRequest`, `NotEnoughPermission` |
| login_session.admin_revoke | global role, then input validation | superadmin only | `InsufficientPrivilege`, `LoginSessionNotFoundError` for a missing session (`repositories/auth/db_source/db_source.py:766-769`) |
| login_session.admin_unblock_user | global role | superadmin only | `InsufficientPrivilege` |

Every method that returns a user node needs READ one more time for every user in the response. `GetDefaultKeypairsAction` checks all owners at once, and when one is blocked the whole call ends with `NotEnoughPermission` (`actions/v2/bulk/validator/rbac.py:91-98`). A user who received only the create permission does not receive the created user in the response.

## Position in the graph

A user is created inside the domain scope. The create gate is user CREATE on the domain scope (`create_user.py:39-40`). A scenario with a user who received a permission therefore holds.

- The virtual entity of the user themself owns and governs the user (`repositories/ops/v2/graph_write.py:59-74`). A role placed on the user scope that grants the user permission passes both the entity permission check and the scope permission check on that user.
- The domain owns and governs the user (`graph_write.py:146-176`). A role placed on the domain scope reaches every user of that domain.
- The preset role of the user scope is created (`repositories/ops/v2/entity_write.py:131,323-360`). The owner preset has `auto_assign: true` and is assigned to the user at creation (`seeds/manager/role_preset/user-owner.yaml:7`, `repositories/ops/v2/user/write.py:99-101`). The migration `dc61fa027fc1` assigned it to users created before that.
- The scenario template database has no preset row, so no preset role is created (`entity_write.py:379-380`). A scenario seeds the roles it needs directly.

## Values not in the request

| Value | Where it comes from | Source |
|---|---|---|
| keypair resource policy | reads the one policy carrying the default marker. This read is to be replaced and is not covered by a scenario | `db_source.py:159-166` |
| user resource policy | the default `"default"` of the request | `common/dto/manager/v2/user/request.py:89-92`, `models/user/creators.py:116` |
| resource policy of the personal project | the name `"default"` fixed by the code | `models/project/creators.py:66-67` |
| personal project name | the user name. On a collision `-2` through `-999`, and on a further collision the user id | `repositories/ops/v2/user/write.py:175-199` |
| access key, secret key | created. The secret is encrypted with the key provider pool | `common/auth/keypair.py`, `repositories/auth/keypair_secrets.py` |
| default SSH keypair | created with the user in the same transaction. The private key is encrypted with the key provider pool | `repositories/auth/keypair_secrets.py`, `repositories/ops/v2/user/write.py` |
| active and admin markers of the default keypair | whether the user status is ACTIVE and whether the role is SUPERADMIN or ADMIN | `write.py:106-107` |
| password hash setting | the manager setting `auth.password_hash_*` | `adapter.py:491-496` |
| domain id | read by name | `adapter.py:217-220` |
| active flag, admin flag, policy and rate limit of a newly issued keypair | follow the default key of the user | `db_source.py:896-901` |
| admin user of the admin purge | an argument outside the request. It receives the shared vfolders and deployment endpoints | `services/user/service.py:185-259` |

## The composed operation that must be written whole

`V2UserWriteOps.create_user(FullUserCreator)` (`repositories/ops/v2/user/write.py:84-111`). The adapter create and the scenario seed (`tests/scenario/bai_scenario/seeds/user/user.py`) use the same operation.

| Order | Row written | Source |
|---|---|---|
| 1 | domain virtual entity (only when absent) | `write.py:87`, `graph_write.py:44-69` |
| 2 | user row | `entity_write.py:127-128` |
| 3 | user virtual entity, self membership, scope link | `entity_write.py:130` |
| 4 | preset role and permissions of the user scope | `entity_write.py:131,323-360` |
| 5 | row where the domain owns and governs the user | `entity_write.py:132`, `graph_write.py:146-176` |
| 6 | assignment of the auto-assign roles of the user scope and the domain scope | `write.py:92`, `entity_write.py:296-319` |
| 7 | default keypair | `write.py:93,97-111` |
| 8 | personal project, its preset role and domain ownership | `write.py:94,146-165` |
| 9 | entry of the personal project in the member list | `write.py:164`, `repositories/ops/v2/roster/write.py:191-198` |

The adapter path adds two steps around this. Inside the same write transaction it first checks the email and user name for duplicates (`db_source.py:188-191`), and afterwards registers in the projects of the request and in the model store project of the domain (`write.py:113-124,213-226`).

| Item | seed | Adapter create |
|---|---|---|
| duplicate check | none | present |
| keypair policy | the policy the earlier step created | read of the default-marked policy (to be replaced) |
| key values | plaintext | created, encrypted |
| project registration | none | present |

## Dependencies the adapter requires

The four searches answer through ops without going through the service (`services/auth/processors.py:211-218`).

## External service boundary

No path reaches agent RPC.

## What the response contains

The default is a whole-node comparison. The items below either cannot state a value or are read as a condition.

### User node

| Item | Check |
|---|---|
| `id` | ignored. The database creates it |
| `basic_info.*`, `status.status`, `status.need_password_change`, `organization.role`, `organization.resource_policy`, `security.allowed_client_ip`, `security.totp_activated`, `security.sudo_session_enabled`, `container.*` | same as the request value or the default written in the values section and the open questions |
| `status.status_info` | None right after creation, `"admin-requested"` after a status change (`db_source.py:317-319,347-363`) |
| `organization.domain_name` | same as the domain name the earlier step created |
| `organization.main_access_key` | same as the default key of that user. None when the default key is inactive (`models/keypair/queriers.py:28-29`) |
| `security.totp_activated_at` | None |
| `timestamps.created_at`, `timestamps.modified_at` | the time this run wrote |

### Keypair node

| Item | Check |
|---|---|
| `id`, `access_key` | ignored for a created key. Equal to the seeded key for a seeded one |
| `is_active`, `is_admin`, `is_default`, `rate_limit`, `resource_policy` | read as values |
| `num_queries` | 0 |
| `last_used` | None |
| `ssh_public_key` | deprecated. The public key of the owner's default SSH keypair, the same for every keypair of one user |
| `created_at`, `modified_at` | the time this run wrote |
| `user_id` | same as the owning user |
| secret key in the issue response | ignored. Created anew each time |

### List response

| Item | Check |
|---|---|
| `items` | compared by the list of names or access keys of the seeded rows. A search that does not guarantee order is sorted by name before comparison |
| order | rows seeded in one transaction have the same creation time. The tie order after creation time descending decides the order: users by id, keypairs by access key, login sessions and histories by id, all ascending |
| `total_count`, `pagination.total` | value |
| `has_next_page`, `has_previous_page` | value |
| `pagination.offset`, `pagination.limit` | value. The unscoped keypair search returns None when limit is omitted (`adapter.py:988-992`) |

### Responses that contain only success

`DeleteUserPayload`, `RestoreUserPayload`, `PurgeUserPayload`, `RevokeMyKeypairPayload`, `SwitchMyMainAccessKeyPayload`, `UpdateMyAllowedClientIPPayload`, `RevokeLoginSessionPayload` and `UnblockUserPayload` contain only `success`. With the response, these rows call the get of the same adapter afterwards and check that the changed result is read. The "afterwards" read in the expected column of the scenario table is that.

## Open questions

1. **Five of the seven auth entries do not go through an adapter.** The login session adapter calls `global_revoke_login_session` and `global_unblock_user` (`api/adapters/login_session/adapter.py:136,145`). The REST handler calls the processor directly for the other five. `authorize`, `get_role` and `update_password_no_auth` are in `api/rest/auth/handler.py`, and `public_resolve_access_key_scope` is in `api/rest/session/handler.py`; the five span three files. The email delegation of the vfolder list calls `LookupUserAction` (`api/rest/vfolder/handler.py`). `authorize` and `update_password_no_auth` include the request object in the action (`services/auth/actions/authorize.py`). This work does not move the handler calls to an adapter, and defers the scenarios of the five.
2. **Add write specs for the login session and login history.** Today there is only the raw insert of the authentication flow (`repositories/auth/db_source/db_source.py:557-597`). Put the two field creators under `models/login_session/` and seed the scenarios through `adding`. The added scope is explained separately in the implementation step.
3. **The permission target of a role scope item.** Giving a role scope to the scope search checks user READ with the role id as the scope (`services/user/actions/scoped_search.py:70-77`). Whether a permission given on the scope that governs the role passes that check could not be verified, so the scenario table has no row.
4. **An empty value in the membership project item does nothing.** The request description says "empty empties it" (`common/dto/manager/v2/user/request.py:149`), but the adapter ignores it (`adapter.py:615-619`). The scenario table fixes the current behavior as a row. Settle which of the description and the behavior to change.
5. **Purge does not require the deleted state first.** There is no status check (`services/user/service.py:185-259`). Whether this is intended could not be verified.
6. **The exception when superadmin reads or updates a missing user.** The read is `UserNotFound` per the docstring (`service.py:179-180`), but the repository was not followed. The scenario table has no row.
7. **The membership sync and the default key switch of a user update run in a transaction different from the update.** A failed default key switch keeps the earlier update (`adapter.py:621-623`, `db_source.py:697-711`). Settle whether to record this partial failure as a row.
8. **The method that gets a domain id from a domain name is not a user scenario.** `resolve_domain_id` (`adapter.py:217-220`) only reads a domain, so the scenario table has no row for it and it remains in the report's list of uncalled calls. Inside the adapter, create and the domain search use it, and outside it is called by the bulk create resolver (`api/gql/user/resolver/mutation.py:122`). If that call moves elsewhere, it can become private.
9. **A scenario does not look at the history a login session revocation writes.** Revocation deletes the session row and writes one history row of the user revocation or the admin revocation result (`repositories/auth/db_source/db_source.py:744-786`). One scenario row receives one adapter only and cannot read afterwards through the history adapter.
10. **The documents of the login session adapter and the login history adapter.** The two packages have no `KNOWLEDGE.md`, and this document covers them. Settle whether to add a document that refers to this one and how to align the report being split into the two packages.
