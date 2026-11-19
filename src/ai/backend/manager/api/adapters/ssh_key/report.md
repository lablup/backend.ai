## ssh_key

[adapter](/src/ai/backend/manager/api/adapters/ssh_key/adapter.py)

Scenario: complete

- direct implementation (2)
  - my_upload: success present 2 · rejection present 2 (single_entity)
  - switch_default: success present 1 · rejection present 1 (single_field)

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

