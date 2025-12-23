from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.models.base import DecimalType, batch_result_in_scalar_stream


@pytest.mark.asyncio
async def test_batch_result_in_scalar_stream():
    key_list = [1, 2, 3]

    mock_rows = [SimpleNamespace(id=1, data="data1"), SimpleNamespace(id=3, data="data3")]

    async def mock_stream_scalars(query):
        for row in mock_rows:
            yield row

    mock_db_sess = MagicMock()
    mock_db_sess.stream_scalars = AsyncMock(side_effect=mock_stream_scalars)

    def mock_from_row(graph_ctx, row):
        return {"id": row.id, "data": row.data}

    mock_obj_type = MagicMock()
    mock_obj_type.from_row.side_effect = mock_from_row

    key_getter = lambda row: row.id
    graph_ctx = None
    result = await batch_result_in_scalar_stream(
        graph_ctx,
        mock_db_sess,
        query=None,  # We use mocking instead of using query here
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
