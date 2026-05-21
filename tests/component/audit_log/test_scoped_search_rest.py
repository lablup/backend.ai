"""Component tests for the scoped audit-log REST v2 endpoint."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import InvalidRequestError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.audit_log.request import (
    AdminSearchAuditLogsInput,
    AuditLogFilter,
    AuditLogScope,
    AuditLogStatusFilter,
    ScopedSearchAuditLogsInput,
)
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.common.dto.manager.v2.rbac.types import EntityTypeScope, UUIDScope
from ai.backend.manager.actions.types import OperationStatus

if TYPE_CHECKING:
    from tests.component.audit_log.conftest import AuditLogFactory


_ENTITY_ID = "ba-6098-vf"
_ACTOR = uuid.uuid4()


@pytest.fixture()
async def seeded_rows(audit_log_factory: AuditLogFactory) -> dict[str, uuid.UUID]:
    """Two SUCCESS rows + one ERROR row on the same target/actor."""
    return {
        "success_a": await audit_log_factory(
            entity_type=RBACElementType.VFOLDER.value,
            entity_id=_ENTITY_ID,
            triggered_by=str(_ACTOR),
            operation="update",
            status=OperationStatus.SUCCESS,
        ),
        "success_b": await audit_log_factory(
            entity_type=RBACElementType.VFOLDER.value,
            entity_id=_ENTITY_ID,
            triggered_by=str(_ACTOR),
            operation="delete",
            status=OperationStatus.SUCCESS,
        ),
        "error_a": await audit_log_factory(
            entity_type=RBACElementType.VFOLDER.value,
            entity_id=_ENTITY_ID,
            triggered_by=str(_ACTOR),
            operation="update",
            status=OperationStatus.ERROR,
        ),
    }


def _entity_scope() -> AuditLogScope:
    return AuditLogScope(
        entity=[
            EntityTypeScope(entity_type=RBACElementType.VFOLDER, entity_id=_ENTITY_ID),
        ]
    )


def _actor_scope() -> AuditLogScope:
    return AuditLogScope(triggered_user=[UUIDScope(value=_ACTOR)])


class TestAuditLogAdminSearchUnchanged:
    """The pre-existing admin endpoint stays superadmin-only and continues to work."""

    async def test_admin_can_call_admin_search(
        self,
        admin_v2_registry: V2ClientRegistry,
        seeded_rows: dict[str, uuid.UUID],
    ) -> None:
        result = await admin_v2_registry.audit_log.search(
            AdminSearchAuditLogsInput(limit=10, offset=0),
        )
        assert result.total_count >= len(seeded_rows)

    async def test_regular_user_cannot_call_admin_search(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.audit_log.search(AdminSearchAuditLogsInput(limit=1))


class TestAuditLogScopedSearchAuth:
    """The new scoped endpoint is reachable by any authenticated user."""

    async def test_regular_user_can_call_scoped_search(
        self,
        user_v2_registry: V2ClientRegistry,
        seeded_rows: dict[str, uuid.UUID],
    ) -> None:
        result = await user_v2_registry.audit_log.scoped_search(
            ScopedSearchAuditLogsInput(scope=_entity_scope(), limit=10),
        )
        ids = {item.id for item in result.items}
        assert {seeded_rows["success_a"], seeded_rows["success_b"], seeded_rows["error_a"]} <= ids


class TestAuditLogScopedSearchValidation:
    """Empty scope is rejected at the API boundary (DTO model_validator)."""

    async def test_empty_scope_rejected(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        bad_input = ScopedSearchAuditLogsInput.model_construct(
            scope=AuditLogScope.model_construct(entity=None, triggered_user=None),
        )
        with pytest.raises(InvalidRequestError):
            await user_v2_registry.audit_log.scoped_search(bad_input)


class TestAuditLogScopedSearchFilter:
    """Attribute filters narrow the scoped result set."""

    async def test_status_filter_narrows_results(
        self,
        user_v2_registry: V2ClientRegistry,
        seeded_rows: dict[str, uuid.UUID],
    ) -> None:
        result = await user_v2_registry.audit_log.scoped_search(
            ScopedSearchAuditLogsInput(
                scope=_entity_scope(),
                filter=AuditLogFilter(
                    status=AuditLogStatusFilter(equals=AuditLogStatus.ERROR),
                ),
                limit=10,
            ),
        )
        ids = {item.id for item in result.items}
        assert seeded_rows["error_a"] in ids
        assert seeded_rows["success_a"] not in ids
        assert seeded_rows["success_b"] not in ids


class TestAuditLogScopedSearchPagination:
    """Both pagination modes work against the scoped endpoint."""

    async def test_offset_pagination_limits_page_size(
        self,
        user_v2_registry: V2ClientRegistry,
        seeded_rows: dict[str, uuid.UUID],
    ) -> None:
        result = await user_v2_registry.audit_log.scoped_search(
            ScopedSearchAuditLogsInput(scope=_actor_scope(), limit=2, offset=0),
        )
        assert len(result.items) <= 2
        assert result.total_count >= len(seeded_rows)

    async def test_cursor_pagination_returns_page_info(
        self,
        user_v2_registry: V2ClientRegistry,
        seeded_rows: dict[str, uuid.UUID],
    ) -> None:
        first_page = await user_v2_registry.audit_log.scoped_search(
            ScopedSearchAuditLogsInput(scope=_actor_scope(), first=1),
        )
        assert len(first_page.items) == 1
        assert first_page.has_next_page is True
