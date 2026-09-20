"""What a deployment search can filter and order by, and how an endpoint row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.types import AutoScalingMetricSource
from ai.backend.manager.data.deployment.types import (
    DeploymentLifecycleSubStep,
    DeploymentNetworkData,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
    ModelDeploymentMetadataInfo,
    ReplicaStateData,
)
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.searchable_fields import (
    ModelRevisionSearchableFields,
)
from ai.backend.manager.models.endpoint.row import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.entity_label.searchable_fields import (
    EntityLabelCorrelation,
    EntityLabelSearchableFields,
)
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.replica_group.searchable_fields import (
    ReplicaGroupSearchableFields,
)
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.routing.searchable_fields import ReplicaSearchableFields
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import DecimalConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.specs.search.usage import UsageConditions


class _DeploymentOwnFields(RowDataConverter[EndpointRow, ModelDeploymentData]):
    """The deployment's own columns."""

    entity_id = SearchableField(
        EndpointRow.id, UUIDConditions(EndpointRow.id), ColumnOrder(EndpointRow.id)
    )
    name = SearchableField(
        EndpointRow.name, StringConditions(EndpointRow.name), ColumnOrder(EndpointRow.name)
    )
    created_user = SearchableField(
        EndpointRow.created_user,
        UUIDConditions(EndpointRow.created_user),
        ColumnOrder(EndpointRow.created_user),
    )
    session_owner = SearchableField(
        EndpointRow.session_owner,
        UUIDConditions(EndpointRow.session_owner),
        ColumnOrder(EndpointRow.session_owner),
    )
    replicas = SearchableField(
        EndpointRow.replicas,
        IntConditions(EndpointRow.replicas),
        ColumnOrder(EndpointRow.replicas),
    )
    desired_replicas = SearchableField(
        EndpointRow.desired_replicas,
        IntConditions(EndpointRow.desired_replicas),
        ColumnOrder(EndpointRow.desired_replicas),
    )
    domain = SearchableField(
        EndpointRow.domain, StringConditions(EndpointRow.domain), ColumnOrder(EndpointRow.domain)
    )
    project = SearchableField(
        EndpointRow.project, UUIDConditions(EndpointRow.project), ColumnOrder(EndpointRow.project)
    )
    resource_group = SearchableField(
        EndpointRow.resource_group,
        StringConditions(EndpointRow.resource_group),
        ColumnOrder(EndpointRow.resource_group),
    )
    lifecycle_stage = SearchableField(
        EndpointRow.lifecycle_stage,
        EnumConditions(EndpointRow.lifecycle_stage, EndpointLifecycle),
        ColumnOrder(EndpointRow.lifecycle_stage),
    )
    scaling_state = SearchableField(
        EndpointRow.scaling_state,
        EnumConditions(EndpointRow.scaling_state, ScalingState),
        ColumnOrder(EndpointRow.scaling_state),
    )
    tag = SearchableField(
        EndpointRow.tag, StringConditions(EndpointRow.tag), ColumnOrder(EndpointRow.tag)
    )
    open_to_public = SearchableField(
        EndpointRow.open_to_public,
        BoolConditions(EndpointRow.open_to_public),
        ColumnOrder(EndpointRow.open_to_public),
    )
    url = SearchableField(
        EndpointRow.url, StringConditions(EndpointRow.url), ColumnOrder(EndpointRow.url)
    )
    retries = SearchableField(
        EndpointRow.retries, IntConditions(EndpointRow.retries), ColumnOrder(EndpointRow.retries)
    )
    created_at = SearchableField(
        EndpointRow.created_at,
        DateTimeConditions(EndpointRow.created_at),
        ColumnOrder(EndpointRow.created_at),
    )
    destroyed_at = SearchableField(
        EndpointRow.destroyed_at,
        DateTimeConditions(EndpointRow.destroyed_at),
        ColumnOrder(EndpointRow.destroyed_at),
    )
    primary_replica_group_id = SearchableField(
        EndpointRow.primary_replica_group_id,
        UUIDConditions(EndpointRow.primary_replica_group_id),
        ColumnOrder(EndpointRow.primary_replica_group_id),
    )
    target_replica_group_id = SearchableField(
        EndpointRow.target_replica_group_id,
        UUIDConditions(EndpointRow.target_replica_group_id),
        ColumnOrder(EndpointRow.target_replica_group_id),
    )
    deploying_revision_id = SearchableField(
        EndpointRow.deploying_revision_id,
        UUIDConditions(EndpointRow.deploying_revision_id),
        ColumnOrder(EndpointRow.deploying_revision_id),
    )
    sub_step = SearchableField(
        EndpointRow.sub_step,
        EnumConditions(EndpointRow.sub_step, DeploymentLifecycleSubStep),
        ColumnOrder(EndpointRow.sub_step),
    )
    revision_history_limit = SearchableField(
        EndpointRow.revision_history_limit,
        IntConditions(EndpointRow.revision_history_limit),
        ColumnOrder(EndpointRow.revision_history_limit),
    )
    options = SearchableField(EndpointRow.options, None, None)

    @override
    def to_data(self, row: EndpointRow) -> ModelDeploymentData:
        """The v2 deployment projection read off this row's own columns.

        ``current_revision_id`` and ``policy`` live on other rows and come back ``None``.
        """
        created_at = self.created_at.read(row)
        open_to_public = self.open_to_public.read(row)
        tag = self.tag.read(row)
        desired_replicas = self.desired_replicas.read(row)
        return ModelDeploymentData(
            id=self.entity_id.read(row),
            metadata=ModelDeploymentMetadataInfo(
                name=self.name.read(row),
                status=ModelDeploymentStatus.from_lifecycle(self.lifecycle_stage.read(row)),
                tags=[tag] if tag else [],
                project_id=self.project.read(row),
                domain_name=self.domain.read(row),
                resource_group_name=self.resource_group.read(row),
                created_at=created_at,
                updated_at=created_at,
            ),
            network_access=DeploymentNetworkData(
                open_to_public=open_to_public if open_to_public is not None else False,
                access_token_ids=None,
                url=self.url.read(row),
                preferred_domain_name=None,
            ),
            current_revision_id=None,
            deploying_revision_id=self.deploying_revision_id.read(row),
            revision_history_ids=[],
            scaling_rule_ids=[],
            replica_state=ReplicaStateData(
                desired_replica_count=desired_replicas
                if desired_replicas is not None
                else self.replicas.read(row),
                replica_ids=[],
            ),
            default_deployment_strategy=DeploymentStrategy.ROLLING,
            created_user_id=self.created_user.read(row),
            options=self.options.read(row),
            scaling_state=self.scaling_state.read(row),
            sub_step=self.sub_step.read(row),
            primary_replica_group_id=self.primary_replica_group_id.read(row),
        )


class _DeploymentAccessTokenOwnFields(
    RowDataConverter[EndpointTokenRow, ModelDeploymentAccessTokenData]
):
    """An access token row's own columns.

    ``token`` holds the plaintext token, so it carries neither a filter nor an order.
    """

    field_id = SearchableField(
        EndpointTokenRow.id,
        UUIDConditions(EndpointTokenRow.id),
        ColumnOrder(EndpointTokenRow.id),
    )
    token = SearchableField(EndpointTokenRow.token, None, None)
    deployment_id = SearchableField(
        EndpointTokenRow.endpoint,
        UUIDConditions(EndpointTokenRow.endpoint),
        ColumnOrder(EndpointTokenRow.endpoint),
    )
    session_owner = SearchableField(
        EndpointTokenRow.session_owner,
        UUIDConditions(EndpointTokenRow.session_owner),
        ColumnOrder(EndpointTokenRow.session_owner),
    )
    domain = SearchableField(
        EndpointTokenRow.domain,
        StringConditions(EndpointTokenRow.domain),
        ColumnOrder(EndpointTokenRow.domain),
    )
    project = SearchableField(
        EndpointTokenRow.project,
        UUIDConditions(EndpointTokenRow.project),
        ColumnOrder(EndpointTokenRow.project),
    )
    expires_at = SearchableField(
        EndpointTokenRow.expires_at,
        DateTimeConditions(EndpointTokenRow.expires_at),
        ColumnOrder(EndpointTokenRow.expires_at),
    )
    created_at = SearchableField(
        EndpointTokenRow.created_at,
        DateTimeConditions(EndpointTokenRow.created_at),
        ColumnOrder(EndpointTokenRow.created_at),
    )

    @override
    def to_data(self, row: EndpointTokenRow) -> ModelDeploymentAccessTokenData:
        return ModelDeploymentAccessTokenData(
            id=DeploymentTokenID(self.field_id.read(row)),
            token=self.token.read(row),
            expires_at=self.expires_at.read(row),
            created_at=self.created_at.read(row),
        )


class DeploymentAccessTokenSearchableFields:
    own = _DeploymentAccessTokenOwnFields()


class _AutoScalingRuleOwnFields(
    RowDataConverter[EndpointAutoScalingRuleRow, ModelDeploymentAutoScalingRuleData]
):
    """An auto-scaling rule row's own columns.

    ``DecimalType`` stores the thresholds as VARCHAR, so both slots compare them as numbers.
    """

    _min_threshold = sa.cast(EndpointAutoScalingRuleRow.min_threshold, sa.Numeric())
    _max_threshold = sa.cast(EndpointAutoScalingRuleRow.max_threshold, sa.Numeric())

    field_id = SearchableField(
        EndpointAutoScalingRuleRow.id,
        UUIDConditions(EndpointAutoScalingRuleRow.id),
        ColumnOrder(EndpointAutoScalingRuleRow.id),
    )
    deployment_id = SearchableField(
        EndpointAutoScalingRuleRow.endpoint,
        UUIDConditions(EndpointAutoScalingRuleRow.endpoint),
        ColumnOrder(EndpointAutoScalingRuleRow.endpoint),
    )
    metric_source = SearchableField(
        EndpointAutoScalingRuleRow.metric_source,
        EnumConditions(EndpointAutoScalingRuleRow.metric_source, AutoScalingMetricSource),
        ColumnOrder(EndpointAutoScalingRuleRow.metric_source),
    )
    metric_name = SearchableField(
        EndpointAutoScalingRuleRow.metric_name,
        StringConditions(EndpointAutoScalingRuleRow.metric_name),
        ColumnOrder(EndpointAutoScalingRuleRow.metric_name),
    )
    min_threshold = SearchableField(
        EndpointAutoScalingRuleRow.min_threshold,
        DecimalConditions(_min_threshold),
        ColumnOrder(_min_threshold),
    )
    max_threshold = SearchableField(
        EndpointAutoScalingRuleRow.max_threshold,
        DecimalConditions(_max_threshold),
        ColumnOrder(_max_threshold),
    )
    step_size = SearchableField(
        EndpointAutoScalingRuleRow.step_size,
        IntConditions(EndpointAutoScalingRuleRow.step_size),
        ColumnOrder(EndpointAutoScalingRuleRow.step_size),
    )
    cooldown_seconds = SearchableField(
        EndpointAutoScalingRuleRow.cooldown_seconds,
        IntConditions(EndpointAutoScalingRuleRow.cooldown_seconds),
        ColumnOrder(EndpointAutoScalingRuleRow.cooldown_seconds),
    )
    min_replicas = SearchableField(
        EndpointAutoScalingRuleRow.min_replicas,
        IntConditions(EndpointAutoScalingRuleRow.min_replicas),
        ColumnOrder(EndpointAutoScalingRuleRow.min_replicas),
    )
    max_replicas = SearchableField(
        EndpointAutoScalingRuleRow.max_replicas,
        IntConditions(EndpointAutoScalingRuleRow.max_replicas),
        ColumnOrder(EndpointAutoScalingRuleRow.max_replicas),
    )
    prometheus_query_preset_id = SearchableField(
        EndpointAutoScalingRuleRow.prometheus_query_preset_id,
        UUIDConditions(EndpointAutoScalingRuleRow.prometheus_query_preset_id),
        ColumnOrder(EndpointAutoScalingRuleRow.prometheus_query_preset_id),
    )
    created_at = SearchableField(
        EndpointAutoScalingRuleRow.created_at,
        DateTimeConditions(EndpointAutoScalingRuleRow.created_at),
        ColumnOrder(EndpointAutoScalingRuleRow.created_at),
    )
    last_triggered_at = SearchableField(
        EndpointAutoScalingRuleRow.last_triggered_at,
        DateTimeConditions(EndpointAutoScalingRuleRow.last_triggered_at),
        ColumnOrder(EndpointAutoScalingRuleRow.last_triggered_at),
    )

    @override
    def to_data(self, row: EndpointAutoScalingRuleRow) -> ModelDeploymentAutoScalingRuleData:
        return ModelDeploymentAutoScalingRuleData(
            id=self.field_id.read(row),
            model_deployment_id=self.deployment_id.read(row),
            metric_source=self.metric_source.read(row),
            metric_name=self.metric_name.read(row),
            min_threshold=self.min_threshold.read(row),
            max_threshold=self.max_threshold.read(row),
            step_size=self.step_size.read(row),
            time_window=self.cooldown_seconds.read(row),
            min_replicas=self.min_replicas.read(row),
            max_replicas=self.max_replicas.read(row),
            created_at=self.created_at.read(row),
            last_triggered_at=self.last_triggered_at.read(row),
            prometheus_query_preset_id=self.prometheus_query_preset_id.read(row),
        )


class AutoScalingRuleSearchableFields:
    own = _AutoScalingRuleOwnFields()


class _DeploymentNestedFields:
    """The rows the deployment owns. Every one is read under the deployment's own permission."""

    labels = NestedSearchableField(
        EntityLabelSearchableFields.own,
        EntityLabelCorrelation(EndpointRow, DeploymentEntityType(), EndpointRow.id),
    )
    revisions = NestedSearchableField(
        ModelRevisionSearchableFields.own,
        ToManyCorrelation(
            DeploymentRevisionRow,
            EndpointRow,
            DeploymentRevisionRow.endpoint == EndpointRow.id,
        ),
    )
    replica_groups = NestedSearchableField(
        ReplicaGroupSearchableFields.own,
        ToManyCorrelation(
            ReplicaGroupRow, EndpointRow, ReplicaGroupRow.deployment_id == EndpointRow.id
        ),
    )
    replicas = NestedSearchableField(
        ReplicaSearchableFields.own,
        ToManyCorrelation(RoutingRow, EndpointRow, RoutingRow.endpoint == EndpointRow.id),
    )
    access_tokens = NestedSearchableField(
        DeploymentAccessTokenSearchableFields.own,
        ToManyCorrelation(
            EndpointTokenRow, EndpointRow, EndpointTokenRow.endpoint == EndpointRow.id
        ),
    )
    auto_scaling_rules = NestedSearchableField(
        AutoScalingRuleSearchableFields.own,
        ToManyCorrelation(
            EndpointAutoScalingRuleRow,
            EndpointRow,
            EndpointAutoScalingRuleRow.endpoint == EndpointRow.id,
        ),
    )


class _DeploymentLinkedEntities:
    """How a deployment connects to other entities; the other entity's permission governs."""

    resource_groups = UsageConditions[ResourceGroupID](
        ToManyCorrelation(
            ResourceGroupRow, EndpointRow, ResourceGroupRow.name == EndpointRow.resource_group
        ),
        ResourceGroupRow.id,
    )
    """Deployments a resource group runs."""


class DeploymentSearchableFields:
    own = _DeploymentOwnFields()
    nested = _DeploymentNestedFields
    linked = _DeploymentLinkedEntities
