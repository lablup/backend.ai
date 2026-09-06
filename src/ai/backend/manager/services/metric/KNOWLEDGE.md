---
name: manager-services-metric
type: design-rationale
description: which shape each container-utilization read takes, why the gates differ per operation, why live stats answer for the session, and the processor field names
scope: src/ai/backend/manager/services/metric
keywords:
  - MetricProcessors
  - SearchUserContainerMetricsAction
  - GlobalSearchContainerMetricsAction
  - PublicSearchContainerMetricMetadataAction
  - BatchGetKernelLiveStatsAction
  - LookupBulkKernelOwnerAction
  - PROMETHEUS_QUERY_PRESET_ENTITY_TYPE
  - PublicActionProcessor
  - Concern.METRIC
sources:
  - src/ai/backend/manager/services/metric
  - src/ai/backend/manager/services/prometheus_query_preset
generated:
  by: claude-code/opus-5
  at: 2026-08-23
status: draft
---

# Container utilization (`services/metric`)

This domain reads the time series Prometheus answers, not a table. The storage layer is
`repositories/metric`, and under it sits the metric store rather than the DB.

## What an operation names decides its shape

- The metric names name no row, so that read is global-shaped.
- The time series splits in two by whose containers it reads. A caller's own metrics
  name that user and are single-entity shaped; reading another user, or every one of
  them, names nobody and stays global. The call site picks between them by comparing the
  target user with the caller.
- Live stats are read per kernel the caller names. A kernel is a row rather than an
  entity, so that read is bulk-field shaped: the sessions owning those kernels are read
  first and each answers for it.
- All four declare `operation_type() == SEARCH`. However far the labels narrow it, it is
  a filtered query.

## The gate differs per operation

- The utilization panel is where an ordinary user looks at their own resources, so a
  superadmin gate would take the feature away. A caller's own metrics pass on READ
  permission over that user instead.
- The metric names check authentication only. The legacy wiring had no gate at all; the
  authentication check arrived with the move to public.
- Another user's metrics moved from a role comparison written by hand in the legacy
  resolver to the global gate. A super admin passes, and so does the MONITOR role on a
  read.

## The entity answering splits three ways

| Operation | Entity answering | Why |
|---|---|---|
| A user's own time series | user | It reads the containers of the user the labels name |
| Time series across users, and the metric names | prometheus query preset | A query fixed in code. It differs from a stored preset row only in being built in rather than a row |
| Kernel live stats | session | A kernel is a row of its session, so `LookupBulkKernelOwnerAction` reads that session and the session answers |

- A user's own metrics are wired through `ProcessorGroup.single_entity` on the user group
  under `Concern.METRIC`.
- The cross-user series and the metric names share the preset domain's group, behind the
  global gate and the public gate respectively.
- Live stats are wired through `ProcessorGroup.bulk_field`. The same shape is used by
  `BatchGetKernelResourceAllocationAction`.
- The processor fields are `search_user_container_metrics` (own metrics), `global_search`
  (cross-user), `metadata_public_search` (metric names) and `batch_get_kernel_live_stats`
  (live stats).

## The service stays

- All four methods call an external system (Prometheus), so none of them can move down to
  the generic ops services. They are not pass-through operations forwarding a repository
  spec.
