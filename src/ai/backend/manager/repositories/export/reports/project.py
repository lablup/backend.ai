"""Project (group) export report definition."""

from __future__ import annotations

import json
from typing import Any

from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow, ScalingGroupRow
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    JoinDef,
    ReportDef,
)

# =============================================================================
# Helper Functions
# =============================================================================


def _serialize_json(value: Any) -> str:
    """Serialize value to JSON string, converting sets to lists."""
    if not value:
        return ""

    def convert(obj: Any) -> Any:
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj

    return json.dumps(convert(dict(value)))


# =============================================================================
# JOIN Definitions
# =============================================================================

# Resource Policy JOIN (N:1, no duplication)
RESOURCE_POLICY_JOIN = JoinDef(
    table=ProjectResourcePolicyRow.__table__,
    condition=GroupRow.resource_policy == ProjectResourcePolicyRow.name,
)

# Scaling Group JOINs (1:N, causes duplication)
SCALING_GROUP_FOR_PROJECT_JOIN = JoinDef(
    table=ScalingGroupForProjectRow.__table__,
    condition=GroupRow.id == ScalingGroupForProjectRow.group,
)
SCALING_GROUP_JOIN = JoinDef(
    table=ScalingGroupRow.__table__,
    condition=ScalingGroupForProjectRow.scaling_group == ScalingGroupRow.name,
)
SCALING_GROUP_JOINS = (SCALING_GROUP_FOR_PROJECT_JOIN, SCALING_GROUP_JOIN)

# Container Registry JOINs (1:N, causes duplication)
CONTAINER_REGISTRY_ASSOC_JOIN = JoinDef(
    table=AssociationContainerRegistriesGroupsRow.__table__,
    condition=GroupRow.id == AssociationContainerRegistriesGroupsRow.group_id,
)
CONTAINER_REGISTRY_JOIN = JoinDef(
    table=ContainerRegistryRow.__table__,
    condition=AssociationContainerRegistriesGroupsRow.registry_id == ContainerRegistryRow.id,
)
CONTAINER_REGISTRY_JOINS = (CONTAINER_REGISTRY_ASSOC_JOIN, CONTAINER_REGISTRY_JOIN)

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
    # Resource Policy Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="resource_policy_name",
        name="Resource Policy Name",
        description="Project resource policy name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.resource_policy,
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
    # Scaling Group Fields (1:N, causes duplication)
    # =========================================================================
    ExportFieldDef(
        key="scaling_group_name",
        name="Scaling Group Name",
        description="Scaling group name",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.name,
        joins=SCALING_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="scaling_group_description",
        name="Scaling Group Description",
        description="Scaling group description",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.description,
        joins=SCALING_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="scaling_group_is_active",
        name="Scaling Group Is Active",
        description="Scaling group active status",
        field_type=ExportFieldType.BOOLEAN,
        column=ScalingGroupRow.is_active,
        joins=SCALING_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="scaling_group_is_public",
        name="Scaling Group Is Public",
        description="Scaling group public status",
        field_type=ExportFieldType.BOOLEAN,
        column=ScalingGroupRow.is_public,
        joins=SCALING_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="scaling_group_driver",
        name="Scaling Group Driver",
        description="Scaling group driver type",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.driver,
        joins=SCALING_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="scaling_group_scheduler",
        name="Scaling Group Scheduler",
        description="Scaling group scheduler type",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.scheduler,
        joins=SCALING_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="scaling_group_created_at",
        name="Scaling Group Created At",
        description="Scaling group creation time",
        field_type=ExportFieldType.DATETIME,
        column=ScalingGroupRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=SCALING_GROUP_JOINS,
    ),
    # =========================================================================
    # Container Registry Fields (1:N, causes duplication)
    # =========================================================================
    ExportFieldDef(
        key="container_registry_id",
        name="Container Registry ID",
        description="Container registry UUID",
        field_type=ExportFieldType.UUID,
        column=ContainerRegistryRow.id,
        joins=CONTAINER_REGISTRY_JOINS,
    ),
    ExportFieldDef(
        key="container_registry_url",
        name="Container Registry URL",
        description="Container registry URL",
        field_type=ExportFieldType.STRING,
        column=ContainerRegistryRow.url,
        joins=CONTAINER_REGISTRY_JOINS,
    ),
    ExportFieldDef(
        key="container_registry_name",
        name="Container Registry Name",
        description="Container registry name",
        field_type=ExportFieldType.STRING,
        column=ContainerRegistryRow.registry_name,
        joins=CONTAINER_REGISTRY_JOINS,
    ),
    ExportFieldDef(
        key="container_registry_type",
        name="Container Registry Type",
        description="Container registry type (docker, harbor, etc.)",
        field_type=ExportFieldType.ENUM,
        column=ContainerRegistryRow.type,
        formatter=lambda v: str(v) if v else "",
        joins=CONTAINER_REGISTRY_JOINS,
    ),
    ExportFieldDef(
        key="container_registry_project",
        name="Container Registry Project",
        description="Container registry project",
        field_type=ExportFieldType.STRING,
        column=ContainerRegistryRow.project,
        joins=CONTAINER_REGISTRY_JOINS,
    ),
    ExportFieldDef(
        key="container_registry_is_global",
        name="Container Registry Is Global",
        description="Container registry global status",
        field_type=ExportFieldType.BOOLEAN,
        column=ContainerRegistryRow.is_global,
        joins=CONTAINER_REGISTRY_JOINS,
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
