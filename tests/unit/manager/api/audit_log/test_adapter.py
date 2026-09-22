"""Tests for the audit log adapter's DTO-filter conversion and DataLoader path."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogFieldType, AuditLogID
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.audit_log.request import AuditLogFilter
from ai.backend.manager.actions.types import ActionKind, ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericForbidden


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


def _record() -> AuditLogData:
    return AuditLogData(
        id=AuditLogID(uuid.uuid4()),
        action_id=uuid.uuid4(),
        action_kind=ActionKind.SINGLE_ENTITY,
        action_name="get_session",
        entity_type="session",
        operation="get",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        description="",
        status=OperationStatus.SUCCESS,
        target_entity_id=str(uuid.uuid4()),
        lookup_kind=None,
        lookup_key=None,
        request_id=None,
        triggered_by=None,
        acted_as=None,
        duration=None,
        client_ip=None,
    )


class TestAuditLogAdapterBatchLoad:
    @pytest.fixture
    def readable(self) -> AuditLogData:
        return _record()

    @pytest.fixture
    def denied_id(self) -> AuditLogID:
        return AuditLogID(uuid.uuid4())

    @pytest.fixture
    def missing_id(self) -> AuditLogID:
        return AuditLogID(uuid.uuid4())

    @pytest.fixture
    def denial(self) -> GenericForbidden:
        return GenericForbidden("no read on the entity this record is about")

    @pytest.fixture
    def processors(
        self,
        readable: AuditLogData,
        denied_id: AuditLogID,
        missing_id: AuditLogID,
        denial: GenericForbidden,
    ) -> MagicMock:
        processors = MagicMock()
        processors.bulk_get.run = AsyncMock(
            return_value=BulkFieldOpsResult(
                successes={readable.id: readable},
                errors={
                    denied_id: denial,
                    missing_id: FieldNotFoundError(
                        field_type=AuditLogFieldType(), operation=ActionOperationType.GET
                    ),
                },
            )
        )
        return processors

    @pytest.fixture
    def adapter(self, processors: MagicMock) -> AuditLogAdapter:
        return AuditLogAdapter(processors)

    async def test_answers_per_id(
        self,
        adapter: AuditLogAdapter,
        readable: AuditLogData,
        denied_id: AuditLogID,
        missing_id: AuditLogID,
        denial: GenericForbidden,
    ) -> None:
        nodes = await adapter.batch_load_by_ids([readable.id, denied_id, missing_id])

        node, refused, missing = nodes
        assert node is not None and not isinstance(node, Exception)
        assert node.id == readable.id
        assert refused is denial
        assert missing is None

    async def test_no_record_found_is_every_id_missing(
        self, adapter: AuditLogAdapter, processors: MagicMock, missing_id: AuditLogID
    ) -> None:
        processors.bulk_get.run.side_effect = FieldNotFoundError(
            field_type=AuditLogFieldType(), operation=ActionOperationType.GET
        )

        assert await adapter.batch_load_by_ids([missing_id]) == [None]

    async def test_no_ids_read_nothing(
        self, adapter: AuditLogAdapter, processors: MagicMock
    ) -> None:
        assert await adapter.batch_load_by_ids([]) == []
        processors.bulk_get.run.assert_not_awaited()
