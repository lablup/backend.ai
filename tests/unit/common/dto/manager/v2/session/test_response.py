"""Tests for ai.backend.common.dto.manager.v2.session.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.session.response import (
    CommitSessionPayload,
    DestroySessionPayload,
    ExecutePayload,
    RestartSessionPayload,
    SearchSessionsPayload,
    SessionLifecycleInfo,
    SessionLifecycleInfoGQLDTO,
    SessionMetadataInfo,
    SessionMetadataInfoGQLDTO,
    SessionNetworkInfo,
    SessionNode,
    SessionResourceInfo,
    SessionResourceInfoGQLDTO,
    SessionRuntimeInfo,
    SessionRuntimeInfoGQLDTO,
    StartServicePayload,
)


def _make_metadata(
    session_type: str = "interactive",
    cluster_mode: str = "single-node",
    cluster_size: int = 1,
    priority: int = 0,
    is_preemptible: bool = False,
) -> SessionMetadataInfo:
    return SessionMetadataInfo(
        session_type=session_type,
        cluster_mode=cluster_mode,
        cluster_size=cluster_size,
        priority=priority,
        is_preemptible=is_preemptible,
    )


def _make_metadata_gql_dto(
    session_type: str = "interactive",
    cluster_mode: str = "single-node",
    cluster_size: int = 1,
    priority: int = 0,
    is_preemptible: bool = False,
) -> SessionMetadataInfoGQLDTO:
    return SessionMetadataInfoGQLDTO(
        session_type=session_type,
        cluster_mode=cluster_mode,
        cluster_size=cluster_size,
        priority=priority,
        is_preemptible=is_preemptible,
    )


def _make_resource() -> SessionResourceInfo:
    return SessionResourceInfo()


def _make_resource_gql_dto() -> SessionResourceInfoGQLDTO:
    return SessionResourceInfoGQLDTO(allocation=None)


def _make_lifecycle(status: str = "RUNNING", result: str = "undefined") -> SessionLifecycleInfo:
    return SessionLifecycleInfo(status=status, result=result)


def _make_lifecycle_gql_dto(
    status: str = "RUNNING", result: str = "undefined"
) -> SessionLifecycleInfoGQLDTO:
    return SessionLifecycleInfoGQLDTO(status=status, result=result)


def _make_runtime() -> SessionRuntimeInfo:
    return SessionRuntimeInfo()


def _make_runtime_gql_dto() -> SessionRuntimeInfoGQLDTO:
    return SessionRuntimeInfoGQLDTO()


def _make_network(use_host_network: bool = False) -> SessionNetworkInfo:
    return SessionNetworkInfo(use_host_network=use_host_network)


def _make_session_node() -> SessionNode:
    return SessionNode(
        id=uuid.uuid4(),
        domain_name="default",
        user_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        metadata=_make_metadata_gql_dto(),
        resource=_make_resource_gql_dto(),
        lifecycle=_make_lifecycle_gql_dto(),
        runtime=_make_runtime_gql_dto(),
        network=_make_network(),
    )


class TestSessionMetadataInfo:
    """Tests for SessionMetadataInfo model."""

    def test_creation_with_required_fields(self) -> None:
        info = SessionMetadataInfo(
            session_type="interactive",
            cluster_mode="single-node",
            cluster_size=1,
            priority=0,
            is_preemptible=False,
        )
        assert info.session_type == "interactive"
        assert info.cluster_mode == "single-node"
        assert info.cluster_size == 1
        assert info.priority == 0
        assert info.is_preemptible is False

    def test_optional_fields_default_none(self) -> None:
        info = _make_metadata()
        assert info.creation_id is None
        assert info.name is None
        assert info.access_key is None
        assert info.tag is None

    def test_creation_with_all_fields(self) -> None:
        info = SessionMetadataInfo(
            creation_id="create-id-123",
            name="my-session",
            session_type="batch",
            access_key="AKIAIOSFODNN7EXAMPLE",
            cluster_mode="multi-node",
            cluster_size=4,
            priority=5,
            is_preemptible=True,
            tag="experiment-1",
        )
        assert info.creation_id == "create-id-123"
        assert info.name == "my-session"
        assert info.session_type == "batch"
        assert info.access_key == "AKIAIOSFODNN7EXAMPLE"
        assert info.cluster_size == 4
        assert info.priority == 5
        assert info.is_preemptible is True
        assert info.tag == "experiment-1"

    def test_round_trip(self) -> None:
        info = _make_metadata(session_type="batch", priority=3)
        json_str = info.model_dump_json()
        restored = SessionMetadataInfo.model_validate_json(json_str)
        assert restored.session_type == "batch"
        assert restored.priority == 3


class TestSessionResourceInfo:
    """Tests for SessionResourceInfo model."""

    def test_all_none_defaults(self) -> None:
        info = SessionResourceInfo()
        assert info.occupying_slots is None
        assert info.requested_slots is None
        assert info.scaling_group_name is None
        assert info.target_sgroup_names is None
        assert info.agent_ids is None
        assert info.images is None

    def test_with_slots(self) -> None:
        info = SessionResourceInfo(
            occupying_slots={"cpu": "2", "mem": "4g"},
            requested_slots={"cpu": "4", "mem": "8g"},
        )
        assert info.occupying_slots == {"cpu": "2", "mem": "4g"}
        assert info.requested_slots == {"cpu": "4", "mem": "8g"}

    def test_with_agents_and_images(self) -> None:
        info = SessionResourceInfo(
            agent_ids=["agent-1", "agent-2"],
            images=["python:3.11", "cuda:12.0"],
        )
        assert info.agent_ids == ["agent-1", "agent-2"]
        assert info.images == ["python:3.11", "cuda:12.0"]

    def test_round_trip(self) -> None:
        info = SessionResourceInfo(scaling_group_name="gpu-group")
        json_str = info.model_dump_json()
        restored = SessionResourceInfo.model_validate_json(json_str)
        assert restored.scaling_group_name == "gpu-group"


class TestSessionLifecycleInfo:
    """Tests for SessionLifecycleInfo model."""

    def test_creation_with_required_fields(self) -> None:
        info = SessionLifecycleInfo(status="RUNNING", result="undefined")
        assert info.status == "RUNNING"
        assert info.result == "undefined"

    def test_optional_fields_default_none(self) -> None:
        info = _make_lifecycle()
        assert info.created_at is None
        assert info.terminated_at is None
        assert info.starts_at is None
        assert info.batch_timeout is None
        assert info.status_info is None

    def test_with_timestamps(self) -> None:
        now = datetime.now(tz=UTC)
        info = SessionLifecycleInfo(
            status="TERMINATED",
            result="success",
            created_at=now,
            terminated_at=now,
        )
        assert info.created_at == now
        assert info.terminated_at == now

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = SessionLifecycleInfo(
            status="RUNNING",
            result="undefined",
            created_at=now,
        )
        json_str = info.model_dump_json()
        restored = SessionLifecycleInfo.model_validate_json(json_str)
        assert restored.status == "RUNNING"
        assert restored.created_at is not None


class TestSessionRuntimeInfo:
    """Tests for SessionRuntimeInfo model."""

    def test_all_none_defaults(self) -> None:
        info = SessionRuntimeInfo()
        assert info.environ is None
        assert info.bootstrap_script is None
        assert info.startup_command is None
        assert info.callback_url is None

    def test_with_environ(self) -> None:
        info = SessionRuntimeInfo(environ={"MY_VAR": "value"})
        assert info.environ == {"MY_VAR": "value"}

    def test_with_all_fields(self) -> None:
        info = SessionRuntimeInfo(
            environ={"KEY": "VAL"},
            bootstrap_script="#!/bin/bash\necho hello",
            startup_command="python main.py",
            callback_url="https://example.com/callback",
        )
        assert info.environ == {"KEY": "VAL"}
        assert info.bootstrap_script == "#!/bin/bash\necho hello"
        assert info.startup_command == "python main.py"
        assert info.callback_url == "https://example.com/callback"

    def test_round_trip(self) -> None:
        info = SessionRuntimeInfo(startup_command="python train.py")
        json_str = info.model_dump_json()
        restored = SessionRuntimeInfo.model_validate_json(json_str)
        assert restored.startup_command == "python train.py"


class TestSessionNetworkInfo:
    """Tests for SessionNetworkInfo model."""

    def test_creation_with_required_field(self) -> None:
        info = SessionNetworkInfo(use_host_network=False)
        assert info.use_host_network is False

    def test_host_network_true(self) -> None:
        info = SessionNetworkInfo(use_host_network=True)
        assert info.use_host_network is True

    def test_optional_fields_default_none(self) -> None:
        info = _make_network()
        assert info.network_type is None
        assert info.network_id is None

    def test_with_all_fields(self) -> None:
        info = SessionNetworkInfo(
            use_host_network=False,
            network_type="overlay",
            network_id="net-abc123",
        )
        assert info.network_type == "overlay"
        assert info.network_id == "net-abc123"

    def test_round_trip(self) -> None:
        info = SessionNetworkInfo(use_host_network=True, network_type="host")
        json_str = info.model_dump_json()
        restored = SessionNetworkInfo.model_validate_json(json_str)
        assert restored.use_host_network is True
        assert restored.network_type == "host"


class TestSessionNode:
    """Tests for SessionNode model with all nested sub-models."""

    def test_creation_with_all_nested(self) -> None:
        session_id = uuid.uuid4()
        node = SessionNode(
            id=session_id,
            domain_name="default",
            user_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            metadata=_make_metadata_gql_dto(),
            resource=_make_resource_gql_dto(),
            lifecycle=_make_lifecycle_gql_dto(),
            runtime=_make_runtime_gql_dto(),
            network=_make_network(),
        )
        assert node.id == session_id
        assert node.metadata is not None
        assert node.resource is not None
        assert node.lifecycle is not None
        assert node.runtime is not None
        assert node.network is not None

    def test_nested_values_accessible(self) -> None:
        node = _make_session_node()
        assert node.metadata.session_type == "interactive"
        assert node.lifecycle.status == "RUNNING"
        assert node.network.use_host_network is False

    def test_serializes_to_json(self) -> None:
        node = _make_session_node()
        data = json.loads(node.model_dump_json())
        assert "id" in data
        assert "metadata" in data
        assert "resource" in data
        assert "lifecycle" in data
        assert "runtime" in data
        assert "network" in data

    def test_nested_structure_in_json(self) -> None:
        node = _make_session_node()
        data = json.loads(node.model_dump_json())
        assert isinstance(data["metadata"], dict)
        assert "session_type" in data["metadata"]
        assert isinstance(data["lifecycle"], dict)
        assert "status" in data["lifecycle"]

    def test_round_trip(self) -> None:
        node = _make_session_node()
        json_str = node.model_dump_json()
        restored = SessionNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.metadata.session_type == node.metadata.session_type
        assert restored.lifecycle.status == node.lifecycle.status
        assert restored.network.use_host_network == node.network.use_host_network


class TestRestartSessionPayload:
    """Tests for RestartSessionPayload model."""

    def test_empty_payload_creation(self) -> None:
        payload = RestartSessionPayload()
        assert payload is not None

    def test_round_trip(self) -> None:
        payload = RestartSessionPayload()
        json_str = payload.model_dump_json()
        restored = RestartSessionPayload.model_validate_json(json_str)
        assert restored is not None


class TestDestroySessionPayload:
    """Tests for DestroySessionPayload model."""

    def test_creation_with_result(self) -> None:
        payload = DestroySessionPayload(result={"status": "destroyed"})
        assert payload.result == {"status": "destroyed"}

    def test_round_trip(self) -> None:
        payload = DestroySessionPayload(result={"task_id": "abc123", "status": "ok"})
        json_str = payload.model_dump_json()
        restored = DestroySessionPayload.model_validate_json(json_str)
        assert restored.result == {"task_id": "abc123", "status": "ok"}


class TestCommitSessionPayload:
    """Tests for CommitSessionPayload model."""

    def test_creation_with_result(self) -> None:
        payload = CommitSessionPayload(result={"image": "my-image:latest"})
        assert payload.result == {"image": "my-image:latest"}

    def test_round_trip(self) -> None:
        payload = CommitSessionPayload(result={"image": "test-image:v1", "digest": "sha256:abc"})
        json_str = payload.model_dump_json()
        restored = CommitSessionPayload.model_validate_json(json_str)
        assert restored.result["image"] == "test-image:v1"


class TestExecutePayload:
    """Tests for ExecutePayload model."""

    def test_creation_with_result(self) -> None:
        payload = ExecutePayload(result={"stdout": "hello\n", "exit_code": 0})
        assert payload.result["stdout"] == "hello\n"
        assert payload.result["exit_code"] == 0

    def test_round_trip(self) -> None:
        payload = ExecutePayload(result={"stdout": "output"})
        json_str = payload.model_dump_json()
        restored = ExecutePayload.model_validate_json(json_str)
        assert restored.result["stdout"] == "output"


class TestStartServicePayload:
    """Tests for StartServicePayload model."""

    def test_creation_with_required_fields(self) -> None:
        payload = StartServicePayload(
            token="auth-token-xyz",
            wsproxy_addr="wss://proxy.example.com:8080",
        )
        assert payload.token == "auth-token-xyz"
        assert payload.wsproxy_addr == "wss://proxy.example.com:8080"

    def test_round_trip(self) -> None:
        payload = StartServicePayload(
            token="my-token",
            wsproxy_addr="wss://localhost:9090",
        )
        json_str = payload.model_dump_json()
        restored = StartServicePayload.model_validate_json(json_str)
        assert restored.token == "my-token"
        assert restored.wsproxy_addr == "wss://localhost:9090"


class TestSearchSessionsPayload:
    """Tests for SearchSessionsPayload model."""

    def test_creation_with_empty_items(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=20)
        payload = SearchSessionsPayload(items=[], pagination=pagination)
        assert payload.items == []
        assert payload.pagination.total == 0

    def test_creation_with_items(self) -> None:
        node = _make_session_node()
        pagination = PaginationInfo(total=1, offset=0, limit=20)
        payload = SearchSessionsPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1
        assert payload.items[0].id == node.id

    def test_nested_json_serialization(self) -> None:
        node = _make_session_node()
        pagination = PaginationInfo(total=1, offset=0, limit=20)
        payload = SearchSessionsPayload(items=[node], pagination=pagination)
        data = json.loads(payload.model_dump_json())
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        assert "metadata" in data["items"][0]
        assert "pagination" in data

    def test_round_trip(self) -> None:
        node = _make_session_node()
        pagination = PaginationInfo(total=5, offset=0, limit=10)
        payload = SearchSessionsPayload(items=[node], pagination=pagination)
        json_str = payload.model_dump_json()
        restored = SearchSessionsPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == node.id
        assert restored.pagination.total == 5
        assert restored.pagination.limit == 10
