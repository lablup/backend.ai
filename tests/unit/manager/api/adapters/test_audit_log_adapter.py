"""Unit tests for audit-log read-surface exposure of ``acted_as``."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.export.reports.audit_log import AUDIT_LOG_FIELDS

_SUPERADMIN = str(uuid.uuid4())
_TARGET = str(uuid.uuid4())


def _make_data(*, triggered_by: str | None, acted_as: str | None) -> AuditLogData:
    return AuditLogData(
        id=uuid.uuid4(),
        action_id=uuid.uuid4(),
        entity_type="vfolder",
        operation="search",
        created_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
        description="test",
        status=OperationStatus.SUCCESS,
        entity_id="entity-1",
        request_id="req-1",
        triggered_by=triggered_by,
        acted_as=acted_as,
        duration=None,
    )


class TestAuditLogReadExposesActedAs:
    def test_data_to_node_maps_acted_as(self) -> None:
        # Impersonation: trigger and effective identities differ.
        data = _make_data(triggered_by=_SUPERADMIN, acted_as=_TARGET)
        node = AuditLogAdapter._data_to_node(data)
        assert node.triggered_by == _SUPERADMIN
        assert node.acted_as == _TARGET

    def test_data_to_node_preserves_null_acted_as(self) -> None:
        # System trigger: both are None.
        data = _make_data(triggered_by=None, acted_as=None)
        node = AuditLogAdapter._data_to_node(data)
        assert node.acted_as is None

    def test_export_report_includes_acted_as(self) -> None:
        keys = {f.key for f in AUDIT_LOG_FIELDS}
        assert "acted_as" in keys
