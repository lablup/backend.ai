"""Purger inputs for RBAC ops entity deletion, addressed with the open entity types.

Successors of the ``RBACElementType``/``RBACElementRef``-keyed purgers in
:mod:`ai.backend.manager.repositories.base.rbac.entity_purger`. Input types only —
the execution lives in the RBAC ops layer (``RBACWriteOps``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityRef, EntityType
from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.purger import (
    BatchPurgerSpec,
    Purger,
    PurgerResult,
    PurgerSpec,
)


class EntityPurgerSpec[TRow: Base](PurgerSpec[TRow], ABC):
    """PurgerSpec that additionally names the entity for RBAC cleanup."""

    @abstractmethod
    def entity_ref(self) -> EntityRef:
        """Return the reference of the entity to delete."""
        raise NotImplementedError


@dataclass
class EntityPurger[TRow: Base](Purger[TRow]):
    """Single-row entity purger by primary key, with RBAC cleanup."""

    spec: EntityPurgerSpec[TRow]


@dataclass
class EntityPurgerResult[TRow: Base](PurgerResult[TRow]):
    """Result of executing a single-row entity purge."""

    pass


class EntityBatchPurgerSpec[TRow: Base](BatchPurgerSpec[TRow], ABC):
    """BatchPurgerSpec that additionally names the entity type for RBAC cleanup."""

    @abstractmethod
    def entity_type(self) -> EntityType:
        """Return the entity type used to address deleted rows' RBAC entries."""
        raise NotImplementedError


@dataclass
class EntityBatchPurger[TRow: Base]:
    """Batch purger for entities with RBAC cleanup.

    Attributes:
        spec: EntityBatchPurgerSpec implementation defining what to delete.
        batch_size: Batch size for chunked deletion.
    """

    spec: EntityBatchPurgerSpec[TRow]
    batch_size: int = 1000


@dataclass
class EntityBatchPurgerResult:
    """Result of an entity batch purge operation."""

    deleted_count: int
    deleted_permission_count: int
    deleted_scope_association_count: int
