from __future__ import annotations

import hashlib
import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.seed.role import RoleSeed

# A derived id is a uuid7 whose timestamp is fixed and whose remaining bits come from
# what it identifies, so the same declaration writes the same file. The timestamp is
# the moment the seed was first generated.
_EPOCH_MS: Final[int] = 1757670718265
_TIMESTAMP: Final[str] = "2025-09-12 09:51:58.265582+00"
# The bits a grant is written out as, one row per bit.
_BITS: Final[tuple[Permission, ...]] = (
    Permission.READ,
    Permission.UPDATE,
    Permission.CREATE,
    Permission.SOFT_DELETE,
    Permission.HARD_DELETE,
)


def _identify(*parts: str) -> str:
    """The uuid7 identifying these parts, the same on every run."""
    digest = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=10).digest()
    value = (_EPOCH_MS & 0xFFFFFFFFFFFF) << 80 | int.from_bytes(digest, "big")
    value &= ~(0xF << 76)
    value |= 0x7 << 76
    value &= ~(0x3 << 62)
    value |= 0x2 << 62
    return str(uuid.UUID(int=value))


class RoleFixture:
    """Writes the preset fixture from the role files. The roles instantiated from the
    presets are not written: `mgr permissions provision` creates them in each scope."""

    _seeds: Mapping[str, RoleSeed]

    def __init__(self, seeds: Sequence[RoleSeed]) -> None:
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
                "deleted": False,
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
                        "id": _identify(
                            "role_permission_preset", preset_id, entity_type, str(int(bit))
                        ),
                        "role_preset_id": preset_id,
                        "entity_type": entity_type,
                        "permission": int(bit),
                        "created_at": _TIMESTAMP,
                    })
        return rows
