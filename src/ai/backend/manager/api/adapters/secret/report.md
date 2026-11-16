## secret

[background](/src/ai/backend/manager/api/adapters/secret/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/secret/adapter.py)

Scenario: complete

- direct implementation (2)
  - admin_reencrypt_secrets: success present 4 · rejection present 2 (global_scope)
  - admin_secret_status: success present 3 · rejection present 1 (global_scope)

**admin_reencrypt_secrets**

| scenario | verdict |
|---|---|
| [when the config key is the write provider and two plaintext secret keys are re-encrypted, the response says both were scanned and rewritten, and the status shows both on that key with no plaintext left](#reencrypting-reencrypting-moves-plaintext-secrets-onto-the-config-key) | answered |
| [when the config key is the write provider and two secret keys are already on that key, re-encrypting scans and rewrites both, and the status still shows the two on that key](#reencrypting-reencrypting-rewrites-secrets-already-on-the-config-key) | answered |
| [when the write provider is plaintext and two plaintext secret keys are re-encrypted, the response says both were scanned and rewritten, and the status still shows two plaintext entries. The rewritten count counts rewritten rows, not changed values](#reencrypting-reencrypting-with-a-plain-writer-rewrites-plaintext-secrets-as-plaintext) | answered |
| [when the write provider is plaintext and the config key provider is read-only, re-encrypting the secret key encrypted with that key scans and rewrites one, and the status holds only plaintext](#reencrypting-reencrypting-with-a-plain-writer-turns-an-encrypted-secret-back-to-plaintext) | answered |
| [when a user who is not the superadmin runs a re-encryption, it is rejected for lack of the role](#reencrypting-a-user-who-is-not-the-superadmin-may-not-reencrypt-secrets) | rejected |
| [when the monitor role runs a re-encryption, it is rejected for lack of the role: it can read the status, but re-encryption is a write and does not pass](#reencrypting-the-monitor-may-not-reencrypt-secrets) | rejected |

**admin_secret_status**

| scenario | verdict |
|---|---|
| [when secrets encrypted with the config key and plaintext secrets are mixed, reading the status returns the encrypted count and the plaintext count as two separate entries](#status-secrets-on-different-keys-are-counted-apart) | answered |
| [when the monitor role reads the status, the same response as the superadmin's comes back, because the superadmin check allows the monitor to read](#status-the-monitor-reads-the-secret-status-like-the-superadmin) | answered |
| [when the write provider is plaintext and the superadmin reads the status, the write provider is plaintext and the count is one entry for the secrets held in plaintext, including the caller's](#status-the-superadmin-reads-a-status-counting-the-plaintext-secrets) | answered |
| [when a user who is not the superadmin reads the status, it is rejected for lack of the role](#status-a-user-who-is-not-the-superadmin-may-not-read-the-secret-status) | rejected |

### admin_reencrypt_secrets

<a id="reencrypting-reencrypting-moves-plaintext-secrets-onto-the-config-key"></a>

#### [reencrypting-moves-plaintext-secrets-onto-the-config-key](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py): pass

when the config key is the write provider and two plaintext secret keys are re-encrypted, the response says both were scanned and rewritten, and the status shows both on that key with no plaintext left

Given

- one superadmin, 1 users holding a plaintext secret key
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- SecretAdapter.admin_reencrypt_secrets: user-1 re-encrypts every secret key

Then

- every secret key is scanned and rewritten, and the status that comes back has all of them moved to the write provider
  - scanned = 2
  - reencrypted = 2
  - status.write_provider_type = 'config'
  - status.counts = [('keypairs.secret_key', 'config', 'k1', 2)]

<a id="reencrypting-reencrypting-rewrites-secrets-already-on-the-config-key"></a>

#### [reencrypting-rewrites-secrets-already-on-the-config-key](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py): pass

when the config key is the write provider and two secret keys are already on that key, re-encrypting scans and rewrites both, and the status still shows the two on that key

Given

- one superadmin, 1 users holding a secret key encrypted with the config key
  - Domain home-1
  - Prepare one user holding an encrypted secret key
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project, and their secret key is encrypted
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project, and their secret key is encrypted

When

- SecretAdapter.admin_reencrypt_secrets: user-1 re-encrypts every secret key

Then

- every secret key is scanned and rewritten, and the status that comes back has all of them moved to the write provider
  - scanned = 2
  - reencrypted = 2
  - status.write_provider_type = 'config'
  - status.counts = [('keypairs.secret_key', 'config', 'k1', 2)]

<a id="reencrypting-reencrypting-with-a-plain-writer-rewrites-plaintext-secrets-as-plaintext"></a>

#### [reencrypting-with-a-plain-writer-rewrites-plaintext-secrets-as-plaintext](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py): pass

when the write provider is plaintext and two plaintext secret keys are re-encrypted, the response says both were scanned and rewritten, and the status still shows two plaintext entries. The rewritten count counts rewritten rows, not changed values

Given

- one superadmin, 1 users holding a plaintext secret key
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- SecretAdapter.admin_reencrypt_secrets: user-1 re-encrypts every secret key

Then

- every secret key is scanned and rewritten, and the status that comes back has all of them moved to the write provider
  - scanned = 2
  - reencrypted = 2
  - status.write_provider_type = 'plain'
  - status.counts = [('keypairs.secret_key', 'plain', None, 2)]

<a id="reencrypting-reencrypting-with-a-plain-writer-turns-an-encrypted-secret-back-to-plaintext"></a>

#### [reencrypting-with-a-plain-writer-turns-an-encrypted-secret-back-to-plaintext](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py): pass

when the write provider is plaintext and the config key provider is read-only, re-encrypting the secret key encrypted with that key scans and rewrites one, and the status holds only plaintext

Given

- one superadmin
  - Domain home-1
  - Prepare one user holding an encrypted secret key
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project, and their secret key is encrypted

When

- SecretAdapter.admin_reencrypt_secrets: user-1 re-encrypts every secret key

Then

- every secret key is scanned and rewritten, and the status that comes back has all of them moved to the write provider
  - scanned = 1
  - reencrypted = 1
  - status.write_provider_type = 'plain'
  - status.counts = [('keypairs.secret_key', 'plain', None, 1)]

<a id="reencrypting-a-user-who-is-not-the-superadmin-may-not-reencrypt-secrets"></a>

#### [a-user-who-is-not-the-superadmin-may-not-reencrypt-secrets](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py): pass

when a user who is not the superadmin runs a re-encryption, it is rejected for lack of the role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SecretAdapter.admin_reencrypt_secrets: user-1 re-encrypts every secret key

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="reencrypting-the-monitor-may-not-reencrypt-secrets"></a>

#### [the-monitor-may-not-reencrypt-secrets](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py): pass

when the monitor role runs a re-encryption, it is rejected for lack of the role: it can read the status, but re-encryption is a write and does not pass

Given

- one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- SecretAdapter.admin_reencrypt_secrets: user-1 re-encrypts every secret key

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_secret_status

<a id="status-secrets-on-different-keys-are-counted-apart"></a>

#### [secrets-on-different-keys-are-counted-apart](/tests/scenario/bai_scenario/manager/secret/test_status.py): pass

when secrets encrypted with the config key and plaintext secrets are mixed, reading the status returns the encrypted count and the plaintext count as two separate entries

Given

- one superadmin, 1 users holding a secret key encrypted with the config key
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Prepare one user holding an encrypted secret key
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project, and their secret key is encrypted

When

- SecretAdapter.admin_secret_status: user-1 reads the secret status

Then

- the secret keys seeded in advance come back counted per encryption key
  - write_provider_type = 'config'
  - counts = [('keypairs.secret_key', 'config', 'k1', 1), ('keypairs.secret_key', 'plain', None, 1)]

<a id="status-the-monitor-reads-the-secret-status-like-the-superadmin"></a>

#### [the-monitor-reads-the-secret-status-like-the-superadmin](/tests/scenario/bai_scenario/manager/secret/test_status.py): pass

when the monitor role reads the status, the same response as the superadmin's comes back, because the superadmin check allows the monitor to read

Given

- one monitor, 1 users holding a plaintext secret key
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- SecretAdapter.admin_secret_status: user-1 reads the secret status

Then

- the secret keys seeded in advance come back counted per encryption key
  - write_provider_type = 'plain'
  - counts = [('keypairs.secret_key', 'plain', None, 2)]

<a id="status-the-superadmin-reads-a-status-counting-the-plaintext-secrets"></a>

#### [the-superadmin-reads-a-status-counting-the-plaintext-secrets](/tests/scenario/bai_scenario/manager/secret/test_status.py): pass

when the write provider is plaintext and the superadmin reads the status, the write provider is plaintext and the count is one entry for the secrets held in plaintext, including the caller's

Given

- one superadmin, 1 users holding a plaintext secret key
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- SecretAdapter.admin_secret_status: user-1 reads the secret status

Then

- the secret keys seeded in advance come back counted per encryption key
  - write_provider_type = 'plain'
  - counts = [('keypairs.secret_key', 'plain', None, 2)]

<a id="status-a-user-who-is-not-the-superadmin-may-not-read-the-secret-status"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-the-secret-status](/tests/scenario/bai_scenario/manager/secret/test_status.py): pass

when a user who is not the superadmin reads the status, it is rejected for lack of the role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SecretAdapter.admin_secret_status: user-1 reads the secret status

Then

- the call is rejected
  - rejected: InsufficientPrivilege

