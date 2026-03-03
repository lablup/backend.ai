from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import (
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
)
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.export import (
    GetExportReportResponse,
    ListExportReportsResponse,
    UserExportCSVRequest,
)


class TestListReports:
    async def test_admin_lists_reports(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.list_reports()
        assert isinstance(result, ListExportReportsResponse)
        assert isinstance(result.reports, list)
        assert len(result.reports) > 0
        report_keys = [r.report_key for r in result.reports]
        assert "users" in report_keys

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.list_reports()


class TestGetReport:
    async def test_admin_gets_users_report(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.get_report("users")
        assert isinstance(result, GetExportReportResponse)
        assert result.report.report_key == "users"
        assert len(result.report.fields) > 0

    async def test_admin_gets_sessions_report(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.get_report("sessions")
        assert isinstance(result, GetExportReportResponse)
        assert result.report.report_key == "sessions"
        assert len(result.report.fields) > 0

    async def test_admin_gets_projects_report(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.get_report("projects")
        assert isinstance(result, GetExportReportResponse)
        assert result.report.report_key == "projects"
        assert len(result.report.fields) > 0

    async def test_get_nonexistent_report(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises((InvalidRequestError, NotFoundError)):
            await admin_registry.export.get_report("nonexistent")

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.get_report("users")


class TestDownloadUsersCSV:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 sends POST with json=None (empty body);"
            " server BodyParam parsing requires a JSON body,"
            " returning 400 'Malformed request body'."
        ),
    )
    async def test_admin_downloads_users_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.download_users_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_admin_downloads_with_fields(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        request = UserExportCSVRequest(fields=["uuid", "email"])
        result = await admin_registry.export.download_users_csv(request)
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_users_csv()


class TestDownloadSessionsCSV:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 sends POST with json=None (empty body);"
            " server BodyParam parsing requires a JSON body,"
            " returning 400 'Malformed request body'."
        ),
    )
    async def test_admin_downloads_sessions_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.download_sessions_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_sessions_csv()


class TestDownloadProjectsCSV:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 sends POST with json=None (empty body);"
            " server BodyParam parsing requires a JSON body,"
            " returning 400 'Malformed request body'."
        ),
    )
    async def test_admin_downloads_projects_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.download_projects_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_projects_csv()


class TestDownloadKeypairsCSV:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 sends POST with json=None (empty body);"
            " server BodyParam parsing requires a JSON body,"
            " returning 400 'Malformed request body'."
        ),
    )
    async def test_admin_downloads_keypairs_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.download_keypairs_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_keypairs_csv()


class TestDownloadAuditLogsCSV:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 sends POST with json=None (empty body);"
            " server BodyParam parsing requires a JSON body,"
            " returning 400 'Malformed request body'."
        ),
    )
    async def test_admin_downloads_audit_logs_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.export.download_audit_logs_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_regular_user_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_audit_logs_csv()
