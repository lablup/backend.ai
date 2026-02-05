"""Session export report definition."""

from __future__ import annotations

import json
from typing import Any

import sqlalchemy as sa

from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
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
            return sorted(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj

    return json.dumps(convert(dict(value)))


# =============================================================================
# JOIN Definitions
# =============================================================================

# Project JOIN (N:1, no duplication)
PROJECT_JOIN = JoinDef(
    table=GroupRow.__table__,
    condition=SessionRow.group_id == GroupRow.id,
)

# Project Resource Policy JOIN (N:1 through Project, no duplication)
PROJECT_RESOURCE_POLICY_JOIN = JoinDef(
    table=ProjectResourcePolicyRow.__table__,
    condition=GroupRow.resource_policy == ProjectResourcePolicyRow.name,
)
PROJECT_POLICY_JOINS = (PROJECT_JOIN, PROJECT_RESOURCE_POLICY_JOIN)

# User JOIN (N:1, no duplication)
USER_JOIN = JoinDef(
    table=UserRow.__table__,
    condition=SessionRow.user_uuid == UserRow.uuid,
)

# All Kernels JOIN (1:N, causes duplication)
KERNEL_JOIN = JoinDef(
    table=KernelRow.__table__,
    condition=SessionRow.id == KernelRow.session_id,
)

# Main Kernel JOIN (N:1, no duplication - main kernel only)
MAIN_KERNEL_JOIN = JoinDef(
    table=KernelRow.__table__,
    condition=sa.and_(
        SessionRow.id == KernelRow.session_id,
        KernelRow.cluster_role == DEFAULT_ROLE,
    ),
)

# Scaling Group JOIN (N:1, no duplication)
SCALING_GROUP_JOIN = JoinDef(
    table=ScalingGroupRow.__table__,
    condition=SessionRow.scaling_group_name == ScalingGroupRow.name,
)

# Field definitions for session export
SESSION_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Session UUID",
        field_type=ExportFieldType.UUID,
        column=SessionRow.id,
    ),
    ExportFieldDef(
        key="name",
        name="Name",
        description="Session name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.name,
    ),
    ExportFieldDef(
        key="session_type",
        name="Type",
        description="Session type",
        field_type=ExportFieldType.ENUM,
        column=SessionRow.session_type,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="domain_name",
        name="Domain",
        description="Domain name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.domain_name,
    ),
    ExportFieldDef(
        key="access_key",
        name="Access Key",
        description="Owning access key",
        field_type=ExportFieldType.STRING,
        column=SessionRow.access_key,
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="Session status",
        field_type=ExportFieldType.ENUM,
        column=SessionRow.status,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="status_info",
        name="Status Info",
        description="Status details",
        field_type=ExportFieldType.STRING,
        column=SessionRow.status_info,
    ),
    ExportFieldDef(
        key="cluster_size",
        name="Cluster Size",
        description="Number of cluster nodes",
        field_type=ExportFieldType.INTEGER,
        column=SessionRow.cluster_size,
    ),
    ExportFieldDef(
        key="resource_used",
        name="Resources Used",
        description="Occupied resource slots",
        field_type=ExportFieldType.JSON,
        column=SessionRow.occupying_slots,
        formatter=lambda v: json.dumps(dict(v), default=str) if v else "",
    ),
    ExportFieldDef(
        key="resource_requested",
        name="Resources Requested",
        description="Requested resource slots",
        field_type=ExportFieldType.JSON,
        column=SessionRow.requested_slots,
        formatter=lambda v: json.dumps(dict(v), default=str) if v else "",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Session creation time",
        field_type=ExportFieldType.DATETIME,
        column=SessionRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="terminated_at",
        name="Terminated At",
        description="Session termination time",
        field_type=ExportFieldType.DATETIME,
        column=SessionRow.terminated_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    # =========================================================================
    # Main Kernel Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="main_kernel_image",
        name="Main Kernel Image",
        description="Main kernel image canonical name",
        field_type=ExportFieldType.STRING,
        column=KernelRow.image,
        joins=frozenset({MAIN_KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="main_kernel_architecture",
        name="Main Kernel Architecture",
        description="Main kernel architecture",
        field_type=ExportFieldType.STRING,
        column=KernelRow.architecture,
        joins=frozenset({MAIN_KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="main_kernel_registry",
        name="Main Kernel Registry",
        description="Main kernel container registry",
        field_type=ExportFieldType.STRING,
        column=KernelRow.registry,
        joins=frozenset({MAIN_KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="main_kernel_tag",
        name="Main Kernel Tag",
        description="Main kernel image tag",
        field_type=ExportFieldType.STRING,
        column=KernelRow.tag,
        joins=frozenset({MAIN_KERNEL_JOIN}),
    ),
    # =========================================================================
    # Project Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="project_name",
        name="Project Name",
        description="Project (group) name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.name,
        joins=frozenset({PROJECT_JOIN}),
    ),
    ExportFieldDef(
        key="project_description",
        name="Project Description",
        description="Project description",
        field_type=ExportFieldType.STRING,
        column=GroupRow.description,
        joins=frozenset({PROJECT_JOIN}),
    ),
    ExportFieldDef(
        key="project_resource_policy",
        name="Project Resource Policy",
        description="Project resource policy name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.resource_policy,
        joins=frozenset({PROJECT_JOIN}),
    ),
    ExportFieldDef(
        key="project_is_active",
        name="Project Active",
        description="Project active status",
        field_type=ExportFieldType.BOOLEAN,
        column=GroupRow.is_active,
        joins=frozenset({PROJECT_JOIN}),
    ),
    ExportFieldDef(
        key="project_created_at",
        name="Project Created At",
        description="Project creation time",
        field_type=ExportFieldType.DATETIME,
        column=GroupRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({PROJECT_JOIN}),
    ),
    # =========================================================================
    # Project Resource Policy Fields (N:1 through Project, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="project_policy_max_vfolder_count",
        name="Project Policy Max VFolders",
        description="Maximum vfolder count for project",
        field_type=ExportFieldType.INTEGER,
        column=ProjectResourcePolicyRow.max_vfolder_count,
        joins=PROJECT_POLICY_JOINS,
    ),
    ExportFieldDef(
        key="project_policy_max_quota_scope_size",
        name="Project Policy Max Quota",
        description="Maximum quota scope size for project",
        field_type=ExportFieldType.INTEGER,
        column=ProjectResourcePolicyRow.max_quota_scope_size,
        joins=PROJECT_POLICY_JOINS,
    ),
    ExportFieldDef(
        key="project_policy_max_network_count",
        name="Project Policy Max Networks",
        description="Maximum network count for project",
        field_type=ExportFieldType.INTEGER,
        column=ProjectResourcePolicyRow.max_network_count,
        joins=PROJECT_POLICY_JOINS,
    ),
    # =========================================================================
    # User Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="user_email",
        name="User Email",
        description="User email address",
        field_type=ExportFieldType.STRING,
        column=UserRow.email,
        joins=frozenset({USER_JOIN}),
    ),
    ExportFieldDef(
        key="user_username",
        name="User Username",
        description="Username",
        field_type=ExportFieldType.STRING,
        column=UserRow.username,
        joins=frozenset({USER_JOIN}),
    ),
    ExportFieldDef(
        key="user_full_name",
        name="User Full Name",
        description="User full name",
        field_type=ExportFieldType.STRING,
        column=UserRow.full_name,
        joins=frozenset({USER_JOIN}),
    ),
    ExportFieldDef(
        key="user_role",
        name="User Role",
        description="User role (admin, user, etc.)",
        field_type=ExportFieldType.STRING,
        column=UserRow.role,
        formatter=lambda v: str(v) if v else "",
        joins=frozenset({USER_JOIN}),
    ),
    # =========================================================================
    # Resource Group Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="resource_group_name",
        name="Resource Group Name",
        description="Resource group name",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.name,
        joins=frozenset({SCALING_GROUP_JOIN}),
    ),
    ExportFieldDef(
        key="resource_group_description",
        name="Resource Group Description",
        description="Resource group description",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.description,
        joins=frozenset({SCALING_GROUP_JOIN}),
    ),
    ExportFieldDef(
        key="resource_group_is_active",
        name="Resource Group Active",
        description="Resource group active status",
        field_type=ExportFieldType.BOOLEAN,
        column=ScalingGroupRow.is_active,
        joins=frozenset({SCALING_GROUP_JOIN}),
    ),
    ExportFieldDef(
        key="resource_group_is_public",
        name="Resource Group Public",
        description="Resource group public status",
        field_type=ExportFieldType.BOOLEAN,
        column=ScalingGroupRow.is_public,
        joins=frozenset({SCALING_GROUP_JOIN}),
    ),
    ExportFieldDef(
        key="resource_group_scheduler",
        name="Resource Group Scheduler",
        description="Resource group scheduler type",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.scheduler,
        joins=frozenset({SCALING_GROUP_JOIN}),
    ),
    ExportFieldDef(
        key="resource_group_created_at",
        name="Resource Group Created At",
        description="Resource group creation time",
        field_type=ExportFieldType.DATETIME,
        column=ScalingGroupRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({SCALING_GROUP_JOIN}),
    ),
    # =========================================================================
    # Kernel Fields (1:N, causes duplication)
    # =========================================================================
    ExportFieldDef(
        key="kernel_id",
        name="Kernel ID",
        description="Kernel UUID",
        field_type=ExportFieldType.UUID,
        column=KernelRow.id,
        joins=frozenset({KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="kernel_role",
        name="Kernel Role",
        description="Kernel cluster role",
        field_type=ExportFieldType.STRING,
        column=KernelRow.cluster_role,
        joins=frozenset({KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="kernel_status",
        name="Kernel Status",
        description="Kernel status",
        field_type=ExportFieldType.STRING,
        column=KernelRow.status,
        formatter=lambda v: str(v) if v else "",
        joins=frozenset({KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="kernel_image",
        name="Kernel Image",
        description="Kernel image name",
        field_type=ExportFieldType.STRING,
        column=KernelRow.image,
        joins=frozenset({KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="kernel_agent",
        name="Kernel Agent",
        description="Agent ID running this kernel",
        field_type=ExportFieldType.STRING,
        column=KernelRow.agent,
        joins=frozenset({KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="kernel_created_at",
        name="Kernel Created At",
        description="Kernel creation time",
        field_type=ExportFieldType.DATETIME,
        column=KernelRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({KERNEL_JOIN}),
    ),
    ExportFieldDef(
        key="kernel_terminated_at",
        name="Kernel Terminated At",
        description="Kernel termination time",
        field_type=ExportFieldType.DATETIME,
        column=KernelRow.terminated_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({KERNEL_JOIN}),
    ),
]


# Report definition
SESSION_REPORT = ReportDef(
    report_key="sessions",
    name="Sessions",
    description="Compute session export report",
    select_from=SessionRow.__table__,
    fields=SESSION_FIELDS,
)
