"""Tests for ai.backend.common.dto.manager.v2.event_stream.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.streaming.types import SessionEventScope
from ai.backend.common.dto.manager.v2.event_stream.request import (
    BackgroundTaskEventSubscribeInput,
    SessionEventSubscribeInput,
)


class TestSessionEventSubscribeInput:
    """Tests for SessionEventSubscribeInput model creation and validation."""

    def test_creation_with_defaults(self) -> None:
        req = SessionEventSubscribeInput()
        assert req.session_name == "*"
        assert req.owner_access_key is None
        assert req.session_id is None
        assert req.group_name == "*"
        assert req.scope == "*"

    def test_creation_with_explicit_session_name(self) -> None:
        req = SessionEventSubscribeInput(session_name="my-session")
        assert req.session_name == "my-session"

    def test_creation_with_owner_access_key(self) -> None:
        req = SessionEventSubscribeInput(owner_access_key="AKIAIOSFODNN7EXAMPLE")
        assert req.owner_access_key == "AKIAIOSFODNN7EXAMPLE"

    def test_creation_with_session_id(self) -> None:
        session_id = uuid.uuid4()
        req = SessionEventSubscribeInput(session_id=session_id)
        assert req.session_id == session_id

    def test_creation_with_group_name(self) -> None:
        req = SessionEventSubscribeInput(group_name="my-group")
        assert req.group_name == "my-group"

    def test_creation_with_scope_enum(self) -> None:
        req = SessionEventSubscribeInput(scope=SessionEventScope.SESSION)
        assert req.scope == SessionEventScope.SESSION

    def test_creation_with_scope_string(self) -> None:
        req = SessionEventSubscribeInput(scope="kernel")
        assert req.scope == "kernel"

    def test_creation_with_all_fields(self) -> None:
        session_id = uuid.uuid4()
        req = SessionEventSubscribeInput(
            session_name="test-session",
            owner_access_key="AKIAIOSFODNN7EXAMPLE",
            session_id=session_id,
            group_name="test-group",
            scope=SessionEventScope.KERNEL,
        )
        assert req.session_name == "test-session"
        assert req.owner_access_key == "AKIAIOSFODNN7EXAMPLE"
        assert req.session_id == session_id
        assert req.group_name == "test-group"
        assert req.scope == SessionEventScope.KERNEL

    def test_session_id_from_string(self) -> None:
        session_id = uuid.uuid4()
        req = SessionEventSubscribeInput.model_validate({"session_id": str(session_id)})
        assert req.session_id == session_id

    def test_session_id_is_uuid_instance_when_set(self) -> None:
        session_id = uuid.uuid4()
        req = SessionEventSubscribeInput(session_id=session_id)
        assert isinstance(req.session_id, uuid.UUID)

    def test_round_trip_serialization_with_defaults(self) -> None:
        req = SessionEventSubscribeInput()
        json_data = req.model_dump_json()
        restored = SessionEventSubscribeInput.model_validate_json(json_data)
        assert restored.session_name == req.session_name
        assert restored.owner_access_key is None
        assert restored.session_id is None
        assert restored.group_name == req.group_name

    def test_round_trip_serialization_with_all_fields(self) -> None:
        session_id = uuid.uuid4()
        req = SessionEventSubscribeInput(
            session_name="my-session",
            owner_access_key="AKIAIOSFODNN7EXAMPLE",
            session_id=session_id,
            group_name="my-group",
            scope=SessionEventScope.SESSION,
        )
        json_data = req.model_dump_json()
        restored = SessionEventSubscribeInput.model_validate_json(json_data)
        assert restored.session_name == req.session_name
        assert restored.owner_access_key == req.owner_access_key
        assert restored.session_id == req.session_id
        assert restored.group_name == req.group_name
        assert restored.scope == req.scope


class TestBackgroundTaskEventSubscribeInput:
    """Tests for BackgroundTaskEventSubscribeInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        task_id = uuid.uuid4()
        req = BackgroundTaskEventSubscribeInput(task_id=task_id)
        assert req.task_id == task_id

    def test_valid_creation_from_uuid_string(self) -> None:
        task_id = uuid.uuid4()
        req = BackgroundTaskEventSubscribeInput.model_validate({"task_id": str(task_id)})
        assert req.task_id == task_id

    def test_invalid_uuid_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            BackgroundTaskEventSubscribeInput.model_validate({"task_id": "not-a-uuid"})

    def test_missing_task_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            BackgroundTaskEventSubscribeInput.model_validate({})

    def test_task_id_is_uuid_instance(self) -> None:
        task_id = uuid.uuid4()
        req = BackgroundTaskEventSubscribeInput(task_id=task_id)
        assert isinstance(req.task_id, uuid.UUID)

    def test_round_trip_serialization(self) -> None:
        task_id = uuid.uuid4()
        req = BackgroundTaskEventSubscribeInput(task_id=task_id)
        json_data = req.model_dump_json()
        restored = BackgroundTaskEventSubscribeInput.model_validate_json(json_data)
        assert restored.task_id == req.task_id
