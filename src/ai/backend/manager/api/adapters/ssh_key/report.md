## ssh_key

[adapter](/src/ai/backend/manager/api/adapters/ssh_key/adapter.py)

Scenario: complete

- built from ops (3)
  - bulk_get_ids: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - my_upload: success present 2 · rejection present 2 (single_entity)
  - switch_default: success present 1 · rejection present 1 (single_field)

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user loads two of their own SSH keys by id, both come back](#batch_loading-a-user-granted-read-loads-their-own-keys) | answered |
| [when a user granted READ on their own user loads their own SSH key together with another user's, only the other user's key is rejected](#batch_loading-a-user-granted-read-is-denied-another-users-key) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user reads their SSH key by its id, that key comes back](#getting-a-user-granted-read-reads-their-key) | answered |
| [a user granted no permission on their own user who tries to read their SSH key is rejected at the owner lookup step with the same exception as a key that does not exist](#getting-a-user-without-read-may-not-read-their-key) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted READ on their own user searches their SSH keys for the default one, only their default key comes back and no other user's key](#searching-a-user-granted-read-finds-their-default-key) | answered |
| [when a user granted no permission on their own user tries to search their SSH keys, it is rejected for lack of permission](#searching-a-user-without-read-may-not-search-their-keys) | rejected |

**my_upload**

| scenario | verdict |
|---|---|
| [when a user granted UPDATE on their own user and holding no SSH key uploads one, it comes back as the default](#uploading-a-user-granted-update-uploads-their-first-key-as-the-default) | answered |
| [when a user granted UPDATE on their own user and already holding a default SSH key uploads one, it comes back as not the default](#uploading-a-user-holding-a-default-uploads-a-key-that-is-not-the-default) | answered |
| [when a user granted only READ on their own user tries to upload an SSH key, it is rejected for lack of permission](#uploading-a-user-granted-read-may-not-upload-a-key) | rejected |
| [even a user granted UPDATE on their own user is rejected when the value they upload is not a public key](#uploading-a-value-that-is-not-a-public-key-is-rejected) | rejected |

**switch_default**

| scenario | verdict |
|---|---|
| [when a user granted READ and UPDATE on their own user sets their SSH key that is not the default as the default, that key comes back as the default](#switching_default-a-user-granted-update-switches-their-default-key) | answered |
| [when a user granted only READ on their own user tries to set their SSH key as the default, it is rejected for lack of permission](#switching_default-a-user-granted-read-may-not-switch-their-default-key) | rejected |

### bulk_get_ids

<a id="batch_loading-a-user-granted-read-loads-their-own-keys"></a>

#### [a-user-granted-read-loads-their-own-keys](/tests/scenario/bai_scenario/manager/ssh_key/test_batch_loading.py): pass

when a user granted READ on their own user loads two of their own SSH keys by id, both come back

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.bulk_get_ids: user-1 loads two of their own SSH keys by id together

Then

- both SSH keys come back in the order asked
  - length = 2
  - [0].id: same as the seeded SSH key
  - [0].field_id: same as the seeded SSH key
  - [0].user_id: same as the calling user
  - [0].public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv'
  - [0].is_default = True
  - [1].id: same as the seeded SSH key
  - [1].field_id: same as the seeded SSH key
  - [1].user_id: same as the calling user
  - [1].public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFYD/Yrss1np0I+R9f51bEJ0Jjs+d0s4JUussQhs0WBG'
  - [1].is_default = False

<a id="batch_loading-a-user-granted-read-is-denied-another-users-key"></a>

#### [a-user-granted-read-is-denied-another-users-key](/tests/scenario/bai_scenario/manager/ssh_key/test_batch_loading.py): pass

when a user granted READ on their own user loads their own SSH key together with another user's, only the other user's key is rejected

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, another user holding a default SSH key, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - regular user user-2: holds one default SSH key
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.bulk_get_ids: user-1 loads their own SSH key and another user's SSH key by id together

Then

- their own SSH key comes back, and a rejection stands in the place of the other user's SSH key
  - length = 2
  - [0].id: same as the seeded SSH key
  - [0].field_id: same as the seeded SSH key
  - [0].user_id: same as the calling user
  - [0].public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv'
  - [0].is_default = True
  - rejected: NotEnoughPermission

### get

<a id="getting-a-user-granted-read-reads-their-key"></a>

#### [a-user-granted-read-reads-their-key](/tests/scenario/bai_scenario/manager/ssh_key/test_getting.py): pass

when a user granted READ on their own user reads their SSH key by its id, that key comes back

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.get: user-1 reads their default SSH key by its id

Then

- the whole SSH key comes back
  - id: same as the seeded SSH key
  - field_id: same as the id in the response
  - user_id: same as the calling user
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv'
  - is_default = True

<a id="getting-a-user-without-read-may-not-read-their-key"></a>

#### [a-user-without-read-may-not-read-their-key](/tests/scenario/bai_scenario/manager/ssh_key/test_getting.py): pass

a user granted no permission on their own user who tries to read their SSH key is rejected at the owner lookup step with the same exception as a key that does not exist

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default

When

- SSHKeyAdapter.get: user-1 reads their default SSH key by its id

Then

- the call is rejected
  - rejected: GenericBadRequest

### scoped_search

<a id="searching-a-user-granted-read-finds-their-default-key"></a>

#### [a-user-granted-read-finds-their-default-key](/tests/scenario/bai_scenario/manager/ssh_key/test_searching.py): pass

when a user granted READ on their own user searches their SSH keys for the default one, only their default key comes back and no other user's key

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, another user holding a default SSH key, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - regular user user-2: holds one default SSH key
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.scoped_search: user-1 searches up to 10 of their SSH keys for the default one

Then

- a page holding only their default SSH key comes back, without the other user's key or the key that is not the default
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as their seeded default SSH key
  - items[0].field_id: same as their seeded default SSH key
  - items[0].user_id: same as the calling user
  - items[0].public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv'
  - items[0].is_default = True

<a id="searching-a-user-without-read-may-not-search-their-keys"></a>

#### [a-user-without-read-may-not-search-their-keys](/tests/scenario/bai_scenario/manager/ssh_key/test_searching.py): pass

when a user granted no permission on their own user tries to search their SSH keys, it is rejected for lack of permission

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default

When

- SSHKeyAdapter.scoped_search: user-1 searches up to 10 of their SSH keys for the default one

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_upload

<a id="uploading-a-user-granted-update-uploads-their-first-key-as-the-default"></a>

#### [a-user-granted-update-uploads-their-first-key-as-the-default](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

when a user granted UPDATE on their own user and holding no SSH key uploads one, it comes back as the default

Given

- one domain and one user holding no SSH key, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.my_upload: user-1 uploads their own SSH key

Then

- the whole SSH key comes back
  - id: skipped: the database generates it
  - field_id: same as the id in the response
  - user_id: same as the calling user
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv'
  - is_default = True

<a id="uploading-a-user-holding-a-default-uploads-a-key-that-is-not-the-default"></a>

#### [a-user-holding-a-default-uploads-a-key-that-is-not-the-default](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

when a user granted UPDATE on their own user and already holding a default SSH key uploads one, it comes back as not the default

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.my_upload: user-1 uploads their own SSH key

Then

- the whole SSH key comes back
  - id: skipped: the database generates it
  - field_id: same as the id in the response
  - user_id: same as the calling user
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICuqqTj6Ee2CFRyYHeq1INgqKdEoYvyazZPR69RTWOJI'
  - is_default = False

<a id="uploading-a-user-granted-read-may-not-upload-a-key"></a>

#### [a-user-granted-read-may-not-upload-a-key](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

when a user granted only READ on their own user tries to upload an SSH key, it is rejected for lack of permission

Given

- one domain and one user holding no SSH key, and the user holds the READ permission on their own user
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

- SSHKeyAdapter.my_upload: user-1 uploads their own SSH key

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="uploading-a-value-that-is-not-a-public-key-is-rejected"></a>

#### [a-value-that-is-not-a-public-key-is-rejected](/tests/scenario/bai_scenario/manager/ssh_key/test_uploading.py): pass

even a user granted UPDATE on their own user is rejected when the value they upload is not a public key

Given

- one domain and one user holding no SSH key, and the user holds the UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - a role assignment granting the user the UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.my_upload: user-1 uploads a value that is not a public key as their SSH key

Then

- the call is rejected
  - rejected: InvalidSSHPublicKey

### switch_default

<a id="switching_default-a-user-granted-update-switches-their-default-key"></a>

#### [a-user-granted-update-switches-their-default-key](/tests/scenario/bai_scenario/manager/ssh_key/test_switching_default.py): pass

when a user granted READ and UPDATE on their own user sets their SSH key that is not the default as the default, that key comes back as the default

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds the READ, UPDATE permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - a role assignment granting the user the READ, UPDATE permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - Role user-role-1: UPDATE allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.switch_default: user-1 sets their SSH key that is not the default as the default

Then

- the whole SSH key comes back
  - id: same as the seeded SSH key
  - field_id: same as the id in the response
  - user_id: same as the calling user
  - public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFYD/Yrss1np0I+R9f51bEJ0Jjs+d0s4JUussQhs0WBG'
  - is_default = True

<a id="switching_default-a-user-granted-read-may-not-switch-their-default-key"></a>

#### [a-user-granted-read-may-not-switch-their-default-key](/tests/scenario/bai_scenario/manager/ssh_key/test_switching_default.py): pass

when a user granted only READ on their own user tries to set their SSH key as the default, it is rejected for lack of permission

Given

- one domain and one user holding one default SSH key and one SSH key that is not the default, and the user holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: holds one default SSH key
  - regular user user-1: holds one SSH key that is not the default
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- SSHKeyAdapter.switch_default: user-1 sets their SSH key that is not the default as the default

Then

- the call is rejected
  - rejected: NotEnoughPermission

