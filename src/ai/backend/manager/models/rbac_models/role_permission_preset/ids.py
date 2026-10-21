from __future__ import annotations

import hashlib
import uuid
from typing import Final

__all__ = ("role_permission_preset_id",)

# The moment the seed was first generated.
_EPOCH_MS: Final[int] = 1757670718265


def role_permission_preset_id(role_preset_id: str, entity_type: str, permission: int) -> str:
    """The id of a preset's grant row: a uuid7 whose timestamp is fixed and whose remaining
    bits come from the grant, so the fixture and a migration write the same row."""
    parts = ("role_permission_preset", role_preset_id, entity_type, str(permission))
    digest = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=10).digest()
    value = (_EPOCH_MS & 0xFFFFFFFFFFFF) << 80 | int.from_bytes(digest, "big")
    value &= ~(0xF << 76)
    value |= 0x7 << 76
    value &= ~(0x3 << 62)
    value |= 0x2 << 62
    return str(uuid.UUID(int=value))
