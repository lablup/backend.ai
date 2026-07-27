---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-28
Created-Version:
Target-Version:
Implemented-Version:
---

# Encrypted Secret-Key Storage

## Related Issues

- Epic **BA-6958**, this BEP **BA-6959**
- Related **BEP-1068** (Login Session Improvements) - same purpose (reduce the risk of stored keys), different method. See 1.2
- Follow-up: after acceptance, decompose into implementation Stories under BA-6958 via `/bep-to-issues`

## 1. Goal

### 1.1 Problem

`keypairs.secret_key` is stored as **plaintext `String(40)`**. It is the HMAC signing key for every API request and the JWT signing key, so a leaked DB dump, backup, or snapshot **hands over every user's credentials verbatim**. Unlike a password, signature verification needs the original value, so hashing is not an option - only **reversible encryption** is.

This BEP defines **at-rest encryption** for it. The threat model is **the DB contents leaking on their own**, and it holds only under the assumption that the DB and the key material are stored separately. A fully compromised manager process is not defended against.

### 1.2 Non-goals

| Item | Reason |
|---|---|
| Reducing the fact that APIs and the CLI return the secret key at all | That is an authentication-algorithm change. **BEP-1068** covers it |
| Plaintext copies left in the Valkey login session and the webserver session store | Same reason - BEP-1068's territory |
| Client-side `~/.config` and the `BACKEND_SECRET_KEY` environment variable | User's machine |
| **KMS integration** | Follow-up. Key lookup is placed behind an interface, but no KMS implementation lands here |
| **`keypairs.ssh_private_key`** | Not this BEP's purpose (protecting API credentials). The same column type can be reused for it later |
| `object_storages.secret_key`, `reservoir_registries.secret_key`, container-registry passwords | **Follow-up work** reusing the same mechanism. This BEP only provides the column type |
| The separate `keypairs` table in the account_manager component | Separate DB and component, follow-up |

**Relation to BEP-1068**: 1068 changes the authentication method so the webserver no longer has to hold or decrypt the secret key (shrinking the exposure paths). This BEP encrypts the stored value itself (shrinking what is stored). The two are **complementary, not mutually exclusive**; once 1068 lands, the "plaintext copies" rows in 1.2 are resolved along with it.

### 1.3 Hard requirement

**Users on existing keys must keep working, unchanged.** No bulk conversion at migration time, no forced re-login, no key reissue. The stored value must therefore be **self-describing per row**, and plaintext rows and ciphertext rows must be able to coexist indefinitely.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 Config

| | Item |
|---|---|
| ✅ | The pydantic section pattern of `ManagerUnifiedConfig` (`AuthConfig` and friends), with the password hash algorithm/rounds settings as precedent |
| ✅ | Unified config is loaded at component startup and reached at runtime through `ManagerConfigProvider` |
| ✅ | A `ManagerConfigProvider` assembly path for one-shot CLI commands - the CLI can read the full unified config too, so no separate key-injection path is needed (3.5) |
| ➕ | New section `secret-encryption`: `mode = plain \| encrypt`, `algorithm`, **`active-key-version`**, and a **per-version key list** |

- `mode` decides **the write policy only**. Reads are always decided by the value itself. The default is `plain` (opt-in).
- **Multiple keys are injected at once, one per version.** Decryption uses the version the value names; new encryption uses `active-key-version` only. That is the whole of key rotation.

```toml
[secret-encryption]
mode = "encrypt"
algorithm = "aes-256-gcm"
active-key-version = "v2"

[secret-encryption.keys]
v1 = "<base64 32B>"   # kept for decryption only
v2 = "<base64 32B>"   # used for new encryption
```

### 2.2 DB (stored schema)

| | Item |
|---|---|
| ✅ | `keypairs.secret_key` = plaintext `String(40)`, nullable. `secrets.token_urlsafe(30)` fills exactly 40 characters |
| ✅ | **No SQL query compares, filters, or sorts on `secret_key`** - every comparison happens in Python after fetching. The precondition for non-deterministic encryption is already satisfied |
| ➕ | Widen the `secret_key` column - ciphertext necessarily exceeds 40 characters (about 120 expected; `String(255)` proposed) |
| ➕ | **No extra metadata column.** The algorithm and key version live in the stored value's prefix (3.1) |

> A separate `secret_key_version` column was considered. It would let rotation progress be queried through an index, but it breaks the structure where one column type handles one value self-containedly (a type cannot see other columns). Progress queries are served well enough by a prefix `LIKE`, so the **single-column self-describing value** wins.

### 2.3 Encryption layer

| | Item |
|---|---|
| ✅ | The TypeDecorator convention in `models/base.py`, and the **`PasswordColumn` precedent** - it refuses raw string binding, demands a `PasswordInfo` value object, and performs the transformation at write time |
| ✅ | Dependencies are already available (`cryptography` and `pycryptodome` are both in the lock file) |
| ❌ | **There is no precedent for reversible at-rest encryption.** Zero uses of Fernet or an encrypted-string type |
| ➕ | An `EncryptedSecretColumn` TypeDecorator - **encrypts on write, parses only on read** (3.3) |
| ➕ | Two value objects - an encryption-request object and a stored-state object (3.3) |
| ➕ | `SecretKeyCipher` - an injectable component that holds the per-version keys and performs decryption (3.2) |
| ➕ | A branch for the new column type in `populate_fixture` (isomorphic to the `PasswordColumn` branch) |

### 2.4 Creation and read paths

| | Item |
|---|---|
| ✅ | Creation: `generate_keypair()` from user creation, `issue_my_keypair`, admin creation, signup, the OpenID plugin, and the legacy GQL mutation |
| ✅ | Read (hot path): the REST auth middleware core-selects the keypair row by access key, then recomputes the HMAC signature and validates JWTs |
| ✅ | Read (rest): the keypair plugin's `/login` plaintext `compare_digest`, the keypair plugin hook's token signing, legacy GQL `KeyPair.secret_key` (consumed by the admin CLI), and the `/auth/authorize` and `/auth/signup` responses |
| ➕ | Write paths bind an **encryption-request value object** instead of a plaintext string |
| ➕ | Read paths get a **stored-state value object** instead of `str`, so every place that needs plaintext calls **explicit decryption** through `SecretKeyCipher` |
| ➕ | A lazy re-encryption hook - at the decryption point, re-store in the background if the key version is not the active one (3.4) |
| ➕ | Batch re-encryption exposed on **all three surfaces: REST API, GQL, and the admin CLI** (3.4) |

> **Every read path has to be touched.** In exchange, the column's static type is no longer `str`, so any place left unfixed fails type checking. Making it structurally impossible for a ciphertext string to flow downstream disguised as plaintext is the central benefit of this approach.

### 2.5 Migration and operations

| | Item |
|---|---|
| ✅ | The alembic conventions, including the idempotency requirement for backports |
| ✅ | A plaintext fixture (`example-keypairs.json`) and keypair generation inside alembic migrations |
| ➕ | One column-widening migration. **No data conversion** (existing rows carry no prefix and are therefore read as plaintext) |
| ➕ | Rollout and rollback procedure, with a warning (3.6) |
| ➕ | A way to count rows per key version (rotation progress) |

## 3. Implementation Design

**Core flow:** on write, encrypt with the active key version and store a self-describing string. On read, the column type **parses only** and returns a value object. Where plaintext is needed, decrypt through `SecretKeyCipher`. If the key version is not the active one, lazy re-encryption converges it; batch re-encryption forces convergence.

### 3.1 Stored format (self-describing)

```
bai:enc:1:<algo>:<key_version>:<nonce_b64u>:<ciphertext_b64u>
```

| Field | Meaning |
|---|---|
| `bai:enc:1` | Magic plus **format version**. Without this prefix, the value is legacy plaintext |
| `algo` | AEAD algorithm identifier (v1: `a256gcm`) |
| `key_version` | Key of the configured key list (e.g. `v1`, `v2`) |
| `nonce` | Freshly drawn per encryption |
| `ciphertext` | Ciphertext plus authentication tag |

- **Legacy detection**: an existing secret key is `token_urlsafe` output and cannot contain `:`, so it never collides with the prefix.
- **AAD**: the column type instance uses its own context string (e.g. `keypairs.secret_key`) as AAD, which blocks transplanting a ciphertext from another column or table.
- **Integrity**: no separate plaintext hash. **The AEAD authentication tag detects both a wrong key and tampering.**
- **Rotation progress**: `WHERE secret_key LIKE 'bai:enc:1:a256gcm:v1:%'` counts the rows per key version. When it reaches zero, that key can be dropped from the config.
- The format-version field means that if a KMS later requires a different structure, a v2 format can be added and coexist.

### 3.2 Key lookup and decryption (`SecretKeyCipher`)

An **injectable component** holding the per-version keys. It depends on no global state.

| Method | Contract |
|---|---|
| `active_version()` | The key version to use for new encryption |
| `encrypt_request(plaintext)` | Builds the **value object to bind** for encryption under the active key (3.3) |
| `decrypt(stored)` | Turns a stored-state object into plaintext. Returns it as-is when the state is plaintext |

- Key lookup sits behind a **`SecretKeyProvider` interface**. There is **exactly one implementation** for now (config); a KMS attaches to the same interface later.
- An unknown key version raises rather than being silently passed through (a `BackendAIError` subclass).
- Decryption is pure CPU work against an in-memory key, with no remote I/O, so it is safe on the authentication hot path.

**Injection points**: decryption is needed in the auth middleware, the keypair plugin (login comparison and token signing), the auth service (login response), and legacy GQL resolvers. The principle is to **decrypt at the repository boundary and pass data objects upward**; where a core select is used directly, as in the auth middleware, the cipher is injected there.

### 3.3 Column type and value objects

The shape mirrors `PasswordColumn`: it **refuses raw `str` binding** and demands a value object.

| Direction | Input/output | What the column does |
|---|---|---|
| Write | Bind an encryption-request object (plaintext + target key version + key material) | **Performs encryption** and serializes to the 3.1 format. Stores plaintext as-is when `mode=plain` |
| Read | Return a stored-state object | **Parses only.** With a prefix, splits into algorithm, key version, nonce, and ciphertext; without one, marks it plaintext |

- **Why reads do not decrypt**: decryption needs a key, and the column type's result-conversion point has no sensible way to receive one (it would require process-global state). Writes, by contrast, **carry the key material in the bound value object, so no global injection is needed.** This asymmetry is the rationale for the design.
- The stored-state object holds the `key_version` (absent when plaintext) and the original string; `SecretKeyCipher` performs the decryption. Plaintext rows and ciphertext rows are **expressed by a single type**, so consumers do not branch.
- The value objects default to frozen dataclasses (there is no serialization requirement). Exact names and fields are the implementer's discretion.
- Both value objects carry a representation that does not expose plaintext, guarding against logging and `repr` accidents.

### 3.4 Key rotation and re-encryption

Rotating a key is **adding a new versioned key to the config and changing `active-key-version`** - nothing more. The old key stays for decryption only.

**Definition of re-encryption**: read the stored value to obtain plaintext (as-is when plaintext, otherwise decrypted with the key version the value names), then encrypt that plaintext again under the **active key version with a freshly drawn nonce** and overwrite. Nonces are never reused - reusing a nonce under the same key destroys confidentiality in GCM, so a fresh nonce is drawn even when re-encrypting the same plaintext.

**The default is lazy re-encryption**, converging gradually by checking the key version at the decryption point.

| Condition | Action |
|---|---|
| Plaintext state, `mode=encrypt` | Encrypt under the active key and re-store |
| `key_version` != active version, `mode=encrypt` | Decrypt, then re-store under the active key |
| `key_version` == active version | Nothing |
| `mode=plain` | No re-store. **No automatic conversion to plaintext either** (ciphertext keeps being decrypted on read) |

Re-encryption has exactly two constraints to honor.

| Constraint | Reason |
|---|---|
| **Conditional UPDATE** - overwrite only if the stored value is still the exact string just read | If **the keypair is reissued between the read and the re-store, stale plaintext would overwrite the new value.** The condition prevents that. When multiple managers race on the same row, one succeeds and the rest are harmless no-ops |
| **Performed outside the reading transaction** | The auth middleware queries the keypair in a read-only transaction and cannot write inside it, so this is split into a background task on a separate session |

- Re-encryption **never blocks the authentication response path.** It is best-effort; failures leave a log and a metric while authentication still succeeds.
- Total write volume is **one write per row**, a one-off load proportional to the number of keypairs. After convergence the condition is false, so no extra writes remain on the hot path.
- Since the update does not change the value, a failure loses no consistency. The next read retries it.

**Batch re-encryption** is the way to force convergence: dropping a key requires zero rows on that version, and lazy convergence leaves rarely used keys behind. **All three surfaces are provided.**

| Surface | Use |
|---|---|
| REST API (admin) | Called from automation and ops tooling |
| GQL mutation (admin) | Management console integration |
| `mgr` admin CLI | Run directly outside the server, for migration work |

Common requirements: sweep the target column **in chunks, resumably**, report remaining counts per key version, and allow the run's status to be queried.

**The batch is a single operation that normalizes storage to whatever the current config specifies.** There is no direction mode or flag.

| `mode` | What the batch does |
|---|---|
| `encrypt` | Encrypts plaintext rows and old-version rows under the active key |
| `plain` | Decrypts ciphertext rows back to plaintext |

Going from ciphertext back to plaintext is not an actual operational requirement but **a generalization that falls out of the config**. No separate feature is built for it, so it costs nothing extra. The automatic path, lazy re-encryption, still does nothing under `mode=plain` - to avoid surprises, **conversion to plaintext happens only through an explicit batch run**.

### 3.5 Where the key material lives

**A new section in the unified config is sufficient.** No separate path is needed.

| Process | Needs the key | Basis |
|---|---|---|
| Manager server | Yes | Reaches unified config through `ManagerConfigProvider` |
| `mgr` CLI (batch re-encryption) | Yes | A `ManagerConfigProvider` assembly path for one-shot CLI commands already exists (TOML plus etcd loader chain); `clear-history` and others use it |
| alembic | **No** | Column widening only, no data conversion |
| Fixture population | **No** | Written as plaintext and left to lazy re-encryption |

Because reads do not decrypt, the bootstrap stages (alembic, fixtures) depend on the key not at all.

### 3.6 Migration and rollout

The migration is **one column widening** with no data conversion. It is written idempotently for backports.

Rollout order:

1. Deploy the code (column type applied, `mode=plain`). Storage behavior does not change.
2. Configure keys, then set `mode=encrypt`. New keypairs are stored encrypted; existing rows converge as they are read.
3. Force convergence with batch re-encryption if needed.

**Rollback warning**: rolling back to step 1 is safe (all rows are plaintext). But **rolling back to an older build after step 2 breaks authentication, because ciphertext is mistaken for plaintext.** Reverting requires completing a batch decryption first. State this in the release notes.

**Performance**: AES-256-GCM decryption is microseconds per request against an in-memory key, so it has no meaningful effect on the authentication hot path.

## Decision Summary

| Decision | Content |
|---|---|
| Mode | Global config `plain \| encrypt`, default `plain` (opt-in). **Decides the write policy only; reads are decided by the value** |
| Stored format | Single-column self-describing `bai:enc:<format version>:<algo>:<key_version>:<nonce>:<ct>`. No prefix means legacy plaintext |
| Extra metadata column | None. Rotation progress is queried with a prefix `LIKE` |
| Column type | Isomorphic to `PasswordColumn`. **Write = take a value object and encrypt; read = parse only, never decrypt** |
| Decryption site | Explicit calls through an injected `SecretKeyCipher` where plaintext is needed. Every read path is modified, and anything missed fails type checking |
| Algorithm | AEAD (AES-256-GCM). No separate plaintext hash; the authentication tag detects a wrong key and tampering. AAD binds the column context |
| Key management | **Inject multiple per-version keys and name an `active-key-version`.** Decrypt with the version the value names, encrypt with the active one |
| Key-lookup abstraction | A `SecretKeyProvider` interface with exactly one implementation (config). **KMS is out of scope here** |
| Key rotation | Adding a new version to the config and changing `active-key-version` is the whole procedure. Re-encryption re-stores the read plaintext under the **active key with a fresh nonce** |
| Re-encryption constraints | **Conditional UPDATE** (guards against a reissue race) plus **a background write outside the reading transaction**. Authentication succeeds even on failure |
| Batch surfaces | **REST admin API, GQL mutation, and the `mgr` admin CLI - all three.** Chunked, resumable, progress-reporting |
| Batch direction | No direction flag. It **normalizes to whatever the current `mode` specifies**, so `plain` yields conversion to plaintext as a consequence. Nothing converts automatically (lazy does nothing under `plain`) |
| Backward compatibility | Plaintext and ciphertext rows coexist indefinitely. No bulk conversion, forced re-login, or key reissue |
| Key material location | **The new unified-config section alone is enough.** The CLI reads it through the same provider assembly path, and alembic and fixtures need no key |
| First target | The single column `keypairs.secret_key` |
| Out of scope | KMS, `ssh_private_key`, exposure-path reduction (BEP-1068), the Valkey and webserver session copies, secret columns in other tables and components |

## Open Questions

- **How automated old-key retirement should be** - whether an operator judges that the remaining count is zero, or the batch emits a "safe to retire" signal.
- **When to extend to other secret columns** - whether object storage, reservoir registry, and container registry become follow-up Stories or continue within the same Epic.

## References

- **BEP-1068** Login Session Improvements - complementary; it reduces exposure paths by changing the authentication algorithm
- Precedent: `PasswordColumn` (one-way hash column type) - the structural template for value-object binding and the fixture branch
- Format prior art: key-id based rotation in Google Tink keysets
