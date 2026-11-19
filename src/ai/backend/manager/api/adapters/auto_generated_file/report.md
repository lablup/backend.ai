## auto_generated_file

[adapter](/src/ai/backend/manager/api/adapters/auto_generated_file/adapter.py)

Scenario: complete

- built from ops (4)
  - get_default_auto_generated_file_by_path: representative success ✓ · representative rejection ✓
  - list_default_auto_generated_files: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - purge_default_auto_generated_file: representative success ✓ · representative rejection ✓
- ops + direct implementation (1)
  - update_default_auto_generated_file: success present 1 · rejection present 2 (scope_search_ops, single_entity)
- direct implementation (2)
  - create: success present 1 · rejection present 1 (scope)
  - create_default_auto_generated_file: success present 1 · rejection present 2 (scope, single_entity)

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
| [when a user holding CREATE tries to write an auto-generated file where the manager keeps its own, input validation rejects it](#config_files-an-auto-generated-file-in-a-place-the-manager-keeps-is-refused) | rejected |

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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
  - Default auto-generated file .vimrc: set as the default of its path
  - Auto-generated file .bashrc: permission 644
  - Auto-generated file .bashrc: has one revision whose content is 'export EDITOR=vim\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'

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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - Auto-generated file .vimrc: permission 644
  - Auto-generated file .vimrc: has one revision whose content is 'set number\n'
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
  - permission = '644'
  - is_default = False

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

<a id="config_files-an-auto-generated-file-in-a-place-the-manager-keeps-is-refused"></a>

#### [an-auto-generated-file-in-a-place-the-manager-keeps-is-refused](/tests/scenario/bai_scenario/manager/auto_generated_file/test_config_files.py): pass

when a user holding CREATE tries to write an auto-generated file where the manager keeps its own, input validation rejects it

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

- AutoGeneratedFileAdapter.create_default_auto_generated_file: user-1 tries to write an auto-generated file where the manager keeps its own

Then

- the call is rejected
  - rejected: InvalidDotfilePath

