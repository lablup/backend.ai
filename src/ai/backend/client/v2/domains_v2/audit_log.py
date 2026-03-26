"""V2 SDK client for the audit log domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.audit_log.request import AdminSearchAuditLogsInput
from ai.backend.common.dto.manager.v2.audit_log.response import AdminSearchAuditLogsPayload

_PATH = "/v2/audit-logs"


class V2AuditLogClient(BaseDomainClient):
    """SDK client for audit log operations."""

    async def search(self, request: AdminSearchAuditLogsInput) -> AdminSearchAuditLogsPayload:
        """Search audit logs with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchAuditLogsPayload,
        )
