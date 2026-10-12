"""Factory for the seed kinds this build applies."""

from __future__ import annotations

from ai.backend.manager.seed.app_config_allow_list.seed import AppConfigAllowListSeed
from ai.backend.manager.seed.app_config_definition.seed import AppConfigDefinitionSeed
from ai.backend.manager.seed.client_ip_masking_policy.seed import ClientIPMaskingPolicySeed
from ai.backend.manager.seed.container_registry.seed import ContainerRegistrySeed
from ai.backend.manager.seed.idle_checker.seed import IdleCheckerSeed
from ai.backend.manager.seed.login_client_type.seed import LoginClientTypeSeed
from ai.backend.manager.seed.notification_channel.seed import NotificationChannelSeed
from ai.backend.manager.seed.object_storage.seed import ObjectStorageSeed
from ai.backend.manager.seed.prometheus_query_preset_category.seed import (
    PrometheusQueryPresetCategorySeed,
)
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.resource_slot_type.seed import ResourceSlotTypeSeed
from ai.backend.manager.seed.retention_policy.seed import RetentionPolicySeed
from ai.backend.manager.seed.role_preset.seed import RolePresetSeed
from ai.backend.manager.seed.storage_backend_type.seed import StorageBackendTypeSeed
from ai.backend.manager.seed.types import SeedKind
from ai.backend.manager.seed.vfs_storage.seed import VFSStorageSeed


def create_seed_kind_registry() -> SeedKindRegistry:
    """Every kind, in the order it is applied."""
    return SeedKindRegistry({
        SeedKind.RESOURCE_SLOT_TYPE: (1, ResourceSlotTypeSeed),
        SeedKind.LOGIN_CLIENT_TYPE: (1, LoginClientTypeSeed),
        SeedKind.RETENTION_POLICY: (1, RetentionPolicySeed),
        SeedKind.STORAGE_BACKEND_TYPE: (1, StorageBackendTypeSeed),
        SeedKind.PROMETHEUS_QUERY_PRESET_CATEGORY: (1, PrometheusQueryPresetCategorySeed),
        SeedKind.APP_CONFIG_DEFINITION: (1, AppConfigDefinitionSeed),
        SeedKind.APP_CONFIG_ALLOW_LIST: (1, AppConfigAllowListSeed),
        SeedKind.CLIENT_IP_MASKING_POLICY: (1, ClientIPMaskingPolicySeed),
        SeedKind.NOTIFICATION_CHANNEL: (1, NotificationChannelSeed),
        SeedKind.ROLE_PRESET: (1, RolePresetSeed),
        SeedKind.IDLE_CHECKER: (1, IdleCheckerSeed),
        SeedKind.CONTAINER_REGISTRY: (1, ContainerRegistrySeed),
        SeedKind.OBJECT_STORAGE: (1, ObjectStorageSeed),
        SeedKind.VFS_STORAGE: (1, VFSStorageSeed),
    })
