"""Type definitions for group configuration repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai.backend.manager.models.group import GroupDotfile


@dataclass
class ResolvedGroup:
    """Resolved group identity with domain info."""

    id: uuid.UUID
    domain_name: str


@dataclass
class GroupDotfilesResult:
    """Result of fetching group dotfiles."""

    dotfiles: list[GroupDotfile]
    leftover_space: int


@dataclass
class DotfileInput:
    """Input for creating or updating a dotfile."""

    path: str
    permission: str
    data: str
