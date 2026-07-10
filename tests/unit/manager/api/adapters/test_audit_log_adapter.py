"""Unit tests for audit-log read-surface exposure of ``acted_as``."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.export.reports.audit_log import AUDIT_LOG_FIELDS

_SUPERADMIN = str(uuid.uuid4())
_TARGET = str(uuid.uuid4())


def _create_audit_log_data(*, triggered_by: str | None, acted_as: str | None) -> AuditLogData:
    """Create a minimal AuditLogData for testing adapter conversion."""
    return AuditLogData(
        id=uuid.uuid4(),
        action_id=uuid.uuid4(),
        entity_type="vfolder",
        operation="search",
        created_at=datetime(2026, 7, 10, tzinfo=UTC),
        description="test",
        status=OperationStatus.SUCCESS,
        entity_id="entity-1",
        request_id="req-1",
        triggered_by=triggered_by,
        acted_as=acted_as,
        duration=None,
    )


class TestDataToNode:
    """Tests for AuditLogAdapter._data_to_node conversion."""

    def test_acted_as_mapped_during_impersonation(self) -> None:
        """Diverging trigger and effective identities should both map onto the node."""
        data = _create_audit_log_data(triggered_by=_SUPERADMIN, acted_as=_TARGET)
        node = AuditLogAdapter._data_to_node(data)
        assert node.triggered_by == _SUPERADMIN
        assert node.acted_as == _TARGET

    def test_null_acted_as_preserved(self) -> None:
        """A system-triggered row (both identities None) should keep acted_as None."""
        data = _create_audit_log_data(triggered_by=None, acted_as=None)
        node = AuditLogAdapter._data_to_node(data)
        assert node.acted_as is None


class TestExportReportFields:
    """Tests for the audit-log export report field set."""

    def test_acted_as_included(self) -> None:
        """acted_as should be an exported audit-log field."""
        keys = {f.key for f in AUDIT_LOG_FIELDS}
        assert "acted_as" in keys
