---
name: auth-service-composition
type: decision-table
description: why the authentication domain's actions split into the global and user groups, what the three gateway-less connections verify their caller with, and why login session and SSH keypair operations are recorded per user
scope: src/ai/backend/manager/services/auth
keywords:
  - AuthProcessors
  - GlobalEntityType
  - anonymous_global
  - PublicActionProcessor
  - RevokeLoginSessionAction
sources:
  - src/ai/backend/manager/services/auth/processors.py
  - src/ai/backend/manager/api/rest/auth/registry.py
generated:
  by: claude-code/opus-5
  at: 2026-08-23
status: draft
---

# Authentication service — Knowledge

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## Why there are two groups

The `global` group takes operations that name no entity. Login and expired-password change
arrive before the caller has a principal. An admin revoking a login session or clearing a
login block reads no owner. The `user` group holds the operations over one user's rows, credentials and
login records.

## The three connections without a gate

`authorize`, `signup` and `update_password_no_auth` are connected as `anonymous_global`. All
three are on routes without the authentication middleware (`api/rest/auth/registry.py`), so
there is no caller context to check. The service checks the caller itself instead: a
password is compared against the secret the row holds. `signup` has no row to compare yet,
and the hook plugin decides the signup request.

`logout` is not one of them. The caller logging out already has a session, so the route
requires authentication and the action names that user. The session token stays a value
that chooses which session to end.

## Role lookup and access key scope resolution

`get_role` is a `single_entity` GET naming the requester.

`public_resolve_access_key_scope` finds the keypair owner by access key, mixed with the
requester's default keypair read and the delegation credential check, so it cannot be
connected as a lookup. Its entity is a user, so it is public in the user group. When
it names a delegation target, the service compares the roles and domains of the requester
and the target to decide.

## Login sessions and SSH keypairs are recorded per user

Neither row has a membership of its own and is read only through the owning user. So an
operation naming the user, such as logout, session revocation, or SSH keypair issuance and
upload, names that user with `single_entity` and declares `UPDATE`. Declaring `DELETE`
would mean deleting the user itself, and the permission is checked against that. Only
`signout`, which deactivates the account, is `DELETE`.

The admin-side revocation (`global_revoke_login_session`) reads no owner, so it cannot name
a user and is global behind the SUPERADMIN gate.

## Relation to the SSH keypair actions in the user domain

`admin_get_ssh_keypair`, `admin_register_ssh_keypair` and `admin_delete_ssh_keypair` in
`services/user` are the path where an admin names another user's keypair. The
`get_ssh_keypair`, `generate_ssh_keypair` and `upload_ssh_keypair` here are the operations
a logged-in user does on its own session's access key, and key generation exists only here.

## Login sessions and history are the user's field group

Both rows are field rows owned by the user, so a read comes from the sub-group that
`user_group.field_group(...)` provides. That group creates the owner lookup itself, and the
domain connects only the four reads. All four go through ops with the `LoginSessionSearcher`
and `LoginHistorySearcher` specs, without a service method.

The scope read is not `scope_search_ops` because the data it returns has to be
`EntityData`. A field row is not an entity, so it has no id to return, and
`ScopedFieldsOpsResult` is the item for it.

A scope read for a missing user raises `UserNotFound` as is, because ops runs the scope
existence check first.
