"""Tests for the cursor conditions and orders PaginationSpec derives."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder


class _Base(DeclarativeBase):
    pass


class _ItemRow(_Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column("id", sa.Uuid, primary_key=True)
    created_at: Mapped[int] = mapped_column("created_at", sa.Integer)


_CURSOR = "0190a5d0-0000-7000-8000-000000000007"
_CURSOR_LITERAL = "'0190a5d0000070008000000000000007'"
_CREATED_AT_OF_CURSOR_ROW = (
    f"(SELECT items.created_at FROM items WHERE items.id = {_CURSOR_LITERAL})"
)


def _sql(condition: QueryCondition) -> str:
    compiled = condition().compile(compile_kwargs={"literal_binds": True})
    return " ".join(str(compiled).split())


def _order_sql(order: QueryOrder) -> str:
    return str(order.compile())


class TestCursorCondition:
    @pytest.fixture
    def newest_first_spec(self) -> PaginationSpec:
        return PaginationSpec(
            forward_order=_ItemRow.created_at.desc(),
            cursor_column=_ItemRow.id,
        )

    @pytest.fixture
    def oldest_first_spec(self) -> PaginationSpec:
        return PaginationSpec(
            forward_order=_ItemRow.created_at.asc(),
            cursor_column=_ItemRow.id,
        )

    def test_forward_condition_with_descending_order(
        self, newest_first_spec: PaginationSpec
    ) -> None:
        assert _sql(newest_first_spec.forward_condition(_CURSOR)) == (
            f"items.created_at < {_CREATED_AT_OF_CURSOR_ROW}"
            f" OR items.created_at = {_CREATED_AT_OF_CURSOR_ROW} AND items.id > {_CURSOR_LITERAL}"
        )

    def test_backward_condition_with_descending_order(
        self, newest_first_spec: PaginationSpec
    ) -> None:
        assert _sql(newest_first_spec.backward_condition(_CURSOR)) == (
            f"items.created_at > {_CREATED_AT_OF_CURSOR_ROW}"
            f" OR items.created_at = {_CREATED_AT_OF_CURSOR_ROW} AND items.id < {_CURSOR_LITERAL}"
        )

    def test_forward_condition_with_ascending_order(
        self, oldest_first_spec: PaginationSpec
    ) -> None:
        assert _sql(oldest_first_spec.forward_condition(_CURSOR)) == (
            f"items.created_at > {_CREATED_AT_OF_CURSOR_ROW}"
            f" OR items.created_at = {_CREATED_AT_OF_CURSOR_ROW} AND items.id > {_CURSOR_LITERAL}"
        )

    def test_backward_condition_with_ascending_order(
        self, oldest_first_spec: PaginationSpec
    ) -> None:
        assert _sql(oldest_first_spec.backward_condition(_CURSOR)) == (
            f"items.created_at < {_CREATED_AT_OF_CURSOR_ROW}"
            f" OR items.created_at = {_CREATED_AT_OF_CURSOR_ROW} AND items.id < {_CURSOR_LITERAL}"
        )

    def test_order_on_cursor_column_compares_the_cursor_value(self) -> None:
        spec = PaginationSpec(
            forward_order=_ItemRow.id.desc(),
            cursor_column=_ItemRow.id,
        )
        assert _sql(spec.forward_condition(_CURSOR)) == f"items.id < {_CURSOR_LITERAL}"
        assert _sql(spec.backward_condition(_CURSOR)) == f"items.id > {_CURSOR_LITERAL}"

    def test_malformed_cursor_raises_value_error(self) -> None:
        spec = PaginationSpec(
            forward_order=_ItemRow.created_at.desc(),
            cursor_column=_ItemRow.id,
        )
        with pytest.raises(ValueError):
            spec.forward_condition("not-a-uuid")
        with pytest.raises(ValueError):
            spec.backward_condition("not-a-uuid")


class TestBackwardOrders:
    def test_backward_reverses_order_and_tiebreaker(self) -> None:
        spec = PaginationSpec(
            forward_order=_ItemRow.created_at.desc(),
            cursor_column=_ItemRow.id,
        )
        assert _order_sql(spec.backward_order) == "items.created_at ASC"
        assert _order_sql(spec.backward_tiebreaker_order) == "items.id DESC"

    def test_order_without_direction_is_rejected(self) -> None:
        spec = PaginationSpec(
            forward_order=_ItemRow.created_at.expression,
            cursor_column=_ItemRow.id,
        )
        with pytest.raises(ServerMisconfiguredError):
            _ = spec.backward_order
