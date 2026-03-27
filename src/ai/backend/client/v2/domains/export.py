from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.export import (
    AuditLogExportCSVInput,
    GetExportReportPayload,
    KeypairExportCSVInput,
    ListExportReportsPayload,
    ProjectExportCSVInput,
    SessionExportCSVInput,
    UserExportCSVInput,
)


class ExportClient(BaseDomainClient):
    API_PREFIX = "/export"

    # ---------------------------------------------------------------------------
    # Report endpoints
    # ---------------------------------------------------------------------------

    async def list_reports(self) -> ListExportReportsPayload:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/reports",
            response_model=ListExportReportsPayload,
        )

    async def get_report(self, report_key: str) -> GetExportReportPayload:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/reports/{report_key}",
            response_model=GetExportReportPayload,
        )

    # ---------------------------------------------------------------------------
    # CSV download endpoints
    # ---------------------------------------------------------------------------

    async def download_users_csv(
        self,
        request: UserExportCSVInput | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/users/csv",
            json=json_body,
        )

    async def download_sessions_csv(
        self,
        request: SessionExportCSVInput | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/sessions/csv",
            json=json_body,
        )

    async def download_projects_csv(
        self,
        request: ProjectExportCSVInput | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/projects/csv",
            json=json_body,
        )

    async def download_keypairs_csv(
        self,
        request: KeypairExportCSVInput | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/keypairs/csv",
            json=json_body,
        )

    async def download_audit_logs_csv(
        self,
        request: AuditLogExportCSVInput | None = None,
    ) -> bytes:
        json_body = request.model_dump(mode="json", exclude_none=True) if request else None
        return await self._client.download(
            f"{self.API_PREFIX}/audit-logs/csv",
            json=json_body,
        )
