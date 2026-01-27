"""Type definitions for project configuration repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai.backend.manager.models.group import GroupDotfile

# NOTE: GroupDotfile is a DB model type that retains the "group" naming from the database schema.


@dataclass
class ResolvedProject:
    """Resolved project identity with domain info."""

    id: uuid.UUID
    domain_name: str


@dataclass
class ProjectDotfilesResult:
    """Result of fetching project dotfiles."""

    dotfiles: list[GroupDotfile]
    leftover_space: int


@dataclass
class DotfileInput:
    """Input for creating or updating a dotfile."""

    path: str
    permission: str
    data: str
