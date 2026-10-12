"""Factory for the seed kinds this build applies."""

from __future__ import annotations

from ai.backend.manager.seed.app_config_definition.seed import AppConfigDefinitionSeed
from ai.backend.manager.seed.client_ip_masking_policy.seed import ClientIPMaskingPolicySeed
from ai.backend.manager.seed.login_client_type.seed import LoginClientTypeSeed
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.resource_slot_type.seed import ResourceSlotTypeSeed
from ai.backend.manager.seed.retention_policy.seed import RetentionPolicySeed
from ai.backend.manager.seed.role_preset.seed import RolePresetSeed
from ai.backend.manager.seed.types import SeedKind


def create_seed_kind_registry() -> SeedKindRegistry:
    """Every kind, in the order it is applied."""
    return SeedKindRegistry({
        SeedKind.RESOURCE_SLOT_TYPE: (1, ResourceSlotTypeSeed),
        SeedKind.LOGIN_CLIENT_TYPE: (1, LoginClientTypeSeed),
        SeedKind.RETENTION_POLICY: (1, RetentionPolicySeed),
        SeedKind.APP_CONFIG_DEFINITION: (1, AppConfigDefinitionSeed),
        SeedKind.CLIENT_IP_MASKING_POLICY: (1, ClientIPMaskingPolicySeed),
        SeedKind.ROLE_PRESET: (1, RolePresetSeed),
    })
