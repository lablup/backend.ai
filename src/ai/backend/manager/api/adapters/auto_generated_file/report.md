## auto_generated_file

[adapter](/src/ai/backend/manager/api/adapters/auto_generated_file/adapter.py)

Scenario: complete

- built from ops (10)
  - add_revision: representative success ✓ · representative rejection ✓
  - bulk_get_ids: representative success ✓ · representative rejection ✓
  - bulk_get_revision_ids: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - get_default_auto_generated_file_by_path: representative success ✓ · representative rejection ✓
  - list_default_auto_generated_files: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - purge_default_auto_generated_file: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - search_revisions: representative success ✓ · representative rejection ✓
- ops + direct implementation (1)
  - update_default_auto_generated_file: success present 1 · rejection present 2 (scope_search_ops, single_entity)
- direct implementation (3)
  - create: success present 1 · rejection present 1 (scope)
  - create_default_auto_generated_file: success present 1 · rejection present 1 (scope, single_entity)
  - switch_default: success present 1 · rejection present 1 (single_entity)

**add_revision**

| scenario | verdict |
|---|---|
| [when a user holding UPDATE adds a revision to their auto-generated file, the content and permission come back as revision 2 and revision 1 stays](#v2_revisions-a-user-granted-update-adds-a-revision-to-an-auto-generated-file) | answered |
| [a user holding no permission who tries to add a revision to their auto-generated file is rejected for lack of permission, and revision 1 stays the only one](#v2_revisions-a-user-granted-nothing-may-not-add-a-revision-to-an-auto-generated-file) | rejected |

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when a user holding READ loads their auto-generated file by id in one call, that file comes back](#v2_reading-a-user-granted-read-loads-an-auto-generated-file-by-id) | answered |
| [when a user holding no permission loads their auto-generated file by id in one call, the call succeeds but that entry is rejected for lack of permission](#v2_reading-a-user-granted-nothing-gets-a-rejection-for-an-auto-generated-file) | rejected |

**bulk_get_revision_ids**

| scenario | verdict |
|---|---|
| [when a user holding READ loads a revision of their auto-generated file by id in one call, that revision comes back](#v2_revisions-a-user-granted-read-loads-a-revision-of-an-auto-generated-file-by-id) | answered |
| [when a user holding no permission loads a revision of their auto-generated file by id in one call, the call succeeds but that entry is rejected for lack of permission](#v2_revisions-a-user-granted-nothing-gets-a-rejection-for-a-revision) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user holding READ reads their auto-generated file by id, that file comes back](#v2_reading-a-user-granted-read-gets-an-auto-generated-file) | answered |
| [a user holding no permission who tries to read their auto-generated file by id is rejected for lack of permission](#v2_reading-a-user-granted-nothing-may-not-get-an-auto-generated-file) | rejected |

**get_default_auto_generated_file_by_path**

| scenario | verdict |
|---|---|
| [when a user holding READ reads an auto-generated file set as default, the content of its last revision comes back](#config_files-a-user-granted-read-on-their-auto-generated-files-reads-the-default-one) | answered |
| [a user holding no permission who tries to read their own auto-generated file is rejected for lack of permission](#config_files-a-user-granted-nothing-may-not-read-an-auto-generated-file) | rejected |
| [when a user holding READ reads an auto-generated file not set as default, it is rejected as not found](#config_files-an-auto-generated-file-that-is-not-set-as-default-is-not-found) | rejected |

**list_default_auto_generated_files**

| scenario | verdict |
|---|---|
| [when a user holding READ on auto-generated files in a domain's scope lists the domain's files, the file set as default comes back](#organization_files-a-user-granted-file-read-in-a-domain-lists-its-auto-generated-files) | answered |
| [when a user holding READ on auto-generated files in a project's scope lists the project's files, the file set as default comes back](#organization_files-a-user-granted-file-read-in-a-project-lists-its-auto-generated-files) | answered |
| [when a user holding READ lists their auto-generated files, only the ones set as default come back, with their last revision's content](#config_files-a-user-granted-read-on-their-auto-generated-files-lists-only-the-default-ones) | answered |
| [a user holding no permission who tries to list their own auto-generated files is rejected for lack of permission](#config_files-a-user-granted-nothing-may-not-list-their-auto-generated-files) | rejected |
| [a user holding only READ on the domain who tries to list the domain's auto-generated files is rejected for lack of permission](#organization_files-a-user-granted-only-domain-read-may-not-list-its-auto-generated-files) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user holding HARD_DELETE purges their auto-generated file not set as default, the id of the file comes back and the file and its revisions are gone](#v2_files-a-user-granted-hard-delete-purges-an-auto-generated-file-not-set-as-default) | answered |
| [a user holding no permission who tries to purge their auto-generated file is rejected for lack of permission](#v2_files-a-user-granted-nothing-may-not-purge-an-auto-generated-file) | rejected |
| [when a user holding HARD_DELETE tries to purge their auto-generated file set as default, it is rejected and the file stays](#v2_files-purging-the-auto-generated-file-set-as-default-is-refused) | rejected |

**purge_default_auto_generated_file**

| scenario | verdict |
|---|---|
| [when a user holding READ and HARD_DELETE deletes an auto-generated file set as default, a response saying it was deleted comes back, and the file and its revisions are gone](#config_files-a-user-granted-read-and-hard-delete-on-their-auto-generated-files-deletes-the-default-one) | answered |
| [a user holding no permission who tries to delete their own auto-generated file is rejected for lack of permission](#config_files-a-user-granted-nothing-may-not-delete-an-auto-generated-file) | rejected |
| [when a user holding READ and HARD_DELETE deletes an auto-generated file not set as default, it is rejected as not found](#config_files-deleting-an-auto-generated-file-that-is-not-set-as-default-is-not-found) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user holding READ lists the auto-generated files of their own scope that are set as default, ordered by path and limited to one page, their file not set as default and another user's file are left out, and only their two files come back in path order](#v2_search-a-user-granted-read-lists-their-auto-generated-files-set-as-default) | answered |
| [a user holding no permission who tries to list the auto-generated files of their own scope is rejected for lack of permission](#v2_search-a-user-granted-nothing-may-not-list-auto-generated-files) | rejected |

**search_revisions**

| scenario | verdict |
|---|---|
| [when a user holding READ reads one page of the revisions of their auto-generated file filtered by number, the revisions filtered out and those of another file are left out, and only that file's revisions come back in order](#v2_revisions-a-user-granted-read-searches-the-revisions-of-an-auto-generated-file) | answered |
| [a user holding no permission who tries to read the revisions of their auto-generated file is rejected for lack of permission](#v2_revisions-a-user-granted-nothing-may-not-search-the-revisions-of-an-auto-generated-file) | rejected |

**update_default_auto_generated_file**

| scenario | verdict |
|---|---|
| [when a user holding READ and UPDATE changes an auto-generated file set as default, an empty response comes back, the file's permission changes and the new content is added as revision 2](#config_files-a-user-granted-read-and-update-on-their-auto-generated-files-updates-the-default-one) | answered |
| [a user holding no permission who tries to change their own auto-generated file is rejected for lack of permission](#config_files-a-user-granted-nothing-may-not-update-an-auto-generated-file) | rejected |
| [when a user holding READ and UPDATE changes an auto-generated file not set as default, it is rejected as not found](#config_files-updating-an-auto-generated-file-that-is-not-set-as-default-is-not-found) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user holding CREATE on their own auto-generated files creates one, the file comes back not set as default, and its content stays as revision 1](#v2_files-a-user-granted-create-creates-an-auto-generated-file-not-set-as-default) | answered |
| [a user holding no permission who tries to create their own auto-generated file is rejected for lack of permission](#v2_files-a-user-granted-nothing-may-not-create-an-auto-generated-file) | rejected |

**create_default_auto_generated_file**

| scenario | verdict |
|---|---|
| [when a user holding CREATE and UPDATE on their own auto-generated files writes one, an empty response comes back, and the file holds its content as revision 1 and is set as the default of its path](#config_files-a-user-granted-create-and-update-on-their-auto-generated-files-writes-one) | answered |
| [a user holding no permission who tries to write their own auto-generated file is rejected for lack of permission](#config_files-a-user-granted-nothing-may-not-write-an-auto-generated-file) | rejected |

**switch_default**

| scenario | verdict |
|---|---|
| [when a user holding UPDATE sets their auto-generated file not set as default as the default of its path, that file comes back set as default and the previous default stays as a file not set as default](#v2_default-a-user-granted-update-switches-the-default-auto-generated-file-of-a-path) | answered |
| [a user holding no permission who tries to set their auto-generated file as the default is rejected for lack of permission](#v2_default-a-user-granted-nothing-may-not-switch-the-default-auto-generated-file) | rejected |

### add_revision

<a id="v2_revisions-a-user-granted-update-adds-a-revision-to-an-auto-generated-file"></a>

#### [a-user-granted-update-adds-a-revision-to-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

when a user holding UPDATE adds a revision to their auto-generated file, the content and permission come back as revision 2 and revision 1 stays

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the UPDATE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the UPDATE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: UPDATE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.add_revision: user-1 adds 'set nonumber\n' with permission 600 as the next revision of their .vimrc auto-generated file

Then

- the content added comes back as revision 2
  - id: skipped: the database generates it
  - field_id: skipped: the database generates it
  - auto_generated_file_id: same as the id of the .vimrc auto-generated file seeded
  - revision_number = 2
  - data = 'set nonumber\n'
  - permission = '600'
  - creator_id: same as the owner's id
  - created_at: the time this run wrote

<a id="v2_revisions-a-user-granted-nothing-may-not-add-a-revision-to-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-add-a-revision-to-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

a user holding no permission who tries to add a revision to their auto-generated file is rejected for lack of permission, and revision 1 stays the only one

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644

When

- AutoGeneratedFileAdapter.add_revision: user-1 adds 'set nonumber\n' with permission 600 as the next revision of their .vimrc auto-generated file

Then

- the call is rejected
  - rejected: NotEnoughPermission

### bulk_get_ids

<a id="v2_reading-a-user-granted-read-loads-an-auto-generated-file-by-id"></a>

#### [a-user-granted-read-loads-an-auto-generated-file-by-id](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

when a user holding READ loads their auto-generated file by id in one call, that file comes back

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.bulk_get_ids: user-1 loads their .vimrc auto-generated file by id in one call

Then

- the one file seeded comes back
  - length = 1
  - id: same as the id of the .vimrc auto-generated file seeded
  - entity_id: same as the id of the .vimrc auto-generated file seeded
  - scope_type = 'user'
  - scope_id: same as the owner's id
  - path = '.vimrc'
  - is_default = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="v2_reading-a-user-granted-nothing-gets-a-rejection-for-an-auto-generated-file"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

when a user holding no permission loads their auto-generated file by id in one call, the call succeeds but that entry is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644

When

- AutoGeneratedFileAdapter.bulk_get_ids: user-1 loads their .vimrc auto-generated file by id in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### bulk_get_revision_ids

<a id="v2_revisions-a-user-granted-read-loads-a-revision-of-an-auto-generated-file-by-id"></a>

#### [a-user-granted-read-loads-a-revision-of-an-auto-generated-file-by-id](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

when a user holding READ loads a revision of their auto-generated file by id in one call, that revision comes back

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.bulk_get_revision_ids: user-1 loads revision 1 of their .vimrc auto-generated file by id in one call

Then

- revision 1 comes back alone
  - length = 1
  - id: same as the id of the revision seeded
  - field_id: same as the id of the revision seeded
  - auto_generated_file_id: same as the id of the .vimrc auto-generated file seeded
  - revision_number = 1
  - data = 'set number\n'
  - permission = '644'
  - creator_id: same as the owner's id
  - created_at: the time this run wrote

<a id="v2_revisions-a-user-granted-nothing-gets-a-rejection-for-a-revision"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-a-revision](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

when a user holding no permission loads a revision of their auto-generated file by id in one call, the call succeeds but that entry is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644

When

- AutoGeneratedFileAdapter.bulk_get_revision_ids: user-1 loads revision 1 of their .vimrc auto-generated file by id in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### get

<a id="v2_reading-a-user-granted-read-gets-an-auto-generated-file"></a>

#### [a-user-granted-read-gets-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

when a user holding READ reads their auto-generated file by id, that file comes back

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.get: user-1 reads their .vimrc auto-generated file by id

Then

- the file seeded comes back
  - id: same as the id of the .vimrc auto-generated file seeded
  - entity_id: same as the id of the .vimrc auto-generated file seeded
  - scope_type = 'user'
  - scope_id: same as the owner's id
  - path = '.vimrc'
  - is_default = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="v2_reading-a-user-granted-nothing-may-not-get-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-get-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_reading.py): pass

a user holding no permission who tries to read their auto-generated file by id is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644

When

- AutoGeneratedFileAdapter.get: user-1 reads their .vimrc auto-generated file by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_default_auto_generated_file_by_path

<a id="config_files-a-user-granted-read-on-their-auto-generated-files-reads-the-default-one"></a>

#### [a-user-granted-read-on-their-auto-generated-files-reads-the-default-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ reads an auto-generated file set as default, the content of its last revision comes back

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.get_default_auto_generated_file_by_path: user-1 reads one of their own auto-generated files

Then

- the default file of the path comes back with its last revision's content
  - response = {'path': '.vimrc', 'perm': '644', 'data': 'set number\n'}

<a id="config_files-a-user-granted-nothing-may-not-read-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-read-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

a user holding no permission who tries to read their own auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AutoGeneratedFileAdapter.get_default_auto_generated_file_by_path: user-1 reads one of their own auto-generated files

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="config_files-an-auto-generated-file-that-is-not-set-as-default-is-not-found"></a>

#### [an-auto-generated-file-that-is-not-set-as-default-is-not-found](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ reads an auto-generated file not set as default, it is rejected as not found

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.get_default_auto_generated_file_by_path: user-1 reads one of their own auto-generated files

Then

- the call is rejected
  - rejected: DotfileNotFound

### list_default_auto_generated_files

<a id="organization_files-a-user-granted-file-read-in-a-domain-lists-its-auto-generated-files"></a>

#### [a-user-granted-file-read-in-a-domain-lists-its-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_organization_files.py): pass

when a user holding READ on auto-generated files in a domain's scope lists the domain's files, the file set as default comes back

Given

- one domain holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), and a user holds the auto_generated_file READ permissions through a role in that domain's scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Role config-file-reader-1: applies only within the scope it is granted in
  - Role config-file-reader-1: READ allowed on every auto_generated_file
  - regular user user-1: holds Role config-file-reader-1

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1 lists the auto-generated files of the owner set as default

Then

- the owner's one default file comes back with its path, permission and content
  - response = [{'path': '.vimrc', 'permission': '644', 'data': 'set number\n'}]

<a id="organization_files-a-user-granted-file-read-in-a-project-lists-its-auto-generated-files"></a>

#### [a-user-granted-file-read-in-a-project-lists-its-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_organization_files.py): pass

when a user holding READ on auto-generated files in a project's scope lists the project's files, the file set as default comes back

Given

- one project holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), and a user holds the auto_generated_file READ permissions through a role in that project's scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Role config-file-reader-1: applies only within the scope it is granted in
  - Role config-file-reader-1: READ allowed on every auto_generated_file
  - regular user user-1: holds Role config-file-reader-1

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1 lists the auto-generated files of the owner set as default

Then

- the owner's one default file comes back with its path, permission and content
  - response = [{'path': '.vimrc', 'permission': '644', 'data': 'set number\n'}]

<a id="config_files-a-user-granted-read-on-their-auto-generated-files-lists-only-the-default-ones"></a>

#### [a-user-granted-read-on-their-auto-generated-files-lists-only-the-default-ones](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ lists their auto-generated files, only the ones set as default come back, with their last revision's content

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds a .bashrc auto-generated file not set as default (permission 644, revision 1 holding 'export EDITOR=vim\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Auto-generated file .bashrc: not set as default
  - Auto-generated file .bashrc: has one revision whose content is 'export EDITOR=vim\n' and permission 644
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1 lists the auto-generated files of theirs set as default

Then

- only the .vimrc file set as default is listed, with its last revision's content
  - files = [('.vimrc', '644', 'set number\n')]

<a id="config_files-a-user-granted-nothing-may-not-list-their-auto-generated-files"></a>

#### [a-user-granted-nothing-may-not-list-their-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

a user holding no permission who tries to list their own auto-generated files is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1 lists the auto-generated files of theirs set as default

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="organization_files-a-user-granted-only-domain-read-may-not-list-its-auto-generated-files"></a>

#### [a-user-granted-only-domain-read-may-not-list-its-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_organization_files.py): pass

a user holding only READ on the domain who tries to list the domain's auto-generated files is rejected for lack of permission

Given

- one domain holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), and a user holds the domain READ permissions through a role in that domain's scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Role config-file-reader-1: applies only within the scope it is granted in
  - Role config-file-reader-1: READ allowed on every domain
  - regular user user-1: holds Role config-file-reader-1

When

- AutoGeneratedFileAdapter.list_default_auto_generated_files: user-1 lists the auto-generated files of the owner set as default

Then

- the call is rejected
  - rejected: NotEnoughPermission

### purge

<a id="v2_files-a-user-granted-hard-delete-purges-an-auto-generated-file-not-set-as-default"></a>

#### [a-user-granted-hard-delete-purges-an-auto-generated-file-not-set-as-default](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

when a user holding HARD_DELETE purges their auto-generated file not set as default, the id of the file comes back and the file and its revisions are gone

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the HARD_DELETE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the HARD_DELETE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: HARD_DELETE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.purge: user-1 purges their .vimrc auto-generated file

Then

- the id of the file purged comes back
  - entity_id: same as the .vimrc auto-generated file seeded

<a id="v2_files-a-user-granted-nothing-may-not-purge-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-purge-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

a user holding no permission who tries to purge their auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644

When

- AutoGeneratedFileAdapter.purge: user-1 purges their .vimrc auto-generated file

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="v2_files-purging-the-auto-generated-file-set-as-default-is-refused"></a>

#### [purging-the-auto-generated-file-set-as-default-is-refused](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

when a user holding HARD_DELETE tries to purge their auto-generated file set as default, it is rejected and the file stays

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds the HARD_DELETE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - a role assignment granting the HARD_DELETE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: HARD_DELETE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.purge: user-1 purges their .vimrc auto-generated file

Then

- the call is rejected
  - rejected: DefaultDotfilePurgeForbidden

### purge_default_auto_generated_file

<a id="config_files-a-user-granted-read-and-hard-delete-on-their-auto-generated-files-deletes-the-default-one"></a>

#### [a-user-granted-read-and-hard-delete-on-their-auto-generated-files-deletes-the-default-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ and HARD_DELETE deletes an auto-generated file set as default, a response saying it was deleted comes back, and the file and its revisions are gone

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ, HARD_DELETE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - a role assignment granting the READ, HARD_DELETE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - Role config-file-role-1: HARD_DELETE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.purge_default_auto_generated_file: user-1 deletes one of their own auto-generated files

Then

- a response saying it was deleted comes back
  - response = {'success': True}

<a id="config_files-a-user-granted-nothing-may-not-delete-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-delete-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

a user holding no permission who tries to delete their own auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AutoGeneratedFileAdapter.purge_default_auto_generated_file: user-1 deletes one of their own auto-generated files

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="config_files-deleting-an-auto-generated-file-that-is-not-set-as-default-is-not-found"></a>

#### [deleting-an-auto-generated-file-that-is-not-set-as-default-is-not-found](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ and HARD_DELETE deletes an auto-generated file not set as default, it is rejected as not found

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ, HARD_DELETE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the READ, HARD_DELETE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - Role config-file-role-1: HARD_DELETE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.purge_default_auto_generated_file: user-1 deletes one of their own auto-generated files

Then

- the call is rejected
  - rejected: DotfileNotFound

### scoped_search

<a id="v2_search-a-user-granted-read-lists-their-auto-generated-files-set-as-default"></a>

#### [a-user-granted-read-lists-their-auto-generated-files-set-as-default](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_search.py): pass

when a user holding READ lists the auto-generated files of their own scope that are set as default, ordered by path and limited to one page, their file not set as default and another user's file are left out, and only their two files come back in path order

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds a .bashrc auto-generated file set as default (permission 644, revision 1 holding 'export EDITOR=vim\n'), another user of the domain holds a .vimrc auto-generated file set as default, the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Auto-generated file .bashrc: not set as default
  - Auto-generated file .bashrc: has one revision whose content is 'export EDITOR=vim\n' and permission 644
  - Default auto-generated file .bashrc: set as the default of its path
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.scoped_search: user-1 lists up to 10 auto-generated files of their own scope that are set as default, ordered by path

Then

- one page holding only their two files set as default, in path order, comes back
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the .bashrc file seeded as default
  - items[0].entity_id: same as the .bashrc file seeded as default
  - items[0].scope_type = 'user'
  - items[0].scope_id: same as the owner's id
  - items[0].path = '.bashrc'
  - items[0].is_default = True
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: same as the .vimrc file seeded as default
  - items[1].entity_id: same as the .vimrc file seeded as default
  - items[1].scope_type = 'user'
  - items[1].scope_id: same as the owner's id
  - items[1].path = '.vimrc'
  - items[1].is_default = True
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote

<a id="v2_search-a-user-granted-nothing-may-not-list-auto-generated-files"></a>

#### [a-user-granted-nothing-may-not-list-auto-generated-files](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_search.py): pass

a user holding no permission who tries to list the auto-generated files of their own scope is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path

When

- AutoGeneratedFileAdapter.scoped_search: user-1 lists up to 10 auto-generated files of their own scope that are set as default, ordered by path

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_revisions

<a id="v2_revisions-a-user-granted-read-searches-the-revisions-of-an-auto-generated-file"></a>

#### [a-user-granted-read-searches-the-revisions-of-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

when a user holding READ reads one page of the revisions of their auto-generated file filtered by number, the revisions filtered out and those of another file are left out, and only that file's revisions come back in order

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n', revision 2 holding 'set nonumber\n', revision 3 holding 'set relativenumber\n'), the user holds a .bashrc auto-generated file not set as default (permission 644, revision 1 holding 'export EDITOR=vim\n'), the user holds the READ permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set nonumber\n' and permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set relativenumber\n' and permission 644
  - Auto-generated file .bashrc: not set as default
  - Auto-generated file .bashrc: has one revision whose content is 'export EDITOR=vim\n' and permission 644
  - a role assignment granting the READ permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.search_revisions: user-1 reads one revision numbered 2 or above of their .vimrc auto-generated file, in descending revision order

Then

- revision 1 and the revisions of the other file are left out; revision 3 comes back alone, out of a total of 2
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - len(items) = 1
  - id: same as the id of the revision seeded
  - field_id: same as the id of the revision seeded
  - auto_generated_file_id: same as the id of the .vimrc auto-generated file seeded
  - revision_number = 3
  - data = 'set relativenumber\n'
  - permission = '644'
  - creator_id: same as the owner's id
  - created_at: the time this run wrote

<a id="v2_revisions-a-user-granted-nothing-may-not-search-the-revisions-of-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-search-the-revisions-of-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_revisions.py): pass

a user holding no permission who tries to read the revisions of their auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n', revision 2 holding 'set nonumber\n', revision 3 holding 'set relativenumber\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set nonumber\n' and permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set relativenumber\n' and permission 644

When

- AutoGeneratedFileAdapter.search_revisions: user-1 reads one revision numbered 2 or above of their .vimrc auto-generated file, in descending revision order

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update_default_auto_generated_file

<a id="config_files-a-user-granted-read-and-update-on-their-auto-generated-files-updates-the-default-one"></a>

#### [a-user-granted-read-and-update-on-their-auto-generated-files-updates-the-default-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ and UPDATE changes an auto-generated file set as default, an empty response comes back, the file's permission changes and the new content is added as revision 2

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ, UPDATE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - a role assignment granting the READ, UPDATE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - Role config-file-role-1: UPDATE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.update_default_auto_generated_file: user-1 changes their .vimrc auto-generated file to permission 600 and content 'set nonumber\n'

Then

- the path of the file updated comes back with its new permission and content
  - path = '.vimrc'
  - perm = '600'
  - data = 'set nonumber\n'

<a id="config_files-a-user-granted-nothing-may-not-update-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-update-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

a user holding no permission who tries to change their own auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AutoGeneratedFileAdapter.update_default_auto_generated_file: user-1 changes their .vimrc auto-generated file to permission 600 and content 'set nonumber\n'

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="config_files-updating-an-auto-generated-file-that-is-not-set-as-default-is-not-found"></a>

#### [updating-an-auto-generated-file-that-is-not-set-as-default-is-not-found](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding READ and UPDATE changes an auto-generated file not set as default, it is rejected as not found

Given

- one domain and one user, the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the READ, UPDATE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the READ, UPDATE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: READ allowed on every auto_generated_file
    - Role config-file-role-1: UPDATE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.update_default_auto_generated_file: user-1 changes their .vimrc auto-generated file to permission 600 and content 'set nonumber\n'

Then

- the call is rejected
  - rejected: DotfileNotFound

### create

<a id="v2_files-a-user-granted-create-creates-an-auto-generated-file-not-set-as-default"></a>

#### [a-user-granted-create-creates-an-auto-generated-file-not-set-as-default](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

when a user holding CREATE on their own auto-generated files creates one, the file comes back not set as default, and its content stays as revision 1

Given

- one domain and one user, the user holds the CREATE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the CREATE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: CREATE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.create: user-1 writes a .vimrc auto-generated file of their own

Then

- the new file, not set as default, comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - scope_type = 'user'
  - scope_id: same as the owner's id
  - path = '.vimrc'
  - is_default = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="v2_files-a-user-granted-nothing-may-not-create-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-create-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_files.py): pass

a user holding no permission who tries to create their own auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AutoGeneratedFileAdapter.create: user-1 writes a .vimrc auto-generated file of their own

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create_default_auto_generated_file

<a id="config_files-a-user-granted-create-and-update-on-their-auto-generated-files-writes-one"></a>

#### [a-user-granted-create-and-update-on-their-auto-generated-files-writes-one](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding CREATE and UPDATE on their own auto-generated files writes one, an empty response comes back, and the file holds its content as revision 1 and is set as the default of its path

Given

- one domain and one user, the user holds the CREATE, UPDATE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the CREATE, UPDATE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: CREATE allowed on every auto_generated_file
    - Role config-file-role-1: UPDATE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.create_default_auto_generated_file: user-1 writes one of their own auto-generated files

Then

- the path, permission and content of the file written come back as is
  - path = '.vimrc'
  - perm = '644'
  - data = 'set number\n'

<a id="config_files-a-user-granted-nothing-may-not-write-an-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-write-an-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

a user holding no permission who tries to write their own auto-generated file is rejected for lack of permission

Given

- one domain and one user, the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AutoGeneratedFileAdapter.create_default_auto_generated_file: user-1 writes one of their own auto-generated files

Then

- the call is rejected
  - rejected: NotEnoughPermission

### switch_default

<a id="v2_default-a-user-granted-update-switches-the-default-auto-generated-file-of-a-path"></a>

#### [a-user-granted-update-switches-the-default-auto-generated-file-of-a-path](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_default.py): pass

when a user holding UPDATE sets their auto-generated file not set as default as the default of its path, that file comes back set as default and the previous default stays as a file not set as default

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds the UPDATE permission on their own auto-generated files
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - a role assignment granting the UPDATE permissions on their own auto-generated files
    - Role config-file-role-1: applies only within the scope it is granted in
    - Role config-file-role-1: UPDATE allowed on every auto_generated_file
    - regular user user-1: holds Role config-file-role-1

When

- AutoGeneratedFileAdapter.switch_default: user-1 sets their .vimrc auto-generated file not set as default as the default

Then

- the file switched to comes back set as default
  - id: same as the file seeded not set as default
  - entity_id: same as the file seeded not set as default
  - scope_type = 'user'
  - scope_id: same as the owner's id
  - path = '.vimrc'
  - is_default = True
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="v2_default-a-user-granted-nothing-may-not-switch-the-default-auto-generated-file"></a>

#### [a-user-granted-nothing-may-not-switch-the-default-auto-generated-file](/tests/scenario/bai_scenario/manager/auto_generated_file/test_v2_default.py): pass

a user holding no permission who tries to set their auto-generated file as the default is rejected for lack of permission

Given

- one domain and one user, the user holds a .vimrc auto-generated file set as default (permission 644, revision 1 holding 'set number\n'), the user holds a .vimrc auto-generated file not set as default (permission 644, revision 1 holding 'set number\n'), the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644
  - Default auto-generated file .vimrc: set as the default of its path
  - Auto-generated file .vimrc: not set as default
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n' and permission 644

When

- AutoGeneratedFileAdapter.switch_default: user-1 sets their .vimrc auto-generated file not set as default as the default

Then

- the call is rejected
  - rejected: NotEnoughPermission

