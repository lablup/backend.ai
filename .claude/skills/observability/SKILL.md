---
name: observability
description: Observe Backend.AI logs, metrics, and traces during local development via the Grafana MCP (Loki logs, Prometheus metrics, Tempo traces, Pyroscope profiles). Use after restarting a service to verify behavior instead of tailing console output.
invoke_method: automatic
auto_execute: false
enabled: true
---

# Observability — Logs & Metrics During Development

The local halfstack ships a full observability stack. Services emit logs/traces over
OTEL (`[otel] enabled = true` in `manager.toml` / `agent.toml` / `storage-proxy.toml`),
so logs land in Loki and metrics in Prometheus automatically. **Query them through the
Grafana MCP (`grafana` server in `.mcp.json`)** — this is the single source of truth for
runtime logs and metrics during development. The MCP runs as a resident container
(`backendai-half-grafana-mcp`, streamable-http at `http://localhost:3001/mcp`) inside the
`observability` profile, so `.mcp.json` just points Claude at that URL.

## Stack

| Service | URL | Datasource UID | Purpose |
|---------|-----|----------------|---------|
| Grafana | http://localhost:3000 (`backend` / `develove`) | — | UI / MCP target |
| Grafana MCP | http://localhost:3001/mcp | — | MCP server Claude connects to |
| Loki | http://localhost:3100 | `loki_ds_001` | Logs |
| Prometheus | http://localhost:9090 | `prom_ds_001` | Metrics |
| Tempo | http://localhost:3200 | `tempo_ds_001` | Traces |
| Pyroscope | http://localhost:4040 | `pyroscope_ds_001` | Profiles |

If these containers are not running (including the MCP), bring up the observability
profile — see `/halfstack`.

Log streams are labelled by `service_name` (`manager`, `agent`, …). Confirm what is
flowing with the Loki label-values tool before querying.

## Grafana MCP — Common Queries

Use the `grafana` MCP tools (e.g. `list_datasources`, `query_loki_logs`,
`query_prometheus`, `list_loki_label_values`, `search_dashboards`). Verify exact tool
names/params from the MCP itself; the queries below are what you pass.

**Logs (Loki / LogQL)** — datasource `loki_ds_001`:

```logql
{service_name="manager"}                       # recent manager logs
{service_name="manager"} |= "error"            # errors only
{service_name="agent"} | json | level="ERROR"  # structured (JSON) filter
{service_name="manager"} |= "<request-id>"     # trace one request end-to-end
```

**Metrics (Prometheus / PromQL)** — datasource `prom_ds_001`:

```promql
up                                                     # which targets are healthy
backendai_api_request_count                            # REST request counter
rate(backendai_api_request_count[1m])                  # request rate
backendai_api_request_duration_sec_bucket              # API latency histogram
backendai_graphql_request_count                        # GraphQL operation counter
```

Metric definitions live in `src/ai/backend/common/metrics/metric.py`
(`backendai_api_request_*`, `backendai_graphql_request_*`); component-specific metrics
under `src/ai/backend/{manager,agent,storage}/metrics/`.

**Dashboards / traces / profiles:** the pre-built dashboard is provisioned from
`grafana-dashboards/dashboard.json` (discover via `search_dashboards`). Tempo
(`tempo_ds_001`) holds distributed traces; Pyroscope (`pyroscope_ds_001`) holds profiles.

## Standard Verification Loop

After a code change:

1. Restart the affected service — `./dev restart mgr` (see `/local-dev`).
2. Exercise it — e.g. a `./bai` call (see `/bai-cli`).
3. **Observe via Grafana MCP**: query Loki for that `service_name` to confirm the request
   ran without errors, and Prometheus to confirm the expected metric moved.

This replaces tailing console output — always confirm runtime behavior through the MCP.

## Related Skills

- `/local-dev` — Restart services before observing.
- `/bai-cli` — Exercise the API, then verify logs/metrics here.
- `/halfstack` — Bring up / inspect the observability containers.
