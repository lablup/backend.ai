---
name: observability
description: Observe Backend.AI logs, metrics, and traces during local development via the Grafana MCP (Loki logs, Prometheus metrics, Tempo traces, Pyroscope profiles). Use after restarting a service to verify behavior instead of tailing console output.
invoke_method: automatic
auto_execute: false
enabled: true
tags:
  - observability
  - grafana
  - logs
  - metrics
  - traces
---

# Observability: logs and metrics during development

The local halfstack ships a full observability stack. Services emit logs and traces over OTEL (`[otel] enabled = true` in `manager.toml`, `agent.toml` and `storage-proxy.toml`), so logs land in Loki and metrics in Prometheus automatically. Query them through the Grafana MCP (the `grafana` server in `.mcp.json`), the reference for runtime logs and metrics during development. The MCP runs as a resident container (`backendai-half-grafana-mcp`, streamable-http at `http://localhost:3001/mcp`) inside the `observability` profile, so `.mcp.json` only points Claude at that URL.

## Stack

| Service | URL | Datasource UID | Purpose |
|---|---|---|---|
| Grafana | http://localhost:3000 (`backend` / `develove`) | none | UI and MCP target |
| Grafana MCP | http://localhost:3001/mcp | none | MCP server Claude connects to |
| Loki | http://localhost:3100 | `loki_ds_001` | Logs |
| Prometheus | http://localhost:9090 | `prom_ds_001` | Metrics |
| Tempo | http://localhost:3200 | `tempo_ds_001` | Traces |
| Pyroscope | http://localhost:4040 | `pyroscope_ds_001` | Profiles |

When these containers are not running, including the MCP, start the observability profile. See `/halfstack`.

Log streams are labelled by `service_name` (`manager`, `agent`, and so on). Confirm what is flowing with the Loki label-values tool before querying.

## Grafana MCP queries

Use the `grafana` MCP tools, for example `list_datasources`, `query_loki_logs`, `query_prometheus`, `list_loki_label_values` and `search_dashboards`. Check the exact tool names and parameters in the MCP itself. The queries below are what you pass.

Logs (Loki and LogQL), datasource `loki_ds_001`:

```logql
{service_name="manager"}                       # recent manager logs
{service_name="manager"} |= "error"            # errors only
{service_name="agent"} | json | level="ERROR"  # structured (JSON) filter
{service_name="manager"} |= "<request-id>"     # trace one request end to end
```

Metrics (Prometheus and PromQL), datasource `prom_ds_001`:

```promql
up                                                     # which targets are healthy
backendai_api_request_count                            # REST request counter
rate(backendai_api_request_count[1m])                  # request rate
backendai_api_request_duration_sec_bucket              # API latency histogram
backendai_graphql_request_count                        # GraphQL operation counter
```

Metric definitions live in `src/ai/backend/common/metrics/metric.py` (`backendai_api_request_*`, `backendai_graphql_request_*`). Component-specific metrics live under `src/ai/backend/{manager,agent,storage}/metrics/`.

Dashboards, traces and profiles: the pre-built dashboard is provisioned from `grafana-dashboards/dashboard.json`; discover it via `search_dashboards`. Tempo (`tempo_ds_001`) holds distributed traces and Pyroscope (`pyroscope_ds_001`) holds profiles.

## Standard verification loop

After a code change:

1. Restart the affected service with `./dev restart mgr`. See `/local-dev`.
2. Exercise it, for example with a `./bai` call. See `/bai-cli`.
3. Observe through the Grafana MCP. Query Loki for that `service_name` to confirm the request ran without errors, and Prometheus to confirm the expected metric moved.

This replaces tailing console output. Confirm runtime behavior through the MCP.

## Related documents

- `/local-dev` - Restart services before observing
- `/bai-cli` - Exercise the API, then verify logs and metrics here
- `/halfstack` - Start and inspect the observability containers
