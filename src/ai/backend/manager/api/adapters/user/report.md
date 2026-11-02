## user

[background](/src/ai/backend/manager/api/adapters/user/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/user/adapter.py)

Scenario: incomplete 8 / 48

- built from ops (23)
  - LoginHistoryAdapter.admin_search: representative success ✓ · representative rejection ✓
  - LoginHistoryAdapter.batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - LoginHistoryAdapter.my_search: representative success ✓ · representative rejection ✓
  - LoginSessionAdapter.admin_search: representative success ✓ · representative rejection ✓
  - LoginSessionAdapter.batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - LoginSessionAdapter.my_search: representative success ✓ · representative rejection ✓
  - UserAdapter.admin_search: representative success ✓ · representative rejection ✓
  - UserAdapter.admin_search_keypairs: representative success ✓ · representative rejection ✓
  - UserAdapter.batch_load_by_ids: representative success ✓ · representative rejection ✓
  - UserAdapter.batch_lookup_by_emails: representative success ✓ · representative rejection ✓
  - UserAdapter.bulk_get_keypair_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - UserAdapter.bulk_lookup_keypair_access_keys: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - UserAdapter.domain_search: representative success ✓ · representative rejection ✓
  - UserAdapter.gql_admin_search: representative success ✓ · representative rejection ✓
  - UserAdapter.gql_admin_search_keypairs: representative success ✓ · representative rejection ✓
  - UserAdapter.gql_scoped_search: representative success ✓ · representative rejection ✓
  - UserAdapter.gql_search_by_domain: representative success ✓ · representative rejection ✓
  - UserAdapter.gql_search_by_project: representative success ✓ · representative rejection ✓
  - UserAdapter.project_search: representative success ✓ · representative rejection ✓
  - UserAdapter.resolve_domain_id: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - UserAdapter.role_search: representative success ✓ · representative rejection ✓
  - UserAdapter.scoped_search: representative success ✓ · representative rejection ✓
  - UserAdapter.search_my_keypairs: representative success ✓ · representative rejection ✓
- ops + direct implementation (7)
  - UserAdapter.bulk_create_users: success absent · rejection present 1 (atomic_bulk_get_ops, global_scope): SCENARIO-GAP
  - UserAdapter.bulk_create_users_with_keypair: success absent · rejection present 1 (atomic_bulk_get_ops, global_scope): SCENARIO-GAP
  - UserAdapter.bulk_update_users: success present 3 · rejection present 1 (atomic_bulk_get_ops, global_scope, partial_bulk_get_ops, single_entity)
  - UserAdapter.create_user: success absent · rejection present 2 (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - UserAdapter.delete_user_by_id: success present 1 · rejection present 1 (atomic_bulk_get_ops, single_entity)
  - UserAdapter.get: success present 1 · rejection present 1 (atomic_bulk_get_ops, single_entity)
  - UserAdapter.update_user_by_id: success present 7 · rejection present 6 (atomic_bulk_get_ops, single_entity)
- direct implementation (18)
  - LoginSessionAdapter.admin_revoke: success present 1 · rejection present 2 (global_scope)
  - LoginSessionAdapter.admin_unblock_user: success present 2 · rejection present 1 (global_scope)
  - LoginSessionAdapter.my_revoke: success present 1 · rejection present 3 (single_field)
  - UserAdapter.admin_create_keypair: success present 1 · rejection present 2 (single_entity)
  - UserAdapter.admin_delete_keypair: success present 1 · rejection present 3 (single_field)
  - UserAdapter.admin_delete_ssh_keypair: success present 1 · rejection present 2 (single_entity)
  - UserAdapter.admin_get_keypair: success present 1 · rejection present 1 (single_field)
  - UserAdapter.admin_get_ssh_keypair: success present 1 · rejection present 1 (single_entity)
  - UserAdapter.admin_register_ssh_keypair: success present 1 · rejection present 2 (single_entity)
  - UserAdapter.admin_update_keypair: success present 1 · rejection present 3 (single_field)
  - UserAdapter.bulk_purge_users: success present 2 · rejection present 1 (global_scope)
  - UserAdapter.issue_my_keypair: success present 2 · rejection present 1 (single_entity)
  - UserAdapter.purge_user_by_id: success present 1 · rejection present 2 (single_entity)
  - UserAdapter.restore_user_by_id: success present 1 · rejection present 2 (single_entity)
  - UserAdapter.revoke_my_keypair: success present 1 · rejection present 4 (single_field)
  - UserAdapter.switch_default_access_key: success present 1 · rejection present 2 (single_entity)
  - UserAdapter.update_my_keypair: success present 1 · rejection present 3 (single_field)
  - UserAdapter.update_user: success present 1 · rejection present 1 (single_entity)

**LoginHistoryAdapter.admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches in a history search gated by the global role, every record seeded in advance comes back in descending creation time regardless of the user](#login_history-the-superadmin-searches-every-users-login-history) | answered |
| [a user holding the permission is rejected by the global role gate when searching every history record](#login_history-a-user-who-is-not-the-superadmin-may-not-search-every-login-history) | rejected |

**LoginHistoryAdapter.my_search**

| scenario | verdict |
|---|---|
| [when a user granted READ in their own scope searches, the history of other users is left out](#login_history-a-user-granted-read-on-themselves-searches-only-their-own-login-history) | answered |
| [a user holding no role who tries to search their own history is rejected by the scope permission gate even for themselves](#login_history-a-user-granted-nothing-may-not-search-their-own-login-history) | rejected |

**LoginSessionAdapter.admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches without page arguments in a session search gated by the global role, every session seeded in advance comes back in descending creation time regardless of the user](#login_sessions-the-superadmin-searches-every-users-login-sessions) | answered |
| [a user holding the permission is rejected by the global role gate when searching every login session](#login_sessions-a-user-who-is-not-the-superadmin-may-not-search-every-login-session) | rejected |

**LoginSessionAdapter.my_search**

| scenario | verdict |
|---|---|
| [when a user granted READ in their own scope searches, the sessions of other users are left out](#login_sessions-a-user-granted-read-on-themselves-searches-only-their-own-login-sessions) | answered |
| [a user holding no role who tries to search their own sessions is rejected by the scope permission gate even for themselves](#login_sessions-a-user-granted-nothing-may-not-search-their-own-login-sessions) | rejected |

**UserAdapter.admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches without a filter in a search gated by the global role, every user seeded in advance comes back, deleted ones included](#searching-the-superadmin-searching-every-user-counts-deleted-ones-too) | answered |
| [even a user granted permission in the domain scope is rejected by the global role gate when searching every user](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-user) | rejected |

**UserAdapter.admin_search_keypairs**

| scenario | verdict |
|---|---|
| [when the superadmin searches without page arguments in a key search gated by the global role, every user's key comes back and the limit field comes back empty](#managing_keypairs-the-superadmin-searching-every-key-gets-every-users-key) | answered |
| [a user holding the permission is rejected by the global role gate when searching every key](#managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key) | rejected |

**UserAdapter.batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user holding no permission gives an empty id list, no action is called and an empty list comes back](#reading-a-batch-load-of-no-ids-answers-an-empty-list) | answered |
| [when the superadmin requests an existing id and a missing id together, it passes the permission gate and the missing element comes back empty](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |
| [when a user granted read on only one user requests a readable user, an unreadable user, and a missing id at once, a result comes back for each element in input order](#reading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order) | rejected |

**UserAdapter.batch_lookup_by_emails**

| scenario | verdict |
|---|---|
| [when a user granted the user read permission in the target user scope looks up that user's email, the id of that user comes back](#reading-a-user-granted-read-on-another-user-looks-up-their-id-by-email) | answered |
| [when a user holding no permission gives an empty email list, no action is called and an empty list comes back](#reading-an-email-lookup-of-no-emails-answers-an-empty-list) | answered |
| [when a user granted read on only one user looks up a readable user, an unreadable user, and a missing email at once, the first comes back as an id and the other two come back with the same rejection in input order](#reading-an-unreadable-user-and-a-missing-email-are-refused-alike) | rejected |

**UserAdapter.domain_search**

| scenario | verdict |
|---|---|
| [when a user granted user READ in the domain scope searches by domain name, the users of other domains are left out](#searching-a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users) | answered |
| [a user holding no role who tries to search by domain name is rejected by the scope permission gate](#searching-a-user-granted-nothing-may-not-search-a-domain-by-name) | rejected |
| [when a user holding the permission searches by a domain name nothing answers to, the name lookup step rejects it as not found before the scope check](#searching-searching-a-domain-name-nothing-answers-to-is-not-found) | rejected |

**UserAdapter.gql_admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches omitting both the cursor and the page arguments, up to ten users come back in descending creation time along with the next page flag](#searching-a-gql-search-without-page-arguments-answers-the-newest-ten) | answered |
| [a user holding the permission is rejected by the global role gate when searching every user over GQL](#searching-a-user-who-is-not-the-superadmin-may-not-gql-search-every-user) | rejected |

**UserAdapter.gql_admin_search_keypairs**

| scenario | verdict |
|---|---|
| [when the superadmin gives a policy name in a GQL key search gated by the global role, only the keys under that policy come back](#managing_keypairs-the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only) | answered |
| [a user holding the permission is rejected by the global role gate when searching keys over GQL](#managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql) | rejected |

**UserAdapter.gql_scoped_search**

| scenario | verdict |
|---|---|
| [a GQL scoped search under the same permission brings back the users of both scopes in the cursor response](#searching-a-gql-scoped-search-over-two-granted-scopes-joins-their-users) | answered |
| [when a user granted READ on only one scope gives two scopes to a GQL scoped search, the scope permission gate rejects all of them](#searching-one-scope-without-a-grant-refuses-the-whole-gql-scoped-search) | rejected |

**UserAdapter.gql_search_by_domain**

| scenario | verdict |
|---|---|
| [a GQL domain search under the same permission brings back only the users of that domain in the cursor response](#searching-a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users) | answered |
| [a GQL domain search from a user holding no role is rejected by the scope permission gate](#searching-a-user-granted-nothing-may-not-gql-search-a-domain) | rejected |

**UserAdapter.gql_search_by_project**

| scenario | verdict |
|---|---|
| [a GQL project search under the same permission brings back only the users on the roster in the cursor response](#searching-a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster) | answered |
| [a GQL project search from a user holding no role is rejected by the scope permission gate](#searching-a-user-granted-nothing-may-not-gql-search-a-project) | rejected |

**UserAdapter.project_search**

| scenario | verdict |
|---|---|
| [when a user granted user READ in the project scope searches by that project, only the users on its roster come back](#searching-a-user-granted-on-a-project-searching-it-finds-only-its-roster) | answered |
| [a project search from a user holding no role is rejected by the scope permission gate](#searching-a-user-granted-nothing-may-not-search-a-project) | rejected |

**UserAdapter.role_search**

| scenario | verdict |
|---|---|
| [when a user granted user READ in the scope that holds the role gives one role, only the user assigned that role comes back](#searching-a-user-granted-on-the-role-scope-searching-by-role-finds-only-its-holders) | answered |
| [when the superadmin gives one role in a role search gated by the global role, only the user assigned that role comes back](#searching-the-superadmin-searching-by-role-finds-only-its-holders) | answered |
| [a user holding no permission who tries to search by role is rejected by the scope permission gate](#searching-a-user-granted-nothing-may-not-search-by-role) | rejected |

**UserAdapter.scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted READ in both the domain scope and the project scope gives both scopes, the users of the two scopes are joined without duplicates](#searching-a-scoped-search-over-two-granted-scopes-joins-their-users) | answered |
| [when a user holding the permission runs a scoped search without page arguments, limit 50 and offset 0 are carried in the response](#searching-a-scoped-search-without-page-arguments-answers-up-to-fifty) | answered |
| [when a user granted READ on only the first scope gives two scopes, the scope permission gate rejects all of them](#searching-one-scope-without-a-grant-refuses-the-whole-scoped-search) | rejected |

**UserAdapter.search_my_keypairs**

| scenario | verdict |
|---|---|
| [when a user granted READ in their own scope searches their own keys, the keys of other users are left out](#own_keypairs-a-user-granted-read-searching-their-keys-sees-only-their-own) | answered |
| [when a user holding the permission searches without page arguments, ten keys in descending creation time and the next page flag come back](#own_keypairs-searching-own-keys-without-page-arguments-answers-the-ten-newest) | answered |
| [a user holding no role who tries to search their own keys is rejected by the scope permission gate](#own_keypairs-a-user-granted-nothing-may-not-search-their-own-keys) | rejected |

**UserAdapter.bulk_create_users**

| scenario | verdict |
|---|---|
| [even a user granted CREATE in the domain scope is rejected by the global role gate when bulk creating users](#creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users) | rejected |

**UserAdapter.bulk_create_users_with_keypair**

| scenario | verdict |
|---|---|
| [a user holding the permission is rejected by the global role gate when calling this bulk create](#creating-a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs) | rejected |

**UserAdapter.bulk_update_users**

| scenario | verdict |
|---|---|
| [when the superadmin bulk edits with DELETED for an active user, ACTIVE for a deleted user, and a full name for another deleted user, the first two are deleted and restored and come back in the updated list, and the third comes back as failed](#retiring-a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit) | answered |
| [when the superadmin gives a default key switch to another user's key along with a bulk edit, that user leaves the updated list and comes back as failed](#editing-a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed) | answered |
| [when the superadmin gives one user to update and one to rename into a taken name in a bulk edit gated by the global role, one is updated and one comes back as failed with its user id](#editing-the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart) | answered |
| [even a user granted UPDATE in the domain scope is rejected by the global role gate when bulk editing users](#editing-a-user-who-is-not-the-superadmin-may-not-bulk-edit-users) | rejected |

**UserAdapter.create_user**

| scenario | verdict |
|---|---|
| [a user holding no role who tries to create a user is rejected by the domain scope permission gate](#creating-a-user-granted-nothing-may-not-create-a-user) | rejected |
| [when a user holding the permission gives a domain name nothing answers to, the domain name lookup step rejects it as not found](#creating-a-user-may-not-be-created-in-a-domain-name-nothing-answers-to) | rejected |

**UserAdapter.delete_user_by_id**

| scenario | verdict |
|---|---|
| [when a user granted SOFT_DELETE in the target user scope deletes the user, success comes back and the state of that user changes to deleted](#retiring-a-user-granted-soft-delete-marks-another-user-deleted) | answered |
| [a user holding no role who tries to delete a user is rejected by the entity permission gate](#retiring-a-user-granted-nothing-may-not-delete-another-user) | rejected |

**UserAdapter.get**

| scenario | verdict |
|---|---|
| [when a user granted the user read permission in the target user scope reads the user, the whole node with the default key filled comes back](#reading-a-user-granted-read-on-another-user-reads-their-whole-node) | answered |
| [a user holding no role who tries to read another user is rejected by the entity permission gate](#reading-a-user-granted-nothing-may-not-read-another-user) | rejected |

**UserAdapter.update_user_by_id**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE and READ in the target user scope gives only a full name, the node comes back with only the full name changed](#editing-a-user-granted-update-changing-only-the-full-name-leaves-the-rest) | answered |
| [when a user granted SOFT_DELETE and READ in the target user scope gives ACTIVE in an edit of a deleted user, the user becomes active as with a restore](#retiring-an-edit-to-active-on-a-deleted-user-restores-the-user) | answered |
| [when a user granted SOFT_DELETE and READ in the target user scope gives DELETED in an edit, the user enters the deleted state as with a delete](#retiring-an-edit-to-deleted-soft-deletes-the-user) | answered |
| [when another user granted UPDATE and READ in the target user scope gives only a new password to a user required to change the password, the node comes back with the requirement still standing](#editing-another-users-new-password-leaves-the-password-change-requirement) | answered |
| [when a user holding the permission names another key of the target as the default key, the node comes back with the default key moved after the edit is applied](#editing-naming-a-default-key-in-an-edit-moves-the-default-to-it) | answered |
| [when a user holding the permission gives an empty value for the projects, the membership is left untouched and only the other edits are applied](#editing-null-project-ids-in-an-edit-leave-the-membership-as-it-is) | answered |
| [when a user required to change the password, granted UPDATE and READ in their own user scope, gives a new password and the requirement lifted together, the node comes back with the requirement lifted](#editing-setting-ones-own-new-password-lifts-the-password-change-requirement) | answered |
| [a user holding no role who tries to edit another user is rejected by the entity permission gate](#editing-a-user-granted-nothing-may-not-edit-another-user) | rejected |
| [when a user holding the permission gives a username another user already holds, input validation rejects it](#editing-a-username-another-user-holds-may-not-be-taken) | rejected |
| [when a user granted UPDATE and READ in the target user scope changes the full name of a deleted user, it is rejected because the user is deleted](#retiring-an-edit-of-another-field-on-a-deleted-user-is-refused) | rejected |
| [when a user granted UPDATE and READ in the target user scope gives BEFORE_VERIFICATION in an edit, input validation rejects it](#retiring-an-edit-to-a-status-other-than-active-or-inactive-is-refused) | rejected |
| [when a user granted only UPDATE and READ in the target user scope gives DELETED in an edit, the entity permission gate of the delete rejects it](#retiring-an-edit-to-deleted-is-refused-without-soft-delete) | rejected |
| [when only DELETED is given in an edit of a deleted user, nothing changes and that user comes back](#retiring-an-edit-to-deleted-on-a-deleted-user-changes-nothing) | rejected |

**LoginSessionAdapter.admin_revoke**

| scenario | verdict |
|---|---|
| [when the superadmin revokes another user's session in an admin revoke gated by the global role, success comes back, the session leaves the whole session search, and a history record says an admin revoked it](#login_sessions-the-superadmin-revokes-another-users-login-session) | answered |
| [a user holding the permission is rejected by the global role gate when revoking a session as admin](#login_sessions-a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin) | rejected |
| [when the superadmin gives a session id that does not exist, input validation rejects it](#login_sessions-even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist) | rejected |

**LoginSessionAdapter.admin_unblock_user**

| scenario | verdict |
|---|---|
| [when the superadmin gives a username in an unblock gated by the global role, success comes back and the block record of that name is gone](#login_sessions-the-superadmin-unblocks-a-user) | answered |
| [when the superadmin gives a username nobody holds, success comes back without checking that it exists](#login_sessions-unblocking-a-username-nobody-holds-still-succeeds) | answered |
| [a user holding the permission is rejected by the global role gate when unblocking a user](#login_sessions-a-user-who-is-not-the-superadmin-may-not-unblock-a-user) | rejected |

**LoginSessionAdapter.my_revoke**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE in their own scope revokes their own session, success comes back, the session is no longer searched, and a history record says the user revoked it](#login_sessions-a-user-granted-update-on-themselves-revokes-their-own-login-session) | answered |
| [a user holding no role who tries to revoke a session is rejected at the owner lookup step](#login_sessions-a-user-granted-nothing-may-not-revoke-their-own-login-session) | rejected |
| [when a user granted READ and UPDATE only in their own scope gives another user's session, the lookup step on its owner rejects it](#login_sessions-a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session) | rejected |
| [a user holding only READ who tries to revoke a session is rejected by the entity permission gate](#login_sessions-a-user-granted-only-read-may-not-revoke-their-own-login-session) | rejected |

**UserAdapter.admin_create_keypair**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE in the target user scope, not the superadmin, creates a key under a policy, a new key that is not the default and its secret come back](#managing_keypairs-a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy) | answered |
| [when a user holding the permission gives a policy name that does not exist, input validation rejects it](#managing_keypairs-a-key-may-not-be-made-under-a-policy-that-does-not-exist) | rejected |
| [a user holding no role who tries to create a key is rejected by the entity permission gate](#managing_keypairs-a-user-granted-nothing-may-not-make-a-key-for-another) | rejected |

**UserAdapter.admin_delete_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE in the target scope deletes a key, the access key of the deleted key comes back](#managing_keypairs-a-granted-user-deleting-another-users-extra-key-gets-its-access-key) | answered |
| [a user holding no role who tries to delete a key is rejected at the owner lookup step](#managing_keypairs-a-user-granted-nothing-may-not-delete-another-users-key) | rejected |
| [a user holding only READ who tries to delete a key is rejected by the entity permission gate](#managing_keypairs-a-user-granted-only-read-may-not-delete-another-users-key) | rejected |
| [when a user holding the permission tries to delete the target's default key, input validation rejects it](#managing_keypairs-another-users-default-key-may-not-be-deleted) | rejected |

**UserAdapter.admin_delete_ssh_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE in the target scope deletes the SSH key, the access key comes back and the public key is emptied](#managing_keypairs-a-granted-user-clearing-another-users-ssh-key-empties-the-public-key) | answered |
| [a user holding no role who tries to delete a key is rejected at the owner lookup step](#managing_keypairs-a-user-granted-nothing-may-not-clear-another-users-ssh-key) | rejected |
| [a user holding only READ who tries to delete a key is rejected by the entity permission gate](#managing_keypairs-a-user-granted-only-read-may-not-clear-another-users-ssh-key) | rejected |

**UserAdapter.admin_get_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ in the target scope reads a key, that whole key node comes back](#managing_keypairs-a-granted-user-reads-another-users-key-by-access-key) | answered |
| [a user holding no role who tries to read a key is rejected at the owner lookup step](#managing_keypairs-a-user-granted-nothing-may-not-read-another-users-key) | rejected |

**UserAdapter.admin_get_ssh_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ in the target scope reads the SSH key, only the access key and the public key come back and the private key does not](#managing_keypairs-a-granted-user-reads-another-users-ssh-public-key-only) | answered |
| [a user holding no role who tries to read a key is rejected at the owner lookup step](#managing_keypairs-a-user-granted-nothing-may-not-read-another-users-ssh-public-key) | rejected |

**UserAdapter.admin_register_ssh_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE in the target scope gives a public key and a private key, they overwrite the stored one without a format check and the access key comes back](#managing_keypairs-a-granted-user-registering-another-users-ssh-key-gets-the-access-key) | answered |
| [a user holding no role who tries to register an SSH key is rejected at the owner lookup step](#managing_keypairs-a-user-granted-nothing-may-not-register-another-users-ssh-key) | rejected |
| [a user holding only READ who tries to register an SSH key is rejected by the entity permission gate](#managing_keypairs-a-user-granted-only-read-may-not-register-another-users-ssh-key) | rejected |

**UserAdapter.admin_update_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE in the target scope gives only a rate limit, the key node comes back with everything else unchanged and only the rate limit changed](#managing_keypairs-a-granted-user-changing-another-users-rate-limit-changes-only-that) | answered |
| [a user holding no role who tries to change a key is rejected at the owner lookup step](#managing_keypairs-a-user-granted-nothing-may-not-change-another-users-key) | rejected |
| [a user holding only READ who tries to change a key is rejected by the entity permission gate](#managing_keypairs-a-user-granted-only-read-may-not-change-another-users-key) | rejected |
| [when a user holding the permission gives a policy name that does not exist, input validation rejects it](#managing_keypairs-another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist) | rejected |

**UserAdapter.bulk_purge_users**

| scenario | verdict |
|---|---|
| [when the superadmin gives an existing user and a missing id together, one is purged and the missing id comes back as failed](#retiring-a-bulk-purge-records-a-missing-id-as-a-failure) | answered |
| [when the superadmin gives two users in a bulk purge gated by the global role, the two ids and a count of two come back](#retiring-the-superadmin-bulk-purge-answers-the-purged-ids-and-count) | answered |
| [even a user granted HARD_DELETE in the domain scope is rejected by the global role gate when purging in bulk](#retiring-a-user-who-is-not-the-superadmin-may-not-purge-in-bulk) | rejected |

**UserAdapter.issue_my_keypair**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE in their own user scope issues a key, the key follows the admin flag, policy, and rate limit of the default key, holds no default flag, and comes back with its secret](#own_keypairs-a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key) | answered |
| [when a user holding the permission issues a key, moves the default key to it, and revokes the original default key, all three calls pass in turn and only the issued key is left](#own_keypairs-an-issued-key-made-default-lets-the-original-default-key-be-revoked) | answered |
| [a user holding no role who tries to issue their own key is rejected by the entity permission gate even for themselves](#own_keypairs-a-user-granted-nothing-may-not-issue-their-own-key) | rejected |

**UserAdapter.purge_user_by_id**

| scenario | verdict |
|---|---|
| [when a user granted HARD_DELETE in the target user scope purges a user that was not deleted, success comes back and that user is no longer found](#retiring-a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions) | answered |
| [a user holding no role who tries to purge a user is rejected by the entity permission gate](#retiring-a-user-granted-nothing-may-not-purge-another-user) | rejected |
| [when a user holding the permission gives an admin id that does not exist as the heir, input validation rejects it](#retiring-purging-a-user-to-an-admin-who-does-not-exist-is-refused) | rejected |

**UserAdapter.restore_user_by_id**

| scenario | verdict |
|---|---|
| [when a user granted SOFT_DELETE in the target user scope restores a deleted user, success comes back and the state changes to active](#retiring-a-user-granted-soft-delete-restores-a-deleted-user-to-active) | answered |
| [a user holding no role who tries to restore a user is rejected by the entity permission gate](#retiring-a-user-granted-nothing-may-not-restore-another-user) | rejected |
| [when a user holding the permission tries to restore an inactive user that was not deleted, it is rejected because the user is not deleted](#retiring-restoring-a-user-who-was-not-deleted-is-refused) | rejected |

**UserAdapter.revoke_my_keypair**

| scenario | verdict |
|---|---|
| [when a user holding the permission revokes their own extra key, success comes back and that key leaves their own key search](#own_keypairs-a-user-granted-read-and-update-revokes-a-non-default-key) | answered |
| [a user holding no role who tries to revoke a key is rejected at the owner lookup step with the same exception as a key that does not exist](#own_keypairs-a-user-granted-nothing-may-not-revoke-their-own-key) | rejected |
| [a user granted only READ in their own scope who tries to revoke a key passes the owner lookup and is rejected by the entity permission gate](#own_keypairs-a-user-granted-only-read-may-not-revoke-their-own-key) | rejected |
| [when a user holding the permission gives a value that is no key, the owner lookup step rejects it with the same exception as a missing permission](#own_keypairs-an-access-key-nobody-holds-may-not-be-revoked) | rejected |
| [when a user holding the permission tries to revoke their own default key, input validation rejects it](#own_keypairs-the-default-key-may-not-be-revoked) | rejected |

**UserAdapter.switch_default_access_key**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE in their own scope moves the default key to an extra key that is active, success comes back and the default key of the user node becomes that key](#own_keypairs-a-user-granted-read-and-update-moves-their-default-key) | answered |
| [a user holding no role who tries to move the default key is rejected by the entity permission gate](#own_keypairs-a-user-granted-nothing-may-not-move-their-default-key) | rejected |
| [when a user holding the permission gives another user's key, input validation rejects it](#own_keypairs-someone-elses-key-may-not-become-the-default-key) | rejected |

**UserAdapter.update_my_keypair**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE in their own scope turns an extra key inactive, the key node comes back with only the active flag changed](#own_keypairs-a-user-granted-read-and-update-turns-off-a-non-default-key) | answered |
| [a user holding no role who tries to turn a key inactive is rejected at the owner lookup step](#own_keypairs-a-user-granted-nothing-may-not-turn-off-their-own-key) | rejected |
| [a user holding only READ who tries to turn a key inactive is rejected by the entity permission gate](#own_keypairs-a-user-granted-only-read-may-not-turn-off-their-own-key) | rejected |
| [when a user holding the permission tries to turn their own default key inactive, input validation rejects it](#own_keypairs-the-default-key-may-not-be-turned-off) | rejected |

**UserAdapter.update_user**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE in the target user scope sends an edit holding only the allowed IP, a success flag comes back and the allowed IP of that user changes](#editing-a-user-granted-update-changes-the-allowed-client-ip) | answered |
| [when an allowed IP edit comes from a user holding no role, the entity permission gate rejects it](#editing-a-user-granted-nothing-may-not-change-the-allowed-client-ip) | rejected |

### LoginHistoryAdapter.admin_search

<a id="login_history-the-superadmin-searches-every-users-login-history"></a>

#### [the-superadmin-searches-every-users-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

when the superadmin searches in a history search gated by the global role, every record seeded in advance comes back in descending creation time regardless of the user

Given

- one domain, one superadmin, and two users who each hold one success record
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
  - regular user user-1: has one successful login record
  - regular user user-2: has one successful login record

When

- LoginHistoryAdapter.admin_search: user-3 searches every login history record

Then

- every record seeded in advance comes back in order
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the record seeded in advance
  - items[0].user_id: same as the record owner
  - items[0].domain_name = 'home-1'
  - items[0].result = 'success'
  - items[0].fail_reason = None
  - items[0].client_ip = None
  - items[0].created_at: the time this run wrote
  - items[1].id: same as the record seeded in advance
  - items[1].user_id: same as the record owner
  - items[1].domain_name = 'home-1'
  - items[1].result = 'success'
  - items[1].fail_reason = None
  - items[1].client_ip = None
  - items[1].created_at: the time this run wrote

<a id="login_history-a-user-who-is-not-the-superadmin-may-not-search-every-login-history"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

a user holding the permission is rejected by the global role gate when searching every history record

Given

- one domain, and the caller holds the user READ permission in the domain scope
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

- LoginHistoryAdapter.admin_search: user-1 searches every login history record

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### LoginHistoryAdapter.my_search

<a id="login_history-a-user-granted-read-on-themselves-searches-only-their-own-login-history"></a>

#### [a-user-granted-read-on-themselves-searches-only-their-own-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

when a user granted READ in their own scope searches, the history of other users is left out

Given

- one domain and two users, the caller holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one successful login record
  - regular user user-2: has one successful login record
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginHistoryAdapter.my_search: user-1 searches their own login history

Then

- only their own record comes back
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as the record seeded in advance
  - items[0].user_id: same as the record owner
  - items[0].domain_name = 'home-1'
  - items[0].result = 'success'
  - items[0].fail_reason = None
  - items[0].client_ip = None
  - items[0].created_at: the time this run wrote

<a id="login_history-a-user-granted-nothing-may-not-search-their-own-login-history"></a>

#### [a-user-granted-nothing-may-not-search-their-own-login-history](/tests/scenario/bai_scenario/manager/user/test_login_history.py): pass

a user holding no role who tries to search their own history is rejected by the scope permission gate even for themselves

Given

- one domain and two users, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one successful login record

When

- LoginHistoryAdapter.my_search: user-1 searches their own login history

Then

- the call is rejected
  - rejected: NotEnoughPermission

### LoginSessionAdapter.admin_search

<a id="login_sessions-the-superadmin-searches-every-users-login-sessions"></a>

#### [the-superadmin-searches-every-users-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when the superadmin searches without page arguments in a session search gated by the global role, every session seeded in advance comes back in descending creation time regardless of the user

Given

- one domain, one superadmin, and two users who each hold one session
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-5: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one active login session

When

- LoginSessionAdapter.admin_search: user-3 searches every login session

Then

- every session seeded in advance comes back in order
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the session seeded in advance
  - items[0].user_id: same as the session owner
  - items[0].access_key: same as the key that opened the session
  - items[0].status = 'active'
  - items[0].created_at: the time this run wrote
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None
  - items[1].id: same as the session seeded in advance
  - items[1].user_id: same as the session owner
  - items[1].access_key: same as the key that opened the session
  - items[1].status = 'active'
  - items[1].created_at: the time this run wrote
  - items[1].last_accessed_at = None
  - items[1].invalidated_at = None

<a id="login_sessions-a-user-who-is-not-the-superadmin-may-not-search-every-login-session"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

a user holding the permission is rejected by the global role gate when searching every login session

Given

- one domain and one user holding a session, and the caller holds the user READ permission in the domain scope
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
  - regular user user-1: has one active login session
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- LoginSessionAdapter.admin_search: user-2 searches every login session

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### LoginSessionAdapter.my_search

<a id="login_sessions-a-user-granted-read-on-themselves-searches-only-their-own-login-sessions"></a>

#### [a-user-granted-read-on-themselves-searches-only-their-own-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when a user granted READ in their own scope searches, the sessions of other users are left out

Given

- one domain and two users, the caller holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one active login session
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginSessionAdapter.my_search: user-1 searches their own login sessions

Then

- only their own session comes back
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as the session seeded in advance
  - items[0].user_id: same as the session owner
  - items[0].access_key: same as the key that opened the session
  - items[0].status = 'active'
  - items[0].created_at: the time this run wrote
  - items[0].last_accessed_at = None
  - items[0].invalidated_at = None

<a id="login_sessions-a-user-granted-nothing-may-not-search-their-own-login-sessions"></a>

#### [a-user-granted-nothing-may-not-search-their-own-login-sessions](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

a user holding no role who tries to search their own sessions is rejected by the scope permission gate even for themselves

Given

- one domain and two users, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session

When

- LoginSessionAdapter.my_search: user-1 searches their own login sessions

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.admin_search

<a id="searching-the-superadmin-searching-every-user-counts-deleted-ones-too"></a>

#### [the-superadmin-searching-every-user-counts-deleted-ones-too](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

when the superadmin searches without a filter in a search gated by the global role, every user seeded in advance comes back, deleted ones included

Given

- one domain, one active user, one deleted user, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Prepare one deleted user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: status deleted, has their own keypair and personal project

When

- UserAdapter.admin_search: user-3 searches every user without a filter

Then

- every user seeded in advance comes back, deleted ones included
  - items(by name, name and state) = [('user-1', 'active'), ('user-2', 'deleted'), ('user-3', 'active')]
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = 50

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-user"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-user](/tests/scenario/bai_scenario/manager/user/test_searching.py): pass

even a user granted permission in the domain scope is rejected by the global role gate when searching every user

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

- UserAdapter.admin_search: user-1 searches every user without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.admin_search_keypairs

<a id="managing_keypairs-the-superadmin-searching-every-key-gets-every-users-key"></a>

#### [the-superadmin-searching-every-key-gets-every-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when the superadmin searches without page arguments in a key search gated by the global role, every user's key comes back and the limit field comes back empty

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

- UserAdapter.admin_search_keypairs: user-3 searches every key without page arguments

Then

- every user's key comes back in owner order
  - items.length = 3
  - items[0].id: skipped: it is a random key the seed made
  - items[0].access_key: skipped: it is a random key the seed made
  - items[0].is_active = True
  - items[0].is_admin = False
  - items[0].is_default = True
  - items[0].rate_limit = 10000
  - items[0].resource_policy = 'keypair-policy-1'
  - items[0].ssh_public_key = ''
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
  - items[1].ssh_public_key = ''
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
  - items[2].ssh_public_key = ''
  - items[2].num_queries = 0
  - items[2].last_used = None
  - items[2].user_id: same as the key owner
  - items[2].created_at: the time this run wrote
  - items[2].modified_at: the time this run wrote
  - pagination.total = 3
  - pagination.offset = 0
  - pagination.limit = None

<a id="managing_keypairs-a-user-who-is-not-the-superadmin-may-not-search-every-key"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding the permission is rejected by the global role gate when searching every key

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

- UserAdapter.admin_search_keypairs: user-1 searches every key without page arguments

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.batch_load_by_ids

<a id="reading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when a user holding no permission gives an empty id list, no action is called and an empty list comes back

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

- UserAdapter.batch_load_by_ids: user-2 batch reads an empty list

Then

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
  - items[0].ssh_public_key = ''
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
  - items[the extra key].ssh_public_key = ''
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
  - items[the default key].ssh_public_key = ''
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

### UserAdapter.bulk_create_users

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

- one domain and one target user, 1 more users, the caller is a superadmin, one more user holds an extra key that is not the default
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
  - updated_users = []
  - failed.length = 1
  - failed[0].user_id: same as the user who tried to move the default key
  - failed[0].message: skipped: the exception message may change

<a id="editing-the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart"></a>

#### [the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when the superadmin gives one user to update and one to rename into a taken name in a bulk edit gated by the global role, one is updated and one comes back as failed with its user id

Given

- one domain and one target user, 2 more users, the caller is a superadmin
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
    - superadmin user-4: has their own keypair and personal project
    - User resource policy user-policy-5: up to 10 folders per user
    - Keypair policy keypair-policy-5: up to 5 concurrent sessions
    - superadmin user-5: has their own keypair and personal project

When

- UserAdapter.bulk_update_users: user-4 bulk edits: renames the full name of user-1, and renames user-3 to user-2

Then

- one comes back in the updated list and one in the failed list
  - updated_users.length = 1
  - failed.length = 1
  - updated_users[0].id: same as the user seeded in advance
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
  - updated_users[0].organization.main_access_key: the user's main access key is filled
  - updated_users[0].security.allowed_client_ip = None
  - updated_users[0].security.totp_activated = False
  - updated_users[0].security.totp_activated_at = None
  - updated_users[0].security.sudo_session_enabled = False
  - updated_users[0].container.container_uid = None
  - updated_users[0].container.container_main_gid = None
  - updated_users[0].container.container_gids = None
  - updated_users[0].timestamps.created_at: the time this run wrote
  - updated_users[0].timestamps.modified_at: the time this run wrote
  - failed[0].user_id: same as the user renamed into a taken name
  - failed[0].message: skipped: the exception message may change

<a id="editing-a-user-who-is-not-the-superadmin-may-not-bulk-edit-users"></a>

#### [a-user-who-is-not-the-superadmin-may-not-bulk-edit-users](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

even a user granted UPDATE in the domain scope is rejected by the global role gate when bulk editing users

Given

- one domain and one target user, 2 more users, the caller is a user and holds UPDATE in the domain scope
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
    - superadmin user-5: has their own keypair and personal project
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-4: holds Role user-role-1

When

- UserAdapter.bulk_update_users: user-4 bulk edits: renames the full name of user-1, and renames user-3 to user-2

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### UserAdapter.create_user

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
  - success = True
  - the read that follows.id: same as the user seeded in advance
  - the read that follows.basic_info.username = 'user-1'
  - the read that follows.basic_info.email = 'user-1@scenario.local'
  - the read that follows.basic_info.full_name = None
  - the read that follows.basic_info.description = None
  - the read that follows.basic_info.integration_name = None
  - the read that follows.status.status = 'deleted'
  - the read that follows.status.status_info = 'admin-requested'
  - the read that follows.status.need_password_change = False
  - the read that follows.organization.domain_name = 'home-1'
  - the read that follows.organization.role = 'user'
  - the read that follows.organization.resource_policy = 'user-policy-1'
  - the read that follows.organization.main_access_key: the user's main access key is filled
  - the read that follows.security.allowed_client_ip = None
  - the read that follows.security.totp_activated = False
  - the read that follows.security.totp_activated_at = None
  - the read that follows.security.sudo_session_enabled = False
  - the read that follows.container.container_uid = None
  - the read that follows.container.container_main_gid = None
  - the read that follows.container.container_gids = None
  - the read that follows.timestamps.created_at: the time this run wrote
  - the read that follows.timestamps.modified_at: the time this run wrote

<a id="retiring-a-user-granted-nothing-may-not-delete-another-user"></a>

#### [a-user-granted-nothing-may-not-delete-another-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

a user holding no role who tries to delete a user is rejected by the entity permission gate

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

- UserAdapter.delete_user_by_id: user-2 deletes user-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.get

<a id="reading-a-user-granted-read-on-another-user-reads-their-whole-node"></a>

#### [a-user-granted-read-on-another-user-reads-their-whole-node](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

when a user granted the user read permission in the target user scope reads the user, the whole node with the default key filled comes back

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

- UserAdapter.get: user-2 reads user-1 by id

Then

- the whole user read comes back
  - id: same as the user seeded in advance
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
  - organization.main_access_key: the user's main access key is filled
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="reading-a-user-granted-nothing-may-not-read-another-user"></a>

#### [a-user-granted-nothing-may-not-read-another-user](/tests/scenario/bai_scenario/manager/user/test_reading.py): pass

a user holding no role who tries to read another user is rejected by the entity permission gate

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

- UserAdapter.get: user-2 reads user-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.update_user_by_id

<a id="editing-a-user-granted-update-changing-only-the-full-name-leaves-the-rest"></a>

#### [a-user-granted-update-changing-only-the-full-name-leaves-the-rest](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when a user granted UPDATE and READ in the target user scope gives only a full name, the node comes back with only the full name changed

Given

- one domain and one target user, the caller is a user and holds UPDATE, READ in the target user scope
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
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-2 changes the full name of user-1 to renamed

Then

- the whole user with only the full name changed comes back
  - id: same as the user seeded in advance
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
  - organization.main_access_key: the user's main access key is filled
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="retiring-an-edit-to-active-on-a-deleted-user-restores-the-user"></a>

#### [an-edit-to-active-on-a-deleted-user-restores-the-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted SOFT_DELETE and READ in the target user scope gives ACTIVE in an edit of a deleted user, the user becomes active as with a restore

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

- UserAdapter.update_user_by_id: user-2 edits user-1: sets the status to ACTIVE

Then

- the whole user in the active state comes back
  - id: same as the user seeded in advance
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'active'
  - status.status_info = 'admin-requested'
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: it is empty because there is no active default key
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="retiring-an-edit-to-deleted-soft-deletes-the-user"></a>

#### [an-edit-to-deleted-soft-deletes-the-user](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted SOFT_DELETE and READ in the target user scope gives DELETED in an edit, the user enters the deleted state as with a delete

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

- UserAdapter.update_user_by_id: user-2 edits user-1: sets the status to DELETED

Then

- the whole user in the deleted state comes back
  - id: same as the user seeded in advance
  - basic_info.username = 'user-1'
  - basic_info.email = 'user-1@scenario.local'
  - basic_info.full_name = None
  - basic_info.description = None
  - basic_info.integration_name = None
  - status.status = 'deleted'
  - status.status_info = 'admin-requested'
  - status.need_password_change = False
  - organization.domain_name = 'home-1'
  - organization.role = 'user'
  - organization.resource_policy = 'user-policy-1'
  - organization.main_access_key: the user's main access key is filled
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="editing-another-users-new-password-leaves-the-password-change-requirement"></a>

#### [another-users-new-password-leaves-the-password-change-requirement](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when another user granted UPDATE and READ in the target user scope gives only a new password to a user required to change the password, the node comes back with the requirement still standing

Given

- one domain and one target user, the caller is a user and holds UPDATE, READ in the target user scope, the target user is required to change the password
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project, and must change their password
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-2 changes only the password of user-1

Then

- the whole user with the password change requirement still standing comes back
  - id: same as the user seeded in advance
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
  - organization.main_access_key: the user's main access key is filled
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="editing-naming-a-default-key-in-an-edit-moves-the-default-to-it"></a>

#### [naming-a-default-key-in-an-edit-moves-the-default-to-it](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when a user holding the permission names another key of the target as the default key, the node comes back with the default key moved after the edit is applied

Given

- one domain and one target user, the caller is a user and holds UPDATE, READ in the target user scope, one more user holds an extra key that is not the default
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
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1
  - Keypair policy keypair-policy-4: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.update_user_by_id: user-2 names the extra key of user-1 as the default key

Then

- the whole user whose default key moved to the extra key comes back
  - id: same as the user seeded in advance
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
  - organization.main_access_key: same as the extra key
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="editing-null-project-ids-in-an-edit-leave-the-membership-as-it-is"></a>

#### [null-project-ids-in-an-edit-leave-the-membership-as-it-is](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when a user holding the permission gives an empty value for the projects, the membership is left untouched and only the other edits are applied

Given

- one domain and one project, the target user on its roster, and one user granted UPDATE and READ in the target user scope
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
  - Project team-1
  - regular user user-1: added to the member list of Project team-1
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-2 gives an empty value for the projects of user-1, and user-3 searches by team-1

Then

- the user is unchanged and stays on the project roster
  - id: same as the user seeded in advance
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
  - organization.main_access_key: the user's main access key is filled
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote
  - the project search that follows.items: same as the one target user on the roster
  - the project search that follows.pagination.total = 1
  - the project search that follows.pagination.offset = 0
  - the project search that follows.pagination.limit = 50

<a id="editing-setting-ones-own-new-password-lifts-the-password-change-requirement"></a>

#### [setting-ones-own-new-password-lifts-the-password-change-requirement](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when a user required to change the password, granted UPDATE and READ in their own user scope, gives a new password and the requirement lifted together, the node comes back with the requirement lifted

Given

- one domain and one user required to change the password, who holds UPDATE and READ in their own user scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project, and must change their password
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-1 changes their own password and lifts the password change requirement

Then

- the whole user with the password change requirement lifted comes back
  - id: same as the user seeded in advance
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
  - organization.main_access_key: the user's main access key is filled
  - security.allowed_client_ip = None
  - security.totp_activated = False
  - security.totp_activated_at = None
  - security.sudo_session_enabled = False
  - container.container_uid = None
  - container.container_main_gid = None
  - container.container_gids = None
  - timestamps.created_at: the time this run wrote
  - timestamps.modified_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-edit-another-user"></a>

#### [a-user-granted-nothing-may-not-edit-another-user](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

a user holding no role who tries to edit another user is rejected by the entity permission gate

Given

- one domain and one target user, the caller is a user
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

- UserAdapter.update_user_by_id: user-2 changes the full name of user-1 to renamed

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-a-username-another-user-holds-may-not-be-taken"></a>

#### [a-username-another-user-holds-may-not-be-taken](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when a user holding the permission gives a username another user already holds, input validation rejects it

Given

- one domain and one target user, 1 more users, the caller is a user and holds UPDATE in the target user scope
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
    - superadmin user-4: has their own keypair and personal project
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-3: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-3 changes the name of user-1 to user-2

Then

- the call is rejected
  - rejected: UserModificationBadRequest

<a id="retiring-an-edit-of-another-field-on-a-deleted-user-is-refused"></a>

#### [an-edit-of-another-field-on-a-deleted-user-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted UPDATE and READ in the target user scope changes the full name of a deleted user, it is rejected because the user is deleted

Given

- one domain and one target deleted user, with the caller holding the user UPDATE, READ permission on the target
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
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-2 edits user-1: changes the full name

Then

- the call is rejected
  - rejected: UserDeleted

<a id="retiring-an-edit-to-a-status-other-than-active-or-inactive-is-refused"></a>

#### [an-edit-to-a-status-other-than-active-or-inactive-is-refused](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted UPDATE and READ in the target user scope gives BEFORE_VERIFICATION in an edit, input validation rejects it

Given

- one domain and one target user, with the caller holding the user UPDATE, READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-2 edits user-1: sets the status to BEFORE_VERIFICATION

Then

- the call is rejected
  - rejected: UserModificationBadRequest

<a id="retiring-an-edit-to-deleted-is-refused-without-soft-delete"></a>

#### [an-edit-to-deleted-is-refused-without-soft-delete](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when a user granted only UPDATE and READ in the target user scope gives DELETED in an edit, the entity permission gate of the delete rejects it

Given

- one domain and one target user, with the caller holding the user UPDATE, READ permission on the target
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - a role assignment granting the user the UPDATE, READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user_by_id: user-2 edits user-1: sets the status to DELETED

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-an-edit-to-deleted-on-a-deleted-user-changes-nothing"></a>

#### [an-edit-to-deleted-on-a-deleted-user-changes-nothing](/tests/scenario/bai_scenario/manager/user/test_retiring.py): pass

when only DELETED is given in an edit of a deleted user, nothing changes and that user comes back

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

- UserAdapter.update_user_by_id: user-2 edits user-1: sets the status to DELETED

Then

- the whole user still in the deleted state comes back
  - rejected: NotEnoughPermission

### LoginSessionAdapter.admin_revoke

<a id="login_sessions-the-superadmin-revokes-another-users-login-session"></a>

#### [the-superadmin-revokes-another-users-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when the superadmin revokes another user's session in an admin revoke gated by the global role, success comes back, the session leaves the whole session search, and a history record says an admin revoked it

Given

- one domain, one superadmin, and one user holding one session
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session

When

- LoginSessionAdapter.admin_revoke: user-2 revokes the login session of user-1 through the admin path

Then

- the revoke succeeds and the session is gone from the search that follows
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
  - after.has_next_page = False
  - after.has_previous_page = False

<a id="login_sessions-a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin"></a>

#### [a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

a user holding the permission is rejected by the global role gate when revoking a session as admin

Given

- one domain and one user holding a session, and the caller holds the user UPDATE permission in the domain scope
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
  - regular user user-1: has one active login session
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- LoginSessionAdapter.admin_revoke: user-2 revokes the login session of user-1 through the admin path

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="login_sessions-even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist"></a>

#### [even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when the superadmin gives a session id that does not exist, input validation rejects it

Given

- one domain, one superadmin, and one user holding one session
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session

When

- LoginSessionAdapter.admin_revoke: user-2 revokes a login session that does not exist through the admin path

Then

- the call is rejected
  - rejected: LoginSessionNotFoundError

### LoginSessionAdapter.admin_unblock_user

<a id="login_sessions-the-superadmin-unblocks-a-user"></a>

#### [the-superadmin-unblocks-a-user](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when the superadmin gives a username in an unblock gated by the global role, success comes back and the block record of that name is gone

Given

- one domain, one superadmin, and one user holding one session
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session

When

- LoginSessionAdapter.admin_unblock_user: user-2 unblocks user-1

Then

- the unblock succeeds
  - success = True

<a id="login_sessions-unblocking-a-username-nobody-holds-still-succeeds"></a>

#### [unblocking-a-username-nobody-holds-still-succeeds](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when the superadmin gives a username nobody holds, success comes back without checking that it exists

Given

- one domain, one superadmin, and one user holding one session
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session

When

- LoginSessionAdapter.admin_unblock_user: user-2 unblocks a username nobody holds

Then

- the unblock succeeds
  - success = True

<a id="login_sessions-a-user-who-is-not-the-superadmin-may-not-unblock-a-user"></a>

#### [a-user-who-is-not-the-superadmin-may-not-unblock-a-user](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

a user holding the permission is rejected by the global role gate when unblocking a user

Given

- one domain and one user holding a session, and the caller holds the user UPDATE permission in the domain scope
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
  - regular user user-1: has one active login session
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- LoginSessionAdapter.admin_unblock_user: user-2 unblocks user-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### LoginSessionAdapter.my_revoke

<a id="login_sessions-a-user-granted-update-on-themselves-revokes-their-own-login-session"></a>

#### [a-user-granted-update-on-themselves-revokes-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when a user granted READ and UPDATE in their own scope revokes their own session, success comes back, the session is no longer searched, and a history record says the user revoked it

Given

- one domain and two users, the caller holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginSessionAdapter.my_revoke: user-1 revokes their own login session

Then

- the revoke succeeds and the session is gone from the search that follows
  - revoked.success = True
  - after.items = []
  - after.total_count = 0
  - after.has_next_page = False
  - after.has_previous_page = False

<a id="login_sessions-a-user-granted-nothing-may-not-revoke-their-own-login-session"></a>

#### [a-user-granted-nothing-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

a user holding no role who tries to revoke a session is rejected at the owner lookup step

Given

- one domain and two users, the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session

When

- LoginSessionAdapter.my_revoke: user-1 revokes their own login session

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="login_sessions-a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session"></a>

#### [a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

when a user granted READ and UPDATE only in their own scope gives another user's session, the lookup step on its owner rejects it

Given

- one domain and two users, the caller holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - regular user user-2: has one active login session
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginSessionAdapter.my_revoke: user-1 revokes the login session of user-2

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="login_sessions-a-user-granted-only-read-may-not-revoke-their-own-login-session"></a>

#### [a-user-granted-only-read-may-not-revoke-their-own-login-session](/tests/scenario/bai_scenario/manager/user/test_login_sessions.py): pass

a user holding only READ who tries to revoke a session is rejected by the entity permission gate

Given

- one domain and two users, the caller holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - regular user user-1: has one active login session
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginSessionAdapter.my_revoke: user-1 revokes their own login session

Then

- the call is rejected
  - rejected: NotEnoughPermission

### UserAdapter.admin_create_keypair

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
  - id: skipped: it is the access key the manager created
  - access_key: skipped: the manager creates it
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 30000
  - resource_policy = 'granted-policy-1'
  - ssh_public_key: skipped: it is the RSA key the manager created
  - num_queries = 0
  - last_used = None
  - user_id: same as the keypair owner
  - created_at: the time this run wrote
  - modified_at: the time this run wrote
  - secret_key: skipped: the manager creates it

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

### UserAdapter.admin_delete_keypair

<a id="managing_keypairs-a-granted-user-deleting-another-users-extra-key-gets-its-access-key"></a>

#### [a-granted-user-deleting-another-users-extra-key-gets-its-access-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted READ and UPDATE in the target scope deletes a key, the access key of the deleted key comes back

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

- UserAdapter.admin_delete_keypair: user-2 deletes the extra key of user-1

Then

- the access key of the deleted key comes back
  - access_key: same as the key seeded in advance

<a id="managing_keypairs-a-user-granted-nothing-may-not-delete-another-users-key"></a>

#### [a-user-granted-nothing-may-not-delete-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding no role who tries to delete a key is rejected at the owner lookup step

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

- UserAdapter.admin_delete_keypair: user-2 deletes the extra key of user-1

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="managing_keypairs-a-user-granted-only-read-may-not-delete-another-users-key"></a>

#### [a-user-granted-only-read-may-not-delete-another-users-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

a user holding only READ who tries to delete a key is rejected by the entity permission gate

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

- UserAdapter.admin_delete_keypair: user-2 deletes the extra key of user-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="managing_keypairs-another-users-default-key-may-not-be-deleted"></a>

#### [another-users-default-key-may-not-be-deleted](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user holding the permission tries to delete the target's default key, input validation rejects it

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

- UserAdapter.admin_delete_keypair: user-2 deletes the default key of user-1

Then

- the call is rejected
  - rejected: KeyPairForbidden

### UserAdapter.admin_delete_ssh_keypair

<a id="managing_keypairs-a-granted-user-clearing-another-users-ssh-key-empties-the-public-key"></a>

#### [a-granted-user-clearing-another-users-ssh-key-empties-the-public-key](/tests/scenario/bai_scenario/manager/user/test_managing_keypairs.py): pass

when a user granted READ and UPDATE in the target scope deletes the SSH key, the access key comes back and the public key is emptied

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

- UserAdapter.admin_delete_ssh_keypair: user-2 deletes the SSH key from the default key of user-1 and reads it

Then

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
  - ssh_public_key = ''
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
  - keypair.ssh_public_key = ''

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

when a user granted READ and UPDATE in the target scope gives a public key and a private key, they overwrite the stored one without a format check and the access key comes back

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
  - ssh_public_key = ''
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

### UserAdapter.issue_my_keypair

<a id="own_keypairs-a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key"></a>

#### [a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user granted UPDATE in their own user scope issues a key, the key follows the admin flag, policy, and rate limit of the default key, holds no default flag, and comes back with its secret

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.issue_my_keypair: user-1 issues their own key

Then

- a new key that is not the default, following the default key, and its secret come back
  - id: skipped: it is the access key the manager created
  - access_key: skipped: the manager creates it
  - is_active = True
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-1'
  - ssh_public_key: skipped: it is the RSA key the manager created
  - num_queries = 0
  - last_used = None
  - user_id: same as the keypair owner
  - created_at: the time this run wrote
  - modified_at: the time this run wrote
  - secret_key: skipped: the manager makes it anew every time

<a id="own_keypairs-an-issued-key-made-default-lets-the-original-default-key-be-revoked"></a>

#### [an-issued-key-made-default-lets-the-original-default-key-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission issues a key, moves the default key to it, and revokes the original default key, all three calls pass in turn and only the issued key is left

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.issue_my_keypair: user-1 finds the default key through their own key search, issues a key, moves the default key to it, revokes the original default key, and searches their own keys again

Then

- all three calls pass and only the issued key is left
  - issued.id: skipped: it is the access key the manager created
  - issued.access_key: skipped: the manager creates it
  - issued.is_active = True
  - issued.is_admin = False
  - issued.is_default = False
  - issued.rate_limit = 10000
  - issued.resource_policy = 'keypair-policy-1'
  - issued.ssh_public_key: skipped: it is the RSA key the manager created
  - issued.num_queries = 0
  - issued.last_used = None
  - issued.user_id: same as the keypair owner
  - issued.created_at: the time this run wrote
  - issued.modified_at: the time this run wrote
  - issued.secret_key: skipped: the manager makes it anew every time
  - switched = True
  - revoked = True
  - after.total_count = 1
  - after.has_next_page = False
  - after.has_previous_page = False
  - after.items.access_key: same as the key issued
  - after.items[0].is_active = True
  - after.items[0].is_admin = False
  - after.items[0].is_default = True
  - after.items[0].rate_limit = 10000
  - after.items[0].resource_policy = 'keypair-policy-1'
  - after.items[0].ssh_public_key: skipped: it is the RSA key the manager created
  - after.items[0].num_queries = 0
  - after.items[0].last_used = None
  - after.items[0].user_id: same as the key owner
  - after.items[0].created_at: the time this run wrote
  - after.items[0].modified_at: the time this run wrote

<a id="own_keypairs-a-user-granted-nothing-may-not-issue-their-own-key"></a>

#### [a-user-granted-nothing-may-not-issue-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user holding no role who tries to issue their own key is rejected by the entity permission gate even for themselves

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- UserAdapter.issue_my_keypair: user-1 issues their own key

Then

- the call is rejected
  - rejected: NotEnoughPermission

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
  - after.has_next_page = False
  - after.has_previous_page = False
  - after.items.length = 1
  - after.items[0].id: skipped: it is an access key the seed makes anew every time
  - after.items[0].access_key: skipped: it is an access key the seed makes anew every time
  - after.items[0].is_active = True
  - after.items[0].is_admin = False
  - after.items[0].is_default = True
  - after.items[0].rate_limit = 10000
  - after.items[0].resource_policy = 'keypair-policy-1'
  - after.items[0].ssh_public_key = ''
  - after.items[0].num_queries = 0
  - after.items[0].last_used = None
  - after.items[0].user_id: same as the key owner
  - after.items[0].created_at: the time this run wrote
  - after.items[0].modified_at: the time this run wrote

<a id="own_keypairs-a-user-granted-nothing-may-not-revoke-their-own-key"></a>

#### [a-user-granted-nothing-may-not-revoke-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user holding no role who tries to revoke a key is rejected at the owner lookup step with the same exception as a key that does not exist

Given

- one domain and one user holding 1 extra keys that are not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.revoke_my_keypair: user-1 revokes their own extra key and searches their own keys again

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="own_keypairs-a-user-granted-only-read-may-not-revoke-their-own-key"></a>

#### [a-user-granted-only-read-may-not-revoke-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user granted only READ in their own scope who tries to revoke a key passes the owner lookup and is rejected by the entity permission gate

Given

- one domain and one user holding 1 extra keys that are not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.revoke_my_keypair: user-1 revokes their own extra key and searches their own keys again

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="own_keypairs-an-access-key-nobody-holds-may-not-be-revoked"></a>

#### [an-access-key-nobody-holds-may-not-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission gives a value that is no key, the owner lookup step rejects it with the same exception as a missing permission

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.revoke_my_keypair: user-1 revokes with an access key nobody holds

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="own_keypairs-the-default-key-may-not-be-revoked"></a>

#### [the-default-key-may-not-be-revoked](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission tries to revoke their own default key, input validation rejects it

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.revoke_my_keypair: user-1 finds the default key through their own key search and revokes it

Then

- the call is rejected
  - rejected: KeyPairForbidden

### UserAdapter.switch_default_access_key

<a id="own_keypairs-a-user-granted-read-and-update-moves-their-default-key"></a>

#### [a-user-granted-read-and-update-moves-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user granted UPDATE in their own scope moves the default key to an extra key that is active, success comes back and the default key of the user node becomes that key

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

- UserAdapter.switch_default_access_key: user-1 moves the default key to their own extra key and reads their own user again

Then

- the switch succeeds and the default key in the read that follows is the extra key
  - success = True
  - node.id: same as the user seeded in advance
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
  - node.organization.main_access_key: same as the extra key
  - node.security.allowed_client_ip = None
  - node.security.totp_activated = False
  - node.security.totp_activated_at = None
  - node.security.sudo_session_enabled = False
  - node.container.container_uid = None
  - node.container.container_main_gid = None
  - node.container.container_gids = None
  - node.timestamps.created_at: the time this run wrote
  - node.timestamps.modified_at: the time this run wrote

<a id="own_keypairs-a-user-granted-nothing-may-not-move-their-default-key"></a>

#### [a-user-granted-nothing-may-not-move-their-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user holding no role who tries to move the default key is rejected by the entity permission gate

Given

- one domain and one user holding 1 extra keys that are not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.switch_default_access_key: user-1 moves the default key to their own extra key

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="own_keypairs-someone-elses-key-may-not-become-the-default-key"></a>

#### [someone-elses-key-may-not-become-the-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission gives another user's key, input validation rejects it

Given

- one domain and one user holding 0 extra keys that are not the default, one other user holding an extra key that is not the default, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: has one more active keypair besides the default one
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.switch_default_access_key: user-1 moves the default key to another user's key

Then

- the call is rejected
  - rejected: KeyPairForbidden

### UserAdapter.update_my_keypair

<a id="own_keypairs-a-user-granted-read-and-update-turns-off-a-non-default-key"></a>

#### [a-user-granted-read-and-update-turns-off-a-non-default-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user granted READ and UPDATE in their own scope turns an extra key inactive, the key node comes back with only the active flag changed

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

- UserAdapter.update_my_keypair: user-1 turns their own extra key inactive

Then

- the whole key node with only the active flag changed comes back
  - id: same as the keypair seeded in advance
  - access_key: same as the keypair seeded in advance
  - is_active = False
  - is_admin = False
  - is_default = False
  - rate_limit = 10000
  - resource_policy = 'keypair-policy-1'
  - ssh_public_key = ''
  - num_queries = 0
  - last_used = None
  - user_id: same as the keypair owner
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="own_keypairs-a-user-granted-nothing-may-not-turn-off-their-own-key"></a>

#### [a-user-granted-nothing-may-not-turn-off-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user holding no role who tries to turn a key inactive is rejected at the owner lookup step

Given

- one domain and one user holding 1 extra keys that are not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one

When

- UserAdapter.update_my_keypair: user-1 turns their own extra key inactive

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="own_keypairs-a-user-granted-only-read-may-not-turn-off-their-own-key"></a>

#### [a-user-granted-only-read-may-not-turn-off-their-own-key](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

a user holding only READ who tries to turn a key inactive is rejected by the entity permission gate

Given

- one domain and one user holding 1 extra keys that are not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: has one more active keypair besides the default one
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.update_my_keypair: user-1 turns their own extra key inactive

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="own_keypairs-the-default-key-may-not-be-turned-off"></a>

#### [the-default-key-may-not-be-turned-off](/tests/scenario/bai_scenario/manager/user/test_own_keypairs.py): pass

when a user holding the permission tries to turn their own default key inactive, input validation rejects it

Given

- one domain and one user holding 0 extra keys that are not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user whose key policy is known
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- UserAdapter.update_my_keypair: user-1 finds the default key through their own key search and turns it inactive

Then

- the call is rejected
  - rejected: KeyPairForbidden

### UserAdapter.update_user

<a id="editing-a-user-granted-update-changes-the-allowed-client-ip"></a>

#### [a-user-granted-update-changes-the-allowed-client-ip](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when a user granted UPDATE in the target user scope sends an edit holding only the allowed IP, a success flag comes back and the allowed IP of that user changes

Given

- one domain and one target user, the caller is a user and holds UPDATE in the target user scope
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
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-2: holds Role user-role-1

When

- UserAdapter.update_user: user-2 changes the allowed IP of user-1, and user-3 reads it back

Then

- the call succeeds and the user read back has only the allowed IP changed
  - success = True
  - the read that follows.id: same as the user seeded in advance
  - the read that follows.basic_info.username = 'user-1'
  - the read that follows.basic_info.email = 'user-1@scenario.local'
  - the read that follows.basic_info.full_name = None
  - the read that follows.basic_info.description = None
  - the read that follows.basic_info.integration_name = None
  - the read that follows.status.status = 'active'
  - the read that follows.status.status_info = None
  - the read that follows.status.need_password_change = False
  - the read that follows.organization.domain_name = 'home-1'
  - the read that follows.organization.role = 'user'
  - the read that follows.organization.resource_policy = 'user-policy-1'
  - the read that follows.organization.main_access_key: the user's main access key is filled
  - the read that follows.security.allowed_client_ip = ['10.0.0.1/32']
  - the read that follows.security.totp_activated = False
  - the read that follows.security.totp_activated_at = None
  - the read that follows.security.sudo_session_enabled = False
  - the read that follows.container.container_uid = None
  - the read that follows.container.container_main_gid = None
  - the read that follows.container.container_gids = None
  - the read that follows.timestamps.created_at: the time this run wrote
  - the read that follows.timestamps.modified_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-change-the-allowed-client-ip"></a>

#### [a-user-granted-nothing-may-not-change-the-allowed-client-ip](/tests/scenario/bai_scenario/manager/user/test_editing.py): pass

when an allowed IP edit comes from a user holding no role, the entity permission gate rejects it

Given

- one domain and one target user, the caller is a user
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

- UserAdapter.update_user: user-2 changes the allowed IP of user-1, and user-3 reads it back

Then

- the call is rejected
  - rejected: NotEnoughPermission

