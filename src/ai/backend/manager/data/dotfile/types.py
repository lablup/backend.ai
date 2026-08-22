from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from typing import Any

from ai.backend.common import msgpack
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)

MAXIMUM_DOTFILE_COUNT = 100


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
class DotfileEntries:
    """The dotfile entries packed into one row's column.

    Every edit is a read of the whole set followed by a write of the whole set, so
    the limits the set has to hold — one entry per path, a count, a packed size —
    are decided here rather than at each of the three tables that store one.
    """

    entries: tuple[DotfileEntry, ...] = ()

    @classmethod
    def unpack(cls, packed: bytes) -> DotfileEntries:
        rows = msgpack.unpackb(packed) or []
        return cls(
            entries=tuple(
                DotfileEntry(path=row["path"], perm=row["perm"], data=row["data"]) for row in rows
            )
        )

    def get(self, path: str) -> DotfileEntry:
        for entry in self.entries:
            if entry.path == path:
                return entry
        raise DotfileNotFound

    def added(self, entry: DotfileEntry) -> DotfileEntries:
        if any(e.path == entry.path for e in self.entries):
            raise DotfileAlreadyExists
        if len(self.entries) >= MAXIMUM_DOTFILE_COUNT:
            raise DotfileCreationFailed("Dotfile creation limit reached")
        return DotfileEntries(entries=(*self.entries, entry))

    def replaced(self, entry: DotfileEntry) -> DotfileEntries:
        kept = tuple(e for e in self.entries if e.path != entry.path)
        if len(kept) == len(self.entries):
            raise DotfileNotFound
        return DotfileEntries(entries=(*kept, entry))

    def removed(self, path: str) -> DotfileEntries:
        kept = tuple(e for e in self.entries if e.path != path)
        if len(kept) == len(self.entries):
            raise DotfileNotFound
        return DotfileEntries(entries=kept)

    def pack(self) -> bytes:
        packed = msgpack.packb([
            {"path": e.path, "perm": e.perm, "data": e.data} for e in self.entries
        ])
        if len(packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")
        return packed


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
