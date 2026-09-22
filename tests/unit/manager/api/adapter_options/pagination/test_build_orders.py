"""Tests for the ORDER BY clauses build_orders derives per pagination mode."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
)
from ai.backend.manager.repositories.base import QueryOrder


class _Base(DeclarativeBase):
    pass


class _ItemRow(_Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column("id", sa.Uuid, primary_key=True)
    created_at: Mapped[int] = mapped_column("created_at", sa.Integer)
    name: Mapped[str] = mapped_column("name", sa.String)


_CURSOR = encode_cursor("0190a5d0-0000-7000-8000-000000000007")


def _sql(orders: list[QueryOrder]) -> list[str]:
    return [str(order.compile()) for order in orders]


@pytest.fixture
def spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=_ItemRow.created_at.desc(),
        cursor_column=_ItemRow.id,
    )


@pytest.fixture
def caller_orders() -> list[QueryOrder]:
    return [_ItemRow.name.asc()]


class TestCursorPagination:
    @pytest.mark.parametrize(
        "options",
        [
            PaginationOptions(first=2),
            PaginationOptions(first=2, after=_CURSOR),
        ],
    )
    def test_forward_cursor_drops_caller_orders(
        self, options: PaginationOptions, spec: PaginationSpec, caller_orders: list[QueryOrder]
    ) -> None:
        assert _sql(build_orders(options, spec, caller_orders)) == ["items.id ASC"]

    @pytest.mark.parametrize(
        "options",
        [
            PaginationOptions(last=2),
            PaginationOptions(last=2, before=_CURSOR),
        ],
    )
    def test_backward_cursor_drops_caller_orders(
        self, options: PaginationOptions, spec: PaginationSpec, caller_orders: list[QueryOrder]
    ) -> None:
        assert _sql(build_orders(options, spec, caller_orders)) == ["items.id DESC"]


class TestOffsetPagination:
    def test_caller_orders_precede_the_tiebreaker(
        self, spec: PaginationSpec, caller_orders: list[QueryOrder]
    ) -> None:
        orders = build_orders(PaginationOptions(limit=10), spec, caller_orders)
        assert _sql(orders) == ["items.name ASC", "items.id ASC"]

    @pytest.mark.parametrize(
        "options",
        [
            PaginationOptions(limit=10),
            PaginationOptions(),
        ],
    )
    def test_forward_order_fills_in_when_no_caller_orders(
        self, options: PaginationOptions, spec: PaginationSpec
    ) -> None:
        assert _sql(build_orders(options, spec, [])) == ["items.created_at DESC", "items.id ASC"]
