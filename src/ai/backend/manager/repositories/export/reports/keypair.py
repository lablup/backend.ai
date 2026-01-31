"""Keypair export report definition."""

from __future__ import annotations

import json
from typing import Any

from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow, ScalingGroupRow
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
    """Serialize value to JSON string, converting sets to lists and Decimals to strings."""
    from decimal import Decimal

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
# JOIN Definitions
# =============================================================================

# User JOIN (N:1, no duplication)
USER_JOIN = JoinDef(
    table=UserRow.__table__,
    condition=KeyPairRow.user == UserRow.uuid,
)

# Resource Policy JOIN (N:1, no duplication)
RESOURCE_POLICY_JOIN = JoinDef(
    table=KeyPairResourcePolicyRow.__table__,
    condition=KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
)

# Resource Group JOINs (1:N, causes duplication)
SGROUP_FOR_KEYPAIR_JOIN = JoinDef(
    table=ScalingGroupForKeypairsRow.__table__,
    condition=KeyPairRow.access_key == ScalingGroupForKeypairsRow.access_key,
)
RESOURCE_GROUP_JOIN = JoinDef(
    table=ScalingGroupRow.__table__,
    condition=ScalingGroupForKeypairsRow.scaling_group == ScalingGroupRow.name,
)
RESOURCE_GROUP_JOINS = (SGROUP_FOR_KEYPAIR_JOIN, RESOURCE_GROUP_JOIN)

# Session JOIN (1:N, causes duplication)
SESSION_JOIN = JoinDef(
    table=SessionRow.__table__,
    condition=KeyPairRow.access_key == SessionRow.access_key,
)

# Field definitions for keypair export
KEYPAIR_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="access_key",
        name="Access Key",
        description="Access key identifier",
        field_type=ExportFieldType.STRING,
        column=KeyPairRow.access_key,
    ),
    ExportFieldDef(
        key="user_id",
        name="User Email",
        description="User email (ID)",
        field_type=ExportFieldType.STRING,
        column=KeyPairRow.user_id,
    ),
    ExportFieldDef(
        key="user_uuid",
        name="User UUID",
        description="User UUID",
        field_type=ExportFieldType.UUID,
        column=KeyPairRow.user,
    ),
    ExportFieldDef(
        key="is_active",
        name="Active",
        description="Keypair active status",
        field_type=ExportFieldType.BOOLEAN,
        column=KeyPairRow.is_active,
    ),
    ExportFieldDef(
        key="is_admin",
        name="Admin",
        description="Admin keypair status",
        field_type=ExportFieldType.BOOLEAN,
        column=KeyPairRow.is_admin,
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Keypair creation time",
        field_type=ExportFieldType.DATETIME,
        column=KeyPairRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="modified_at",
        name="Modified At",
        description="Last modification time",
        field_type=ExportFieldType.DATETIME,
        column=KeyPairRow.modified_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="last_used",
        name="Last Used",
        description="Last used timestamp",
        field_type=ExportFieldType.DATETIME,
        column=KeyPairRow.last_used,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="resource_policy_name",
        name="Resource Policy",
        description="Keypair resource policy name",
        field_type=ExportFieldType.STRING,
        column=KeyPairRow.resource_policy,
    ),
    # =========================================================================
    # User Fields (N:1, no duplication)
    # =========================================================================
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
        description="User role",
        field_type=ExportFieldType.STRING,
        column=UserRow.role,
        formatter=lambda v: str(v) if v else "",
        joins=frozenset({USER_JOIN}),
    ),
    ExportFieldDef(
        key="user_status",
        name="User Status",
        description="User account status",
        field_type=ExportFieldType.STRING,
        column=UserRow.status,
        formatter=lambda v: str(v) if v else "",
        joins=frozenset({USER_JOIN}),
    ),
    ExportFieldDef(
        key="user_domain_name",
        name="User Domain",
        description="User domain name",
        field_type=ExportFieldType.STRING,
        column=UserRow.domain_name,
        joins=frozenset({USER_JOIN}),
    ),
    # =========================================================================
    # Keypair Resource Policy Fields (N:1, no duplication)
    # =========================================================================
    ExportFieldDef(
        key="resource_policy_created_at",
        name="Policy Created At",
        description="Resource policy creation time",
        field_type=ExportFieldType.DATETIME,
        column=KeyPairResourcePolicyRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_concurrent_sessions",
        name="Policy Max Concurrent Sessions",
        description="Maximum concurrent sessions allowed",
        field_type=ExportFieldType.INTEGER,
        column=KeyPairResourcePolicyRow.max_concurrent_sessions,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_containers_per_session",
        name="Policy Max Containers Per Session",
        description="Maximum containers per session",
        field_type=ExportFieldType.INTEGER,
        column=KeyPairResourcePolicyRow.max_containers_per_session,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_idle_timeout",
        name="Policy Idle Timeout",
        description="Idle timeout in seconds",
        field_type=ExportFieldType.INTEGER,
        column=KeyPairResourcePolicyRow.idle_timeout,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_session_lifetime",
        name="Policy Max Session Lifetime",
        description="Maximum session lifetime in seconds",
        field_type=ExportFieldType.INTEGER,
        column=KeyPairResourcePolicyRow.max_session_lifetime,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_pending_session_count",
        name="Policy Max Pending Sessions",
        description="Maximum number of pending sessions",
        field_type=ExportFieldType.INTEGER,
        column=KeyPairResourcePolicyRow.max_pending_session_count,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_pending_session_resource_slots",
        name="Policy Max Pending Session Resources",
        description="Maximum resource slots for pending sessions",
        field_type=ExportFieldType.JSON,
        column=KeyPairResourcePolicyRow.max_pending_session_resource_slots,
        formatter=_serialize_json,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    ExportFieldDef(
        key="resource_policy_max_concurrent_sftp_sessions",
        name="Policy Max Concurrent SFTP Sessions",
        description="Maximum concurrent SFTP sessions",
        field_type=ExportFieldType.INTEGER,
        column=KeyPairResourcePolicyRow.max_concurrent_sftp_sessions,
        joins=frozenset({RESOURCE_POLICY_JOIN}),
    ),
    # =========================================================================
    # Resource Group Fields (1:N, causes duplication)
    # =========================================================================
    ExportFieldDef(
        key="resource_group_name",
        name="Resource Group Name",
        description="Resource group name",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.name,
        joins=RESOURCE_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="resource_group_description",
        name="Resource Group Description",
        description="Resource group description",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.description,
        joins=RESOURCE_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="resource_group_is_active",
        name="Resource Group Active",
        description="Resource group active status",
        field_type=ExportFieldType.BOOLEAN,
        column=ScalingGroupRow.is_active,
        joins=RESOURCE_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="resource_group_scheduler",
        name="Resource Group Scheduler",
        description="Resource group scheduler type",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.scheduler,
        joins=RESOURCE_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="resource_group_wsproxy_addr",
        name="Resource Group WSProxy Address",
        description="WebSocket proxy address for resource group",
        field_type=ExportFieldType.STRING,
        column=ScalingGroupRow.wsproxy_addr,
        joins=RESOURCE_GROUP_JOINS,
    ),
    ExportFieldDef(
        key="resource_group_fair_share_spec",
        name="Resource Group Fair Share Spec",
        description="Fair share specification for resource group",
        field_type=ExportFieldType.JSON,
        column=ScalingGroupRow.fair_share_spec,
        formatter=_serialize_json,
        joins=RESOURCE_GROUP_JOINS,
    ),
    # =========================================================================
    # Session Fields (1:N, causes duplication)
    # =========================================================================
    ExportFieldDef(
        key="session_id",
        name="Session ID",
        description="Session UUID",
        field_type=ExportFieldType.UUID,
        column=SessionRow.id,
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_name",
        name="Session Name",
        description="Session name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.name,
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_status",
        name="Session Status",
        description="Session status",
        field_type=ExportFieldType.STRING,
        column=SessionRow.status,
        formatter=lambda v: str(v) if v else "",
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_type",
        name="Session Type",
        description="Session type (interactive, batch, etc.)",
        field_type=ExportFieldType.STRING,
        column=SessionRow.session_type,
        formatter=lambda v: str(v) if v else "",
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_domain_name",
        name="Session Domain",
        description="Session domain name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.domain_name,
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_group_id",
        name="Session Group ID",
        description="Session project/group UUID",
        field_type=ExportFieldType.UUID,
        column=SessionRow.group_id,
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_created_at",
        name="Session Created At",
        description="Session creation time",
        field_type=ExportFieldType.DATETIME,
        column=SessionRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_terminated_at",
        name="Session Terminated At",
        description="Session termination time",
        field_type=ExportFieldType.DATETIME,
        column=SessionRow.terminated_at,
        formatter=lambda v: v.isoformat() if v else "",
        joins=frozenset({SESSION_JOIN}),
    ),
    ExportFieldDef(
        key="session_requested_slots",
        name="Session Requested Slots",
        description="Requested resource slots for session",
        field_type=ExportFieldType.JSON,
        column=SessionRow.requested_slots,
        formatter=_serialize_json,
        joins=frozenset({SESSION_JOIN}),
    ),
]


# Report definition
KEYPAIR_REPORT = ReportDef(
    report_key="keypairs",
    name="Keypairs",
    description="Keypair (access key) export report",
    select_from=KeyPairRow.__table__,
    fields=KEYPAIR_FIELDS,
)
