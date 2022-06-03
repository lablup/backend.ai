import asyncio
import os
import secrets
import shutil
from collections import defaultdict
from pathlib import Path

from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.types import EtcdRedisConfig, HostPortPair
from ai.backend.testutils.bootstrap import etcd_container, redis_container  # noqa: F401
from ai.backend.testutils.pants import get_parallel_slot

import aiodocker
import pytest


@pytest.fixture(scope='session')
def test_id():
    return f'testing-{secrets.token_urlsafe(8)}'


@pytest.fixture(scope='session')
def local_config(test_id, etcd_container, redis_container):  # noqa: F811
    # ipc_base_path = Path.cwd() / f'tmp/backend.ai/ipc-{test_id}'
    ipc_base_path = Path.cwd() / f'ipc/ipc-{test_id}'
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    etcd_addr = etcd_container[1]

    cfg = {
        'agent': {
            'region': f"rg-{test_id}",
            'id': f"i-{test_id}",
            'scaling-group': f"sg-{test_id}",
            'ipc-base-path': ipc_base_path,
            'backend': 'docker',
            'rpc-listen-addr': HostPortPair('', 6001),
            'agent-sock-port': 6009,
        },
        'container': {
            'scratch-type': 'hostdir',
            'stats-type': 'docker',
            'port-range': [
                19000 + 200 * get_parallel_slot(),
                19200 + 200 * get_parallel_slot(),
            ],
        },
        'resource': {
            'reserved-cpu': 1,
            'reserved-mem': tx.BinarySize().check('256M'),
            'reserved-disk': tx.BinarySize().check('1G'),
        },
        'logging': {},
        'debug': defaultdict(lambda: False),
        'etcd': {
            'addr': etcd_addr,
            'namespace': f'ns-{test_id}',
        },
        'redis': EtcdRedisConfig(
            addr=redis_container[1],
            sentinel=None,
            service_name=None,
            password=None,
        ),
        'plugins': {},
    }

    def _override_if_exists(src: dict, dst: dict, key: str) -> None:
        sentinel = object()
        if (val := src.get(key, sentinel)) is not sentinel:
            dst[key] = val

    try:
        # Override external database config with the current environment's config.
        fs_local_config, cfg_src_path = config.read_from_file(None, 'agent')
        cfg['etcd']['addr'] = fs_local_config['etcd']['addr']
        _override_if_exists(fs_local_config['etcd'], cfg['etcd'], 'user')
        _override_if_exists(fs_local_config['etcd'], cfg['etcd'], 'password')
    except config.ConfigurationError:
        pass
    yield cfg
    shutil.rmtree(ipc_base_path)


@pytest.fixture(scope='session', autouse=True)
def test_local_instance_id(local_config, session_mocker, test_id):
    ipc_base_path = local_config['agent']['ipc-base-path']
    registry_state_path = ipc_base_path / f'last_registry.{test_id}.dat'
    try:
        os.unlink(registry_state_path)
    except FileNotFoundError:
        pass
    mock_generate_local_instance_id = session_mocker.patch(
        'ai.backend.agent.agent.generate_local_instance_id',
    )
    mock_generate_local_instance_id.return_value = f"i-{test_id}"
    yield
    try:
        os.unlink(registry_state_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope='session')
def prepare_images():

    async def pull():
        docker = aiodocker.Docker()
        images_to_pull = [
            'alpine:3.8',
            'nginx:1.17-alpine',
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
        if 'no current event loop' not in str(exc):
            raise
    try:
        asyncio.run(pull())
    finally:
        asyncio.set_event_loop(old_loop)


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
            name=f'kernel.{test_id}-{cont_id}',
        )
        return container

    try:
        yield _create_container
    finally:
        if container is not None:
            await container.delete(force=True)
