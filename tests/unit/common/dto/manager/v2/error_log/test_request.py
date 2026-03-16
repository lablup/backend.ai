"""Tests for ai.backend.common.dto.manager.v2.error_log.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.error_log.request import (
    AppendErrorLogInput,
    ListErrorLogsInput,
    MarkClearedInput,
)


class TestAppendErrorLogInput:
    """Tests for AppendErrorLogInput model creation and validation."""

    def test_valid_creation_with_all_required_fields(self) -> None:
        inp = AppendErrorLogInput(
            severity="critical",
            source="manager",
            message="Database connection failed",
            context_lang="python",
            context_env={"version": "3.11"},
        )
        assert inp.severity == "critical"
        assert inp.source == "manager"
        assert inp.message == "Database connection failed"
        assert inp.context_lang == "python"
        assert inp.context_env == {"version": "3.11"}

    def test_optional_fields_default_to_none(self) -> None:
        inp = AppendErrorLogInput(
            severity="error",
            source="agent",
            message="Kernel error",
            context_lang="python",
            context_env={},
        )
        assert inp.request_url is None
        assert inp.request_status is None
        assert inp.traceback is None

    def test_with_all_optional_fields(self) -> None:
        inp = AppendErrorLogInput(
            severity="error",
            source="manager",
            message="HTTP error",
            context_lang="python",
            context_env={"env": "production"},
            request_url="/api/v2/sessions",
            request_status=500,
            traceback="Traceback (most recent call last):\n  File ...",
        )
        assert inp.request_url == "/api/v2/sessions"
        assert inp.request_status == 500
        assert inp.traceback is not None

    def test_context_env_parsed_from_json_string(self) -> None:
        inp = AppendErrorLogInput.model_validate({
            "severity": "warning",
            "source": "storage",
            "message": "Low disk space",
            "context_lang": "python",
            "context_env": '{"disk_usage": 95, "path": "/data"}',
        })
        assert isinstance(inp.context_env, dict)
        assert inp.context_env["disk_usage"] == 95
        assert inp.context_env["path"] == "/data"

    def test_context_env_json_string_empty_object(self) -> None:
        inp = AppendErrorLogInput.model_validate({
            "severity": "info",
            "source": "manager",
            "message": "Info log",
            "context_lang": "python",
            "context_env": "{}",
        })
        assert inp.context_env == {}

    def test_context_env_invalid_json_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "severity": "error",
                "source": "manager",
                "message": "Error",
                "context_lang": "python",
                "context_env": "not-valid-json",
            })

    def test_context_env_json_non_object_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "severity": "error",
                "source": "manager",
                "message": "Error",
                "context_lang": "python",
                "context_env": "[1, 2, 3]",
            })

    def test_missing_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogInput.model_validate({
                "severity": "error",
                "source": "manager",
                # missing message, context_lang, context_env
            })

    def test_creation_from_dict(self) -> None:
        inp = AppendErrorLogInput.model_validate({
            "severity": "critical",
            "source": "scheduler",
            "message": "Scheduler crashed",
            "context_lang": "python",
            "context_env": {"scheduler_version": "4.0"},
        })
        assert inp.severity == "critical"
        assert inp.source == "scheduler"


class TestListErrorLogsInput:
    """Tests for ListErrorLogsInput model creation and validation."""

    def test_default_values(self) -> None:
        inp = ListErrorLogsInput()
        assert inp.mark_read is False
        assert inp.page_size == 20
        assert inp.page_no == 1

    def test_custom_values(self) -> None:
        inp = ListErrorLogsInput(mark_read=True, page_size=50, page_no=3)
        assert inp.mark_read is True
        assert inp.page_size == 50
        assert inp.page_no == 3

    def test_page_size_min_boundary(self) -> None:
        inp = ListErrorLogsInput(page_size=1)
        assert inp.page_size == 1

    def test_page_size_max_boundary(self) -> None:
        inp = ListErrorLogsInput(page_size=100)
        assert inp.page_size == 100

    def test_page_size_exceeds_max_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=200)

    def test_page_size_exceeds_max_boundary_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=101)

    def test_page_size_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=0)

    def test_page_size_negative_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_size=-1)

    def test_page_no_min_boundary(self) -> None:
        inp = ListErrorLogsInput(page_no=1)
        assert inp.page_no == 1

    def test_page_no_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_no=0)

    def test_page_no_negative_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsInput(page_no=-5)

    def test_mark_read_true(self) -> None:
        inp = ListErrorLogsInput(mark_read=True)
        assert inp.mark_read is True

    def test_creation_from_dict(self) -> None:
        inp = ListErrorLogsInput.model_validate({"mark_read": True, "page_size": 10, "page_no": 2})
        assert inp.mark_read is True
        assert inp.page_size == 10
        assert inp.page_no == 2


class TestMarkClearedInput:
    """Tests for MarkClearedInput model creation and validation."""

    def test_valid_creation(self) -> None:
        inp = MarkClearedInput(log_id="log-123-abc")
        assert inp.log_id == "log-123-abc"

    def test_creation_with_uuid_like_string(self) -> None:
        inp = MarkClearedInput(log_id="550e8400-e29b-41d4-a716-446655440000")
        assert inp.log_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_missing_log_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MarkClearedInput.model_validate({})

    def test_creation_from_dict(self) -> None:
        inp = MarkClearedInput.model_validate({"log_id": "error-log-42"})
        assert inp.log_id == "error-log-42"

    def test_round_trip_serialization(self) -> None:
        inp = MarkClearedInput(log_id="test-log-id-001")
        json_str = inp.model_dump_json()
        restored = MarkClearedInput.model_validate_json(json_str)
        assert restored.log_id == inp.log_id
