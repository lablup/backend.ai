"""Project (group) export report definition."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import aggregate_order_by

from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow, ScalingGroupRow
from ai.backend.manager.repositories.base.export import (
    ExportColumn,
    ExportFieldDef,
    ExportFieldType,
    JoinDef,
    ReportDef,
)

# Separator between the values a 1:N field aggregates into one CSV cell.
MULTI_VALUE_SEPARATOR = ", "

# =============================================================================
# Helper Functions
# =============================================================================


def _serialize_json(value: Any) -> str:
    """Serialize value to JSON string, converting sets to lists and Decimals to strings."""
    if not value:
        return ""

    def convert(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj

    return json.dumps(convert(dict(value)))


# =============================================================================
# JOIN Definitions (N:1 only)
# =============================================================================

# Resource Policy JOIN (N:1, no duplication)
RESOURCE_POLICY_JOIN = JoinDef(
    table=ProjectResourcePolicyRow.__table__,
    condition=GroupRow.resource_policy == ProjectResourcePolicyRow.name,
)


# =============================================================================
# 1:N Aggregations
# =============================================================================
# A project may be bound to many scaling groups and to many container registries.
# Joining either relation into the main query emits one row per
# (project x related row) and repeats every other column on the extra rows, so
# these fields select a correlated aggregate that folds the related values into
# a single cell and keep the export at one row per project.


# The project's allowed scaling groups.
SCALING_GROUP_RELATION = sa.join(
    ScalingGroupForProjectRow.__table__,
    ScalingGroupRow.__table__,
    ScalingGroupForProjectRow.scaling_group == ScalingGroupRow.name,
)
SCALING_GROUP_CONDITION = ScalingGroupForProjectRow.group == GroupRow.id

# The registries reachable from a project: every global registry (available to
# all projects) plus the ones explicitly associated with it.
_assoc_table = AssociationContainerRegistriesGroupsRow.__table__
CONTAINER_REGISTRY_RELATION = ContainerRegistryRow.__table__
CONTAINER_REGISTRY_CONDITION = sa.or_(
    ContainerRegistryRow.is_global.is_(True),
    sa.select(sa.literal(1))
    .where(
        sa.and_(
            _assoc_table.c.group_id == GroupRow.id,
            _assoc_table.c.registry_id == ContainerRegistryRow.id,
        ),
    )
    .correlate(GroupRow.__table__, ContainerRegistryRow.__table__)
    .exists(),
)


def aggregate_related(
    column: ExportColumn,
    relation: sa.FromClause,
    condition: sa.ColumnElement[bool],
) -> ExportColumn:
    """Fold the related rows matching ``condition`` into one sorted, de-duplicated cell.

    Casts to text so a single expression covers every column type the reports
    aggregate (uuid, boolean, enum, timestamp), and correlates the project table
    so the subquery is evaluated per exported project row.
    """
    value = sa.cast(column, sa.Text)
    return (
        sa.select(
            sa.func.string_agg(
                sa.distinct(value),
                aggregate_order_by(sa.literal(MULTI_VALUE_SEPARATOR), value),
            )
        )
        .select_from(relation)
        .where(condition)
        .correlate(GroupRow.__table__)
        .scalar_subquery()
    )


# Field definitions for project export
PROJECT_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Project UUID",
        field_type=ExportFieldType.UUID,
        column=GroupRow.id,
    ),
    ExportFieldDef(
        key="name",
        name="Name",
        description="Project name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.name,
    ),
    ExportFieldDef(
        key="description",
        name="Description",
        description="Project description",
        field_type=ExportFieldType.STRING,
        column=GroupRow.description,
    ),
    ExportFieldDef(
        key="domain_name",
        name="Domain",
        description="Domain name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.domain_name,
    ),
    ExportFieldDef(
        key="is_active",
        name="Active",
        description="Active status",
        field_type=ExportFieldType.BOOLEAN,
        column=GroupRow.is_active,
    ),
    ExportFieldDef(
        key="total_resource_slots",
        name="Resource Slots",
        description="Total resource slots allocated",
        field_type=ExportFieldType.JSON,
        column=GroupRow.total_resource_slots,
        formatter=_serialize_json,
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Creation time",
        field_type=ExportFieldType.DATETIME,
        column=GroupRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="modified_at",
        name="Modified At",
        description="Last modification time",
        field_type=ExportFieldType.DATETIME,
        column=GroupRow.modified_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    # =========================================================================
    # Folder Host Permission (no JOIN needed, already in GroupRow as JSONB)
    # =========================================================================
    ExportFieldDef(
        key="allowed_vfolder_hosts",
        name="Allowed VFolder Hosts",
        description="Allowed virtual folder hosts with permissions",
        field_type=ExportFieldType.JSON,
        column=GroupRow.allowed_vfolder_hosts,
        formatter=_serialize_json,
    ),
    # =========================================================================
    # Container Registry for Image Commit (no JOIN needed, already in GroupRow as JSONB)
    # =========================================================================
    ExportFieldDef(
        key="container_registry",
        name="Container Registry",
        description="Container registry and project for image commit",
        field_type=ExportFieldType.JSON,
        column=GroupRow.container_registry,
        formatter=_serialize_json,
    ),
    # =========================================================================
    # Resource Policy Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="resource_policy_name",
        name="Resource Policy Name",
        description="Project resource policy name",
        field_type=ExportFieldType.STRING,
        column=ProjectResourcePolicyRow.name,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_vfolder_count",
        name="Resource Policy Max VFolder Count",
        description="Maximum number of virtual folders allowed",
        field_type=ExportFieldType.INTEGER,
        column=ProjectResourcePolicyRow.max_vfolder_count,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_quota_scope_size",
        name="Resource Policy Max Quota Scope Size",
        description="Maximum quota scope size in bytes",
        field_type=ExportFieldType.INTEGER,
        column=ProjectResourcePolicyRow.max_quota_scope_size,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_network_count",
        name="Resource Policy Max Network Count",
        description="Maximum number of networks allowed",
        field_type=ExportFieldType.INTEGER,
        column=ProjectResourcePolicyRow.max_network_count,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_created_at",
        name="Resource Policy Created At",
        description="Resource policy creation time",
        field_type=ExportFieldType.DATETIME,
        column=ProjectResourcePolicyRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    # =========================================================================
    # Scaling Group Fields (1:N — aggregated into one cell per project)
    # =========================================================================
    ExportFieldDef(
        key="scaling_group_name",
        name="Scaling Group Name",
        description="Names of the scaling groups allowed for the project, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.name, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    ExportFieldDef(
        key="scaling_group_description",
        name="Scaling Group Description",
        description="Descriptions of the allowed scaling groups, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.description, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    ExportFieldDef(
        key="scaling_group_is_active",
        name="Scaling Group Is Active",
        description="Active statuses of the allowed scaling groups, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.is_active, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    ExportFieldDef(
        key="scaling_group_is_public",
        name="Scaling Group Is Public",
        description="Public statuses of the allowed scaling groups, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.is_public, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    ExportFieldDef(
        key="scaling_group_driver",
        name="Scaling Group Driver",
        description="Driver types of the allowed scaling groups, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.driver, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    ExportFieldDef(
        key="scaling_group_scheduler",
        name="Scaling Group Scheduler",
        description="Scheduler types of the allowed scaling groups, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.scheduler, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    ExportFieldDef(
        key="scaling_group_created_at",
        name="Scaling Group Created At",
        description="Creation times of the allowed scaling groups, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ScalingGroupRow.created_at, SCALING_GROUP_RELATION, SCALING_GROUP_CONDITION
        ),
    ),
    # =========================================================================
    # Container Registry Fields (1:N — aggregated into one cell per project)
    # =========================================================================
    ExportFieldDef(
        key="container_registry_id",
        name="Container Registry ID",
        description="UUIDs of the container registries available to the project, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ContainerRegistryRow.id, CONTAINER_REGISTRY_RELATION, CONTAINER_REGISTRY_CONDITION
        ),
    ),
    ExportFieldDef(
        key="container_registry_url",
        name="Container Registry URL",
        description="URLs of the available container registries, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ContainerRegistryRow.url, CONTAINER_REGISTRY_RELATION, CONTAINER_REGISTRY_CONDITION
        ),
    ),
    ExportFieldDef(
        key="container_registry_name",
        name="Container Registry Name",
        description="Names of the available container registries, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ContainerRegistryRow.registry_name,
            CONTAINER_REGISTRY_RELATION,
            CONTAINER_REGISTRY_CONDITION,
        ),
    ),
    ExportFieldDef(
        key="container_registry_type",
        name="Container Registry Type",
        description="Types of the available container registries (docker, harbor, etc.),"
        " comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ContainerRegistryRow.type, CONTAINER_REGISTRY_RELATION, CONTAINER_REGISTRY_CONDITION
        ),
    ),
    ExportFieldDef(
        key="container_registry_project",
        name="Container Registry Project",
        description="Projects of the available container registries, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ContainerRegistryRow.project, CONTAINER_REGISTRY_RELATION, CONTAINER_REGISTRY_CONDITION
        ),
    ),
    ExportFieldDef(
        key="container_registry_is_global",
        name="Container Registry Is Global",
        description="Global statuses of the available container registries, comma-separated",
        field_type=ExportFieldType.STRING,
        column=aggregate_related(
            ContainerRegistryRow.is_global,
            CONTAINER_REGISTRY_RELATION,
            CONTAINER_REGISTRY_CONDITION,
        ),
    ),
]


# Report definition
PROJECT_REPORT = ReportDef(
    report_key="projects",
    name="Projects",
    description="Project (group) export report",
    select_from=GroupRow.__table__,
    fields=PROJECT_FIELDS,
)
