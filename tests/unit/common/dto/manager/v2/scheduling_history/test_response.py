"""Tests for ai.backend.common.dto.manager.v2.scheduling_history.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    DeploymentHistoryNode,
    ListDeploymentHistoryPayload,
    ListRouteHistoryPayload,
    ListSessionHistoryPayload,
    RouteHistoryNode,
    SessionHistoryNode,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import SubStepResultInfo


def make_substep(step: str = "check", result: str = "success") -> SubStepResultInfo:
    now = datetime.now(tz=UTC)
    return SubStepResultInfo(
        step=step,
        result=result,
        error_code=None,
        message=None,
        started_at=now,
        ended_at=now,
    )


class TestSessionHistoryNodeCreation:
    """Tests for SessionHistoryNode model creation."""

    def test_creation_with_minimal_fields(self) -> None:
        now = datetime.now(tz=UTC)
        node = SessionHistoryNode(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            phase="scheduling",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        assert node.from_status is None
        assert node.to_status is None
        assert node.error_code is None
        assert node.message is None
        assert node.sub_steps == []

    def test_creation_with_all_fields(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        session_id = uuid.uuid4()
        sub_step = make_substep()
        node = SessionHistoryNode(
            id=record_id,
            session_id=session_id,
            phase="scaling",
            from_status="PENDING",
            to_status="RUNNING",
            result="SUCCESS",
            error_code=None,
            message="Scheduled successfully",
            sub_steps=[sub_step],
            attempts=2,
            created_at=now,
            updated_at=now,
        )
        assert node.id == record_id
        assert node.session_id == session_id
        assert node.phase == "scaling"
        assert node.from_status == "PENDING"
        assert node.to_status == "RUNNING"
        assert node.message == "Scheduled successfully"
        assert len(node.sub_steps) == 1

    def test_creation_with_error_fields(self) -> None:
        now = datetime.now(tz=UTC)
        node = SessionHistoryNode(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            phase="scheduling",
            result="FAILURE",
            error_code="ERR_RESOURCES",
            message="Not enough resources",
            attempts=3,
            created_at=now,
            updated_at=now,
        )
        assert node.result == "FAILURE"
        assert node.error_code == "ERR_RESOURCES"
        assert node.message == "Not enough resources"

    def test_nested_sub_steps(self) -> None:
        now = datetime.now(tz=UTC)
        sub_steps = [make_substep("step1"), make_substep("step2")]
        node = SessionHistoryNode(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            phase="scheduling",
            result="SUCCESS",
            sub_steps=sub_steps,
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        assert len(node.sub_steps) == 2
        assert node.sub_steps[0].step == "step1"
        assert node.sub_steps[1].step == "step2"

    def test_sub_steps_serialize_to_nested_json(self) -> None:
        now = datetime.now(tz=UTC)
        sub_step = make_substep("my_step", "success")
        node = SessionHistoryNode(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            phase="scheduling",
            result="SUCCESS",
            sub_steps=[sub_step],
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        data = json.loads(node.model_dump_json())
        assert isinstance(data["sub_steps"], list)
        assert len(data["sub_steps"]) == 1
        assert data["sub_steps"][0]["step"] == "my_step"

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        session_id = uuid.uuid4()
        node = SessionHistoryNode(
            id=record_id,
            session_id=session_id,
            phase="scheduling",
            result="SUCCESS",
            sub_steps=[make_substep()],
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        json_str = node.model_dump_json()
        restored = SessionHistoryNode.model_validate_json(json_str)
        assert restored.id == record_id
        assert restored.session_id == session_id
        assert restored.phase == "scheduling"
        assert len(restored.sub_steps) == 1


class TestDeploymentHistoryNodeCreation:
    """Tests for DeploymentHistoryNode model creation."""

    def test_creation_with_minimal_fields(self) -> None:
        now = datetime.now(tz=UTC)
        node = DeploymentHistoryNode(
            id=uuid.uuid4(),
            deployment_id=uuid.uuid4(),
            phase="scaling",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        assert node.sub_steps == []
        assert node.error_code is None

    def test_creation_with_sub_steps(self) -> None:
        now = datetime.now(tz=UTC)
        node = DeploymentHistoryNode(
            id=uuid.uuid4(),
            deployment_id=uuid.uuid4(),
            phase="scaling",
            result="FAILURE",
            sub_steps=[make_substep("check", "failure")],
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        assert len(node.sub_steps) == 1

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        dep_id = uuid.uuid4()
        node = DeploymentHistoryNode(
            id=record_id,
            deployment_id=dep_id,
            phase="scaling",
            result="SUCCESS",
            attempts=2,
            created_at=now,
            updated_at=now,
        )
        json_str = node.model_dump_json()
        restored = DeploymentHistoryNode.model_validate_json(json_str)
        assert restored.id == record_id
        assert restored.deployment_id == dep_id
        assert restored.attempts == 2


class TestRouteHistoryNodeCreation:
    """Tests for RouteHistoryNode model creation."""

    def test_creation_with_minimal_fields(self) -> None:
        now = datetime.now(tz=UTC)
        node = RouteHistoryNode(
            id=uuid.uuid4(),
            route_id=uuid.uuid4(),
            deployment_id=uuid.uuid4(),
            category="lifecycle",
            phase="routing",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        assert node.sub_steps == []
        assert node.from_status is None
        assert node.to_status is None
        assert node.category == "lifecycle"

    def test_route_and_deployment_ids_stored(self) -> None:
        now = datetime.now(tz=UTC)
        route_id = uuid.uuid4()
        dep_id = uuid.uuid4()
        node = RouteHistoryNode(
            id=uuid.uuid4(),
            route_id=route_id,
            deployment_id=dep_id,
            category="lifecycle",
            phase="routing",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        assert node.route_id == route_id
        assert node.deployment_id == dep_id

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        route_id = uuid.uuid4()
        dep_id = uuid.uuid4()
        node = RouteHistoryNode(
            id=record_id,
            route_id=route_id,
            deployment_id=dep_id,
            category="health",
            phase="routing",
            result="FAILURE",
            error_code="ERR_ROUTE",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        json_str = node.model_dump_json()
        restored = RouteHistoryNode.model_validate_json(json_str)
        assert restored.id == record_id
        assert restored.route_id == route_id
        assert restored.deployment_id == dep_id
        assert restored.error_code == "ERR_ROUTE"
        assert restored.category == "health"


class TestListSessionHistoryPayload:
    """Tests for ListSessionHistoryPayload model."""

    def test_creation_with_items(self) -> None:
        now = datetime.now(tz=UTC)
        node = SessionHistoryNode(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            phase="scheduling",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = ListSessionHistoryPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1
        assert payload.pagination.total == 1

    def test_empty_items(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=50)
        payload = ListSessionHistoryPayload(items=[], pagination=pagination)
        assert payload.items == []

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        node = SessionHistoryNode(
            id=record_id,
            session_id=uuid.uuid4(),
            phase="scheduling",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = ListSessionHistoryPayload(items=[node], pagination=pagination)
        json_str = payload.model_dump_json()
        restored = ListSessionHistoryPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == record_id
        assert restored.pagination.total == 1


class TestListDeploymentHistoryPayload:
    """Tests for ListDeploymentHistoryPayload model."""

    def test_creation_with_items(self) -> None:
        now = datetime.now(tz=UTC)
        node = DeploymentHistoryNode(
            id=uuid.uuid4(),
            deployment_id=uuid.uuid4(),
            phase="scaling",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = ListDeploymentHistoryPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        node = DeploymentHistoryNode(
            id=record_id,
            deployment_id=uuid.uuid4(),
            phase="scaling",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = ListDeploymentHistoryPayload(items=[node], pagination=pagination)
        json_str = payload.model_dump_json()
        restored = ListDeploymentHistoryPayload.model_validate_json(json_str)
        assert restored.items[0].id == record_id


class TestListRouteHistoryPayload:
    """Tests for ListRouteHistoryPayload model."""

    def test_creation_with_items(self) -> None:
        now = datetime.now(tz=UTC)
        node = RouteHistoryNode(
            id=uuid.uuid4(),
            route_id=uuid.uuid4(),
            deployment_id=uuid.uuid4(),
            category="lifecycle",
            phase="routing",
            result="SUCCESS",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = ListRouteHistoryPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        record_id = uuid.uuid4()
        route_id = uuid.uuid4()
        dep_id = uuid.uuid4()
        node = RouteHistoryNode(
            id=record_id,
            route_id=route_id,
            deployment_id=dep_id,
            category="lifecycle",
            phase="routing",
            result="STALE",
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = ListRouteHistoryPayload(items=[node], pagination=pagination)
        json_str = payload.model_dump_json()
        restored = ListRouteHistoryPayload.model_validate_json(json_str)
        assert restored.items[0].id == record_id
        assert restored.items[0].route_id == route_id
        assert restored.items[0].deployment_id == dep_id
