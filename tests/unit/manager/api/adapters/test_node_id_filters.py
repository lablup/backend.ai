"""Every v2 filter takes the id its node carries (`entityId` / `fieldId`)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.agent.request import AgentFilter
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    AppConfigAllowListFilter,
)
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import AppConfigFragmentFilter
from ai.backend.common.dto.manager.v2.artifact.request import (
    ArtifactFilter,
    ArtifactGQLFilterInputDTO,
    ArtifactRevisionGQLFilterInputDTO,
)
from ai.backend.common.dto.manager.v2.audit_log.request import AuditLogFilter, AuditLogScopeFilter
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    ClientIPMaskingPolicyFilter,
)
from ai.backend.common.dto.manager.v2.container_registry.request import ContainerRegistryFilter
from ai.backend.common.dto.manager.v2.deployment.request import RouteFilter
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    DeploymentRevisionPresetFilter,
)
from ai.backend.common.dto.manager.v2.domain.request import DomainFilter
from ai.backend.common.dto.manager.v2.entity_label.request import EntityLabelFilter
from ai.backend.common.dto.manager.v2.entity_share.request import EntityShareFilter
from ai.backend.common.dto.manager.v2.group.request import ProjectFilter
from ai.backend.common.dto.manager.v2.idle_checker.request import IdleCheckerFilter
from ai.backend.common.dto.manager.v2.image.request import ImageFilterInputDTO
from ai.backend.common.dto.manager.v2.kernel.request import KernelFilter
from ai.backend.common.dto.manager.v2.keypair.request import KeypairFilter
from ai.backend.common.dto.manager.v2.login_client_type.request import LoginClientTypeFilter
from ai.backend.common.dto.manager.v2.login_history.request import LoginHistoryFilter
from ai.backend.common.dto.manager.v2.login_session.request import LoginSessionFilter
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationChannelFilter,
    NotificationRuleFilter,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import QueryDefinitionFilter
from ai.backend.common.dto.manager.v2.rbac.request import PermissionFilter, RoleFilter
from ai.backend.common.dto.manager.v2.resource_group.request import ResourceGroupFilter
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    KeypairResourcePolicyFilter,
    ProjectResourcePolicyFilter,
    UserResourcePolicyFilter,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import ResourcePresetFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AgentResourceFilter,
    ResourceAllocationFilter,
    ResourceSlotTypeFilter,
)
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    DomainUsageBucketFilter,
    ProjectUsageBucketFilter,
    UserUsageBucketFilter,
)
from ai.backend.common.dto.manager.v2.retention_policy.request import RetentionPolicyFilter
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    RolePermissionPresetFilter,
)
from ai.backend.common.dto.manager.v2.role_preset.request import RolePresetFilter
from ai.backend.common.dto.manager.v2.runtime_variant.request import RuntimeVariantFilter
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    RuntimeVariantPresetFilter,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    DeploymentHistoryFilter,
    KernelHistoryFilter,
    ReplicaGroupHistoryFilter,
    RouteHistoryFilter,
    SessionHistoryFilter,
)
from ai.backend.common.dto.manager.v2.service_catalog.request import ServiceCatalogFilter
from ai.backend.common.dto.manager.v2.session.request import SessionFilter
from ai.backend.common.dto.manager.v2.user.request import UserFilter
from ai.backend.common.dto.manager.v2.vfolder.request import VFolderFilter
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.api.adapters.login_history.adapter import LoginHistoryAdapter
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.api.adapters.resource_usage.adapter import ResourceUsageAdapter
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.api.adapters.scheduling_history.adapter import SchedulingHistoryAdapter
from ai.backend.manager.api.adapters.service_catalog.adapter import ServiceCatalogAdapter
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.models.clauses import QueryCondition


@dataclass(frozen=True)
class NodeIdFilterCase:
    adapter: type[BaseAdapter]
    convert: str
    filter_type: type[Any]
    field: str
    column: str
    deprecated_field: str | None = None

    def conditions(self, field: str, value: uuid.UUID) -> list[QueryCondition]:
        adapter = self.adapter.__new__(self.adapter)
        convert: Callable[[Any], list[QueryCondition]] = getattr(adapter, self.convert)
        return convert(self.filter_type(**{field: UUIDFilter(equals=value)}))


CASES = [
    NodeIdFilterCase(AgentAdapter, "_convert_filter", AgentFilter, "entity_id", "agents.uuid"),
    NodeIdFilterCase(
        AppConfigAllowListAdapter,
        "_convert_filter",
        AppConfigAllowListFilter,
        "entity_id",
        "app_config_allow_list.id",
    ),
    NodeIdFilterCase(
        AppConfigDefinitionAdapter,
        "_convert_filter",
        AppConfigDefinitionFilter,
        "entity_id",
        "app_config_definitions.id",
    ),
    NodeIdFilterCase(
        AppConfigFragmentAdapter,
        "_convert_filter",
        AppConfigFragmentFilter,
        "entity_id",
        "app_config_fragments.id",
    ),
    NodeIdFilterCase(
        ArtifactAdapter,
        "_convert_gql_filter",
        ArtifactGQLFilterInputDTO,
        "entity_id",
        "artifacts.id",
    ),
    NodeIdFilterCase(
        ArtifactAdapter, "_convert_filter", ArtifactFilter, "entity_id", "artifacts.id"
    ),
    NodeIdFilterCase(
        ArtifactAdapter,
        "_convert_gql_revision_filter",
        ArtifactRevisionGQLFilterInputDTO,
        "field_id",
        "artifact_revisions.id",
    ),
    NodeIdFilterCase(
        AuditLogAdapter, "_convert_filter", AuditLogFilter, "field_id", "audit_logs.id"
    ),
    NodeIdFilterCase(
        AuditLogAdapter,
        "_convert_scope_filter",
        AuditLogScopeFilter,
        "field_id",
        "audit_log_scopes.id",
    ),
    NodeIdFilterCase(
        BaseAdapter,
        "_convert_entity_label_filter",
        EntityLabelFilter,
        "field_id",
        "entity_labels.id",
    ),
    NodeIdFilterCase(
        ClientIPMaskingAdapter,
        "_convert_filter",
        ClientIPMaskingPolicyFilter,
        "entity_id",
        "client_ip_masking_policies.id",
    ),
    NodeIdFilterCase(
        ContainerRegistryAdapter,
        "_convert_filter",
        ContainerRegistryFilter,
        "entity_id",
        "container_registries.id",
    ),
    NodeIdFilterCase(
        DeploymentAdapter, "_convert_route_filter", RouteFilter, "field_id", "routings.id"
    ),
    NodeIdFilterCase(
        DeploymentRevisionPresetAdapter,
        "_convert_filter",
        DeploymentRevisionPresetFilter,
        "entity_id",
        "deployment_revision_presets.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        DomainAdapter,
        "_convert_domain_filter",
        DomainFilter,
        "entity_id",
        "domains.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        EntityShareAdapter, "_convert_filter", EntityShareFilter, "entity_id", "entity_shares.id"
    ),
    NodeIdFilterCase(
        IdleCheckerAdapter, "_convert_filter", IdleCheckerFilter, "entity_id", "idle_checkers.id"
    ),
    NodeIdFilterCase(
        ImageAdapter,
        "_convert_filter",
        ImageFilterInputDTO,
        "entity_id",
        "images.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        LoginClientTypeAdapter,
        "_convert_filter",
        LoginClientTypeFilter,
        "entity_id",
        "login_client_types.id",
    ),
    NodeIdFilterCase(
        LoginHistoryAdapter, "_convert_filter", LoginHistoryFilter, "field_id", "login_history.id"
    ),
    NodeIdFilterCase(
        LoginSessionAdapter, "_convert_filter", LoginSessionFilter, "field_id", "login_sessions.id"
    ),
    NodeIdFilterCase(
        NotificationAdapter,
        "_convert_channel_filter",
        NotificationChannelFilter,
        "entity_id",
        "notification_channels.id",
    ),
    NodeIdFilterCase(
        NotificationAdapter,
        "_convert_rule_filter",
        NotificationRuleFilter,
        "entity_id",
        "notification_rules.id",
    ),
    NodeIdFilterCase(
        ProjectAdapter,
        "_convert_group_filter",
        ProjectFilter,
        "entity_id",
        "groups.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        PrometheusQueryPresetAdapter,
        "_convert_filter",
        QueryDefinitionFilter,
        "entity_id",
        "prometheus_query_presets.id",
    ),
    NodeIdFilterCase(RBACAdapter, "_convert_role_filter_gql", RoleFilter, "entity_id", "roles.id"),
    NodeIdFilterCase(
        RBACAdapter, "_convert_permission_filter", PermissionFilter, "field_id", "permissions.id"
    ),
    NodeIdFilterCase(
        ResourceGroupAdapter,
        "_convert_filter",
        ResourceGroupFilter,
        "entity_id",
        "scaling_groups.id",
    ),
    NodeIdFilterCase(
        ResourcePolicyAdapter,
        "_convert_keypair_filter",
        KeypairResourcePolicyFilter,
        "entity_id",
        "keypair_resource_policies.uuid",
    ),
    NodeIdFilterCase(
        ResourcePolicyAdapter,
        "_convert_user_filter",
        UserResourcePolicyFilter,
        "entity_id",
        "user_resource_policies.uuid",
    ),
    NodeIdFilterCase(
        ResourcePolicyAdapter,
        "_convert_project_filter",
        ProjectResourcePolicyFilter,
        "entity_id",
        "project_resource_policies.uuid",
    ),
    NodeIdFilterCase(
        ResourcePresetAdapter,
        "_convert_filter",
        ResourcePresetFilter,
        "entity_id",
        "resource_presets.id",
    ),
    NodeIdFilterCase(
        ResourceSlotAdapter,
        "_convert_slot_type_filter",
        ResourceSlotTypeFilter,
        "entity_id",
        "resource_slot_types.uuid",
    ),
    NodeIdFilterCase(
        ResourceSlotAdapter,
        "_convert_agent_resource_filter",
        AgentResourceFilter,
        "field_id",
        "agent_resources.id",
    ),
    NodeIdFilterCase(
        ResourceSlotAdapter,
        "_convert_resource_allocation_filter",
        ResourceAllocationFilter,
        "field_id",
        "resource_allocations.id",
    ),
    NodeIdFilterCase(
        ResourceUsageAdapter,
        "_convert_domain_filter",
        DomainUsageBucketFilter,
        "field_id",
        "domain_usage_buckets.id",
    ),
    NodeIdFilterCase(
        ResourceUsageAdapter,
        "_convert_project_filter",
        ProjectUsageBucketFilter,
        "field_id",
        "project_usage_buckets.id",
    ),
    NodeIdFilterCase(
        ResourceUsageAdapter,
        "_convert_user_filter",
        UserUsageBucketFilter,
        "field_id",
        "user_usage_buckets.id",
    ),
    NodeIdFilterCase(
        RetentionPolicyAdapter,
        "_convert_filter",
        RetentionPolicyFilter,
        "entity_id",
        "retention_policies.id",
    ),
    NodeIdFilterCase(
        RolePresetAdapter,
        "_convert_filter",
        RolePresetFilter,
        "entity_id",
        "role_presets.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        RolePresetAdapter,
        "_convert_permission_filter",
        RolePermissionPresetFilter,
        "field_id",
        "role_permission_presets.id",
    ),
    NodeIdFilterCase(
        RuntimeVariantAdapter,
        "_convert_filter",
        RuntimeVariantFilter,
        "entity_id",
        "runtime_variants.id",
    ),
    NodeIdFilterCase(
        RuntimeVariantPresetAdapter,
        "_convert_filter",
        RuntimeVariantPresetFilter,
        "entity_id",
        "runtime_variant_presets.id",
    ),
    NodeIdFilterCase(
        SchedulingHistoryAdapter,
        "_convert_session_filter",
        SessionHistoryFilter,
        "field_id",
        "session_scheduling_history.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        SchedulingHistoryAdapter,
        "_convert_kernel_filter",
        KernelHistoryFilter,
        "field_id",
        "kernel_scheduling_history.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        SchedulingHistoryAdapter,
        "_convert_deployment_filter",
        DeploymentHistoryFilter,
        "field_id",
        "deployment_history.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        SchedulingHistoryAdapter,
        "_convert_replica_group_filter",
        ReplicaGroupHistoryFilter,
        "field_id",
        "replica_group_history.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        SchedulingHistoryAdapter,
        "_convert_route_filter",
        RouteHistoryFilter,
        "field_id",
        "route_history.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        ServiceCatalogAdapter,
        "_convert_filter",
        ServiceCatalogFilter,
        "entity_id",
        "service_catalog.id",
    ),
    NodeIdFilterCase(
        SessionAdapter,
        "_convert_session_filter",
        SessionFilter,
        "entity_id",
        "sessions.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        SessionAdapter,
        "_convert_kernel_filter",
        KernelFilter,
        "field_id",
        "kernels.id",
        deprecated_field="id",
    ),
    NodeIdFilterCase(
        UserAdapter,
        "_convert_user_filter",
        UserFilter,
        "entity_id",
        "users.uuid",
        deprecated_field="uuid",
    ),
    NodeIdFilterCase(
        UserAdapter, "_convert_keypair_filter", KeypairFilter, "field_id", "keypairs.id"
    ),
    NodeIdFilterCase(
        VFolderAdapter, "_convert_vfolder_filter", VFolderFilter, "entity_id", "vfolders.id"
    ),
]


def _compile(conditions: list[QueryCondition]) -> tuple[str, dict[str, Any]]:
    assert len(conditions) == 1
    compiled = conditions[0]().compile()
    return str(compiled), dict(compiled.params)


def _case_id(case: NodeIdFilterCase) -> str:
    return f"{case.filter_type.__name__}.{case.field}"


class TestNodeIdFilter:
    @pytest.mark.parametrize("case", CASES, ids=_case_id)
    def test_equals_matches_the_node_id_column(self, case: NodeIdFilterCase) -> None:
        value = uuid.uuid4()

        sql, params = _compile(case.conditions(case.field, value))

        assert case.column in sql
        assert value in params.values()

    @pytest.mark.parametrize(
        "case", [c for c in CASES if c.deprecated_field is not None], ids=_case_id
    )
    def test_deprecated_id_matches_the_same_rows(self, case: NodeIdFilterCase) -> None:
        assert case.deprecated_field is not None
        value = uuid.uuid4()

        assert _compile(case.conditions(case.deprecated_field, value)) == _compile(
            case.conditions(case.field, value)
        )
