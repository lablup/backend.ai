from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, override
from unittest.mock import AsyncMock, MagicMock

import sqlalchemy as sa
from sqlalchemy.engine.default import DefaultDialect

from ai.backend.manager.api.gql_legacy.base import batch_result_in_scalar_stream
from ai.backend.manager.models.base import ABCColumn, ABCColumnPayload, DecimalType


async def test_batch_result_in_scalar_stream() -> None:
    key_list = [1, 2, 3]

    mock_rows = [SimpleNamespace(id=1, data="data1"), SimpleNamespace(id=3, data="data3")]

    async def mock_stream_scalars(query: sa.Select[Any]) -> AsyncGenerator[Any, None]:
        for row in mock_rows:
            yield row

    mock_db_sess = MagicMock()
    mock_db_sess.stream_scalars = AsyncMock(side_effect=mock_stream_scalars)

    def mock_from_row(graph_ctx: Any, row: Any) -> dict[str, Any]:
        return {"id": row.id, "data": row.data}

    mock_obj_type = MagicMock()
    mock_obj_type.from_row.side_effect = mock_from_row

    key_getter = lambda row: row.id
    mock_graph_ctx = MagicMock()
    mock_query = MagicMock(spec=sa.Select)
    result = await batch_result_in_scalar_stream(
        mock_graph_ctx,
        mock_db_sess,
        query=mock_query,
        obj_type=mock_obj_type,
        key_list=key_list,
        key_getter=key_getter,
    )

    expected_result = [{"id": 1, "data": "data1"}, None, {"id": 3, "data": "data3"}]
    assert result == expected_result


class TestDecimalType:
    def test_process_bind_param_with_positive_value(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_bind_param(Decimal("123.45"), None)  # type: ignore[arg-type]
        assert result == "123.45"

    def test_process_bind_param_with_negative_value(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_bind_param(Decimal("-123.45"), None)  # type: ignore[arg-type]
        assert result == "-123.45"

    def test_process_bind_param_with_zero(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_bind_param(Decimal("0"), None)  # type: ignore[arg-type]
        assert result == "0"

    def test_process_bind_param_with_none(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_bind_param(None, None)  # type: ignore[arg-type]
        assert result is None

    def test_process_result_value_with_positive_value(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_result_value("123.45", None)  # type: ignore[arg-type]
        assert result == Decimal("123.45")

    def test_process_result_value_with_negative_value(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_result_value("-123.45", None)  # type: ignore[arg-type]
        assert result == Decimal("-123.45")

    def test_process_result_value_with_zero(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_result_value("0", None)  # type: ignore[arg-type]
        assert result == Decimal("0")

    def test_process_result_value_with_none(self) -> None:
        decimal_type = DecimalType()
        result = decimal_type.process_result_value(None, None)  # type: ignore[arg-type]
        assert result is None


class _Shape(ABCColumnPayload):
    """Test-only polymorphic payload base; `load` dispatches by the `kind` tag."""

    @classmethod
    @override
    def load(cls, raw: dict[str, Any]) -> _Shape:
        kind = raw["kind"]
        if kind == "circle":
            return _Circle(radius=raw["radius"])
        if kind == "square":
            return _Square(side=raw["side"])
        raise ValueError(f"unknown shape kind: {kind!r}")


@dataclass
class _Circle(_Shape):
    radius: float

    @override
    def serialize(self) -> dict[str, Any]:
        return {"kind": "circle", "radius": self.radius}


@dataclass
class _Square(_Shape):
    side: float

    @override
    def serialize(self) -> dict[str, Any]:
        return {"kind": "square", "side": self.side}


class TestABCColumn:
    def test_process_bind_param_serializes_to_dict(self) -> None:
        column = ABCColumn(_Shape)
        result = column.process_bind_param(_Circle(radius=2.0), DefaultDialect())
        assert result == {"kind": "circle", "radius": 2.0}

    def test_process_result_value_rehydrates_typed_object(self) -> None:
        column = ABCColumn(_Shape)
        result = column.process_result_value({"kind": "square", "side": 3.0}, DefaultDialect())
        assert result == _Square(side=3.0)

    def test_roundtrip_preserves_concrete_subtype(self) -> None:
        column = ABCColumn(_Shape)
        original = _Circle(radius=1.5)
        stored = column.process_bind_param(original, DefaultDialect())
        restored = column.process_result_value(stored, DefaultDialect())
        assert restored == original
        assert type(restored) is _Circle
