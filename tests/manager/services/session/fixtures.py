import copy
import dataclasses
import uuid
from datetime import datetime, timezone
from uuid import uuid4

import yarl

from ai.backend.common.types import (
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.session import SessionRow, SessionStatus

SESSION_ROW_FIXTURE = SessionRow(
    id=SessionId(uuid4()),
    creation_id=uuid4().hex[:22],
    name="test_session",
    session_type=SessionTypes.INTERACTIVE,
    priority=0,
    cluster_mode=ClusterMode.SINGLE_NODE.name,
    cluster_size=1,
    agent_ids=[],
    scaling_group_name="default",
    target_sgroup_names=[],
    domain_name="default",
    group_id=uuid.UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831"),  # from example-users.json
    user_uuid=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),  # from example-users.json
    access_key="AKIAIOSFODNN7EXAMPLE",
    images=["cr.backend.ai/stable/python:latest"],
    tag=None,
    occupying_slots=ResourceSlot(cpu=1, mem=1024),
    requested_slots=ResourceSlot(cpu=1, mem=1024),
    vfolder_mounts=[],
    environ={},
    bootstrap_script=None,
    use_host_network=False,
    timeout=None,
    batch_timeout=None,
    created_at=datetime.now(timezone.utc),
    terminated_at=None,
    starts_at=None,
    status=SessionStatus.RUNNING,
    status_info=None,
    status_data=None,
    status_history=None,
    callback_url=yarl.URL(""),
    startup_command=None,
    result=SessionResult.UNDEFINED,
    num_queries=0,
    last_stat=None,
    network_type=NetworkType.VOLATILE,
    network_id=None,
)

KERNEL_ROW_FIXTURE = KernelRow(
    id=KernelId(uuid4()),
    session_id=SESSION_ROW_FIXTURE.id,
    session_creation_id=SESSION_ROW_FIXTURE.creation_id,
    session_name=SESSION_ROW_FIXTURE.name,
    session_type=SessionTypes.INTERACTIVE,
    cluster_mode=ClusterMode.SINGLE_NODE,
    cluster_size=1,
    cluster_role="main",
    cluster_idx=1,
    local_rank=0,
    cluster_hostname="main1",
    uid=None,
    main_gid=None,
    gids=[],
    scaling_group="default",
    agent="i-ubuntu",
    agent_addr="tcp://127.0.0.1:6011",
    domain_name=SESSION_ROW_FIXTURE.domain_name,
    group_id=SESSION_ROW_FIXTURE.group_id,
    user_uuid=SESSION_ROW_FIXTURE.user_uuid,
    access_key=SESSION_ROW_FIXTURE.access_key,
    image="registry.example.com/test_project/python:3.9",
    architecture="x86_64",
    registry="registry.example.com",
    tag=None,
    container_id=uuid4().hex[:12],
    occupied_slots=ResourceSlot(cpu=1, mem=1024),
    requested_slots=ResourceSlot(cpu=1, mem=1024),
    occupied_shares={},
    environ=[],
    mounts=None,
    mount_map=None,
    vfolder_mounts=[],
    attached_devices={},
    resource_opts={},
    bootstrap_script=None,
    kernel_host="127.0.0.1",
    repl_in_port=20000,
    repl_out_port=30001,
    stdin_port=40001,
    stdout_port=50001,
    service_ports=None,
    preopen_ports=[],
    use_host_network=False,
    created_at=datetime.now(timezone.utc),
    terminated_at=None,
    starts_at=None,
    status=KernelStatus.RUNNING,
    status_changed=None,
    status_info=None,
    status_data=None,
    status_history=None,
    callback_url=SESSION_ROW_FIXTURE.callback_url,
    startup_command=None,
    result=SessionResult.UNDEFINED,
    internal_data=None,
    container_log=None,
    num_queries=0,
    last_stat=None,
)
SESSION_ROW_FIXTURE.kernels = [KERNEL_ROW_FIXTURE]

SESSION_FIXTURE_DATA = SESSION_ROW_FIXTURE.to_dataclass()

SESSION_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        SESSION_FIXTURE_DATA,
        result=SESSION_FIXTURE_DATA.result.name,  # type: ignore
        status=SESSION_FIXTURE_DATA.status.value,  # type: ignore
    )
)

del SESSION_FIXTURE_DICT["service_ports"]

# Add status_history for testing
SESSION_FIXTURE_DICT["status_history"] = {
    "history": [
        {"status": "PENDING", "timestamp": "2023-01-01T00:00:00Z"},
        {"status": "RUNNING", "timestamp": "2023-01-01T00:01:00Z"},
    ]
}

KERNEL_FIXTURE_DATA = KERNEL_ROW_FIXTURE.to_dataclass()
KERNEL_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        KERNEL_FIXTURE_DATA,
        session_type=KERNEL_FIXTURE_DATA.session_type.value,  # type: ignore
        cluster_mode=KERNEL_FIXTURE_DATA.cluster_mode.name,  # type: ignore
        result=KERNEL_FIXTURE_DATA.result.name,  # type: ignore
        status=KERNEL_FIXTURE_DATA.status.value,  # type: ignore
    )
)


PENDING_SESSION_FIXTURE_DATA = copy.deepcopy(SESSION_FIXTURE_DATA)
PENDING_SESSION_FIXTURE_DATA.id = SessionId(uuid.uuid4())
PENDING_SESSION_FIXTURE_DATA.name = "pending_session"
PENDING_SESSION_FIXTURE_DATA.status = SessionStatus.PENDING

PENDING_SESSION_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        PENDING_SESSION_FIXTURE_DATA,
        result=PENDING_SESSION_FIXTURE_DATA.result.name,  # type: ignore
        status=PENDING_SESSION_FIXTURE_DATA.status.value,  # type: ignore
    )
)

# Additional fixtures for complex database operations
IMAGE_FIXTURE_DATA = {
    "id": "test_image_id",
    "name": "python",
    "project": "test_project",
    "tag": "3.9",
    "registry": "registry.example.com",
    "architecture": "x86_64",
    "config_digest": "sha256:test_config_digest",
    "size_bytes": 1024,
    "type": "compute",
    "accelerators": "",
    "labels": {},
    "resource_limits": [],
    "supported_accelerators": "",
    "installed_global_pkgs": [],
    "digest": "sha256:test_digest",
    "installed": True,
    "resource_slots": {"cpu": "1", "mem": "1g"},
    "environments": [],
    "min_kernel_version": "1.0.0",
    "is_local": False,
}

GROUP_FIXTURE_DATA = {
    "id": SESSION_FIXTURE_DATA.group_id,
    "name": "test_group",
    "description": "Test group for fixtures",
    "is_active": True,
    "domain_name": SESSION_FIXTURE_DATA.domain_name,
    "total_resource_slots": {},
    "allowed_vfolder_hosts": {},
    "resource_policy": "default",
    "type": "general",
    "container_registry": {
        "registry": "registry.example.com",
        "project": "test_project",
    },
}

USER_FIXTURE_DATA = {
    "uuid": SESSION_FIXTURE_DATA.user_uuid,
    "username": "test_user",
    "email": "test@example.com",
    "password": "test_password",
    "need_password_change": False,
    "full_name": "Test User",
    "description": "Test user for fixtures",
    "status": "active",
    "status_info": "admin-requested",
    "domain_name": SESSION_FIXTURE_DATA.domain_name,
    "role": "user",
    "main_access_key": SESSION_FIXTURE_DATA.access_key,
    "resource_policy": "default",
}

# Association table for groups and users
GROUP_USER_ASSOCIATION_DATA = {
    "group_id": SESSION_FIXTURE_DATA.group_id,
    "user_id": SESSION_FIXTURE_DATA.user_uuid,
}

# Child session fixture for dependency graph testing
SESSION_ROW_FIXTURE2 = SessionRow(
    id=SessionId(uuid4()),
    creation_id=uuid4().hex[:22],
    name="test_session_child",
    session_type=SessionTypes.INTERACTIVE,
    priority=0,
    cluster_mode=ClusterMode.SINGLE_NODE.name,
    cluster_size=1,
    agent_ids=[],
    scaling_group_name="default",
    target_sgroup_names=[],
    domain_name="default",
    group_id=uuid.UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831"),
    user_uuid=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
    access_key="AKIAIOSFODNN7EXAMPLE",
    images=["cr.backend.ai/stable/python:latest"],
    tag=None,
    occupying_slots=ResourceSlot(cpu=1, mem=1024),
    requested_slots=ResourceSlot(cpu=1, mem=1024),
    vfolder_mounts=[],
    environ={},
    bootstrap_script=None,
    use_host_network=False,
    timeout=None,
    batch_timeout=None,
    created_at=datetime.now(timezone.utc),
    terminated_at=None,
    starts_at=None,
    status=SessionStatus.RUNNING,
    status_info=None,
    status_data=None,
    status_history=None,
    callback_url=yarl.URL(""),
    startup_command=None,
    result=SessionResult.UNDEFINED,
    num_queries=0,
    last_stat=None,
    network_type=NetworkType.VOLATILE,
    network_id=None,
)

KERNEL_ROW_FIXTURE2 = KernelRow(
    id=KernelId(uuid4()),
    session_id=SESSION_ROW_FIXTURE2.id,
    session_creation_id=SESSION_ROW_FIXTURE2.creation_id,
    session_name=SESSION_ROW_FIXTURE2.name,
    session_type=SessionTypes.INTERACTIVE,
    cluster_mode=ClusterMode.SINGLE_NODE,
    cluster_size=1,
    cluster_role="main",
    cluster_idx=1,
    local_rank=0,
    cluster_hostname="main1",
    uid=None,
    main_gid=None,
    gids=[],
    scaling_group="default",
    agent="i-ubuntu",
    agent_addr="tcp://127.0.0.1:6011",
    domain_name=SESSION_ROW_FIXTURE2.domain_name,
    group_id=SESSION_ROW_FIXTURE2.group_id,
    user_uuid=SESSION_ROW_FIXTURE2.user_uuid,
    access_key=SESSION_ROW_FIXTURE2.access_key,
    image="registry.example.com/test_project/python:3.9",
    architecture="x86_64",
    registry="registry.example.com",
    tag=None,
    container_id=uuid4().hex[:12],
    occupied_slots=ResourceSlot(cpu=1, mem=1024),
    requested_slots=ResourceSlot(cpu=1, mem=1024),
    occupied_shares={},
    environ=[],
    mounts=None,
    mount_map=None,
    vfolder_mounts=[],
    attached_devices={},
    resource_opts={},
    bootstrap_script=None,
    kernel_host="127.0.0.1",
    repl_in_port=20000,
    repl_out_port=30001,
    stdin_port=40001,
    stdout_port=50001,
    service_ports=None,
    preopen_ports=[],
    use_host_network=False,
    created_at=datetime.now(timezone.utc),
    terminated_at=None,
    starts_at=None,
    status=KernelStatus.RUNNING,
    status_changed=None,
    status_info=None,
    status_data=None,
    status_history=None,
    callback_url=SESSION_ROW_FIXTURE2.callback_url,
    startup_command=None,
    result=SessionResult.UNDEFINED,
    internal_data=None,
    container_log=None,
    num_queries=0,
    last_stat=None,
)
SESSION_ROW_FIXTURE2.kernels = [KERNEL_ROW_FIXTURE2]

SESSION_FIXTURE_DATA2 = SESSION_ROW_FIXTURE2.to_dataclass()

SESSION_FIXTURE_DICT2 = dataclasses.asdict(
    dataclasses.replace(
        SESSION_FIXTURE_DATA2,
        result=SESSION_FIXTURE_DATA2.result.name,
        status=SESSION_FIXTURE_DATA2.status.value,
    )
)

KERNEL_FIXTURE_DATA2 = KERNEL_ROW_FIXTURE2.to_dataclass()
KERNEL_FIXTURE_DICT2 = dataclasses.asdict(
    dataclasses.replace(
        KERNEL_FIXTURE_DATA2,
        session_type=KERNEL_FIXTURE_DATA2.session_type.value,
        cluster_mode=KERNEL_FIXTURE_DATA2.cluster_mode.name,
        result=KERNEL_FIXTURE_DATA2.result.name,
        status=KERNEL_FIXTURE_DATA2.status.value,
    )
)

del SESSION_FIXTURE_DICT2["service_ports"]

SESSION_FIXTURE_DICT2["status_history"] = {
    "history": [
        {"status": "PENDING", "timestamp": "2023-01-01T00:00:00Z"},
        {"status": "RUNNING", "timestamp": "2023-01-01T00:01:00Z"},
    ]
}
