## bootstrap_script

[adapter](/src/ai/backend/manager/api/adapters/bootstrap_script/adapter.py)

Scenario: complete

- built from ops (4)
  - bulk_get_ids: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
- direct implementation (4)
  - add_revision: success present 1 · rejection present 1 (runtime_single_field)
  - bulk_get_current_revisions: success present 1 · rejection present 1 (partial_bulk_field)
  - create: success present 1 · rejection present 1 (single_entity)
  - switch_default: success present 1 · rejection present 1 (single_entity)

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user loads their bootstrap script by id, that script comes back](#batch_loading-a-user-granted-read-loads-their-bootstrap-script-by-id) | answered |
| [when a user granted READ on their own user loads their script and another user's script by id, the call succeeds but the entry of the other user's script is rejected for lack of permission](#batch_loading-a-strangers-bootstrap-script-is-rejected-in-the-batch) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user reads their bootstrap script by id, that script comes back](#reading-a-user-granted-read-reads-their-bootstrap-script) | answered |
| [when a user granted nothing tries to read their bootstrap script by id, it is rejected with an answer that does not tell whether the script exists](#reading-a-user-granted-nothing-may-not-read-their-bootstrap-script) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE on their own user purges their bootstrap script that is not the default, the id of that script comes back](#purging-a-user-granted-update-purges-their-bootstrap-script) | answered |
| [when a user granted only READ on their own user tries to purge their bootstrap script, it is rejected for lack of permission](#purging-a-user-granted-read-may-not-purge-their-bootstrap-script) | rejected |
| [when a user granted READ and UPDATE on their own user tries to purge their default bootstrap script, it is rejected until the default moves](#purging-the-default-bootstrap-script-is-not-purged) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user searches their bootstrap scripts that are not the default, only that script comes back, not the default one nor the script of another user](#searching-a-user-granted-read-searches-their-bootstrap-scripts) | answered |
| [when a user granted nothing tries to search their bootstrap scripts, it is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-search-their-bootstrap-scripts) | rejected |

**add_revision**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE on their own user replaces the content of their bootstrap script, revision 2 comes back](#revising-a-user-granted-update-adds-a-revision) | answered |
| [when a user granted only READ on their own user tries to replace the content of their bootstrap script, it is rejected for lack of permission](#revising-a-user-granted-read-may-not-add-a-revision) | rejected |

**bulk_get_current_revisions**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user loads the latest revision of their bootstrap script, that revision comes back](#batch_loading_revisions-a-user-granted-read-loads-their-bootstrap-script-current-revision) | answered |
| [when a user granted READ on their own user loads the latest revisions of their script and another user's script, the call succeeds but the entry of the other user's script is rejected for lack of permission](#batch_loading_revisions-a-strangers-bootstrap-script-revision-is-rejected-in-the-batch) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE on their own user adds a bootstrap script, revision 1 of the new script comes back](#creating-a-user-granted-update-adds-a-bootstrap-script) | answered |
| [when a user granted only READ on their own user tries to add a bootstrap script, it is rejected for lack of permission](#creating-a-user-granted-read-may-not-add-a-bootstrap-script) | rejected |

**switch_default**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE on their own user sets their bootstrap script that is not the default as the default, that script comes back](#switching_default-a-user-granted-update-switches-their-default-script) | answered |
| [when a user granted only READ on their own user tries to set their bootstrap script as the default, it is rejected for lack of permission](#switching_default-a-user-granted-read-may-not-switch-their-default-script) | rejected |

### bulk_get_ids

<a id="batch_loading-a-user-granted-read-loads-their-bootstrap-script-by-id"></a>

#### [a-user-granted-read-loads-their-bootstrap-script-by-id](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading.py): pass

when a user granted READ on their own user loads their bootstrap script by id, that script comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.bulk_get_ids: user-1 loads their default bootstrap script by id in one call

Then

- their one default script comes back
  - length = 1
  - [0].id: same as the seeded default script
  - [0].field_id: same as the id in the response
  - [0].user_id: same as the calling user
  - [0].created_at: the time this run wrote

<a id="batch_loading-a-strangers-bootstrap-script-is-rejected-in-the-batch"></a>

#### [a-strangers-bootstrap-script-is-rejected-in-the-batch](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading.py): pass

when a user granted READ on their own user loads their script and another user's script by id, the call succeeds but the entry of the other user's script is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and another user of the domain holds one bootstrap script, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - regular user user-2: holds one bootstrap script whose revision 1 holds 'echo stranger'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.bulk_get_ids: user-1 loads their default bootstrap script and the bootstrap script of another user by id in one call

Then

- their own script comes back, and the entry of the other user's script is rejected for lack of permission
  - length = 2
  - [0].id: same as the seeded default script
  - [0].field_id: same as the id in the response
  - [0].user_id: same as the calling user
  - [0].created_at: the time this run wrote
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-reads-their-bootstrap-script"></a>

#### [a-user-granted-read-reads-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_reading.py): pass

when a user granted READ on their own user reads their bootstrap script by id, that script comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.get: user-1 reads their default bootstrap script by id

Then

- the whole bootstrap script comes back
  - id: same as the seeded default script
  - field_id: same as the id in the response
  - user_id: same as the calling user
  - created_at: the time this run wrote

<a id="reading-a-user-granted-nothing-may-not-read-their-bootstrap-script"></a>

#### [a-user-granted-nothing-may-not-read-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_reading.py): pass

when a user granted nothing tries to read their bootstrap script by id, it is rejected with an answer that does not tell whether the script exists

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'

When

- BootstrapScriptAdapter.get: user-1 reads their default bootstrap script by id

Then

- the call is rejected
  - rejected: GenericBadRequest

### purge

<a id="purging-a-user-granted-update-purges-their-bootstrap-script"></a>

#### [a-user-granted-update-purges-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_purging.py): pass

when a user granted READ and UPDATE on their own user purges their bootstrap script that is not the default, the id of that script comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.purge: user-1 purges their bootstrap script that is not the default

Then

- the id of the purged script comes back
  - field_id: same as the seeded script that is not the default

<a id="purging-a-user-granted-read-may-not-purge-their-bootstrap-script"></a>

#### [a-user-granted-read-may-not-purge-their-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_purging.py): pass

when a user granted only READ on their own user tries to purge their bootstrap script, it is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.purge: user-1 purges their bootstrap script that is not the default

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-the-default-bootstrap-script-is-not-purged"></a>

#### [the-default-bootstrap-script-is-not-purged](/tests/scenario/bai_scenario/manager/bootstrap_script/test_purging.py): pass

when a user granted READ and UPDATE on their own user tries to purge their default bootstrap script, it is rejected until the default moves

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.purge: user-1 purges their default bootstrap script

Then

- the call is rejected
  - rejected: DefaultBootstrapScriptPurgeForbidden

### scoped_search

<a id="searching-a-user-granted-read-searches-their-bootstrap-scripts"></a>

#### [a-user-granted-read-searches-their-bootstrap-scripts](/tests/scenario/bai_scenario/manager/bootstrap_script/test_searching.py): pass

when a user granted READ on their own user searches their bootstrap scripts that are not the default, only that script comes back, not the default one nor the script of another user

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and another user of the domain holds one bootstrap script, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - regular user user-2: holds one bootstrap script whose revision 1 holds 'echo stranger'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.scoped_search: user-1 searches their bootstrap scripts that are not the default, latest created first, up to 10

Then

- only their one script that is not the default comes back
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - len(items) = 1
  - items[0].id: same as the seeded script that is not the default
  - items[0].field_id: same as the id in the response
  - items[0].user_id: same as the calling user
  - items[0].created_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-search-their-bootstrap-scripts"></a>

#### [a-user-granted-nothing-may-not-search-their-bootstrap-scripts](/tests/scenario/bai_scenario/manager/bootstrap_script/test_searching.py): pass

when a user granted nothing tries to search their bootstrap scripts, it is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'

When

- BootstrapScriptAdapter.scoped_search: user-1 searches their bootstrap scripts that are not the default, latest created first, up to 10

Then

- the call is rejected
  - rejected: NotEnoughPermission

### add_revision

<a id="revising-a-user-granted-update-adds-a-revision"></a>

#### [a-user-granted-update-adds-a-revision](/tests/scenario/bai_scenario/manager/bootstrap_script/test_revising.py): pass

when a user granted READ and UPDATE on their own user replaces the content of their bootstrap script, revision 2 comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.add_revision: user-1 replaces the content of their bootstrap script that is not the default with 'echo new'

Then

- the whole revision comes back
  - id: skipped: the database generates it
  - field_id: same as the id in the response
  - script_id: same as the seeded script that is not the default
  - revision_number = 2
  - script = 'echo new'
  - creator_id: same as the calling user
  - created_at: the time this run wrote

<a id="revising-a-user-granted-read-may-not-add-a-revision"></a>

#### [a-user-granted-read-may-not-add-a-revision](/tests/scenario/bai_scenario/manager/bootstrap_script/test_revising.py): pass

when a user granted only READ on their own user tries to replace the content of their bootstrap script, it is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.add_revision: user-1 replaces the content of their bootstrap script that is not the default with 'echo new'

Then

- the call is rejected
  - rejected: NotEnoughPermission

### bulk_get_current_revisions

<a id="batch_loading_revisions-a-user-granted-read-loads-their-bootstrap-script-current-revision"></a>

#### [a-user-granted-read-loads-their-bootstrap-script-current-revision](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading_revisions.py): pass

when a user granted READ on their own user loads the latest revision of their bootstrap script, that revision comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.bulk_get_current_revisions: user-1 loads the latest revision of their default bootstrap script in one call

Then

- the latest revision of their default script comes back
  - length = 1
  - [0].id: same as revision 1 of the seeded default script
  - [0].field_id: same as the id in the response
  - [0].script_id: same as the seeded default script
  - [0].revision_number = 1
  - [0].script = 'echo default'
  - [0].creator_id: same as the calling user
  - [0].created_at: the time this run wrote

<a id="batch_loading_revisions-a-strangers-bootstrap-script-revision-is-rejected-in-the-batch"></a>

#### [a-strangers-bootstrap-script-revision-is-rejected-in-the-batch](/tests/scenario/bai_scenario/manager/bootstrap_script/test_batch_loading_revisions.py): pass

when a user granted READ on their own user loads the latest revisions of their script and another user's script, the call succeeds but the entry of the other user's script is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and another user of the domain holds one bootstrap script, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - regular user user-2: holds one bootstrap script whose revision 1 holds 'echo stranger'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.bulk_get_current_revisions: user-1 loads the latest revision of their default bootstrap script and of the bootstrap script of another user in one call

Then

- their own script comes back, and the entry of the other user's script is rejected for lack of permission
  - length = 2
  - [0].id: same as revision 1 of the seeded default script
  - [0].field_id: same as the id in the response
  - [0].script_id: same as the seeded default script
  - [0].revision_number = 1
  - [0].script = 'echo default'
  - [0].creator_id: same as the calling user
  - [0].created_at: the time this run wrote
  - rejected: NotEnoughPermission

### create

<a id="creating-a-user-granted-update-adds-a-bootstrap-script"></a>

#### [a-user-granted-update-adds-a-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_creating.py): pass

when a user granted UPDATE on their own user adds a bootstrap script, revision 1 of the new script comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.create: user-1 adds a bootstrap script holding 'echo new' to their own user

Then

- the whole revision comes back
  - id: skipped: the database generates it
  - field_id: same as the id in the response
  - script_id: skipped: the database generates it
  - revision_number = 1
  - script = 'echo new'
  - creator_id: same as the calling user
  - created_at: the time this run wrote

<a id="creating-a-user-granted-read-may-not-add-a-bootstrap-script"></a>

#### [a-user-granted-read-may-not-add-a-bootstrap-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_creating.py): pass

when a user granted only READ on their own user tries to add a bootstrap script, it is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.create: user-1 adds a bootstrap script holding 'echo new' to their own user

Then

- the call is rejected
  - rejected: NotEnoughPermission

### switch_default

<a id="switching_default-a-user-granted-update-switches-their-default-script"></a>

#### [a-user-granted-update-switches-their-default-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_switching_default.py): pass

when a user granted UPDATE on their own user sets their bootstrap script that is not the default as the default, that script comes back

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.switch_default: user-1 sets their bootstrap script that is not the default as the default

Then

- the whole bootstrap script comes back
  - id: same as the seeded script that is not the default
  - field_id: same as the id in the response
  - user_id: same as the calling user
  - created_at: the time this run wrote

<a id="switching_default-a-user-granted-read-may-not-switch-their-default-script"></a>

#### [a-user-granted-read-may-not-switch-their-default-script](/tests/scenario/bai_scenario/manager/bootstrap_script/test_switching_default.py): pass

when a user granted only READ on their own user tries to set their bootstrap script as the default, it is rejected for lack of permission

Given

- one domain and one user holding one default bootstrap script and one that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo default'
  - regular user user-1: sets that bootstrap script as the default
  - regular user user-1: holds one bootstrap script whose revision 1 holds 'echo extra'
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- BootstrapScriptAdapter.switch_default: user-1 sets their bootstrap script that is not the default as the default

Then

- the call is rejected
  - rejected: NotEnoughPermission

