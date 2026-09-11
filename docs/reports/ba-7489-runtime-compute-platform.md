# BA-7489 part 3 — runtime test, Compute & Platform slice

Every wired v2 action in the `resource_group`, `system`, `app_config`, `metric`,
`notification_center`, `visibility` and `label` concerns, driven against the running local
manager and scored against the five questions. Findings only — nothing was fixed.

| | |
|---|---|
| Slice | Compute & Platform (agent C) |
| Actions in scope | 188 |
| Manager | `http://127.0.0.1:8091`, api mode, HMAC keypair auth |
| Principals | superadmin, domain admin, plain user, plain user 2, monitor |
| Base commit | `05e005d18b` |

## Coverage

| outcome | count |
|---|---:|
| exercised against the live manager | 170 |
| unreachable — no client route exists | 8 |
| not exercised — reachable only from an internal caller | 7 |
| not exercised — would destabilise the shared stack | 3 |
| **total** | **188** |

Unreachable (no CLI, no REST, no GraphQL field found): `scoped_search_resource_groups`,
`global_get_wsproxy_version`, `associate_resource_group_with_keypairs`,
`disassociate_resource_group_from_keypairs`, `get_resource_slot_type`,
`lookup_bulk_entity_label_owner`, and the two `bulk_get_app_config_*` loaders whose only GraphQL
`appConfigDefinition` / `appConfigAllowList` fields sit on create payloads that do not go through a
loader.

Reachable only from an internal caller, with no client-facing field:
`global_load_agent_container_counts`, `global_sync_agent_registry`,
`global_resolve_resource_group_ids`, `lookup_kernel_owner`, `process_notification`, and the
`--remove` halves of `disassociate_resource_group_from_domains` /
`disassociate_resource_group_from_projects` (routes exist and were left alone so the `default`
domain and project bindings were not perturbed).

`public_bulk_get_runtime_variants` and `public_bulk_get_prometheus_query_preset_categories` were
initially recorded here; both turned out to be drivable through their GraphQL DataLoader relations
and are now exercised — see F16 and section 3.

**No live compute agent.** `agent`, `proxy-coordinator` and `proxy-worker` were stopped for the
whole run; the `agents` table holds exactly one row, `i-MacBook-Air.local`, status `TERMINATED`,
`schedulable=t`. The 13 `agent` actions are scored against that fact — a read returning an empty or
terminated-only result is correct here, not a defect, and the three watcher lifecycle actions had
nothing live to act on even had they been safe to run. The one agent finding below (F15) is about
how the unavailability is *reported*, not about the unavailability itself.

Skipped to protect the shared stack: `global_start_agent`, `global_stop_agent`,
`global_restart_agent` — the three watcher lifecycle routes exist and are superadmin-gated, but
running them would drive the one agent the other two agents depend on.

## 1. Reading audit rows (Q3) — procedure and scoring rule

The query in the brief is correct and the column mapping is exact. One environment gotcha: `psql`
is shadowed by an `rtk` wrapper that swallows `-c`, so use the absolute path:

```bash
PGPASSWORD=develove /opt/homebrew/bin/psql -h 127.0.0.1 -p 8101 -U postgres -d backend -A -F'|' -c \
  "select action_name, entity_type, operation, action_kind, entity_id, lookup_kind, lookup_key,
          status, triggered_by, acted_as, created_at
   from audit_logs where created_at > now() - interval '10 minutes' order by created_at desc limit 20;"
```

**What is recorded is decided by `AuditLogPolicy` (`manager/actions/audit_policy.py`):**

| case | recorded |
|---|---|
| anything that failed or was denied | always |
| successful mutation | always |
| successful read, operation opted in | yes |
| successful read, otherwise | no |

No read operation is opted in on this deployment. The scoring consequence, which governs every Q3
verdict in section 5:

- **`no row` after a successful read is correct behaviour**, not a defect. Those rows are scored
  `Q3 ok (no row — successful read, policy-correct)`.
- **`no row` after a mutation or a failure would be a defect.** Re-probing found none: every
  mutation in this slice writes a row.

An earlier draft of this report treated "successful reads write no row" as a finding. That was
wrong and has been corrected throughout. Every mutation in the slice was re-probed against the
table afterwards — etcd set/delete, manager announcement/status, scheduler ops, retention policy
create/update, IP-masking upsert/purge, all four notification mutations plus both validate paths,
resource preset create/update/delete, resource group create/purge, the app-config definition /
allow-list / fragment writes, both fair-share upsert shapes, runtime variant create, agent
resource-group update, and the CSV exports — and all of them wrote a row with the expected
`operation` and `action_kind`.

**The one genuine gap is the route middleware.** A request refused by `superadmin_required` never
reaches a processor, so `AuditLogPolicy` never sees it and no row is written — even though the
policy's first line promises that anything denied is always recorded. Every
`403 backendai_generic_forbidden` in section 5 is invisible in `audit_logs`. This is the same defect
agent B recorded on the `superadmin_required` path; it is noted here because 109 of this slice's
actions are refused that way.

Two observations worth carrying forward:

- **A public-scope app-config fragment write emits two rows for one call** —
  `global_bulk_upsert_app_config_fragments` (`global`/`upsert`/`global`) and
  `bulk_upsert_app_config_fragments` (`app_config_fragment`/`upsert`/`scope`) — because the global
  action delegates to the scope action and both are instrumented.
- **`global`-kind actions record `entity_type = 'global'`** rather than the declared type. This is
  agent A's F10 (`actions/v2/global_scope/monitor/audit_log.py:73` passes `GLOBAL_ENTITY_TYPE`
  instead of `action.entity_type()`); it is not re-filed here. This slice reproduces it on 22
  actions, listed in section 3.

## 2. Findings

Ranked most severe first.

### F1 — a plain user reads any other user's app-config fragments

| | |
|---|---|
| Declared | `app_config_fragment / search / search_app_config_fragments`, kind `scope`, gate `permission` |
| Actual | any authenticated user reads any other user's `user`-scope fragments, values included |
| Severity | highest in this slice — cross-tenant data disclosure, unlogged |

The scope the check runs against is taken from the caller-supplied request body and is never
constrained to the caller. `adapter.py:220` passes `self._ref_owner(input.scope)` straight through
to `ScopedSearchAppConfigFragmentAction(owner=...)`. The user-scope READ check then passes for any
authenticated principal. Domain-scope reads are correctly denied, and all writes (other user,
domain, public) are correctly denied — only the user-scope read leaks.

Reproduction — admin writes a value at user2's scope, then user1 reads it:

```bash
# as superadmin
./bai app-config-fragment update --scope-type user --scope-id 009fb1a4-487c-4f6e-9b1b-228b94b1d040 \
  --items '[{"config_name":"ba7489c-cfg","config":{"secret":"user2-private-value","token":"s3cr3t"}}]'

# as user@lablup.com (AKIANABBDUSEREXAMPLE)
./bai app-config-fragment get --scope-type user --scope-id 009fb1a4-487c-4f6e-9b1b-228b94b1d040 ba7489c-cfg
# -> 200, {"config": {"token": "s3cr3t", "secret": "user2-private-value"}}
```

Confirmed in both directions and on the raw route
`POST /v2/app-config-fragments/scoped/by-names`. **No audit row is written for the read**, so the
disclosure is also invisible.

Blast radius: every config value any user or admin has stored at a user scope is readable by every
authenticated account, including inactive-domain accounts. App config is the surface intended to
hold per-user client settings, so whatever a deployment puts there is exposed.

### F2 — entity-label ids are enumerable from the 403/404 split

| | |
|---|---|
| Declared | `label / update / purge_entity_label`, kind `single_entity`, gate `permission`; no-leakage expected |
| Actual | an unprivileged caller gets 403 for a label that exists and 404 for one that does not |

`lookup_entity_label_owner` runs *before* the permission check (`repository.py:169
runtime_field_owner`), so the miss is reported before the gate can mask it.

```bash
# as user@lablup.com — label exists but the caller has no permission
./bai entity-label purge 6b495057-db9b-4f06-80fc-fe8c2af811e2
# -> 403 role_create_forbidden

# as user@lablup.com — label does not exist
./bai entity-label purge 00000000-0000-0000-0000-0000000000ff
# -> 404 database_access_not-found "No field row matches the given id"
```

Blast radius: any authenticated user can probe the label id space and learn which ids are live.
The same owner-lookup-before-gate ordering is shared by every `lookup` action in the slice, so the
pattern is worth checking beyond labels.

### F3 — bulk runs give no per-item answer, and one silently writes orphan rows

Two of the three bulk shapes in this slice fail Q5, and one of them corrupts data.

**`bulk_upsert_domain_fair_share_weights`** accepts a domain that does not exist and reports it as
a success:

```bash
python3 req.py sa POST /v2/fair-share/domains/bulk-upsert \
  '{"resource_group_name":"default","inputs":[{"domain_name":"default","weight":null},
                                              {"domain_name":"ba7489c-nosuch","weight":"1.0"}]}'
# -> 200 {"upserted_count": 2}
```

A `domain_fair_shares` row for the nonexistent domain `ba7489c-nosuch` was created
(`id=667925a2-ecbb-432e-8a18-15b4d5dded5c`), with no FK preventing it. The API offers no delete
endpoint on the fair-share surface, so nothing in this run could remove what the API had created;
the row survived a manager restart and was finally removed by hand
(`delete from domain_fair_shares where id='667925a2-...'`, `DELETE 1`). Nothing in the system
reclaimed it. The table now holds only the legitimate `default` row with `weight=null`. The same
shape applies to the project and user variants. The response carries a count and nothing else: no
per-item outcome, no way to tell a write from a no-op from a bogus target.

**`search_entity_labels`** is declared `bulk` but behaves atomically — one denied entity fails the
whole run, and a nonexistent entity is reported inside the denial list rather than as a miss:

```bash
./bai entity-label search --entity-type resource_group \
  --entity-id 4d1e9b32-90c7-5b32-8f0e-6f470b8ed24a --entity-id 00000000-0000-0000-0000-0000000000ff
# as plain user -> 403 "...lacks the permission this run asks for on entities
#   [RuntimeEntityID('4d1e9b32-...'), RuntimeEntityID('00000000-...ff')]"
```

Folding the miss into the denial is good for Q4 but means Q5 cannot be satisfied at all.

For contrast, `bulk_purge_app_config_fragments` gets this right: `items` / `failed` with a reason
per id, and a denial and a miss carry the *same* message for a non-admin — passing Q4 and Q5 together.

### F4 — every self-service export requires superadmin

| | |
|---|---|
| Declared | `export_my_keypairs_c_s_v`, `export_my_sessions_c_s_v`, `export_sessions_by_project_c_s_v`, `export_users_by_domain_c_s_v` — kind `scope`, gate `permission` |
| Actual | all four return `403 user_auth_forbidden` for a plain user *and* for a domain admin |

The routes are correctly registered with `auth_required`, and the processors are correctly built
with `group.scope(...)`. The gate comes from somewhere else: every export handler first calls the
**global** `get_report` processor, which carries `SuperAdminActionValidator`.

```python
# api/rest/export/handler.py:385  (export_my_sessions_csv)
report_result = await self._export.get_report.run(
    GetReportAction(report_key=SESSIONS_REPORT_KEY)
)
```

The report-metadata lookup rejects the caller before the user-scoped export action ever runs.

```bash
BACKEND_ACCESS_KEY=AKIANABBDUSEREXAMPLE BACKEND_SECRET_KEY=... ./bai my export sessions
# -> 403 "This operation requires super-admin privileges."  (superadmin.py:26 validate)
```

Blast radius: the "export my own data" feature is unusable by the only audience it exists for, and
the two per-scope admin exports are unusable by domain admins. Superadmin gets its own data instead.

### F5 — a failed delivery probe is reported as a 500

`validate_notification_channel` and `validate_notification_rule` exist to tell an operator whether
a channel works. A channel that does not work produces a server error rather than a negative result.

```bash
# webhook pointing at a closed port
python3 req.py sa POST /v2/notifications/channels/validate '{"id":"<id>","test_message":"probe"}'
# -> 500 backendai_generic_internal-error, empty type/title  (connection error unmapped)

# webhook pointing at a reachable URL that 404s
# -> 500 notification_generic_internal-error "Webhook delivery failed with status 404: ..."
```

`validate_notification_rule` reaches the same path once a complete event payload is supplied, so it
500s too. The unreachable-host case is not even mapped to the typed error — the connection exception
escapes unhandled.

Blast radius: the validate endpoints cannot distinguish "your channel is misconfigured" from "the
manager broke", which is exactly the distinction they exist to make.

### F6 — the `my` app-config read denies every non-superadmin their own config

| | |
|---|---|
| Declared | `app_config / search / search_app_configs`, kind `scope`, gate `permission` |
| Actual | `403 role_create_forbidden` — READ on `app_config` at the caller's **own** user scope |

```bash
python3 req.py pu POST /v2/app-config/my/get '{"config_names":["ba7489c-cfg"]}'
# -> 403 "User dfa9da54-... lacks permission <Permission.READ: 1> on app_config
#         at scopes [ScopeRef(scope_type='user', scope_id=UserID('dfa9da54-...'))]"
```

Confirmed for the domain admin, both plain users and the monitor; only superadmin succeeds. The
denial fires before any config name is resolved, so it is universal.

The inconsistency is sharp: the same user *can* read and write their own fragments
(`my app-config-fragment get` / `update` both return 200) but cannot read the merged view those
fragments feed. The aggregate read is gated more tightly than the per-scope reads it aggregates.

### F7 — `GET /resource/presets` 500s: a ContextVar read with no fallback

| | |
|---|---|
| Declared | `resource_preset / search / global_list_resource_presets`, kind `global`, gate `public` |
| Actual | 500 for every principal, in every request after a short window following manager startup |

From the manager log:

```
File ".../services/resource_preset/service.py", line 87, in list_presets
LookupError: <ContextVar name='current_resource_slots' at 0x10f7e6de0>
```

`list_presets` calls `preset_data.resource_slots.normalize_slots(ignore_unknown=True)`, which reads
the `current_resource_slots` ContextVar **directly, with no fallback**. The only code that populates
that var on the manager side is `LegacyEtcdLoader.get_resource_slots()`, which does guard the read:

```python
# config/loader/legacy_etcd_loader.py:112
try:
    ret = current_resource_slots.get()
except LookupError:
    configured_slots = await self._get_resource_slots()
    ret = {**INTRINSIC_SLOTS, **configured_slots}
    current_resource_slots.set(ret)
```

`list_presets` never goes through that loader, and a `set()` inside one request's asyncio context is
not visible to any other request. Priming it in a prior request therefore does not help — verified:

```bash
for i in 1 2 3 4; do
  python3 req.py sa GET /config/resource-slots   # 200 — this path populates the var, in its own context
  python3 req.py sa GET /resource/presets        # 500 — every time
done
```

12 consecutive superadmin calls and 6 plain-user calls all returned 500 (`num_proc` is 4, so this is
not one bad worker). The one exception across the whole run was a single 200 in the first moments
after a manager restart, before it settled into failing permanently — consistent with the var being
present in the startup context and absent from later request contexts.

`global_check_resource_presets` (`POST /resource/check-presets`) returns 200 every time because it
passes `known_slot_types` explicitly instead of reading the var, which is why the defect is not more
visible.

Blast radius: the public preset list — what a client calls to show a user what they can launch — is
effectively dead on a running manager.

### F8 — mutation DTOs require an `id` in the body that the handler ignores

`update_retention_policy` and `update_resource_preset` both take the entity id in the path *and*
require it again in the body: omitting it returns `400 api_parsing_invalid-parameters` naming `id`
as a missing field, and supplying it succeeds. The body value is then silently discarded — a
mismatch is neither honoured nor rejected.

```bash
# path = logs, body id = login
python3 req.py sa PATCH /v2/retention-policies/b1e5f4a0-0001-4c10-8a01-000000000001 \
  '{"id":"b1e5f4a0-0002-4c10-8a01-000000000002","retention_period_days":364}'
# -> 200, and it is the *logs* policy that changes; login is untouched
```

The path wins, so there is no privilege bypass. The defect is the contract: clients must supply a
required field that has no effect, and a client that sends the wrong one gets a silent success on a
different entity than it named.

### F9 — an unknown scheduler op returns 500 instead of 400

```python
# api/rest/manager/handler.py:259
op = SchedulerOps(params.op)          # outside the try — ValueError escapes
try:
    args: Any = _iv_scheduler_ops_args[op].check(params.args)
except t.DataError as e:
    raise InvalidAPIParameters(...)
...
else:
    raise GenericBadRequest("Unknown scheduler operation")   # unreachable
```

```bash
python3 req.py sa POST /manager/scheduler/operation '{"op":"ba7489c-bogus","args":[]}'
# -> 500 backendai_generic_internal-error
```

The `GenericBadRequest` branch is dead code — the enum constructor raises first.

### F10 — `create_retention_policy` has no reachable success path on a seeded stack

`category` is a closed enum of exactly the eight categories the fixtures already create, and the
create path rejects duplicates with 409. On any normally seeded deployment the action can only ever
return 409; it becomes callable only after something deletes a policy.

```bash
python3 req.py sa POST /v2/retention-policies '{"category":"logs","retention_period_days":30,"enabled":false}'
# -> 409 retention-policy_generic_conflict
```

### F11 — `delete` and `purge` on a retention policy are the same destructive operation

Both are declared `operation = purge`. `DELETE /v2/retention-policies/{id}` hard-deletes the row, so
the subsequent `POST /{id}/purge` returns 404. There is no soft-delete state between them and no way
to reach `purge_retention_policy` on a row that `delete` has touched.

```bash
python3 req.py sa DELETE /v2/retention-policies/<id>        # -> 200, row gone
python3 req.py sa POST   /v2/retention-policies/<id>/purge  # -> 404
```

### F12 — the monitor account cannot execute any metric preset

`get_prometheus_query_preset` is `public`, so any authenticated caller reads the full PromQL
template. `execute_prometheus_query_preset` is `permission` and denies READ on
`prometheus_query_preset` to the plain user **and to `monitor@lablup.com`**.

```bash
BACKEND_ACCESS_KEY=AKIANAMONITOREXAMPLE ... ./bai prometheus-query-definition execute <id>
# -> 403 "User 2e10157d-... lacks permission <Permission.READ: 1> on prometheus_query_preset"
```

A monitor principal that can read every query but run none is unlikely to be the intent.

### F13 — container metrics are gated by a hand-rolled resolver check, not the action gate

`public_search_container_metrics` is declared `global`/`public`, but the real ownership check lives
in the legacy GraphQL resolver and raises a built-in exception:

```python
# api/gql_legacy/schema.py:3324
if user["role"] not in (UserRole.SUPERADMIN, UserRole.MONITOR):
    if user["uuid"] != user_id:
        raise RuntimeError("Permission denied.")
```

Behaviour is correct — self only for plain users, any user for superadmin and monitor — but it is
enforced outside the action layer, by a bare `RuntimeError` rather than a `BackendAIError`, so it
surfaces as an untyped GraphQL error with no `error_code`.

### F14 — `admin_effective_allocation` can never succeed

| | |
|---|---|
| Declared | `session / get / get_effective_allocation`, kind `scope`, gate `permission` |
| Actual | `404 No such domain` for superadmin on valid fixture ids |

```python
# api/adapters/resource_allocation/adapter.py:283
domain_name="",  # will be resolved from user_id in the repository
```

The comment is wrong. Neither `repositories/resource_allocation/repository.py:87` nor
`db_source.py:265` resolves the domain from `user_id`; the empty string reaches
`get_domain_usage("")` and raises. Secondly the action is built with
`access_key=AccessKey(access_key)` — the *caller's* key, not the target user's — so even with the
domain fixed the keypair figures would be the admin's own.

```bash
./bai admin resource-allocation effective --user-id dfa9da54-4b28-432f-be29-c0d680c7a412 \
  --project-id 2de2b969-1d04-48a6-af16-0bc8adb3c831 --resource-group default
# -> 404 No such domain.
```

The `my` variant works correctly; only the admin-targets-another-user variant is broken.

### F15 — `global_get_agent_watcher_status` 500s for superadmin

```bash
python3 req.py sa GET '/resource/watcher?agent_id=i-MacBook-Air.local'
# -> 500 backendai_generic_internal-error, empty type/title
```

The agent is stopped and no watcher is configured, so "unavailable" is the correct *answer* — the
defect is that it arrives as an untyped 500 with empty `type` and `title` rather than a typed
"watcher not reachable" error a client could act on. Low severity, and it would need re-checking
against a running agent before being filed.

### F16 — no defect: both DataLoader batches answer correctly (Q5 evidence)

Recorded as a **pass**, because Q5 is the thinnest-measured question in the audit and this is
positive evidence.

Both `bulk`-kind loaders in this slice are reachable through a nullable GraphQL relation:
`RuntimeVariantPreset.runtimeVariant` drives `public_bulk_get_runtime_variants`, and
`QueryDefinition.category` drives `public_bulk_get_prometheus_query_preset_categories`. Driven with
a mixed batch, both answer one item per input, positionally, with no cross-contamination:

| case | how it was constructed | `public_bulk_get_runtime_variants` | `..._prometheus_query_preset_categories` |
|---|---|---|---|
| valid | preset pointing at a live parent | resolves correctly | resolves correctly |
| duplicate of first | two presets pointing at the *same* parent id | both positions resolve independently and correctly | both positions resolve independently and correctly |
| null FK | preset created with no parent | n/a (column is non-null) | answers `null` at its own position |
| nonexistent | parent deleted out from under the preset | answers `null` at its own position; other positions unaffected, no query-level error | not constructible — see F17 |
| not permitted | — | **not constructible**: gate is `public`, so every authenticated caller is permitted | same |

```bash
./bai gql --v2 '{ runtimeVariantPresets(limit:50){ edges{ node{ name runtimeVariantId runtimeVariant{ name } } } } }'
#   ba7489c-p3 rvId=4f67fbb3 -> NULL          (parent deleted)
#   ba7489c-p2 rvId=d60ca018 -> ba7489c-rv1   (duplicate id, position 2)
#   ba7489c-p1 rvId=d60ca018 -> ba7489c-rv1   (duplicate id, position 3)

./bai gql --v2 '{ prometheusQueryPresets(limit:60){ edges{ node{ name categoryId category{ name } } } } }'
#   ba7489c-q2 catId=2330c5b6 -> ba7489c-cat1
#   ba7489c-q1 catId=2330c5b6 -> ba7489c-cat1
#   ba7489c-q3 catId=None     -> NULL
```

Identical results for superadmin and for the plain user. This matches what agent B found on its
DataLoader path, so the correctness looks like a property of the DataLoader implementation rather
than of any one entity.

**The limit on this evidence:** neither loader can produce a denied item, because both are gated
`public`. Q5's "denials and misses told apart" clause is therefore untestable on these two — a miss
is the only negative outcome they can produce. The three bulk surfaces in this slice that *can*
deny (`search_entity_labels`, `bulk_purge_app_config_fragments`,
`bulk_upsert_*_fair_share_weights`) are scored in F3.

### F17 — deleting a runtime variant leaves orphan presets; the sibling entity does not

Two structurally identical parent/child pairs clean up differently on parent delete.

```bash
# runtime variant: child keeps a dangling FK
./bai admin runtime-variant delete <rv2>          # -> 200
./bai runtime-variant-preset search --limit 50    # ba7489c-p3 still present, runtime_variant_id = <rv2>

# prometheus query preset category: child FK is nulled
./bai admin prometheus-query-definition-category delete <cat1>   # -> 200
./bai prometheus-query-definition search --limit 60              # ba7489c-q1/q2 present, category_id = null
```

`purge_prometheus_query_preset_category` behaves as `ON DELETE SET NULL`;
`purge_runtime_variant` leaves the child row pointing at an id that no longer exists.
`RuntimeVariantPreset.runtimeVariantId` is non-null in the GraphQL schema while
`RuntimeVariantPreset.runtimeVariant` is nullable, so the schema already anticipates the dangling
state — the loader answers `null` for it rather than failing (F16). The data is nonetheless
inconsistent, and a client reading `runtimeVariantId` gets an id it cannot resolve.

Blast radius: low in isolation, but it is the same class of missing referential cleanup as F3's
orphan fair-share row, and it is silent in both cases.

## 3. Cross-cutting observations

**The declared `permission` gate is usually not the gate that fires.** Of the 168 exercised
actions, 142 declare gate `permission`, and on 109 of them the non-admin request was refused by the
route-level `superadmin_required` middleware at `api/rest/middleware/auth.py:917` — before any RBAC
validator ran. In every one of those cases the domain admin is denied exactly as the plain user is. The declared per-entity and
per-scope gates on those actions are therefore unreachable — no RBAC grant can ever widen them.
Whole entity families are affected: the three `*_fair_share` types (all 15 actions), the three
`*_usage_bucket` types (all 6), `retention_policy` (all 6), `notification_channel` and
`notification_rule` (all 13), `app_config_definition`, `app_config_allow_list`, and every exercised
`resource_group` action.

**Confirmed F1 from the brief, with a wider blast radius than recorded.** The `client_ip` defect
blocks not only `GET /v2/audit-logs` but also the GraphQL `adminAuditLogsV2` **and**
`scopedAuditLogsV2` — the non-admin scoped surface. Both audit_log actions in this slice are
unusable from every client; only direct SQL reads the table.

```bash
./bai gql --v2 '{ adminAuditLogsV2(first:2){ count } }'
# -> "Schema validation failed. (Input should be a valid string)"
```

**Confirmed F2 from the brief.** Every 4xx/5xx response in this slice carries a full server-side
`traceback` naming the raising function and file:line. In this slice it does *not* create a new
oracle — where a denial and a miss share a status they also share a traceback (verified for
`resource_group`, `retention_policy`, `resource_preset`, `notification_channel`). The leak is a
disclosure problem in its own right, not an additional Q4 failure here. F2 in this report is a
separate, genuine Q4 failure with different status codes.

**`global`-kind actions record `entity_type = 'global'` — agent A's F10, reproduced here.** Not
re-filed. This slice hits it on 22 actions: `global_create_resource_group`,
`global_create_resource_preset`, `global_update_agent_resource_group`, `create_retention_policy`,
`upsert_client_ip_masking_policy`, `create_notification_channel`, `create_notification_rule`,
`create_runtime_variant`, `create_runtime_variant_preset`, `create_login_client_type`,
`create_resource_slot_type`, `update_resource_slot_type`, `create_app_config_definition`,
`create_app_config_allow_list`, `global_bulk_upsert_app_config_fragments`,
`create_prometheus_query_preset`, `create_prometheus_query_preset_category`, and the five global
CSV exports. `single_entity` and `scope` actions record their declared entity type correctly —
including all four `scope`-kind exports, which record `export`. Anyone filtering the audit log by
entity type loses every global-kind mutation.

**`error_code` says `create` for non-create denials.** RBAC denials return
`role_create_forbidden` regardless of the operation — seen on an UPDATE
(`upsert_entity_label`), a READ (`purge_entity_label`, `search_app_configs`) and a SEARCH
(`search_entity_labels`).

**Three different denial texts.** "Insufficient privileges" (route middleware), "Insufficient
privilege." (`InsufficientPrivilege`), and "Insufficient permission to perform this operation."
(`NotEnoughPermission`) all mean 403. The text reliably identifies which layer refused, which is a
mild fingerprinting surface.

**`admin`-namespaced CLI commands any user can run.** `admin runtime-variant search`,
`admin runtime-variant-preset search` and `admin login-client-type search` are declared `public` and
correctly return full results to a plain user — but the CLI groups them under `admin` and the help
says "with admin scope". The declaration is right; the CLI misleads.

## 4. Shared state — snapshot and restore

Every global singleton this slice touched was snapshotted, mutated, verified and restored.

| singleton | how it was exercised | restored |
|---|---|---|
| `resource_slot_type` | added `ba7489c.device` as `--disabled --not-required` so the scheduler ignores it | yes — 14 types before and after; `GET /config/resource-slots` unchanged (`cpu`, `mem`) |
| `retention_policy` | update on `logs` with exact value restore; delete + create + purge + create on `reconcile_history` | yes — 8 policies with identical categories and periods. **One caveat**: `reconcile_history` now carries a fresh UUID instead of the seeded `b1e5f4a0-0003-...`, because delete is a hard delete |
| `client_ip_masking_policy` | upsert `login_history`/`mode=none` (semantically identical to the empty table), then purge | yes — table empty again |
| `manager_admin` announcement | enabled with a probe message, then cleared | yes — `{"enabled": false, "message": ""}` |
| `manager_admin` status | written with the current value `running` only | yes — unchanged |
| `etcd_config` | set/get/delete under the `ba7489c/` prefix only | yes — key absent |
| `service_catalog` | read-only | untouched |
| scheduler ops | `include-agents` on an agent already `schedulable=t` | yes — unchanged |

The orphan `domain_fair_shares` row from F3 is no longer present because the lead deleted it —
`delete from domain_fair_shares where id='667925a2-ecbb-432e-8a18-15b4d5dded5c'`, one row removed,
leaving only the `default` row with `weight=null`. Nothing reclaimed it on its own: the row survived
the manager restart. F3 stands unchanged — the write was accepted and reported as success against a
nonexistent domain, and the API offers no way to remove what it created.

The lead's etcd key `volumes/proxies/local/secret` was never touched by this slice: the only etcd
writes were under the `ba7489c/` prefix, and both were deleted. The key is present and externally
modified, as the lead stated.

All prefixed entities were removed: resource group, runtime variant, runtime variant preset, login
client type, resource slot type, resource preset, entity labels, app config definition / allow-lists
/ fragments, prometheus query preset and category, notification channels and rules.

No user, domain, project, keypair or session was created, modified or deleted. The `session` and
`user` entity types in the `resource_group` concern were exercised on their read paths only.

## 5. Per-action results

`route exercised` names the entry point that actually reaches the action. `admin result` is
superadmin; `non-admin result` is the plain user unless noted. `SA403` shorthand is expanded in
full in the rows.

| concern | entity_type | operation | action_name | declared kind/gate | route exercised | admin result | non-admin result | audit row match | Q verdicts | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| resource_group | agent | get | `get_agent_resource_by_slot` | single_entity/permission | cli:resource-slot agent-resource search (per-slot path) | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-slot agent-resource search --limit 2 |
| resource_group | agent | get | `global_get_agent_total_resources` | global/public | cli:admin agent total-resources | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (declared public, route superadmin), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin agent total-resources |
| resource_group | agent | get | `global_get_agent_watcher_status` | global/permission | rest:GET /resource/watcher | 500 backendai_generic_internal-error | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — admin path 500s (F7) | req.py sa GET '/resource/watcher?agent_id=i-MacBook-Air.local' |
| resource_group | agent | get | `global_load_agent_container_counts` | global/public | gql:adapters/agent (batch) | not exercised | not exercised | n/a | Q1 reachable only as a GraphQL field resolver on agent nodes | grep: only caller is api/adapters/agent/adapter.py |
| resource_group | agent | lookup | `lookup_agent` | lookup/public | internal lookup via admin agent update-resource-group | 404 agent_read_not-found | n/a | no row (successful read — policy-correct) | Q1 ok (indirect), Q2 n/a, Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | ./bai admin agent update-resource-group ba7489c-nosuch-agent --resource-group-id <rg> |
| resource_group | agent | search | `global_search_agent_resources` | global/permission | cli:resource-slot agent-resource search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-slot agent-resource search --limit 2 |
| resource_group | agent | search | `global_search_agents` | global/public | cli:admin agent search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (declared public, route is superadmin-only), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin agent search --limit 2 |
| resource_group | agent | update | `global_recalculate_agent_usage` | global/permission | rest:POST /resource/recalculate-usage | ok (200 {}) | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | req.py sa POST /resource/recalculate-usage '{}' |
| resource_group | agent | update | `global_restart_agent` | global/permission | rest:POST /resource/watcher/agent/restart | not exercised | not exercised | n/a | Q1 ok (route exists, superadmin) — not exercised: would destabilise the shared stack | POST /resource/watcher/agent/restart |
| resource_group | agent | update | `global_start_agent` | global/permission | rest:POST /resource/watcher/agent/start | not exercised | not exercised | n/a | Q1 ok (route exists, superadmin) — not exercised: would drive the shared agent's lifecycle | POST /resource/watcher/agent/start |
| resource_group | agent | update | `global_stop_agent` | global/permission | rest:POST /resource/watcher/agent/stop | not exercised | not exercised | n/a | Q1 ok (route exists, superadmin) — not exercised: would destabilise the shared stack | POST /resource/watcher/agent/stop |
| resource_group | agent | update | `global_sync_agent_registry` | global/permission | rest: session handler (internal) | not exercised | not exercised | n/a | Q1 reachable only from api/rest/session/handler.py, not as a standalone client route | grep: only caller is api/rest/session/handler.py |
| resource_group | agent | update | `global_update_agent_resource_group` | global/permission | cli:admin agent update-resource-group | 404 agent_read_not-found (miss) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10); status=error on the miss | Q1 ok, Q2 ok, Q3 mismatch, Q4 ok (non-admin blocked before lookup), Q5 n/a | ./bai admin agent update-resource-group ba7489c-nosuch-agent --resource-group-id <rg> |
| resource_group | domain | get | `get_domain_usage` | single_entity/permission | cli:admin resource-allocation domain-usage | ok | 403 Forbidden operation | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-allocation domain-usage default |
| resource_group | domain_fair_share | get | `get_domain_fair_share` | scope/permission | cli:fair-share domain get / rest:POST /v2/fair-share/domains/get | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope/permission declared, route superadmin_required), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai fair-share domain get --resource-group default ... |
| resource_group | domain_fair_share | search | `global_search_domain_fair_shares` | global/permission | cli:fair-share domain search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai fair-share domain search --limit 2 |
| resource_group | domain_fair_share | search | `search_domain_fair_shares` | scope/permission | rest:POST /v2/fair-share/domains/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope declared, superadmin enforced), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/fair-share/domains/search |
| resource_group | domain_fair_share | update | `bulk_upsert_domain_fair_share_weights` | scope/permission | rest:POST /v2/fair-share/domains/bulk-upsert | ok | 403 backendai_generic_forbidden | match (domain_fair_share|update|scope) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 FAIL — returns only upserted_count, accepts nonexistent targets (F3) | req.py sa POST /v2/fair-share/domains/bulk-upsert |
| resource_group | domain_fair_share | update | `upsert_domain_fair_share_weight` | scope/permission | rest:POST /v2/fair-share/domains/upsert | ok | 403 backendai_generic_forbidden | match (domain_fair_share|update|scope) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a — operation declared update but is an upsert | req.py sa POST /v2/fair-share/domains/upsert |
| resource_group | project | get | `get_project_usage` | single_entity/permission | cli:resource-allocation project-usage | ok | 403 Insufficient permission | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (project member denied on own project), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-allocation project-usage <project> |
| resource_group | project_fair_share | get | `get_project_fair_share` | scope/permission | cli:fair-share project get / rest:POST /v2/fair-share/projects/get | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope/permission declared, route superadmin_required), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai fair-share project get --resource-group default ... |
| resource_group | project_fair_share | search | `global_search_project_fair_shares` | global/permission | cli:fair-share project search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai fair-share project search --limit 2 |
| resource_group | project_fair_share | search | `search_project_fair_shares` | scope/permission | rest:POST /v2/fair-share/projects/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope declared, superadmin enforced), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/fair-share/projects/search |
| resource_group | project_fair_share | update | `bulk_upsert_project_fair_share_weights` | scope/permission | rest:POST /v2/fair-share/projects/bulk-upsert | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 FAIL — returns only upserted_count, accepts nonexistent targets (F3) | req.py sa POST /v2/fair-share/projects/bulk-upsert |
| resource_group | project_fair_share | update | `upsert_project_fair_share_weight` | scope/permission | rest:POST /v2/fair-share/projects/upsert | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a — operation declared update but is an upsert | req.py sa POST /v2/fair-share/projects/upsert |
| resource_group | resource_group | create | `associate_resource_group_with_domains` | single_entity/permission | cli:admin resource-group allow-domains --add | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok (folded into update_allowed_domains_*), Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-group allow-domains ba7489c-rg --add default |
| resource_group | resource_group | create | `associate_resource_group_with_keypairs` | single_entity/permission | none | not exercised | not exercised | n/a | Q1 unreachable — no CLI command and no keypair route on the resource-group registry | grep registry.py: no keypair path |
| resource_group | resource_group | create | `associate_resource_group_with_projects` | single_entity/permission | cli:admin resource-group allow-projects --add | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok (folded), Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-group allow-projects ba7489c-rg --add <project> |
| resource_group | resource_group | create | `global_create_resource_group` | global/permission | cli:admin resource-group create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin resource-group create --name ba7489c-rg --domain-name default |
| resource_group | resource_group | delete | `disassociate_resource_group_from_domains` | single_entity/permission | cli:admin resource-group allow-domains --remove | not exercised | not exercised | n/a | Q1 ok (route exists), not run to avoid perturbing the default domain binding | ./bai admin resource-group allow-domains <rg> --remove <domain> |
| resource_group | resource_group | delete | `disassociate_resource_group_from_keypairs` | single_entity/permission | none | not exercised | not exercised | n/a | Q1 unreachable — same as the associate counterpart | no keypair path on the registry |
| resource_group | resource_group | delete | `disassociate_resource_group_from_projects` | single_entity/permission | cli:admin resource-group allow-projects --remove | not exercised | not exercised | n/a | Q1 ok (route exists), not run to avoid perturbing the default project binding | ./bai admin resource-group allow-projects <rg> --remove <project> |
| resource_group | resource_group | get | `get_allowed_domains_for_resource_group` | single_entity/permission | cli:admin resource-group allowed-domains | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | ./bai admin resource-group allowed-domains default |
| resource_group | resource_group | get | `get_allowed_projects_for_resource_group` | single_entity/permission | cli:admin resource-group allowed-projects | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | ./bai admin resource-group allowed-projects default |
| resource_group | resource_group | get | `get_resource_group_resource_info` | single_entity/permission | cli:admin resource-group resource-info | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 ok (403 for both real and miss), Q5 n/a | ./bai admin resource-group resource-info default |
| resource_group | resource_group | get | `global_get_resource_group_usage` | global/permission | cli:resource-allocation resource-group-usage | ok | 403 Insufficient privilege | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-allocation resource-group-usage default |
| resource_group | resource_group | get | `global_get_wsproxy_version` | global/public | none | not exercised | not exercised | n/a | Q1 unreachable via CLI/REST v2 in this slice's routes | no route found in api/rest/v2/resource_group/registry.py |
| resource_group | resource_group | get | `global_resolve_resource_group_ids` | global/permission | none (internal) | not exercised | not exercised | n/a | Q1 internal helper — no client route | no api/ caller with a route |
| resource_group | resource_group | lookup | `lookup_resource_group` | lookup/public | internal lookup via admin resource-group resource-info | 404 database_access_not-found | n/a | match (lookup_kind=resource_group_name, lookup_key=name=...) | Q1 ok (indirect), Q2 n/a, Q3 match, Q4 leaks (see F5), Q5 n/a | ./bai admin resource-group resource-info ba7489c-nosuch |
| resource_group | resource_group | purge | `purge_resource_group` | single_entity/permission | cli:admin resource-group delete | ok | 403 backendai_generic_forbidden | match (resource_group|purge|single_entity) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a | ./bai admin resource-group delete ba7489c-rg |
| resource_group | resource_group | search | `global_search_resource_groups` | global/permission | cli:admin resource-group search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (route superadmin, not RBAC), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-group search --limit 2 |
| resource_group | resource_group | search | `scoped_search_resource_groups` | scope/permission | none | not exercised | not exercised | n/a | Q1 unreachable — no CLI/REST scoped route found, only the global admin search | grep registry.py: only /search (superadmin) |
| resource_group | resource_group | update | `replace_resource_group_default_deployment_options` | single_entity/permission | cli:admin resource-group default-options get/replace | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai admin resource-group default-options get ba7489c-rg |
| resource_group | resource_group | update | `replace_resource_group_default_session_options` | single_entity/permission | cli:admin resource-group default-session-options get/replace | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai admin resource-group default-session-options get ba7489c-rg |
| resource_group | resource_group | update | `update_allowed_domains_for_resource_group` | single_entity/permission | cli:admin resource-group allow-domains | ok | 403 backendai_generic_forbidden | match (resource_group|update|single_entity) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a | ./bai admin resource-group allow-domains ba7489c-rg --add default |
| resource_group | resource_group | update | `update_allowed_projects_for_resource_group` | single_entity/permission | cli:admin resource-group allow-projects | ok | 403 backendai_generic_forbidden | match (resource_group|update|single_entity) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a | ./bai admin resource-group allow-projects ba7489c-rg --add <project> |
| resource_group | resource_group | update | `update_allowed_resource_groups_for_domain` | single_entity/permission | cli:admin resource-group allow-for-domain | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 not observed, Q4 n/a, Q5 n/a | ./bai admin resource-group allow-for-domain default --add default |
| resource_group | resource_group | update | `update_allowed_resource_groups_for_project` | single_entity/permission | cli:admin resource-group allow-for-project | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 not observed, Q4 n/a, Q5 n/a | ./bai admin resource-group allow-for-project <project> --add default |
| resource_group | resource_group | update | `update_resource_group` | single_entity/permission | cli:admin resource-group update | ok | 403 backendai_generic_forbidden | match (resource_group|update|single_entity) | Q1 ok, Q2 mismatch, Q3 match, Q4 ok, Q5 n/a | ./bai admin resource-group update ba7489c-rg --description x |
| resource_group | resource_group | update | `update_resource_group_fair_share_spec` | single_entity/permission | rest:PATCH /v2/resource-groups/{name}/fair-share-spec | 400 api_parsing_invalid-parameters | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok (route exists), Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | req.py sa PATCH /v2/resource-groups/default/fair-share-spec '{"half_life_days":7}' -> 400 schema |
| resource_group | resource_preset | create | `global_create_resource_preset` | global/permission | rest:POST /v2/resource-presets | ok (201) | 403 Forbidden operation | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | req.py sa POST /v2/resource-presets '{"name":"ba7489c-preset","resource_slots":[{"resource_type":"cpu","quantity":"1"},{"resource_type":"mem","quantity":"1073741824"}]}' |
| resource_group | resource_preset | delete | `delete_resource_preset` | single_entity/permission | rest:DELETE /v2/resource-presets/{id} | ok | 403 backendai_generic_forbidden | match (resource_preset|delete|single_entity) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a | req.py sa DELETE /v2/resource-presets/<id> |
| resource_group | resource_preset | lookup | `lookup_resource_preset` | lookup/public | internal lookup via GET /v2/resource-presets/{id} | 404 resource-preset_read_not-found | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok (indirect), Q2 n/a, Q3 ok (no row — successful read, policy-correct), Q4 ok (403 for both real and miss), Q5 n/a | req.py pu GET /v2/resource-presets/00000000-0000-0000-0000-0000000000ff |
| resource_group | resource_preset | search | `check_preset_availability` | scope/permission | cli:admin resource-preset check-availability | ok | 403 Insufficient permission | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-preset check-availability --project-id <p> --resource-group default |
| resource_group | resource_preset | search | `global_check_resource_presets` | global/public | rest:POST /resource/check-presets | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (public gate honoured), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py pu POST /resource/check-presets '{"scaling_group":"default","group":"default"}' |
| resource_group | resource_preset | search | `global_list_resource_presets` | global/public | rest:GET /resource/presets | 500 backendai_generic_internal-error | 500 backendai_generic_internal-error | no row (successful read — policy-correct) | Q1 ok, Q2 unobservable (500 before any gate), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — always 500 (F2) | req.py sa GET /resource/presets |
| resource_group | resource_preset | search | `global_search_resource_presets` | global/permission | cli:admin resource-preset search | ok | 403 Forbidden operation | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-preset search --limit 2 |
| resource_group | resource_preset | update | `update_resource_preset` | single_entity/permission | rest:PATCH /v2/resource-presets/{id} | 400 api_parsing_invalid-parameters (needs body id) | 403 backendai_generic_forbidden | match (resource_preset|update|single_entity) | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a — body `id` required though path carries it (F8) | req.py sa PATCH /v2/resource-presets/<id> '{"name":"x"}' |
| resource_group | session | get | `get_domain_resource_overview` | scope/permission | cli:admin resource-allocation domain-usage | ok | 403 Forbidden operation | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin resource-allocation domain-usage default |
| resource_group | session | get | `get_effective_allocation` | scope/permission | cli:my resource-allocation effective / admin ... effective | ok (my) / 404 No such domain (admin) | ok (my) | match (session|get|scope) on the error path | Q1 ok, Q2 ok for my, Q3 match, Q4 n/a, Q5 n/a — admin variant always 404s (F4) | ./bai admin resource-allocation effective --user-id <u> --project-id <p> --resource-group default |
| resource_group | session | get | `get_kernel_allocation_by_slot` | single_entity/permission | cli:resource-slot allocation search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-slot allocation search --limit 2 |
| resource_group | session | get | `get_project_resource_overview` | scope/permission | cli:resource-allocation project-usage | ok | 403 Insufficient permission | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-allocation project-usage <project> |
| resource_group | session | lookup | `lookup_kernel_owner` | lookup/permission | internal lookup | not exercised | not exercised | n/a | Q1 internal owner lookup; no session mutation run (agent A owns identity, no sessions created) | not run — session creation out of scope for this slice |
| resource_group | session | search | `global_search_resource_allocations` | global/permission | cli:resource-slot allocation search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-slot allocation search --limit 2 |
| resource_group | user | get | `get_keypair_usage` | single_entity/permission | cli:my resource-allocation keypair-usage | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (self-service works for all), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai my resource-allocation keypair-usage |
| resource_group | user | get | `resolve_keypair_context` | single_entity/permission | internal (folded into keypair-usage/effective) | ok | ok | no row (successful read — policy-correct) | Q1 ok (indirect), Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai my resource-allocation keypair-usage |
| resource_group | user_fair_share | get | `get_user_fair_share` | scope/permission | cli:fair-share user get / rest:POST /v2/fair-share/users/get | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope/permission declared, route superadmin_required), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai fair-share user get --resource-group default ... |
| resource_group | user_fair_share | search | `global_search_user_fair_shares` | global/permission | cli:fair-share user search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai fair-share user search --limit 2 |
| resource_group | user_fair_share | search | `search_user_fair_shares` | scope/permission | rest:POST /v2/fair-share/users/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope declared, superadmin enforced), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/fair-share/users/search |
| resource_group | user_fair_share | update | `bulk_upsert_user_fair_share_weights` | scope/permission | rest:POST /v2/fair-share/users/bulk-upsert | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 FAIL — returns only upserted_count, accepts nonexistent targets (F3) | req.py sa POST /v2/fair-share/users/bulk-upsert |
| resource_group | user_fair_share | update | `upsert_user_fair_share_weight` | scope/permission | rest:POST /v2/fair-share/users/upsert | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a — operation declared update but is an upsert | req.py sa POST /v2/fair-share/users/upsert |
| resource_group | domain_usage_bucket | search | `global_search_domain_usage_buckets` | global/permission | cli:resource-usage domain search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-usage domain search --limit 2 |
| resource_group | domain_usage_bucket | search | `search_domain_usage_buckets` | scope/permission | rest:POST /v2/resource-usage/domains/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope declared, superadmin route), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — catalog entity_type `global` vs checked `domain` (BA-7486 R) | req.py sa POST /v2/resource-usage/domains/search |
| resource_group | project_usage_bucket | search | `global_search_project_usage_buckets` | global/permission | cli:resource-usage project search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-usage project search --limit 2 |
| resource_group | project_usage_bucket | search | `search_project_usage_buckets` | scope/permission | rest:POST /v2/resource-usage/projects/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope declared, superadmin route), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — catalog entity_type `global` vs checked `project` (BA-7486 R) | req.py sa POST /v2/resource-usage/projects/search |
| resource_group | user_usage_bucket | search | `global_search_user_usage_buckets` | global/permission | cli:resource-usage user search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-usage user search --limit 2 |
| resource_group | user_usage_bucket | search | `search_user_usage_buckets` | scope/permission | rest:POST /v2/resource-usage/users/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch (scope declared, superadmin route), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — catalog entity_type `global` vs checked `user` (BA-7486 R) | req.py sa POST /v2/resource-usage/users/search |
| system | client_ip_masking_policy | purge | `purge_client_ip_masking_policy` | single_entity/permission | rest:POST /v2/client-ip-masking-policies/purge | ok | 403 backendai_generic_forbidden | match (client_ip_masking_policy|purge|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 ok (403 for both real and miss as non-admin), Q5 n/a — restored to empty | req.py sa POST /v2/client-ip-masking-policies/purge '{"id":"<id>"}' |
| system | client_ip_masking_policy | search | `search_client_ip_masking_policies` | global/permission | rest:POST /v2/client-ip-masking-policies/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/client-ip-masking-policies/search |
| system | client_ip_masking_policy | upsert | `upsert_client_ip_masking_policy` | global/permission | rest:POST /v2/client-ip-masking-policies/upsert | ok (create and update paths) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — used target login_history/mode none so effective behaviour was unchanged | req.py sa POST /v2/client-ip-masking-policies/upsert '{"target_type":"login_history","mode":"none"}' |
| system | etcd_config | delete | `delete_etcd_config` | global/permission | rest:POST /config/delete | ok | 403 backendai_generic_forbidden | match (global|delete|global) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | req.py sa POST /config/delete '{"key":"ba7489c/probe"}' |
| system | etcd_config | get | `get_etcd_config` | global/permission | rest:POST /config/get | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok (missing key returns 200 result:null, not 404), Q5 n/a | req.py sa POST /config/get '{"key":"ba7489c/probe"}' |
| system | etcd_config | get | `get_resource_metadata` | global/public | rest:GET /config/resource-slots/details | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py pu GET /config/resource-slots/details |
| system | etcd_config | get | `get_resource_slots` | global/public | rest:GET /config/resource-slots | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (public honoured), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py pu GET /config/resource-slots |
| system | etcd_config | get | `get_vfolder_types` | global/public | rest:GET /config/vfolder-types | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py pu GET /config/vfolder-types |
| system | etcd_config | update | `set_etcd_config` | global/permission | rest:POST /config/set | ok | 403 backendai_generic_forbidden | match (global|update|global) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | req.py sa POST /config/set '{"key":"ba7489c/probe","value":"runtime-audit"}' |
| system | login_client_type | create | `create_login_client_type` | global/permission | cli:admin login-client-type create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin login-client-type create --name ba7489c-lct |
| system | login_client_type | get | `get_login_client_type` | single_entity/public | cli:login-client-type get | ok | ok | match | Q1 ok, Q2 ok (public honoured), Q3 match, Q4 n/a, Q5 n/a | ./bai login-client-type get <id> |
| system | login_client_type | purge | `purge_login_client_type` | single_entity/permission | cli:admin login-client-type delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | ./bai admin login-client-type delete <id> |
| system | login_client_type | search | `search_login_client_types` | global/public | cli:admin login-client-type search | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (declared public; note the CLI advertises it as admin), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin login-client-type search --limit 2 (as plain user: ok) |
| system | login_client_type | update | `update_login_client_type` | single_entity/permission | cli:admin login-client-type update | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | ./bai admin login-client-type update <id> --description x |
| system | manager_admin | get | `fetch_manager_status` | global/permission | rest:GET /manager/status | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa GET /manager/status |
| system | manager_admin | get | `get_db_connection_status` | global/permission | rest:GET /manager/prom | ok (prometheus text) | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa GET /manager/prom |
| system | manager_admin | get | `get_manager_announcement` | global/permission | rest:GET /manager/announcement | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa GET /manager/announcement |
| system | manager_admin | update | `perform_scheduler_ops` | global/permission | rest:POST /manager/scheduler/operation | ok (204) | 403 backendai_generic_forbidden | match (global|update|global) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a — unknown op returns 500 not 400 (F9) | req.py sa POST /manager/scheduler/operation '{"op":"include-agents","args":["i-MacBook-Air.local"]}' |
| system | manager_admin | update | `update_manager_announcement` | global/permission | rest:POST /manager/announcement | ok (204) | 403 backendai_generic_forbidden | match (global|update|global) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a — snapshot/restore verified | req.py sa POST /manager/announcement '{"enabled":true,"message":"..."}' then restore |
| system | manager_admin | update | `update_manager_status` | global/permission | rest:PUT /manager/status | ok (204) | 403 backendai_generic_forbidden | match (global|update|global) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a — set to current value `running` only | req.py sa PUT /manager/status '{"status":"running","force_kill":false}' |
| system | resource_slot_type | create | `create_resource_slot_type` | global/permission | cli:resource-slot slot-type create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai resource-slot slot-type create ba7489c.device count --disabled --not-required |
| system | resource_slot_type | get | `get_resource_slot_type` | single_entity/public | none | not exercised | not exercised | n/a | Q1 unreachable — no CLI command and no GET route on the resource-slots registry | registry.py has only /slot-types/search, POST, PATCH, DELETE |
| system | resource_slot_type | lookup | `lookup_resource_slot_type` | lookup/public | internal lookup via DELETE /slot-types/{slot_name} | 404 database_access_not-found | n/a | match (lookup_kind=resource_slot_type_name, lookup_key=slot_name=...) | Q1 ok (indirect), Q2 n/a, Q3 match, Q4 n/a, Q5 n/a | ./bai resource-slot slot-type delete ba7489c-nosuch.device |
| system | resource_slot_type | purge | `purge_resource_slot_type` | single_entity/permission | cli:resource-slot slot-type delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a — singleton restored 14->14 | ./bai resource-slot slot-type delete ba7489c.device |
| system | resource_slot_type | search | `search_resource_slot_types` | global/public | cli:resource-slot slot-type search | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (public honoured), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai resource-slot slot-type search --limit 3 |
| system | resource_slot_type | update | `update_resource_slot_type` | global/permission | cli:resource-slot slot-type update | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai resource-slot slot-type update ba7489c.device --description x |
| system | retention_policy | create | `create_retention_policy` | global/permission | rest:POST /v2/retention-policies | ok (201) / 409 on duplicate category | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — category enum is exhausted by the 8 seeded rows (F10) | req.py sa POST /v2/retention-policies '{"category":"reconcile_history","retention_period_days":365,"enabled":false}' |
| system | retention_policy | get | `get_retention_policy` | single_entity/permission | rest:GET /v2/retention-policies/{id} | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok (403 for both real and miss), Q5 n/a | req.py pu GET /v2/retention-policies/<id> vs /00000000-...ff -> both 403 |
| system | retention_policy | purge | `delete_retention_policy` | single_entity/permission | rest:DELETE /v2/retention-policies/{id} | ok (hard delete) | 403 backendai_generic_forbidden | row written (mutation) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a — hard-deletes, so purge afterwards 404s (F11) | req.py sa DELETE /v2/retention-policies/<id> |
| system | retention_policy | purge | `purge_retention_policy` | single_entity/permission | rest:POST /v2/retention-policies/{id}/purge | ok | 403 backendai_generic_forbidden | row written (mutation) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a — indistinguishable from delete (F11) | req.py sa POST /v2/retention-policies/<id>/purge |
| system | retention_policy | search | `search_retention_policies` | global/permission | rest:POST /v2/retention-policies/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/retention-policies/search |
| system | retention_policy | update | `update_retention_policy` | single_entity/permission | rest:PATCH /v2/retention-policies/{id} | ok | 403 backendai_generic_forbidden | match (retention_policy|update|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 ok, Q5 n/a — body `id` required but silently ignored (F8) | req.py sa PATCH /v2/retention-policies/<logs> '{"id":"<login>","retention_period_days":364}' -> path wins |
| system | runtime_variant | create | `create_runtime_variant` | global/permission | cli:admin runtime-variant create | ok | 403 Forbidden operation | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin runtime-variant create '{"name":"ba7489c-rv"}' |
| system | runtime_variant | get | `public_bulk_get_runtime_variants` | bulk/public | gql:runtimeVariantPresets { runtimeVariant } (DataLoader batch) | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (public honoured), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 PASS — one answer per input, positional, duplicate ids independent, nonexistent answers null without affecting other positions (F16) | ./bai gql --v2 '{ runtimeVariantPresets(limit:50){ edges{ node{ name runtimeVariantId runtimeVariant{ name } } } } }' |
| system | runtime_variant | get | `public_get_runtime_variant` | single_entity/public | cli:runtime-variant get | ok | ok | match (on the error path) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | ./bai runtime-variant get <id> |
| system | runtime_variant | lookup | `lookup_runtime_variant` | lookup/public | internal lookup | not observed | not observed | no row (successful read — policy-correct) | Q1 indirect; no lookup row surfaced on the paths exercised | ./bai runtime-variant get <id> |
| system | runtime_variant | purge | `purge_runtime_variant` | single_entity/permission | cli:admin runtime-variant delete | ok | 403 Forbidden operation | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai admin runtime-variant delete <id> |
| system | runtime_variant | search | `search_runtime_variants` | global/public | cli:runtime-variant search | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai runtime-variant search --limit 2 |
| system | runtime_variant | update | `update_runtime_variant` | single_entity/permission | cli:admin runtime-variant update | ok | 403 Forbidden operation | match | Q1 ok, Q2 mismatch (single_entity/permission declared, route superadmin), Q3 match, Q4 ok, Q5 n/a | ./bai admin runtime-variant update <id> '{"description":"x"}' |
| system | runtime_variant_preset | create | `create_runtime_variant_preset` | global/permission | cli:admin runtime-variant-preset create | ok | 403 Forbidden operation | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin runtime-variant-preset create '{"runtime_variant_id":"<rv>","name":"ba7489c-tp",...}' |
| system | runtime_variant_preset | get | `public_get_runtime_variant_preset` | single_entity/public | cli:runtime-variant-preset get | ok | ok | match (error path) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | ./bai runtime-variant-preset get <id> |
| system | runtime_variant_preset | purge | `purge_runtime_variant_preset` | single_entity/permission | cli:admin runtime-variant-preset delete | ok | 403 Forbidden operation | row written (mutation; not individually captured) | Q1 ok, Q2 mismatch, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai admin runtime-variant-preset delete <id> |
| system | runtime_variant_preset | search | `search_runtime_variant_presets` | global/public | cli:runtime-variant-preset search | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai runtime-variant-preset search --limit 2 |
| system | runtime_variant_preset | update | `update_runtime_variant_preset` | single_entity/permission | cli:admin runtime-variant-preset update | ok | 403 Forbidden operation | match | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a | ./bai admin runtime-variant-preset update <id> '{"description":"x"}' |
| system | service_catalog | search | `search_service_catalogs` | global/permission | cli:admin service-catalog search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — read-only, singleton untouched | ./bai admin service-catalog search --limit 2 |
| app_config | app_config | search | `anonymous_search_app_configs` | scope/anonymous | rest:POST /v2/app-config/public/get (no auth) | ok | ok (unauthenticated) | no row (successful read — policy-correct) | Q1 ok, Q2 ok (anonymous gate honoured, no credentials needed), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 ok (positional) | curl -X POST http://127.0.0.1:8091/v2/app-config/public/get -d '{"config_names":["ba7489c-cfg"]}' |
| app_config | app_config | search | `search_app_configs` | scope/permission | rest:POST /v2/app-config/my/get | ok | 403 role_create_forbidden (READ on app_config at own user scope) | no row (successful read — policy-correct) | Q1 ok, Q2 FAIL — the self-service `my` read denies every non-superadmin on their own scope (F6), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py pu POST /v2/app-config/my/get '{"config_names":["ba7489c-cfg"]}' |
| app_config | app_config_allow_list | create | `create_app_config_allow_list` | global/permission | cli:admin app-config-allow-list create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin app-config-allow-list create --config-name ba7489c-cfg --scope-type public |
| app_config | app_config_allow_list | get | `bulk_get_app_config_allow_lists` | bulk/permission | gql:dataloader batch | not exercised | not exercised | n/a | Q1 no live caller found — same as bulk_get_app_config_definitions | grep supergraph.graphql + api/gql/data_loader/data_loaders.py |
| app_config | app_config_allow_list | get | `get_app_config_allow_list` | single_entity/permission | cli:admin app-config-allow-list get | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | ./bai admin app-config-allow-list get <id> |
| app_config | app_config_allow_list | purge | `purge_app_config_allow_list` | single_entity/permission | cli:admin app-config-allow-list purge | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai admin app-config-allow-list purge <id> |
| app_config | app_config_allow_list | search | `admin_search_app_config_allow_lists` | global/permission | cli:admin app-config-allow-list search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin app-config-allow-list search --limit 3 |
| app_config | app_config_allow_list | update | `update_app_config_allow_list` | single_entity/permission | cli:admin app-config-allow-list update | ok | 403 backendai_generic_forbidden | row written (mutation; not individually captured) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai admin app-config-allow-list update <id> --rank 350 |
| app_config | app_config_definition | create | `create_app_config_definition` | global/permission | cli:admin app-config-definition create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin app-config-definition create --config-name ba7489c-cfg |
| app_config | app_config_definition | get | `bulk_get_app_config_definitions` | bulk/permission | gql:dataloader batch | not exercised | not exercised | n/a | Q1 no live caller found — the only GraphQL appConfigDefinition fields are create payloads, which do not go through the loader | grep supergraph.graphql + api/gql/data_loader/data_loaders.py |
| app_config | app_config_definition | get | `get_app_config_definition` | single_entity/permission | cli:admin app-config-definition get | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | ./bai admin app-config-definition get <id> |
| app_config | app_config_definition | purge | `purge_app_config_definition` | single_entity/permission | cli:admin app-config-definition purge | ok | 403 backendai_generic_forbidden | match (app_config_definition|purge|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | ./bai admin app-config-definition purge <id> |
| app_config | app_config_definition | search | `global_search_app_config_definitions` | global/permission | cli:admin app-config-definition search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin app-config-definition search --limit 3 |
| app_config | app_config_fragment | get | `bulk_get_app_config_fragments` | bulk/permission | cli:app-config-fragment get / my app-config-fragment get | ok | ok (own scope) | no row (successful read — policy-correct) | Q1 ok, Q2 ok for own scope, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 ok — 3 names in, 3 answers out, null for unknown | ./bai app-config-fragment get --scope-type public ba7489c-cfg ba7489c-nosuch ba7489c-cfg |
| app_config | app_config_fragment | get | `get_app_config_fragment` | single_entity/permission | rest:GET /v2/app-config-fragments/{id} | ok | ok (own) | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai app-config-fragment get --scope-type public ba7489c-cfg |
| app_config | app_config_fragment | purge | `bulk_purge_app_config_fragments` | bulk/permission | cli:app-config-fragment bulk-purge --id ... --id ... | ok | partial: own purged, others reported in `failed` | row written (mutation; not individually captured) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 ok — a denial and a miss carry the SAME message for a non-admin, Q5 ok — per-item `items`/`failed` with reasons | ./bai app-config-fragment bulk-purge --id <own> --id <other> --id 00000000-0000-0000-0000-0000000000ff |
| app_config | app_config_fragment | purge | `purge_app_config_fragment` | single_entity/permission | cli:app-config-fragment purge --id | ok | 403 Insufficient permission (other user's) | row written (mutation; not individually captured) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a | ./bai app-config-fragment purge --id <fragment> |
| app_config | app_config_fragment | search | `admin_search_app_config_fragments` | global/permission | cli:admin app-config-fragment search | ok | 403 Forbidden operation | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin app-config-fragment search --limit 3 |
| app_config | app_config_fragment | search | `search_app_config_fragments` | scope/permission | rest:POST /v2/app-config-fragments/scoped/by-names | ok | ok — including OTHER users' scopes | no row (successful read — policy-correct) | Q1 ok, Q2 FAIL — cross-user read (F1), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 ok (positional, null for absent) | req.py pu POST /v2/app-config-fragments/scoped/by-names '{"scope":{"scope_type":"user","scope_id":"<other-user>"},"config_names":["ba7489c-cfg"]}' |
| app_config | app_config_fragment | upsert | `bulk_upsert_app_config_fragments` | scope/permission | cli:app-config-fragment update / my app-config-fragment update | ok | ok (own scope only) | match (app_config_fragment|upsert|scope) | Q1 ok, Q2 ok — writes to other users, domain and public scopes are all correctly denied, Q3 match, Q4 n/a, Q5 atomic (all-or-nothing, as documented) | ./bai app-config-fragment update --scope-type user --scope-id <other> --items '[...]' -> 403 |
| app_config | app_config_fragment | upsert | `global_bulk_upsert_app_config_fragments` | global/permission | rest:POST /v2/app-config-fragments/scoped/bulk-upsert (public scope) | ok | 403 Insufficient privilege | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 atomic | ./bai app-config-fragment update --scope-type public --items '[...]' |
| metric | prometheus_query_preset | create | `create_prometheus_query_preset` | global/permission | cli:admin prometheus-query-definition create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin prometheus-query-definition create --name ba7489c-query --metric-name up --query-template 'up{}' |
| metric | prometheus_query_preset | get | `execute_prometheus_query_preset` | single_entity/permission | cli:prometheus-query-definition execute | ok | 403 role_create_forbidden (READ on prometheus_query_preset) | no row (successful read — policy-correct) | Q1 ok, Q2 mismatch in effect — a user may read the preset but not run it, and the monitor account is denied too (F12), Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | ./bai prometheus-query-definition execute <id> (as pu and as monitor: 403) |
| metric | prometheus_query_preset | get | `get_prometheus_query_preset` | single_entity/public | cli:prometheus-query-definition get | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (public honoured — full PromQL template is world-readable), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai prometheus-query-definition get <id> |
| metric | prometheus_query_preset | get | `preview_prometheus_query_preset` | global/permission | cli:admin prometheus-query-definition preview | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — bad template returns a clean 400 metric_read_invalid-parameters | ./bai admin prometheus-query-definition preview --query-template 'up{{{' |
| metric | prometheus_query_preset | purge | `purge_prometheus_query_preset` | single_entity/permission | cli:admin prometheus-query-definition delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 match, Q4 n/a, Q5 n/a | ./bai admin prometheus-query-definition delete <id> |
| metric | prometheus_query_preset | search | `public_search_container_metric_metadata` | global/public | gql:container_utilization_metric_metadata (gql_legacy) | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai gql '{ container_utilization_metric_metadata { metric_names } }' |
| metric | prometheus_query_preset | search | `public_search_container_metrics` | global/public | gql:user_utilization_metric (gql_legacy) | ok | ok for self, 'Permission denied.' for another user | no row (successful read — policy-correct) | Q1 ok, Q2 ok in effect but enforced by a hand-rolled resolver check raising a bare RuntimeError, not the action gate (F13), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai gql 'query($u:UUID!){ user_utilization_metric(user_id:$u, props:{...}) { user_id } }' |
| metric | prometheus_query_preset | search | `search_prometheus_query_presets` | global/public | cli:prometheus-query-definition search | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai prometheus-query-definition search --limit 3 |
| metric | prometheus_query_preset | update | `update_prometheus_query_preset` | single_entity/permission | cli:admin prometheus-query-definition update | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch (single_entity/permission declared, route superadmin), Q3 match, Q4 n/a, Q5 n/a | ./bai admin prometheus-query-definition update <id> --description x |
| metric | prometheus_query_preset_category | create | `create_prometheus_query_preset_category` | global/permission | cli:admin prometheus-query-definition-category create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | ./bai admin prometheus-query-definition-category create --name ba7489c-cat |
| metric | prometheus_query_preset_category | get | `get_prometheus_query_preset_category` | single_entity/public | cli:prometheus-query-definition-category get | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai prometheus-query-definition-category get <id> |
| metric | prometheus_query_preset_category | get | `public_bulk_get_prometheus_query_preset_categories` | bulk/public | gql:prometheusQueryPresets { category } (DataLoader batch) | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok (public honoured), Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 PASS — positional, duplicate ids independent, null FK answers null; dangling id not constructible (F17) | ./bai gql --v2 '{ prometheusQueryPresets(limit:60){ edges{ node{ name categoryId category{ name } } } } }' |
| metric | prometheus_query_preset_category | purge | `purge_prometheus_query_preset_category` | single_entity/permission | cli:admin prometheus-query-definition-category delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | ./bai admin prometheus-query-definition-category delete <id> |
| metric | prometheus_query_preset_category | search | `search_prometheus_query_preset_categories` | global/public | cli:prometheus-query-definition-category search | ok | ok | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai prometheus-query-definition-category search --limit 3 |
| notification_center | notification_channel | create | `create_notification_channel` | global/permission | rest:POST /v2/notifications/channels | ok (201) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | req.py sa POST /v2/notifications/channels '{"name":"ba7489c-chan","channel_type":"webhook","spec":{"webhook":{"url":"..."}},"enabled":false}' |
| notification_center | notification_channel | get | `get_notification_channel` | single_entity/permission | rest:GET /v2/notifications/channels/{id} | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok (403 for both real and miss), Q5 n/a | req.py sa GET /v2/notifications/channels/<id> |
| notification_center | notification_channel | purge | `purge_notification_channel` | single_entity/permission | cli:notification channel delete / rest:POST .../channels/delete | ok | 403 backendai_generic_forbidden | match (notification_channel|purge|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | req.py sa POST /v2/notifications/channels/delete '{"id":"<id>"}' |
| notification_center | notification_channel | search | `search_notification_channels` | global/permission | cli:notification channel search / rest:POST .../channels/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/notifications/channels/search |
| notification_center | notification_channel | update | `update_notification_channel` | single_entity/permission | rest:PATCH /v2/notifications/channels/{id} | ok | 403 backendai_generic_forbidden | match (notification_channel|update|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | req.py sa PATCH /v2/notifications/channels/<id> '{"description":"x"}' |
| notification_center | notification_channel | update | `validate_notification_channel` | single_entity/permission | rest:POST /v2/notifications/channels/validate | 500 on any delivery failure | 403 backendai_generic_forbidden | match (notification_channel|update|single_entity, status=error) | Q1 ok, Q2 ok, Q3 match, Q4 ok (missing id gives a clean 404), Q5 n/a — a failed probe is reported as a server error (F5) | req.py sa POST /v2/notifications/channels/validate '{"id":"<id>","test_message":"probe"}' |
| notification_center | notification_rule | create | `create_notification_rule` | global/permission | rest:POST /v2/notifications/rules | ok (201) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | req.py sa POST /v2/notifications/rules '{"name":"ba7489c-rule","rule_type":"session.started",...}' |
| notification_center | notification_rule | create | `process_notification` | global/permission | bgtask:event_dispatcher/handlers/notification.py | not exercised | not exercised | n/a | Q1 internal only — driven by the event dispatcher, no client route | grep: only caller is event_dispatcher/handlers/notification.py:75 |
| notification_center | notification_rule | get | `get_notification_rule` | single_entity/permission | rest:GET /v2/notifications/rules/{id} | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok, Q5 n/a | req.py sa GET /v2/notifications/rules/<id> |
| notification_center | notification_rule | purge | `purge_notification_rule` | single_entity/permission | cli:notification rule delete / rest:POST .../rules/delete | ok | 403 backendai_generic_forbidden | match (notification_rule|purge|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | req.py sa POST /v2/notifications/rules/delete '{"id":"<id>"}' |
| notification_center | notification_rule | search | `search_notification_rules` | global/permission | cli:notification rule search / rest:POST .../rules/search | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | req.py sa POST /v2/notifications/rules/search |
| notification_center | notification_rule | update | `update_notification_rule` | single_entity/permission | rest:PATCH /v2/notifications/rules/{id} | ok | 403 backendai_generic_forbidden | match (notification_rule|update|single_entity) | Q1 ok, Q2 ok, Q3 match, Q4 n/a, Q5 n/a | req.py sa PATCH /v2/notifications/rules/<id> '{"description":"x"}' |
| notification_center | notification_rule | update | `validate_notification_rule` | single_entity/permission | rest:POST /v2/notifications/rules/validate | 400 without a full event payload; 500 once delivery is attempted | 403 backendai_generic_forbidden | row written (mutation, status=error) | Q1 ok, Q2 ok, Q3 row written (entity_type not individually captured), Q4 n/a, Q5 n/a — caller must hand-build the internal event schema, then hits F5 | req.py sa POST /v2/notifications/rules/validate '{"id":"<id>","notification_data":{"session_id":...,"session_type":...,"cluster_mode":...,"status":...}}' |
| visibility | export | create | `export_audit_logs_c_s_v` | global/permission | cli:admin export audit-logs | ok (CSV stream) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — action_name carries the `_c_s_v` mangling (BA-7486 R) | ./bai admin export audit-logs |
| visibility | export | create | `export_keypairs_c_s_v` | global/permission | cli:admin export keypairs | ok (CSV stream) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — action_name carries the `_c_s_v` mangling (BA-7486 R) | ./bai admin export keypairs |
| visibility | export | create | `export_my_keypairs_c_s_v` | scope/permission | cli:my export keypairs | ok | 403 user_auth_forbidden 'This operation requires super-admin privileges.' | match (export|create|scope) | Q1 ok, Q2 FAIL — declared scope/permission but a superadmin gate fires first (F4), Q3 match, Q4 n/a, Q5 n/a | ./bai my export keypairs  (as plain user and as domain admin: 403) |
| visibility | export | create | `export_my_sessions_c_s_v` | scope/permission | cli:my export sessions | ok | 403 user_auth_forbidden 'This operation requires super-admin privileges.' | match (export|create|scope) | Q1 ok, Q2 FAIL — declared scope/permission but a superadmin gate fires first (F4), Q3 match, Q4 n/a, Q5 n/a | ./bai my export sessions  (as plain user and as domain admin: 403) |
| visibility | export | create | `export_projects_c_s_v` | global/permission | cli:admin export projects | ok (CSV stream) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — action_name carries the `_c_s_v` mangling (BA-7486 R) | ./bai admin export projects |
| visibility | export | create | `export_sessions_by_project_c_s_v` | scope/permission | cli:admin export sessions-by-project | ok | 403 user_auth_forbidden 'This operation requires super-admin privileges.' | match (export|create|scope) | Q1 ok, Q2 FAIL — declared scope/permission but a superadmin gate fires first (F4), Q3 match, Q4 n/a, Q5 n/a | ./bai admin export sessions-by-project <project>  (as plain user and as domain admin: 403) |
| visibility | export | create | `export_sessions_c_s_v` | global/permission | cli:admin export sessions | ok (CSV stream) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — action_name carries the `_c_s_v` mangling (BA-7486 R) | ./bai admin export sessions |
| visibility | export | create | `export_users_by_domain_c_s_v` | scope/permission | cli:admin export users-by-domain | ok | 403 user_auth_forbidden 'This operation requires super-admin privileges.' | match (export|create|scope) | Q1 ok, Q2 FAIL — declared scope/permission but a superadmin gate fires first (F4), Q3 match, Q4 n/a, Q5 n/a | ./bai admin export users-by-domain default  (as plain user and as domain admin: 403) |
| visibility | export | create | `export_users_c_s_v` | global/permission | cli:admin export users | ok (CSV stream) | 403 backendai_generic_forbidden | mismatch: entity_type=global (A's F10) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a — action_name carries the `_c_s_v` mangling (BA-7486 R) | ./bai admin export users |
| visibility | export | get | `get_report` | global/permission | cli:admin export get-report | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a — but every export handler calls it first, which is the cause of F4 | ./bai admin export get-report <key> |
| visibility | export | search | `list_reports` | global/permission | cli:admin export list-reports | ok | 403 backendai_generic_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 n/a, Q5 n/a | ./bai admin export list-reports |
| visibility | audit_log | search | `scoped_search_audit_logs` | bulk/permission | gql:scopedAuditLogsV2 | GraphQL error: Schema validation failed. (Input should be a valid string) | same error | n/a | Q1 FAIL — same client_ip defect blocks the non-admin scoped surface too (F1), Q2 unobservable, Q3 n/a, Q4 n/a, Q5 n/a | ./bai gql --v2 'query($u:UUID!){ scopedAuditLogsV2(scope:{triggeredUser:[{value:$u}]}, first:2){ count } }' |
| visibility | audit_log | search | `search_audit_logs` | global/permission | cli:audit-log search / rest:POST /v2/audit-logs/search / gql:adminAuditLogsV2 | 500 backendai_generic_internal-error | 403 backendai_generic_forbidden | n/a | Q1 FAIL — unusable on every route (F1/known F1), Q2 unobservable, Q3 n/a, Q4 n/a, Q5 n/a | ./bai audit-log search --limit 2 ; ./bai gql --v2 '{ adminAuditLogsV2(first:2){ count } }' |
| label | label | lookup | `lookup_bulk_entity_label_owner` | lookup/permission | none | not exercised | not exercised | n/a | Q1 unreachable — confirms BA-7486 `W` (field_group() registers it but no bulk field operation is wired) | BA-7486 01-wiring.md:355 |
| label | label | lookup | `lookup_entity_label_owner` | lookup/permission | internal lookup via entity-label purge | 404 database_access_not-found | 404 (same, before the permission check) | match (entity_type=global, lookup_kind=entity_label_id) | Q1 ok (indirect), Q2 n/a, Q3 match, Q4 FAIL — runs before the gate, which is the mechanism behind F2, Q5 n/a | ./bai entity-label purge 00000000-0000-0000-0000-0000000000ff |
| label | label | search | `search_entity_labels` | bulk/permission | cli:entity-label search | ok | 403 role_create_forbidden | no row (successful read — policy-correct) | Q1 ok, Q2 ok, Q3 ok (no row — successful read, policy-correct), Q4 ok — a missing entity is folded into the denial list, Q5 FAIL — atomic, flat list, no per-entity outcome (F3) | ./bai entity-label search --entity-type resource_group --entity-id <rg> --entity-id 00000000-0000-0000-0000-0000000000ff |
| label | label | update | `purge_entity_label` | single_entity/permission | cli:entity-label purge <label_id> | ok | 403 for an existing label id, 404 for a missing one | match | Q1 ok, Q2 ok, Q3 match, Q4 FAIL — a non-admin can enumerate label ids from the 403/404 split (F2), Q5 n/a | ./bai entity-label purge <real-label-id> vs ./bai entity-label purge 00000000-0000-0000-0000-0000000000ff (as plain user) |
| label | label | update | `upsert_entity_label` | single_entity/permission | cli:entity-label upsert | ok | 403 role_create_forbidden (UPDATE on resource_group) | match | Q1 ok, Q2 ok, Q3 match, Q4 ok — denial is identical for a real and a missing entity, Q5 n/a | ./bai entity-label upsert --entity-type resource_group --entity-id <rg> --key ba7489c-probe --value v1 |
