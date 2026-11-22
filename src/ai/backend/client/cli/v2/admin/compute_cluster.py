"""Admin CLI commands for compute clusters (superadmin required)."""

from __future__ import annotations

import asyncio
import uuid
from typing import IO

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)

_STATUS_CHOICES = ("UNKNOWN", "ALIVE", "LOST")


@click.group()
def compute_cluster() -> None:
    """Compute cluster admin commands (superadmin required)."""


@compute_cluster.command()
@click.argument("compute_cluster_id", type=click.UUID)
def get(compute_cluster_id: uuid.UUID) -> None:
    """Get a compute cluster by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.compute_cluster.admin_get(compute_cluster_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@compute_cluster.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--name-contains", default=None, type=str, help="Filter by name (substring match).")
@click.option(
    "--status",
    default=None,
    type=click.Choice(_STATUS_CHOICES),
    help="Filter by status.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    status: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search compute clusters."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.compute_cluster.request import (
        ComputeClusterFilter,
        ComputeClusterOrder,
        SearchComputeClustersInput,
    )
    from ai.backend.common.dto.manager.v2.compute_cluster.types import (
        ComputeClusterOrderField,
        ComputeClusterStatus,
        ComputeClusterStatusFilter,
    )

    filter_dto: ComputeClusterFilter | None = None
    if name_contains is not None or status is not None:
        filter_dto = ComputeClusterFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            status=ComputeClusterStatusFilter(equals=ComputeClusterStatus(status))
            if status is not None
            else None,
        )
    orders = (
        parse_order_options(order_by, ComputeClusterOrderField, ComputeClusterOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.compute_cluster.admin_search(
                SearchComputeClustersInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@compute_cluster.command()
@click.option("--name", required=True, type=str, help="Unique compute cluster name.")
@click.option("--api-server", required=True, type=str, help="Kubernetes API server URL.")
@click.option(
    "--kubeconfig",
    "kubeconfig_file",
    required=True,
    type=click.File("r"),
    help="Path to the kubeconfig file (stored encrypted, never shown).",
)
@click.option("--description", default=None, type=str, help="Optional description.")
@click.option(
    "--namespace-prefix",
    default="bai-",
    show_default=True,
    type=str,
    help="Prefix of the namespaces created in the cluster.",
)
@click.option("--gateway-addr", default=None, type=str, help="Network gateway address.")
@click.option("--gateway-public-key", default=None, type=str, help="Gateway public key.")
def create(
    name: str,
    api_server: str,
    kubeconfig_file: IO[str],
    description: str | None,
    namespace_prefix: str,
    gateway_addr: str | None,
    gateway_public_key: str | None,
) -> None:
    """Register a compute cluster."""
    from ai.backend.common.dto.manager.v2.compute_cluster.request import (
        CreateComputeClusterInput,
    )

    input_ = CreateComputeClusterInput(
        name=name,
        description=description,
        api_server=api_server,
        kubeconfig=kubeconfig_file.read(),
        namespace_prefix=namespace_prefix,
        gateway_addr=gateway_addr,
        gateway_public_key=gateway_public_key,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.compute_cluster.admin_create(input_)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@compute_cluster.command()
@click.argument("compute_cluster_id", type=click.UUID)
@click.option("--description", default=None, type=str, help="Updated description.")
@click.option("--set-null-description", is_flag=True, help="Clear the current description.")
@click.option("--api-server", default=None, type=str, help="Updated API server URL.")
@click.option(
    "--kubeconfig",
    "kubeconfig_file",
    default=None,
    type=click.File("r"),
    help="Path to a replacement kubeconfig file.",
)
@click.option("--namespace-prefix", default=None, type=str, help="Updated namespace prefix.")
@click.option("--gateway-addr", default=None, type=str, help="Updated gateway address.")
@click.option("--set-null-gateway-addr", is_flag=True, help="Clear the gateway address.")
@click.option("--gateway-public-key", default=None, type=str, help="Updated gateway public key.")
@click.option("--set-null-gateway-public-key", is_flag=True, help="Clear the gateway public key.")
@click.option(
    "--status",
    default=None,
    type=click.Choice(_STATUS_CHOICES),
    help="Updated status.",
)
def update(
    compute_cluster_id: uuid.UUID,
    description: str | None,
    set_null_description: bool,
    api_server: str | None,
    kubeconfig_file: IO[str] | None,
    namespace_prefix: str | None,
    gateway_addr: str | None,
    set_null_gateway_addr: bool,
    gateway_public_key: str | None,
    set_null_gateway_public_key: bool,
    status: str | None,
) -> None:
    """Update a compute cluster."""
    from ai.backend.common.dto.manager.v2.compute_cluster.request import (
        UpdateComputeClusterInput,
    )
    from ai.backend.common.dto.manager.v2.compute_cluster.types import ComputeClusterStatus
    from ai.backend.common.tristate.unset import UNSET

    for value, flag, name in (
        (description, set_null_description, "description"),
        (gateway_addr, set_null_gateway_addr, "gateway-addr"),
        (gateway_public_key, set_null_gateway_public_key, "gateway-public-key"),
    ):
        if value is not None and flag:
            raise click.UsageError(f"--{name} and --set-null-{name} cannot be used together")

    input_ = UpdateComputeClusterInput(
        description=None
        if set_null_description
        else description
        if description is not None
        else UNSET,
        api_server=api_server if api_server is not None else UNSET,
        kubeconfig=kubeconfig_file.read() if kubeconfig_file is not None else UNSET,
        namespace_prefix=namespace_prefix if namespace_prefix is not None else UNSET,
        gateway_addr=None
        if set_null_gateway_addr
        else gateway_addr
        if gateway_addr is not None
        else UNSET,
        gateway_public_key=None
        if set_null_gateway_public_key
        else gateway_public_key
        if gateway_public_key is not None
        else UNSET,
        status=ComputeClusterStatus(status) if status is not None else UNSET,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.compute_cluster.admin_update(compute_cluster_id, input_)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@compute_cluster.command()
@click.argument("compute_cluster_id", type=click.UUID)
def purge(compute_cluster_id: uuid.UUID) -> None:
    """Permanently remove a compute cluster."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.compute_cluster.admin_purge(compute_cluster_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
