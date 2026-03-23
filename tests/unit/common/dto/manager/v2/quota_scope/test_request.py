"""Tests for ai.backend.common.dto.manager.v2.quota_scope.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.quota_scope.request import (
    QuotaScopeFilter,
    QuotaScopeOrder,
    SearchQuotaScopesInput,
    SetQuotaInput,
    UnsetQuotaInput,
)
from ai.backend.common.dto.manager.v2.quota_scope.types import OrderDirection, QuotaScopeOrderField


class TestSearchQuotaScopesInput:
    """Tests for SearchQuotaScopesInput model."""

    def test_default_values(self) -> None:
        req = SearchQuotaScopesInput()
        assert req.limit == DEFAULT_PAGE_LIMIT
        assert req.offset == 0
        assert req.filter is None
        assert req.order is None

    def test_limit_default_equals_page_limit_constant(self) -> None:
        req = SearchQuotaScopesInput()
        assert req.limit == 50

    def test_limit_max_is_max_page_limit(self) -> None:
        req = SearchQuotaScopesInput(limit=MAX_PAGE_LIMIT)
        assert req.limit == MAX_PAGE_LIMIT

    def test_limit_exceeds_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchQuotaScopesInput(limit=MAX_PAGE_LIMIT + 1)

    def test_limit_below_1_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchQuotaScopesInput(limit=0)

    def test_offset_default_is_zero(self) -> None:
        req = SearchQuotaScopesInput()
        assert req.offset == 0

    def test_negative_offset_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchQuotaScopesInput(offset=-1)

    def test_with_filter(self) -> None:
        f = QuotaScopeFilter(quota_scope_id=StringFilter(equals="user:abc"))
        req = SearchQuotaScopesInput(filter=f)
        assert req.filter is not None
        assert req.filter.quota_scope_id is not None

    def test_with_order(self) -> None:
        order = QuotaScopeOrder(field=QuotaScopeOrderField.QUOTA_SCOPE_ID)
        req = SearchQuotaScopesInput(order=[order])
        assert req.order is not None
        assert len(req.order) == 1

    def test_round_trip(self) -> None:
        req = SearchQuotaScopesInput(limit=20, offset=10)
        restored = SearchQuotaScopesInput.model_validate_json(req.model_dump_json())
        assert restored.limit == 20
        assert restored.offset == 10


class TestQuotaScopeFilter:
    """Tests for QuotaScopeFilter model."""

    def test_empty_filter(self) -> None:
        f = QuotaScopeFilter()
        assert f.quota_scope_id is None
        assert f.storage_host_name is None

    def test_with_string_filter(self) -> None:
        sf = StringFilter(equals="user:abc-123")
        f = QuotaScopeFilter(quota_scope_id=sf)
        assert f.quota_scope_id is not None
        assert f.quota_scope_id.equals == "user:abc-123"

    def test_nested_string_filter_round_trip(self) -> None:
        sf = StringFilter(contains="nfs")
        f = QuotaScopeFilter(storage_host_name=sf)
        restored = QuotaScopeFilter.model_validate_json(f.model_dump_json())
        assert restored.storage_host_name is not None
        assert restored.storage_host_name.contains == "nfs"


class TestQuotaScopeOrder:
    """Tests for QuotaScopeOrder model."""

    def test_default_direction_is_asc(self) -> None:
        order = QuotaScopeOrder(field=QuotaScopeOrderField.QUOTA_SCOPE_ID)
        assert order.direction == OrderDirection.ASC

    def test_desc_direction(self) -> None:
        order = QuotaScopeOrder(
            field=QuotaScopeOrderField.STORAGE_HOST_NAME,
            direction=OrderDirection.DESC,
        )
        assert order.direction == OrderDirection.DESC

    def test_round_trip(self) -> None:
        order = QuotaScopeOrder(
            field=QuotaScopeOrderField.QUOTA_SCOPE_ID,
            direction=OrderDirection.DESC,
        )
        restored = QuotaScopeOrder.model_validate_json(order.model_dump_json())
        assert restored.field == QuotaScopeOrderField.QUOTA_SCOPE_ID
        assert restored.direction == OrderDirection.DESC


class TestSetQuotaInput:
    """Tests for SetQuotaInput model."""

    def test_valid_creation(self) -> None:
        req = SetQuotaInput(
            storage_host_name="nfs01",
            quota_scope_id="user:abc-123",
            hard_limit_bytes=1073741824,
        )
        assert req.storage_host_name == "nfs01"
        assert req.hard_limit_bytes == 1073741824

    def test_hard_limit_zero_is_valid(self) -> None:
        req = SetQuotaInput(
            storage_host_name="nfs01",
            quota_scope_id="user:abc",
            hard_limit_bytes=0,
        )
        assert req.hard_limit_bytes == 0

    def test_negative_hard_limit_raises(self) -> None:
        with pytest.raises(ValidationError):
            SetQuotaInput(
                storage_host_name="nfs01",
                quota_scope_id="user:abc",
                hard_limit_bytes=-1,
            )

    def test_round_trip(self) -> None:
        req = SetQuotaInput(
            storage_host_name="nfs01",
            quota_scope_id="project:xyz",
            hard_limit_bytes=5368709120,
        )
        restored = SetQuotaInput.model_validate_json(req.model_dump_json())
        assert restored.quota_scope_id == "project:xyz"
        assert restored.hard_limit_bytes == 5368709120


class TestUnsetQuotaInput:
    """Tests for UnsetQuotaInput model."""

    def test_valid_creation(self) -> None:
        req = UnsetQuotaInput(storage_host_name="nfs01", quota_scope_id="user:abc")
        assert req.storage_host_name == "nfs01"
        assert req.quota_scope_id == "user:abc"

    def test_round_trip(self) -> None:
        req = UnsetQuotaInput(storage_host_name="cephfs", quota_scope_id="project:xyz")
        restored = UnsetQuotaInput.model_validate_json(req.model_dump_json())
        assert restored.storage_host_name == "cephfs"
        assert restored.quota_scope_id == "project:xyz"
