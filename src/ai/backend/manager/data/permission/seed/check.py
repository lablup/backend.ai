from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import Final

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.seed.kinds import PermissionKinds
from ai.backend.manager.data.permission.seed.role import RoleSeed

# A member role is compared with the admin role whose name shares its prefix.
_MEMBER_SUFFIX: Final[str] = "_member"
_ADMIN_SUFFIX: Final[str] = "_admin"


@dataclasses.dataclass(frozen=True)
class SeedFinding:
    """One error in the declaration, named with the role that states it."""

    role: str
    message: str

    def render(self) -> str:
        return f"{self.role}: {self.message}"


class RoleSeedChecker:
    """Compares the declaration with the entity types this build defines."""

    _kinds: PermissionKinds
    _seeds: Sequence[RoleSeed]

    def __init__(self, kinds: PermissionKinds, seeds: Sequence[RoleSeed]) -> None:
        self._kinds = kinds
        self._seeds = seeds

    def findings(self) -> list[SeedFinding]:
        findings: list[SeedFinding] = []
        findings.extend(self._duplicate_names())
        for seed in self._seeds:
            findings.extend(self._states_every_kind(seed))
        findings.extend(self._member_within_admin())
        return findings

    def _duplicate_names(self) -> list[SeedFinding]:
        seen: dict[str, int] = {}
        for seed in self._seeds:
            seen[seed.name] = seen.get(seed.name, 0) + 1
        return [
            SeedFinding(name, f"{count} files state this role")
            for name, count in sorted(seen.items())
            if count > 1
        ]

    def _states_every_kind(self, seed: RoleSeed) -> list[SeedFinding]:
        declared = self._kinds.declared()
        stated = set(seed.permissions)
        findings: list[SeedFinding] = []
        for kind in sorted(declared - stated):
            findings.append(SeedFinding(seed.name, f"{kind} is not stated"))
        for kind in sorted(stated - declared):
            findings.append(SeedFinding(seed.name, f"{kind} is not an entity type"))
        return findings

    def _member_within_admin(self) -> list[SeedFinding]:
        by_name = {seed.name: seed for seed in self._seeds}
        findings: list[SeedFinding] = []
        for seed in self._seeds:
            if not seed.name.endswith(_MEMBER_SUFFIX):
                continue
            admin = by_name.get(seed.name[: -len(_MEMBER_SUFFIX)] + _ADMIN_SUFFIX)
            if admin is None or admin.covers(seed):
                continue
            beyond = sorted(
                kind
                for kind, mask in seed.granted().items()
                if not admin.permissions.get(kind, Permission.NONE).covers(mask)
            )
            findings.append(
                SeedFinding(
                    seed.name,
                    f"holds on {', '.join(beyond)} what {admin.name} does not",
                )
            )
        return findings
