from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.role_permission_preset.ids import (
    role_permission_preset_id,
)
from ai.backend.manager.seed.role_preset.seed import RolePresetSeed

_TIMESTAMP: Final[str] = "2025-09-12 09:51:58.265582+00"
# The bits a grant is written out as, one row per bit.
_BITS: Final[tuple[Permission, ...]] = (
    Permission.READ,
    Permission.UPDATE,
    Permission.CREATE,
    Permission.SOFT_DELETE,
    Permission.HARD_DELETE,
)


class RoleFixture:
    """Writes the preset fixture from the role files. The roles instantiated from the
    presets are not written: `mgr permissions provision` creates them in each scope."""

    _seeds: Mapping[str, RolePresetSeed]

    def __init__(self, seeds: Sequence[RolePresetSeed]) -> None:
        self._seeds = {seed.name: seed for seed in seeds}

    def render_presets(self) -> dict[str, Any]:
        return {
            "__generated_by": "backend.ai mgr permissions emit",
            "role_presets": self._presets(),
            "role_permission_presets": self._permission_presets(),
        }

    def _presets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": str(seed.id),
                "name": seed.name,
                "role_name_template": None,
                "scope_type": str(seed.scope_type),
                "auto_assign": seed.auto_assign,
                "deleted_at": None,
                "created_at": _TIMESTAMP,
                "updated_at": _TIMESTAMP,
            }
            for seed in self._seeds.values()
        ]

    def _permission_presets(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for seed in self._seeds.values():
            preset_id = str(seed.id)
            granted = seed.granted()
            for entity_type in sorted(granted):
                for bit in _BITS:
                    if not granted[entity_type] & bit:
                        continue
                    rows.append({
                        "id": role_permission_preset_id(preset_id, entity_type, int(bit)),
                        "role_preset_id": preset_id,
                        "entity_type": entity_type,
                        "permission": int(bit),
                        "created_at": _TIMESTAMP,
                    })
        return rows
