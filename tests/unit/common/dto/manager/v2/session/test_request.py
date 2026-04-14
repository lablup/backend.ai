"""Tests for ai.backend.common.dto.manager.v2.session.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.session.request import (
    CommitSessionInput,
    DestroySessionInput,
    DownloadFilesInput,
    EnqueueSessionInput,
    ExecuteInput,
    GetContainerLogsInput,
    ListFilesInput,
    RenameSessionInput,
    RestartSessionInput,
    SearchSessionsInput,
    SessionFilter,
    SessionOrder,
    SessionPathParam,
    ShutdownServiceInput,
    StartServiceInput,
    UploadFilesInput,
)
from ai.backend.common.dto.manager.v2.session.types import (
    CreateSessionTypeEnum,
    OrderDirection,
    SessionOrderField,
    SessionStatusEnum,
    SessionStatusFilter,
)


class TestSessionPathParam:
    """Tests for SessionPathParam model."""

    def test_valid_creation(self) -> None:
        param = SessionPathParam(session_name="my-session")
        assert param.session_name == "my-session"

    def test_round_trip(self) -> None:
        param = SessionPathParam(session_name="test-session")
        json_str = param.model_dump_json()
        restored = SessionPathParam.model_validate_json(json_str)
        assert restored.session_name == "test-session"

    def test_missing_session_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SessionPathParam.model_validate({})


class TestSessionFilter:
    """Tests for SessionFilter model."""

    def test_all_none_defaults(self) -> None:
        f = SessionFilter()
        assert f.id is None
        assert f.status is None
        assert f.name is None
        assert f.domain_name is None
        assert f.project_id is None
        assert f.user_uuid is None
        assert f.created_at is None

    def test_status_filter(self) -> None:
        status_filter = SessionStatusFilter(in_=[SessionStatusEnum.RUNNING])
        f = SessionFilter(status=status_filter)
        assert f.status is not None
        assert f.status.in_ == [SessionStatusEnum.RUNNING]


class TestSearchSessionsInput:
    """Tests for SearchSessionsInput model."""

    def test_defaults(self) -> None:
        inp = SearchSessionsInput()
        assert inp.filter is None
        assert inp.order is None
        assert inp.limit > 0
        assert inp.offset == 0

    def test_with_filter_and_order(self) -> None:
        status_filter = SessionStatusFilter(in_=[SessionStatusEnum.RUNNING])
        session_filter = SessionFilter(status=status_filter)
        order = SessionOrder(field=SessionOrderField.CREATED_AT, direction=OrderDirection.DESC)
        inp = SearchSessionsInput(filter=session_filter, order=order, limit=10, offset=0)
        assert inp.filter is not None
        assert inp.filter.status is not None
        assert inp.filter.status.in_ == [SessionStatusEnum.RUNNING]
        assert inp.order is not None
        assert inp.order.field == SessionOrderField.CREATED_AT
        assert inp.order.direction == OrderDirection.DESC
        assert inp.limit == 10

    def test_invalid_limit_zero_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchSessionsInput(limit=0)

    def test_invalid_offset_negative_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchSessionsInput(offset=-1)


class TestRestartSessionInput:
    """Tests for RestartSessionInput model."""

    def test_instantiable(self) -> None:
        RestartSessionInput()


class TestDestroySessionInput:
    """Tests for DestroySessionInput model."""

    def test_defaults(self) -> None:
        inp = DestroySessionInput()
        assert inp.forced is False
        assert inp.recursive is False

    def test_forced_true(self) -> None:
        inp = DestroySessionInput(forced=True)
        assert inp.forced is True
        assert inp.recursive is False

    def test_forced_and_recursive_true(self) -> None:
        inp = DestroySessionInput(forced=True, recursive=True)
        assert inp.forced is True
        assert inp.recursive is True

    def test_round_trip(self) -> None:
        inp = DestroySessionInput(forced=True, recursive=True)
        json_str = inp.model_dump_json()
        restored = DestroySessionInput.model_validate_json(json_str)
        assert restored.forced is True
        assert restored.recursive is True


class TestCommitSessionInput:
    """Tests for CommitSessionInput model."""

    def test_defaults(self) -> None:
        inp = CommitSessionInput()
        assert inp.login_session_token is None
        assert inp.filename is None

    def test_with_filename(self) -> None:
        inp = CommitSessionInput(filename="snapshot.tar")
        assert inp.filename == "snapshot.tar"

    def test_with_all_fields(self) -> None:
        inp = CommitSessionInput(login_session_token="token123", filename="snapshot.tar")
        assert inp.login_session_token == "token123"
        assert inp.filename == "snapshot.tar"

    def test_round_trip(self) -> None:
        inp = CommitSessionInput(filename="my-snapshot.tar.gz")
        json_str = inp.model_dump_json()
        restored = CommitSessionInput.model_validate_json(json_str)
        assert restored.filename == "my-snapshot.tar.gz"


class TestExecuteInput:
    """Tests for ExecuteInput model."""

    def test_all_none_defaults(self) -> None:
        inp = ExecuteInput()
        assert inp.mode is None
        assert inp.run_id is None
        assert inp.code is None
        assert inp.options is None

    def test_with_mode_and_code(self) -> None:
        inp = ExecuteInput(mode="query", code="print(1)")
        assert inp.mode == "query"
        assert inp.code == "print(1)"

    def test_with_all_fields(self) -> None:
        inp = ExecuteInput(
            mode="query",
            run_id="run-123",
            code="print(1)",
            options={"timeout": 30},
        )
        assert inp.mode == "query"
        assert inp.run_id == "run-123"
        assert inp.code == "print(1)"
        assert inp.options == {"timeout": 30}

    def test_round_trip(self) -> None:
        inp = ExecuteInput(mode="query", code="print('hello')")
        json_str = inp.model_dump_json()
        restored = ExecuteInput.model_validate_json(json_str)
        assert restored.mode == "query"
        assert restored.code == "print('hello')"


class TestStartServiceInput:
    """Tests for StartServiceInput model."""

    def test_valid_creation_with_app_only(self) -> None:
        inp = StartServiceInput(app="jupyter")
        assert inp.app == "jupyter"
        assert inp.port is None

    def test_valid_port_at_min(self) -> None:
        inp = StartServiceInput(app="jupyter", port=1024)
        assert inp.port == 1024

    def test_valid_port_at_max(self) -> None:
        inp = StartServiceInput(app="jupyter", port=65535)
        assert inp.port == 65535

    def test_port_below_1024_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            StartServiceInput(app="jupyter", port=80)

    def test_port_zero_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            StartServiceInput(app="jupyter", port=0)

    def test_port_above_65535_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            StartServiceInput(app="jupyter", port=65536)

    def test_with_all_fields(self) -> None:
        inp = StartServiceInput(
            app="tensorboard",
            port=6006,
            envs="KEY=VALUE",
            arguments="--logdir /logs",
            login_session_token="token123",
        )
        assert inp.app == "tensorboard"
        assert inp.port == 6006
        assert inp.envs == "KEY=VALUE"
        assert inp.arguments == "--logdir /logs"
        assert inp.login_session_token == "token123"


class TestShutdownServiceInput:
    """Tests for ShutdownServiceInput model."""

    def test_valid_creation(self) -> None:
        inp = ShutdownServiceInput(service_name="jupyter")
        assert inp.service_name == "jupyter"

    def test_missing_service_name_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            ShutdownServiceInput.model_validate({})


class TestRenameSessionInput:
    """Tests for RenameSessionInput model."""

    def test_valid_name(self) -> None:
        inp = RenameSessionInput(name="new-session-name")
        assert inp.name == "new-session-name"

    def test_whitespace_is_stripped(self) -> None:
        inp = RenameSessionInput(name="  my-session  ")
        assert inp.name == "my-session"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            RenameSessionInput(name="")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            RenameSessionInput(name="   ")

    def test_round_trip(self) -> None:
        inp = RenameSessionInput(name="my-session")
        json_str = inp.model_dump_json()
        restored = RenameSessionInput.model_validate_json(json_str)
        assert restored.name == "my-session"


class TestDownloadFilesInput:
    """Tests for DownloadFilesInput model."""

    def test_valid_creation(self) -> None:
        inp = DownloadFilesInput(files=["/path/to/file.txt", "/another/file.csv"])
        assert inp.files == ["/path/to/file.txt", "/another/file.csv"]

    def test_missing_files_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DownloadFilesInput.model_validate({})


class TestUploadFilesInput:
    """Tests for UploadFilesInput model."""

    def test_empty_body_creation(self) -> None:
        inp = UploadFilesInput()
        assert inp is not None


class TestListFilesInput:
    """Tests for ListFilesInput model."""

    def test_default_path(self) -> None:
        inp = ListFilesInput()
        assert inp.path == "."

    def test_custom_path(self) -> None:
        inp = ListFilesInput(path="/workspace/data")
        assert inp.path == "/workspace/data"


class TestGetContainerLogsInput:
    """Tests for GetContainerLogsInput model."""

    def test_all_none_defaults(self) -> None:
        inp = GetContainerLogsInput()
        assert inp.kernel_id is None

    def test_with_kernel_id(self) -> None:
        kernel_id = uuid.uuid4()
        inp = GetContainerLogsInput(kernel_id=kernel_id)
        assert inp.kernel_id == kernel_id


class TestEnqueueSessionInputOwnerDelegation:
    """Tests for owner_id delegation on EnqueueSessionInput."""

    def test_owner_id_defaults_to_none(self) -> None:
        """owner_id should be optional and default to None."""
        inp = EnqueueSessionInput(
            session_name="s",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid.uuid4(),
            resource_entries=[],
            project_id=uuid.uuid4(),
        )
        assert inp.owner_id is None

    def test_owner_id_accepts_uuid(self) -> None:
        owner = uuid.uuid4()
        inp = EnqueueSessionInput(
            session_name="s",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid.uuid4(),
            resource_entries=[],
            project_id=uuid.uuid4(),
            owner_id=owner,
        )
        assert inp.owner_id == owner

    def test_owner_id_round_trip(self) -> None:
        owner = uuid.uuid4()
        inp = EnqueueSessionInput(
            session_name="s",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid.uuid4(),
            resource_entries=[],
            project_id=uuid.uuid4(),
            owner_id=owner,
        )
        restored = EnqueueSessionInput.model_validate_json(inp.model_dump_json())
        assert restored.owner_id == owner
