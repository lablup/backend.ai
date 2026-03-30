"""Tests for ai.backend.common.dto.manager.v2.quota_scope.response module."""

from __future__ import annotations

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.quota_scope.response import (
    GetQuotaScopePayload,
    QuotaScopeNode,
    SearchQuotaScopesPayload,
    SetQuotaPayload,
    UnsetQuotaPayload,
)


def _make_node(quota_scope_id: str = "user:abc-123") -> QuotaScopeNode:
    return QuotaScopeNode(
        quota_scope_id=quota_scope_id,
        storage_host_name="nfs01",
        usage_bytes=1024,
        usage_count=10,
        hard_limit_bytes=1073741824,
    )


class TestQuotaScopeNode:
    """Tests for QuotaScopeNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = _make_node()
        assert node.quota_scope_id == "user:abc-123"
        assert node.storage_host_name == "nfs01"
        assert node.usage_bytes == 1024
        assert node.hard_limit_bytes == 1073741824

    def test_creation_with_none_fields(self) -> None:
        node = QuotaScopeNode(
            quota_scope_id="project:xyz",
            storage_host_name="cephfs",
        )
        assert node.usage_bytes is None
        assert node.usage_count is None
        assert node.hard_limit_bytes is None

    def test_round_trip(self) -> None:
        node = _make_node()
        restored = QuotaScopeNode.model_validate_json(node.model_dump_json())
        assert restored.quota_scope_id == "user:abc-123"
        assert restored.usage_bytes == 1024
        assert restored.hard_limit_bytes == 1073741824

    def test_round_trip_with_none_values(self) -> None:
        node = QuotaScopeNode(quota_scope_id="user:x", storage_host_name="nfs01")
        restored = QuotaScopeNode.model_validate_json(node.model_dump_json())
        assert restored.usage_bytes is None
        assert restored.hard_limit_bytes is None


class TestSearchQuotaScopesPayload:
    """Tests for SearchQuotaScopesPayload model."""

    def test_creation(self) -> None:
        nodes = [_make_node("user:a"), _make_node("user:b")]
        pagination = PaginationInfo(total=2, offset=0, limit=50)
        payload = SearchQuotaScopesPayload(quota_scopes=nodes, pagination=pagination)
        assert len(payload.quota_scopes) == 2
        assert payload.pagination.total == 2

    def test_empty_list(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=50)
        payload = SearchQuotaScopesPayload(quota_scopes=[], pagination=pagination)
        assert payload.quota_scopes == []

    def test_round_trip(self) -> None:
        nodes = [_make_node()]
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = SearchQuotaScopesPayload(quota_scopes=nodes, pagination=pagination)
        restored = SearchQuotaScopesPayload.model_validate_json(payload.model_dump_json())
        assert len(restored.quota_scopes) == 1
        assert restored.quota_scopes[0].quota_scope_id == "user:abc-123"
        assert restored.pagination.total == 1


class TestGetQuotaScopePayload:
    """Tests for GetQuotaScopePayload model."""

    def test_creation(self) -> None:
        node = _make_node()
        payload = GetQuotaScopePayload(quota_scope=node)
        assert payload.quota_scope.quota_scope_id == "user:abc-123"

    def test_round_trip(self) -> None:
        node = _make_node("project:xyz")
        payload = GetQuotaScopePayload(quota_scope=node)
        restored = GetQuotaScopePayload.model_validate_json(payload.model_dump_json())
        assert restored.quota_scope.quota_scope_id == "project:xyz"


class TestSetQuotaPayload:
    """Tests for SetQuotaPayload model."""

    def test_creation(self) -> None:
        node = _make_node()
        payload = SetQuotaPayload(quota_scope=node)
        assert payload.quota_scope.hard_limit_bytes == 1073741824

    def test_round_trip(self) -> None:
        node = _make_node()
        payload = SetQuotaPayload(quota_scope=node)
        restored = SetQuotaPayload.model_validate_json(payload.model_dump_json())
        assert restored.quota_scope.storage_host_name == "nfs01"


class TestUnsetQuotaPayload:
    """Tests for UnsetQuotaPayload model."""

    def test_creation(self) -> None:
        node = QuotaScopeNode(
            quota_scope_id="user:abc",
            storage_host_name="nfs01",
            hard_limit_bytes=None,
        )
        payload = UnsetQuotaPayload(quota_scope=node)
        assert payload.quota_scope.hard_limit_bytes is None

    def test_round_trip(self) -> None:
        node = QuotaScopeNode(quota_scope_id="user:def", storage_host_name="cephfs")
        payload = UnsetQuotaPayload(quota_scope=node)
        restored = UnsetQuotaPayload.model_validate_json(payload.model_dump_json())
        assert restored.quota_scope.quota_scope_id == "user:def"
