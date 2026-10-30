"""Test-only tables the shared searchable-field declarations are exercised against.

Five tables shaped like a real entity and the rows it reaches: a searched outer row
(``shelf``), a to-one related row (``category``), a to-many child (``box``) with a
to-one (``spec``) and a to-many (``item``) of its own, and the rows of another entity
that uses a shelf (``cart`` / ``cart_line``).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import override

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.models.base import Base


class ShelfKind(enum.StrEnum):
    BOOK = "book"
    TOOL = "tool"
    TOY = "toy"


class BoxState(enum.StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class ShelfEntityType(EntityType):
    """The type the graph records a shelf under."""

    @override
    @classmethod
    def name(cls) -> str:
        return "test_search_shelf"


class ZoneEntityType(EntityType):
    """The type the graph records a zone under."""

    @override
    @classmethod
    def name(cls) -> str:
        return "test_search_zone"


class ZoneID(EntityIdentifier):
    """The scope a shelf belongs to."""

    @override
    def entity_type(self) -> EntityType:
        return ZoneEntityType()


class CartID(EntityIdentifier):
    """The entity whose use narrows a shelf search."""

    @override
    def entity_type(self) -> EntityType:
        return EntityType("test_search_cart")


class CategoryRow(Base):
    __tablename__ = "test_search_category"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    rank: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class ShelfRow(Base):
    __tablename__ = "test_search_shelf"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    count: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    kind: Mapped[ShelfKind] = mapped_column(
        sa.Enum(ShelfKind, name="test_search_shelf_kind"), nullable=False
    )
    active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    tags: Mapped[list[str]] = mapped_column(postgresql.ARRAY(sa.String), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    stocked_on: Mapped[date] = mapped_column(sa.Date, nullable=False)
    zone_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("test_search_category.id"), nullable=True
    )


class SpecRow(Base):
    """Reached from a box by a column carrying no foreign key constraint."""

    __tablename__ = "test_search_spec"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    shelf_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("test_search_shelf.id"), nullable=False
    )
    grade: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    weight: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class BoxRow(Base):
    __tablename__ = "test_search_box"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    shelf_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("test_search_shelf.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    size: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    state: Mapped[BoxState] = mapped_column(
        sa.Enum(BoxState, name="test_search_box_state"), nullable=False
    )
    spec_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, nullable=True)


class ShelfItemRow(Base):
    __tablename__ = "test_search_item"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    box_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("test_search_box.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    qty: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class CartRow(Base):
    __tablename__ = "test_search_cart"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    zone_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)


class CartLineRow(Base):
    """One cart's use of one shelf; a revoked line is not a use."""

    __tablename__ = "test_search_cart_line"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    cart_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("test_search_cart.id"), nullable=False
    )
    shelf_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("test_search_shelf.id"), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)


@dataclass(frozen=True)
class ShelfData:
    id: uuid.UUID
    name: str
    note: str | None
    count: int
    price: Decimal
    kind: ShelfKind
    active: bool
    tags: list[str]
    opened_at: datetime
    closed_at: datetime | None
    stocked_on: date
    zone_id: uuid.UUID
    category_id: uuid.UUID | None


@dataclass(frozen=True)
class BoxData:
    id: uuid.UUID
    shelf_id: uuid.UUID
    label: str
    size: int
    state: BoxState
    spec_id: uuid.UUID | None


@dataclass(frozen=True)
class SpecData:
    id: uuid.UUID
    shelf_id: uuid.UUID
    grade: str
    weight: int


@dataclass(frozen=True)
class ShelfItemData:
    id: uuid.UUID
    box_id: uuid.UUID
    code: str
    qty: int


@dataclass(frozen=True)
class CategoryData:
    id: uuid.UUID
    title: str
    rank: int
