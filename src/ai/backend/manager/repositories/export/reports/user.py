"""User export report definition."""

from __future__ import annotations

import json
from typing import Any

from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
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

# User Resource Policy JOIN (N:1, no duplication)
USER_RESOURCE_POLICY_JOIN = JoinDef(
    table=UserResourcePolicyRow.__table__,
    condition=UserRow.resource_policy == UserResourcePolicyRow.name,
)

# Project JOINs (1:N, causes duplication)
ASSOC_GROUP_USER_JOIN = JoinDef(
    table=AssocGroupUserRow.__table__,
    condition=UserRow.uuid == AssocGroupUserRow.user_id,
)
PROJECT_JOIN = JoinDef(
    table=GroupRow.__table__,
    condition=AssocGroupUserRow.group_id == GroupRow.id,
)
PROJECT_JOINS = (ASSOC_GROUP_USER_JOIN, PROJECT_JOIN)

# Main Keypair JOIN (N:1, no duplication)
MAIN_KEYPAIR_JOIN = JoinDef(
    table=KeyPairRow.__table__,
    condition=UserRow.main_access_key == KeyPairRow.access_key,
)

# Field definitions for user export
USER_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="uuid",
        name="UUID",
        description="User UUID",
        field_type=ExportFieldType.UUID,
        column=UserRow.uuid,
    ),
    ExportFieldDef(
        key="username",
        name="Username",
        description="Login username",
        field_type=ExportFieldType.STRING,
        column=UserRow.username,
    ),
    ExportFieldDef(
        key="email",
        name="Email",
        description="Email address",
        field_type=ExportFieldType.STRING,
        column=UserRow.email,
    ),
    ExportFieldDef(
        key="full_name",
        name="Full Name",
        description="User full name",
        field_type=ExportFieldType.STRING,
        column=UserRow.full_name,
    ),
    ExportFieldDef(
        key="domain_name",
        name="Domain",
        description="Domain name",
        field_type=ExportFieldType.STRING,
        column=UserRow.domain_name,
    ),
    ExportFieldDef(
        key="role",
        name="Role",
        description="User role",
        field_type=ExportFieldType.ENUM,
        column=UserRow.role,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="User status",
        field_type=ExportFieldType.ENUM,
        column=UserRow.status,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Registration time",
        field_type=ExportFieldType.DATETIME,
        column=UserRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="modified_at",
        name="Modified At",
        description="Last modification time",
        field_type=ExportFieldType.DATETIME,
        column=UserRow.modified_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    # =========================================================================
    # User Resource Policy Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="resource_policy_name",
        name="Resource Policy",
        description="User resource policy name",
        field_type=ExportFieldType.STRING,
        column=UserRow.resource_policy,
    ),
    ExportFieldDef(
        key="resource_policy_created_at",
        name="Policy Created At",
        description="Resource policy creation time",
        field_type=ExportFieldType.DATETIME,
        column=UserResourcePolicyRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({USER_RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_vfolder_count",
        name="Policy Max VFolder Count",
        description="Maximum number of vfolders allowed",
        field_type=ExportFieldType.INTEGER,
        column=UserResourcePolicyRow.max_vfolder_count,
        joins=frozenset({USER_RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_quota_scope_size",
        name="Policy Max Quota Size",
        description="Maximum quota scope size in bytes",
        field_type=ExportFieldType.INTEGER,
        column=UserResourcePolicyRow.max_quota_scope_size,
        joins=frozenset({USER_RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_session_count_per_model",
        name="Policy Max Sessions Per Model",
        description="Maximum sessions per model serving",
        field_type=ExportFieldType.INTEGER,
        column=UserResourcePolicyRow.max_session_count_per_model_session,
        joins=frozenset({USER_RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_customized_image_count",
        name="Policy Max Custom Images",
        description="Maximum customized images allowed",
        field_type=ExportFieldType.INTEGER,
        column=UserResourcePolicyRow.max_customized_image_count,
        joins=frozenset({USER_RESOURCE_POLICY_JOIN}),
    ),
    # =========================================================================
    # Project Fields (1:N, causes duplication)
    # =========================================================================
    ExportFieldDef(
        key="project_id",
        name="Project ID",
        description="Project UUID",
        field_type=ExportFieldType.UUID,
        column=GroupRow.id,
        joins=PROJECT_JOINS,
    ),
    ExportFieldDef(
        key="project_name",
        name="Project Name",
        description="Project name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.name,
        joins=PROJECT_JOINS,
    ),
    ExportFieldDef(
        key="project_description",
        name="Project Description",
        description="Project description",
        field_type=ExportFieldType.STRING,
        column=GroupRow.description,
        joins=PROJECT_JOINS,
    ),
    ExportFieldDef(
        key="project_domain_name",
        name="Project Domain",
        description="Project domain name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.domain_name,
        joins=PROJECT_JOINS,
    ),
    ExportFieldDef(
        key="project_is_active",
        name="Project Active",
        description="Project active status",
        field_type=ExportFieldType.BOOLEAN,
        column=GroupRow.is_active,
        joins=PROJECT_JOINS,
    ),
    ExportFieldDef(
        key="project_created_at",
        name="Project Created At",
        description="Project creation time",
        field_type=ExportFieldType.DATETIME,
        column=GroupRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=PROJECT_JOINS,
    ),
    # =========================================================================
    # Main Keypair Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="main_access_key",
        name="Main Access Key",
        description="Main keypair access key",
        field_type=ExportFieldType.STRING,
        column=UserRow.main_access_key,
    ),
    ExportFieldDef(
        key="main_keypair_is_active",
        name="Main Keypair Active",
        description="Main keypair active status",
        field_type=ExportFieldType.BOOLEAN,
        column=KeyPairRow.is_active,
        joins=frozenset({MAIN_KEYPAIR_JOIN}),
    ),
    ExportFieldDef(
        key="main_keypair_created_at",
        name="Main Keypair Created At",
        description="Main keypair creation time",
        field_type=ExportFieldType.DATETIME,
        column=KeyPairRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({MAIN_KEYPAIR_JOIN}),
    ),
    ExportFieldDef(
        key="main_keypair_last_used",
        name="Main Keypair Last Used",
        description="Main keypair last used timestamp",
        field_type=ExportFieldType.DATETIME,
        column=KeyPairRow.last_used,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({MAIN_KEYPAIR_JOIN}),
    ),
]


# Report definition
USER_REPORT = ReportDef(
    report_key="users",
    name="Users",
    description="User account export report",
    select_from=UserRow.__table__,
    fields=USER_FIELDS,
)
