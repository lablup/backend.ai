"""Type definitions for project configuration repository.

As there is an ongoing migration of renaming group to project,
there are some occurrences where "group" is being used as "project"
(e.g., GroupDotfile).
It will be fixed in the future; for now understand them as the same concept.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai.backend.manager.models.group import GroupDotfile


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
