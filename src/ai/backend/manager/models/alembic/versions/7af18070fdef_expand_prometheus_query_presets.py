"""expand_prometheus_query_presets

Revision ID: 7af18070fdef
Revises: 0113c63f3261
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
down_revision = "0113c63f3261"
branch_labels = None
depends_on = None

# Matched by name because the previous seed migration generated UUIDs at insert
# time (uuid_generate_v4), so the row id differs per environment.
CONTAINER_RENAMES: list[dict[str, Any]] = [
    {
        "old_name": "container_gauge",
        "new_name": "Per-Kernel Resource Metric — Instant Value (sum)",
        "description": "Instant value of the per-kernel resource utilization gauge, summed across the selected grouping",
        "rank": 100,
    },
    {
        "old_name": "container_diff",
        "new_name": "Per-Kernel Resource Metric — 5-Minute Rate (sum)",
        "description": "Per-second rate of the per-kernel resource utilization gauge over a 5-minute window, summed across the selected grouping",
        "rank": 200,
    },
]

CONTAINER_OPTIONS = json.dumps({
    "filter_labels": [
        "container_metric_name",
        "kernel_id",
        "session_id",
        "agent_id",
        "user_id",
        "project_id",
        "value_type",
    ],
    "group_labels": [
        "kernel_id",
        "session_id",
        "agent_id",
        "user_id",
        "project_id",
        "value_type",
    ],
})

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

# vLLM presets were never seeded into production DBs by a previous migration,
# but the example fixture seeds 5 of these ids under legacy names. All 14 rows
# are upserted by id, so both production and fixture-seeded DBs converge.
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

VLLM_OPTIONS = json.dumps({
    "filter_labels": ["deployment_id"],
    "group_labels": ["deployment_id"],
})


def _seed_category(conn: sa.Connection, name: str, description: str) -> uuid.UUID:
    # Insert only if the category is missing (name is unique), letting the DB
    # generate the id, then return whichever id is now in place — the existing
    # one if it was already seeded, otherwise the freshly generated one.
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                INSERT INTO prometheus_query_preset_categories (name, description)
                SELECT :name, :description
                WHERE NOT EXISTS (
                    SELECT 1 FROM prometheus_query_preset_categories
                    WHERE name = CAST(:name AS varchar)
                )
            """)
        ),
        parameters={
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


def _upsert_presets(
    conn: sa.Connection,
    presets: list[dict[str, Any]],
    category_id: uuid.UUID,
    options: str,
) -> None:
    # Upsert by id (the table's only unique key): environments seeded from the
    # example fixture already hold these ids under their old names, so a plain
    # insert would hit the primary key. ON CONFLICT converges those rows to the
    # new definitions, while fresh production DBs simply insert.
    for preset in presets:
        conn.execute(
            sa.text(
                textwrap.dedent("""\
                    INSERT INTO prometheus_query_presets
                        (id, name, description, rank, category_id,
                         metric_name, query_template, time_window, options)
                    VALUES (CAST(:id AS uuid), :name, :description, :rank,
                            CAST(:category_id AS uuid),
                            :metric_name, :query_template, :time_window,
                            CAST(:options AS jsonb))
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        rank = EXCLUDED.rank,
                        category_id = EXCLUDED.category_id,
                        metric_name = EXCLUDED.metric_name,
                        query_template = EXCLUDED.query_template,
                        time_window = EXCLUDED.time_window,
                        options = EXCLUDED.options
                """)
            ),
            parameters={
                **preset,
                "category_id": str(category_id),
                "options": options,
            },
        )


def _rename_presets(
    conn: sa.Connection, renames: list[dict[str, Any]], category_id: uuid.UUID
) -> None:
    # Rename existing seeded presets only if the row is still in its original
    # state (name unchanged), preserving any user customization.
    for rename in renames:
        conn.execute(
            sa.text(
                textwrap.dedent("""\
                    UPDATE prometheus_query_presets
                    SET name = :new_name,
                        description = :description,
                        rank = :rank,
                        category_id = CAST(:category_id AS uuid)
                    WHERE name = CAST(:old_name AS varchar)
                """)
            ),
            parameters={
                **rename,
                "category_id": str(category_id),
            },
        )


def _delete_presets(conn: sa.Connection, names: list[str]) -> None:
    for name in names:
        conn.execute(
            sa.text("DELETE FROM prometheus_query_presets WHERE name = CAST(:name AS varchar)"),
            parameters={"name": name},
        )


def upgrade() -> None:
    conn = op.get_bind()

    container_category_id = _seed_category(
        conn,
        name="container",
        description="Container-level utilization metrics collected by Backend.AI agents",
    )
    vllm_category_id = _seed_category(
        conn,
        name="vllm-inference",
        description="vLLM inference runtime metrics scraped from model serving endpoints",
    )

    _rename_presets(conn, renames=CONTAINER_RENAMES, category_id=container_category_id)

    # Drop container_rate: its sum(rate)/5.0 normalization doesn't compose with
    # the new avg/min/max variants.
    _delete_presets(conn, names=["container_rate"])

    _upsert_presets(
        conn,
        presets=CONTAINER_INSERTIONS,
        category_id=container_category_id,
        options=CONTAINER_OPTIONS,
    )
    _upsert_presets(
        conn,
        presets=VLLM_INSERTIONS,
        category_id=vllm_category_id,
        options=VLLM_OPTIONS,
    )


def downgrade() -> None:
    # Data-only migration: seeded rows are not removed on downgrade
    # to avoid deleting user-modified presets that share the same identifiers.
    pass
