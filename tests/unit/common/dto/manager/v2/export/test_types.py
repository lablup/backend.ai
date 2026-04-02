"""Tests for ai.backend.common.dto.manager.v2.export.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.export.types import (
    ExportFieldInfoNode,
    ExportReportInfoNode,
    ExportReportKey,
    OrderDirection,
)


class TestOrderDirection:
    """Tests for OrderDirection StrEnum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestExportReportKey:
    """Tests for ExportReportKey StrEnum."""

    def test_users_value(self) -> None:
        assert ExportReportKey.USERS.value == "users"

    def test_sessions_value(self) -> None:
        assert ExportReportKey.SESSIONS.value == "sessions"

    def test_projects_value(self) -> None:
        assert ExportReportKey.PROJECTS.value == "projects"

    def test_enum_members_count(self) -> None:
        assert len(list(ExportReportKey)) == 3

    def test_all_values_are_strings(self) -> None:
        for member in ExportReportKey:
            assert isinstance(member.value, str)

    def test_from_string_users(self) -> None:
        assert ExportReportKey("users") is ExportReportKey.USERS

    def test_from_string_sessions(self) -> None:
        assert ExportReportKey("sessions") is ExportReportKey.SESSIONS


class TestExportFieldInfoNode:
    """Tests for ExportFieldInfoNode model creation and serialization."""

    def test_creation_with_all_fields(self) -> None:
        node = ExportFieldInfoNode(
            key="username",
            name="Username",
            description="The unique username of the user",
            field_type="string",
        )
        assert node.key == "username"
        assert node.name == "Username"
        assert node.description == "The unique username of the user"
        assert node.field_type == "string"

    def test_creation_with_datetime_type(self) -> None:
        node = ExportFieldInfoNode(
            key="created_at",
            name="Created At",
            description="Timestamp when the record was created",
            field_type="datetime",
        )
        assert node.field_type == "datetime"

    def test_round_trip_serialization(self) -> None:
        node = ExportFieldInfoNode(
            key="email",
            name="Email",
            description="User email address",
            field_type="string",
        )
        json_str = node.model_dump_json()
        restored = ExportFieldInfoNode.model_validate_json(json_str)
        assert restored.key == node.key
        assert restored.name == node.name
        assert restored.description == node.description
        assert restored.field_type == node.field_type

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        node = ExportFieldInfoNode(
            key="field_type",
            name="Field Type",
            description="Type of the field",
            field_type="string",
        )
        data = json.loads(node.model_dump_json())
        assert "field_type" in data
        assert "fieldType" not in data


class TestExportReportInfoNode:
    """Tests for ExportReportInfoNode model creation and serialization."""

    def test_creation_with_fields(self) -> None:
        fields = [
            ExportFieldInfoNode(
                key="username", name="Username", description="User name", field_type="string"
            ),
            ExportFieldInfoNode(
                key="email", name="Email", description="User email", field_type="string"
            ),
        ]
        node = ExportReportInfoNode(
            report_key="users",
            name="Users Report",
            description="Export user data",
            fields=fields,
        )
        assert node.report_key == "users"
        assert node.name == "Users Report"
        assert node.description == "Export user data"
        assert len(node.fields) == 2
        assert node.fields[0].key == "username"

    def test_creation_with_empty_fields(self) -> None:
        node = ExportReportInfoNode(
            report_key="test",
            name="Test Report",
            description="Test",
            fields=[],
        )
        assert node.fields == []

    def test_round_trip_serialization_with_nested_fields(self) -> None:
        fields = [
            ExportFieldInfoNode(
                key="id",
                name="ID",
                description="Unique identifier",
                field_type="uuid",
            ),
        ]
        node = ExportReportInfoNode(
            report_key="sessions",
            name="Sessions Report",
            description="Export session data",
            fields=fields,
        )
        json_str = node.model_dump_json()
        restored = ExportReportInfoNode.model_validate_json(json_str)
        assert restored.report_key == node.report_key
        assert restored.name == node.name
        assert len(restored.fields) == 1
        assert restored.fields[0].key == "id"

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        node = ExportReportInfoNode(
            report_key="users",
            name="Users",
            description="Users report",
            fields=[],
        )
        data = json.loads(node.model_dump_json())
        assert "report_key" in data
        assert "reportKey" not in data
