"""Tests for ai.backend.common.dto.manager.v2.event_stream.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.event_stream.response import (
    BgtaskCancelledNode,
    BgtaskDoneNode,
    BgtaskFailedNode,
    BgtaskPartialSuccessNode,
    BgtaskUpdatedNode,
    SessionEventNode,
    SessionKernelEventNode,
)


class TestSessionEventNode:
    """Tests for SessionEventNode model creation and defaults."""

    def test_creation_with_all_defaults(self) -> None:
        node = SessionEventNode()
        assert node.reason == ""
        assert node.session_name == ""
        assert node.owner_access_key == ""
        assert node.session_id == ""
        assert node.exit_code is None

    def test_creation_with_explicit_values(self) -> None:
        node = SessionEventNode(
            reason="OOM",
            session_name="sess-1",
            owner_access_key="AKIAIOSFODNN7EXAMPLE",
            session_id="abc-123",
            exit_code=1,
        )
        assert node.reason == "OOM"
        assert node.session_name == "sess-1"
        assert node.owner_access_key == "AKIAIOSFODNN7EXAMPLE"
        assert node.session_id == "abc-123"
        assert node.exit_code == 1

    def test_exit_code_can_be_zero(self) -> None:
        node = SessionEventNode(exit_code=0)
        assert node.exit_code == 0

    def test_exit_code_none_by_default(self) -> None:
        node = SessionEventNode()
        assert node.exit_code is None

    def test_round_trip_serialization(self) -> None:
        node = SessionEventNode(
            reason="OOM",
            session_name="sess-1",
            owner_access_key="test-key",
            session_id="abc",
            exit_code=137,
        )
        json_str = node.model_dump_json()
        restored = SessionEventNode.model_validate_json(json_str)
        assert restored.reason == node.reason
        assert restored.session_name == node.session_name
        assert restored.owner_access_key == node.owner_access_key
        assert restored.session_id == node.session_id
        assert restored.exit_code == node.exit_code

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        node = SessionEventNode(session_name="test", owner_access_key="key")
        data = json.loads(node.model_dump_json())
        assert "session_name" in data
        assert "owner_access_key" in data
        assert "sessionName" not in data
        assert "ownerAccessKey" not in data


class TestSessionKernelEventNode:
    """Tests for SessionKernelEventNode inheriting from SessionEventNode."""

    def test_inherits_from_session_event_node(self) -> None:
        assert issubclass(SessionKernelEventNode, SessionEventNode)

    def test_creation_with_kernel_defaults(self) -> None:
        node = SessionKernelEventNode()
        assert node.kernel_id == ""
        assert node.cluster_role == "main"
        assert node.cluster_idx == 0

    def test_inherits_parent_defaults(self) -> None:
        node = SessionKernelEventNode()
        assert node.reason == ""
        assert node.session_name == ""
        assert node.owner_access_key == ""
        assert node.session_id == ""
        assert node.exit_code is None

    def test_creation_with_all_fields(self) -> None:
        node = SessionKernelEventNode(
            reason="OOM",
            session_name="sess-1",
            owner_access_key="test-key",
            session_id="abc",
            exit_code=1,
            kernel_id="kernel-123",
            cluster_role="sub",
            cluster_idx=2,
        )
        assert node.reason == "OOM"
        assert node.kernel_id == "kernel-123"
        assert node.cluster_role == "sub"
        assert node.cluster_idx == 2

    def test_round_trip_serialization(self) -> None:
        node = SessionKernelEventNode(
            session_name="sess-1",
            kernel_id="kernel-123",
            cluster_role="sub",
            cluster_idx=1,
        )
        json_str = node.model_dump_json()
        restored = SessionKernelEventNode.model_validate_json(json_str)
        assert restored.session_name == node.session_name
        assert restored.kernel_id == node.kernel_id
        assert restored.cluster_role == node.cluster_role
        assert restored.cluster_idx == node.cluster_idx


class TestBgtaskUpdatedNode:
    """Tests for BgtaskUpdatedNode model."""

    def test_creation_with_required_fields(self) -> None:
        node = BgtaskUpdatedNode(
            task_id="task-abc",
            message="Processing...",
            current_progress=50.0,
            total_progress=100.0,
        )
        assert node.task_id == "task-abc"
        assert node.message == "Processing..."
        assert node.current_progress == 50.0
        assert node.total_progress == 100.0

    def test_round_trip_serialization(self) -> None:
        node = BgtaskUpdatedNode(
            task_id="task-abc",
            message="Processing...",
            current_progress=25.0,
            total_progress=100.0,
        )
        json_str = node.model_dump_json()
        restored = BgtaskUpdatedNode.model_validate_json(json_str)
        assert restored.task_id == node.task_id
        assert restored.message == node.message
        assert restored.current_progress == node.current_progress
        assert restored.total_progress == node.total_progress

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        node = BgtaskUpdatedNode(task_id="t", message="m", current_progress=1.0, total_progress=2.0)
        data = json.loads(node.model_dump_json())
        assert "task_id" in data
        assert "current_progress" in data
        assert "total_progress" in data
        assert "currentProgress" not in data
        assert "totalProgress" not in data


class TestBgtaskDoneNode:
    """Tests for BgtaskDoneNode model."""

    def test_creation_with_required_fields(self) -> None:
        node = BgtaskDoneNode(task_id="task-abc", message="Completed")
        assert node.task_id == "task-abc"
        assert node.message == "Completed"

    def test_round_trip_serialization(self) -> None:
        node = BgtaskDoneNode(task_id="task-abc", message="Done!")
        json_str = node.model_dump_json()
        restored = BgtaskDoneNode.model_validate_json(json_str)
        assert restored.task_id == node.task_id
        assert restored.message == node.message


class TestBgtaskPartialSuccessNode:
    """Tests for BgtaskPartialSuccessNode model."""

    def test_creation_with_errors(self) -> None:
        node = BgtaskPartialSuccessNode(
            task_id="task-abc",
            message="Partial success",
            errors=["error 1", "error 2"],
        )
        assert node.task_id == "task-abc"
        assert node.message == "Partial success"
        assert len(node.errors) == 2
        assert node.errors[0] == "error 1"

    def test_creation_with_empty_errors(self) -> None:
        node = BgtaskPartialSuccessNode(task_id="t", message="m", errors=[])
        assert node.errors == []

    def test_round_trip_serialization(self) -> None:
        node = BgtaskPartialSuccessNode(
            task_id="task-abc",
            message="Partial",
            errors=["err1", "err2"],
        )
        json_str = node.model_dump_json()
        restored = BgtaskPartialSuccessNode.model_validate_json(json_str)
        assert restored.task_id == node.task_id
        assert restored.errors == node.errors


class TestBgtaskCancelledNode:
    """Tests for BgtaskCancelledNode model."""

    def test_creation_with_required_fields(self) -> None:
        node = BgtaskCancelledNode(task_id="task-abc", message="Cancelled by user")
        assert node.task_id == "task-abc"
        assert node.message == "Cancelled by user"

    def test_round_trip_serialization(self) -> None:
        node = BgtaskCancelledNode(task_id="task-abc", message="Cancelled")
        json_str = node.model_dump_json()
        restored = BgtaskCancelledNode.model_validate_json(json_str)
        assert restored.task_id == node.task_id
        assert restored.message == node.message


class TestBgtaskFailedNode:
    """Tests for BgtaskFailedNode model."""

    def test_creation_with_required_fields(self) -> None:
        node = BgtaskFailedNode(task_id="task-abc", message="Task failed")
        assert node.task_id == "task-abc"
        assert node.message == "Task failed"

    def test_round_trip_serialization(self) -> None:
        node = BgtaskFailedNode(task_id="task-abc", message="Failed")
        json_str = node.model_dump_json()
        restored = BgtaskFailedNode.model_validate_json(json_str)
        assert restored.task_id == node.task_id
        assert restored.message == node.message
