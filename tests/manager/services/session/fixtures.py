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
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelStatus,
    LifecycleStatus,
    Metadata,
    Metrics,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.data.user.types import UserData, UserRole
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


AGENT_ROW_FIXTURE = AgentRow(
    id="i-ubuntu",
    status=AgentStatus.ALIVE,
    status_changed=datetime.now(timezone.utc),
    region="us-east-1",
    scaling_group="default",
    available_slots=ResourceSlot(cpu=16, mem=32768),
    occupied_slots=ResourceSlot(cpu=0, mem=0),
    addr="tcp://127.0.0.1:6011",
    first_contact=datetime.now(timezone.utc),
    lost_at=None,
    version="24.09.0",
    compute_plugins={},
    architecture="x86_64",
)

USER_ROW_FIXTURE = UserRow(
    uuid=uuid4(),
    username=f"test_user_{uuid4()}",
    email=f"test-{uuid4()}@example.com",
    password=create_test_password_info("test_password"),
    need_password_change=False,
    full_name="Test User",
    description="Test user for fixtures",
    status="active",
    resource_policy="default",
    sudo_session_enabled=True,
)

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
    user=USER_ROW_FIXTURE,
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

# Create SessionData directly instead of using to_dataclass()
SESSION_FIXTURE_DATA = SessionData(
    id=SESSION_ROW_FIXTURE.id,
    creation_id=SESSION_ROW_FIXTURE.creation_id,
    name=SESSION_ROW_FIXTURE.name,
    session_type=SESSION_ROW_FIXTURE.session_type,
    priority=SESSION_ROW_FIXTURE.priority,
    cluster_mode=ClusterMode[SESSION_ROW_FIXTURE.cluster_mode],
    cluster_size=SESSION_ROW_FIXTURE.cluster_size,
    agent_ids=SESSION_ROW_FIXTURE.agent_ids,
    domain_name=SESSION_ROW_FIXTURE.domain_name,
    group_id=SESSION_ROW_FIXTURE.group_id,
    user_uuid=SESSION_ROW_FIXTURE.user_uuid,
    access_key=SESSION_ROW_FIXTURE.access_key,
    images=SESSION_ROW_FIXTURE.images,
    tag=SESSION_ROW_FIXTURE.tag,
    occupying_slots=SESSION_ROW_FIXTURE.occupying_slots,
    requested_slots=SESSION_ROW_FIXTURE.requested_slots,
    vfolder_mounts=SESSION_ROW_FIXTURE.vfolder_mounts,
    environ=SESSION_ROW_FIXTURE.environ,
    bootstrap_script=SESSION_ROW_FIXTURE.bootstrap_script,
    use_host_network=SESSION_ROW_FIXTURE.use_host_network,
    timeout=SESSION_ROW_FIXTURE.timeout,
    batch_timeout=SESSION_ROW_FIXTURE.batch_timeout,
    created_at=SESSION_ROW_FIXTURE.created_at,
    terminated_at=SESSION_ROW_FIXTURE.terminated_at,
    starts_at=SESSION_ROW_FIXTURE.starts_at,
    status=SESSION_ROW_FIXTURE.status,
    status_info=SESSION_ROW_FIXTURE.status_info,
    status_data=dict(SESSION_ROW_FIXTURE.status_data) if SESSION_ROW_FIXTURE.status_data else None,
    status_history=SESSION_ROW_FIXTURE.status_history,
    callback_url=str(SESSION_ROW_FIXTURE.callback_url),
    startup_command=SESSION_ROW_FIXTURE.startup_command,
    result=SESSION_ROW_FIXTURE.result,
    num_queries=SESSION_ROW_FIXTURE.num_queries,
    last_stat=SESSION_ROW_FIXTURE.last_stat,
    network_type=SESSION_ROW_FIXTURE.network_type,
    network_id=SESSION_ROW_FIXTURE.network_id,
    scaling_group_name=SESSION_ROW_FIXTURE.scaling_group_name,
    target_sgroup_names=SESSION_ROW_FIXTURE.target_sgroup_names,
    owner=UserData(
        id=USER_ROW_FIXTURE.uuid,
        uuid=USER_ROW_FIXTURE.uuid,
        username=USER_ROW_FIXTURE.username,
        email=USER_ROW_FIXTURE.email,
        need_password_change=USER_ROW_FIXTURE.need_password_change,
        full_name=USER_ROW_FIXTURE.full_name,
        description=USER_ROW_FIXTURE.description,
        is_active=True,
        status=USER_ROW_FIXTURE.status,
        status_info=None,
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        domain_name="default",
        role=UserRole.USER,
        resource_policy=USER_ROW_FIXTURE.resource_policy,
        allowed_client_ip=None,
        totp_activated=False,
        totp_activated_at=None,
        sudo_session_enabled=USER_ROW_FIXTURE.sudo_session_enabled,
        main_access_key="AKIAIOSFODNN7EXAMPLE",
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
    ),
    service_ports=None,
)

SESSION_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        SESSION_FIXTURE_DATA,
        result=SESSION_FIXTURE_DATA.result.name,  # type: ignore
        status=SESSION_FIXTURE_DATA.status.name,  # type: ignore
    )
)

del SESSION_FIXTURE_DICT["service_ports"]
del SESSION_FIXTURE_DICT["owner"]

# Add status_history for testing
SESSION_FIXTURE_DICT["status_history"] = {
    "history": [
        {"status": "PENDING", "timestamp": "2023-01-01T00:00:00Z"},
        {"status": "RUNNING", "timestamp": "2023-01-01T00:01:00Z"},
    ]
}

# Create KernelInfo directly instead of using to_dataclass()
KERNEL_FIXTURE_DATA = KernelInfo(
    id=KERNEL_ROW_FIXTURE.id,
    session=RelatedSessionInfo(
        session_id=str(KERNEL_ROW_FIXTURE.session_id),
        creation_id=KERNEL_ROW_FIXTURE.session_creation_id,
        name=KERNEL_ROW_FIXTURE.session_name,
        session_type=KERNEL_ROW_FIXTURE.session_type,
    ),
    user_permission=UserPermission(
        user_uuid=KERNEL_ROW_FIXTURE.user_uuid,
        access_key=KERNEL_ROW_FIXTURE.access_key,
        domain_name=KERNEL_ROW_FIXTURE.domain_name,
        group_id=KERNEL_ROW_FIXTURE.group_id,
        uid=KERNEL_ROW_FIXTURE.uid,
        main_gid=KERNEL_ROW_FIXTURE.main_gid,
        gids=KERNEL_ROW_FIXTURE.gids if KERNEL_ROW_FIXTURE.gids else [],
    ),
    image=ImageInfo(
        identifier=None,
        registry=KERNEL_ROW_FIXTURE.registry,
        tag=KERNEL_ROW_FIXTURE.tag,
    ),
    network=NetworkConfig(
        kernel_host=KERNEL_ROW_FIXTURE.kernel_host,
        repl_in_port=KERNEL_ROW_FIXTURE.repl_in_port,
        repl_out_port=KERNEL_ROW_FIXTURE.repl_out_port,
        stdin_port=KERNEL_ROW_FIXTURE.stdin_port,
        stdout_port=KERNEL_ROW_FIXTURE.stdout_port,
        service_ports=KERNEL_ROW_FIXTURE.service_ports,
        preopen_ports=KERNEL_ROW_FIXTURE.preopen_ports,
        use_host_network=KERNEL_ROW_FIXTURE.use_host_network,
    ),
    cluster=ClusterConfig(
        cluster_mode=KERNEL_ROW_FIXTURE.cluster_mode.name,
        cluster_size=KERNEL_ROW_FIXTURE.cluster_size,
        cluster_role=KERNEL_ROW_FIXTURE.cluster_role,
        cluster_idx=KERNEL_ROW_FIXTURE.cluster_idx,
        local_rank=KERNEL_ROW_FIXTURE.local_rank,
        cluster_hostname=KERNEL_ROW_FIXTURE.cluster_hostname,
    ),
    resource=ResourceInfo(
        scaling_group=KERNEL_ROW_FIXTURE.scaling_group,
        agent=KERNEL_ROW_FIXTURE.agent,
        agent_addr=KERNEL_ROW_FIXTURE.agent_addr,
        container_id=KERNEL_ROW_FIXTURE.container_id,
        occupied_slots=KERNEL_ROW_FIXTURE.occupied_slots,
        requested_slots=KERNEL_ROW_FIXTURE.requested_slots,
        occupied_shares=KERNEL_ROW_FIXTURE.occupied_shares,
        attached_devices=KERNEL_ROW_FIXTURE.attached_devices,
        resource_opts=KERNEL_ROW_FIXTURE.resource_opts,
    ),
    runtime=RuntimeConfig(
        environ=KERNEL_ROW_FIXTURE.environ,
        mounts=KERNEL_ROW_FIXTURE.mounts,
        mount_map=KERNEL_ROW_FIXTURE.mount_map,
        vfolder_mounts=KERNEL_ROW_FIXTURE.vfolder_mounts,
        bootstrap_script=KERNEL_ROW_FIXTURE.bootstrap_script,
        startup_command=KERNEL_ROW_FIXTURE.startup_command,
    ),
    lifecycle=LifecycleStatus(
        status=KERNEL_ROW_FIXTURE.status,
        result=KERNEL_ROW_FIXTURE.result,
        created_at=KERNEL_ROW_FIXTURE.created_at,
        terminated_at=KERNEL_ROW_FIXTURE.terminated_at,
        starts_at=KERNEL_ROW_FIXTURE.starts_at,
        status_changed=KERNEL_ROW_FIXTURE.status_changed,
        status_info=KERNEL_ROW_FIXTURE.status_info,
        status_data=KERNEL_ROW_FIXTURE.status_data,
        status_history=KERNEL_ROW_FIXTURE.status_history,
        last_seen=datetime.now(timezone.utc),
    ),
    metrics=Metrics(
        num_queries=KERNEL_ROW_FIXTURE.num_queries,
        last_stat=KERNEL_ROW_FIXTURE.last_stat,
        container_log=KERNEL_ROW_FIXTURE.container_log,
    ),
    metadata=Metadata(
        callback_url=str(KERNEL_ROW_FIXTURE.callback_url),
        internal_data=KERNEL_ROW_FIXTURE.internal_data,
    ),
)

# Create flat dict suitable for database insertion
AGENT_FIXTURE_DICT = {
    "id": AGENT_ROW_FIXTURE.id,
    "status": AGENT_ROW_FIXTURE.status.name,  # Use name instead of value for enum
    "status_changed": AGENT_ROW_FIXTURE.status_changed,
    "region": AGENT_ROW_FIXTURE.region,
    "scaling_group": AGENT_ROW_FIXTURE.scaling_group,
    "available_slots": AGENT_ROW_FIXTURE.available_slots,
    "occupied_slots": AGENT_ROW_FIXTURE.occupied_slots,
    "addr": AGENT_ROW_FIXTURE.addr,
    "first_contact": AGENT_ROW_FIXTURE.first_contact,
    "lost_at": AGENT_ROW_FIXTURE.lost_at,
    "version": AGENT_ROW_FIXTURE.version,
    "compute_plugins": AGENT_ROW_FIXTURE.compute_plugins,
    "architecture": AGENT_ROW_FIXTURE.architecture,
}

KERNEL_FIXTURE_DICT = {
    "id": KERNEL_ROW_FIXTURE.id,
    "session_id": KERNEL_ROW_FIXTURE.session_id,
    "session_creation_id": KERNEL_ROW_FIXTURE.session_creation_id,
    "session_name": KERNEL_ROW_FIXTURE.session_name,
    "session_type": KERNEL_ROW_FIXTURE.session_type.value,
    "cluster_mode": KERNEL_ROW_FIXTURE.cluster_mode.name,
    "cluster_size": KERNEL_ROW_FIXTURE.cluster_size,
    "cluster_role": KERNEL_ROW_FIXTURE.cluster_role,
    "cluster_idx": KERNEL_ROW_FIXTURE.cluster_idx,
    "local_rank": KERNEL_ROW_FIXTURE.local_rank,
    "cluster_hostname": KERNEL_ROW_FIXTURE.cluster_hostname,
    "uid": KERNEL_ROW_FIXTURE.uid,
    "main_gid": KERNEL_ROW_FIXTURE.main_gid,
    "gids": KERNEL_ROW_FIXTURE.gids,
    "scaling_group": KERNEL_ROW_FIXTURE.scaling_group,
    "agent": KERNEL_ROW_FIXTURE.agent,
    "agent_addr": KERNEL_ROW_FIXTURE.agent_addr,
    "domain_name": KERNEL_ROW_FIXTURE.domain_name,
    "group_id": KERNEL_ROW_FIXTURE.group_id,
    "user_uuid": KERNEL_ROW_FIXTURE.user_uuid,
    "access_key": KERNEL_ROW_FIXTURE.access_key,
    "image": KERNEL_ROW_FIXTURE.image,
    "architecture": KERNEL_ROW_FIXTURE.architecture,
    "registry": KERNEL_ROW_FIXTURE.registry,
    "tag": KERNEL_ROW_FIXTURE.tag,
    "container_id": KERNEL_ROW_FIXTURE.container_id,
    "occupied_slots": KERNEL_ROW_FIXTURE.occupied_slots,
    "requested_slots": KERNEL_ROW_FIXTURE.requested_slots,
    "occupied_shares": KERNEL_ROW_FIXTURE.occupied_shares,
    "environ": KERNEL_ROW_FIXTURE.environ,
    "mounts": KERNEL_ROW_FIXTURE.mounts,
    "mount_map": KERNEL_ROW_FIXTURE.mount_map,
    "vfolder_mounts": KERNEL_ROW_FIXTURE.vfolder_mounts,
    "attached_devices": KERNEL_ROW_FIXTURE.attached_devices,
    "resource_opts": KERNEL_ROW_FIXTURE.resource_opts,
    "bootstrap_script": KERNEL_ROW_FIXTURE.bootstrap_script,
    "kernel_host": KERNEL_ROW_FIXTURE.kernel_host,
    "repl_in_port": KERNEL_ROW_FIXTURE.repl_in_port,
    "repl_out_port": KERNEL_ROW_FIXTURE.repl_out_port,
    "stdin_port": KERNEL_ROW_FIXTURE.stdin_port,
    "stdout_port": KERNEL_ROW_FIXTURE.stdout_port,
    "service_ports": KERNEL_ROW_FIXTURE.service_ports,
    "preopen_ports": KERNEL_ROW_FIXTURE.preopen_ports,
    "use_host_network": KERNEL_ROW_FIXTURE.use_host_network,
    "created_at": KERNEL_ROW_FIXTURE.created_at,
    "terminated_at": KERNEL_ROW_FIXTURE.terminated_at,
    "starts_at": KERNEL_ROW_FIXTURE.starts_at,
    "status": KERNEL_ROW_FIXTURE.status.name,  # Use name instead of value for enum
    "status_changed": KERNEL_ROW_FIXTURE.status_changed,
    "status_info": KERNEL_ROW_FIXTURE.status_info,
    "status_data": KERNEL_ROW_FIXTURE.status_data,
    "status_history": KERNEL_ROW_FIXTURE.status_history,
    "callback_url": str(KERNEL_ROW_FIXTURE.callback_url),
    "startup_command": KERNEL_ROW_FIXTURE.startup_command,
    "result": KERNEL_ROW_FIXTURE.result.name,
    "internal_data": KERNEL_ROW_FIXTURE.internal_data,
    "container_log": KERNEL_ROW_FIXTURE.container_log,
    "num_queries": KERNEL_ROW_FIXTURE.num_queries,
    "last_stat": KERNEL_ROW_FIXTURE.last_stat,
}


PENDING_SESSION_FIXTURE_DATA = copy.deepcopy(SESSION_FIXTURE_DATA)
PENDING_SESSION_FIXTURE_DATA.id = SessionId(uuid.uuid4())
PENDING_SESSION_FIXTURE_DATA.name = "pending_session"
PENDING_SESSION_FIXTURE_DATA.status = SessionStatus.PENDING

PENDING_SESSION_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        PENDING_SESSION_FIXTURE_DATA,
        result=PENDING_SESSION_FIXTURE_DATA.result.name,  # type: ignore
        status=PENDING_SESSION_FIXTURE_DATA.status.name,  # type: ignore
    )
)

del PENDING_SESSION_FIXTURE_DICT["owner"]

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

# Create SessionData directly for FIXTURE2
SESSION_FIXTURE_DATA2 = SessionData(
    id=SESSION_ROW_FIXTURE2.id,
    creation_id=SESSION_ROW_FIXTURE2.creation_id,
    name=SESSION_ROW_FIXTURE2.name,
    session_type=SESSION_ROW_FIXTURE2.session_type,
    priority=SESSION_ROW_FIXTURE2.priority,
    cluster_mode=ClusterMode[SESSION_ROW_FIXTURE2.cluster_mode],
    cluster_size=SESSION_ROW_FIXTURE2.cluster_size,
    agent_ids=SESSION_ROW_FIXTURE2.agent_ids,
    domain_name=SESSION_ROW_FIXTURE2.domain_name,
    group_id=SESSION_ROW_FIXTURE2.group_id,
    user_uuid=SESSION_ROW_FIXTURE2.user_uuid,
    access_key=SESSION_ROW_FIXTURE2.access_key,
    images=SESSION_ROW_FIXTURE2.images,
    tag=SESSION_ROW_FIXTURE2.tag,
    occupying_slots=SESSION_ROW_FIXTURE2.occupying_slots,
    requested_slots=SESSION_ROW_FIXTURE2.requested_slots,
    vfolder_mounts=SESSION_ROW_FIXTURE2.vfolder_mounts,
    environ=SESSION_ROW_FIXTURE2.environ,
    bootstrap_script=SESSION_ROW_FIXTURE2.bootstrap_script,
    use_host_network=SESSION_ROW_FIXTURE2.use_host_network,
    timeout=SESSION_ROW_FIXTURE2.timeout,
    batch_timeout=SESSION_ROW_FIXTURE2.batch_timeout,
    created_at=SESSION_ROW_FIXTURE2.created_at,
    terminated_at=SESSION_ROW_FIXTURE2.terminated_at,
    starts_at=SESSION_ROW_FIXTURE2.starts_at,
    status=SESSION_ROW_FIXTURE2.status,
    status_info=SESSION_ROW_FIXTURE2.status_info,
    status_data=dict(SESSION_ROW_FIXTURE2.status_data)
    if SESSION_ROW_FIXTURE2.status_data
    else None,
    status_history=SESSION_ROW_FIXTURE2.status_history,
    callback_url=str(SESSION_ROW_FIXTURE2.callback_url),
    startup_command=SESSION_ROW_FIXTURE2.startup_command,
    result=SESSION_ROW_FIXTURE2.result,
    num_queries=SESSION_ROW_FIXTURE2.num_queries,
    last_stat=SESSION_ROW_FIXTURE2.last_stat,
    network_type=SESSION_ROW_FIXTURE2.network_type,
    network_id=SESSION_ROW_FIXTURE2.network_id,
    scaling_group_name=SESSION_ROW_FIXTURE2.scaling_group_name,
    target_sgroup_names=SESSION_ROW_FIXTURE2.target_sgroup_names,
    owner=None,
    service_ports=None,
)

SESSION_FIXTURE_DICT2 = dataclasses.asdict(
    dataclasses.replace(
        SESSION_FIXTURE_DATA2,
        result=SESSION_FIXTURE_DATA2.result.name,  # type: ignore
        status=SESSION_FIXTURE_DATA2.status.name,  # type: ignore
    )
)

# Create KernelInfo directly for FIXTURE2
KERNEL_FIXTURE_DATA2 = KernelInfo(
    id=KERNEL_ROW_FIXTURE2.id,
    session=RelatedSessionInfo(
        session_id=str(KERNEL_ROW_FIXTURE2.session_id),
        creation_id=KERNEL_ROW_FIXTURE2.session_creation_id,
        name=KERNEL_ROW_FIXTURE2.session_name,
        session_type=KERNEL_ROW_FIXTURE2.session_type,
    ),
    user_permission=UserPermission(
        user_uuid=KERNEL_ROW_FIXTURE2.user_uuid,
        access_key=KERNEL_ROW_FIXTURE2.access_key,
        domain_name=KERNEL_ROW_FIXTURE2.domain_name,
        group_id=KERNEL_ROW_FIXTURE2.group_id,
        uid=KERNEL_ROW_FIXTURE2.uid,
        main_gid=KERNEL_ROW_FIXTURE2.main_gid,
        gids=KERNEL_ROW_FIXTURE2.gids if KERNEL_ROW_FIXTURE2.gids else [],
    ),
    image=ImageInfo(
        identifier=None,
        registry=KERNEL_ROW_FIXTURE2.registry,
        tag=KERNEL_ROW_FIXTURE2.tag,
    ),
    network=NetworkConfig(
        kernel_host=KERNEL_ROW_FIXTURE2.kernel_host,
        repl_in_port=KERNEL_ROW_FIXTURE2.repl_in_port,
        repl_out_port=KERNEL_ROW_FIXTURE2.repl_out_port,
        stdin_port=KERNEL_ROW_FIXTURE2.stdin_port,
        stdout_port=KERNEL_ROW_FIXTURE2.stdout_port,
        service_ports=KERNEL_ROW_FIXTURE2.service_ports,
        preopen_ports=KERNEL_ROW_FIXTURE2.preopen_ports,
        use_host_network=KERNEL_ROW_FIXTURE2.use_host_network,
    ),
    cluster=ClusterConfig(
        cluster_mode=KERNEL_ROW_FIXTURE2.cluster_mode.name,
        cluster_size=KERNEL_ROW_FIXTURE2.cluster_size,
        cluster_role=KERNEL_ROW_FIXTURE2.cluster_role,
        cluster_idx=KERNEL_ROW_FIXTURE2.cluster_idx,
        local_rank=KERNEL_ROW_FIXTURE2.local_rank,
        cluster_hostname=KERNEL_ROW_FIXTURE2.cluster_hostname,
    ),
    resource=ResourceInfo(
        scaling_group=KERNEL_ROW_FIXTURE2.scaling_group,
        agent=KERNEL_ROW_FIXTURE2.agent,
        agent_addr=KERNEL_ROW_FIXTURE2.agent_addr,
        container_id=KERNEL_ROW_FIXTURE2.container_id,
        occupied_slots=KERNEL_ROW_FIXTURE2.occupied_slots,
        requested_slots=KERNEL_ROW_FIXTURE2.requested_slots,
        occupied_shares=KERNEL_ROW_FIXTURE2.occupied_shares,
        attached_devices=KERNEL_ROW_FIXTURE2.attached_devices,
        resource_opts=KERNEL_ROW_FIXTURE2.resource_opts,
    ),
    runtime=RuntimeConfig(
        environ=KERNEL_ROW_FIXTURE2.environ,
        mounts=KERNEL_ROW_FIXTURE2.mounts,
        mount_map=KERNEL_ROW_FIXTURE2.mount_map,
        vfolder_mounts=KERNEL_ROW_FIXTURE2.vfolder_mounts,
        bootstrap_script=KERNEL_ROW_FIXTURE2.bootstrap_script,
        startup_command=KERNEL_ROW_FIXTURE2.startup_command,
    ),
    lifecycle=LifecycleStatus(
        status=KERNEL_ROW_FIXTURE2.status,
        result=KERNEL_ROW_FIXTURE2.result,
        created_at=KERNEL_ROW_FIXTURE2.created_at,
        terminated_at=KERNEL_ROW_FIXTURE2.terminated_at,
        starts_at=KERNEL_ROW_FIXTURE2.starts_at,
        status_changed=KERNEL_ROW_FIXTURE2.status_changed,
        status_info=KERNEL_ROW_FIXTURE2.status_info,
        status_data=KERNEL_ROW_FIXTURE2.status_data,
        status_history=KERNEL_ROW_FIXTURE2.status_history,
        last_seen=datetime.now(timezone.utc),
    ),
    metrics=Metrics(
        num_queries=KERNEL_ROW_FIXTURE2.num_queries,
        last_stat=KERNEL_ROW_FIXTURE2.last_stat,
        container_log=KERNEL_ROW_FIXTURE2.container_log,
    ),
    metadata=Metadata(
        callback_url=str(KERNEL_ROW_FIXTURE2.callback_url),
        internal_data=KERNEL_ROW_FIXTURE2.internal_data,
    ),
)

# Create flat dict suitable for database insertion for FIXTURE2
KERNEL_FIXTURE_DICT2 = {
    "id": KERNEL_ROW_FIXTURE2.id,
    "session_id": KERNEL_ROW_FIXTURE2.session_id,
    "session_creation_id": KERNEL_ROW_FIXTURE2.session_creation_id,
    "session_name": KERNEL_ROW_FIXTURE2.session_name,
    "session_type": KERNEL_ROW_FIXTURE2.session_type.value,
    "cluster_mode": KERNEL_ROW_FIXTURE2.cluster_mode.name,
    "cluster_size": KERNEL_ROW_FIXTURE2.cluster_size,
    "cluster_role": KERNEL_ROW_FIXTURE2.cluster_role,
    "cluster_idx": KERNEL_ROW_FIXTURE2.cluster_idx,
    "local_rank": KERNEL_ROW_FIXTURE2.local_rank,
    "cluster_hostname": KERNEL_ROW_FIXTURE2.cluster_hostname,
    "uid": KERNEL_ROW_FIXTURE2.uid,
    "main_gid": KERNEL_ROW_FIXTURE2.main_gid,
    "gids": KERNEL_ROW_FIXTURE2.gids,
    "scaling_group": KERNEL_ROW_FIXTURE2.scaling_group,
    "agent": KERNEL_ROW_FIXTURE2.agent,
    "agent_addr": KERNEL_ROW_FIXTURE2.agent_addr,
    "domain_name": KERNEL_ROW_FIXTURE2.domain_name,
    "group_id": KERNEL_ROW_FIXTURE2.group_id,
    "user_uuid": KERNEL_ROW_FIXTURE2.user_uuid,
    "access_key": KERNEL_ROW_FIXTURE2.access_key,
    "image": KERNEL_ROW_FIXTURE2.image,
    "architecture": KERNEL_ROW_FIXTURE2.architecture,
    "registry": KERNEL_ROW_FIXTURE2.registry,
    "tag": KERNEL_ROW_FIXTURE2.tag,
    "container_id": KERNEL_ROW_FIXTURE2.container_id,
    "occupied_slots": KERNEL_ROW_FIXTURE2.occupied_slots,
    "requested_slots": KERNEL_ROW_FIXTURE2.requested_slots,
    "occupied_shares": KERNEL_ROW_FIXTURE2.occupied_shares,
    "environ": KERNEL_ROW_FIXTURE2.environ,
    "mounts": KERNEL_ROW_FIXTURE2.mounts,
    "mount_map": KERNEL_ROW_FIXTURE2.mount_map,
    "vfolder_mounts": KERNEL_ROW_FIXTURE2.vfolder_mounts,
    "attached_devices": KERNEL_ROW_FIXTURE2.attached_devices,
    "resource_opts": KERNEL_ROW_FIXTURE2.resource_opts,
    "bootstrap_script": KERNEL_ROW_FIXTURE2.bootstrap_script,
    "kernel_host": KERNEL_ROW_FIXTURE2.kernel_host,
    "repl_in_port": KERNEL_ROW_FIXTURE2.repl_in_port,
    "repl_out_port": KERNEL_ROW_FIXTURE2.repl_out_port,
    "stdin_port": KERNEL_ROW_FIXTURE2.stdin_port,
    "stdout_port": KERNEL_ROW_FIXTURE2.stdout_port,
    "service_ports": KERNEL_ROW_FIXTURE2.service_ports,
    "preopen_ports": KERNEL_ROW_FIXTURE2.preopen_ports,
    "use_host_network": KERNEL_ROW_FIXTURE2.use_host_network,
    "created_at": KERNEL_ROW_FIXTURE2.created_at,
    "terminated_at": KERNEL_ROW_FIXTURE2.terminated_at,
    "starts_at": KERNEL_ROW_FIXTURE2.starts_at,
    "status": KERNEL_ROW_FIXTURE2.status.name,  # Use name instead of value for enum
    "status_changed": KERNEL_ROW_FIXTURE2.status_changed,
    "status_info": KERNEL_ROW_FIXTURE2.status_info,
    "status_data": KERNEL_ROW_FIXTURE2.status_data,
    "status_history": KERNEL_ROW_FIXTURE2.status_history,
    "callback_url": str(KERNEL_ROW_FIXTURE2.callback_url),
    "startup_command": KERNEL_ROW_FIXTURE2.startup_command,
    "result": KERNEL_ROW_FIXTURE2.result.name,
    "internal_data": KERNEL_ROW_FIXTURE2.internal_data,
    "container_log": KERNEL_ROW_FIXTURE2.container_log,
    "num_queries": KERNEL_ROW_FIXTURE2.num_queries,
    "last_stat": KERNEL_ROW_FIXTURE2.last_stat,
}

del SESSION_FIXTURE_DICT2["service_ports"]
del SESSION_FIXTURE_DICT2["owner"]

SESSION_FIXTURE_DICT2["status_history"] = {
    "history": [
        {"status": "PENDING", "timestamp": "2023-01-01T00:00:00Z"},
        {"status": "RUNNING", "timestamp": "2023-01-01T00:01:00Z"},
    ]
}
