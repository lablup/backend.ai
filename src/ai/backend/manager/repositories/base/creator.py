"""Creator for repository insert operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ai.backend.manager.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class CreatorSpec(ABC, Generic[TRow]):
    """Abstract base class defining a row to insert.

    Implementations specify what to create by providing:
    - A build_row() method that returns the ORM instance to insert
    """

    @abstractmethod
    def build_row(self) -> TRow:
        """Build ORM row instance to insert.

        Returns:
            An ORM model instance to be inserted
        """
        raise NotImplementedError


@dataclass
class Creator(Generic[TRow]):
    """Bundles creator spec for insert operations.

    Attributes:
        spec: CreatorSpec implementation defining what to create.

    Note:
        Additional fields (e.g., RBAC context) may be added later.
    """

    spec: CreatorSpec[TRow]


@dataclass
class CreatorResult(Generic[TRow]):
    """Result of executing a create operation."""

    row: TRow


async def execute_creator(
    db_sess: SASession,
    creator: Creator[TRow],
) -> CreatorResult[TRow]:
    """Execute INSERT with creator.

    Args:
        db_sess: Database session (must be writable)
        creator: Creator containing spec for the row to insert

    Returns:
        CreatorResult containing the created row with generated values (id, timestamps, etc.)

    Example:
        class UserCreatorSpec(CreatorSpec[UserRow]):
            def __init__(self, name: str, email: str):
                self._name = name
                self._email = email

            def build_row(self) -> UserRow:
                return UserRow(name=self._name, email=self._email)

        creator = Creator(spec=UserCreatorSpec("Alice", "alice@example.com"))
        result = await execute_creator(db_sess, creator)
        print(result.row.id)  # Generated ID
    """
    row = creator.spec.build_row()
    db_sess.add(row)
    await db_sess.flush()
    await db_sess.refresh(row)
    return CreatorResult(row=row)
