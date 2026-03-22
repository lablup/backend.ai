"""Tests for ai.backend.common.dto.manager.v2.compute_session.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.compute_session.response import (
    ComputeSessionNode,
    ContainerNode,
    GetComputeSessionDetailPayload,
    SearchComputeSessionsPayload,
)


def _make_container(status: str = "RUNNING") -> ContainerNode:
    return ContainerNode(
        id=uuid.uuid4(),
        agent_id="agent-1",
        status=status,
    )


def _make_compute_session(
    num_containers: int = 1,
) -> ComputeSessionNode:
    return ComputeSessionNode(
        id=uuid.uuid4(),
        name="test-session",
        type="interactive",
        status="RUNNING",
        created_at=datetime.now(tz=UTC),
        containers=[_make_container() for _ in range(num_containers)],
    )


class TestContainerNode:
    """Tests for ContainerNode model."""

    def test_creation_with_required_fields(self) -> None:
        container_id = uuid.uuid4()
        node = ContainerNode(id=container_id, status="RUNNING")
        assert node.id == container_id
        assert node.status == "RUNNING"
        assert node.agent_id is None
        assert node.resource_usage is None

    def test_creation_with_all_fields(self) -> None:
        container_id = uuid.uuid4()
        node = ContainerNode(
            id=container_id,
            agent_id="agent-abc",
            status="RUNNING",
            resource_usage={"cpu": "0.5", "mem": "1g"},
        )
        assert node.agent_id == "agent-abc"
        assert node.resource_usage == {"cpu": "0.5", "mem": "1g"}

    def test_round_trip(self) -> None:
        container_id = uuid.uuid4()
        node = ContainerNode(id=container_id, agent_id="agent-1", status="RUNNING")
        json_str = node.model_dump_json()
        restored = ContainerNode.model_validate_json(json_str)
        assert restored.id == container_id
        assert restored.agent_id == "agent-1"
        assert restored.status == "RUNNING"


class TestComputeSessionNode:
    """Tests for ComputeSessionNode model with containers."""

    def test_creation_with_required_fields(self) -> None:
        session_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = ComputeSessionNode(
            id=session_id,
            type="interactive",
            status="RUNNING",
            created_at=now,
        )
        assert node.id == session_id
        assert node.type == "interactive"
        assert node.status == "RUNNING"
        assert node.created_at == now
        assert node.containers == []

    def test_optional_fields_default(self) -> None:
        node = _make_compute_session(num_containers=0)
        assert node.name == "test-session"
        assert node.image is None
        assert node.scaling_group is None
        assert node.resource_slots is None
        assert node.occupied_slots is None
        assert node.terminated_at is None
        assert node.starts_at is None

    def test_with_containers(self) -> None:
        node = _make_compute_session(num_containers=2)
        assert len(node.containers) == 2
        for container in node.containers:
            assert container.status == "RUNNING"

    def test_with_all_fields(self) -> None:
        session_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        container = _make_container()
        node = ComputeSessionNode(
            id=session_id,
            name="full-session",
            type="batch",
            status="TERMINATED",
            image=["python:3.11", "cuda:12.0"],
            scaling_group="gpu-group",
            resource_slots={"cpu": "4", "mem": "16g"},
            occupied_slots={"cpu": "4", "mem": "16g"},
            created_at=now,
            terminated_at=now,
            starts_at=now,
            containers=[container],
        )
        assert node.name == "full-session"
        assert node.type == "batch"
        assert node.image == ["python:3.11", "cuda:12.0"]
        assert node.scaling_group == "gpu-group"
        assert len(node.containers) == 1

    def test_serializes_to_json_with_containers(self) -> None:
        node = _make_compute_session(num_containers=1)
        data = json.loads(node.model_dump_json())
        assert "containers" in data
        assert isinstance(data["containers"], list)
        assert len(data["containers"]) == 1
        assert "id" in data["containers"][0]
        assert "status" in data["containers"][0]

    def test_round_trip(self) -> None:
        node = _make_compute_session(num_containers=2)
        json_str = node.model_dump_json()
        restored = ComputeSessionNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.status == node.status
        assert len(restored.containers) == 2


class TestGetComputeSessionDetailPayload:
    """Tests for GetComputeSessionDetailPayload model."""

    def test_creation_with_session_node(self) -> None:
        node = _make_compute_session()
        payload = GetComputeSessionDetailPayload(session=node)
        assert payload.session.id == node.id
        assert payload.session.status == "RUNNING"

    def test_round_trip(self) -> None:
        node = _make_compute_session(num_containers=1)
        payload = GetComputeSessionDetailPayload(session=node)
        json_str = payload.model_dump_json()
        restored = GetComputeSessionDetailPayload.model_validate_json(json_str)
        assert restored.session.id == node.id
        assert len(restored.session.containers) == 1


class TestSearchComputeSessionsPayload:
    """Tests for SearchComputeSessionsPayload model."""

    def test_creation_with_empty_items(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=20)
        payload = SearchComputeSessionsPayload(items=[], pagination=pagination)
        assert payload.items == []
        assert payload.pagination.total == 0

    def test_creation_with_items(self) -> None:
        node = _make_compute_session()
        pagination = PaginationInfo(total=1, offset=0, limit=20)
        payload = SearchComputeSessionsPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1
        assert payload.items[0].id == node.id

    def test_nested_json_structure(self) -> None:
        node = _make_compute_session(num_containers=1)
        pagination = PaginationInfo(total=1, offset=0, limit=20)
        payload = SearchComputeSessionsPayload(items=[node], pagination=pagination)
        data = json.loads(payload.model_dump_json())
        assert "items" in data
        assert "pagination" in data
        assert isinstance(data["items"], list)
        assert "containers" in data["items"][0]

    def test_round_trip(self) -> None:
        nodes = [_make_compute_session(num_containers=1) for _ in range(3)]
        pagination = PaginationInfo(total=3, offset=0, limit=10)
        payload = SearchComputeSessionsPayload(items=nodes, pagination=pagination)
        json_str = payload.model_dump_json()
        restored = SearchComputeSessionsPayload.model_validate_json(json_str)
        assert len(restored.items) == 3
        assert restored.pagination.total == 3
