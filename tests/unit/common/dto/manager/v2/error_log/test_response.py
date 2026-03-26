"""Tests for ai.backend.common.dto.manager.v2.error_log.response module."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.error_log.response import (
    AppendErrorLogPayload,
    ErrorLogNode,
    ListErrorLogsPayload,
    MarkClearedPayload,
)
from ai.backend.common.dto.manager.v2.error_log.types import (
    ErrorLogContextInfo,
    ErrorLogRequestInfo,
)


def _make_context_info() -> ErrorLogContextInfo:
    return ErrorLogContextInfo(
        context_lang="python",
        context_env={"version": "3.11", "env": "production"},
    )


def _make_request_info(
    url: str | None = "/api/v2/sessions",
    status: int | None = 500,
) -> ErrorLogRequestInfo:
    return ErrorLogRequestInfo(request_url=url, request_status=status)


def _make_error_log_node(
    log_id: str = "log-001",
    is_cleared: bool | None = None,
) -> ErrorLogNode:
    return ErrorLogNode(
        log_id=log_id,
        created_at=1700000000.0,
        severity="critical",
        source="manager",
        is_read=False,
        message="Database connection failed",
        context=_make_context_info(),
        request_info=_make_request_info(),
        is_cleared=is_cleared,
    )


class TestErrorLogNodeCreation:
    """Tests for ErrorLogNode model creation."""

    def test_creation_with_required_fields(self) -> None:
        node = _make_error_log_node()
        assert node.log_id == "log-001"
        assert node.severity == "critical"
        assert node.source == "manager"
        assert node.is_read is False
        assert node.message == "Database connection failed"

    def test_creation_with_all_fields(self) -> None:
        node = ErrorLogNode(
            log_id="log-002",
            created_at=1700000001.5,
            severity="error",
            source="agent",
            user="user-uuid-abc",
            is_read=True,
            message="Kernel crashed",
            context=_make_context_info(),
            request_info=_make_request_info(),
            traceback="Traceback (most recent call last):\n  ...",
            is_cleared=True,
        )
        assert node.log_id == "log-002"
        assert node.user == "user-uuid-abc"
        assert node.traceback is not None
        assert node.is_cleared is True

    def test_default_user_is_none(self) -> None:
        node = _make_error_log_node()
        assert node.user is None

    def test_default_traceback_is_none(self) -> None:
        node = _make_error_log_node()
        assert node.traceback is None

    def test_default_is_cleared_is_none(self) -> None:
        node = _make_error_log_node()
        assert node.is_cleared is None

    def test_context_groups_context_fields(self) -> None:
        node = _make_error_log_node()
        assert isinstance(node.context, ErrorLogContextInfo)
        assert node.context.context_lang == "python"
        assert node.context.context_env["version"] == "3.11"

    def test_request_info_groups_http_fields(self) -> None:
        node = _make_error_log_node()
        assert isinstance(node.request_info, ErrorLogRequestInfo)
        assert node.request_info.request_url == "/api/v2/sessions"
        assert node.request_info.request_status == 500

    def test_request_info_with_none_fields(self) -> None:
        node = ErrorLogNode(
            log_id="log-003",
            created_at=1700000002.0,
            severity="warning",
            source="storage",
            is_read=False,
            message="Disk warning",
            context=_make_context_info(),
            request_info=ErrorLogRequestInfo(),
        )
        assert node.request_info.request_url is None
        assert node.request_info.request_status is None

    def test_is_cleared_can_be_true(self) -> None:
        node = _make_error_log_node(is_cleared=True)
        assert node.is_cleared is True

    def test_is_cleared_can_be_false(self) -> None:
        node = _make_error_log_node(is_cleared=False)
        assert node.is_cleared is False

    def test_missing_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ErrorLogNode.model_validate({
                "log_id": "log-004",
                "severity": "error",
                # missing created_at, source, is_read, message, context, request_info
            })


class TestErrorLogNodeSerialization:
    """Tests for ErrorLogNode serialization."""

    def test_model_dump_json_includes_all_fields(self) -> None:
        node = _make_error_log_node()
        data = json.loads(node.model_dump_json())
        assert "log_id" in data
        assert "created_at" in data
        assert "severity" in data
        assert "source" in data
        assert "is_read" in data
        assert "message" in data
        assert "context" in data
        assert "request_info" in data

    def test_nested_context_preserved_in_json(self) -> None:
        node = _make_error_log_node()
        data = json.loads(node.model_dump_json())
        assert "context" in data
        assert data["context"]["context_lang"] == "python"
        assert data["context"]["context_env"]["version"] == "3.11"

    def test_nested_request_info_preserved_in_json(self) -> None:
        node = _make_error_log_node()
        data = json.loads(node.model_dump_json())
        assert "request_info" in data
        assert data["request_info"]["request_url"] == "/api/v2/sessions"
        assert data["request_info"]["request_status"] == 500

    def test_round_trip_serialization(self) -> None:
        node = _make_error_log_node()
        json_str = node.model_dump_json()
        restored = ErrorLogNode.model_validate_json(json_str)
        assert restored.log_id == node.log_id
        assert restored.severity == node.severity
        assert restored.source == node.source
        assert restored.is_read == node.is_read

    def test_round_trip_preserves_nested_context(self) -> None:
        node = _make_error_log_node()
        json_str = node.model_dump_json()
        restored = ErrorLogNode.model_validate_json(json_str)
        assert restored.context.context_lang == "python"
        assert restored.context.context_env["version"] == "3.11"

    def test_round_trip_preserves_nested_request_info(self) -> None:
        node = _make_error_log_node()
        json_str = node.model_dump_json()
        restored = ErrorLogNode.model_validate_json(json_str)
        assert restored.request_info.request_url == "/api/v2/sessions"
        assert restored.request_info.request_status == 500

    def test_round_trip_with_all_optional_fields(self) -> None:
        node = ErrorLogNode(
            log_id="log-full",
            created_at=1700000099.0,
            severity="error",
            source="manager",
            user="user-abc",
            is_read=True,
            message="Full error",
            context=_make_context_info(),
            request_info=_make_request_info(),
            traceback="tb line 1\ntb line 2",
            is_cleared=False,
        )
        json_str = node.model_dump_json()
        restored = ErrorLogNode.model_validate_json(json_str)
        assert restored.user == "user-abc"
        assert restored.traceback == "tb line 1\ntb line 2"
        assert restored.is_cleared is False


class TestAppendErrorLogPayload:
    """Tests for AppendErrorLogPayload model."""

    def test_creation_with_success_true(self) -> None:
        payload = AppendErrorLogPayload(success=True)
        assert payload.success is True

    def test_creation_with_success_false(self) -> None:
        payload = AppendErrorLogPayload(success=False)
        assert payload.success is False

    def test_missing_success_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AppendErrorLogPayload.model_validate({})

    def test_round_trip_serialization(self) -> None:
        payload = AppendErrorLogPayload(success=True)
        json_str = payload.model_dump_json()
        restored = AppendErrorLogPayload.model_validate_json(json_str)
        assert restored.success is True


class TestListErrorLogsPayload:
    """Tests for ListErrorLogsPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = ListErrorLogsPayload(logs=[], count=0)
        assert payload.logs == []
        assert payload.count == 0

    def test_creation_with_log_nodes(self) -> None:
        nodes = [_make_error_log_node("log-001"), _make_error_log_node("log-002")]
        payload = ListErrorLogsPayload(logs=nodes, count=2)
        assert len(payload.logs) == 2
        assert payload.count == 2

    def test_logs_contains_error_log_node_instances(self) -> None:
        node = _make_error_log_node()
        payload = ListErrorLogsPayload(logs=[node], count=1)
        assert isinstance(payload.logs[0], ErrorLogNode)
        assert payload.logs[0].log_id == "log-001"

    def test_missing_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListErrorLogsPayload.model_validate({"logs": []})  # missing count

    def test_round_trip_serialization(self) -> None:
        nodes = [_make_error_log_node("log-r01"), _make_error_log_node("log-r02")]
        payload = ListErrorLogsPayload(logs=nodes, count=2)
        json_str = payload.model_dump_json()
        restored = ListErrorLogsPayload.model_validate_json(json_str)
        assert restored.count == 2
        assert len(restored.logs) == 2
        assert restored.logs[0].log_id == "log-r01"
        assert restored.logs[1].log_id == "log-r02"

    def test_round_trip_preserves_nested_context(self) -> None:
        node = _make_error_log_node()
        payload = ListErrorLogsPayload(logs=[node], count=1)
        json_str = payload.model_dump_json()
        restored = ListErrorLogsPayload.model_validate_json(json_str)
        assert restored.logs[0].context.context_lang == "python"


class TestMarkClearedPayload:
    """Tests for MarkClearedPayload model."""

    def test_creation_with_success_true(self) -> None:
        payload = MarkClearedPayload(success=True)
        assert payload.success is True

    def test_creation_with_success_false(self) -> None:
        payload = MarkClearedPayload(success=False)
        assert payload.success is False

    def test_missing_success_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MarkClearedPayload.model_validate({})

    def test_round_trip_serialization(self) -> None:
        payload = MarkClearedPayload(success=False)
        json_str = payload.model_dump_json()
        restored = MarkClearedPayload.model_validate_json(json_str)
        assert restored.success is False
