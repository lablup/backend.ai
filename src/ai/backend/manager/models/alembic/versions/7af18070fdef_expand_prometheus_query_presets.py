"""expand_prometheus_query_presets

Revision ID: 7af18070fdef
Revises: bee1c0de01a1
Create Date: 2026-05-27 00:00:00.000000

# Part of: 26.3.0 (main)
"""

import json
import textwrap
import uuid
from typing import Any, cast

import sqlalchemy as sa
from alembic import op

revision = "7af18070fdef"
down_revision = "bee1c0de01a1"
branch_labels = None
depends_on = None

CONTAINER_CATEGORY_ID = uuid.UUID("4f1e6c43-8a52-4d6e-9b7c-1c8a2f3d9b40")
CONTAINER_CATEGORY_NAME = "container"
CONTAINER_CATEGORY_DESCRIPTION = (
    "Container-level utilization metrics collected by Backend.AI agents"
)

VLLM_CATEGORY_ID = uuid.UUID("6a2d8f19-7b34-4e0c-9f15-3e8b4d2a7c81")
VLLM_CATEGORY_NAME = "vllm-inference"
VLLM_CATEGORY_DESCRIPTION = "vLLM inference runtime metrics scraped from model serving endpoints"

CONTAINER_FILTER_LABELS = [
    "container_metric_name",
    "kernel_id",
    "session_id",
    "agent_id",
    "user_id",
    "project_id",
    "value_type",
]
CONTAINER_GROUP_LABELS = [
    "kernel_id",
    "session_id",
    "agent_id",
    "user_id",
    "project_id",
    "value_type",
]
CONTAINER_OPTIONS = json.dumps({
    "filter_labels": CONTAINER_FILTER_LABELS,
    "group_labels": CONTAINER_GROUP_LABELS,
})

VLLM_OPTIONS = json.dumps({
    "filter_labels": ["deployment_id"],
    "group_labels": ["deployment_id"],
})

# (old_name, new_name, new_description, new_rank)
# Matched by name because the previous seed migration generated UUIDs at insert
# time (server_default uuid_generate_v4), so the row id differs per environment.
CONTAINER_RENAMES: list[tuple[str, str, str, int]] = [
    (
        "container_gauge",
        "Per-Kernel Resource Metric — Instant Value (sum)",
        "Instant value of the per-kernel resource utilization gauge, summed across the selected grouping",
        100,
    ),
    (
        "container_diff",
        "Per-Kernel Resource Metric — 5-Minute Rate (sum)",
        "Per-second rate of the per-kernel resource utilization gauge over a 5-minute window, summed across the selected grouping",
        200,
    ),
]

# old_name — only deleted if the row is still in its original seeded state.
CONTAINER_DELETIONS: list[str] = ["container_rate"]

CONTAINER_INSERTIONS: list[dict[str, Any]] = [
    {
        "id": "106513b9-0a8b-4b07-9820-4ce541441509",
        "name": "Per-Kernel Resource Metric — Instant Value (avg)",
        "description": "Instant value of the per-kernel resource utilization gauge, averaged across the selected grouping",
        "rank": 110,
        "metric_name": "backendai_container_utilization",
        "query_template": "avg by ({group_by})(backendai_container_utilization{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "0d8023df-807b-4fe1-953a-6bfb3870a9e4",
        "name": "Per-Kernel Resource Metric — Instant Value (max)",
        "description": "Instant value of the per-kernel resource utilization gauge, maximum across the selected grouping",
        "rank": 120,
        "metric_name": "backendai_container_utilization",
        "query_template": "max by ({group_by})(backendai_container_utilization{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "8d97af1c-67d5-4ef6-af30-3cfe4689dc99",
        "name": "Per-Kernel Resource Metric — Instant Value (min)",
        "description": "Instant value of the per-kernel resource utilization gauge, minimum across the selected grouping",
        "rank": 130,
        "metric_name": "backendai_container_utilization",
        "query_template": "min by ({group_by})(backendai_container_utilization{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "234c0e84-fe6f-46ec-87b9-d177cb1c9b85",
        "name": "Per-Kernel Resource Metric — 5-Minute Rate (avg)",
        "description": "Per-second rate of the per-kernel resource utilization gauge over a 5-minute window, averaged across the selected grouping",
        "rank": 210,
        "metric_name": "backendai_container_utilization",
        "query_template": "avg by ({group_by})(rate(backendai_container_utilization{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
    {
        "id": "40b3b678-ab2a-4dcc-9045-120bd208a19f",
        "name": "Per-Kernel Resource Metric — 5-Minute Rate (max)",
        "description": "Per-second rate of the per-kernel resource utilization gauge over a 5-minute window, maximum across the selected grouping",
        "rank": 220,
        "metric_name": "backendai_container_utilization",
        "query_template": "max by ({group_by})(rate(backendai_container_utilization{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
    {
        "id": "537ffea7-dc84-457e-b663-52e21be34085",
        "name": "Per-Kernel Resource Metric — 5-Minute Rate (min)",
        "description": "Per-second rate of the per-kernel resource utilization gauge over a 5-minute window, minimum across the selected grouping",
        "rank": 230,
        "metric_name": "backendai_container_utilization",
        "query_template": "min by ({group_by})(rate(backendai_container_utilization{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
]

# vLLM presets were never seeded into production DBs by a previous migration.
# All 14 rows are inserted here (idempotent by id NOT EXISTS).
VLLM_INSERTIONS: list[dict[str, Any]] = [
    {
        "id": "2f0634e3-a976-4eeb-ba01-1e1829965453",
        "name": "vLLM Inflight Requests (sum)",
        "description": "Number of requests currently being processed by vLLM, summed across the selected grouping",
        "rank": 300,
        "metric_name": "vllm:num_requests_running",
        "query_template": "sum by ({group_by})(vllm:num_requests_running{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "52ca4304-4f61-414c-a69f-66a70b25a637",
        "name": "vLLM Inflight Requests (avg)",
        "description": "Number of requests currently being processed by vLLM, averaged across the selected grouping",
        "rank": 310,
        "metric_name": "vllm:num_requests_running",
        "query_template": "avg by ({group_by})(vllm:num_requests_running{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "0520d769-0240-46db-a8ac-e557f7739d56",
        "name": "vLLM Inflight Requests (max)",
        "description": "Number of requests currently being processed by vLLM, maximum across the selected grouping",
        "rank": 320,
        "metric_name": "vllm:num_requests_running",
        "query_template": "max by ({group_by})(vllm:num_requests_running{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "2a0939c6-b634-4f1e-ac8c-8738d7bbc244",
        "name": "vLLM Queued Requests (sum)",
        "description": "Number of requests waiting in the vLLM queue, summed across the selected grouping",
        "rank": 400,
        "metric_name": "vllm:num_requests_waiting",
        "query_template": "sum by ({group_by})(vllm:num_requests_waiting{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "598d0148-c3d5-4282-b31c-ea05e7fca98c",
        "name": "vLLM Queued Requests (avg)",
        "description": "Number of requests waiting in the vLLM queue, averaged across the selected grouping",
        "rank": 410,
        "metric_name": "vllm:num_requests_waiting",
        "query_template": "avg by ({group_by})(vllm:num_requests_waiting{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "baf09246-9bbd-4368-91fd-76c6f97233d4",
        "name": "vLLM Queued Requests (max)",
        "description": "Number of requests waiting in the vLLM queue, maximum across the selected grouping",
        "rank": 420,
        "metric_name": "vllm:num_requests_waiting",
        "query_template": "max by ({group_by})(vllm:num_requests_waiting{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "00c6467d-58da-4285-9166-fa36404f2012",
        "name": "vLLM GPU KV Cache Usage Ratio (avg)",
        "description": "GPU KV cache usage ratio (0.0-1.0) reported by vLLM, averaged across the selected grouping",
        "rank": 500,
        "metric_name": "vllm:gpu_cache_usage_perc",
        "query_template": "avg by ({group_by})(vllm:gpu_cache_usage_perc{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "4bed8110-4718-4300-a39d-d64a25e6aa6e",
        "name": "vLLM GPU KV Cache Usage Ratio (max)",
        "description": "GPU KV cache usage ratio (0.0-1.0) reported by vLLM, maximum across the selected grouping",
        "rank": 510,
        "metric_name": "vllm:gpu_cache_usage_perc",
        "query_template": "max by ({group_by})(vllm:gpu_cache_usage_perc{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "aab38882-1c45-40ae-bd71-d60e20a76849",
        "name": "vLLM GPU KV Cache Usage Ratio (min)",
        "description": "GPU KV cache usage ratio (0.0-1.0) reported by vLLM, minimum across the selected grouping",
        "rank": 520,
        "metric_name": "vllm:gpu_cache_usage_perc",
        "query_template": "min by ({group_by})(vllm:gpu_cache_usage_perc{{{labels}}})",
        "time_window": None,
    },
    {
        "id": "73f67248-497b-4794-a71a-562fcebc248a",
        "name": "vLLM Successful Requests per Second — 5-Minute Rate (sum)",
        "description": "Per-second rate of vLLM successful request completions over a 5-minute window, summed across the selected grouping",
        "rank": 600,
        "metric_name": "vllm:request_success_total",
        "query_template": "sum by ({group_by})(rate(vllm:request_success_total{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
    {
        "id": "4b4cf413-c00a-464d-8694-ab0de1eb0d6d",
        "name": "vLLM Successful Requests per Second — 5-Minute Rate (avg)",
        "description": "Per-second rate of vLLM successful request completions over a 5-minute window, averaged across the selected grouping",
        "rank": 610,
        "metric_name": "vllm:request_success_total",
        "query_template": "avg by ({group_by})(rate(vllm:request_success_total{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
    {
        "id": "0a4762f4-1eb9-46ff-96f2-ffaadcfc4957",
        "name": "vLLM Successful Requests per Second — 5-Minute Rate (max)",
        "description": "Per-second rate of vLLM successful request completions over a 5-minute window, maximum across the selected grouping",
        "rank": 620,
        "metric_name": "vllm:request_success_total",
        "query_template": "max by ({group_by})(rate(vllm:request_success_total{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
    {
        "id": "119da10b-23df-4579-8c8b-d6bff18ee1b8",
        "name": "vLLM End-to-End Request Latency — 5-Minute Average (avg)",
        "description": "End-to-end request latency averaged over a 5-minute window, averaged across the selected grouping",
        "rank": 700,
        "metric_name": "vllm:e2e_request_latency_seconds",
        "query_template": "avg by ({group_by})(rate(vllm:e2e_request_latency_seconds_sum{{{labels}}}[{window}]) / rate(vllm:e2e_request_latency_seconds_count{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
    {
        "id": "c658562f-6740-4347-ad1a-42bb76a848c9",
        "name": "vLLM End-to-End Request Latency — 5-Minute Average (max)",
        "description": "End-to-end request latency averaged over a 5-minute window, maximum across the selected grouping",
        "rank": 710,
        "metric_name": "vllm:e2e_request_latency_seconds",
        "query_template": "max by ({group_by})(rate(vllm:e2e_request_latency_seconds_sum{{{labels}}}[{window}]) / rate(vllm:e2e_request_latency_seconds_count{{{labels}}}[{window}]))",
        "time_window": "5m",
    },
]


def _seed_category(
    conn: sa.Connection, category_id: uuid.UUID, name: str, description: str
) -> uuid.UUID:
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                INSERT INTO prometheus_query_preset_categories (id, name, description)
                SELECT CAST(:id AS uuid), :name, :description
                WHERE NOT EXISTS (
                    SELECT 1 FROM prometheus_query_preset_categories
                    WHERE name = CAST(:name AS varchar)
                )
            """)
        ),
        parameters={
            "id": str(category_id),
            "name": name,
            "description": description,
        },
    )
    return cast(
        uuid.UUID,
        conn.execute(
            sa.text("SELECT id FROM prometheus_query_preset_categories WHERE name = :name"),
            parameters={"name": name},
        ).scalar_one(),
    )


def _insert_presets(
    conn: sa.Connection,
    presets: list[dict[str, Any]],
    category_id: uuid.UUID,
    options: str,
) -> None:
    for preset in presets:
        conn.execute(
            sa.text(
                textwrap.dedent("""\
                    INSERT INTO prometheus_query_presets
                        (id, name, description, rank, category_id,
                         metric_name, query_template, time_window, options)
                    SELECT CAST(:id AS uuid), :name, :description, :rank,
                           CAST(:category_id AS uuid),
                           :metric_name, :query_template, :time_window,
                           CAST(:options AS jsonb)
                    WHERE NOT EXISTS (
                        SELECT 1 FROM prometheus_query_presets
                        WHERE name = CAST(:name AS varchar)
                    )
                """)
            ),
            parameters={
                **preset,
                "category_id": str(category_id),
                "options": options,
            },
        )


def upgrade() -> None:
    conn = op.get_bind()

    container_category_id = _seed_category(
        conn,
        CONTAINER_CATEGORY_ID,
        CONTAINER_CATEGORY_NAME,
        CONTAINER_CATEGORY_DESCRIPTION,
    )
    vllm_category_id = _seed_category(
        conn,
        VLLM_CATEGORY_ID,
        VLLM_CATEGORY_NAME,
        VLLM_CATEGORY_DESCRIPTION,
    )

    # Rename existing seeded presets only if the row is still in its original
    # state (name unchanged), preserving any user customization.
    for old_name, new_name, new_description, new_rank in CONTAINER_RENAMES:
        conn.execute(
            sa.text(
                textwrap.dedent("""\
                    UPDATE prometheus_query_presets
                    SET name = :new_name,
                        description = :new_description,
                        rank = :new_rank,
                        category_id = CAST(:category_id AS uuid)
                    WHERE name = CAST(:old_name AS varchar)
                """)
            ),
            parameters={
                "old_name": old_name,
                "new_name": new_name,
                "new_description": new_description,
                "new_rank": new_rank,
                "category_id": str(container_category_id),
            },
        )

    for old_name in CONTAINER_DELETIONS:
        conn.execute(
            sa.text(
                textwrap.dedent("""\
                    DELETE FROM prometheus_query_presets
                    WHERE name = CAST(:old_name AS varchar)
                """)
            ),
            parameters={"old_name": old_name},
        )

    _insert_presets(conn, CONTAINER_INSERTIONS, container_category_id, CONTAINER_OPTIONS)
    _insert_presets(conn, VLLM_INSERTIONS, vllm_category_id, VLLM_OPTIONS)


def downgrade() -> None:
    # Data-only migration: seeded rows are not removed on downgrade
    # to avoid deleting user-modified presets that share the same identifiers.
    pass
