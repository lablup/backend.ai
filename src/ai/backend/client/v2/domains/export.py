from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.export import (
    AuditLogExportCSVRequest,
    GetExportReportResponse,
    KeypairExportCSVRequest,
    ListExportReportsResponse,
    ProjectExportCSVRequest,
    SessionExportCSVRequest,
    UserExportCSVRequest,
)


class ExportClient(BaseDomainClient):
    API_PREFIX = "/export"

    # ---------------------------------------------------------------------------
    # Report endpoints
    # ---------------------------------------------------------------------------

    async def list_reports(self) -> ListExportReportsResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/reports",
            response_model=ListExportReportsResponse,
        )

    async def get_report(self, report_key: str) -> GetExportReportResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/reports/{report_key}",
            response_model=GetExportReportResponse,
        )

    # ---------------------------------------------------------------------------
    # CSV download endpoints
    # ---------------------------------------------------------------------------

    async def download_users_csv(
        self,
        request: UserExportCSVRequest | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/users/csv",
            json=json_body,
        )

    async def download_sessions_csv(
        self,
        request: SessionExportCSVRequest | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/sessions/csv",
            json=json_body,
        )

    async def download_projects_csv(
        self,
        request: ProjectExportCSVRequest | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/projects/csv",
            json=json_body,
        )

    async def download_keypairs_csv(
        self,
        request: KeypairExportCSVRequest | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/keypairs/csv",
            json=json_body,
        )

    async def download_audit_logs_csv(
        self,
        request: AuditLogExportCSVRequest | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/audit-logs/csv",
            json=json_body,
        )
