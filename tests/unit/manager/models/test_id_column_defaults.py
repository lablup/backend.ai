from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import DefaultClause, Table
from sqlalchemy.sql.elements import TextClause

from ai.backend.manager.models.alembic.versions.c4a7e2f10b93_uuid7_for_history_usage_and_log_ids import (
    _TARGET_TABLES,
)
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.event_log.row import EventLogRow
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.vfolder.row import VFolderInvitationRow

_V7_ROWS = (
    SessionSchedulingHistoryRow,
    KernelSchedulingHistoryRow,
    DeploymentHistoryRow,
    RouteHistoryRow,
    ReplicaGroupHistoryRow,
    KernelUsageRecordRow,
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
    EventLogRow,
    AuditLogRow,
    AuditLogScopeRow,
    ErrorLogRow,
    LoginHistoryRow,
)

# Ids handed to an untrusted holder stay on v4 so the issue time does not leak.
_V4_ROWS = (
    LoginSessionRow,
    EndpointTokenRow,
    EntityInvitationRow,
    VFolderInvitationRow,
)


def _default_expr(row: Any) -> str:
    table: Table = row.__table__
    server_default = table.c.id.server_default
    assert isinstance(server_default, DefaultClause)
    expr = server_default.arg
    assert isinstance(expr, TextClause)
    return expr.text


class TestIdColumnDefaults:
    @pytest.mark.parametrize("row", _V7_ROWS, ids=lambda row: row.__tablename__)
    def test_history_usage_and_log_ids_default_to_v7(self, row: Any) -> None:
        assert _default_expr(row) == "uuid_generate_v7()"

    @pytest.mark.parametrize("row", _V4_ROWS, ids=lambda row: row.__tablename__)
    def test_untrusted_holder_ids_stay_on_v4(self, row: Any) -> None:
        assert _default_expr(row) == "uuid_generate_v4()"

    def test_migration_alters_exactly_the_declared_tables(self) -> None:
        assert set(_TARGET_TABLES) == {row.__tablename__ for row in _V7_ROWS}
