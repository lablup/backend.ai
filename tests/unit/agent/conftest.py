import asyncio
import os
import secrets
import shutil
import subprocess
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import aiodocker
import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.agent.runtime import AgentRuntime
from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.types import AgentId, HostPortPair
from ai.backend.logging import LocalLogger
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat, LogLevel
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    redis_container,
    sync_file_lock,
)
from ai.backend.testutils.pants import get_parallel_slot


@pytest.fixture(scope="session")
def test_id() -> str:
    return f"testing-{secrets.token_urlsafe(8)}"


@pytest.fixture(scope="session")
def logging_config() -> Generator[LoggingConfig, None, None]:
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
    logging_config: LoggingConfig,
    etcd_container: tuple[object, object],  # noqa: F811
    redis_container: tuple[object, object],  # noqa: F811
) -> Generator[AgentUnifiedConfig, None, None]:
    ipc_base_path = Path.cwd() / f".tmp/{test_id}/agent-ipc"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    var_base_path = Path.cwd() / f".tmp/{test_id}/agent-var"
    var_base_path.mkdir(parents=True, exist_ok=True)
    etcd_addr = etcd_container[1]
    redis_addr = redis_container[1]
    mount_path = Path.cwd() / "vfroot"

    registry_state_path = var_base_path / f"last_registry.{test_id}.dat"
    try:
        os.unlink(registry_state_path)
    except FileNotFoundError:
        pass

    raw_server_config = {
        "agent": {
            "region": f"rg-{test_id}",
            "id": f"i-{test_id}",
            "scaling-group": f"sg-{test_id}",
            "ipc-base-path": ipc_base_path,
            "var-base-path": var_base_path,
            "mount-path": mount_path,
            "backend": "dummy",
            "rpc-listen-addr": HostPortPair("", 18100 + get_parallel_slot()),
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
        server_config.etcd.addr = fs_local_config["etcd"]["addr"]
        _override_if_exists(fs_local_config["etcd"], server_config.etcd.model_dump(), "user")
        _override_if_exists(fs_local_config["etcd"], server_config.etcd.model_dump(), "password")
    except config.ConfigurationError:
        pass
    yield server_config
    shutil.rmtree(ipc_base_path)
    try:
        os.unlink(registry_state_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session", autouse=True)
def test_local_instance_id(
    session_mocker: MockerFixture, test_id: str
) -> Generator[None, None, None]:
    mock_generate_local_instance_id = session_mocker.patch(
        "ai.backend.agent.agent.generate_local_instance_id",
    )
    mock_generate_local_instance_id.return_value = f"i-{test_id}"
    yield


@pytest.fixture(scope="session")
def prepare_images() -> None:
    async def pull() -> None:
        docker = aiodocker.Docker()
        images_to_pull = [
            "alpine:3.8",
            "nginx:1.17-alpine",
        ]
        for img in images_to_pull:
            try:
                await docker.images.inspect(img)
            except aiodocker.exceptions.DockerError as e:
                assert e.status == 404
                print(f'Pulling image "{img}" for testing...')
                await docker.pull(img)
        await docker.close()

    # We need to preserve the current loop configured by pytest-asyncio
    # because asyncio.run() calls asyncio.set_event_loop(None) upon its completion.
    # Here we cannot just use "event_loop" fixture because this fixture
    # is session-scoped and pytest does not allow calling function-scoped fixtuers
    # from session-scoped fixtures.
    try:
        old_loop = asyncio.get_event_loop()
    except RuntimeError as exc:
        if "no current event loop" not in str(exc):
            raise
    try:
        asyncio.run(pull())
    finally:
        asyncio.set_event_loop(old_loop)


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


@pytest.fixture
async def docker() -> AsyncIterator[aiodocker.Docker]:
    docker = aiodocker.Docker()
    try:
        yield docker
    finally:
        await docker.close()


@pytest.fixture
async def create_container(
    test_id: str, docker: aiodocker.Docker
) -> AsyncIterator[Callable[[dict[str, Any]], Any]]:
    container = None
    cont_id = secrets.token_urlsafe(4)

    async def _create_container(config: dict[str, Any]) -> Any:
        nonlocal container
        container = await docker.containers.create_or_replace(
            config=config,
            name=f"kernel.{test_id}-{cont_id}",
        )
        return container

    try:
        yield _create_container
    finally:
        if container is not None:
            await container.delete(force=True)


@pytest.fixture
async def agent_runtime(
    local_config: AgentUnifiedConfig,
    mocker: object,
) -> AsyncIterator[AgentRuntime]:
    """
    Create a mocked AgentRuntime instance for unit testing.

    This fixture provides a minimal AgentRuntime with:
    - Mocked agents and resource allocator
    - No real backend or resource loading
    - Proper cleanup after tests
    """
    # Create mock agents
    mock_agent_id = AgentId(local_config.agent.defaulted_id)
    mock_agent = AsyncMock(spec=AbstractAgent)
    mock_agent.id = mock_agent_id
    mock_agent.shutdown = AsyncMock()

    # Create mock etcd view
    mock_etcd_view = Mock()

    # Create mock resource allocator
    mock_resource_allocator = AsyncMock()
    mock_resource_allocator.__aexit__ = AsyncMock()

    # Create runtime using constructor directly (not create_runtime)
    runtime = AgentRuntime(
        local_config=local_config,
        etcd_views={mock_agent_id: mock_etcd_view},
        agents={mock_agent_id: mock_agent},
        primary_agent=mock_agent,
        kernel_registry=KernelRegistry(),
        resource_allocator=mock_resource_allocator,
        metadata_server=None,
    )

    try:
        yield runtime
    finally:
        await runtime.__aexit__(None, None, None)
