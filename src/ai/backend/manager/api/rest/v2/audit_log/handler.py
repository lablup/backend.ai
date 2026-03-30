"""REST v2 handler for the audit log domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.audit_log.request import AdminSearchAuditLogsInput
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.audit_log import AuditLogAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AuditLogHandler:
    """REST v2 handler for audit log operations."""

    def __init__(self, *, adapter: AuditLogAdapter) -> None:
        self._adapter = adapter

    async def admin_search_audit_logs(
        self,
        body: BodyParam[AdminSearchAuditLogsInput],
    ) -> APIResponse:
        """Search audit logs with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
