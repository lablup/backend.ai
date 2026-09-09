"""The wiring-time spec catalog vs the v2 actions defined in the import closure.

Constructing a v2-wired package accumulates every wired spec on its registry, and
recursing ``__subclasses__()`` from the five v2 action bases finds every concrete
v2 action class defined. The two sets matching is what catches an action that was
defined but never wired. A new v2 wiring extends this guard by being imported and
constructed here.

The same sweep also holds every action to the audit identity contract: the
``(entity_type, operation, action_name)`` triple must be unique and the name must
be a lowercase snake_case phrase, so recorded rows stay distinguishable and
filterable.
"""

from __future__ import annotations

import inspect
import re
from typing import Any
from unittest.mock import MagicMock

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.app_config import AppConfigEntityType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListEntityType
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionEntityType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionFieldType
from ai.backend.common.data.entity.audit_log import AuditLogFieldType
from ai.backend.common.data.entity.auth import AuthFieldType
from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.entity_label import EntityLabelFieldType
from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.export import ExportEntityType
from ai.backend.common.data.entity.fair_share import (
    DomainFairShareEntityType,
    ProjectFairShareEntityType,
    UserFairShareEntityType,
)
from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.notification import (
    NotificationChannelEntityType,
    NotificationRuleEntityType,
)
from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.prometheus_query_preset import (
    PrometheusQueryPresetEntityType,
)
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.retention_policy import RetentionPolicyEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.common.data.entity.service_catalog import ServiceCatalogEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.session_template import SessionTemplateEntityType
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.entity.vfolder_invitation import VFolderInvitationEntityType
from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.types import ActionGate, ActionKind
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.field.base import (
    BaseRuntimeSingleFieldAction,
    BaseSingleFieldAction,
)
from ai.backend.manager.actions.v2.field.bulk_base import BaseBulkFieldAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.bulk_base import BaseBulkLookupAction
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.agent.actions.bulk_get import BulkGetAgentsAction
from ai.backend.manager.services.agent.actions.bulk_load_container_counts import (
    BulkLoadContainerCountsAction,
)
from ai.backend.manager.services.agent.actions.bulk_load_permissions import (
    BulkLoadAgentPermissionsAction,
)
from ai.backend.manager.services.agent.actions.bulk_lookup import BulkLookupAgentsAction
from ai.backend.manager.services.agent.actions.get_total_resources import (
    GetTotalResourcesAction,
)
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
)
from ai.backend.manager.services.agent.actions.lookup import LookupAgentAction
from ai.backend.manager.services.agent.actions.lookup_resource_owner import (
    LookupAgentResourceOwnerAction,
    LookupBulkAgentResourceOwnerAction,
)
from ai.backend.manager.services.agent.actions.scoped_search_resources import (
    ScopedSearchAgentResourcesAction,
)
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.app_config.processors import AppConfigProcessors
from ai.backend.manager.services.artifact.actions.bulk_get import BulkGetArtifactsAction
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.revision.actions.bulk_get import (
    BulkGetArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.manager.services.artifact.revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.deployment.actions.access_token.bulk_get_access_tokens import (
    BulkGetAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.bulk_get_deployment_policies import (
    BulkGetDeploymentPoliciesAction,
)
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkDeploymentAccessTokenOwnerAction,
    LookupBulkReplicaOwnerAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.bulk_get_revisions import (
    BulkGetRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.replica.bulk_get_replicas import (
    BulkGetReplicasAction,
)
from ai.backend.manager.services.deployment.actions.route.bulk_get_routes import (
    BulkGetRoutesAction,
)
from ai.backend.manager.services.deployment.actions.scoped_search import (
    ScopedSearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment_revision_preset.processors import (
    DeploymentPresetProcessors,
)
from ai.backend.manager.services.domain.actions.bulk_get import BulkGetDomainsAction
from ai.backend.manager.services.domain.actions.bulk_lookup import BulkLookupDomainsAction
from ai.backend.manager.services.domain.actions.get import GetDomainAction
from ai.backend.manager.services.domain.actions.scoped_search import ScopedSearchDomainsAction
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
    LookupEntityLabelOwnerAction,
)
from ai.backend.manager.services.entity_label.processors import EntityLabelProcessors
from ai.backend.manager.services.entity_share.processors import (
    EntityShareProcessors,
)
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.idle_checker_assignment.processors import (
    IdleCheckerAssignmentProcessors,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.login_client_type.processors import (
    LoginClientTypeProcessors,
)
from ai.backend.manager.services.metric.processors import MetricProcessors
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.notification.actions.bulk_get_channels import (
    BulkGetChannelsAction,
)
from ai.backend.manager.services.notification.actions.bulk_get_rules import BulkGetRulesAction
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.services.prometheus_query_preset_category.processors import (
    PrometheusQueryPresetCategoryProcessors,
)
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.resource_group.actions.bulk_get import (
    BulkGetResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.bulk_lookup import (
    BulkLookupResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.get_preset import (
    GetResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.retention_policy.processors import RetentionPolicyProcessors
from ai.backend.manager.services.role_preset.processors import RolePresetProcessors
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors
from ai.backend.manager.services.runtime_variant_preset.processors import (
    RuntimeVariantPresetProcessors,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_deployment_histories import (
    BulkGetDeploymentHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_kernel_histories import (
    BulkGetKernelHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_route_histories import (
    BulkGetRouteHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_session_histories import (
    BulkGetSessionHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkKernelSchedulingHistoryOwnerAction,
    LookupBulkSessionSchedulingHistoryOwnerAction,
)
from ai.backend.manager.services.scheduling_history.processors import (
    SchedulingHistoryProcessors,
)
from ai.backend.manager.services.service_catalog.processors import ServiceCatalogProcessors
from ai.backend.manager.services.session.actions.compute_schedule import (
    ComputeScheduleAction,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.storage_namespace.processors import (
    StorageNamespaceProcessors,
)
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user_resource_policy.processors import (
    UserResourcePolicyProcessors,
)
from ai.backend.manager.services.vfolder.processors.file import VFolderFileProcessors
from ai.backend.manager.services.vfolder.processors.invite import VFolderInviteProcessors
from ai.backend.manager.services.vfolder.processors.sharing import VFolderSharingProcessors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.processors.vfolder_admin import VFolderAdminProcessors
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors

_V2_ACTION_BASES: tuple[type[Any], ...] = (
    BaseSingleEntityAction,
    BaseBulkAction,
    BaseScopeAction,
    BaseRelationAction,
    BaseGlobalAction,
    BaseLookupAction,
    BaseBulkLookupAction,
    BaseSingleFieldAction,
    BaseRuntimeSingleFieldAction,
    BaseBulkFieldAction,
)

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def _concrete_v2_action_classes() -> set[type[Any]]:
    """Every non-abstract v2 action class defined in the imported manager modules.

    Filtered to the manager package so action classes defined locally by other test
    modules in the same process cannot leak into the sweep.
    """
    found: set[type[Any]] = set()
    stack: list[type[Any]] = list(_V2_ACTION_BASES)
    while stack:
        cls = stack.pop()
        for subclass in cls.__subclasses__():
            stack.append(subclass)
            if not inspect.isabstract(subclass) and subclass.__module__.startswith(
                "ai.backend.manager."
            ):
                found.add(subclass)
    return found


def _ops_registry() -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(MagicMock()),
        )
    )


def test_every_defined_v2_action_is_wired() -> None:
    # One shared registry, as in the production wiring: every v2 package registers
    # through it, so its wired_actions() is the complete catalog of registered actions.
    registry = _ops_registry()
    fair_share_groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    artifact_revisions = registry.group(GroupMeta(ArtifactEntityType())).field_group(
        FieldGroupMeta(ArtifactRevisionFieldType()),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    resource_slot_groups = registry.concern(ConcernMeta(Concern.SYSTEM))
    scheduling_history_groups = registry.concern(ConcernMeta(Concern.SESSION))
    resource_allocation_groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    agent_groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    AgentProcessors(agent_groups.group(GroupMeta(AgentEntityType())), MagicMock(), [])
    AppConfigProcessors(
        registry.group(GroupMeta(AppConfigEntityType())),
        registry.group(GroupMeta(AppConfigDefinitionEntityType())),
        registry.group(GroupMeta(AppConfigAllowListEntityType())),
        registry.group(GroupMeta(AppConfigFragmentEntityType())),
        MagicMock(),
    )
    ResourceSlotProcessors(
        resource_slot_groups.group(GroupMeta(ResourceSlotTypeEntityType())),
        resource_slot_groups.group(GroupMeta(SessionEntityType())),
        resource_slot_groups.group(GroupMeta(AgentEntityType())),
        MagicMock(),
    )
    IdleCheckerProcessors(
        registry.group(GroupMeta(IdleCheckerEntityType())),
        registry.group(GroupMeta(SessionEntityType())),
        MagicMock(),
    )
    IdleCheckerAssignmentProcessors(
        scheduling_history_groups.group(GroupMeta(IdleCheckerEntityType())),
        MagicMock(),
    )
    RetentionPolicyProcessors(registry.group(GroupMeta(RetentionPolicyEntityType())))
    LoginClientTypeProcessors(registry.group(GroupMeta(LoginClientTypeEntityType())))
    ServiceCatalogProcessors(registry.group(GroupMeta(ServiceCatalogEntityType())))
    ProjectResourcePolicyProcessors(registry.group(GroupMeta(ProjectResourcePolicyEntityType())))
    UserResourcePolicyProcessors(registry.group(GroupMeta(UserResourcePolicyEntityType())))
    KeypairResourcePolicyProcessors(registry.group(GroupMeta(KeyPairResourcePolicyEntityType())))
    RolePresetProcessors(registry.group(GroupMeta(RolePresetEntityType())), MagicMock())
    EntityShareProcessors(registry.group(GroupMeta(EntityShareEntityType())), MagicMock())
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        [],
    )
    RuntimeVariantProcessors(registry.group(GroupMeta(RuntimeVariantEntityType())))
    ObjectStorageProcessors(
        registry.group(GroupMeta(ObjectStorageEntityType())),
        artifact_revisions,
        MagicMock(),
    )
    VFSStorageProcessors(registry.group(GroupMeta(VFSStorageEntityType())), MagicMock())
    NotificationProcessors(
        registry.group(GroupMeta(NotificationChannelEntityType())),
        registry.group(GroupMeta(NotificationRuleEntityType())),
        MagicMock(),
    )
    PrometheusQueryPresetCategoryProcessors(
        registry.group(GroupMeta(PrometheusQueryPresetCategoryEntityType()))
    )
    MetricProcessors(
        registry.group(GroupMeta(PrometheusQueryPresetEntityType())),
        registry.group(GroupMeta(UserEntityType())),
        registry.group(GroupMeta(SessionEntityType())),
        MagicMock(),
    )
    RuntimeVariantPresetProcessors(
        registry.group(GroupMeta(RuntimeVariantPresetEntityType())), MagicMock()
    )
    AuditLogProcessors(
        registry.dangling_field_group(FieldGroupMeta(AuditLogFieldType()), AuditLogData)
    )
    EntityLabelProcessors(
        registry.dangling_lookup_field_group(
            FieldGroupMeta(EntityLabelFieldType()),
            EntityLabelData,
            LookupEntityLabelOwnerAction,
            LookupBulkEntityLabelOwnerAction,
        )
    )
    PrometheusQueryPresetProcessors(
        registry.group(GroupMeta(PrometheusQueryPresetEntityType())), MagicMock()
    )
    StorageNamespaceProcessors(registry.group(GroupMeta(StorageNamespaceEntityType())))
    DeploymentPresetProcessors(registry.group(GroupMeta(DeploymentPresetEntityType())), MagicMock())
    DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock(), [])
    PermissionControllerProcessors(
        registry.group(GroupMeta(RoleEntityType())), MagicMock(), [], MagicMock()
    )
    ProjectProcessors(registry.group(GroupMeta(ProjectEntityType())), MagicMock())
    UserProcessors(
        registry.group(GroupMeta(UserEntityType())),
        MagicMock(),
    )
    AuthProcessors(
        registry.dangling_field_group(FieldGroupMeta(AuthFieldType())),
        registry.group(GroupMeta(UserEntityType())),
        MagicMock(),
    )
    FairShareProcessors(
        fair_share_groups.group(GroupMeta(DomainFairShareEntityType())),
        fair_share_groups.group(GroupMeta(ProjectFairShareEntityType())),
        fair_share_groups.group(GroupMeta(UserFairShareEntityType())),
        MagicMock(),
    )
    ResourcePresetProcessors(registry.group(GroupMeta(ResourcePresetEntityType())), MagicMock())
    ResourceGroupProcessors(registry.group(GroupMeta(ResourceGroupEntityType())), MagicMock())
    ArtifactProcessors(
        registry.group(GroupMeta(ArtifactEntityType())),
        artifact_revisions,
        ArtifactRevisionProcessors(
            registry.group(GroupMeta(ArtifactEntityType())),
            artifact_revisions,
            MagicMock(),
        ),
        MagicMock(),
    )
    ArtifactRegistryProcessors(registry.group(GroupMeta(ArtifactRegistryEntityType())), MagicMock())
    ModelCardProcessors(registry.group(GroupMeta(ModelCardEntityType())), MagicMock())
    ContainerRegistryProcessors(
        registry.group(GroupMeta(ContainerRegistryEntityType())), MagicMock()
    )
    ImageProcessors(registry.group(GroupMeta(ImageEntityType())), MagicMock())
    ExportProcessors(registry.group(GroupMeta(ExportEntityType())), MagicMock())
    TemplateProcessors(registry.group(GroupMeta(SessionTemplateEntityType())), MagicMock())
    SchedulingHistoryProcessors(
        scheduling_history_groups.group(GroupMeta(SessionEntityType())),
        scheduling_history_groups.group(GroupMeta(DeploymentEntityType())),
        scheduling_history_groups.group(GroupMeta(DeploymentEntityType())),
        MagicMock(),
    )
    SessionProcessors(
        registry.group(GroupMeta(SessionEntityType())),
        resource_allocation_groups.group(GroupMeta(ResourceGroupEntityType())),
        ResourceAllocationProcessors(
            resource_allocation_groups.group(GroupMeta(UserEntityType())),
            resource_allocation_groups.group(GroupMeta(ProjectEntityType())),
            resource_allocation_groups.group(GroupMeta(DomainEntityType())),
            resource_allocation_groups.group(GroupMeta(ResourceGroupEntityType())),
            resource_allocation_groups.group(GroupMeta(SessionEntityType())),
            resource_allocation_groups.group(GroupMeta(ResourcePresetEntityType())),
            MagicMock(),
        ),
        MagicMock(),
    )
    DeploymentProcessors(registry.group(GroupMeta(DeploymentEntityType())), MagicMock())
    VFolderProcessors(registry.group(GroupMeta(VFolderEntityType())), MagicMock())
    VFolderAdminProcessors(registry.group(GroupMeta(VFolderEntityType())), MagicMock())
    VFolderFileProcessors(registry.group(GroupMeta(VFolderEntityType())), MagicMock())
    VFolderInviteProcessors(registry.group(GroupMeta(VFolderInvitationEntityType())), MagicMock())
    VFolderSharingProcessors(registry.group(GroupMeta(VFolderEntityType())), MagicMock())
    ModelServingProcessors(registry.group(GroupMeta(DeploymentEntityType())), MagicMock())
    ModelServingAutoScalingProcessors(
        registry.group(GroupMeta(DeploymentEntityType())), MagicMock()
    )

    # One action class may be wired more than once -- an owner lookup is built by every
    # field operation that runs it first -- and the catalog is which classes are wired.
    wired = sorted({cls.action_name() for cls in registry.wired_actions()})
    defined = sorted(cls.action_name() for cls in _concrete_v2_action_classes())

    assert wired == defined


def test_action_names_follow_the_snake_case_convention() -> None:
    for cls in _concrete_v2_action_classes():
        name = cls.action_name()
        assert _SNAKE_CASE.fullmatch(name), (
            f"{cls.__module__}.{cls.__qualname__} declares action_name()={name!r}, "
            "which is not a lowercase snake_case phrase."
        )


def test_action_name_is_unique_across_v2_actions() -> None:
    """Audit rows identify the run by its action name.

    The entity type no longer joins it: a single-entity action derives that from the id
    it names and a field action has none until its owner is read, so the name alone has
    to tell two runs apart.
    """
    seen: dict[str, type[Any]] = {}
    for cls in _concrete_v2_action_classes():
        name = cls.action_name()
        holder = seen.setdefault(name, cls)
        assert holder is cls, (
            f"{cls.__module__}.{cls.__qualname__} and {holder.__module__}.{holder.__qualname__} "
            f"both record as {name!r}; declare a distinct action_name() on one of them."
        )


def test_resource_preset_reads_keep_their_judged_gates() -> None:
    """Pins the three preset reads BA-7710 ruled on, so a rewiring has to restate them.

    A preset is a catalog: its name, resource slots and shared memory hold no owner
    and no secret. The two reads a session launcher makes start from a resource group
    name and stay public; the read the admin route makes starts from the preset's id,
    so it is judged on that entity like the update and the delete beside it.
    """
    registry = _ops_registry()
    ResourcePresetProcessors(registry.group(GroupMeta(ResourcePresetEntityType())), MagicMock())

    judged = {
        ListResourcePresetsAction: (
            ResourcePresetEntityType(),
            ActionKind.GLOBAL,
            ActionGate.PUBLIC,
        ),
        CheckResourcePresetsAction: (
            ResourcePresetEntityType(),
            ActionKind.GLOBAL,
            ActionGate.PUBLIC,
        ),
        GetResourcePresetAction: (
            ResourcePresetEntityType(),
            ActionKind.SINGLE_ENTITY,
            ActionGate.PERMISSION,
        ),
    }
    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
        if record.action_cls in judged
    }
    assert recorded == judged


def test_resource_domain_and_agent_reads_keep_their_judged_gates() -> None:
    """Pins the five reads BA-7673 ruled on, so a rewiring has to restate the ruling.

    The gate is decided by the factory a processor is wired through, not by the action
    class, so the catalog record is what the assertion reads.
    """
    registry = _ops_registry()
    resource_group_groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    AgentProcessors(resource_group_groups.group(GroupMeta(AgentEntityType())), MagicMock(), [])
    DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock(), [])
    SessionProcessors(
        registry.group(GroupMeta(SessionEntityType())),
        resource_group_groups.group(GroupMeta(ResourceGroupEntityType())),
        ResourceAllocationProcessors(
            resource_group_groups.group(GroupMeta(UserEntityType())),
            resource_group_groups.group(GroupMeta(ProjectEntityType())),
            resource_group_groups.group(GroupMeta(DomainEntityType())),
            resource_group_groups.group(GroupMeta(ResourceGroupEntityType())),
            resource_group_groups.group(GroupMeta(SessionEntityType())),
            resource_group_groups.group(GroupMeta(ResourcePresetEntityType())),
            MagicMock(),
        ),
        MagicMock(),
    )

    judged = {
        ComputeScheduleAction: (
            ResourceGroupEntityType(),
            ActionKind.SINGLE_ENTITY,
            ActionGate.PERMISSION,
        ),
        GetDomainAction: (
            DomainEntityType(),
            ActionKind.SINGLE_ENTITY,
            ActionGate.PERMISSION,
        ),
        GetTotalResourcesAction: (AgentEntityType(), ActionKind.GLOBAL, ActionGate.PERMISSION),
        # Admin search surfaces only: the DataLoaders read per named agent below.
        SearchAgentsAction: (AgentEntityType(), ActionKind.GLOBAL, ActionGate.PERMISSION),
        LoadContainerCountsAction: (AgentEntityType(), ActionKind.GLOBAL, ActionGate.PERMISSION),
        # What the DataLoaders read: checked per agent.
        BulkGetAgentsAction: (AgentEntityType(), ActionKind.BULK, ActionGate.PERMISSION),
        BulkLoadContainerCountsAction: (
            AgentEntityType(),
            ActionKind.BULK,
            ActionGate.PERMISSION,
        ),
        BulkLoadAgentPermissionsAction: (
            AgentEntityType(),
            ActionKind.BULK,
            ActionGate.PERMISSION,
        ),
        # The lookup carries no permission; the read that follows it is checked.
        LookupAgentAction: (AgentEntityType(), ActionKind.LOOKUP, ActionGate.PUBLIC),
        BulkLookupAgentsAction: (AgentEntityType(), ActionKind.LOOKUP, ActionGate.PUBLIC),
        # The slot rows are field rows of the agent: read per named agent, owner resolved
        # through the lookups the field group builds.
        LookupAgentResourceOwnerAction: (
            AgentEntityType(),
            ActionKind.LOOKUP,
            ActionGate.PERMISSION,
        ),
        LookupBulkAgentResourceOwnerAction: (
            AgentEntityType(),
            ActionKind.LOOKUP,
            ActionGate.PERMISSION,
        ),
        ScopedSearchAgentResourcesAction: (
            AgentEntityType(),
            ActionKind.BULK,
            ActionGate.PERMISSION,
        ),
    }
    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
        if record.action_cls in judged
    }
    assert recorded == judged


def test_artifact_registry_metas_read_is_a_partial_bulk_permission_read() -> None:
    """The named registries are read one permission check per registry, not superadmin-only."""
    registry = _ops_registry()
    ArtifactRegistryProcessors(registry.group(GroupMeta(ArtifactRegistryEntityType())), MagicMock())

    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
    }
    assert recorded[GetArtifactRegistryMetasAction] == (
        ArtifactRegistryEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )


def test_rg_domain_read_is_a_scoped_permission_read() -> None:
    """The domains a resource group serves are read within the resource-group scope."""
    registry = _ops_registry()
    DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock(), [])

    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
    }
    assert recorded[ScopedSearchDomainsAction] == (
        DomainEntityType(),
        ActionKind.SCOPE,
        ActionGate.PERMISSION,
    )


def test_scoped_deployment_read_is_a_scoped_permission_read() -> None:
    """A user's own deployments and a project's deployments are read within that scope."""
    registry = _ops_registry()
    DeploymentProcessors(registry.group(GroupMeta(DeploymentEntityType())), MagicMock())

    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
    }
    assert recorded[ScopedSearchDeploymentsAction] == (
        DeploymentEntityType(),
        ActionKind.SCOPE,
        ActionGate.PERMISSION,
    )


def test_field_data_loader_reads_are_partial_permission_reads() -> None:
    """The DataLoaders over field rows read per named row, checked per owning entity.

    The owner lookup a partial field read runs first is recorded public beside its
    permission-gated record: it refuses nothing, the read that follows answers per owner.
    """
    registry = _ops_registry()
    DeploymentProcessors(registry.group(GroupMeta(DeploymentEntityType())), MagicMock())
    SchedulingHistoryProcessors(
        registry.group(GroupMeta(SessionEntityType())),
        registry.group(GroupMeta(DeploymentEntityType())),
        registry.group(GroupMeta(DeploymentEntityType())),
        MagicMock(),
    )

    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
        if record.kind == ActionKind.BULK
    }
    partial = (DeploymentEntityType(), ActionKind.BULK, ActionGate.PERMISSION)
    assert recorded[BulkGetRevisionsAction] == partial
    assert recorded[BulkGetReplicasAction] == partial
    assert recorded[BulkGetRoutesAction] == partial
    assert recorded[BulkGetAccessTokensAction] == partial
    assert recorded[BulkGetDeploymentPoliciesAction] == partial
    assert recorded[BulkGetDeploymentHistoriesAction] == partial
    assert recorded[BulkGetRouteHistoriesAction] == partial
    assert recorded[BulkGetSessionHistoriesAction] == (
        SessionEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )
    assert recorded[BulkGetKernelHistoriesAction] == (
        SessionEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )

    lookup_gates = {
        (record.action_cls, record.gate)
        for record in registry.wired_processors()
        if record.kind == ActionKind.LOOKUP
    }
    for owner_lookup in (
        LookupBulkReplicaOwnerAction,
        LookupBulkDeploymentAccessTokenOwnerAction,
        LookupBulkSessionSchedulingHistoryOwnerAction,
        LookupBulkKernelSchedulingHistoryOwnerAction,
    ):
        assert (owner_lookup, ActionGate.PUBLIC) in lookup_gates
        assert (owner_lookup, ActionGate.PERMISSION) in lookup_gates


def test_entity_data_loader_reads_are_checked_per_entity_except_domains() -> None:
    """The resource group, notification and artifact DataLoaders read per named
    entity; the domain one is public, since a regular user holds no read on domains.
    """
    registry = _ops_registry()
    ResourceGroupProcessors(registry.group(GroupMeta(ResourceGroupEntityType())), MagicMock())
    DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock(), [])
    NotificationProcessors(
        registry.group(GroupMeta(NotificationChannelEntityType())),
        registry.group(GroupMeta(NotificationRuleEntityType())),
        MagicMock(),
    )
    artifact_revisions = registry.group(GroupMeta(ArtifactEntityType())).field_group(
        FieldGroupMeta(ArtifactRevisionFieldType()),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    ArtifactProcessors(
        registry.group(GroupMeta(ArtifactEntityType())),
        artifact_revisions,
        ArtifactRevisionProcessors(
            registry.group(GroupMeta(ArtifactEntityType())),
            artifact_revisions,
            MagicMock(),
        ),
        MagicMock(),
    )

    recorded = {
        record.action_cls: (record.entity_type, record.kind, record.gate)
        for record in registry.wired_processors()
    }
    assert recorded[BulkGetResourceGroupsAction] == (
        ResourceGroupEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )
    assert recorded[BulkLookupResourceGroupsAction] == (
        ResourceGroupEntityType(),
        ActionKind.LOOKUP,
        ActionGate.PUBLIC,
    )
    assert recorded[BulkGetChannelsAction] == (
        NotificationChannelEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )
    assert recorded[BulkGetRulesAction] == (
        NotificationRuleEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )
    assert recorded[BulkGetArtifactsAction] == (
        ArtifactEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )
    assert recorded[BulkGetArtifactRevisionsAction] == (
        ArtifactEntityType(),
        ActionKind.BULK,
        ActionGate.PERMISSION,
    )
    assert recorded[BulkGetDomainsAction] == (
        DomainEntityType(),
        ActionKind.BULK,
        ActionGate.PUBLIC,
    )
    assert recorded[BulkLookupDomainsAction] == (
        DomainEntityType(),
        ActionKind.LOOKUP,
        ActionGate.PUBLIC,
    )
