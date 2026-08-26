# BA-7489 runtime exercise — Identity & Access

Every wired v2 action in the `organization`, `rbac` and `resource_policy` concerns, driven against the
running local manager and scored against the five questions. **Findings only — nothing was fixed.**

| | |
|---|---|
| Jira | BA-7489 |
| Slice | Identity & Access — `organization` (99), `rbac` (19), `resource_policy` (20) = 138 actions |
| Branch | `doc/BA-7486-v2-action-wiring-audit` (base `05e005d18b`) |
| Target | manager direct API `http://127.0.0.1:8091`, API-mode HMAC credentials |
| Entity prefix | `ba7489a-` |
| Run date | 2026-08-25 |
| Re-verified | after the lead's manager restart on 2026-08-25; F1, F4, F5, F6, F7, F8, F9 and F12 all reproduce identically |

## Conclusion

The declared gate is not the gate the request meets on 54 of the 138 actions. The gap runs in both
directions and the two directions are the two severe findings:

- **Under-gated.** `search_users_by_project` and `get_user` hand every member of a project the full user
  record of every other member — email, role, security posture and `main_access_key`, the superadmin's
  included. The RBAC grant behind this comes from `create_user`, which auto-grants every new account the
  member role of the `default` and `model-store` projects.
- **Over-gated.** 37 of the 54 are actions whose declared `permission` gate is pre-empted by route
  middleware, and 17 more are RBAC grants too narrow for the operation. A user cannot read their own
  keypair, their own resource policy, their own projects, or update their own record.

Both directions share one cause: the route middleware and the action gate are decided independently, and
nothing reconciles them.

The over-gating is not merely inconvenient. An ordinary user holds no permission on entities at their own
user scope, and that single gap makes three features unusable end to end: a user cannot read their own
resource policy (F6), list their own projects (F5), or see, accept or reject an invitation addressed to
them (F16). `accept_entity_invitation` and `reject_entity_invitation` cannot be completed by **any**
principal — the invitee is denied by RBAC, and the superadmin who bypasses RBAC is by construction not the
invitee the repository matches on.

Three further systemic defects cut across the slice:

| | |
|---|---|
| Every `global`-kind action writes `entity_type = 'global'` | `actions/v2/global_scope/monitor/audit_log.py:73` passes `GLOBAL_ENTITY_TYPE` instead of `action.entity_type()`, so the audit row never names what the catalog declares. 33 global-kind actions in this slice; the catalog declares `auth`, `user`, `domain`, `role_preset` or a policy type for every one of them. |
| Every RBAC denial reports `role_create_forbidden` | `errors/permission.py:93` hardcodes `ErrorDomain.ROLE` + `ErrorOperation.CREATE`, whatever the entity and operation were. |
| A route-middleware denial leaves no audit row | The middleware rejects before the action runs, so 57 `permission`-gated actions record nothing on a denial. |

## How to read the Q columns

| | |
|---|---|
| Q1 | Is the action reachable from any client at all, and by which route? |
| Q2 | Is the gate the wiring declares the gate the request actually meets — admin AND non-admin? |
| Q3 | Does the audit row carry the entity_type / operation / action_name the catalog predicts? |
| Q4 | Do a lookup miss and a permission denial come back indistinguishable where no-leakage requires it? |
| Q5 | Does a partial bulk run answer one item per named entity, in order, with denials and misses told apart? |

`no row (successful read)` in the audit column is **not** a defect. The rule, from
`actions/audit_policy.py` and confirmed against the table:

| run | row written? |
|---|---|
| any mutation — `success`, `denied` or `error` | always |
| a read that failed or was denied | always |
| a successful read whose operation is opted in | yes; no read operation is opted in here |
| a successful read otherwise | no |
| anything stopped by route middleware before the processor | **never** — see F12 |

The last line is not part of `AuditLogPolicy` at all: the policy runs inside the action processor, and a
route-middleware rejection never reaches it. That is why superadmin-gate denials leave no trace.

### The audit surface, measured

The read path is live: a freshly run action's row is queryable within a second. Lifetime state at the end
of this run was 814 rows across 262 distinct `action_name` values.

Two forms of `action_name` coexist. The legacy `entity:operation` form comes from `LegacyAuditLogCreator`
and writes `action_kind='unknown'`; the v2 form writes the action's own `action_name()`.

| form | rows | distinct names | last written |
|---|---:|---:|---|
| legacy `entity:operation` | 171 | 5 | 2026-08-25 (only `role:assignment:delete`) |
| v2 `action_name` | 643 | 257 | current |

The five legacy names are `agent:update`, `session:create`, `session:delete`, `auth:create` and
`role:assignment:delete`. Of these only `role:assignment:delete` is still being written — by `revoke_role`,
recorded in F15. The other four are stale: `auth:create` has exactly two rows, both from 2026-08-20
12:55, five days before this run.

**Q3 for the `auth` entity type specifically.** `auth` is the one entity in this slice whose actions leave a
row on the success path, so it is worth stating plainly what the row does and does not get right. The
`action_name` is correct and modern — every `authorize` run writes `action_name='authorize'`,
`action_kind='global'`, not the legacy `auth:create`. What is wrong is the `entity_type`: all seven `auth`
actions record `global` where the catalog declares `auth`. That is F10, and it is the only Q3 defect on
this entity type.

```bash
POST /auth/authorize {"type":"keypair","domain":"default","username":"ba7489a-probe@lablup.com","password":"..."}
```
```sql
select action_name, entity_type, action_kind from audit_logs order by created_at desc limit 1;
-- authorize | global | global
select action_name, count(*), max(created_at) from audit_logs where action_name like '%:%' group by 1;
-- auth:create | 2 | 2026-08-20 12:55:48   ← stale, predates the v2 auth wiring
```

## Coverage

| | count |
|---|---:|
| Actions in the slice | 138 |
| Exercised against the live manager | 129 |
| Confirmed unreachable — no caller anywhere | 9 |

Every action with a caller was driven on both the admin and the non-admin path. The three `global_*_users`
bulk mutations were driven through `./bai gql --v2`; the six `entity_invitation` actions were driven on
both the denial and the success path after the `f4b1c9d27a08` migration was applied mid-run.

The 9 unreachable actions are `lookup_login_history_owner`, `lookup_bulk_error_log_owner`,
`lookup_bulk_keypair_owner`, `lookup_bulk_login_history_owner`, `lookup_bulk_login_session_owner`,
`lookup_user_by_access_key`, `lookup_role_permission_preset_owner`, `purge_role_preset`, and
`global_search_error_logs`. The first eight confirm the BA-7486 static `W` verdicts. The ninth is new:
`GET /logs/error` always runs the scoped variant, so the global one has no route that selects it.

Verdicts across the 138 rows:

| verdict | count |
|---|---:|
| Q1 mismatch — not reachable from any client | 9 |
| Q2 mismatch — declared gate is not the gate met | 54 |
| Q3 mismatch — audit row disagrees with the catalog | 18 |
| Q4 mismatch — a miss and a denial are distinguishable | 12 |
| Q5 mismatch — a partial bulk does not answer per named entity | 3 of 7 measured |

Q5 is now a measured verdict rather than an assumed one. The seven partial-bulk surfaces in the slice are
`global_create_users`, `global_update_users`, `global_purge_users`, `assign_users_to_project`,
`unassign_users_from_project`, the `role_preset` bulk trio, and `bulk_remove_role_permission_presets`.

The `entity_invitations` table was absent for the first part of this run: the DB sat at `8c41a7e5b6d2`
while the table is created by the immediately following migration `f4b1c9d27a08`. That was a local
environment gap, not a product defect, and it exposed F8. The migration was applied mid-run, so the six
invitation actions were driven on both the denial and the success path; F16 records what the success
path shows. F8 stands as written — the trigger condition is gone from this deployment, the code path is
unchanged.

## Environment

| principal | email | role |
|---|---|---|
| `sa` | admin@lablup.com | superadmin |
| `da` | domain-admin@lablup.com | domain admin of `default` |
| `u1` | user@lablup.com | plain user, member of `default` and `model-store` |
| `mon` | monitor@lablup.com | monitor |
| `probe` | ba7489a-probe@lablup.com | created for this run, `default` domain, no project |
| `victim` | ba7489a-victim@lablup.com | created for this run, `ba7489a-dom` domain |
| `doom` | ba7489a-doomed@lablup.com | created for this run, signed out at the end |

Entities left behind, all prefixed: domains `ba7489a-dom` and `ba7489a-dom-v1`, project `ba7489a-proj`,
users `ba7489a-probe`, `ba7489a-victim`, `ba7489a-doomed` (inactive), `ba7489a-signup`.
No fixture account, domain, project or resource group was mutated. Nothing was written to Postgres
directly; every state change went through the API.

## Per-action results

| concern | entity_type | operation | action_name | declared kind/gate | route exercised | admin result | non-admin result | audit row match | Q verdicts | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| organization | auth | create | authorize | global / anonymous | rest:POST /auth/authorize | ok | ok (anonymous by design) | mismatch: entity_type=global, catalog says auth | Q1 ok, Q2 ok, Q3 mismatch, Q4 **mismatch**, Q5 n/a | `req.py sa POST /auth/authorize '{"type":"keypair","domain":"default","username":"user@lablup.com","password":"wrong"}' --anon` |
| organization | auth | update | update_password_no_auth | global / anonymous | rest:POST /auth/update-password-no-auth | 400 backendai_generic_bad-request (`Unsupported function.`) | 400 same | mismatch: entity_type=global, catalog says auth | Q1 ok (disabled by config), Q2 ok, Q3 mismatch, Q4 ok, Q5 n/a | `POST /auth/update-password-no-auth {domain,username,current_password,new_password}` — identical body+traceback for existing and unknown user |
| organization | auth | get | public_get_role | global / public | rest:GET /auth/role | ok | ok | no row (successful read, not opted in) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /auth/role` → u1 `{global_role:user,domain_role:user}`; `?group=<model-store>` → `group_role:user` |
| organization | auth | update | global_unblock_user | global / permission | rest:POST /v2/login-sessions/unblock-user | ok (200 even for an unknown username) | 403 backendai_generic_forbidden (route middleware) | mismatch: entity_type=global; success row written for a no-op | Q1 ok, Q2 ok (a `global` action's declared gate is SUPERADMIN, which the route enforces), Q3 mismatch, Q4 ok, Q5 n/a | `POST /v2/login-sessions/unblock-user {"username":"ba7489a-nosuch@lablup.com"}` → 200 `{success:true}` |
| organization | auth | delete | global_revoke_login_session | global / permission | rest:POST /v2/login-sessions/revoke | 404 auth_read_not-found (miss) | 403 backendai_generic_forbidden (route middleware) | match (entity_type=global as the global monitor always writes) | Q1 ok, Q2 ok (declared gate is SUPERADMIN), Q3 mismatch (entity_type), Q4 ok, Q5 n/a | `POST /v2/login-sessions/revoke {"session_id":"00000000-0000-0000-0000-0000000000ff"}` |
| organization | auth | get | public_resolve_access_key_scope | global / public | internal: rest/session/handler.py:599, rest/service/handler.py:647, rest/userconfig/handler.py:74 | ok (no direct route) | ok | no row (successful read) | Q1 ok (internal caller only), Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | no client-facing route; runs inside v1 session/service/user-config handlers |
| organization | auth | get | public_resolve_user_scope | global / public | internal: rest/vfolder/handler.py:326 | ok (no direct route) | ok | no row (successful read) | Q1 ok (internal caller only), Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | no client-facing route; runs inside the v1 vfolder handler |
| organization | domain | create | global_create_domain | global / permission | rest:POST /admin/domains (v1) | 201 ok | 403 (route middleware) | mismatch: entity_type=global | Q1 ok (v1 route only), Q2 ok (declared gate is SUPERADMIN), Q3 mismatch, Q4 n/a, Q5 n/a | `POST /admin/domains {"name":"ba7489a-dom-v1",...}` → audit `global_create_domain` + a side-effect `create_project` |
| organization | domain | create | global_create_domain_node | global / permission | rest:POST /v2/domains | 201 ok | 403 (route middleware) | mismatch: entity_type=global | Q1 ok, Q2 ok (declared gate is SUPERADMIN), Q3 mismatch, Q4 n/a, Q5 n/a | `POST /v2/domains {"name":"ba7489a-dom"}` → audit action_name is `global_create_domain_node`, not `global_create_domain` |
| organization | domain | get | get_domain | single_entity / public | rest:GET /v2/domains/{name} | ok | ok (any authenticated user reads any domain) | no row on hit; `lookup_domain` error row on miss | Q1 ok, Q2 ok, Q3 n/a, Q4 **mismatch** (404 on miss vs 200 on hit for any user) | `GET /v2/domains/ba7489a-dom` as u1 → 200; `GET /v2/domains/ba7489a-nodomain` → 404 database_access_not-found |
| organization | domain | lookup | lookup_domain | lookup / public | internal: fires ahead of every `/v2/domains/{name}` and `/v2/users/domains/{name}/...` route | 404 on miss | 404 on miss | match (`lookup_kind=domain_name`, `lookup_key=name=<x>`) | Q1 ok, Q2 ok, Q3 ok, Q4 **mismatch** (miss is 404 for everyone, before any permission check) | `GET /v2/domains/ba7489a-nodomain` → audit `lookup_domain\|domain\|lookup\|lookup\|error` |
| organization | domain | search | global_search_domains | global / permission | rest:POST /v2/domains/search | 200 ok | 403 (u1 and domain-admin both) | no row (successful read); no row on denial (middleware) | Q1 ok, Q2 ok (declared gate is SUPERADMIN), Q3 **no row**, Q4 ok, Q5 n/a | `POST /v2/domains/search` as `da` → 403 backendai_generic_forbidden, no audit row |
| organization | domain | search | search_rg_domains | global / public | rest:GET /v2/resource-groups/{name}/allowed-domains | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 **mismatch** (declared public, route is superadmin_required), Q3 n/a, Q4 ok, Q5 n/a | `GET /v2/resource-groups/default/allowed-domains` → sa 200 `{items:[default]}`, u1 403 |
| organization | domain | update | update_domain | single_entity / permission | rest:PATCH /admin/domains/{name} (v1) | 200 ok | 403 (route middleware) | match | Q1 ok (v1 route only), Q2 mismatch, Q3 ok, Q4 n/a, Q5 n/a | `PATCH /admin/domains/ba7489a-dom {"description":"..."}` → audit `update_domain` |
| organization | domain | update | update_domain_node | single_entity / permission | rest:PATCH /v2/domains/{name} | 200 ok | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok (404 for both on miss), Q5 n/a | `PATCH /v2/domains/ba7489a-dom` → audit `update_domain_node` |
| organization | domain | delete | delete_domain | single_entity / permission | rest:POST /v2/domains/delete | 200 ok | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/domains/delete {"name":"ba7489a-dom-v1"}` → 200; miss → 404 via `lookup_domain` |
| organization | domain | restore | restore_domain | single_entity / permission | rest:POST /v2/domains/restore | 200 ok | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/domains/restore {"name":"ba7489a-dom-v1"}` → 200 |
| organization | domain | purge | purge_domain | single_entity / permission | rest:POST /admin/domains/purge (v1) | 409 domain_purge_conflict | 403 (route middleware) | match (status=error) | Q1 ok (v1 route; `/v2/domains/purge` never reaches the action), Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /admin/domains/purge {"name":"ba7489a-dom-v1"}` → 409; `POST /v2/domains/purge` on a miss stops at `lookup_domain` |
| organization | domain | update | create_domain_dotfile | single_entity / permission | rest:POST /domain-config/dotfiles | 200 ok | 403 role_create_forbidden (RBAC; domain-admin denied on its OWN domain) | match (operation=update as declared) | Q1 ok, Q2 **mismatch** (a domain admin lacks UPDATE on its own domain), Q3 ok, Q4 ok, Q5 n/a | `POST /domain-config/dotfiles {"domain":"default",...}` as `da` → 403 lacks `<Permission.UPDATE: 2>` on domain b9e676dc |
| organization | domain | update | update_domain_dotfile | single_entity / permission | rest:PATCH /domain-config/dotfiles | 200 ok | 403 role_create_forbidden | match | Q1 ok, Q2 mismatch (as above), Q3 ok, Q4 ok, Q5 n/a | `PATCH /domain-config/dotfiles {"domain":"ba7489a-dom","path":"/home/work/.ba7489a",...}` |
| organization | domain | update | delete_domain_dotfile | single_entity / permission | rest:DELETE /domain-config/dotfiles | 200 ok | 403 role_create_forbidden | match | Q1 ok, Q2 mismatch (as above), Q3 ok, Q4 ok, Q5 n/a | `DELETE /domain-config/dotfiles?domain=ba7489a-dom&path=/home/work/.ba7489a` |
| organization | project | create | create_project | scope / permission | rest:POST /v2/projects | 201 ok (requires `resource_policy`, undocumented as required) | 403 (route middleware) | match | Q1 ok, Q2 **mismatch** (scope gate never runs — superadmin_required), Q3 ok, Q4 n/a, Q5 n/a | `POST /v2/projects {"name":"ba7489a-proj","domain_name":"default","resource_policy":"default"}`; omitting resource_policy → 400 leaking the failing DB row |
| organization | project | get | get_project | single_entity / permission | rest:GET /v2/projects/{id} | 404 database_access_not-found on miss | 403 role_create_forbidden — **including for projects the caller belongs to** | match (denied / error rows both written) | Q1 ok, Q2 **mismatch** (members denied READ), Q3 ok, Q4 ok (miss and denial identical for non-admin), Q5 n/a | `GET /v2/projects/2de2b969-...` as u1 (a member) → 403 lacks `<Permission.READ: 1>` |
| organization | project | lookup | lookup_project | lookup / public | internal: rest/resource_group/handler.py:70, cluster_template/handler.py:88, session_template/handler.py:89 | ok | ok | no row (successful read) | Q1 ok (internal caller only), Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | no client-facing route of its own |
| organization | project | update | update_project | single_entity / permission | rest:PATCH /v2/projects/{id} | 200 ok; **500 + `status=success` audit row on a missing id** | 403 (route middleware) | **mismatch: status=success recorded for a run that returned 500** | Q1 ok, Q2 mismatch, Q3 **mismatch**, Q4 n/a, Q5 n/a | `PATCH /v2/projects/00000000-0000-0000-0000-0000000000ff {"description":"x"}` → 500 `UnreachableError: modify_group must return data`, audit `update_project\|...\|success` |
| organization | project | delete | delete_project | single_entity / permission | rest:POST /v2/projects/delete (body key `group_id`) | 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/projects/delete {"group_id":"00000000-0000-0000-0000-0000000000ff"}` → 404 database_access_not-found |
| organization | project | restore | restore_project | single_entity / permission | rest:POST /v2/projects/restore (body key `group_id`) | 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/projects/restore {"group_id":"00000000-0000-0000-0000-0000000000ff"}` → 404 database_access_not-found |
| organization | project | purge | purge_project | single_entity / permission | rest:POST /v2/projects/purge (body key `group_id`) | 404 group_read_not-found on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/projects/purge {"group_id":"00000000-0000-0000-0000-0000000000ff"}` → 404 `group_read_not-found` (delete/restore return `database_access_not-found` for the same input) |
| organization | project | search | global_search_projects | global / permission | rest:POST /v2/projects/search | 200 ok | 403 (route middleware) | no row (successful read); no row on denial | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/projects/search {"pagination":{"limit":2}}` |
| organization | project | search | search_projects_by_domain | scope / permission | gql:domainProjectsV2 (also DomainNode.projects) | 200 ok | 403 role_create_forbidden | match (`project\|search\|scope\|denied`) | Q1 ok (GraphQL only — no REST route), Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `./bai gql --v2 'query { domainProjectsV2(scope:{domainName:"default"}, limit:2) { count } }'` |
| organization | project | search | search_projects_by_user | scope / permission | gql:UserV2.projects (e.g. myUserV2 { projects }) | 200 ok | 403 role_create_forbidden — **a user cannot list their own projects** | match (`project\|search\|scope\|denied`) | Q1 ok (GraphQL only), Q2 **mismatch**, Q3 ok, Q4 n/a, Q5 n/a | `./bai gql --v2 'query { myUserV2 { projects(limit:3) { count } } }'` as u1 → lacks READ on project at its own user scope |
| organization | project | search | global_search_project_usage_per_month | global / permission | rest:GET /resource/usage/month | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `GET /resource/usage/month?group_ids=2de2b969-...&month=202608` |
| organization | project | search | global_search_project_usage_per_period | global / permission | rest:GET /resource/usage/period | 200 ok (returns every user's email + access key) | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `GET /resource/usage/period?group_id=2de2b969-...&start_date=20260801&end_date=20260825` |
| organization | project | update | assign_users_to_project | single_entity / permission | rest:POST /v2/projects/{id}/users/assign | 200 ok — **grants the caller-named `role_id` regardless of the project in the path, and writes no membership row** | 403 role_create_forbidden (RBAC) | match (one row per call, not per user) | Q1 ok, Q2 ok at the route, **role_id unvalidated against the path project**, Q3 ok, Q4 n/a, Q5 **mismatch** (a nonexistent user id is silently dropped; a duplicate aborts the whole call with 409) | `POST /v2/projects/2de2b969-.../users/assign {"user_ids":[<u>],"role_id":"254fef91-...(model-store member)"}` → 200 and the user gains `role_project_8e32dd28_member` |
| organization | project | update | unassign_users_from_project | single_entity / permission | rest:POST /v2/projects/{id}/users/unassign | 200 ok with a per-user `failed` list | 403 role_create_forbidden (RBAC) | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 partial — every named user is answered and `User does not exist.` is told apart from `User is not assigned to this project.`, but **the answers are not in input order** | `POST /v2/projects/54c7cf75-.../users/unassign {"user_ids":[doomed,00000000-0000-0000-0000-0000000000ff,probe]}` → failed list ordered [00000000-0000-0000-0000-0000000000ff, probe, doomed] |
| organization | project | update | create_project_dotfile | single_entity / permission | rest:POST /group-config/dotfiles | 200 ok | 403 backendai_generic_forbidden (admin_required) | match (operation=update as declared) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /group-config/dotfiles {"group":"54c7cf75-...","path":"/home/work/.ba7489a-p",...}` |
| organization | project | update | update_project_dotfile | single_entity / permission | rest:PATCH /group-config/dotfiles | 200 ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `PATCH /group-config/dotfiles {"group":"54c7cf75-...",...}` |
| organization | project | update | delete_project_dotfile | single_entity / permission | rest:DELETE /group-config/dotfiles | 200 ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /group-config/dotfiles?group=54c7cf75-...&path=/home/work/.ba7489a-p` |
| organization | user | create | create_user | scope / permission | rest:POST /v2/users | 201 ok | 403 (route middleware) | match (`user\|create\|scope\|success`) | Q1 ok, Q2 mismatch (scope gate never runs), Q3 ok, Q4 n/a, Q5 n/a | `POST /v2/users {"email":"ba7489a-victim@lablup.com","domain_name":"ba7489a-dom",...}` → the new user is auto-granted `role_project_2de2b969_member` and `role_project_8e32dd28_member` without any project membership |
| organization | user | create | global_create_users | global / permission | gql:adminBulkCreateUsersV2 (and adminBulkCreateUsersWithKeypairV2) | 200 ok with `createdUsers` + `failed`; **one item naming a nonexistent domain aborts the whole batch** | 403 `Admin exclusive access`, surfaced as `backendai_generic_internal-error`; no audit row | mismatch: entity_type=global; one row per batch, `status=success` with 2 of 4 items failed | Q1 ok, Q2 ok (superadmin enforced by `check_admin_only`), Q3 mismatch, Q4 n/a, Q5 **mismatch** | `./bai gql --v2 'mutation { adminBulkCreateUsersV2(input:{users:[…4 items…]}) { createdUsers { id } failed { index username email message } } }'` — with a bad `domainName` → `data: null`, one top-level `database_access_not-found`, nothing created |
| organization | user | create | signup | global / anonymous | rest:POST /auth/signup | 201 ok — an unauthenticated caller creates an active user with a working keypair | 201 ok (anonymous by design) | mismatch: entity_type=global, catalog says user | Q1 ok, Q2 ok, Q3 mismatch, Q4 **mismatch** (`user_create_already-exists` vs `user_create_bad-request` vs 201 enumerates users and domains), Q5 n/a | `POST /auth/signup {"domain":"default","email":"user@lablup.com",...}` → 400 `Email already exists` |
| organization | user | delete | delete_user | single_entity / permission | rest:POST /v2/users/delete | 200 ok | 403 backendai_generic_forbidden (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok (identical 403 for self/other/missing), Q5 n/a | `POST /v2/users/delete {"user_id":"1c6a1ab4-..."}` |
| organization | user | delete | signout | single_entity / permission | rest:POST /auth/signout | 200 ok (self only) | 200 ok for self; 403 `Not the account owner` for another email; 401 on a wrong password | match (success and error rows both written) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /auth/signout {"email":"user2@lablup.com","password":"..."}` as the doomed user → 403 `Not the account owner` |
| organization | user | get | get_user | single_entity / permission | rest:GET /v2/users/{id} (auth_required) and GET /admin/users/{id} (superadmin_required) | 200 ok; 404 user_read_not-found on miss | **200 ok for any user in the caller's domain** — full record incl. `main_access_key`; 403 for cross-domain and for a missing id | match on denial/error; no row on a successful read | Q1 ok, Q2 **mismatch** (two routes, two gates; the v2 route leaks peers), Q3 ok, Q4 ok for non-admin (miss and denial both 403), Q5 n/a | `GET /v2/users/f38dea23-...` as u1 → 200 with admin@'s `main_access_key` |
| organization | user | get | get_user_month_stats | single_entity / permission | rest:GET /resource/stats/user/month | 200 ok | 200 ok (own stats) | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /resource/stats/user/month` |
| organization | user | get | global_get_user_month_stats | global / permission | rest:GET /resource/stats/admin/month | 200 ok | 403 (route middleware) | no row (successful read); no row on denial | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `GET /resource/stats/admin/month` |
| organization | user | get | get_bootstrap_script | single_entity / permission | rest:GET /user-config/bootstrap-script | 200 ok | 200 ok (own script) | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /user-config/bootstrap-script` |
| organization | user | get | get_ssh_keypair | single_entity / permission | rest:GET /auth/ssh-keypair | 200 ok | 200 ok (own key) | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /auth/ssh-keypair` |
| organization | user | get | admin_get_ssh_keypair | single_entity / permission | rest:GET /v2/keypairs/{access_key}/ssh | 200 ok; 404 on miss | 403 backendai_generic_forbidden (route middleware) | no row on hit; `lookup_keypair_owner_by_access_key` error row on miss | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok (non-admin sees one 403 for both cases), Q5 n/a | `GET /v2/keypairs/AKIANOSUCHKEYBA7489A/ssh` → 404 `No field row matches the given key` |
| organization | user | lookup | lookup_user | lookup / public | internal: gql_legacy/keypair.py:542 | ok | ok | no row (successful read) | Q1 ok (legacy GraphQL keypair resolver only), Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | no REST route; resolves a keypair's owner by email |
| organization | user | lookup | lookup_keypair | lookup / permission | internal: fires ahead of `GET/DELETE /v2/keypairs/{access_key}` | 404 on miss | not reached (route denies first) | match (`lookup_kind=keypair_access_key`) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/keypairs/AKIANOSUCHKEYBA7489A` → audit `lookup_keypair\|user\|lookup\|lookup\|error` |
| organization | user | lookup | lookup_keypair_owner | lookup / permission | internal: companion of the keypair single-entity ops (services/user/actions/keypair_ops.py:75) | ok | not reached | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | runs inside `get_keypair` / `update_keypair` / `purge_keypair` |
| organization | user | lookup | lookup_keypair_owner_by_access_key | lookup / permission | internal: fires ahead of the `/v2/keypairs/{ak}/ssh` routes | 404 on miss | not reached | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/keypairs/AKIANOSUCHKEYBA7489A/ssh` → audit `lookup_keypair_owner_by_access_key\|user\|lookup\|lookup\|error` |
| organization | user | lookup | lookup_error_log_owner | lookup / permission | internal: fires ahead of `POST /logs/error/{log_id}/clear` | 404 on miss | 404 on miss | match (`lookup_kind=error_log_id`) | Q1 ok, Q2 ok, Q3 ok, Q4 **mismatch** (a non-owner learns a log id does not exist before any permission check) | `POST /logs/error/00000000-0000-0000-0000-0000000000ff/clear` → audit `lookup_error_log_owner\|user\|lookup\|lookup\|error` |
| organization | user | lookup | lookup_login_session_owner | lookup / permission | internal: fires ahead of `POST /v2/login-sessions/my/revoke` | 404 on miss | 404 on miss | match (`lookup_kind=login_session_id`) | Q1 ok, Q2 ok, Q3 ok, Q4 **mismatch** (same shape as above) | `POST /v2/login-sessions/my/revoke {"session_id":"00000000-0000-0000-0000-0000000000ff"}` → audit `lookup_login_session_owner\|user\|lookup\|lookup\|error` |
| organization | user | lookup | lookup_login_history_owner | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch** (registered but no single field op is wired), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirmed by the BA-7486 static sweep; no caller found and no audit row produced by any login-history route |
| organization | user | lookup | lookup_bulk_error_log_owner | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch** (bulk field ops not wired for this domain), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no caller; matches the BA-7486 `W` verdict |
| organization | user | lookup | lookup_bulk_keypair_owner | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no caller; matches the BA-7486 `W` verdict |
| organization | user | lookup | lookup_bulk_login_history_owner | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no caller; matches the BA-7486 `W` verdict |
| organization | user | lookup | lookup_bulk_login_session_owner | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no caller; matches the BA-7486 `W` verdict |
| organization | user | lookup | lookup_user_by_access_key | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch** (wired into the processor, called by nothing), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | `ResolveUserIDByAccessKeyAction` appears only in services/auth/processors.py:205 |
| organization | user | purge | purge_user | single_entity / permission | rest:POST /admin/users/purge (v1) | 404 user_read_not-found on miss | 403 (route middleware) | match | Q1 ok (v1 route only), Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /admin/users/purge {"user_id":"00000000-0000-0000-0000-0000000000ff"}` → audit `purge_user\|user\|purge\|single_entity\|error` |
| organization | user | purge | global_purge_users | global / permission | gql:adminBulkPurgeUsersV2 | 200 ok; 4 items in → `purgedCount: 2` + 2 `failed` | 403 `Admin exclusive access` as `backendai_generic_internal-error`; no audit row | mismatch: entity_type=global; one row per batch, `status=success` with 2 of 4 items failed | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 **mismatch** (successes come back only as a count, so the caller cannot tell which users were purged) | `./bai gql --v2 'mutation { adminBulkPurgeUsersV2(input:{userIds:["<b1>","<b3>","00000000-0000-0000-0000-0000000000ff","<b1>"]}) { purgedCount failed { userId message } } }'` |
| organization | user | restore | restore_user | single_entity / permission | rest:POST /v2/users/restore | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/users/restore {"user_id":"1c6a1ab4-..."}` → 200; miss → 404 `user_read_not-found` |
| organization | user | search | global_search_users | global / permission | rest:POST /v2/users/search | 200 ok | 403 (route middleware) | no row (successful read); no row on denial | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/users/search {"pagination":{"limit":2}}` |
| organization | user | search | search_users_by_domain | scope / permission | rest:POST /v2/users/domains/{domain_name}/search | 200 ok | 403 role_create_forbidden — **denied on the caller's own domain** | match (`user\|search\|scope\|denied`) | Q1 ok, Q2 **mismatch** (denies the listing that `get_user` hands out row by row), Q3 ok, Q4 **mismatch** (an unknown domain gives 404 `database_access_not-found` from `lookup_domain` while a known one gives 403) | `POST /v2/users/domains/default/search` as u1 → 403; `.../domains/ba7489a-nodomain/search` → 404 |
| organization | user | search | search_users_by_project | scope / permission | rest:POST /v2/users/projects/{project_id}/search | 200 ok | **200 ok on the `default` project** — returns every member's email, role and `main_access_key`, including the superadmin's | match on denial; no row on a successful read | Q1 ok, Q2 **mismatch**, Q3 ok, Q4 ok (a nonexistent project id and an unauthorized one both give 403), Q5 n/a | `POST /v2/users/projects/2de2b969-1d04-48a6-af16-0bc8adb3c831/search {"pagination":{"limit":2}}` as u1 → 200 containing `AKIAIOSFODNN7EXAMPLE` |
| organization | user | search | search_users_by_role | global / permission | rest:POST /v2/users/roles/{role_id}/search | 200 ok | 403 user_auth_forbidden (`InsufficientPrivilege`, raised inside the processor) | mismatch: entity_type=global, catalog says user | Q1 ok, Q2 ok (the route is auth_required but the global processor enforces superadmin and leaves a row), Q3 mismatch, Q4 ok, Q5 n/a | `POST /v2/users/roles/00000000-0000-0000-0000-0000000000ff/search` as u1 → audit `search_users_by_role\|global\|search\|global\|denied` |
| organization | user | search | global_search_keypairs | global / permission | rest:POST /v2/keypairs/search | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/keypairs/search {"pagination":{"limit":2}}` |
| organization | user | search | search_keypairs | scope / permission | rest:POST /v2/keypairs/my/search | 200 ok | 200 ok (own keypairs only) | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `POST /v2/keypairs/my/search {"pagination":{"limit":5}}` as u1 → only `AKIANABBDUSEREXAMPLE` |
| organization | user | update | admin_create_keypair | single_entity / permission | rest:POST /v2/keypairs | 201 ok | 403 (route middleware) | match (`user\|update\|single_entity\|success`, entity_id = the target user) | Q1 ok, Q2 mismatch, Q3 ok, Q4 n/a, Q5 n/a | `POST /v2/keypairs {"user_id":"f2355877-...","is_active":true,"resource_policy":"default","rate_limit":1000}` |
| organization | user | update | admin_register_ssh_keypair | single_entity / permission | rest:POST /v2/keypairs/ssh | 200 ok | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 n/a, Q5 n/a | `POST /v2/keypairs/ssh {"access_key":"AKIA4M67TO54V7P2EPP6","ssh_public_key":"...","ssh_private_key":"x"}` |
| organization | user | update | admin_delete_ssh_keypair | single_entity / permission | rest:DELETE /v2/keypairs/{access_key}/ssh | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/keypairs/AKIA4M67TO54V7P2EPP6/ssh` |
| organization | user | update | create_keypair_dotfile | single_entity / permission | rest:POST /user-config/dotfiles | 200 ok | 200 ok (own dotfiles) | match (operation=update as declared) | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `POST /user-config/dotfiles {"path":"/home/work/.ba7489a-kp","data":"x","permission":"644"}` |
| organization | user | update | update_keypair_dotfile | single_entity / permission | rest:PATCH /user-config/dotfiles | 200 ok | 200 ok | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `PATCH /user-config/dotfiles {"path":"/home/work/.ba7489a-kp","data":"y","permission":"600"}` |
| organization | user | update | delete_keypair_dotfile | single_entity / permission | rest:DELETE /user-config/dotfiles | 200 ok | 200 ok | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `DELETE /user-config/dotfiles?path=/home/work/.ba7489a-kp` |
| organization | user | update | generate_ssh_keypair | single_entity / permission | rest:PATCH /auth/ssh-keypair | 200 ok | 200 ok (own key) | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `PATCH /auth/ssh-keypair` → returns a fresh RSA pair |
| organization | user | update | upload_ssh_keypair | single_entity / permission | rest:POST /auth/ssh-keypair | 400 keypair_create_invalid-data-format on a malformed key | same | match (status=error) | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `POST /auth/ssh-keypair {"pubkey":"...","privkey":"..."}` |
| organization | user | update | global_update_users | global / permission | gql:adminBulkUpdateUsersV2 | 200 ok; 4 items in → 3 `updatedUsers` in input order + 1 `failed` | 403 `Admin exclusive access` as `backendai_generic_internal-error` (domain admin also denied); no audit row | mismatch: entity_type=global; one row per batch, `status=success` with 1 of 4 items failed | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 ok (`failed` carries `userId` but no `index`, so a repeated id is ambiguous) | `./bai gql --v2 'mutation { adminBulkUpdateUsersV2(input:{users:[{userId:"<b1>",input:{fullName:"…"}},{userId:"<b3>",…},{userId:"00000000-0000-0000-0000-0000000000ff",…},{userId:"<b1>",…}]}) { updatedUsers { id } failed { userId message } } }'` |
| organization | user | update | issue_keypair | single_entity / permission | rest:POST /v2/keypairs/my/issue | 201 ok | 201 ok (own keypair) | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `POST /v2/keypairs/my/issue {}` as u1 → new access key |
| organization | user | update | logout | single_entity / permission | rest:POST /auth/logout | 200 ok | **200 ok and a `success` audit row even for a session token that does not exist** | **mismatch: a success row for a revocation that never happened** | Q1 ok, Q2 ok, Q3 **mismatch**, Q4 ok, Q5 n/a | `POST /auth/logout {"session_token":"00000000000000000000000000000000"}` → 200, audit `logout\|user\|update\|single_entity\|success` |
| organization | user | update | switch_default_access_key | single_entity / permission | rest:POST /v2/keypairs/my/switch-main | 200 ok | 403 keypair_read_forbidden on another user's key | match (status=error on the denial) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/keypairs/my/switch-main {"access_key":"AKIAIOSFODNN7EXAMPLE"}` as probe → 403 `Cannot set another user's access key as the default access key.` |
| organization | user | update | update_bootstrap_script | single_entity / permission | rest:POST /user-config/bootstrap-script | 200 ok | 200 ok (own script) | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `POST /user-config/bootstrap-script {"script":"echo ba7489a"}` |
| organization | user | update | update_full_name | single_entity / permission | rest:POST /auth/update-full-name | 200 ok | 200 ok — **the required `email` field is ignored; the caller is always the target** | match (entity_id is always the caller) | Q1 ok, Q2 ok (no cross-user write), Q3 ok, Q4 **mismatch** (an unknown email returns the same 200 as the caller's own), Q5 n/a | `POST /auth/update-full-name {"email":"user2@lablup.com","full_name":"HIJACK"}` → 200 and user2's name is untouched; the caller is renamed |
| organization | user | update | update_password | single_entity / permission | rest:POST /auth/update-password | 200 ok | 401 on a wrong old password; **400 with `status=success` in the audit row when the two new passwords disagree** | **mismatch: success row for a run that returned 400 and changed nothing** | Q1 ok, Q2 ok, Q3 **mismatch**, Q4 ok, Q5 n/a | `POST /auth/update-password {"old_password":"<correct>","new_password":"A","new_password2":"B"}` → 400 `new password mismatch`, audit `update_password\|user\|update\|single_entity\|success` |
| organization | user | update | update_user | single_entity / permission | rest:PATCH /v2/users/{id} | 200 ok; 404 on miss | 403 backendai_generic_forbidden — **a user cannot update their own record on this route** | match | Q1 ok, Q2 **mismatch** (superadmin_required, so the single-entity gate never runs), Q3 ok, Q4 ok (self/other/missing all give the same 403), Q5 n/a | `PATCH /v2/users/dfa9da54-... {"full_name":"x"}` as that same user → 403 |
| organization | error_log | search | global_search_error_logs | global / permission | none — `GET /logs/error` always runs the scoped search | not exercised | not exercised | no row | Q1 **mismatch** (no route selects the global variant), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | `GET /logs/error` as sa returns only the caller's own logs |
| organization | error_log | search | search_error_logs | scope / permission | rest:GET /logs/error | 200 ok (own logs only) | 200 ok (own logs only) | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /logs/error` → u1 sees `{logs:[],count:0}` while probe sees only its own entry |
| organization | error_log | update | create_error_log | single_entity / permission | rest:POST /logs/error | 200 ok | 200 ok | match (`user\|update\|single_entity\|success`) | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `POST /logs/error {"severity":"error","source":"ba7489a","message":"BA-7489 probe"}` |
| organization | error_log | update | delete_error_log | single_entity / permission | rest:POST /logs/error/{log_id}/clear | 404 on miss | 404 on miss | `lookup_error_log_owner` error row on miss; the action itself never runs | Q1 ok, Q2 ok, Q3 ok, Q4 **mismatch** (the lookup 404s before any permission check) | `POST /logs/error/00000000-0000-0000-0000-0000000000ff/clear` → 404 `No field row matches the given id` |
| organization | keypair | get | get_default_keypairs | bulk / permission | internal: adapters/user/adapter.py:1578 and adapters/project/adapter.py:366 | ok | ok — **the bulk gate does not stop a plain user from receiving peers' `main_access_key`** | no row (successful read) | Q1 ok (internal only), Q2 **mismatch**, Q3 n/a, Q4 n/a, Q5 not exercised | runs while filling `main_access_key` in the `search_users_by_project` payload |
| organization | keypair | get | get_keypair | single_entity / permission | rest:GET /v2/keypairs/{access_key} | 200 ok; 404 on miss | 403 — **including for the caller's own access key** | no row on hit; `lookup_keypair` error row on miss | Q1 ok, Q2 **mismatch** (superadmin_required blocks the owner), Q3 ok, Q4 ok (one 403 for own/other/missing), Q5 n/a | `GET /v2/keypairs/AKIANABBDUSEREXAMPLE` as u1 (its owner) → 403 backendai_generic_forbidden |
| organization | keypair | update | purge_keypair | single_entity / permission | rest:DELETE /v2/keypairs/{access_key} | 200 ok; 404 on miss | 403 (route middleware) | match (operation=update as declared) | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/keypairs/AKIAKWY3FRWUYC4YCIUF` → audit `purge_keypair\|user\|update\|single_entity\|success` |
| organization | keypair | update | update_keypair | single_entity / permission | rest:PATCH /v2/keypairs/my (self) and PATCH /v2/keypairs (admin) | 200 ok | 200 ok on `/my`; 403 on the admin route | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `PATCH /v2/keypairs/my {"access_key":"AKIANABBDUSEREXAMPLE","is_active":true}` |
| organization | login_history | search | global_search_login_history | global / permission | rest:POST /v2/login-history/search | **500 backendai_generic_internal-error** | 403 (route middleware) | no row (the failure is a response-serialisation error after the action succeeded) | Q1 ok, Q2 ok, Q3 no row, Q4 n/a, Q5 n/a | `POST /v2/login-history/search {"pagination":{"limit":2}}` → `LoginHistoryNode.client_ip` gets an `IPv4Address` |
| organization | login_history | search | search_login_history | scope / permission | rest:POST /v2/login-history/my/search | **500** | **500** | no row | Q1 ok, Q2 not reachable, Q3 no row, Q4 n/a, Q5 n/a | `POST /v2/login-history/my/search {"pagination":{"limit":3}}` → same `client_ip` validation error |
| organization | login_session | search | global_search_login_sessions | global / permission | rest:POST /v2/login-sessions/search | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/login-sessions/search {"pagination":{"limit":2}}` |
| organization | login_session | search | search_login_sessions | scope / permission | rest:POST /v2/login-sessions/my/search | 200 ok | 200 ok (own sessions only) | no row (successful read) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `POST /v2/login-sessions/my/search {"pagination":{"limit":5}}` |
| organization | login_session | update | revoke_login_session | single_entity / permission | rest:POST /v2/login-sessions/my/revoke | 404 on miss | 404 on miss | `lookup_login_session_owner` error row; the action itself never runs on a miss | Q1 ok, Q2 ok, Q3 ok, Q4 **mismatch** (the lookup 404s before any permission check) | `POST /v2/login-sessions/my/revoke {"session_id":"00000000-0000-0000-0000-0000000000ff"}` → 404 |
| rbac | entity_invitation | create | create_entity_invitation | scope / permission | rest:POST /v2/entity-invitations · cli:`bai entity-invitation create` | 201 ok | 403 role_create_forbidden (lacks CREATE on entity_invitation at the project scope) | match (`entity_invitation\|create\|scope\|success`, entity_id set) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/entity-invitations {"target_entity_type":"project","target_entity_id":"54c7cf75-…","invitee_email":"ba7489a-probe@lablup.com","permissions":["read"]}` → 201, status `pending`. A second identical call → 409 `entity-invitation_create_conflict` |
| rbac | entity_invitation | get | get_entity_invitation | single_entity / permission | rest:GET /v2/entity-invitations/{id} · cli:`bai entity-invitation get` | 200 ok; 404 `database_access_not-found` on miss | 403 role_create_forbidden — **including for the invitee named on the invitation** | match (denied / error rows both written) | Q1 ok, Q2 **mismatch** (the invitee cannot read their own invitation), Q3 ok, Q4 ok (the invitee gets the same 403 for a real id and a nonexistent one), Q5 n/a | `GET /v2/entity-invitations/fa9a8e9a-…` as `probe`, the `invitee_email` on that row → 403 lacks `<Permission.READ: 1>` |
| rbac | entity_invitation | update | accept_entity_invitation | scope / permission | rest:POST /v2/entity-invitations/{id}/accept · cli:`bai entity-invitation accept` | **404 `entity-invitation_read_not-found`** — the superadmin passes RBAC but is not the invitee, and the repository matches on `invitee_user_id` | 403 role_create_forbidden at the caller's own user scope | match (`entity_invitation\|update\|scope`, denied then error) | Q1 ok, Q2 **mismatch** — **no principal can complete this action**, Q3 ok, Q4 ok, Q5 n/a | invitee → 403; superadmin → 404 `No pending invitation … to accept`; the row stays `pending` (`repositories/entity_invitation/repository.py:41`) |
| rbac | entity_invitation | update | reject_entity_invitation | scope / permission | rest:POST /v2/entity-invitations/{id}/reject · cli:`bai entity-invitation reject` | **404 `entity-invitation_read_not-found`** — same cause as accept | 403 role_create_forbidden at the caller's own user scope | match | Q1 ok, Q2 **mismatch** — **no principal can complete this action**, Q3 ok, Q4 ok, Q5 n/a | invitee → 403; superadmin → 404 `No pending invitation … to reject` |
| rbac | entity_invitation | delete | cancel_entity_invitation | single_entity / permission | rest:DELETE /v2/entity-invitations/{id} · cli:`bai entity-invitation cancel` | 200 ok, status → `canceled` | 403 role_create_forbidden (`<Permission.SOFT_DELETE: 8>`) | match (`entity_invitation\|delete\|single_entity\|success`) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/entity-invitations/fa9a8e9a-…` as the inviter → 200; the invitee → 403 |
| rbac | entity_invitation | search | search_entity_invitations | scope / permission | rest:POST /v2/entity-invitations/scoped/search · cli:`bai entity-invitation scoped-search` | 200 ok by `invitee` or by `inviter` scope | 403 role_create_forbidden — **denied on the caller's own user scope** | match (`entity_invitation\|search\|scope\|denied`) | Q1 ok, Q2 **mismatch** (a user cannot search the invitations addressed to them), Q3 ok, Q4 ok (self, another user and a nonexistent id all give the same 403), Q5 n/a | `POST /v2/entity-invitations/scoped/search {"scope":{"invitee":[{"value":"f2355877-…"}]},"limit":5}` as that same user → 403; as superadmin → 200 |
| rbac | role_preset | create | create_role_preset | global / permission | rest:POST /v2/role-presets | 201 ok | 403 (route middleware) | mismatch: entity_type=global, catalog says role_preset | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `POST /v2/role-presets {"name":"ba7489a-preset","scope_type":"project","auto_assign":false,"permissions":[]}` |
| rbac | role_preset | get | get_role_preset | single_entity / permission | rest:GET /v2/role-presets/{id} | 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `GET /v2/role-presets/00000000-0000-0000-0000-0000000000ff` → 404 `RolePresetRow ... not found` |
| rbac | role_preset | update | update_role_preset | single_entity / permission | rest:PATCH /v2/role-presets/{id} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `PATCH /v2/role-presets/00000000-0000-0000-0000-0000000000ff {"description":"x"}` |
| rbac | role_preset | search | search_role_presets | global / permission | rest:POST /v2/role-presets/search | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/role-presets/search {"pagination":{"limit":3}}` |
| rbac | role_preset | delete | bulk_delete_role_presets | bulk / permission | rest:POST /v2/role-presets/bulk-delete | 200 ok with `items` + `failed` | 403 (route middleware) | match (one row per resolved entity; `error` row for the miss) | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 ok with a caveat — every named id is answered exactly once and a miss carries `Entity not found.`, but successes and failures come back as **two lists rather than one input-ordered sequence** | `POST /v2/role-presets/bulk-delete {"role_preset_ids":[<real>,00000000-0000-0000-0000-0000000000ff,<real>]}` → items=[real,real], failed=[00000000-0000-0000-0000-0000000000ff] |
| rbac | role_preset | restore | bulk_restore_role_presets | bulk / permission | rest:POST /v2/role-presets/bulk-restore | 200 ok with `items` + `failed` | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 ok (same caveat) | `POST /v2/role-presets/bulk-restore {"role_preset_ids":["00000000-0000-0000-0000-0000000000ff"]}` |
| rbac | role_preset | purge | bulk_purge_role_presets | bulk / permission | rest:POST /v2/role-presets/bulk-purge | 200 ok with `items` + `failed` | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 ok (same caveat) | `POST /v2/role-presets/bulk-purge {"role_preset_ids":["00000000-0000-0000-0000-0000000000ff"]}` |
| rbac | role_preset | purge | purge_role_preset | single_entity / permission | none — the API only calls `bulk_purge` | unreachable | unreachable | no row | Q1 **mismatch**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no single-purge route exists on `/v2/role-presets`; matches the BA-7486 `W` verdict |
| rbac | role_preset | lookup | lookup_bulk_role_permission_preset_owner | lookup / permission | internal: fires ahead of `POST /v2/role-presets/permissions/remove` | 404-class error row on a miss | 403 (route middleware) | match (`role_preset\|lookup\|lookup\|error`) | Q1 ok — **reachable, unlike the singular variant**, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /v2/role-presets/permissions/remove {"permission_preset_ids":[<real>,00000000-0000-0000-0000-0000000000ff,<real>]}` → audit `lookup_bulk_role_permission_preset_owner\|role_preset\|lookup\|lookup\|error` |
| rbac | role_preset | lookup | lookup_role_permission_preset_owner | lookup / permission | none | unreachable | unreachable | no row | Q1 **mismatch** (single field ops are not wired for this domain), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no caller; matches the BA-7486 `W` verdict |
| rbac | role_permission_preset | search | search_role_permission_presets | scope / permission | rest:POST /v2/role-presets/{id}/permissions/search | 200 ok — **200 with an empty list for a preset that does not exist** | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 mismatch (superadmin_required, so the scope gate never runs), Q3 no row, Q4 **mismatch** (a missing preset is indistinguishable from an empty one, so nothing 404s), Q5 n/a | `POST /v2/role-presets/00000000-0000-0000-0000-0000000000ff/permissions/search {"pagination":{"limit":5}}` → 200 `{items:[],total_count:0}` |
| rbac | role_permission_preset | update | bulk_add_role_permission_presets | single_entity / permission | rest:POST /v2/role-presets/{id}/permissions/add | 200 ok; **409 with a raw asyncpg FK-violation message on a missing preset** | 403 (route middleware) | match (`role_preset\|update\|single_entity`) | Q1 ok, Q2 mismatch, Q3 ok, Q4 **mismatch** (409 `database_generic_not-found` — the status and the error code disagree, and the DB constraint name leaks), Q5 n/a | `POST /v2/role-presets/00000000-0000-0000-0000-0000000000ff/permissions/add {"permissions":[{"entity_type":"vfolder","operation":"read"}]}` |
| rbac | role_permission_preset | update | bulk_remove_role_permission_presets | bulk / permission | rest:POST /v2/role-presets/permissions/remove | 200 ok with `items` + `failed` | 403 (route middleware) | match (one `success` row per resolved entity, plus the lookup `error` row for the miss) | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 ok with the same two-list caveat | `POST /v2/role-presets/permissions/remove {"permission_preset_ids":[<real>,00000000-0000-0000-0000-0000000000ff,<real>]}` → items=2, failed=1 |
| resource_policy | keypair_resource_policy | create | global_create_keypair_resource_policy | global / permission | rest:POST /v2/resource-policies/keypair | 201 ok | 403 (route middleware) | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `POST /v2/resource-policies/keypair {"name":"ba7489a-kprp","default_for_unspecified":"UNLIMITED","total_resource_slots":[],"allowed_vfolder_hosts":[],...}` |
| resource_policy | keypair_resource_policy | get | get_keypair_resource_policy | single_entity / permission | rest:GET /v2/resource-policies/keypair/{name} | 200 ok; 404 on miss | 403 (route middleware) | no row on hit; `lookup_keypair_resource_policy` error row on miss | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok (one 403 for both cases), Q5 n/a | `GET /v2/resource-policies/keypair/ba7489a-nopolicy` → 404 `No KeyPairResourcePolicyRow matches the given key` |
| resource_policy | keypair_resource_policy | lookup | lookup_keypair_resource_policy | lookup / permission | internal: fires ahead of the `/keypair/{name}` GET, PATCH and DELETE routes | 404 on miss | not reached (route denies first) | match (`lookup_kind=keypair_resource_policy_name`) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `PATCH /v2/resource-policies/keypair/ba7489a-nopolicy` → audit `lookup_keypair_resource_policy\|...\|error` |
| resource_policy | keypair_resource_policy | search | global_search_keypair_resource_policies | global / permission | rest:POST /v2/resource-policies/keypair/search | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/resource-policies/keypair/search {"pagination":{"limit":2}}` |
| resource_policy | keypair_resource_policy | search | search_keypair_resource_policies | scope / permission | rest:GET /v2/resource-policies/keypair/my | 200 ok (superadmin bypasses RBAC) | **403 role_create_forbidden — the owner cannot read their own policy** | match (`keypair_resource_policy\|search\|scope\|denied`) | Q1 ok, Q2 **mismatch**, Q3 ok, Q4 ok, Q5 n/a | `GET /v2/resource-policies/keypair/my` as u1 → lacks `<Permission.READ: 1>` on keypair_resource_policy at its own user scope |
| resource_policy | keypair_resource_policy | update | update_keypair_resource_policy | single_entity / permission | rest:PATCH /v2/resource-policies/keypair/{name} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `PATCH /v2/resource-policies/keypair/ba7489a-kprp {"max_concurrent_sessions":7}` |
| resource_policy | keypair_resource_policy | purge | global_purge_keypair_resource_policy | single_entity / permission | rest:DELETE /v2/resource-policies/keypair/{name} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/resource-policies/keypair/ba7489a-kprp` → audit `global_purge_keypair_resource_policy\|keypair_resource_policy\|purge\|single_entity\|success` |
| resource_policy | user_resource_policy | create | global_create_user_resource_policy | global / permission | rest:POST /v2/resource-policies/user | 201 ok | 403 (route middleware) | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `POST /v2/resource-policies/user {"name":"ba7489a-urp","max_vfolder_count":10,"max_quota_scope_size":{"expr":"-1"},...}` |
| resource_policy | user_resource_policy | get | get_user_resource_policy | single_entity / permission | rest:GET /v2/resource-policies/user/{name} | 200 ok; 404 on miss | 403 (route middleware) | no row on hit; `lookup_user_resource_policy` error row on miss | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `GET /v2/resource-policies/user/ba7489a-nopolicy` → 404 |
| resource_policy | user_resource_policy | lookup | lookup_user_resource_policy | lookup / permission | internal: fires ahead of the `/user/{name}` GET, PATCH and DELETE routes | 404 on miss | not reached | match (`lookup_kind=user_resource_policy_name`) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/resource-policies/user/ba7489a-nopolicy` → audit `lookup_user_resource_policy\|...\|error` |
| resource_policy | user_resource_policy | search | global_search_user_resource_policies | global / permission | rest:POST /v2/resource-policies/user/search | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/resource-policies/user/search {"pagination":{"limit":2}}` |
| resource_policy | user_resource_policy | search | search_user_resource_policies | scope / permission | rest:GET /v2/resource-policies/user/my | 200 ok (superadmin bypasses RBAC) | **403 role_create_forbidden — the owner cannot read their own policy** | match (`user_resource_policy\|search\|scope\|denied`) | Q1 ok, Q2 **mismatch**, Q3 ok, Q4 ok, Q5 n/a | `GET /v2/resource-policies/user/my` as u1 → lacks READ at its own user scope; as sa → 200 |
| resource_policy | user_resource_policy | update | update_user_resource_policy | single_entity / permission | rest:PATCH /v2/resource-policies/user/{name} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `PATCH /v2/resource-policies/user/ba7489a-urp {"max_vfolder_count":11}` |
| resource_policy | user_resource_policy | purge | global_purge_user_resource_policy | single_entity / permission | rest:DELETE /v2/resource-policies/user/{name} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/resource-policies/user/ba7489a-urp` → 200 `{name: ba7489a-urp}` |
| resource_policy | project_resource_policy | create | global_create_project_resource_policy | global / permission | rest:POST /v2/resource-policies/project | 201 ok | 403 (route middleware) | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `POST /v2/resource-policies/project {"name":"ba7489a-prp","max_vfolder_count":10,"max_quota_scope_size":{"expr":"-1"},"max_network_count":3}` |
| resource_policy | project_resource_policy | get | get_project_resource_policy | single_entity / permission | rest:GET /v2/resource-policies/project/{name} | 200 ok; 404 on miss | 403 (route middleware) | no row on hit; `lookup_project_resource_policy` error row on miss | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `GET /v2/resource-policies/project/ba7489a-nopolicy` → 404 |
| resource_policy | project_resource_policy | lookup | lookup_project_resource_policy | lookup / permission | internal: fires ahead of the `/project/{name}` GET, PATCH and DELETE routes | 404 on miss | not reached | match (`lookup_kind=project_resource_policy_name`) | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/resource-policies/project/ba7489a-nopolicy` → audit `lookup_project_resource_policy\|...\|error` |
| resource_policy | project_resource_policy | search | global_search_project_resource_policies | global / permission | rest:POST /v2/resource-policies/project/search | 200 ok | 403 (route middleware) | no row (successful read) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /v2/resource-policies/project/search {"pagination":{"limit":2}}` |
| resource_policy | project_resource_policy | update | update_project_resource_policy | single_entity / permission | rest:PATCH /v2/resource-policies/project/{name} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `PATCH /v2/resource-policies/project/ba7489a-prp {"max_vfolder_count":11}` |
| resource_policy | project_resource_policy | purge | global_purge_project_resource_policy | single_entity / permission | rest:DELETE /v2/resource-policies/project/{name} | 200 ok; 404 on miss | 403 (route middleware) | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `DELETE /v2/resource-policies/project/ba7489a-prp` → 200 `{name: ba7489a-prp}` |

## Findings

Ranked most severe first. Each entry gives what was declared, what happened, the reproduction, and the
blast radius. Reproductions use the API-mode HMAC credentials from the shared brief; `<sa>`/`<u1>` name
the principal.

F16–F19 were found in a second pass, after the lead applied the `f4b1c9d27a08` migration and pointed out
that `./bai gql --v2` reaches the bulk mutations. They are appended rather than renumbered because F1–F15
have already been circulated. By severity F16 belongs immediately after F6 — it shares their root cause,
an ordinary user holding no permission at their own user scope — and F17–F19 belong around F13.

### F1 — Any project member reads every other member's record, including the superadmin's access key

| | |
|---|---|
| Actions | `search_users_by_project` (scope / permission), `get_user` (single_entity / permission), `get_default_keypairs` (bulk / permission) |
| Declared | An RBAC READ check on `user` at the named project scope, and a bulk READ check on the keypairs behind `main_access_key`. |
| Happened | `u1`, a plain user, gets 200 and the full record of every member of the `default` project — `email`, `username`, `role`, `main_access_key`, `allowed_client_ip`, `totp_activated`, `sudo_session_enabled`, `container_uid`. `admin@lablup.com`'s `main_access_key` (`AKIAIOSFODNN7EXAMPLE`) is in the response. The single-entity path leaks the same data one row at a time across the whole domain. |

Reproduction:

```bash
# every member of the default project, as a plain user
<u1> POST /v2/users/projects/2de2b969-1d04-48a6-af16-0bc8adb3c831/search  {"pagination":{"limit":50}}
# one arbitrary user, as a plain user — works for any user in the caller's domain
<u1> GET  /v2/users/f38dea23-50fa-42a0-b5ae-338f5f4693f4     # admin@lablup.com → 200
<u1> GET  /v2/users/2e10157d-20ca-4bd0-9806-3f909cbcd0e6     # monitor@ → 200
<u1> GET  /v2/users/97a5ec88-9393-45c3-b77c-859b41151136     # ba7489a-victim@, other domain → 403
```

The grant comes from `create_user`: every account created through the API is auto-granted
`role_project_2de2b969_member` and `role_project_8e32dd28_member` — the `default` and `model-store`
project member roles — even when the account has no row in `association_groups_users`.

```sql
select r.name from user_roles ur join roles r on r.id=ur.role_id
 where ur.user_id='<a user created via POST /v2/users>';
-- role_project_2de2b969_member, role_project_8e32dd28_member, role_domain_default_member, user-<id>
select g.name from association_groups_users agu join groups g on g.id=agu.group_id
 where agu.user_id='<same user>';
-- (0 rows)
```

Blast radius: every authenticated user of the deployment. Access keys are half of the HMAC credential and
directly identify the superadmin's keypair, which makes every other action in this slice a targeted one.
The `security` block additionally tells an attacker which accounts have no TOTP and which have
`sudo_session_enabled`.

### F2 — `assign_users_to_project` grants a role belonging to a different project

| | |
|---|---|
| Action | `assign_users_to_project` (single_entity / permission) |
| Declared | UPDATE on the project named in the path. |
| Happened | The `role_id` in the body is never checked against the project in the path. Assigning a user to project A while naming project B's member role grants B's role. |

Reproduction:

```bash
# grant the model-store member role while assigning to the default project
<sa> POST /v2/rbac/assignments/revoke {"user_id":"<u>","role_id":"254fef91-2574-46f5-afc6-c9b18cfa340b"}
<sa> POST /v2/projects/2de2b969-1d04-48a6-af16-0bc8adb3c831/users/assign \
        {"user_ids":["<u>"],"role_id":"254fef91-2574-46f5-afc6-c9b18cfa340b"}   # 254fef91 = role_project_8e32dd28_member
# → 200; the user now holds BOTH role_project_2de2b969_member and role_project_8e32dd28_member
select r.name from user_roles ur join roles r on r.id=ur.role_id where ur.user_id='<u>';
select scope_type, scope_id, relation_type from association_scopes_entities where entity_id='<u>';
-- project | 2de2b969-… | auto     ← membership is written here, not in association_groups_users
```

Blast radius: anyone who holds UPDATE on any one project can grant a role scoped to any other project,
provided they can name its id. Role ids are readable from `POST /v2/rbac/roles/search`. On this deployment
that route is superadmin-only, which contains the exposure today — but the action's own declared gate is
per-project UPDATE, so the containment is the route middleware, not the check the action asks for.

### F3 — Projects created through the API get no RBAC roles, so nobody can ever be granted access

| | |
|---|---|
| Action | `create_project` (scope / permission) |
| Declared | Creates a project. |
| Happened | No `role_project_<id>_admin` or `role_project_<id>_member` row is created. Only the two fixture projects seeded at install time have roles. A project created through the API therefore has no role anyone can be assigned to, and `assign_users_to_project` on it can only grant some *other* project's role. |

Reproduction:

```bash
<sa> POST /v2/projects {"name":"ba7489a-proj","domain_name":"default","type":"general","resource_policy":"default"}
```
```sql
select name, created_at from roles where name like 'role_project%';
-- only role_project_2de2b969_* and role_project_8e32dd28_*, both created 2025-09-12 at install
select id, name, created_at from groups order by created_at desc;
-- ba7489a-proj 2026-08-25, model-store (in ba7489a-dom-v1) 2026-08-25 — neither has roles
```

The same holds for the `model-store` project auto-created as a side effect of `POST /admin/domains`.

Blast radius: every project created after install is unusable through RBAC. Combined with F5, a project
is both unmanageable and invisible to its members.

### F4 — `POST /auth/authorize` distinguishes an unknown user from a wrong password

| | |
|---|---|
| Action | `authorize` (global / anonymous) |
| Declared | Anonymous login. The 401 body is identical in both cases: `user_auth_unauthorized` / `Credential/signature mismatch.` / `User credential mismatch.` |
| Happened | The `traceback` string the error response carries is not identical. A wrong password unwinds through `_check_password`; an unknown user does not. The response body length differs by 192 bytes, which is a user-existence oracle available to an unauthenticated caller. |

Reproduction:

```bash
# existing user, wrong password
POST /auth/authorize {"type":"keypair","domain":"default","username":"user@lablup.com","password":"wrong"}
# unknown user
POST /auth/authorize {"type":"keypair","domain":"default","username":"nosuch@lablup.com","password":"wrong"}
# diff the `traceback` field of the two 401 bodies:
#   unknown user : db_source.py:419 in verify_credential
#   wrong password: db_source.py:421 → _check_password → db_source.py:330
```

Blast radius: unauthenticated account enumeration against the login endpoint. `POST /auth/signup` gives
the same oracle more directly — an existing email returns `user_create_already-exists`, a fresh one
returns 201 — so the two together enumerate and then confirm.

This is the per-action confirmation the brief asked for on the known F2 traceback leak: on this endpoint
the traceback is the *only* thing that differs, so removing it closes the oracle.

### F5 — A user cannot read any project they belong to, nor list their own projects

| | |
|---|---|
| Actions | `get_project` (single_entity / permission), `search_projects_by_user` (scope / permission) |
| Declared | READ on the project; READ on `project` at the caller's own user scope. |
| Happened | Both denied for an ordinary user, including for projects the caller is a verified member of. `u1` has rows in `association_groups_users` for both `default` and `model-store` and is denied READ on each. |

Reproduction:

```bash
<u1> GET /v2/projects/2de2b969-1d04-48a6-af16-0bc8adb3c831   # default, u1 is a member → 403
<u1> GET /v2/projects/8e32dd28-d319-4e3b-8851-ea37837699a5   # model-store, u1 is a member → 403
./bai gql --v2 'query { myUserV2 { projects(limit:3) { count } } }'   # as u1 → 403 at its own user scope
```

Blast radius: the project surface is closed to every non-superadmin. This is the exact inverse of F1 on
the same data — the project's member list is readable by anyone in it, the project itself by no one.

### F6 — A user cannot read their own resource policy

| | |
|---|---|
| Actions | `search_keypair_resource_policies`, `search_user_resource_policies` (both scope / permission) |
| Declared | READ on the policy at the caller's own user scope — these two actions exist to back the `/my` routes. |
| Happened | 403 for every non-superadmin. A superadmin gets 200 only because the validator returns early for `is_superadmin`. |

Reproduction:

```bash
<u1>    GET /v2/resource-policies/keypair/my   # 403 role_create_forbidden
<u1>    GET /v2/resource-policies/user/my      # 403 role_create_forbidden
<probe> GET /v2/resource-policies/keypair/my   # 403 — a second, freshly created user
<sa>    GET /v2/resource-policies/user/my      # 200
```

Blast radius: the entire self-service resource-policy read surface is dead for real users.

### F7 — The whole login-history read surface returns 500

| | |
|---|---|
| Actions | `global_search_login_history`, `search_login_history` |
| Declared | Admin and self-service login-history search. |
| Happened | Both 500. `LoginHistoryNode.client_ip` is `str \| None` in `common/dto/manager/v2/login_history/response.py:32` but the column is `inet`, so `adapters/login_history/adapter.py:177` hands pydantic an `IPv4Address`. |

Reproduction:

```bash
<sa> POST /v2/login-history/search     {"pagination":{"limit":2}}   # 500
<u1> POST /v2/login-history/my/search  {"pagination":{"limit":3}}   # 500
```

This is a second instance of the known F1 audit-log defect, in a different DTO and adapter. Fixing one
does not fix the other; both should be closed together, and the `inet`-to-`str` pattern is worth sweeping
for across every v2 response model.

**Full blast radius of the `inet`-vs-`str` pattern.** The brief recorded the audit-log instance as
affecting `GET /v2/audit-logs` only. Verified here, it takes down every client-facing route over both
tables — five in total, leaving direct SQL as the only way to read `audit_logs`:

| surface | result |
|---|---|
| `POST /v2/audit-logs/search` | 500 `backendai_generic_internal-error` |
| `gql:adminAuditLogsV2` | error `backendai_parsing_invalid-parameters` |
| `gql:scopedAuditLogsV2` | error `backendai_parsing_invalid-parameters` |
| `POST /v2/login-history/search` | 500 |
| `POST /v2/login-history/my/search` | 500 |

Two things make it worse than a single broken endpoint. **Not selecting the offending field is not a
workaround** — the pydantic model is built in the adapter before field selection is applied, so
`adminAuditLogsV2 { entityType operation status }` fails identically to a query that asks for `clientIp`.
And the GraphQL surface reports it as `backendai_parsing_invalid-parameters`, a client-error code, for
what is a server-side serialisation bug; the REST surface calls the same failure an internal error.

```bash
./bai gql --v2 'query { adminAuditLogsV2(limit:2) { count edges { node { entityType operation status } } } }'
./bai gql --v2 'query { scopedAuditLogsV2(scope:{triggeredUser:[{value:"<uuid>"}]}, limit:2) { count } }'
# both: "Schema validation failed. (Input should be a valid string)"
```

### F8 — A missing table returns the raw INSERT statement and its parameter values to the client

| | |
|---|---|
| Action | `create_entity_invitation` (scope / permission) |
| Declared | 500 responses should not carry SQL. |
| Happened | The 500 body contains the full `INSERT INTO entity_invitations (...) VALUES (...)` statement, the bound parameter tuple (inviter UUID, invitee email, target entity id), and the asyncpg exception class. |

Reproduction:

```bash
<sa> POST /v2/entity-invitations \
     {"target_entity_type":"project","target_entity_id":"2de2b969-1d04-48a6-af16-0bc8adb3c831",
      "invitee_email":"ba7489a-probe@lablup.com","permissions":["read"]}
```

`create_project` shows the same class of leak on a constraint violation — omitting the (optional in the
DTO, NOT NULL in the DB) `resource_policy` field returns
`DETAIL: Failing row contains (436619ef-..., ba7489a-proj, BA-7489 A, t, null, default, {}, {}, \x90, ...)`.

Blast radius: any DB-level failure discloses schema, column order and live row contents.

**Trigger condition since removed, code path unchanged.** The lead applied `f4b1c9d27a08` mid-run, so
`entity_invitations` now exists and this particular 500 no longer reproduces. Nothing in the error path
changed, and the same leak is still reachable on the same entity without a missing table: a duplicate
pending invitation returns a correct domain error (409 `entity-invitation_create_conflict`) whose
`traceback` still carries the raw asyncpg text, the constraint name `uq_entity_invitations_pending`, and
the key values.

```bash
# the same invitation twice
<sa> POST /v2/entity-invitations {"target_entity_type":"project","target_entity_id":"54c7cf75-…","invitee_email":"ba7489a-probe@lablup.com","permissions":["read"]}
# 409 body carries: DETAIL: Key (invitee_email, target_entity_type, target_entity_id)=(ba7489a-probe@lablup.com, project, 54c7cf75-…) already exists.
```

### F9 — Audit rows record success for runs that failed

Three actions write `status = success` for a run that returned an error or changed nothing.

| action | what happened | reproduction |
|---|---|---|
| `update_project` | 500 `UnreachableError: modify_group must return data` on a missing id, audit row `success` | `<sa> PATCH /v2/projects/00000000-0000-0000-0000-0000000000ff {"description":"x"}` |
| `update_password` | 400 `new password mismatch`, nothing changed, audit row `success` | `<probe> POST /auth/update-password {"old_password":"<correct>","new_password":"A","new_password2":"B"}` |
| `logout` | 200 and audit row `success` for a session token that does not exist | `<probe> POST /auth/logout {"session_token":"00000000000000000000000000000000"}` |

`global_unblock_user` behaves the same way — `{"username":"ba7489a-nosuch@lablup.com"}` returns 200
`{success:true}` and writes a success row for an account that does not exist.

**Independently re-verified.** Agent C flagged the `update_project` row from the other side of the
audit table and read it as a separate defect on a different entity; it is this finding's own first row,
not a second instance. Re-run confirms the more severe of the two readings the lead asked about — the
HTTP response is **500**, not a 404, and the row's `description` column literally reads `Success`:

```bash
<sa> PATCH /v2/projects/00000000-0000-0000-0000-0000000000ff {"description":"BA-7489 verify"}
# HTTP 500 backendai_generic_unreachable | modify_group must return data
```
```sql
select action_name, entity_id, status, description from audit_logs order by created_at desc limit 1;
-- update_project | 00000000-0000-0000-0000-0000000000ff | success | Success
```

So the pattern is four actions across three entity types (`project`, `user`, `auth`/`login_session`),
and in the `update_project` case the run that the trail calls a success actually raised a 500.

Blast radius: the audit log affirms password changes, session revocations and project edits that never
happened. Anyone reading the trail to answer "was this changed?" gets the wrong answer.

### F10 — Every `global`-kind action records `entity_type = 'global'`

| | |
|---|---|
| Actions | all 33 global-kind actions in this slice, including the seven `auth` actions, `signup`, `global_create_domain`, `global_create_domain_node`, `search_users_by_role`, `create_role_preset` and the three `global_create_*_resource_policy` actions |
| Declared | The catalog names `auth`, `user`, `domain`, `role_preset`, `keypair_resource_policy`, … |
| Happened | `actions/v2/global_scope/monitor/audit_log.py:73` calls `create_dangling_field(GLOBAL_ENTITY_TYPE, creator)`, discarding `action.entity_type()`. Every such row lands as `global`. |

Reproduction:

```bash
POST /auth/authorize {...}   # then:
```
```sql
select action_name, entity_type, action_kind from audit_logs where action_name='authorize' order by created_at desc limit 1;
-- authorize | global | global      (the catalog declares entity_type `auth`)
```

Blast radius: no audit query can filter global-kind operations by the entity they touched. Note the
non-global monitors do this correctly — `global_purge_user_resource_policy` writes
`entity_type=user_resource_policy` — so the fix is one call site.

### F11 — Every RBAC denial reports `role_create_forbidden`

`NotEnoughPermission.error_code()` in `errors/permission.py:93` hardcodes `ErrorDomain.ROLE` and
`ErrorOperation.CREATE`. A user READ denial, a domain UPDATE denial and an invitation SOFT_DELETE denial
all come back as `role_create_forbidden`.

```bash
<u1> GET  /v2/users/97a5ec88-9393-45c3-b77c-859b41151136        # role_create_forbidden, "lacks READ on user"
<da> POST /domain-config/dotfiles {"domain":"default",...}      # role_create_forbidden, "lacks UPDATE on domain"
<u1> DELETE /v2/entity-invitations/00000000-...-0000000000ff    # role_create_forbidden, "lacks SOFT_DELETE"
```

Blast radius: any client branching on `error_code` cannot tell these apart. The human-readable `msg` does
carry the real entity and permission bit — which is also the only reason F1 and F5 were diagnosable.

### F12 — 57 gated actions never reach the gate they declare, and leave no audit row when denied

(41 of these are scored `Q2 mismatch`; the other 16 are `global`-kind actions where superadmin happens to
be the right answer, so only the missing audit row is wrong.)

Every action whose route carries `superadmin_required` is decided by the middleware, not by the RBAC check
the action declares. The middleware raises `GenericForbidden("Insufficient privileges")` from
`api/rest/middleware/auth.py:917` before the processor runs, so no audit row is written.

The mechanism is confirmed, not inferred, and it is the interaction of two rules. `AuditLogPolicy` writes a
row for every mutation — success, `denied` and `error` alike — and for every read that fails, but nothing
for a successful read. That policy runs inside the action processor. A route-middleware rejection never
reaches the processor, so the policy never gets a chance to apply: **superadmin-gate denials are absent
from `audit_logs` entirely**, whatever the operation. A `denied` row therefore only ever exists where the
RBAC validator ran, which is exactly the set of actions the middleware let through.

```bash
<u1> POST /v2/domains/search   # 403 backendai_generic_forbidden
select count(*) from audit_logs where created_at > now() - interval '1 minute';   -- 0
```

Two consequences beyond the missing rows:

- A `permission`-gated action is in practice superadmin-only. `create_project` declares a scope gate, so a
  domain admin holding CREATE on the domain should be able to create a project; `da` gets 403.
- The same action reached through two routes meets two different gates. `get_user` is
  `superadmin_required` on `GET /admin/users/{id}` and `auth_required` on `GET /v2/users/{id}`, which is
  how F1 became reachable.

Actions affected in this slice: all `global_*` and `admin_*` REST routes, the domain and project lifecycle
routes, `update_user`, `delete_user`, `get_keypair`, `purge_keypair`, the `role_preset` set, and the
`resource_policy` admin set. The per-action table marks each one `Q2 mismatch`.

### F13 — Three lookup surfaces 404 a miss before any permission check

| action | route | behaviour |
|---|---|---|
| `lookup_error_log_owner` | `POST /logs/error/{log_id}/clear` | an unknown id returns 404 `database_access_not-found` to any authenticated caller, before ownership is tested |
| `lookup_login_session_owner` | `POST /v2/login-sessions/my/revoke` | same |
| `lookup_domain` | every `/v2/domains/{name}` and `/v2/users/domains/{name}/…` route | an unknown domain returns 404 while a known-but-unauthorized one returns 403 |

```bash
<probe> POST /logs/error/00000000-0000-0000-0000-0000000000ff/clear            # 404
<u1>    POST /v2/users/domains/ba7489a-nodomain/search {"pagination":{"limit":3}}  # 404
<u1>    POST /v2/users/domains/default/search          {"pagination":{"limit":3}}  # 403
```

Blast radius: id and domain-name enumeration for any authenticated user. The keypair surface does this
correctly — `GET /v2/keypairs/{ak}` returns the same 403 for the caller's own key, another user's key and
a nonexistent key — so the correct shape already exists in the codebase.

### F14 — `assign_users_to_project` drops unknown users silently and aborts on a duplicate

| | |
|---|---|
| Declared | A single-entity update over a named list of users. |
| Happened | A user id that does not exist is not reported at all — it is absent from both the response and the audit trail. A user who already holds the role aborts the entire call with 409 and rolls back the users that would have succeeded. The paired `unassign_users_from_project` gets this right: it answers every named user and distinguishes `User does not exist.` from `User is not assigned to this project.` — but returns them out of input order. |

```bash
<sa> POST /v2/projects/54c7cf75-.../users/assign \
     {"user_ids":["<real>","00000000-0000-0000-0000-0000000000ff","<real>"],"role_id":"<r>"}
# → 200, two items, the unknown id unmentioned
<sa> POST /v2/projects/54c7cf75-.../users/unassign \
     {"user_ids":["<doomed>","00000000-0000-0000-0000-0000000000ff","<probe>"]}
# → 200, failed=[00000000-…, probe, doomed] — every id answered, input order not preserved
```

The `role_preset` bulk actions are the best-behaved partial bulks in the slice: `bulk_delete`,
`bulk_restore`, `bulk_purge` and `bulk_remove_role_permission_presets` all account for every named id
exactly once across `items` and `failed`, with `Entity not found.` on the misses. Their only shortcoming
is the same one — the caller must merge two lists to recover input order.

### F15 — Smaller mismatches

| what | action | detail |
|---|---|---|
| A required parameter that does nothing | `update_full_name` | `POST /auth/update-full-name` requires `email` and then ignores it. Naming another user's email returns 200 and renames the caller. Naming an address that does not exist also returns 200. Verified: `user2@lablup.com`'s `full_name` is unchanged after the attempt. |
| Missing preset reads as empty | `search_role_permission_presets` | `POST /v2/role-presets/{missing}/permissions/search` returns 200 `{items:[],total_count:0}` instead of 404. |
| Status and error code disagree | `bulk_add_role_permission_presets` | Adding to a preset that does not exist returns HTTP 409 with `error_code: database_generic_not-found`, and the body carries the raw asyncpg FK-violation text including the constraint name. |
| Inconsistent not-found codes on one entity | `purge_project` vs `delete_project` / `restore_project` | The same missing `group_id` gives `group_read_not-found` from purge and `database_access_not-found` from delete and restore. |
| v1 body key in a v2 DTO | `delete_project`, `restore_project`, `purge_project` | The v2 routes take `group_id`, not `project_id`. |
| Optional in the DTO, NOT NULL in the DB | `create_project` | `resource_policy` defaults to `None` in `CreateProjectInput` and the insert then violates the constraint (see F8). |
| Domain admin has no UPDATE on its own domain | `create/update/delete_domain_dotfile` | The `/domain-config/dotfiles` routes are `admin_required`, so `da` passes the middleware and is then denied by RBAC on `default`, the domain it administers. |
| Superadmin gets 500 where a user gets 403 | `get_entity_invitation` | The superadmin bypasses RBAC and reaches the missing table; a plain user is denied first and gets a clean 403. |
| Legacy audit format still in use | `revoke_role` (adjacent to this slice) | Writes `action_name='role:assignment:delete'`, `action_kind='unknown'` — the `LegacyAuditLogCreator` path. |
| GraphQL cannot project `action_name` | `admin_search_audit_logs` (adjacent) | The `AuditLogV2` GQL node exposes `actionId`, `entityType`, `operation`, `entityId`, `status` and `clientIp` but no `actionName`, though the column and the REST DTO both carry it. A reader on the GraphQL side cannot see which action produced a row. |

### F16 — The entity-invitation flow cannot be completed by any principal

Ranks with F5 and F6: same root cause, larger consequence. Found after the `f4b1c9d27a08` migration made
the success path reachable.

| step | inviter (superadmin) | invitee | verdict |
|---|---|---|---|
| `create_entity_invitation` | 201 ok | 403 — lacks CREATE at the project scope | admin-only, works |
| `get_entity_invitation` | 200 ok | **403 — lacks READ on the invitation addressed to them** | invitee blind |
| `search_entity_invitations` | 200 ok by `invitee` or `inviter` scope | **403 — lacks READ at their own user scope** | invitee blind |
| `accept_entity_invitation` | **404 `No pending invitation … to accept`** | **403 — lacks UPDATE at their own user scope** | **nobody can accept** |
| `reject_entity_invitation` | **404 `No pending invitation … to reject`** | **403 — lacks UPDATE at their own user scope** | **nobody can reject** |
| `cancel_entity_invitation` | 200 ok, status → `canceled` | 403 (`SOFT_DELETE`) | admin-only, works |

An invitation can be created and cancelled by an administrator, and that is all. The invitee can neither
see it, accept it, nor reject it, so no invitation can ever be settled.

Reproduction:

```bash
<sa>    POST   /v2/entity-invitations {"target_entity_type":"project","target_entity_id":"54c7cf75-…",
                                      "invitee_email":"ba7489a-probe@lablup.com","permissions":["read"]}   # 201, pending
<probe> GET    /v2/entity-invitations/<id>                        # 403 lacks READ  — probe IS the invitee
<probe> POST   /v2/entity-invitations/<id>/accept                 # 403 lacks UPDATE at its own user scope
<sa>    POST   /v2/entity-invitations/<id>/accept                 # 404 No pending invitation … to accept
<probe> POST   /v2/entity-invitations/scoped/search {"scope":{"invitee":[{"value":"<probe uuid>"}]}}  # 403
select status from entity_invitations;                            # still 'pending'
```

The superadmin's 404 is not a permission problem — it is the repository matching on the caller:
`accept()` and `reject()` filter by `invitee_user_id` (`repositories/entity_invitation/repository.py:30-56`),
so the only principal RBAC permits is the one principal the query excludes.

Blast radius: the entity-invitation feature is inert. The six actions are wired, routed, CLI-exposed
(`./bai entity-invitation create|get|accept|reject|cancel|scoped-search`) and audited correctly — the
gate is the only thing stopping them.

### F17 — `global_create_users` aborts the whole batch when one item names a missing domain

| | |
|---|---|
| Action | `global_create_users` (global / permission), `gql:adminBulkCreateUsersV2` |
| Declared | A partial bulk. The payload has a `failed` list whose entries carry `index`, `username`, `email` and `message` — the only per-item error type in this slice that reports the input position. |
| Happened | With every domain resolving, the contract is honoured exactly: 4 items in → 2 in `createdUsers`, 2 in `failed` with correct indices, the in-batch duplicate correctly reported as already existing. Change one item's `domainName` to a name that does not exist and the entire mutation returns `data: null` with a single top-level `database_access_not-found`. Nothing is created, and `failed` is never populated. The domain is resolved up front in `_build_bulk_create_user_action` (`api/gql/user/resolver/mutation.py:100-146`), outside the partial-bulk machinery. |

Reproduction:

```bash
# honoured: 4 items → 2 created, 2 failed with index 1 and index 2
./bai gql --v2 'mutation { adminBulkCreateUsersV2(input:{users:[
  {email:"ba7489a-bulk1@lablup.com", username:"ba7489a-bulk1", …, domainName:"default", …},
  {email:"user@lablup.com",          username:"user",          …, domainName:"default", …},
  {email:"ba7489a-bulk1@lablup.com", username:"ba7489a-bulk1", …, domainName:"default", …},
  {email:"ba7489a-bulk3@lablup.com", username:"ba7489a-bulk3", …, domainName:"default", …}
]}) { createdUsers { id } failed { index username email message } } }'

# aborted: swap item 2's domainName to "ba7489a-nodomain" → data:null, nothing created
```

Blast radius: one unknown domain in a batch of any size silently discards every valid item in it. A caller
following the schema would expect that item to appear in `failed` and the rest to be created.

### F18 — `global_purge_users` reports successes only as a count

| | |
|---|---|
| Action | `global_purge_users` (global / permission), `gql:adminBulkPurgeUsersV2` |
| Declared | A partial bulk over a named list of user ids. |
| Happened | `BulkPurgeUsersV2Payload` returns `purgedCount: Int` and a `failed` list. Failures name their `userId`; successes do not appear at all. With a mixed batch the caller can only infer which users were purged by subtracting the failures — and cannot do even that when the batch contains a repeated id, since neither side carries an `index`. |

Reproduction:

```bash
./bai gql --v2 'mutation { adminBulkPurgeUsersV2(input:{userIds:["<b1>","<b3>","00000000-0000-0000-0000-0000000000ff","<b1>"]})
                          { purgedCount failed { userId message } } }'
# → purgedCount: 2, failed: [00000000-… "does not exist", <b1> "does not exist"]
```

The repeated id reports `The user does not exist.` on its second occurrence, which is true only because
the first occurrence purged it — a miss and an already-consumed duplicate are indistinguishable.

Blast radius: an irreversible operation whose result cannot be reconciled against its input. `global_update_users`
on the same data gets this right, returning the full `updatedUsers` list in input order.

### F19 — GraphQL admin-gate denials surface as internal errors

`check_admin_only()` (`api/gql/utils.py:14`) raises a bare `web.HTTPForbidden`, not a `BackendAIError`.
The GraphQL error mapper has no code for it, so an authorization failure reaches the client as
`extensions.code = backendai_generic_internal-error`.

```bash
u1 ./bai gql --v2 'mutation { adminBulkPurgeUsersV2(input:{userIds:["…"]}) { purgedCount } }'
# → "message": "Admin exclusive access", "extensions": {"code": "backendai_generic_internal-error"}
```

Confirmed on all three bulk mutations, for both a plain user and a domain admin. No audit row is written,
which is the F12 pattern on the GraphQL side. The gate itself is correct — despite the name,
`check_admin_only` tests `is_superadmin`, matching the declared `global` / `permission` gate.

Blast radius: clients cannot distinguish "you may not do this" from "the server broke", and monitoring
that alerts on internal errors will fire on every ordinary permission denial through these mutations.
This is also a direct violation of the project rule that exceptions inherit from `BackendAIError`.

### F20 — `signup`'s anonymous gate rests on a hook that nothing registers

Ranks with F4, which is the observable consequence. Found while re-scoring the `auth` rows against the
"is the declared gate justified?" question rather than the "is it the declared gate?" question.

| | |
|---|---|
| Action | `signup` (global / anonymous), `rest:POST /auth/signup` |
| Declared | `anonymous`, and correctly so — the request has no credential to present. What justifies skipping authentication is the `PRE_SIGNUP` hook, the admission control a deployment plugs in to decide whether self-registration is allowed at all (invite code, e-mail domain allowlist, captcha). |
| Happened | No plugin registers `PRE_SIGNUP` on this deployment. `HookPluginContext.dispatch` defaults to `success_if_no_hook=True` (`common/plugin/hook.py:126`) and `signup` does not override it (`services/auth/service.py:479`), so with no handler the loop body never runs and the result is `PASSED`. The guard that justifies the open gate is a no-op, and an unauthenticated caller creates a real active account with a working keypair. |

Reproduction:

```bash
POST /auth/signup {"domain":"default","email":"ba7489a-signup@lablup.com","username":"ba7489a-signup",
                   "password":"…","full_name":"Signup Probe"}
# → 201 {"access_key": "AKIAUB6CQ4ESWKJFP52C", "secret_key": "…"} — usable immediately
```

This is a different defect from F4. F4 is the response splitting on whether the e-mail already exists,
which discloses accounts; F20 is that nothing decides whether the caller may create one. Fixing F4 leaves
the gate open; fixing F20 closes the surface that makes F4 reachable.

The two sibling anonymous actions were checked against the same question and are **not** affected:

| action | what justifies `anonymous` | holds at runtime? |
|---|---|---|
| `authorize` | the password check is the operation itself, and the rate-limit middleware sits in front | yes — the credential check runs unconditionally |
| `update_password_no_auth` | `check_credential_without_migration(domain, email, current_password)` runs before any write | yes — and the whole action is config-disabled here (`auth.max_password_age is None`) |

Blast radius: unauthenticated account creation against any deployment that ships without a `PRE_SIGNUP`
plugin. The created account lands in the `default` domain and is auto-granted the `default` and
`model-store` project member roles by `create_user`, which is the entry condition for F1.
