"""Tests for ai.backend.common.dto.manager.v2.operations.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.operations.response import (
    AnnouncementNode,
    AppendErrorLogPayload,
    ClearErrorLogPayload,
    ErrorLogNode,
    ListErrorLogsPayload,
    ManagerNodeInfo,
    ManagerStatusPayload,
)
from ai.backend.common.dto.manager.v2.operations.types import (
    ErrorLogContextInfo,
    ErrorLogRequestInfo,
)


class TestErrorLogNodeCreation:
    """Tests for ErrorLogNode model creation with all fields."""

    def test_creation_with_required_fields(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={})
        req_info = ErrorLogRequestInfo()
        node = ErrorLogNode(
            log_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            created_at=1700000000.0,
            severity="error",
            source="manager",
            user=None,
            is_read=False,
            message="Something failed",
            context=ctx,
            request=req_info,
        )
        assert node.log_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert node.created_at == 1700000000.0
        assert node.severity == "error"
        assert node.source == "manager"
        assert node.user is None
        assert node.is_read is False
        assert node.message == "Something failed"
        assert node.traceback is None
        assert node.is_cleared is None

    def test_creation_with_all_fields(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"DEBUG": "true"})
        req_info = ErrorLogRequestInfo(url="/api/v2/session", status=500)
        node = ErrorLogNode(
            log_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            created_at=1700000000.0,
            severity="critical",
            source="agent",
            user="user-uuid-string",
            is_read=True,
            message="Critical failure in agent",
            context=ctx,
            request=req_info,
            traceback="Traceback (most recent call last)...",
            is_cleared=False,
        )
        assert node.user == "user-uuid-string"
        assert node.is_read is True
        assert node.traceback == "Traceback (most recent call last)..."
        assert node.is_cleared is False

    def test_nested_context_is_preserved(self) -> None:
        ctx = ErrorLogContextInfo(lang="javascript", env={"NODE_ENV": "production"})
        req_info = ErrorLogRequestInfo()
        node = ErrorLogNode(
            log_id="log-id-string",
            created_at=1700000000.0,
            severity="warning",
            source="webserver",
            user=None,
            is_read=False,
            message="Warning",
            context=ctx,
            request=req_info,
        )
        assert node.context.lang == "javascript"
        assert node.context.env["NODE_ENV"] == "production"

    def test_nested_request_info_is_preserved(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={})
        req_info = ErrorLogRequestInfo(url="/api/health", status=503)
        node = ErrorLogNode(
            log_id="log-id-string",
            created_at=1700000000.0,
            severity="error",
            source="manager",
            user=None,
            is_read=False,
            message="Health check failed",
            context=ctx,
            request=req_info,
        )
        assert node.request.url == "/api/health"
        assert node.request.status == 503

    def test_request_with_none_fields(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={})
        req_info = ErrorLogRequestInfo()
        node = ErrorLogNode(
            log_id="log-id-string",
            created_at=1700000000.0,
            severity="error",
            source="manager",
            user=None,
            is_read=False,
            message="Error",
            context=ctx,
            request=req_info,
        )
        assert node.request.url is None
        assert node.request.status is None


class TestErrorLogNodeSerialization:
    """Tests for ErrorLogNode serialization and round-trip."""

    def test_model_dump_json_has_nested_context(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"k": "v"})
        req_info = ErrorLogRequestInfo(url="/api", status=404)
        node = ErrorLogNode(
            log_id="log-id-string",
            created_at=1700000000.0,
            severity="error",
            source="manager",
            user=None,
            is_read=False,
            message="Not found",
            context=ctx,
            request=req_info,
        )
        data = json.loads(node.model_dump_json())
        assert "context" in data
        assert data["context"]["lang"] == "python"
        assert data["context"]["env"] == {"k": "v"}
        assert "request" in data
        assert data["request"]["url"] == "/api"
        assert data["request"]["status"] == 404

    def test_serialization_round_trip_preserves_all_fields(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={"VERSION": "1.0"})
        req_info = ErrorLogRequestInfo(url="/api/v2", status=400)
        node = ErrorLogNode(
            log_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            created_at=1700000000.5,
            severity="critical",
            source="storage",
            user="user-123",
            is_read=True,
            message="Disk full",
            context=ctx,
            request=req_info,
            traceback="line 42...",
            is_cleared=True,
        )
        json_str = node.model_dump_json()
        restored = ErrorLogNode.model_validate_json(json_str)
        assert restored.log_id == node.log_id
        assert restored.created_at == node.created_at
        assert restored.severity == node.severity
        assert restored.source == node.source
        assert restored.user == node.user
        assert restored.is_read == node.is_read
        assert restored.message == node.message
        assert restored.context.lang == node.context.lang
        assert restored.context.env == node.context.env
        assert restored.request.url == node.request.url
        assert restored.request.status == node.request.status
        assert restored.traceback == node.traceback
        assert restored.is_cleared == node.is_cleared

    def test_round_trip_with_none_optional_fields(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={})
        req_info = ErrorLogRequestInfo()
        node = ErrorLogNode(
            log_id="log-id-string",
            created_at=1700000000.0,
            severity="warning",
            source="agent",
            user=None,
            is_read=False,
            message="Warning message",
            context=ctx,
            request=req_info,
        )
        json_str = node.model_dump_json()
        restored = ErrorLogNode.model_validate_json(json_str)
        assert restored.user is None
        assert restored.traceback is None
        assert restored.is_cleared is None
        assert restored.request.url is None
        assert restored.request.status is None


class TestAppendErrorLogPayload:
    """Tests for AppendErrorLogPayload model."""

    def test_creation_with_success_true(self) -> None:
        payload = AppendErrorLogPayload(success=True)
        assert payload.success is True

    def test_creation_with_success_false(self) -> None:
        payload = AppendErrorLogPayload(success=False)
        assert payload.success is False

    def test_round_trip_serialization(self) -> None:
        payload = AppendErrorLogPayload(success=True)
        json_str = payload.model_dump_json()
        restored = AppendErrorLogPayload.model_validate_json(json_str)
        assert restored.success is True


class TestListErrorLogsPayload:
    """Tests for ListErrorLogsPayload model."""

    def test_creation_with_empty_logs(self) -> None:
        payload = ListErrorLogsPayload(logs=[], count=0)
        assert payload.logs == []
        assert payload.count == 0

    def test_creation_with_error_log_nodes(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={})
        req_info = ErrorLogRequestInfo()
        node = ErrorLogNode(
            log_id="log-id-1",
            created_at=1700000000.0,
            severity="error",
            source="manager",
            user=None,
            is_read=False,
            message="Error 1",
            context=ctx,
            request=req_info,
        )
        payload = ListErrorLogsPayload(logs=[node], count=1)
        assert len(payload.logs) == 1
        assert payload.count == 1
        assert payload.logs[0].log_id == "log-id-1"

    def test_round_trip_with_multiple_logs(self) -> None:
        ctx = ErrorLogContextInfo(lang="python", env={})
        req_info = ErrorLogRequestInfo()
        nodes = [
            ErrorLogNode(
                log_id=f"log-id-{i}",
                created_at=1700000000.0 + i,
                severity="error",
                source="manager",
                user=None,
                is_read=False,
                message=f"Error {i}",
                context=ctx,
                request=req_info,
            )
            for i in range(3)
        ]
        payload = ListErrorLogsPayload(logs=nodes, count=3)
        json_str = payload.model_dump_json()
        restored = ListErrorLogsPayload.model_validate_json(json_str)
        assert len(restored.logs) == 3
        assert restored.count == 3
        assert restored.logs[0].log_id == "log-id-0"
        assert restored.logs[2].log_id == "log-id-2"


class TestClearErrorLogPayload:
    """Tests for ClearErrorLogPayload model."""

    def test_creation_with_success_true(self) -> None:
        payload = ClearErrorLogPayload(success=True)
        assert payload.success is True

    def test_creation_with_success_false(self) -> None:
        payload = ClearErrorLogPayload(success=False)
        assert payload.success is False

    def test_round_trip_serialization(self) -> None:
        payload = ClearErrorLogPayload(success=False)
        json_str = payload.model_dump_json()
        restored = ClearErrorLogPayload.model_validate_json(json_str)
        assert restored.success is False


class TestManagerNodeInfo:
    """Tests for ManagerNodeInfo model."""

    def test_creation_with_all_fields(self) -> None:
        node = ManagerNodeInfo(
            id="manager-01",
            num_proc=4,
            service_addr="0.0.0.0:8080",
            heartbeat_timeout=30.0,
            ssl_enabled=False,
            active_sessions=10,
            status="running",
            version="24.12.0",
            api_version=[9, "20250722"],
        )
        assert node.id == "manager-01"
        assert node.num_proc == 4
        assert node.service_addr == "0.0.0.0:8080"
        assert node.heartbeat_timeout == 30.0
        assert node.ssl_enabled is False
        assert node.active_sessions == 10
        assert node.status == "running"
        assert node.version == "24.12.0"
        assert node.api_version == [9, "20250722"]

    def test_ssl_enabled_true(self) -> None:
        node = ManagerNodeInfo(
            id="manager-02",
            num_proc=2,
            service_addr="0.0.0.0:8443",
            heartbeat_timeout=60.0,
            ssl_enabled=True,
            active_sessions=0,
            status="frozen",
            version="24.12.0",
            api_version=[9, "20250722"],
        )
        assert node.ssl_enabled is True

    def test_round_trip_serialization(self) -> None:
        node = ManagerNodeInfo(
            id="manager-01",
            num_proc=4,
            service_addr="127.0.0.1:8080",
            heartbeat_timeout=30.0,
            ssl_enabled=False,
            active_sessions=5,
            status="running",
            version="24.12.0",
            api_version=[9, "20250722"],
        )
        json_str = node.model_dump_json()
        restored = ManagerNodeInfo.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.num_proc == node.num_proc
        assert restored.service_addr == node.service_addr
        assert restored.heartbeat_timeout == node.heartbeat_timeout
        assert restored.ssl_enabled == node.ssl_enabled
        assert restored.active_sessions == node.active_sessions
        assert restored.status == node.status
        assert restored.version == node.version
        assert restored.api_version == node.api_version


class TestManagerStatusPayload:
    """Tests for ManagerStatusPayload model."""

    def test_creation_with_empty_nodes(self) -> None:
        payload = ManagerStatusPayload(nodes=[], status="running", active_sessions=0)
        assert payload.nodes == []
        assert payload.status == "running"
        assert payload.active_sessions == 0

    def test_creation_with_manager_nodes(self) -> None:
        node = ManagerNodeInfo(
            id="manager-01",
            num_proc=4,
            service_addr="0.0.0.0:8080",
            heartbeat_timeout=30.0,
            ssl_enabled=False,
            active_sessions=5,
            status="running",
            version="24.12.0",
            api_version=[9, "20250722"],
        )
        payload = ManagerStatusPayload(nodes=[node], status="running", active_sessions=5)
        assert len(payload.nodes) == 1
        assert payload.nodes[0].id == "manager-01"
        assert payload.active_sessions == 5

    def test_round_trip_serialization(self) -> None:
        node = ManagerNodeInfo(
            id="manager-01",
            num_proc=4,
            service_addr="0.0.0.0:8080",
            heartbeat_timeout=30.0,
            ssl_enabled=False,
            active_sessions=3,
            status="running",
            version="24.12.0",
            api_version=[9, "20250722"],
        )
        payload = ManagerStatusPayload(nodes=[node], status="running", active_sessions=3)
        json_str = payload.model_dump_json()
        restored = ManagerStatusPayload.model_validate_json(json_str)
        assert len(restored.nodes) == 1
        assert restored.nodes[0].id == "manager-01"
        assert restored.status == "running"
        assert restored.active_sessions == 3


class TestAnnouncementNode:
    """Tests for AnnouncementNode model."""

    def test_creation_with_enabled_true(self) -> None:
        node = AnnouncementNode(enabled=True, message="System maintenance tonight")
        assert node.enabled is True
        assert node.message == "System maintenance tonight"

    def test_creation_with_enabled_false(self) -> None:
        node = AnnouncementNode(enabled=False, message="")
        assert node.enabled is False
        assert node.message == ""

    def test_creation_with_empty_message(self) -> None:
        node = AnnouncementNode(enabled=False, message="")
        assert node.message == ""

    def test_round_trip_serialization(self) -> None:
        node = AnnouncementNode(enabled=True, message="Important announcement")
        json_str = node.model_dump_json()
        restored = AnnouncementNode.model_validate_json(json_str)
        assert restored.enabled is True
        assert restored.message == "Important announcement"

    def test_round_trip_disabled_announcement(self) -> None:
        node = AnnouncementNode(enabled=False, message="")
        json_str = node.model_dump_json()
        restored = AnnouncementNode.model_validate_json(json_str)
        assert restored.enabled is False
        assert restored.message == ""

    def test_model_dump(self) -> None:
        node = AnnouncementNode(enabled=True, message="Hello")
        data = node.model_dump()
        assert data["enabled"] is True
        assert data["message"] == "Hello"
