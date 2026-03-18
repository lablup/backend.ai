"""Tests for ai.backend.common.dto.manager.v2.export.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.export.response import (
    GetExportReportPayload,
    ListExportReportsPayload,
)
from ai.backend.common.dto.manager.v2.export.types import ExportFieldInfoNode, ExportReportInfoNode


def _make_field(key: str = "username", field_type: str = "string") -> ExportFieldInfoNode:
    return ExportFieldInfoNode(
        key=key,
        name=key.replace("_", " ").title(),
        description=f"The {key} field",
        field_type=field_type,
    )


def _make_report(
    report_key: str = "users",
    fields: list[ExportFieldInfoNode] | None = None,
) -> ExportReportInfoNode:
    return ExportReportInfoNode(
        report_key=report_key,
        name=f"{report_key.title()} Report",
        description=f"Export {report_key} data",
        fields=fields or [],
    )


class TestListExportReportsPayload:
    """Tests for ListExportReportsPayload model."""

    def test_creation_with_empty_reports(self) -> None:
        payload = ListExportReportsPayload(reports=[])
        assert payload.reports == []

    def test_creation_with_single_report(self) -> None:
        report = _make_report("users", [_make_field("username")])
        payload = ListExportReportsPayload(reports=[report])
        assert len(payload.reports) == 1
        assert payload.reports[0].report_key == "users"

    def test_creation_with_multiple_reports(self) -> None:
        reports = [
            _make_report("users", [_make_field("username")]),
            _make_report("sessions", [_make_field("name")]),
            _make_report("projects", [_make_field("name")]),
        ]
        payload = ListExportReportsPayload(reports=reports)
        assert len(payload.reports) == 3
        assert payload.reports[1].report_key == "sessions"

    def test_reports_contain_export_report_info_nodes(self) -> None:
        report = _make_report("users")
        payload = ListExportReportsPayload(reports=[report])
        assert isinstance(payload.reports[0], ExportReportInfoNode)

    def test_round_trip_serialization(self) -> None:
        reports = [
            _make_report("users", [_make_field("username"), _make_field("email")]),
            _make_report("sessions", [_make_field("name")]),
        ]
        payload = ListExportReportsPayload(reports=reports)
        json_str = payload.model_dump_json()
        restored = ListExportReportsPayload.model_validate_json(json_str)
        assert len(restored.reports) == 2
        assert restored.reports[0].report_key == "users"
        assert len(restored.reports[0].fields) == 2
        assert restored.reports[0].fields[0].key == "username"

    def test_model_dump_json_structure(self) -> None:
        payload = ListExportReportsPayload(reports=[_make_report("users")])
        data = json.loads(payload.model_dump_json())
        assert "reports" in data
        assert isinstance(data["reports"], list)
        assert len(data["reports"]) == 1
        assert "report_key" in data["reports"][0]

    def test_nested_fields_in_serialized_json(self) -> None:
        fields = [_make_field("username"), _make_field("created_at", "datetime")]
        report = _make_report("users", fields)
        payload = ListExportReportsPayload(reports=[report])
        data = json.loads(payload.model_dump_json())
        assert "fields" in data["reports"][0]
        assert len(data["reports"][0]["fields"]) == 2
        assert data["reports"][0]["fields"][0]["key"] == "username"


class TestGetExportReportPayload:
    """Tests for GetExportReportPayload model."""

    def test_creation_with_report(self) -> None:
        report = _make_report("users", [_make_field("username")])
        payload = GetExportReportPayload(report=report)
        assert payload.report.report_key == "users"

    def test_report_name_accessible(self) -> None:
        report = _make_report("sessions")
        payload = GetExportReportPayload(report=report)
        assert payload.report.name == "Sessions Report"

    def test_report_fields_accessible(self) -> None:
        fields = [_make_field("name"), _make_field("status")]
        report = _make_report("sessions", fields)
        payload = GetExportReportPayload(report=report)
        assert len(payload.report.fields) == 2
        assert payload.report.fields[0].key == "name"

    def test_round_trip_serialization(self) -> None:
        fields = [
            _make_field("id", "uuid"),
            _make_field("username"),
            _make_field("created_at", "datetime"),
        ]
        report = _make_report("users", fields)
        payload = GetExportReportPayload(report=report)
        json_str = payload.model_dump_json()
        restored = GetExportReportPayload.model_validate_json(json_str)
        assert restored.report.report_key == "users"
        assert len(restored.report.fields) == 3
        assert restored.report.fields[0].key == "id"
        assert restored.report.fields[0].field_type == "uuid"

    def test_model_dump_json_structure(self) -> None:
        payload = GetExportReportPayload(report=_make_report("projects"))
        data = json.loads(payload.model_dump_json())
        assert "report" in data
        assert "report_key" in data["report"]
        assert "name" in data["report"]
        assert "description" in data["report"]
        assert "fields" in data["report"]

    def test_report_is_export_report_info_node_instance(self) -> None:
        payload = GetExportReportPayload(report=_make_report("users"))
        assert isinstance(payload.report, ExportReportInfoNode)
