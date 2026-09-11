"""Tests for the audit log adapter's DTO-filter conversion."""

from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.audit_log.request import AuditLogFilter
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter


def _make_adapter() -> AuditLogAdapter:
    return AuditLogAdapter(MagicMock())


class TestAuditLogAdapterConvertFilter:
    def test_empty_filter_produces_no_conditions(self) -> None:
        conditions = _make_adapter()._convert_filter(AuditLogFilter())
        assert len(conditions) == 0

    def test_entity_id_filter_produces_one_condition(self) -> None:
        filter_dto = AuditLogFilter(entity_id=StringFilter(equals="e-1"))
        conditions = _make_adapter()._convert_filter(filter_dto)
        assert len(conditions) == 1

    def test_entity_id_and_entity_type_produce_two_conditions(self) -> None:
        filter_dto = AuditLogFilter(
            entity_id=StringFilter(equals="e-1"),
            entity_type=StringFilter(equals="user"),
        )
        conditions = _make_adapter()._convert_filter(filter_dto)
        assert len(conditions) == 2
