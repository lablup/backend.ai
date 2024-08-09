import asyncio
import os
import secrets
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import aiodocker
import pytest

from ai.backend.agent.config import agent_local_config_iv
from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.logging import LocalLogger
from ai.backend.common.types import EtcdRedisConfig, HostPortPair
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    redis_container,
    sync_file_lock,
)
from ai.backend.testutils.pants import get_parallel_slot


@pytest.fixture(scope="session")
def test_id():
    return f"testing-{secrets.token_urlsafe(8)}"


@pytest.fixture(scope="session")
def logging_config():
    config = {
        "drivers": ["console"],
        "console": {"colored": None, "format": "verbose"},
        "level": "DEBUG",
        "pkg-ns": {
            "": "INFO",
            "ai.backend": "DEBUG",
            "tests": "DEBUG",
            "alembic": "INFO",
            "aiotools": "INFO",
            "aiohttp": "INFO",
            "sqlalchemy": "WARNING",
        },
    }
    logger = LocalLogger(config)
    with logger:
        yield config


@pytest.fixture(scope="session")
def local_config(test_id, logging_config, etcd_container, redis_container):  # noqa: F811
    ipc_base_path = Path.cwd() / f".tmp/{test_id}/agent-ipc"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    var_base_path = Path.cwd() / f".tmp/{test_id}/agent-var"
    var_base_path.mkdir(parents=True, exist_ok=True)
    etcd_addr = etcd_container[1]
    mount_path = Path.cwd() / "vfroot"

    registry_state_path = var_base_path / f"last_registry.{test_id}.dat"
    try:
        os.unlink(registry_state_path)
    except FileNotFoundError:
        pass

    cfg = {
        "agent": {
            "region": f"rg-{test_id}",
            "id": f"i-{test_id}",
            "scaling-group": f"sg-{test_id}",
            "ipc-base-path": ipc_base_path,
            "var-base-path": var_base_path,
            "mount-path": mount_path,
            "backend": "docker",
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
        "logging": logging_config,
        "debug": defaultdict(lambda: False),
        "etcd": {
            "addr": etcd_addr,
            "namespace": f"ns-{test_id}",
        },
        "redis": EtcdRedisConfig(
            addr=redis_container[1],
            sentinel=None,
            service_name=None,
            password=None,
            redis_helper_config=config.redis_helper_default_config,
        ),
        "plugins": {},
    }
    cfg = agent_local_config_iv.check(cfg)

    def _override_if_exists(src: dict, dst: dict, key: str) -> None:
        sentinel = object()
        if (val := src.get(key, sentinel)) is not sentinel:
            dst[key] = val

    try:
        # Override external database config with the current environment's config.
        fs_local_config, cfg_src_path = config.read_from_file(None, "agent")
        cfg["etcd"]["addr"] = fs_local_config["etcd"]["addr"]
        _override_if_exists(fs_local_config["etcd"], cfg["etcd"], "user")
        _override_if_exists(fs_local_config["etcd"], cfg["etcd"], "password")
    except config.ConfigurationError:
        pass
    yield cfg
    shutil.rmtree(ipc_base_path)
    try:
        os.unlink(registry_state_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session", autouse=True)
def test_local_instance_id(session_mocker, test_id):
    mock_generate_local_instance_id = session_mocker.patch(
        "ai.backend.agent.agent.generate_local_instance_id",
    )
    mock_generate_local_instance_id.return_value = f"i-{test_id}"
    yield


@pytest.fixture(scope="session")
def prepare_images():
    async def pull():
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
def socket_relay_image():
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
async def docker():
    docker = aiodocker.Docker()
    try:
        yield docker
    finally:
        await docker.close()


@pytest.fixture
async def create_container(test_id, docker):
    container = None
    cont_id = secrets.token_urlsafe(4)

    async def _create_container(config):
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
