from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.specs.purger import FieldBatchPurger
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
class SeedWriteItemResult:
    """Whether a seed item wrote any row, or the constraint that refused it."""

    written: bool
    error: RepositoryIntegrityError | None = None
