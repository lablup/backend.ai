"""Tests for ai.backend.common.dto.manager.v2.compute_session.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.compute_session.request import (
    ComputeSessionPathParam,
    SearchComputeSessionsInput,
)
from ai.backend.common.dto.manager.v2.compute_session.types import (
    ComputeSessionFilter,
    ComputeSessionOrder,
    ComputeSessionOrderField,
    OrderDirection,
)


class TestComputeSessionPathParam:
    """Tests for ComputeSessionPathParam model."""

    def test_valid_creation(self) -> None:
        param = ComputeSessionPathParam(session_id="session-abc-123")
        assert param.session_id == "session-abc-123"

    def test_missing_session_id_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            ComputeSessionPathParam.model_validate({})

    def test_round_trip(self) -> None:
        param = ComputeSessionPathParam(session_id="my-session")
        json_str = param.model_dump_json()
        restored = ComputeSessionPathParam.model_validate_json(json_str)
        assert restored.session_id == "my-session"


class TestSearchComputeSessionsInput:
    """Tests for SearchComputeSessionsInput model."""

    def test_defaults(self) -> None:
        inp = SearchComputeSessionsInput()
        assert inp.filter is None
        assert inp.order is None
        assert inp.limit > 0
        assert inp.offset == 0

    def test_with_filter(self) -> None:
        f = ComputeSessionFilter(status=["RUNNING"])
        inp = SearchComputeSessionsInput(filter=f)
        assert inp.filter is not None
        assert inp.filter.status == ["RUNNING"]

    def test_with_order_list(self) -> None:
        orders = [
            ComputeSessionOrder(
                field=ComputeSessionOrderField.CREATED_AT,
                direction=OrderDirection.DESC,
            )
        ]
        inp = SearchComputeSessionsInput(order=orders, limit=20, offset=0)
        assert inp.order is not None
        assert len(inp.order) == 1
        assert inp.order[0].field == ComputeSessionOrderField.CREATED_AT
        assert inp.order[0].direction == OrderDirection.DESC

    def test_with_filter_and_order(self) -> None:
        f = ComputeSessionFilter(status=["RUNNING", "PENDING"])
        orders = [
            ComputeSessionOrder(
                field=ComputeSessionOrderField.ID,
                direction=OrderDirection.ASC,
            )
        ]
        inp = SearchComputeSessionsInput(filter=f, order=orders, limit=50, offset=10)
        assert inp.filter is not None
        assert inp.filter.status == ["RUNNING", "PENDING"]
        assert inp.order is not None
        assert inp.limit == 50
        assert inp.offset == 10

    def test_invalid_limit_zero_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchComputeSessionsInput(limit=0)

    def test_invalid_offset_negative_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchComputeSessionsInput(offset=-1)

    def test_round_trip(self) -> None:
        f = ComputeSessionFilter(status=["RUNNING"])
        inp = SearchComputeSessionsInput(filter=f, limit=10, offset=0)
        json_str = inp.model_dump_json()
        restored = SearchComputeSessionsInput.model_validate_json(json_str)
        assert restored.filter is not None
        assert restored.filter.status == ["RUNNING"]
        assert restored.limit == 10
