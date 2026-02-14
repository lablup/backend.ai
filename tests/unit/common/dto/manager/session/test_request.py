from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.defs.session import (
    SESSION_PRIORITY_DEFAULT,
    SESSION_PRIORITY_MAX,
    SESSION_PRIORITY_MIN,
)
from ai.backend.common.dto.manager.session.request import (
    CommitSessionRequest,
    CompleteRequest,
    ConvertSessionToImageRequest,
    CreateClusterRequest,
    CreateFromParamsRequest,
    CreateFromTemplateRequest,
    DestroySessionRequest,
    DownloadFilesRequest,
    DownloadSingleRequest,
    ExecuteRequest,
    GetAbusingReportRequest,
    GetCommitStatusRequest,
    GetContainerLogsRequest,
    GetStatusHistoryRequest,
    GetTaskLogsRequest,
    ListFilesRequest,
    MatchSessionsRequest,
    RenameSessionRequest,
    RestartSessionRequest,
    ShutdownServiceRequest,
    StartServiceRequest,
    SyncAgentRegistryRequest,
    TransitSessionStatusRequest,
)
from ai.backend.common.types import ClusterMode, SessionTypes


class TestCreateFromTemplateRequest:
    def test_minimal(self) -> None:
        req = CreateFromTemplateRequest.model_validate({
            "template_id": str(uuid4()),
        })
        assert req.priority == SESSION_PRIORITY_DEFAULT
        assert req.cluster_size == 1
        assert req.cluster_mode == ClusterMode.SINGLE_NODE
        assert req.enqueue_only is False
        assert req.reuse is True

    def test_camel_case_aliases(self) -> None:
        tid = uuid4()
        req = CreateFromTemplateRequest.model_validate({
            "templateId": str(tid),
            "clientSessionToken": "my-session",
            "sessionType": "batch",
            "clusterSize": 4,
            "clusterMode": "SINGLE_NODE",
            "enqueueOnly": True,
            "maxWaitSeconds": 30,
            "startsAt": "2025-01-01T00:00:00Z",
            "batchTimeout": "1h",
            "reuseIfExists": False,
            "startupCommand": "echo hello",
            "bootstrapScript": "#!/bin/bash",
            "callbackUrl": "https://example.com",
        })
        assert req.template_id == tid
        assert req.session_name == "my-session"
        assert req.session_type == SessionTypes.BATCH
        assert req.cluster_size == 4
        assert req.enqueue_only is True
        assert req.max_wait_seconds == 30
        assert req.reuse is False

    def test_priority_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CreateFromTemplateRequest.model_validate({
                "template_id": str(uuid4()),
                "priority": SESSION_PRIORITY_MIN - 1,
            })
        with pytest.raises(ValidationError):
            CreateFromTemplateRequest.model_validate({
                "template_id": str(uuid4()),
                "priority": SESSION_PRIORITY_MAX + 1,
            })

    def test_dependencies_with_uuid_strings(self) -> None:
        """UUID-formatted strings are accepted; they remain str because
        Pydantic matches ``str`` before ``UUID`` in the union.  The handler
        layer is responsible for coercing to UUID when needed."""
        dep_ids = [uuid4(), uuid4()]
        req = CreateFromTemplateRequest.model_validate({
            "template_id": str(uuid4()),
            "dependencies": [str(d) for d in dep_ids],
        })
        assert req.dependencies is not None
        assert len(req.dependencies) == 2

    def test_dependencies_with_plain_strings(self) -> None:
        req = CreateFromTemplateRequest.model_validate({
            "template_id": str(uuid4()),
            "dependencies": ["sess-a", "sess-b"],
        })
        assert req.dependencies == ["sess-a", "sess-b"]


class TestCreateFromParamsRequest:
    def test_required_fields(self) -> None:
        req = CreateFromParamsRequest.model_validate({
            "session_name": "test-sess",
            "image": "python:3.11",
        })
        assert req.session_name == "test-sess"
        assert req.image == "python:3.11"
        assert req.session_type == SessionTypes.INTERACTIVE
        assert req.group == "default"
        assert req.domain == "default"

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            CreateFromParamsRequest.model_validate({})

    def test_all_aliases(self) -> None:
        req = CreateFromParamsRequest.model_validate({
            "clientSessionToken": "my-sess",
            "lang": "python:3.11",
            "arch": "x86_64",
            "groupName": "mygroup",
            "domainName": "mydomain",
        })
        assert req.session_name == "my-sess"
        assert req.image == "python:3.11"
        assert req.architecture == "x86_64"
        assert req.group == "mygroup"
        assert req.domain == "mydomain"

    def test_dependencies_with_uuid_strings(self) -> None:
        """UUID-formatted strings are accepted; they remain str because
        Pydantic matches ``str`` before ``UUID`` in the union.  The handler
        layer is responsible for coercing to UUID when needed."""
        dep_ids = [uuid4(), uuid4()]
        req = CreateFromParamsRequest.model_validate({
            "session_name": "s",
            "image": "python:3.11",
            "dependencies": [str(d) for d in dep_ids],
        })
        assert req.dependencies is not None
        assert len(req.dependencies) == 2

    def test_dependencies_with_plain_strings(self) -> None:
        req = CreateFromParamsRequest.model_validate({
            "session_name": "s",
            "image": "python:3.11",
            "dependencies": ["session-name-a", "session-name-b"],
        })
        assert req.dependencies is not None
        assert req.dependencies == ["session-name-a", "session-name-b"]

    def test_dependencies_none(self) -> None:
        req = CreateFromParamsRequest.model_validate({
            "session_name": "s",
            "image": "python:3.11",
        })
        assert req.dependencies is None


class TestCreateClusterRequest:
    def test_minimal(self) -> None:
        tid = uuid4()
        req = CreateClusterRequest.model_validate({
            "clientSessionToken": "cluster-sess",
            "template_id": str(tid),
        })
        assert req.session_name == "cluster-sess"
        assert req.template_id == tid
        assert req.session_type == SessionTypes.INTERACTIVE
        assert req.group == "default"
        assert req.domain == "default"

    def test_scaling_group_alias(self) -> None:
        req = CreateClusterRequest.model_validate({
            "clientSessionToken": "cluster-sess",
            "templateId": str(uuid4()),
            "scalingGroup": "gpu-cluster",
        })
        assert req.scaling_group == "gpu-cluster"


class TestStartServiceRequest:
    def test_minimal(self) -> None:
        req = StartServiceRequest.model_validate({"app": "jupyter"})
        assert req.app == "jupyter"
        assert req.port is None
        assert req.login_session_token is None

    def test_service_alias(self) -> None:
        req = StartServiceRequest.model_validate({"service": "ttyd"})
        assert req.app == "ttyd"

    def test_port_range(self) -> None:
        req = StartServiceRequest.model_validate({"app": "x", "port": 8080})
        assert req.port == 8080
        with pytest.raises(ValidationError):
            StartServiceRequest.model_validate({"app": "x", "port": 80})
        with pytest.raises(ValidationError):
            StartServiceRequest.model_validate({"app": "x", "port": 70000})


class TestGetCommitStatusRequest:
    def test_defaults(self) -> None:
        req = GetCommitStatusRequest()
        assert req.login_session_token is None


class TestGetAbusingReportRequest:
    def test_defaults(self) -> None:
        req = GetAbusingReportRequest()
        assert req.login_session_token is None


class TestSyncAgentRegistryRequest:
    def test_required(self) -> None:
        req = SyncAgentRegistryRequest.model_validate({"agent": "agent-001"})
        assert req.agent == "agent-001"

    def test_missing(self) -> None:
        with pytest.raises(ValidationError):
            SyncAgentRegistryRequest.model_validate({})


class TestTransitSessionStatusRequest:
    def test_with_ids(self) -> None:
        ids = [uuid4(), uuid4()]
        req = TransitSessionStatusRequest.model_validate({
            "ids": [str(i) for i in ids],
        })
        assert req.ids == ids

    def test_session_ids_alias(self) -> None:
        sid = uuid4()
        req = TransitSessionStatusRequest.model_validate({
            "session_ids": [str(sid)],
        })
        assert req.ids == [sid]

    def test_camel_alias(self) -> None:
        sid = uuid4()
        req = TransitSessionStatusRequest.model_validate({
            "sessionIds": [str(sid)],
        })
        assert req.ids == [sid]


class TestCommitSessionRequest:
    def test_defaults(self) -> None:
        req = CommitSessionRequest()
        assert req.login_session_token is None
        assert req.filename is None

    def test_fname_alias(self) -> None:
        req = CommitSessionRequest.model_validate({"fname": "snapshot.tar"})
        assert req.filename == "snapshot.tar"


class TestConvertSessionToImageRequest:
    def test_valid(self) -> None:
        req = ConvertSessionToImageRequest.model_validate({
            "image_name": "my-image-v1",
        })
        assert req.image_name == "my-image-v1"
        assert req.image_visibility == CustomizedImageVisibilityScope.USER

    def test_invalid_image_name(self) -> None:
        with pytest.raises(ValidationError):
            ConvertSessionToImageRequest.model_validate({
                "image_name": "invalid name!",
            })


class TestRenameSessionRequest:
    def test_aliases(self) -> None:
        req = RenameSessionRequest.model_validate({"name": "new-name"})
        assert req.session_name == "new-name"

        req2 = RenameSessionRequest.model_validate({"clientSessionToken": "tok"})
        assert req2.session_name == "tok"


class TestDestroySessionRequest:
    def test_defaults(self) -> None:
        req = DestroySessionRequest()
        assert req.forced is False
        assert req.recursive is False
        assert req.owner_access_key is None


class TestRestartSessionRequest:
    def test_defaults(self) -> None:
        req = RestartSessionRequest()
        assert req.owner_access_key is None


class TestMatchSessionsRequest:
    def test_required(self) -> None:
        req = MatchSessionsRequest.model_validate({"id": "some-session"})
        assert req.id == "some-session"


class TestExecuteRequest:
    def test_defaults(self) -> None:
        req = ExecuteRequest()
        assert req.mode is None
        assert req.run_id is None
        assert req.code is None
        assert req.options is None

    def test_with_values(self) -> None:
        req = ExecuteRequest.model_validate({
            "mode": "query",
            "run_id": "run-001",
            "code": "print('hello')",
            "options": {"key": "val"},
        })
        assert req.mode == "query"
        assert req.code == "print('hello')"


class TestCompleteRequest:
    def test_defaults(self) -> None:
        req = CompleteRequest()
        assert req.code is None
        assert req.options is None


class TestShutdownServiceRequest:
    def test_required(self) -> None:
        req = ShutdownServiceRequest.model_validate({"service_name": "jupyter"})
        assert req.service_name == "jupyter"


class TestDownloadFilesRequest:
    def test_required(self) -> None:
        req = DownloadFilesRequest.model_validate({"files": ["a.txt", "b.txt"]})
        assert req.files == ["a.txt", "b.txt"]


class TestDownloadSingleRequest:
    def test_required(self) -> None:
        req = DownloadSingleRequest.model_validate({"file": "data.csv"})
        assert req.file == "data.csv"


class TestListFilesRequest:
    def test_default_path(self) -> None:
        req = ListFilesRequest()
        assert req.path == "."

    def test_custom_path(self) -> None:
        req = ListFilesRequest.model_validate({"path": "/home/work"})
        assert req.path == "/home/work"


class TestGetContainerLogsRequest:
    def test_defaults(self) -> None:
        req = GetContainerLogsRequest()
        assert req.owner_access_key is None
        assert req.kernel_id is None

    def test_aliases(self) -> None:
        kid = uuid4()
        req = GetContainerLogsRequest.model_validate({
            "ownerAccessKey": "AKIAEXAMPLE",
            "kernelId": str(kid),
        })
        assert req.owner_access_key == "AKIAEXAMPLE"
        assert req.kernel_id == kid


class TestGetTaskLogsRequest:
    def test_kernel_id(self) -> None:
        kid = uuid4()
        req = GetTaskLogsRequest.model_validate({"kernel_id": str(kid)})
        assert req.kernel_id == kid

    def test_session_name_alias(self) -> None:
        kid = uuid4()
        req = GetTaskLogsRequest.model_validate({"session_name": str(kid)})
        assert req.kernel_id == kid

    def test_task_id_alias(self) -> None:
        kid = uuid4()
        req = GetTaskLogsRequest.model_validate({"taskId": str(kid)})
        assert req.kernel_id == kid


class TestGetStatusHistoryRequest:
    def test_defaults(self) -> None:
        req = GetStatusHistoryRequest()
        assert req.owner_access_key is None
