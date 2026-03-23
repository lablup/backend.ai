"""Tests for ai.backend.common.dto.manager.v2.operations.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.operations.types import (
    ErrorLogSeverity,
    ManagerStatus,
    SchedulerOps,
)
from ai.backend.common.dto.manager.v2.operations.types import (
    ErrorLogContextInfo,
    ErrorLogOrderField,
    ErrorLogRequestInfo,
    OrderDirection,
)
from ai.backend.common.dto.manager.v2.operations.types import (
    ErrorLogSeverity as ExportedErrorLogSeverity,
)
from ai.backend.common.dto.manager.v2.operations.types import ManagerStatus as ExportedManagerStatus
from ai.backend.common.dto.manager.v2.operations.types import SchedulerOps as ExportedSchedulerOps


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestErrorLogOrderField:
    """Tests for ErrorLogOrderField enum."""

    def test_created_at_value(self) -> None:
        assert ErrorLogOrderField.CREATED_AT.value == "created_at"

    def test_severity_value(self) -> None:
        assert ErrorLogOrderField.SEVERITY.value == "severity"

    def test_source_value(self) -> None:
        assert ErrorLogOrderField.SOURCE.value == "source"

    def test_all_values_are_strings(self) -> None:
        for member in ErrorLogOrderField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(ErrorLogOrderField)
        assert len(members) == 3

    def test_from_string_created_at(self) -> None:
        assert ErrorLogOrderField("created_at") is ErrorLogOrderField.CREATED_AT

    def test_from_string_severity(self) -> None:
        assert ErrorLogOrderField("severity") is ErrorLogOrderField.SEVERITY

    def test_from_string_source(self) -> None:
        assert ErrorLogOrderField("source") is ErrorLogOrderField.SOURCE


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_error_log_severity_is_same_object(self) -> None:
        assert ExportedErrorLogSeverity is ErrorLogSeverity

    def test_manager_status_is_same_object(self) -> None:
        assert ExportedManagerStatus is ManagerStatus

    def test_scheduler_ops_is_same_object(self) -> None:
        assert ExportedSchedulerOps is SchedulerOps

    def test_error_log_severity_critical_value(self) -> None:
        assert ExportedErrorLogSeverity.CRITICAL.value == "critical"

    def test_error_log_severity_error_value(self) -> None:
        assert ExportedErrorLogSeverity.ERROR.value == "error"

    def test_error_log_severity_warning_value(self) -> None:
        assert ExportedErrorLogSeverity.WARNING.value == "warning"

    def test_manager_status_running_value(self) -> None:
        assert ExportedManagerStatus.RUNNING.value == "running"

    def test_manager_status_frozen_value(self) -> None:
        assert ExportedManagerStatus.FROZEN.value == "frozen"

    def test_manager_status_terminated_value(self) -> None:
        assert ExportedManagerStatus.TERMINATED.value == "terminated"

    def test_manager_status_preparing_value(self) -> None:
        assert ExportedManagerStatus.PREPARING.value == "preparing"

    def test_scheduler_ops_include_agents_value(self) -> None:
        assert ExportedSchedulerOps.INCLUDE_AGENTS.value == "include-agents"

    def test_scheduler_ops_exclude_agents_value(self) -> None:
        assert ExportedSchedulerOps.EXCLUDE_AGENTS.value == "exclude-agents"


class TestErrorLogContextInfoCreation:
    """Tests for ErrorLogContextInfo Pydantic model creation."""

    def test_basic_creation(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"key": "value"})
        assert ctx.lang == "python"
        assert ctx.env == {"key": "value"}

    def test_creation_with_empty_env(self) -> None:
        ctx = ErrorLogContextInfo(lang="javascript", env={})
        assert ctx.lang == "javascript"
        assert ctx.env == {}

    def test_creation_with_nested_env(self) -> None:
        ctx = ErrorLogContextInfo(
            lang="python",
            env={"BACKEND_AI_VERSION": "24.12.0", "DEBUG": "true"},
        )
        assert ctx.env["BACKEND_AI_VERSION"] == "24.12.0"

    def test_creation_from_dict(self) -> None:
        ctx = ErrorLogContextInfo.model_validate({
            "lang": "python",
            "env": {"HOME": "/root"},
        })
        assert ctx.lang == "python"
        assert ctx.env["HOME"] == "/root"


class TestErrorLogContextInfoSerialization:
    """Tests for ErrorLogContextInfo serialization and deserialization."""

    def test_model_dump(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"k": "v"})
        data = ctx.model_dump()
        assert data["lang"] == "python"
        assert data["env"] == {"k": "v"}

    def test_model_dump_json(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"k": "v"})
        json_str = ctx.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["lang"] == "python"
        assert parsed["env"] == {"k": "v"}

    def test_serialization_round_trip(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"VERSION": "1.0"})
        json_str = ctx.model_dump_json()
        restored = ErrorLogContextInfo.model_validate_json(json_str)
        assert restored.lang == ctx.lang
        assert restored.env == ctx.env


class TestErrorLogRequestInfoCreation:
    """Tests for ErrorLogRequestInfo Pydantic model creation."""

    def test_defaults_are_none(self) -> None:
        req = ErrorLogRequestInfo()
        assert req.url is None
        assert req.status is None

    def test_creation_with_url_and_status(self) -> None:
        req = ErrorLogRequestInfo(url="/api/v2/resource", status=404)
        assert req.url == "/api/v2/resource"
        assert req.status == 404

    def test_creation_with_url_only(self) -> None:
        req = ErrorLogRequestInfo(url="/api/v2/session")
        assert req.url == "/api/v2/session"
        assert req.status is None

    def test_creation_with_status_only(self) -> None:
        req = ErrorLogRequestInfo(status=500)
        assert req.url is None
        assert req.status == 500

    def test_creation_from_dict(self) -> None:
        req = ErrorLogRequestInfo.model_validate({"url": "/health", "status": 200})
        assert req.url == "/health"
        assert req.status == 200


class TestErrorLogRequestInfoSerialization:
    """Tests for ErrorLogRequestInfo serialization and deserialization."""

    def test_model_dump_with_all_fields(self) -> None:
        req = ErrorLogRequestInfo(url="/api", status=500)
        data = req.model_dump()
        assert data["url"] == "/api"
        assert data["status"] == 500

    def test_model_dump_with_none_fields(self) -> None:
        req = ErrorLogRequestInfo()
        data = req.model_dump()
        assert data["url"] is None
        assert data["status"] is None

    def test_serialization_round_trip(self) -> None:
        req = ErrorLogRequestInfo(url="/api/v2", status=400)
        json_str = req.model_dump_json()
        restored = ErrorLogRequestInfo.model_validate_json(json_str)
        assert restored.url == req.url
        assert restored.status == req.status

    def test_serialization_round_trip_with_none(self) -> None:
        req = ErrorLogRequestInfo()
        json_str = req.model_dump_json()
        restored = ErrorLogRequestInfo.model_validate_json(json_str)
        assert restored.url is None
        assert restored.status is None
