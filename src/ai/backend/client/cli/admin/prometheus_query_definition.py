import sys
from collections.abc import Sequence

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext

from . import admin


def _parse_label_filters(labels: tuple[str, ...]) -> Sequence[object]:
    from ai.backend.common.dto.manager.prometheus_query_preset import MetricLabelEntry

    parsed: list[MetricLabelEntry] = []
    for label in labels:
        if "=" not in label:
            print(f"Invalid label format: {label} (expected key=value)", file=sys.stderr)
            sys.exit(ExitCode.INVALID_ARGUMENT)
        key, value = label.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            print(
                f"Invalid label key or value: {label} (both key and value must be non-empty)",
                file=sys.stderr,
            )
            sys.exit(ExitCode.INVALID_ARGUMENT)
        parsed.append(MetricLabelEntry(key=key, value=value))
    return parsed


@admin.group()
def prometheus_query_definition() -> None:
    """Prometheus query definition administration commands."""


@prometheus_query_definition.command()
@pass_ctx_obj
@click.option("--filter-name", type=str, default=None, help="Filter by name (contains match).")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--limit", type=int, default=20, help="Maximum items to return.")
def search(ctx: CLIContext, filter_name: str | None, offset: int, limit: int) -> None:
    """Search prometheus query definitions."""
    import asyncio

    from ai.backend.client.config import get_config
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.registry import BackendAIClientRegistry
    from ai.backend.common.dto.manager.prometheus_query_preset import (
        QueryDefinitionFilter,
        SearchQueryDefinitionsRequest,
    )
    from ai.backend.common.dto.manager.query import StringFilter

    async def _run() -> None:
        api_config = get_config()
        v2_config = ClientConfig.from_v1_config(api_config)
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        registry = await BackendAIClientRegistry.create(v2_config, auth)
        try:
            name_filter = None
            if filter_name is not None:
                name_filter = StringFilter(contains=filter_name)
            request = SearchQueryDefinitionsRequest(
                filter=QueryDefinitionFilter(name=name_filter) if name_filter else None,
                offset=offset,
                limit=limit,
            )
            response = await registry.prometheus_query_definition.search(request)
            if not response.items:
                print("No definitions found.")
                return
            for definition in response.items:
                print(f"ID: {definition.id}")
                print(f"  Name: {definition.name}")
                print(f"  Metric: {definition.metric_name}")
                print(f"  Time Window: {definition.time_window or '-'}")
                print(f"  Created: {definition.created_at}")
                print()
            print(
                f"Total: {response.pagination.total}"
                f" (offset={response.pagination.offset}, limit={response.pagination.limit})"
            )
        finally:
            await registry.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
def info(ctx: CLIContext, definition_id: str) -> None:
    """Show details of a prometheus query definition."""
    import asyncio
    from uuid import UUID

    from ai.backend.client.config import get_config
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.registry import BackendAIClientRegistry

    async def _run() -> None:
        api_config = get_config()
        v2_config = ClientConfig.from_v1_config(api_config)
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        registry = await BackendAIClientRegistry.create(v2_config, auth)
        try:
            response = await registry.prometheus_query_definition.get(UUID(definition_id))
            d = response.item
            print(f"ID: {d.id}")
            print(f"Name: {d.name}")
            print(f"Metric Name: {d.metric_name}")
            print(f"Query Template: {d.query_template}")
            print(f"Time Window: {d.time_window or '-'}")
            print(f"Filter Labels: {d.options.filter_labels}")
            print(f"Group Labels: {d.options.group_labels}")
            print(f"Created: {d.created_at}")
            print(f"Updated: {d.updated_at}")
        finally:
            await registry.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.option("--name", type=str, required=True, help="Definition name.")
@click.option("--metric-name", type=str, required=True, help="Prometheus metric name.")
@click.option("--query-template", type=str, required=True, help="PromQL template.")
@click.option("--time-window", type=str, default=None, help="Default time window (e.g. 5m).")
@click.option(
    "--filter-labels",
    type=str,
    default="",
    help="Comma-separated allowed filter label keys.",
)
@click.option(
    "--group-labels",
    type=str,
    default="",
    help="Comma-separated allowed group-by label keys.",
)
def add(
    ctx: CLIContext,
    name: str,
    metric_name: str,
    query_template: str,
    time_window: str | None,
    filter_labels: str,
    group_labels: str,
) -> None:
    """Create a new prometheus query definition."""
    import asyncio

    from ai.backend.client.cli.pretty import print_done
    from ai.backend.client.config import get_config
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.registry import BackendAIClientRegistry
    from ai.backend.common.dto.manager.prometheus_query_preset import (
        CreateQueryDefinitionOptionsRequest,
        CreateQueryDefinitionRequest,
    )

    async def _run() -> None:
        api_config = get_config()
        v2_config = ClientConfig.from_v1_config(api_config)
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        registry = await BackendAIClientRegistry.create(v2_config, auth)
        try:
            fl = [s.strip() for s in filter_labels.split(",") if s.strip()] if filter_labels else []
            gl = [s.strip() for s in group_labels.split(",") if s.strip()] if group_labels else []
            request = CreateQueryDefinitionRequest(
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                options=CreateQueryDefinitionOptionsRequest(
                    filter_labels=fl,
                    group_labels=gl,
                ),
            )
            response = await registry.prometheus_query_definition.create(request)
            print(f"Created definition: {response.item.id}")
            print_done("Done.")
        finally:
            await registry.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
@click.option("--name", type=str, default=None, help="New definition name.")
@click.option("--metric-name", type=str, default=None, help="New Prometheus metric name.")
@click.option("--query-template", type=str, default=None, help="New PromQL template.")
@click.option("--time-window", type=str, default=None, help="New default time window.")
@click.option(
    "--filter-labels",
    type=str,
    default=None,
    help="Comma-separated allowed filter label keys.",
)
@click.option(
    "--group-labels",
    type=str,
    default=None,
    help="Comma-separated allowed group-by label keys.",
)
def modify(
    ctx: CLIContext,
    definition_id: str,
    name: str | None,
    metric_name: str | None,
    query_template: str | None,
    time_window: str | None,
    filter_labels: str | None,
    group_labels: str | None,
) -> None:
    """Modify an existing prometheus query definition."""
    import asyncio
    from uuid import UUID

    from ai.backend.client.cli.pretty import print_done
    from ai.backend.client.config import get_config
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.registry import BackendAIClientRegistry
    from ai.backend.common.dto.manager.prometheus_query_preset import (
        ModifyQueryDefinitionOptionsRequest,
        ModifyQueryDefinitionRequest,
    )

    if all(
        v is None
        for v in (name, metric_name, query_template, time_window, filter_labels, group_labels)
    ):
        print("At least one field must be specified to modify.", file=sys.stderr)
        sys.exit(ExitCode.INVALID_ARGUMENT)

    async def _run() -> None:
        api_config = get_config()
        v2_config = ClientConfig.from_v1_config(api_config)
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        registry = await BackendAIClientRegistry.create(v2_config, auth)
        try:
            fl = (
                [s.strip() for s in filter_labels.split(",") if s.strip()]
                if filter_labels is not None
                else None
            )
            gl = (
                [s.strip() for s in group_labels.split(",") if s.strip()]
                if group_labels is not None
                else None
            )
            options = None
            if fl is not None or gl is not None:
                options = ModifyQueryDefinitionOptionsRequest(
                    filter_labels=fl,
                    group_labels=gl,
                )
            request = ModifyQueryDefinitionRequest(
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                options=options,
            )
            response = await registry.prometheus_query_definition.modify(
                UUID(definition_id), request
            )
            print(f"Modified definition: {response.item.id}")
            print_done("Done.")
        finally:
            await registry.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
@click.confirmation_option(prompt="Are you sure you want to delete this definition?")
def delete(ctx: CLIContext, definition_id: str) -> None:
    """Delete a prometheus query definition."""
    import asyncio
    from uuid import UUID

    from ai.backend.client.cli.pretty import print_done
    from ai.backend.client.config import get_config
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.registry import BackendAIClientRegistry

    async def _run() -> None:
        api_config = get_config()
        v2_config = ClientConfig.from_v1_config(api_config)
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        registry = await BackendAIClientRegistry.create(v2_config, auth)
        try:
            await registry.prometheus_query_definition.delete(UUID(definition_id))
            print(f"Deleted definition: {definition_id}")
            print_done("Done.")
        finally:
            await registry.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
@click.option("--start", type=str, default=None, help="Start time (ISO8601).")
@click.option("--end", type=str, default=None, help="End time (ISO8601).")
@click.option("--step", type=str, default=None, help="Step duration (e.g. 60s).")
@click.option(
    "--label",
    "labels",
    multiple=True,
    type=str,
    help="Label filter in key=value format (repeatable).",
)
@click.option(
    "--group-labels",
    type=str,
    default=None,
    help="Comma-separated group labels.",
)
@click.option("--time-window", type=str, default=None, help="Time window override.")
def execute(
    ctx: CLIContext,
    definition_id: str,
    start: str | None,
    end: str | None,
    step: str | None,
    labels: tuple[str, ...],
    group_labels: str | None,
    time_window: str | None,
) -> None:
    """Execute a prometheus query definition."""
    import asyncio
    import json
    from uuid import UUID

    from ai.backend.client.config import get_config
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.registry import BackendAIClientRegistry
    from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
    from ai.backend.common.dto.manager.prometheus_query_preset import (
        ExecuteQueryDefinitionOptionsRequest,
        ExecuteQueryDefinitionRequest,
    )

    async def _run() -> None:
        api_config = get_config()
        v2_config = ClientConfig.from_v1_config(api_config)
        auth = HMACAuth(api_config.access_key, api_config.secret_key)
        registry = await BackendAIClientRegistry.create(v2_config, auth)
        try:
            filter_label_entries = _parse_label_filters(labels)

            group_labels_list: list[str] = []
            if group_labels is not None:
                group_labels_list = [gl.strip() for gl in group_labels.split(",") if gl.strip()]

            time_range: QueryTimeRange | None = None
            if start is not None and end is not None and step is not None:
                time_range = QueryTimeRange(start=start, end=end, step=step)

            request = ExecuteQueryDefinitionRequest(
                options=ExecuteQueryDefinitionOptionsRequest(
                    filter_labels=filter_label_entries,
                    group_labels=group_labels_list,
                ),
                time_window=time_window,
                time_range=time_range,
            )
            response = await registry.prometheus_query_definition.execute(
                UUID(definition_id), request
            )
            print(json.dumps(response.model_dump(mode="json"), indent=2, default=str))
        finally:
            await registry.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)
