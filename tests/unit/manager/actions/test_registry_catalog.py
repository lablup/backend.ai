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

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.app_config import (
    APP_CONFIG_ALLOW_LIST_ENTITY_TYPE,
    APP_CONFIG_ENTITY_TYPE,
    APP_CONFIG_FRAGMENT_ENTITY_TYPE,
)
from ai.backend.common.data.entity.app_config_definition import APP_CONFIG_DEFINITION_ENTITY_TYPE
from ai.backend.common.data.entity.artifact import ARTIFACT_ENTITY_TYPE
from ai.backend.common.data.entity.artifact_registry import ARTIFACT_REGISTRY_ENTITY_TYPE
from ai.backend.common.data.entity.artifact_revision import ARTIFACT_REVISION_FIELD_TYPE
from ai.backend.common.data.entity.audit_log import AUDIT_LOG_FIELD_TYPE
from ai.backend.common.data.entity.container_registry import CONTAINER_REGISTRY_ENTITY_TYPE
from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE
from ai.backend.common.data.entity.deployment_preset import DEPLOYMENT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.export import EXPORT_ENTITY_TYPE
from ai.backend.common.data.entity.fair_share import (
    DOMAIN_FAIR_SHARE_ENTITY_TYPE,
    PROJECT_FAIR_SHARE_ENTITY_TYPE,
    USER_FAIR_SHARE_ENTITY_TYPE,
)
from ai.backend.common.data.entity.image import IMAGE_ENTITY_TYPE
from ai.backend.common.data.entity.login_client_type import LOGIN_CLIENT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.notification import (
    NOTIFICATION_CHANNEL_ENTITY_TYPE,
    NOTIFICATION_RULE_ENTITY_TYPE,
)
from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.runtime_variant_preset import RUNTIME_VARIANT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.service_catalog import SERVICE_CATALOG_ENTITY_TYPE
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.session_template import SESSION_TEMPLATE_ENTITY_TYPE
from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE
from ai.backend.common.data.entity.vfolder_invitation import VFOLDER_INVITATION_ENTITY_TYPE
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.field.bulk_base import BaseBulkFieldAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.bulk_base import BaseBulkLookupAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.app_config.processors import AppConfigProcessors
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.manager.services.artifact.revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment_revision_preset.processors import (
    DeploymentPresetProcessors,
)
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.login_client_type.processors import (
    LoginClientTypeProcessors,
)
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
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
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.retention_policy.processors import RetentionPolicyProcessors
from ai.backend.manager.services.role_preset.processors import RolePresetProcessors
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors
from ai.backend.manager.services.runtime_variant_preset.processors import (
    RuntimeVariantPresetProcessors,
)
from ai.backend.manager.services.scheduling_history.processors import (
    SchedulingHistoryProcessors,
)
from ai.backend.manager.services.service_catalog.processors import ServiceCatalogProcessors
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
    BaseGlobalAction,
    BaseLookupAction,
    BaseBulkLookupAction,
    BaseSingleFieldAction,
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
    fair_share_groups = registry.concern(ConcernMeta("fair_share"))
    artifact_revisions = registry.group(GroupMeta(ARTIFACT_ENTITY_TYPE)).field_group(
        FieldGroupMeta(ARTIFACT_REVISION_FIELD_TYPE),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    resource_slot_groups = registry.concern(ConcernMeta("resource_slot"))
    scheduling_history_groups = registry.concern(ConcernMeta("scheduling_history"))
    resource_allocation_groups = registry.concern(ConcernMeta("resource_allocation"))
    AppConfigProcessors(
        registry.group(GroupMeta(APP_CONFIG_ENTITY_TYPE)),
        registry.group(GroupMeta(APP_CONFIG_DEFINITION_ENTITY_TYPE)),
        registry.group(GroupMeta(APP_CONFIG_ALLOW_LIST_ENTITY_TYPE)),
        registry.group(GroupMeta(APP_CONFIG_FRAGMENT_ENTITY_TYPE)),
        MagicMock(),
    )
    ResourceSlotProcessors(
        resource_slot_groups.group(GroupMeta(RESOURCE_SLOT_TYPE_ENTITY_TYPE)),
        resource_slot_groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
        resource_slot_groups.group(GroupMeta(AGENT_ENTITY_TYPE)),
        MagicMock(),
    )
    IdleCheckerProcessors(registry.group(GroupMeta(SESSION_ENTITY_TYPE)), MagicMock(), [])
    RetentionPolicyProcessors(registry.group(GroupMeta(RETENTION_POLICY_ENTITY_TYPE)))
    LoginClientTypeProcessors(registry.group(GroupMeta(LOGIN_CLIENT_TYPE_ENTITY_TYPE)))
    ServiceCatalogProcessors(registry.group(GroupMeta(SERVICE_CATALOG_ENTITY_TYPE)))
    ProjectResourcePolicyProcessors(registry.group(GroupMeta(PROJECT_RESOURCE_POLICY_ENTITY_TYPE)))
    UserResourcePolicyProcessors(registry.group(GroupMeta(USER_RESOURCE_POLICY_ENTITY_TYPE)))
    KeypairResourcePolicyProcessors(registry.group(GroupMeta(KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE)))
    RolePresetProcessors(registry.group(GroupMeta(ROLE_PRESET_ENTITY_TYPE)), MagicMock())
    RuntimeVariantProcessors(registry.group(GroupMeta(RUNTIME_VARIANT_ENTITY_TYPE)))
    ObjectStorageProcessors(
        registry.group(GroupMeta(OBJECT_STORAGE_ENTITY_TYPE)),
        artifact_revisions,
        MagicMock(),
    )
    VFSStorageProcessors(registry.group(GroupMeta(VFS_STORAGE_ENTITY_TYPE)), MagicMock())
    NotificationProcessors(
        registry.group(GroupMeta(NOTIFICATION_CHANNEL_ENTITY_TYPE)),
        registry.group(GroupMeta(NOTIFICATION_RULE_ENTITY_TYPE)),
        MagicMock(),
    )
    PrometheusQueryPresetCategoryProcessors(
        registry.group(GroupMeta(PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE))
    )
    RuntimeVariantPresetProcessors(
        registry.group(GroupMeta(RUNTIME_VARIANT_PRESET_ENTITY_TYPE)), MagicMock()
    )
    AuditLogProcessors(
        registry.dangling_field_group(FieldGroupMeta(AUDIT_LOG_FIELD_TYPE), AuditLogData)
    )
    PrometheusQueryPresetProcessors(
        registry.group(GroupMeta(PROMETHEUS_QUERY_PRESET_ENTITY_TYPE)), MagicMock()
    )
    StorageNamespaceProcessors(registry.group(GroupMeta(STORAGE_NAMESPACE_ENTITY_TYPE)))
    DeploymentPresetProcessors(
        registry.group(GroupMeta(DEPLOYMENT_PRESET_ENTITY_TYPE)), MagicMock()
    )
    DomainProcessors(registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)), MagicMock(), [])
    ProjectProcessors(registry.group(GroupMeta(PROJECT_ENTITY_TYPE)), MagicMock())
    UserProcessors(
        registry.group(GroupMeta(USER_ENTITY_TYPE)),
        MagicMock(),
    )
    FairShareProcessors(
        fair_share_groups.group(GroupMeta(DOMAIN_FAIR_SHARE_ENTITY_TYPE)),
        fair_share_groups.group(GroupMeta(PROJECT_FAIR_SHARE_ENTITY_TYPE)),
        fair_share_groups.group(GroupMeta(USER_FAIR_SHARE_ENTITY_TYPE)),
        MagicMock(),
    )
    ResourcePresetProcessors(registry.group(GroupMeta(RESOURCE_PRESET_ENTITY_TYPE)), MagicMock())
    ResourceGroupProcessors(registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), MagicMock())
    ArtifactProcessors(
        registry.group(GroupMeta(ARTIFACT_ENTITY_TYPE)),
        ArtifactRevisionProcessors(
            registry.group(GroupMeta(ARTIFACT_ENTITY_TYPE)),
            artifact_revisions,
            MagicMock(),
        ),
        MagicMock(),
    )
    ArtifactRegistryProcessors(
        registry.group(GroupMeta(ARTIFACT_REGISTRY_ENTITY_TYPE)), MagicMock()
    )
    ModelCardProcessors(registry.group(GroupMeta(MODEL_CARD_ENTITY_TYPE)), MagicMock())
    ContainerRegistryProcessors(
        registry.group(GroupMeta(CONTAINER_REGISTRY_ENTITY_TYPE)), MagicMock()
    )
    ImageProcessors(registry.group(GroupMeta(IMAGE_ENTITY_TYPE)), MagicMock())
    ExportProcessors(registry.group(GroupMeta(EXPORT_ENTITY_TYPE)), MagicMock())
    TemplateProcessors(registry.group(GroupMeta(SESSION_TEMPLATE_ENTITY_TYPE)), MagicMock())
    SchedulingHistoryProcessors(
        scheduling_history_groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
        scheduling_history_groups.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)),
        scheduling_history_groups.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)),
        MagicMock(),
    )
    SessionProcessors(
        registry.group(GroupMeta(SESSION_ENTITY_TYPE)),
        ResourceAllocationProcessors(
            resource_allocation_groups.group(GroupMeta(USER_ENTITY_TYPE)),
            resource_allocation_groups.group(GroupMeta(PROJECT_ENTITY_TYPE)),
            resource_allocation_groups.group(GroupMeta(DOMAIN_ENTITY_TYPE)),
            resource_allocation_groups.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)),
            resource_allocation_groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
            resource_allocation_groups.group(GroupMeta(RESOURCE_PRESET_ENTITY_TYPE)),
            MagicMock(),
        ),
        MagicMock(),
    )
    DeploymentProcessors(registry.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)), MagicMock())
    VFolderProcessors(registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), MagicMock())
    VFolderAdminProcessors(registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), MagicMock())
    VFolderFileProcessors(registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), MagicMock())
    VFolderInviteProcessors(registry.group(GroupMeta(VFOLDER_INVITATION_ENTITY_TYPE)), MagicMock())
    VFolderSharingProcessors(registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), MagicMock())
    ModelServingProcessors(registry.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)), MagicMock())
    ModelServingAutoScalingProcessors(
        registry.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)), MagicMock()
    )

    wired = sorted(cls.action_name() for cls in registry.wired_actions())
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
