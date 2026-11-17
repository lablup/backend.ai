from __future__ import annotations

import os
import secrets
import shutil
import signal
import subprocess
from collections import defaultdict
from collections.abc import Generator, Mapping
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.agent import AgentClass
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior, HostPortPair
from ai.backend.logging import LocalLogger
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat, LogLevel
from ai.backend.testutils.bootstrap import ETCD_PASSWORD, ETCD_USER, sync_file_lock
from ai.backend.testutils.pants import get_parallel_slot


@pytest.fixture(scope="session")
def logging_config() -> Generator[LoggingConfig]:
    config = LoggingConfig(
        version=1,
        disable_existing_loggers=False,
        handlers={},
        loggers={},
        drivers=[LogDriver.CONSOLE],
        console=ConsoleConfig(
            colored=None,
            format=LogFormat.VERBOSE,
        ),
        file=None,
        logstash=None,
        graylog=None,
        level=LogLevel.DEBUG,
        pkg_ns={
            "": LogLevel.INFO,
            "ai.backend": LogLevel.DEBUG,
            "tests": LogLevel.DEBUG,
            "alembic": LogLevel.INFO,
            "aiotools": LogLevel.INFO,
            "aiohttp": LogLevel.INFO,
            "sqlalchemy": LogLevel.WARNING,
        },
    )
    logger = LocalLogger(config)
    with logger:
        yield config


@pytest.fixture(scope="session")
def local_config(
    test_id: str,
    rpc_auth_key_config: dict[str, Path],
    logging_config: LoggingConfig,
    etcd_container: tuple[object, object],
    redis_container: tuple[object, object],
) -> Generator[AgentUnifiedConfig]:
    ipc_base_path = Path.cwd() / f".tmp/{test_id}/agent-ipc"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    var_base_path = Path.cwd() / f".tmp/{test_id}/agent-var"
    var_base_path.mkdir(parents=True, exist_ok=True)
    etcd_addr = etcd_container[1]
    redis_addr = redis_container[1]
    mount_path = Path.cwd() / "vfroot"

    raw_server_config = {
        "agent": {
            "region": f"rg-{test_id}",
            "id": f"i-{test_id}",
            "initial-resource-group-name": f"sg-{test_id}",
            "ipc-base-path": ipc_base_path,
            "var-base-path": var_base_path,
            "mount-path": mount_path,
            "backend": "dummy",
            "rpc-listen-addr": HostPortPair("", 18100 + get_parallel_slot()),
            **rpc_auth_key_config,
            "agent-sock-port": 18200 + get_parallel_slot(),
            "metadata-server-bind-host": "0.0.0.0",
            "metadata-server-port": 18300 + get_parallel_slot(),
            "allow-compute-plugins": set(),
            "block-compute-plugins": set(),
        },
        "container": {
            "scratch-type": "hostdir",
            "stats-type": "docker",
            "port-range": [
                19000 + 200 * get_parallel_slot(),
                19200 + 200 * get_parallel_slot(),
            ],
            "bind-host": "127.0.0.1",
        },
        "resource": {
            "reserved-cpu": 1,
            "reserved-mem": tx.BinarySize().check("256M"),
            "reserved-disk": tx.BinarySize().check("1G"),
        },
        "pyroscope": {
            "enabled": False,
            "app-name": "backend.ai-test",
            "server-addr": "http://localhost:4040",
            "sample-rate": 100,
        },
        "logging": logging_config,
        "debug": defaultdict(lambda: False),
        "etcd": {
            "addr": etcd_addr,
            "namespace": f"ns-{test_id}",
            "user": ETCD_USER,
            "password": ETCD_PASSWORD,
        },
        "redis": {
            "addr": redis_addr,
            "sentinel": None,
            "service_name": None,
            "password": None,
            "redis_helper_config": config.redis_helper_default_config,
        },
        "plugins": {},
    }
    server_config = AgentUnifiedConfig.model_validate(raw_server_config)

    def _override_if_exists(src: dict[str, Any], dst: dict[str, Any], key: str) -> None:
        sentinel = object()
        if (val := src.get(key, sentinel)) is not sentinel:
            dst[key] = val

    try:
        # Override external database config with the current environment's config.
        fs_local_config, cfg_src_path = config.read_from_file(None, "agent")
        server_config.etcd.addrs = EtcdConfig.model_validate(fs_local_config["etcd"]).addrs
        _override_if_exists(fs_local_config["etcd"], server_config.etcd.model_dump(), "user")
        _override_if_exists(fs_local_config["etcd"], server_config.etcd.model_dump(), "password")
    except config.ConfigurationError:
        pass
    yield server_config
    shutil.rmtree(ipc_base_path)


@pytest.fixture(scope="session")
def socket_relay_image() -> None:
    # Since pulling all LFS files takes too much GitHub storage bandwidth in CI,
    # we fetch the only required image for tests on demand.
    build_root = os.environ.get("BACKEND_BUILD_ROOT", os.getcwd())
    lock_path = Path("~/.cache/bai/testing/lfs-pull.lock").expanduser()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    image_path = (
        f"src/ai/backend/agent/docker/backendai-socket-relay.img.{DEFAULT_IMAGE_ARCH}.tar.gz"
    )
    already_fetched = False
    with sync_file_lock(lock_path):
        with open(image_path, "rb") as f:
            head = f.read(256)
            if not head.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                already_fetched = True
        if not already_fetched:
            proc = subprocess.Popen(["git", "lfs", "pull", "--include", image_path], cwd=build_root)
            try:
                proc.wait()
            except (KeyboardInterrupt, SystemExit):
                # This will trigger 'Filesystem changed during run' in pants and let it retry the test
                # after interrupting the test via SIGINT.
                # We need to wait until the git command to complete anyway.
                proc.wait()
                raise


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}


@pytest.fixture
async def agent(local_config: Any, test_id: str, mocker: Any, socket_relay_image: Any) -> Any:
    dummy_etcd = DummyEtcd()
    mocked_etcd_get_prefix = AsyncMock(return_value={})
    mocker.patch.object(dummy_etcd, "get_prefix", new=mocked_etcd_get_prefix)
    test_case_id = secrets.token_hex(8)
    kernel_registry = KernelRegistry()
    agent = await DockerAgent.new(
        dummy_etcd,
        local_config,
        stats_monitor=None,
        error_monitor=None,
        skip_initial_scan=True,
        agent_public_key=None,
        kernel_registry=kernel_registry,
        computers={},
        slots={},
        agent_class=AgentClass.PRIMARY,
        sentinel_monitors=SentinelMonitorSet([]),
    )  # for faster test iteration
    agent.local_instance_id = test_case_id  # use per-test private registry file
    try:
        yield agent
    finally:
        await agent.shutdown(signal.SIGTERM)


async def test_init(agent: DockerAgent, mocker: Any) -> None:
    print(agent)


imgref = ImageRef(
    name="lua",
    project="lablup",
    tag="5.3-alpine3.8",
    registry="index.docker.io",
    architecture=DEFAULT_IMAGE_ARCH,
    is_local=False,
)
query_digest = "sha256:b000000000000000000000000000000000000000000000000000000000000001"
digest_matching_image_info = {
    "Id": "sha256:b000000000000000000000000000000000000000000000000000000000000001",
    "RepoTags": [
        "lablup/lua:5.3-alpine3.8",
    ],
}
digest_mismatching_image_info = {
    "Id": "sha256:a000000000000000000000000000000000000000000000000000000000000002",
    "RepoTags": [
        "lablup/lua:5.3-alpine3.8",
    ],
}


async def test_auto_pull_digest_when_digest_matching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.DIGEST
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_digest_when_digest_mismatching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.DIGEST
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_digest_when_missing(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.DIGEST
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=HTTPStatus.NOT_FOUND,
            message="Simulated missing image",
        ),
    )
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_called_with(imgref.canonical)


async def test_auto_pull_tag_when_digest_matching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.TAG
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_tag_when_digest_mismatching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.TAG
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_tag_when_missing(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.TAG
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=HTTPStatus.NOT_FOUND,
            message="Simulated missing image",
        ),
    )
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_called_with(imgref.canonical)


async def test_auto_pull_none_when_digest_matching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.NONE
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_none_when_digest_mismatching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.NONE
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_none_when_missing(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.NONE
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=HTTPStatus.NOT_FOUND,
            message="Simulated missing image",
        ),
    )
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    with pytest.raises(ImageNotAvailable) as e:
        await agent.check_image(imgref, query_digest, behavior)
    assert e.value.args[0] is imgref
    inspect_mock.assert_called_with(imgref.canonical)
