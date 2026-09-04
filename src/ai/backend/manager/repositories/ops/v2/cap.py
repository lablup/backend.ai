"""How a permission mask and a field scope spread over per-bit rows."""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission


class V2CapOps:
    """Shared by the writes that keep one row per permission bit."""

    def _bits_of(self, mask: Permission) -> list[Permission]:
        """The single bits a mask spans — one row each."""
        return [bit for bit in Permission if bit and mask & bit]

    def _scoped_paths(
        self, fields: Mapping[FieldPath, Permission]
    ) -> dict[Permission, frozenset[FieldPath]]:
        """The field scope regrouped per bit: which paths each bit is scoped to."""
        scoped: dict[Permission, set[FieldPath]] = {}
        for path, bits in fields.items():
            for bit in self._bits_of(bits):
                scoped.setdefault(bit, set()).add(path)
        return {bit: frozenset(paths) for bit, paths in scoped.items()}
