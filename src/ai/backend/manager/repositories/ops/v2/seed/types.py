from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.models.specs.upserter import EntityUpserter, FieldUpserter


@dataclass(frozen=True)
class SeedWrite:
    """The specs one seed item is written with: the entity, the field rows it states, the
    field rows an overwrite drops, and the users granted the entity when it is a role."""

    upserter: EntityUpserter[Any, Any]
    field_upserters: Sequence[FieldUpserter[Any, Any, Any]]
    field_purgers: Sequence[FieldBatchPurger[Any, Any, Any]]
    granted_users: Sequence[UserID] = ()


@dataclass(frozen=True)
class SeedRelationWrite:
    """A relation linking two existing entities, written with the creator the API uses."""

    creator: RelationCreator[Any, Any, Any]
    scope: EntityIdentifier
    target: EntityIdentifier


@dataclass(frozen=True)
class SeedRosterWrite:
    """A user put on a project's roster."""

    project_id: ProjectID
    user_id: UserID


type SeedItemWrite = SeedWrite | SeedRelationWrite | SeedRosterWrite


@dataclass(frozen=True)
class SeedWriteItemResult:
    """Whether a seed item wrote any row, or the error that refused it."""

    written: bool
    error: BackendAIError | None = None
