"""Factory for the seed kinds this build applies."""

from __future__ import annotations

from ai.backend.manager.seed.app_config_definition.seed import AppConfigDefinitionSeed
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.role_preset.seed import RolePresetSeed
from ai.backend.manager.seed.types import SeedKind


def create_seed_kind_registry() -> SeedKindRegistry:
    """Every kind, in the order it is applied."""
    return SeedKindRegistry({
        SeedKind.APP_CONFIG_DEFINITION: (1, AppConfigDefinitionSeed),
        SeedKind.ROLE_PRESET: (1, RolePresetSeed),
    })
