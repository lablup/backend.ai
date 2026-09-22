"""What a resource group search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.resource_group.types import (
    FairShareResourceGroupSpec,
    PreemptionConfig,
    ResourceGroupData,
    ResourceGroupDriverConfig,
    ResourceGroupMetadata,
    ResourceGroupNetworkConfig,
    ResourceGroupSchedulerConfig,
    ResourceGroupSchedulerOptions,
    ResourceGroupStatus,
    SchedulerType,
)
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.specs.search.usage import UsedByConditions


class _ResourceGroupOwnFields(RowDataConverter[ResourceGroupRow, ResourceGroupData]):
    """The resource group's own columns."""

    id = SearchableField(
        ResourceGroupRow.id,
        UUIDConditions(ResourceGroupRow.id),
        ColumnOrder(ResourceGroupRow.id),
    )
    name = SearchableField(
        ResourceGroupRow.name,
        StringConditions(ResourceGroupRow.name),
        ColumnOrder(ResourceGroupRow.name),
    )
    description = SearchableField(
        ResourceGroupRow.description,
        StringConditions(ResourceGroupRow.description),
        ColumnOrder(ResourceGroupRow.description),
    )
    is_active = SearchableField(
        ResourceGroupRow.is_active,
        BoolConditions(ResourceGroupRow.is_active),
        ColumnOrder(ResourceGroupRow.is_active),
    )
    is_public = SearchableField(
        ResourceGroupRow.is_public,
        BoolConditions(ResourceGroupRow.is_public),
        ColumnOrder(ResourceGroupRow.is_public),
    )
    """Whether a regular user is offered the group. Unrelated to registration in public."""
    is_default = SearchableField(
        ResourceGroupRow.is_default,
        BoolConditions(ResourceGroupRow.is_default),
        ColumnOrder(ResourceGroupRow.is_default),
    )
    created_at = SearchableField(
        ResourceGroupRow.created_at,
        DateTimeConditions(ResourceGroupRow.created_at),
        ColumnOrder(ResourceGroupRow.created_at),
    )
    wsproxy_addr = SearchableField(
        ResourceGroupRow.wsproxy_addr,
        StringConditions(ResourceGroupRow.wsproxy_addr),
        ColumnOrder(ResourceGroupRow.wsproxy_addr),
    )
    wsproxy_api_token = SearchableField(ResourceGroupRow.wsproxy_api_token, None, None)
    """Sensitive: the token the manager authenticates to the proxy with."""
    driver = SearchableField(
        ResourceGroupRow.driver,
        StringConditions(ResourceGroupRow.driver),
        ColumnOrder(ResourceGroupRow.driver),
    )
    driver_opts = SearchableField(ResourceGroupRow.driver_opts, None, None)
    """Impossible: a JSON document of driver settings."""
    scheduler = SearchableField(
        ResourceGroupRow.scheduler,
        StringConditions(ResourceGroupRow.scheduler),
        ColumnOrder(ResourceGroupRow.scheduler),
    )
    scheduler_opts = SearchableField(ResourceGroupRow.scheduler_opts, None, None)
    """Impossible: a JSON document of scheduler settings."""
    use_host_network = SearchableField(
        ResourceGroupRow.use_host_network,
        BoolConditions(ResourceGroupRow.use_host_network),
        ColumnOrder(ResourceGroupRow.use_host_network),
    )
    fair_share_spec = SearchableField(ResourceGroupRow.fair_share_spec, None, None)
    """Impossible: a JSON document of fair-share weights."""
    default_deployment_options = SearchableField(
        ResourceGroupRow.default_deployment_options, None, None
    )
    """Impossible: a JSON document of deployment defaults."""
    default_session_options = SearchableField(ResourceGroupRow.default_session_options, None, None)
    """Impossible: a JSON document of session defaults."""

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        is_active = self.is_active.read(row)
        scheduler_opts = self.scheduler_opts.read(row)
        preemption = scheduler_opts.preemption
        return ResourceGroupData(
            id=self.id.read(row),
            name=self.name.read(row),
            status=ResourceGroupStatus(
                is_active=is_active if is_active is not None else True,
                is_public=self.is_public.read(row),
                is_default=self.is_default.read(row),
            ),
            metadata=ResourceGroupMetadata(
                description=self.description.read(row) or "",
                created_at=self.created_at.read(row),
            ),
            network=ResourceGroupNetworkConfig(
                wsproxy_addr=self.wsproxy_addr.read(row) or "",
                wsproxy_api_token=self.wsproxy_api_token.read(row) or "",
                use_host_network=self.use_host_network.read(row),
            ),
            driver=ResourceGroupDriverConfig(
                name=self.driver.read(row),
                options=self.driver_opts.read(row),
            ),
            scheduler=ResourceGroupSchedulerConfig(
                name=SchedulerType(self.scheduler.read(row)),
                options=ResourceGroupSchedulerOptions(
                    allowed_session_types=scheduler_opts.allowed_session_types,
                    pending_timeout=scheduler_opts.pending_timeout,
                    config=scheduler_opts.config,
                    agent_selection_strategy=scheduler_opts.agent_selection_strategy,
                    agent_selector_config=scheduler_opts.agent_selector_config,
                    allow_fractional_resource_fragmentation=scheduler_opts.allow_fractional_resource_fragmentation,
                    route_cleanup_target_statuses=scheduler_opts.route_cleanup_target_statuses,
                    preemption=PreemptionConfig(
                        enabled=preemption.enabled,
                        preemptible_priority=preemption.preemptible_priority,
                        order=preemption.order,
                        mode=preemption.mode,
                        preemption_min_runtime=preemption.preemption_min_runtime,
                        victim_scope=preemption.victim_scope,
                    ),
                ),
            ),
            fair_share_spec=self.fair_share_spec.read(row) or FairShareResourceGroupSpec(),
            default_deployment_options=self.default_deployment_options.read(row),
            default_session_options=self.default_session_options.read(row),
        )


class _ResourceGroupUsage:
    """Uses between a resource group and other entities."""

    sessions = UsedByConditions[SessionID](
        ToManyCorrelation(
            SessionRow, ResourceGroupRow, SessionRow.resource_group_id == ResourceGroupRow.id
        ),
        SessionRow.id,
    )
    """Resource groups the session runs in."""
    deployments = UsedByConditions[DeploymentID](
        ToManyCorrelation(
            EndpointRow, ResourceGroupRow, EndpointRow.resource_group == ResourceGroupRow.name
        ),
        EndpointRow.id,
    )
    """Resource groups the deployment runs in."""


class _ResourceGroupLinkedEntities:
    """How a resource group connects to other entities; the other entity's permission governs."""

    usage = _ResourceGroupUsage


class ResourceGroupSearchableFields:
    own = _ResourceGroupOwnFields()
    linked = _ResourceGroupLinkedEntities
