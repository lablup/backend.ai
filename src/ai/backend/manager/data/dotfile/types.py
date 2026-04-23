from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from typing import Any


class DotfileScope(enum.StrEnum):
    DOMAIN = "domain"
    GROUP = "group"
    USER = "user"


DotfileEntityKey = str | uuid.UUID


@dataclass(frozen=True)
class DotfileEntry:
    path: str
    perm: str
    data: str


@dataclass(frozen=True)
class DotfileQueryResult:
    entries: list[DotfileEntry]
    leftover_space: int


@dataclass(frozen=True)
class SSHKeypair:
    """SSH keypair pulled from ``keypairs`` for a user session."""

    public_key: str
    private_key: str


@dataclass(frozen=True)
class DotfileBundle:
    """Typed snapshot consumed by the scheduling-controller context.

    Replaces the legacy ``Mapping[str, Any]`` shape that flowed through
    ``SessionSpecPreparationContext.dotfile_data`` /
    ``SessionSpecValidationContext.dotfile_data``. The agent-facing
    wire format is still a plain JSONB dict — use
    :meth:`to_internal_data` at the boundary.
    """

    dotfiles: tuple[DotfileEntry, ...] = ()
    ssh_keypair: SSHKeypair | None = None

    def to_internal_data(self) -> dict[str, Any]:
        """Render the bundle back into the agent-facing JSONB shape."""
        result: dict[str, Any] = {}
        if self.dotfiles:
            result["dotfiles"] = [
                {"path": e.path, "perm": e.perm, "data": e.data} for e in self.dotfiles
            ]
        if self.ssh_keypair is not None:
            result["ssh_keypair"] = {
                "public_key": self.ssh_keypair.public_key,
                "private_key": self.ssh_keypair.private_key,
            }
        return result
