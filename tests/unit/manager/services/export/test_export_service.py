"""Unit tests for ExportService."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.errors.export import ExportReportNotFound
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
    StreamingExportQuery,
)
from ai.backend.manager.repositories.export.repository import ExportRepository
from ai.backend.manager.services.export.actions.export_audit_logs_csv import (
    ExportAuditLogsCSVAction,
    ExportAuditLogsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_keypairs_csv import (
    ExportKeypairsCSVAction,
    ExportKeypairsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_projects_csv import (
    ExportProjectsCSVAction,
    ExportProjectsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_sessions_csv import (
    ExportSessionsCSVAction,
    ExportSessionsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_users_csv import (
    ExportUsersCSVAction,
    ExportUsersCSVActionResult,
)
from ai.backend.manager.services.export.actions.get_report import (
    GetReportAction,
    GetReportActionResult,
)
from ai.backend.manager.services.export.actions.list_reports import (
    ListReportsAction,
    ListReportsActionResult,
)
from ai.backend.manager.services.export.service import ExportService


async def _mock_row_iterator() -> AsyncIterator[Sequence[Sequence[Any]]]:
    yield [("val1", "val2"), ("val3", "val4")]


def _make_field(name: str) -> ExportFieldDef:
    col = MagicMock()
    return ExportFieldDef(
        key=name,
        name=name,
        description=f"Test field {name}",
        field_type=ExportFieldType.STRING,
        column=col,
    )


def _make_query(*field_names: str) -> StreamingExportQuery:
    fields = [_make_field(n) for n in field_names]
    return StreamingExportQuery(
        select_from=MagicMock(),
        fields=fields,
        conditions=[],
        orders=[],
        max_rows=1000,
        statement_timeout_sec=30,
    )


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=ExportRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> ExportService:
    return ExportService(repository=mock_repository)


class TestListReportsAction:
    async def test_returns_all_defined_reports(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        report = ReportDef(
            report_key="users",
            name="Users",
            description="User report",
            select_from=MagicMock(),
            fields=[_make_field("email")],
        )
        mock_repository.list_reports.return_value = [report]

        action = ListReportsAction()
        result = await service.list_reports(action)

        assert isinstance(result, ListReportsActionResult)
        assert result.reports == [report]
        mock_repository.list_reports.assert_called_once()

    async def test_returns_empty_list_when_none(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        mock_repository.list_reports.return_value = []

        action = ListReportsAction()
        result = await service.list_reports(action)

        assert result.reports == []


class TestGetReportAction:
    async def test_valid_report_key_returns_report_def(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        report = ReportDef(
            report_key="users",
            name="Users",
            description="User report",
            select_from=MagicMock(),
            fields=[_make_field("email")],
        )
        mock_repository.get_report.return_value = report

        action = GetReportAction(report_key="users")
        result = await service.get_report(action)

        assert isinstance(result, GetReportActionResult)
        assert result.report == report
        mock_repository.get_report.assert_called_once_with("users")

    async def test_non_existent_key_raises_export_report_not_found(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        mock_repository.get_report.side_effect = ExportReportNotFound("nonexistent")

        action = GetReportAction(report_key="nonexistent")
        with pytest.raises(ExportReportNotFound):
            await service.get_report(action)


class TestExportUsersCSVAction:
    async def test_utf8_encoding_with_field_names_and_row_iterator(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("email", "username")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        action = ExportUsersCSVAction(query=query, encoding="utf-8", filename="test.csv")
        result = await service.export_users_csv(action)

        assert isinstance(result, ExportUsersCSVActionResult)
        assert result.field_names == ["email", "username"]
        assert result.encoding == "utf-8"
        assert result.filename == "test.csv"
        mock_repository.execute_export.assert_called_once_with(query)

    async def test_custom_filename_used(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("email")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        action = ExportUsersCSVAction(query=query, filename="my-export.csv")
        result = await service.export_users_csv(action)

        assert result.filename == "my-export.csv"

    async def test_no_filename_generates_timestamp_based_name(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("email")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        with patch("ai.backend.manager.services.export.service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260305120000"
            action = ExportUsersCSVAction(query=query, filename=None)
            result = await service.export_users_csv(action)

        assert result.filename == "users-20260305120000.csv"

    async def test_empty_result_set_returns_headers_only(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        async def empty_iter() -> AsyncIterator[Sequence[Sequence[Any]]]:
            return
            yield  # noqa: unreachable

        query = _make_query("email", "username")
        mock_repository.execute_export = MagicMock(return_value=empty_iter())

        action = ExportUsersCSVAction(query=query, filename="test.csv")
        result = await service.export_users_csv(action)

        assert result.field_names == ["email", "username"]
        collected: list[Sequence[Sequence[Any]]] = []
        async for partition in result.row_iterator:
            collected.append(partition)
        assert collected == []

    async def test_large_data_streams_via_iterator(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        async def multi_partition_iter() -> AsyncIterator[Sequence[Sequence[Any]]]:
            yield [("a",), ("b",)]
            yield [("c",), ("d",)]
            yield [("e",), ("f",)]

        query = _make_query("name")
        mock_repository.execute_export = MagicMock(return_value=multi_partition_iter())

        action = ExportUsersCSVAction(query=query, filename="big.csv")
        result = await service.export_users_csv(action)

        partitions: list[Sequence[Sequence[Any]]] = []
        async for partition in result.row_iterator:
            partitions.append(partition)
        assert len(partitions) == 3


class TestExportSessionsCSVAction:
    async def test_generated_filename_and_field_names(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("session_id", "status", "created_at")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        with patch("ai.backend.manager.services.export.service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260305120000"
            action = ExportSessionsCSVAction(query=query, filename=None)
            result = await service.export_sessions_csv(action)

        assert isinstance(result, ExportSessionsCSVActionResult)
        assert result.field_names == ["session_id", "status", "created_at"]
        assert result.filename == "sessions-20260305120000.csv"

    async def test_custom_filename_and_rows(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("session_id")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        action = ExportSessionsCSVAction(query=query, filename="sessions-report.csv")
        result = await service.export_sessions_csv(action)

        assert result.filename == "sessions-report.csv"
        mock_repository.execute_export.assert_called_once_with(query)


class TestExportProjectsCSVAction:
    async def test_project_data_accuracy(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("name", "description", "created_at")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        action = ExportProjectsCSVAction(query=query, filename="projects.csv")
        result = await service.export_projects_csv(action)

        assert isinstance(result, ExportProjectsCSVActionResult)
        assert result.field_names == ["name", "description", "created_at"]
        assert result.filename == "projects.csv"

    async def test_empty_projects_returns_headers_only(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        async def empty_iter() -> AsyncIterator[Sequence[Sequence[Any]]]:
            return
            yield  # noqa: unreachable

        query = _make_query("name")
        mock_repository.execute_export = MagicMock(return_value=empty_iter())

        action = ExportProjectsCSVAction(query=query, filename="projects.csv")
        result = await service.export_projects_csv(action)

        assert result.field_names == ["name"]
        collected: list[Sequence[Sequence[Any]]] = []
        async for partition in result.row_iterator:
            collected.append(partition)
        assert collected == []


class TestExportKeypairsCSVAction:
    async def test_keypair_export_fields(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("access_key", "is_active", "created_at")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        action = ExportKeypairsCSVAction(query=query, filename="keypairs.csv")
        result = await service.export_keypairs_csv(action)

        assert isinstance(result, ExportKeypairsCSVActionResult)
        assert result.field_names == ["access_key", "is_active", "created_at"]
        assert "secret_key" not in result.field_names

    async def test_auto_generated_filename(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("access_key")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        with patch("ai.backend.manager.services.export.service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260305120000"
            action = ExportKeypairsCSVAction(query=query, filename=None)
            result = await service.export_keypairs_csv(action)

        assert result.filename == "keypairs-20260305120000.csv"


class TestExportAuditLogsCSVAction:
    async def test_audit_log_export_with_fields(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("timestamp", "user_id", "resource_type", "action")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        action = ExportAuditLogsCSVAction(query=query, filename="audit-logs.csv")
        result = await service.export_audit_logs_csv(action)

        assert isinstance(result, ExportAuditLogsCSVActionResult)
        assert result.field_names == ["timestamp", "user_id", "resource_type", "action"]
        assert result.filename == "audit-logs.csv"

    async def test_auto_generated_filename(
        self, service: ExportService, mock_repository: MagicMock
    ) -> None:
        query = _make_query("timestamp")
        mock_repository.execute_export = MagicMock(return_value=_mock_row_iterator())

        with patch("ai.backend.manager.services.export.service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260305120000"
            action = ExportAuditLogsCSVAction(query=query, filename=None)
            result = await service.export_audit_logs_csv(action)

        assert result.filename == "audit-logs-20260305120000.csv"
