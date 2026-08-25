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
| ✅ | The pydantic section pattern of `ManagerUnifiedConfig` (`AuthConfig` and friends), with the password hash algorithm settings as precedent |
| ✅ | Unified config is loaded at component startup and reached at runtime through `ManagerConfigProvider` |
| ✅ | A `ManagerConfigProvider` assembly path for one-shot CLI commands - the CLI reads the full unified config too, so no separate key-injection path is needed (3.5) |
| ➕ | New section `secret-encryption`: **which provider type writes**, plus an optional subsection per provider type |

- **There is no separate on/off switch.** Naming the provider type that writes is what turns encryption on, and naming `plain` again is what turns it off. The default is `plain`, so it is opt-in.
- **Reads are decided by the stored value.** A value names the provider type that reads it, so returning writes to plaintext leaves already-encrypted rows readable.
- A provider subsection that is absent leaves that provider unregistered. A subsection that is present must name its active key and carry the key list.

```toml
[secret-encryption]
write-provider-type = "config"        # defaults to "plain"

[secret-encryption.config-provider]
active-key-id = "v2"

[secret-encryption.config-provider.keys]
v1 = "Zn1QcOyzGX9OfSV9/XThDEPGTVFH2n0+PgZ7sDd1lDM="
v2 = "hK8vN2pQrL4xW9cE1mYbT7uZ0aJ6dF3sG5nR8iO2kP4="
```

A key is 32 random bytes in base64, produced by `openssl rand -base64 32`. Both the standard and url-safe alphabets are accepted. The unified config loader chain holds TOML and etcd only, so **a key cannot be supplied through an environment variable.**

### 2.2 DB (stored schema)

| | Item |
|---|---|
| ✅ | `keypairs.secret_key` = plaintext `String(40)`, nullable. `secrets.token_urlsafe(30)` fills exactly 40 characters |
| ✅ | **No SQL query compares, filters, or sorts on `secret_key`** - every comparison happens in Python after fetching. The precondition for non-deterministic encryption is already satisfied |
| ✅ | `keypairs.ssh_private_key` in the same table is already `Text` |
| ➕ | Change `secret_key` to `Text`. **No length limit** |
| ➕ | **No extra metadata column.** One stored value carries everything needed to read it (3.1) |

> The limit is left off because it cannot be known. The size of a stored value follows two values a key provider decides: the key id it names (a GCP CryptoKey name alone runs 70-80 characters) and the size of a wrapped data encryption key. A limit on the column would turn changing providers into a migration. In PostgreSQL `varchar(n)` and `text` are stored the same way and perform the same, so a limit is pure cost. Measured against the config provider, a stored value is about 190 characters.

> The existing column holds plaintext strings, so it becomes `text`.

### 2.3 Encryption layer

| | Item |
|---|---|
| ✅ | The TypeDecorator convention in `models/base.py`, and the **`PasswordColumn` precedent** - it refuses raw string binding and demands a value object |
| ✅ | Dependencies are already available (`cryptography`) |
| ❌ | **There is no precedent for reversible at-rest encryption.** |
| ➕ | `SecretColumn` - converts between the stored string and its parsed form, and performs no cryptography (3.3) |
| ➕ | Value types expressing the stored form (3.1) |
| ➕ | `KeyProvider` - encrypts and decrypts one value (3.2) |
| ➕ | `KeyProviderPool` - sends a read to the provider its value names, and a write to the provider designated for writes |
| ➕ | A branch for the new column type in `populate_fixture` (fixtures carry plaintext, so they need no key) |

### 2.4 Creation and read paths

| | Item |
|---|---|
| ✅ | Creation: `generate_keypair()` from user creation, `issue_my_keypair`, admin creation, signup, the OpenID plugin, and the legacy GQL mutation |
| ✅ | Read (hot path): the REST auth middleware core-selects the keypair row by access key, then recomputes the HMAC signature and validates JWTs |
| ✅ | Read (rest): the keypair plugin's `/login` plaintext `compare_digest`, the plugin hook's token signing, legacy GQL `KeyPair.secret_key`, and the `/auth/authorize` and `/auth/signup` responses |
| ➕ | Write paths encrypt through a provider and bind the result. **Encryption is asynchronous, so it finishes before binding** |
| ➕ | Read paths get a parsed value instead of `str`, and every place that needs plaintext decrypts explicitly through the pool |
| ➕ | Batch re-encryption exposed on **all three surfaces: REST API, GQL, and the admin CLI** (3.4) |

> **Every read path has to be touched.** In exchange, the column's static type is no longer `str`, so any place left unfixed fails type checking. Making it structurally impossible for a ciphertext string to flow downstream disguised as plaintext is the central benefit of this approach.

### 2.5 Migration and operations

| | Item |
|---|---|
| ✅ | The alembic conventions, including the idempotency requirement for backports |
| ✅ | A plaintext fixture (`example-keypairs.json`) and keypair generation inside alembic migrations |
| ➕ | One column type migration. **No data conversion** (existing rows carry no marker and are therefore read as plaintext) |
| ➕ | Rollout and rollback procedure, with a warning (3.6) |
| ➕ | A way to count rows remaining per key id |

## 3. Implementation Design

**Core flow:** on write, draw a fresh data encryption key per value, encrypt the value with it, wrap that key under the provider's active key, and store a self-describing string. On read the column **parses only**, and the value is decrypted through the provider it names. Rotating a key is followed by a batch pass that encrypts the stored values again, drawing a fresh data encryption key per row.

### 3.1 Stored format (self-describing)

```
bai-enc:1:<provider type>:<key id>:<wrapped data key>:<nonce>:<ciphertext>
```

| Field | Meaning |
|---|---|
| `bai-enc` | Marker. Without it, the value is legacy plaintext |
| `1` | Format version |
| provider type | The provider that reads this value. `plain` cannot appear, since plaintext is stored without the marker |
| key id | Which key within that provider. **The provider defines it** |
| wrapped data key | This value's own data encryption key, wrapped under the provider's key |
| nonce | Freshly drawn per encryption |
| ciphertext | Ciphertext plus authentication tag |

- **Legacy detection**: an existing secret key is `token_urlsafe` output and cannot contain `:`, so it never collides with the marker.
- **AAD**: the column's name is the associated data, which blocks transplanting a value from another column.
- **Integrity**: no separate plaintext hash. The AEAD authentication tag detects both a wrong key and tampering.
- **No algorithm field.** The format version implies the algorithm; changing the algorithm bumps that version.
- **No length prefixes.** The three trailing fields are base64url and carry no delimiter, so splitting them off from the right is unambiguous. That is what lets a provider-defined key id contain delimiters.
- **A data encryption key belongs to one row.** Two users' values are never encrypted under the same key.
- The format version is a branch on read. A new version **adds** a branch rather than replacing one, so values written by older builds keep parsing.

### 3.2 Key providers and the pool

A `KeyProvider` works **on one value**. Which key id it writes under and how it wraps a data encryption key are its own business; a stored value names only which provider to hand it back to.

| Method | Contract |
|---|---|
| `provider_type()` | The type written into stored values |
| `encrypt(plaintext, context)` | Encrypts a new value under this provider's current key |
| `decrypt(value, context)` | Recovers the plaintext of a value this provider wrote |

There is one implementation for now, backed by the config. It draws a data encryption key per value, encrypts the value with it, and wraps that key under the active key. A KMS attaches to the same interface later.

`KeyProviderPool` holds the registered providers and the one designated for writes.

- A read goes to the provider its value names. Without a marker the value is plaintext and is returned as is.
- A write goes to the designated provider. When that is `plain`, the value is stored unencrypted.
- An unknown provider type, or one that is not configured, raises.

**Injection points**: decryption is needed in the auth middleware, the keypair plugin (login comparison and token signing), the auth service, and legacy GQL resolvers. The principle is to **decrypt at the repository boundary and pass data objects upward**; where a core select is used directly, as in the auth middleware, the pool is injected there.

Decryption is pure CPU work against an in-memory key, with no remote I/O, so it is safe on the authentication hot path.

### 3.3 Column type

`SecretColumn` converts between the stored string and its parsed form and **performs no cryptography**. Encrypting needs a key provider and is asynchronous, which SQLAlchemy's synchronous bind hook cannot do, so a value is already encrypted when it reaches the column.

| Direction | Input/output | What the column does |
|---|---|---|
| Write | Bind a parsed value | Serializes it to the stored string. **Refuses anything but a parsed value** |
| Read | Return a parsed value | Parses the stored string, marking a value without the marker as plaintext |

- Refusing a raw `str` is what keeps a plaintext string from being stored by accident.
- The column's `context` argument is its own name, and is what callers pass the provider as associated data. **It must be a plain attribute rather than a private one** - SQLAlchemy builds a type's statement cache key from the `__init__` arguments it finds as plain attributes, so hiding it would let two columns share a cache key and a compiled statement bind a value under another column's associated data.
- Plaintext rows and encrypted rows are **expressed by a single type**, so consumers do not branch.
- The value types are frozen dataclasses, and neither plaintext nor key material appears in `repr`.

### 3.4 Key rotation and re-encryption

Rotating a key is **adding a new key to the config and changing the active key id**. The old key stays for decryption only.

**Definition of re-encryption**: decrypt the value, then encrypt it again through the write provider. A fresh data encryption key is drawn per row, so the wrapped key, the nonce, and the ciphertext all change.

**No row is treated differently.** There is no path that skips a value already on the active key, and none that rewraps its data encryption key alone. Whatever key a value sat on, it gets the same work.

An old key left in the config keeps its values readable. Convergence is needed when that key is to be dropped, and a batch pass is what does it.

The batch takes no direction flag.

| Write target | What the batch does |
|---|---|
| A provider | Encrypts every value again under that provider's active key |
| `plain` | Returns every value to plaintext |

Turning ciphertext back into plaintext is not a separate feature but a consequence of the setting.

Re-encryption has one constraint to honor.

| Constraint | Reason |
|---|---|
| **Conditional UPDATE** - overwrite only if the stored value is still the exact string just read | If **the keypair is reissued between the read and the write, a stale value would overwrite the new one.** The condition prevents that. When several managers race on one row, one succeeds and the rest are harmless no-ops |

- Total write volume is **one write per row**, a one-off load proportional to the number of keypairs.
- The pass decrypts the values, so it **needs permission to handle plaintext**.
- A failure leaves the stored value valid as it stands, and the next run handles it again.

**The batch is provided on all three surfaces.**

| Surface | Use |
|---|---|
| REST API (admin) | Called from automation and ops tooling |
| GQL mutation (admin) | Management console integration |
| `mgr` admin CLI | Run directly outside the server, for migration work |

Common requirements: sweep the target column **in chunks**, report the count per key id, and allow the stored state to be queried. The chunk size is the implementation's to decide and is not passed by the caller. An interrupted pass is continued by running it again.

### 3.5 Where the key material lives

**A new section in the unified config is sufficient.** No separate path is needed.

| Process | Needs the key | Basis |
|---|---|---|
| Manager server | Yes | Reaches unified config through `ManagerConfigProvider` |
| `mgr` CLI (batch re-encryption) | Yes | A `ManagerConfigProvider` assembly path for one-shot CLI commands already exists |
| alembic | **No** | Column type change only, no data conversion |
| Fixture population | **No** | Written as plaintext and moved later by a batch pass |

Because reads only parse, the bootstrap stages (alembic, fixtures) depend on the key not at all.

Holding the keys in etcd instead of the file takes no code change. etcd is already in the unified config loader chain, and a watcher that revalidates the whole unified config on change already runs. etcd is a separate store from PostgreSQL, so the threat model of "the DB leaking on its own" still holds.

### 3.6 Migration and rollout

The migration is **one column type change** with no data conversion, written idempotently for backports. `varchar(40)` to `text` is binary coercible, so no table rewrite happens, and this column carries no index.

Rollout order:

1. Deploy the code (column type applied, writes still `plain`). Storage behavior does not change.
2. Configure keys, then name the write provider type. New keypairs are stored encrypted.
3. Move existing rows with a batch pass if needed.

**Rollback warning**: rolling back to step 1 is safe (all rows are plaintext). But **rolling back to an older build after step 2 breaks authentication, because ciphertext is mistaken for plaintext.** Reverting requires setting the write target back to `plain` and completing a batch conversion first. State this in the release notes.

**Performance**: decryption is microseconds against an in-memory key, so it has no meaningful effect on the authentication hot path. Reading one value performs two AES operations - unwrapping the data encryption key and decrypting the value.

## Decision Summary

| Decision | Content |
|---|---|
| Turning it on and off | No separate switch. **Naming the write provider type** turns it on, and naming `plain` turns it off. The default is `plain` |
| Reads | **Decided by the stored value.** A value names the provider that reads it, so reads are independent of the write setting |
| Stored format | Single-column self-describing `bai-enc:<format version>:<provider type>:<key id>:<wrapped data key>:<nonce>:<ciphertext>`. No marker means legacy plaintext |
| Algorithm field | None. The format version implies it |
| Length prefixes | None. The three trailing fields are base64url, so splitting from the right is unambiguous |
| Extra metadata column | None |
| Scope of a data encryption key | **One row.** Two users' values are never encrypted under the same key |
| Column type | Converts between the stored string and its parsed form only. **It performs no cryptography** - encryption is asynchronous and finishes before binding. A raw string is refused |
| Decryption site | Explicit calls through the pool where plaintext is needed. Every read path is modified, and anything missed fails type checking |
| Algorithm | AEAD (AES-256-GCM). No separate plaintext hash. The column's name is bound as associated data |
| Key management | Each provider holds keys by id and names an active id. Decrypt with the id the value names, wrap new values under the active one |
| Key provider abstraction | `KeyProvider` encrypts and decrypts one value. There is one config-backed implementation, and a KMS attaches to the same interface later |
| Key rotation | Adding a key to the config and changing the active id is the whole procedure. **A batch pass encrypts every value again under a fresh data encryption key** |
| Immediate convergence | Not performed. An old key left in the config keeps its values readable, and convergence happens in a batch when that key is dropped |
| Re-encryption constraint | **Conditional UPDATE** (guards against a reissue race) |
| Batch surfaces | **REST admin API, GQL mutation, and the `mgr` admin CLI - all three.** Chunked, reporting the count per key id |
| Batch direction | No direction flag. It **normalizes to whatever the current write target specifies**, so `plain` yields conversion to plaintext |
| Column type change | `String(40)` to `Text`, **with no length limit** - the stored size follows the provider implementation, so no limit can be known. `varchar` to `text` needs no table rewrite |
| Backward compatibility | Plaintext and encrypted rows coexist indefinitely. No bulk conversion, forced re-login, or key reissue |
| Key material location | **The new unified-config section alone is enough.** The CLI reads it through the same assembly path, alembic and fixtures need no key, and etcd works without code changes |
| First target | The single column `keypairs.secret_key` |
| Out of scope | KMS, `ssh_private_key`, exposure-path reduction (BEP-1068), the Valkey and webserver copies, secret columns in other tables and components |

## Open Questions

- **How automated old-key retirement should be** - whether an operator judges that the remaining count is zero, or the batch emits a "safe to retire" signal.
- **When to extend to other secret columns** - whether object storage, reservoir registry, and container registry become follow-up Stories or continue within the same Epic.

## References

- **BEP-1068** Login Session Improvements - complementary; it reduces exposure paths by changing the authentication algorithm
- Precedent: `PasswordColumn` (one-way hash column type) - the structural template for value-object binding and the fixture branch
- Format prior art: key-id based rotation in Google Tink keysets
