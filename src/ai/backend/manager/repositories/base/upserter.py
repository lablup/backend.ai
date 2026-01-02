"""Upserter for repository upsert (INSERT ON CONFLICT UPDATE) operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.manager.errors.repository import UpsertEmptyResultError
from ai.backend.manager.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class UpserterSpec(ABC, Generic[TRow]):
    """Abstract base class for upsert operations.

    Implementations specify what to upsert by providing:
    - row_class property for target table and result reconstruction
    - build_insert_values() for INSERT part
    - build_update_values() for ON CONFLICT UPDATE part
    """

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and result reconstruction."""
        raise NotImplementedError

    @abstractmethod
    def build_insert_values(self) -> dict[str, Any]:
        """Build column name to value mapping for INSERT.

        Returns:
            Dict with all column values for new row insertion
        """
        raise NotImplementedError

    @abstractmethod
    def build_update_values(self) -> dict[str, Any]:
        """Build column name to value mapping for ON CONFLICT UPDATE.

        Returns:
            Dict with column values to update on conflict
            (may be subset of insert values)
        """
        raise NotImplementedError


@dataclass
class Upserter(Generic[TRow]):
    """Bundles upserter spec for upsert operations.

    Attributes:
        spec: UpserterSpec implementation defining row_class and values to insert/update.
    """

    spec: UpserterSpec[TRow]


@dataclass
class UpserterResult(Generic[TRow]):
    """Result of executing an upsert operation."""

    row: TRow


async def execute_upserter(
    db_sess: SASession,
    upserter: Upserter[TRow],
    *,
    index_elements: list[str],
) -> UpserterResult[TRow]:
    """Execute INSERT ON CONFLICT UPDATE with upserter.

    Args:
        db_sess: Database session (must be writable)
        upserter: Upserter containing spec for the row to insert/update
        index_elements: Column names to use for conflict detection

    Returns:
        UpserterResult containing the created or updated row

    Example:
        class ConfigUpserterSpec(UpserterSpec[ConfigRow]):
            def __init__(self, key: str, value: str):
                self._key = key
                self._value = value

            @property
            def row_class(self) -> type[ConfigRow]:
                return ConfigRow

            def build_insert_values(self) -> dict[str, Any]:
                return {"key": self._key, "value": self._value, "created_at": now()}

            def build_update_values(self) -> dict[str, Any]:
                return {"value": self._value}  # Only update value, keep created_at

        upserter = Upserter(spec=ConfigUpserterSpec("setting", "enabled"))
        result = await execute_upserter(db_sess, upserter, index_elements=["key"])
    """
    spec = upserter.spec
    row_class = spec.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    insert_values = spec.build_insert_values()
    update_values = spec.build_update_values()

    stmt = pg_insert(table).values(insert_values)
    stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_=update_values,
    ).returning(*table.columns)

    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        raise UpsertEmptyResultError

    created_row: TRow = row_class(**dict(row_data._mapping))
    return UpserterResult(row=created_row)
