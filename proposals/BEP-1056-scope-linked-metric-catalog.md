---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-07
Created-Version:
Target-Version:
Implemented-Version:
---

# Scope-Linked Metric Catalog & Dashboards

## Related Issues

- Epic **BA-6683**, this BEP **BA-6685**
- Related: BA-6449 (remove legacy resource-usage/stats REST), BA-6114 (move resource_usage off Valkey),
  BA-126 (resource-usage API refactor), BA-6446 (new unified resource query API), BA-4051 (remove ValkeyStatClient)
- Base BEPs (referenced, not expanded): **[BEP-1045](BEP-1045-prometheus-client-extraction-and-querier-interface-abstraction.md)** (Prometheus client extraction),
  **[BEP-1050](BEP-1050-prometheus-query-preset-system.md)** (query preset system),
  **[BEP-1026](BEP-1026-fair-share-scheduler.md)** (resource_usage_history buckets),
  virtual_scope RBAC (permission model)

## 1. Goal

Define a **Scope Metric Catalog** layer that takes `(scope_type, scope_id)` and returns that
scope's **instant/range metrics** and a **dedicated dashboard**.

Core principle: keep the scope↔metric binding as a **stored, generalized catalog**:

- Which metrics (query definitions) a scope has is **stored in dedicated tables**, and the client
  receives the **generalized descriptor plus the values**. Specific queries such as `live_stat` or
  monthly usage are **not hardcoded in code**.
- The actual values still come from Prometheus queries (BEP-1050 presets), but because the
  **scope→query binding is data-driven**, the Prometheus label schema does not need to be extended.
- Read permission is treated as a **scoped operation** (virtual_scope RBAC).

Much of the metric data already flows into Prometheus (`backendai_container_utilization`,
model-service `vllm:*`), but there is **no entry point to query/visualize it per scope**. This BEP
defines that entry point (stored catalog + scope REST + dashboards).

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 Metric source (Prometheus series)

| | Item |
|---|---|
| ✅ | `backendai_container_utilization{agent_id, kernel_id, session_id, user_id, project_id, container_metric_name, value_type}`, `backendai_device_utilization` (agent), `backendai_process_utilization` — `agent/metrics/metric.py` |
| ✅ | model-service scrape: each route registers `ModelServiceMetadata{runtime_variant, endpoint_id, deployment_id, project}` → `/metrics/service_discovery` → Prometheus `http-sd` scrapes `vllm:*` |
| ➕ | The scope→metric binding is owned by the **stored catalog** (by `scope_type`). **Prometheus label additions/strategy are out of scope for this BEP** (solved by dedicated tables) |

### 2.2 Catalog storage (scope↔metric binding)

| | Item |
|---|---|
| ✅ | `prometheus_query_presets` table + CRUD/execute REST, `MetricPreset({labels}/{window}/{group_by})`, `ContainerMetricQuerier`, `PrometheusClient.execute_preset` (BEP-1050) |
| ➕ | **No catalog table storing per-scope-type metric bindings** — callers must know labels/queries every time. This BEP introduces the stored catalog |

### 2.3 API

| | Item |
|---|---|
| ✅ | superadmin preset-execute REST (`resource/prometheus-query-definitions`) |
| ➕ | **No scope-level REST v2 endpoint** returning instant/range metrics and a dashboard for `(scope_type, scope_id)` |

### 2.4 Dashboard

| | Item |
|---|---|
| ✅ | Web UI `StatisticsPage`/`DeploymentDetailPage` bundles exist |
| ➕ | No stored structure for **dashboard / panel (1:N) / scope↔dashboard link** — managed **separately** from the metric catalog |

## 3. Implementation Design

**Core flow (metrics):** `(scope_type, scope_id)` → look up the `scope_type`'s metric bindings from
the stored catalog → pass the `scope_id` received at query time as `id` to the preset and execute
(instant/range). Permission is checked as a scoped operation.

**Dashboards are a separate subsystem** (dashboard 1:N panel + scope link), managed independently of
the metric catalog (see (c)).

### (a) Scope definition + stored binding (core)

`ScopeType = {session, kernel, agent, deployment, resource_group, domain, project, user}` (extensible).

Keep the scope↔metric binding as a **stored catalog**. The contract of one binding (conceptual):

| Field | Meaning |
|-------|---------|
| `scope_type` | The scope kind this binding applies to |
| `preset_ref` | Reference to the PromQL preset to execute (BEP-1050) |
| `mode` | instant \| range |
| `viz`, `unit` | Panel render hints (stat/timeseries/gauge/table, unit) |

- **Generalized**: the client receives a **binding descriptor + executed values**, not a specific
  query. Adding a new metric/scope is a **catalog data addition**, not a code change.
- **Binding is per `scope_type`**: the catalog links metrics to `scope_type` only. **`scope_id` is not
  stored**; it is received at query time as `id` and passed to preset execution. The storage schema
  (a single binding table vs per-scope tables) is an implementation choice.
- **Management**: the catalog is populated with **fixed seed defaults** and editable via **admin CRUD**.

### (b) Per-scope MetricSet

A scope's MetricSet = **the set of bindings stored for that `scope_type`**. The only selection axis is
the **scope**.

> Metric sets are not split by runtime variant (vLLM/custom, etc.). A deployment simply receives the
> stored MetricSet of its scope. Needing different metrics per runtime is a **data problem (add more
> bindings to the catalog)**, not a design axis.

### (c) Dashboard — separate subsystem (dashboard 1:N panel + scope link)

Dashboards are managed as a **stored structure separate from the metric catalog in (a)**. Three parts:

| Part | Meaning |
|------|---------|
| `dashboard` | A single dashboard (title and other metadata) |
| `panel` | A panel belonging to a dashboard `{title, preset_ref, mode, viz, unit, order}` — **dashboard 1 : N panel** |
| scope↔dashboard link | A mapping connecting an entity (scope) to a dashboard — provides per-scope dashboard association |

On query, return the **dashboard linked to the scope and its panels**; each panel's preset executes
with `scope_id` as `id`. The **consumer is the Web UI**, which renders the panels natively (Grafana
provisioning/deeplink out of scope). dashboard/panel/link are managed via fixed seed + admin CRUD.

### (d) API surface

```
GET /resource/scopes/{scope_type}/{scope_id}/metrics?range=<window>&step=<step>
    → { "<preset>": {"instant": <scalar>, "series": [[ts,val],...]}, ... }   # instant only when range omitted
GET /resource/scopes/{scope_type}/{scope_id}/dashboard
    → linked dashboard + panels (each panel preset executes with scope_id)   # rendered natively by Web UI
```

REST v2 tree. The metric catalog and dashboard/panel/link each have an admin CRUD surface.

### (e) Permission — scoped operation

Read permission is **treated as a scoped operation under virtual_scope RBAC**. Since `(scope_type,
scope_id)` is itself the permission scope, a metric query reduces to a read-permission check on that
scope (session/deployment = owner/project, resource_group/domain = admin, etc. are decided by RBAC
policy). No separate permission axis is introduced for metrics.

### (f) Applications (thin)

Thin applications of the general mechanism only — no separate query builder / SoT design.

- **session instant set ≈ existing `live_stat`**: served as the session scope's instant MetricSet.
  Replace the hardcoded `live_stat` queries with catalog bindings (joins with BA-6114, removal of
  `ValkeyStatClient`).
- **Monthly usage**: live/range via this API; billing-grade monthly aggregation continues to expose
  the `resource_usage_history` buckets as the SoT. **No queries are hardcoded in code.** Removal of the
  four legacy endpoints is delegated to BA-6449.

## Decision Summary

| Decision | Content |
|----------|---------|
| Catalog | Store scope↔metric bindings in **stored tables (generalized)**. Adding a metric/scope = adding data. No hardcoded queries |
| Labels | scope→series resolved by passing `scope_id` as `id` at query time → **no Prometheus label extension** |
| Selection axis | **Scope only**. Runtime-variant axis dropped |
| Permission | **Scoped operation** (virtual_scope RBAC) — no separate permission axis |
| SLA | Just a **stored metric entry** mapped to a scope_type (not a design problem) |
| Applications (live_stat/monthly) | Thin applications of the general mechanism. No separate query builder / SoT debate |
| Dashboard | A **separate structure** from the metric catalog: `dashboard` 1:N `panel` + scope↔dashboard link. Web UI native render (Grafana provisioning out of scope) |
| Management | Both the metric catalog and dashboards use **fixed seed + admin CRUD** |

## Out of Scope

- Long-retention TSDB (Thanos/Mimir) and other infrastructure layers.
- Prometheus label strategy / cardinality tuning (replaced by the stored catalog).

## References

- [BEP-1045](BEP-1045-prometheus-client-extraction-and-querier-interface-abstraction.md) · [BEP-1050](BEP-1050-prometheus-query-preset-system.md) · [BEP-1026](BEP-1026-fair-share-scheduler.md) · [BEP-1025](BEP-1025-server-side-csv-export.md)
- Code: `agent/metrics/metric.py`, `manager/clients/prometheus/*`, `sokovan/deployment/route/executor.py`, `repositories/resource_usage_history/`, `example-prometheus-query-presets.json`
