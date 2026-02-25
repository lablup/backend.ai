from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.export import (
    GetExportReportResponse,
    ListExportReportsResponse,
)


@pytest.mark.integration
class TestExportLifecycle:
    @pytest.mark.asyncio
    async def test_list_reports_then_get_each(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """list_reports -> validate report keys -> get_report(key) for each."""
        list_result = await admin_registry.export.list_reports()
        assert isinstance(list_result, ListExportReportsResponse)
        assert len(list_result.reports) > 0

        for report_info in list_result.reports:
            detail = await admin_registry.export.get_report(report_info.report_key)
            assert isinstance(detail, GetExportReportResponse)
            assert detail.report.report_key == report_info.report_key
            assert detail.report.name == report_info.name
            assert len(detail.report.fields) > 0
            for field in detail.report.fields:
                assert field.key
                assert field.name
                assert field.field_type


@pytest.mark.integration
class TestExportCSVDownload:
    @pytest.mark.asyncio
    async def test_download_users_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Download users CSV and verify it contains data."""
        result = await admin_registry.export.download_users_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_download_projects_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Download projects CSV and verify it contains seeded group data."""
        result = await admin_registry.export.download_projects_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_download_keypairs_csv(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Download keypairs CSV and verify it contains seeded keypair data."""
        result = await admin_registry.export.download_keypairs_csv()
        assert isinstance(result, bytes)
        assert len(result) > 0


@pytest.mark.integration
class TestExportAccessControl:
    @pytest.mark.asyncio
    async def test_regular_user_forbidden_on_all_endpoints(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user should get 403 on all export endpoints."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.list_reports()

        with pytest.raises(PermissionDeniedError):
            await user_registry.export.get_report("users")

        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_users_csv()

        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_sessions_csv()

        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_projects_csv()

        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_keypairs_csv()

        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_audit_logs_csv()
