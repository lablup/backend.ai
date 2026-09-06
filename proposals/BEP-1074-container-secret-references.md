---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-25
Created-Version: 26.8.0
Target-Version:
Implemented-Version:
---

# Container Secret References

## Related Issues

- BA-7480 (secrets on sessions and deployments)
- Depends on BEP-1065 (Encrypted Secret-Key Storage) — provides `SecretColumn` and the key provider pool
- Related BEP-1052 (Scoped App Config Redesign) — precedent for the same scope axis

## 1. Goal

### 1.1 Problem

`environ` is the only way to hand an API key or a token to a container.
`sessions.environ` and `deployment_revisions.environ` are plaintext JSONB, so anyone who
can read a session or a deployment reads the values, and a DB dump carries them verbatim.

The same value also has to be supplied over and over. Sessions are created and discarded
often, and each time the user pastes the key again. Changing a value means finding every
place that holds it, and nothing records where a given value went.

### 1.2 What this BEP defines

Named secrets stored as immutable versions, and a structure in which sessions and
deployment revisions **reference a specific version** to have it injected into their
containers.

### 1.3 Non-goals

| Item | Reason |
|---|---|
| Fixed, named single credentials | Container registry passwords, HuggingFace tokens, object storage access keys, the wsproxy token. This structure can be reused for them and that is the better answer — see 1.5 |
| The SMTP password inside `notification_channels.config` | A pydantic spec with fixed field names, not a key/value bag. Same follow-up as above |
| Dotfiles | A filename-to-content map held as a msgpack blob, not environment variable pairs |
| Plaintext inside the container | Unavoidable while the value is delivered as an environment variable. See 3.6 |
| Revision presets and resource group defaults | The same shape opens to them, but merge rules have to be defined first. Follow-up |
| Applying a value to a running container | Container environment variables are fixed at creation |

### 1.4 Hard requirement

**A revision must stay immutable.** Replicas started from one revision must hold the same
values whenever they started. This requirement decides most of the design below.

### 1.5 Extending to fixed, named credentials

Registry tokens and storage access keys can reference `secrets` and `secret_versions` too,
and that beats putting a `SecretColumn` on each of their columns — the ciphertext lives in
one table, so what a re-encryption pass covers stays independent of how many domains hold
credentials; rotation happens in one place; and no domain has to separately honor the rule
that a value never leaves through a read.

The meaning of the reference differs, though.

| Target | Reference | Reason |
|---|---|---|
| Container injection | A pinned version | 1.4. Replicas of one revision must not diverge |
| Outbound-call credentials | The latest version | Each call needs what is valid now. No snapshot is wanted |

The wiring differs as well. A fixed, named value has no counterpart to `env_key`, so the
reference sits in a foreign key column on that row rather than in the binding table of 3.1.

**This BEP defines container injection only.** The pinned-version rule below holds within
that scope. The global scope and the latest-version reference that the extension needs are
left open.

## 2. Current State & Scope, by Area

### 2.1 Storage

| | Item |
|---|---|
| ✅ | `SecretColumn` — self-describing storage where plaintext and ciphertext coexist in one column (`models/base.py`) |
| ✅ | `KeyProviderPool` — encryption, decryption, and provider selection. Already injected into every repository through `RepositoryArgs` |
| ✅ | `sessions.environ`, `kernels.environ`, `deployment_revisions.environ` — all plaintext |
| ➕ | `secrets` — a shell holding a name and an owning scope |
| ➕ | `secret_versions` — where the value lives. Immutable |
| ➕ | `secret_bindings` — which version a session or revision receives under which environment variable name |

### 2.2 Scope and permission

| | Item |
|---|---|
| ✅ | The RBAC virtual scope graph. Every entity doubles as a scope |
| ✅ | The `(scope_type, scope_id)` axis and CHECK constraint of `app_config_fragments` — precedent for the same shape |
| ✅ | `models/mixins/timestamp.py` — `CreatedAtMixin` and `UpdatedAtMixin` are separate, so a table adopts only what it needs |
| ✅ | `domains` keys on `name` but carries a separate `DomainID` GUID column |
| ➕ | `SecretScopeType` — user, project, domain |
| ➕ | The rule that creating takes write permission on the scope and referencing takes read permission |

### 2.3 Revision lifecycle

| | Item |
|---|---|
| ✅ | A revision is immutable. It has no update spec, and changing `environ` creates a new revision |
| ✅ | Activating a revision recreates every replica. A route is bound to a revision |
| ✅ | Activating an older revision is what rollback is. There is no dedicated API |
| ✅ | `revision_history_limit` defaults to 10, and revisions past it are hard-deleted |
| ➕ | A path that creates secret bindings alongside a revision |

### 2.4 Delivery to the agent

| | Item |
|---|---|
| ✅ | `KernelCreationConfig["environ"]` reaches the agent as Callosum msgpack |
| ✅ | The agent writes `environ.txt` and sets the Docker `Env` array |
| ✅ | With `debug.log-kernel-config` on, the whole config is dumped to the log. The only log leak |
| ✅ | Events and audit logs carry no environment variables |
| ➕ | Sending secrets in a field separate from `environ` in the RPC payload, and masking them in the log dump |

## 3. Implementation Design

### 3.1 Three tables

**`secrets`** — an entity. Holds no value.

| Column | Content |
|---|---|
| `id` | |
| `scope_type` | user, project, domain |
| `scope_id` | The owning entity's id. All three are GUIDs, so one column serves them |
| `name` | |

`UNIQUE(scope_type, scope_id, name)`. Declared as an `EntityCreator` whose `member_of` is
the owning scope entity. It provisions its own virtual scope node, so sharing and grants
are possible.

**`secret_versions`** — a field of `secrets`. The only place a value lives.

| Column | Content |
|---|---|
| `id` | |
| `secret_id` | |
| `version` | Increases from 1 within a secret |
| `value` | `SecretColumn` |

`UNIQUE(secret_id, version)`. **No update spec is declared.** Changing a value adds a
version.

`version` is computed inside the INSERT rather than read first — a scalar subquery adding
one to that secret's highest number. No read precedes the INSERT, so the `secrets` row
needs no lock. Two concurrent inserts can pick the same number; the unique constraint
rejects the loser and the caller retries. `deployment_revisions.revision_number` works the
same way.

Locking the row is worse. A lock on the `secrets` row makes adding a version contend with
renaming that secret.

**`secret_bindings`** — a field of sessions and revisions.

| Column | Content |
|---|---|
| `id` | |
| `owner_type` | session, deployment revision |
| `owner_id` | |
| `env_key` | The environment variable name this value takes in the container |
| `version_id` | Foreign key to `secret_versions.id`, `ON DELETE RESTRICT` |

`UNIQUE(owner_type, owner_id, env_key)`, `INDEX(owner_type, owner_id)`,
`INDEX(version_id)`.

**Only the side that needs referential integrity is a foreign key.** `version_id` is a real
foreign key, so deleting a referenced version is refused by the database.
`INDEX(version_id)` serves the reverse lookup — finding the sessions and revisions that use
a version is how a leaked value is answered. The owner side spans two types, so it is an
enumerated column, and 3.9 covers its cleanup.

`env_key` living on the binding means **one secret can be handed over under several
names**. A secret's name and its name inside the container are separate things.

### 3.2 A reference pins a version

A binding points at `secret_versions`, not at `secrets`. This is what satisfies 1.4.

| | Result |
|---|---|
| Rotating a value | A new version appears. Existing bindings keep pointing at the old one |
| Replicas of one revision | The same version and the same value, whenever they started |
| Applying a new value | A new revision points at the new version. An explicit rollout |
| Rollback | An older revision points at an older version, so it returns to the value of that time |

**Container injection allows no "latest" reference.** With one, only replicas recreated
after a value changed would receive the new value, and values would diverge within a single
revision. That is the destruction of a revision being the unit of deployment. Outbound-call
credentials carry the opposite requirement, which 1.5 covers.

A create request may name a secret, and the service pins **the latest version at that
moment** into the binding. Naming a version directly is accepted too — reproducible
deployments need it.

### 3.3 A read never answers with a value

| Subject | Response |
|---|---|
| A secret | Name, scope, the version list (number and creation time), and each version's reference count |
| A session or revision | The environment variable names, and which secret and version number each came from |

The value leaves through no path. Neither does a masked value — producing one needs
decryption, which would put decryption on the read path for nothing.

Answering with the origin is safe and necessary. The UI has to fill in the "add revision"
form, and since it cannot read the values, the origin name takes their place.

### 3.4 Written at creation, never modified after

Bindings on a session or a revision are created only by the create request.

A session enters scheduling as soon as it is created, and container environment variables
are fixed at creation. An update API would make a modification that never takes effect look
like it succeeded. A revision is immutable to begin with.

Creating bindings shares one transaction with creating the owner. `FieldCreator` is the
spec that builds a row from a settled owner id, and `atomic_create_fields` executes it.
Encrypting a value calls the key provider, so it happens before the transaction opens.

### 3.5 What happens when a secret value changes

**Sessions and revisions that already exist are unaffected**, because their bindings pin a
version. Restarting a kernel reads the same version, so it gets the same value.

Using a new value means creating a new session, or — for a deployment — creating and
activating a new revision that points at the new version. The latter is the rollout, and it
is the only way a changed value reaches a container.

### 3.6 The boundary is the container surface

Decryption happens once, when a session starts. From there the value follows the path
`environ` follows today.

**Inside the container a secret is plaintext, and that cannot be prevented.** Environment
variables are readable through `/proc/<pid>/environ` and are inherited by child processes.
Storing and delivering them differently changes nothing — injecting a Kubernetes Secret as
an environment variable, or exporting a value fetched from an external store, lands in the
same place. The only way to prevent it is for the application to read a file or an API
directly, which removes the requirement of handing the value over as an environment
variable.

So what this BEP closes is **outside the container surface**, which is the range that was
raised as the problem in the first place.

| Point | Result |
|---|---|
| DB | Secrets are not written to `sessions.environ` or `kernels.environ`. Ciphertext lives only in `secret_versions` |
| Read responses | 3.3 |
| Agent log | The config dump under `debug.log-kernel-config` keeps only the key names of secrets |
| Events and audit log | They never carried environment variables |
| Inside the container (environment variables, `environ.txt`, the pickled restart config) | Plaintext. Inside the boundary, for the reason above |
| `docker inspect`, the host scratch directory | Plaintext. Closable, but outside this BEP's scope (open question) |

No secret ends up in `sessions.environ` not because something blocks it, but **because
secrets never travel that path**. The session draft carries bindings separately from
`environ`, and the specs that build the session and kernel rows are left untouched.

**Separating secrets from `environ` in the RPC payload exists for log masking alone.** The
values are merged into `environ` at the agent anyway, so the manager merging them
beforehand would produce the same result — but then the agent's config dump could not tell
which entries are secrets. What makes the separation work is that the dump happens before
the merge, so that ordering has to be pinned in the code.

After merging, the secret field is removed from the config. The whole config is serialized
for restarts immediately afterward and stored in a directory the container reads, so
leaving it in would store the same values twice.

### 3.7 Name collisions

A secret carries an environment variable name. Two cases are refused at creation.

| | |
|---|---|
| A name already present in `environ` | Defining a merge precedence would silently overwrite. Refusing is better |
| A name starting with `BACKENDAI_` | It would overwrite a variable the system injects |

Both a session and a revision create `environ` and their bindings in one request, so the
check happens there.

### 3.8 Timestamps

| Table | Carries | Reason |
|---|---|---|
| `secrets` | created, updated | The name can change |
| `secret_versions` | created | No operation modifies the value |
| `secret_bindings` | created | 3.4 |

An updated-at column on an immutable row is one that never updates.
`deployment_revisions` carries only a creation time for the same reason.

### 3.9 Deletion and cleanup

| Subject | Rule |
|---|---|
| A version | Deletable only with no binding referencing it. The foreign key enforces that |
| A secret | Deletable only once no version remains |
| Deleting a session or revision | Deletes its bindings with it |

Versions accumulate one per rotation, but they are not created in bulk the way sessions
are, so size is not the concern. A value sitting in the DB while a reference remains is
correct — it means a session or revision using it is alive.

**No automatic cleanup is provided.** Nothing guarantees that the moment a reference count
reaches zero is a moment it is safe to delete. The count covers only the references this
system knows about, and says nothing about whether the value is still valid externally.
Trimming by count is wrong here too — a revision is a derivative that can be rebuilt, while
a secret value is the original, and deleting it leaves reissuing it externally as the only
recovery. The user deletes.

There are two session deletion paths. The v2 delete goes through `_teardown_entity`, so the
binding delete is added there. The retention policy's bulk delete does not, so it takes a
cleanup entry of its own. `entity_labels` already has this same gap.

Versions are not a retention policy subject. That framework deletes rows that reached a
terminal state some time ago, and a version has no terminal state and does not age. Session
retention does act on them indirectly, though: when a session is deleted its bindings go
with it, which is what makes a version deletable. Nothing has to be wired for that.

## 4. Migration and Compatibility

Three new tables, no existing column changed. `environ` stays as it is.

Secrets already sitting in `environ` as plaintext are not converted automatically — the
system has no way to tell which entries are secrets. Users register their secrets and
switch to references from the next session or revision.

`secret_versions.value` is added to the re-encryption catalog of BA-7044 as one entry.

## 5. Implementation Plan

| Phase | Content |
|---|---|
| 1 | `secrets`, `secret_versions` — the entity, versions, the three scopes, the v2 standard operations, API/CLI/SDK |
| 2 | `secret_bindings` and session injection — the delivery path, the RPC split, log masking |
| 3 | Deployment revision bindings |

2 and 3 depend on 1. 2 and 3 are independent of each other.

## Decision Summary

| Decision | Content |
|---|---|
| Storage unit | Named secrets with immutable versions. The value lives only in `secret_versions` |
| Reference form | Container injection pins a version. No "latest" reference within this scope |
| Deployment unit | The revision. A deployment holds values that take effect immediately, and a secret requires recreating the container |
| Scope | User, project, domain. No global scope within this BEP |
| Fixed, named credentials | The same structure is reused by reference. Outside this BEP |
| Read response | Key names and origins. Neither values nor masked values |
| Modification | At creation only. A session's or revision's bindings never change afterward |
| Effect of a value change | Existing sessions and revisions are unaffected. New sessions or new revisions carry it |
| Version numbering | A subquery inside the INSERT plus the unique constraint. No row lock |
| Version cleanup | The user deletes when nothing references it. No automatic cleanup, not a retention subject |
| Exposure boundary | The container surface. Outside is closed; inside is plaintext by the nature of environment variable delivery |
| The RPC split | Exists for log masking alone. Removed from the config after the merge |
| Name collisions | A name colliding with `environ` and the `BACKENDAI_` prefix are refused at creation |

## Open Questions

| Item | Content |
|---|---|
| Creating project and domain secrets | Whether a project secret takes a project admin or any member |
| Auditing | Whether referencing a secret is recorded in the audit log, and on which operations |
| Global scope | The extension in 1.5 needs it. Whether creation there is restricted to super-admins |
| `docker inspect` exposure | Closed by handing secrets over as a file instead of the container `Env` array. Confirming that every container goes through the runner that reads that file has to come first |
| Plaintext on the host disk | Whether the directory holding secrets is made RAM-backed on its own. The current RAM-backed scratch mode covers the whole scratch and requires Linux and root |

## References

- BEP-1065 Encrypted Secret-Key Storage — `SecretColumn` and the key providers
- BEP-1052 Scoped App Config Redesign — precedent for the `(scope_type, scope_id)` axis
- BEP-1062 Virtual Scope RBAC Ownership Model
- Prior art: GCP Secret Manager's secrets and immutable versions, AWS Secrets Manager's
  versions and staging labels, HashiCorp Vault KV v2's version retention, and Kubernetes'
  immutable Secrets with the idiom of renaming an object to trigger a rollout
