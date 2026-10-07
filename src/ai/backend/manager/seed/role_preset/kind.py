from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.purgers import (
    RolePermissionPresetUngrantedPurger,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.upserters import (
    RolePermissionPresetUpserter,
)
from ai.backend.manager.models.rbac_models.role_preset.creators import RolePresetSeedCreator
from ai.backend.manager.models.rbac_models.role_preset.upserters import RolePresetUpserter
from ai.backend.manager.seed.kind import (
    SeedCreation,
    SeedFileItems,
    SeedKind,
    SeedRejection,
    SeedUpsert,
)
from ai.backend.manager.seed.role_preset.check import RoleSeedChecker
from ai.backend.manager.seed.role_preset.kinds import PermissionKinds
from ai.backend.manager.seed.role_preset.loader import RoleSeedLoader
from ai.backend.manager.seed.role_preset.role import RoleSeed


class RolePresetSeedKind(SeedKind[RoleSeed]):
    """Role presets and their permission presets, keyed by the preset id.

    The roles a preset calls for are created in each scope by `mgr permissions provision`.
    """

    @override
    def name(self) -> str:
        return RoleSeedLoader.kind

    @override
    def versions(self) -> frozenset[int]:
        return RoleSeedLoader.versions

    @override
    def apply_after(self) -> frozenset[str]:
        return frozenset()

    @override
    def schema(self) -> type[RoleSeed]:
        return RoleSeed

    @override
    def key(self, item: RoleSeed) -> str:
        return str(item.id)

    @override
    def reject(self, files: Sequence[SeedFileItems[RoleSeed]]) -> list[SeedRejection]:
        sources_by_name: dict[str, set[str]] = defaultdict(set)
        for file in files:
            for seed in file.items:
                sources_by_name[seed.name].add(file.source)
        rejections: list[SeedRejection] = []
        seeds = [seed for file in files for seed in file.items]
        for finding in RoleSeedChecker(PermissionKinds(), seeds).findings():
            rejections.extend(
                SeedRejection(source, finding.render())
                for source in sorted(sources_by_name[finding.role])
            )
        return rejections

    @override
    def creation(self, item: RoleSeed) -> SeedCreation:
        return SeedCreation(
            creator=RolePresetSeedCreator(
                id=item.id,
                name=item.name,
                scope_type=item.scope_type,
                auto_assign=item.auto_assign,
            ),
            field_creators=[
                RolePermissionPresetCreator(entity_type=entity_type, permission=bit)
                for entity_type, bit in self._grants(item)
            ],
        )

    @override
    def upsert(self, item: RoleSeed) -> SeedUpsert:
        return SeedUpsert(
            upserter=RolePresetUpserter(
                id=item.id,
                name=item.name,
                scope_type=item.scope_type,
                auto_assign=item.auto_assign,
            ),
            field_upserters=[
                RolePermissionPresetUpserter(entity_type=entity_type, permission=bit)
                for entity_type, bit in self._grants(item)
            ],
            field_purgers=[
                RolePermissionPresetUngrantedPurger(
                    grants={
                        EntityType(entity_type): mask
                        for entity_type, mask in item.permissions.items()
                    }
                )
            ]
            if item.permissions
            else [],
        )

    def _grants(self, item: RoleSeed) -> list[tuple[EntityType, Permission]]:
        """One entry per granted bit, as a permission row holds it."""
        return [
            (EntityType(entity_type), bit)
            for entity_type, mask in sorted(item.granted().items())
            for bit in mask
        ]
