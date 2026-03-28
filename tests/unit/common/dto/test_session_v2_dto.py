"""Unit tests for v2 session DTOs."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.request import (
    BatchConfigInput,
    EnqueueSessionInput,
    GetSessionLogsQuery,
    MountItemInput,
    ResourceOptsInput,
    ShutdownSessionServiceInput,
    StartSessionServiceInput,
    TerminateSessionsInput,
    UpdateSessionInput,
)
from ai.backend.common.dto.manager.v2.session.types import (
    ClusterModeEnum,
    CreateSessionTypeEnum,
)


class TestEnqueueSessionInput:
    """Tests for EnqueueSessionInput creation DTO."""

    def test_valid_interactive_session(self) -> None:
        """Valid interactive session with minimal required fields."""
        result = EnqueueSessionInput(
            session_name="test-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[
                ResourceSlotEntryInput(resource_type="cpu", quantity="1"),
                ResourceSlotEntryInput(resource_type="mem", quantity="1g"),
            ],
            project_id=uuid4(),
        )
        assert result.session_name == "test-session"
        assert result.session_type == CreateSessionTypeEnum.INTERACTIVE
        assert result.cluster_size == 1
        assert result.cluster_mode == ClusterModeEnum.SINGLE_NODE
        assert result.priority == 10
        assert result.is_preemptible is True
        assert result.batch is None

    def test_valid_batch_session(self) -> None:
        """Valid batch session with batch config."""
        result = EnqueueSessionInput(
            session_name="batch-job",
            session_type=CreateSessionTypeEnum.BATCH,
            image_id=uuid4(),
            resource_entries=[
                ResourceSlotEntryInput(resource_type="cpu", quantity="2"),
                ResourceSlotEntryInput(resource_type="mem", quantity="4g"),
            ],
            project_id=uuid4(),
            batch=BatchConfigInput(
                startup_command="python train.py",
                batch_timeout=3600,
            ),
        )
        assert result.batch is not None
        assert result.batch.startup_command == "python train.py"
        assert result.batch.batch_timeout == 3600

    def test_session_name_too_long(self) -> None:
        """Session name exceeding max_length should fail."""
        with pytest.raises(ValidationError):
            EnqueueSessionInput(
                session_name="x" * 65,
                session_type=CreateSessionTypeEnum.INTERACTIVE,
                image_id=uuid4(),
                resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                project_id=uuid4(),
            )

    def test_empty_session_name(self) -> None:
        """Empty session name should fail."""
        with pytest.raises(ValidationError):
            EnqueueSessionInput(
                session_name="",
                session_type=CreateSessionTypeEnum.INTERACTIVE,
                image_id=uuid4(),
                resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                project_id=uuid4(),
            )

    def test_cluster_size_zero(self) -> None:
        """Cluster size 0 should fail."""
        with pytest.raises(ValidationError):
            EnqueueSessionInput(
                session_name="test",
                session_type=CreateSessionTypeEnum.INTERACTIVE,
                image_id=uuid4(),
                resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                project_id=uuid4(),
                cluster_size=0,
            )

    def test_priority_out_of_range(self) -> None:
        """Priority > 100 should fail."""
        with pytest.raises(ValidationError):
            EnqueueSessionInput(
                session_name="test",
                session_type=CreateSessionTypeEnum.INTERACTIVE,
                image_id=uuid4(),
                resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                project_id=uuid4(),
                priority=101,
            )

    def test_with_mounts(self) -> None:
        """Session with virtual folder mounts."""
        vfolder_id = uuid4()
        result = EnqueueSessionInput(
            session_name="mounted-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            project_id=uuid4(),
            mounts=[
                MountItemInput(vfolder_id=vfolder_id, mount_path="/data", permission="ro"),
            ],
        )
        assert result.mounts is not None
        assert len(result.mounts) == 1
        assert result.mounts[0].vfolder_id == vfolder_id
        assert result.mounts[0].permission == "ro"

    def test_with_resource_opts(self) -> None:
        """Session with resource options."""
        result = EnqueueSessionInput(
            session_name="shmem-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            project_id=uuid4(),
            resource_opts=ResourceOptsInput(shmem="2g"),
        )
        assert result.resource_opts is not None
        assert result.resource_opts.shmem == "2g"

    def test_project_id_required(self) -> None:
        """project_id is required."""
        with pytest.raises(ValidationError):
            EnqueueSessionInput.model_validate({
                "session_name": "test",
                "session_type": "interactive",
                "image_id": str(uuid4()),
                "resource_entries": [ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            })

    def test_multi_node_cluster(self) -> None:
        """Multi-node cluster configuration."""
        result = EnqueueSessionInput(
            session_name="cluster-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            project_id=uuid4(),
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            cluster_size=4,
        )
        assert result.cluster_mode == ClusterModeEnum.MULTI_NODE
        assert result.cluster_size == 4


class TestBatchConfigInput:
    """Tests for BatchConfigInput model."""

    def test_valid_batch_config(self) -> None:
        config = BatchConfigInput(
            startup_command="python train.py",
            starts_at="2026-04-01T00:00:00Z",
            batch_timeout=7200,
        )
        assert config.startup_command == "python train.py"
        assert config.batch_timeout == 7200

    def test_empty_startup_command(self) -> None:
        with pytest.raises(ValidationError):
            BatchConfigInput(startup_command="")

    def test_negative_timeout(self) -> None:
        with pytest.raises(ValidationError):
            BatchConfigInput(startup_command="echo hi", batch_timeout=-1)

    def test_optional_fields_default_none(self) -> None:
        config = BatchConfigInput(startup_command="echo hi")
        assert config.starts_at is None
        assert config.batch_timeout is None


class TestTerminateSessionsInput:
    """Tests for TerminateSessionsInput model."""

    def test_valid_terminate(self) -> None:
        ids = [uuid4(), uuid4()]
        result = TerminateSessionsInput(session_ids=ids, forced=True)
        assert len(result.session_ids) == 2
        assert result.forced is True

    def test_default_not_forced(self) -> None:
        result = TerminateSessionsInput(session_ids=[uuid4()])
        assert result.forced is False

    def test_empty_session_ids(self) -> None:
        """Empty list is valid (results in no-op)."""
        result = TerminateSessionsInput(session_ids=[])
        assert len(result.session_ids) == 0


class TestStartSessionServiceInput:
    """Tests for StartSessionServiceInput model."""

    def test_valid_minimal(self) -> None:
        result = StartSessionServiceInput(service="jupyter")
        assert result.service == "jupyter"
        assert result.port is None
        assert result.envs is None
        assert result.arguments is None

    def test_with_all_fields(self) -> None:
        result = StartSessionServiceInput(
            service="tensorboard",
            port=6006,
            envs={"CUDA_VISIBLE_DEVICES": "0"},
            arguments={"--logdir": "/logs"},
            login_session_token="abc123",
        )
        assert result.port == 6006
        assert result.envs == {"CUDA_VISIBLE_DEVICES": "0"}
        assert result.arguments == {"--logdir": "/logs"}

    def test_port_below_range(self) -> None:
        with pytest.raises(ValidationError):
            StartSessionServiceInput(service="jupyter", port=80)

    def test_port_above_range(self) -> None:
        with pytest.raises(ValidationError):
            StartSessionServiceInput(service="jupyter", port=70000)


class TestShutdownSessionServiceInput:
    """Tests for ShutdownSessionServiceInput model."""

    def test_valid(self) -> None:
        result = ShutdownSessionServiceInput(service="tensorboard")
        assert result.service == "tensorboard"


class TestUpdateSessionInput:
    """Tests for UpdateSessionInput model."""

    def test_name_only(self) -> None:
        result = UpdateSessionInput(name="new-name")
        assert result.name == "new-name"
        assert result.tag is None

    def test_tag_only(self) -> None:
        result = UpdateSessionInput(tag="experiment-1")
        assert result.tag == "experiment-1"

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UpdateSessionInput(name="x" * 65)

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            UpdateSessionInput(name="")

    def test_both_none(self) -> None:
        """Both None is valid (no-op update)."""
        result = UpdateSessionInput()
        assert result.name is None
        assert result.tag is None


class TestGetSessionLogsQuery:
    """Tests for GetSessionLogsQuery model."""

    def test_default_no_kernel(self) -> None:
        query = GetSessionLogsQuery()
        assert query.kernel_id is None

    def test_with_kernel_id(self) -> None:
        kid = uuid4()
        query = GetSessionLogsQuery(kernel_id=kid)
        assert query.kernel_id == kid


class TestCreateSessionTypeEnum:
    """Tests for CreateSessionTypeEnum values."""

    def test_only_interactive_and_batch(self) -> None:
        assert CreateSessionTypeEnum.INTERACTIVE.value == "interactive"
        assert CreateSessionTypeEnum.BATCH.value == "batch"
        assert len(CreateSessionTypeEnum) == 2


class TestClusterModeEnum:
    """Tests for ClusterModeEnum values."""

    def test_values(self) -> None:
        assert ClusterModeEnum.SINGLE_NODE.value == "single-node"
        assert ClusterModeEnum.MULTI_NODE.value == "multi-node"


class TestMountItemInput:
    """Tests for MountItemInput model."""

    def test_valid_mount(self) -> None:
        vfolder_id = uuid4()
        result = MountItemInput(vfolder_id=vfolder_id, mount_path="/data", permission="rw")
        assert result.vfolder_id == vfolder_id
        assert result.mount_path == "/data"
        assert result.permission == "rw"

    def test_optional_fields_default_none(self) -> None:
        vfolder_id = uuid4()
        result = MountItemInput(vfolder_id=vfolder_id)
        assert result.mount_path is None
        assert result.permission is None


class TestResourceOptsInput:
    """Tests for ResourceOptsInput model."""

    def test_valid_shmem(self) -> None:
        result = ResourceOptsInput(shmem="2g")
        assert result.shmem == "2g"

    def test_default_none(self) -> None:
        result = ResourceOptsInput()
        assert result.shmem is None
