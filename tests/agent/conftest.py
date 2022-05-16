import asyncio
import json
import os
import time
import secrets
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.types import HostPortPair
from ai.backend.agent import config as agent_config

import aiodocker
import pytest


@pytest.fixture(scope='session')
def backend_type():
    # TODO: change by environment/tox?
    return 'docker'


@pytest.fixture(scope='session')
def test_id():
    return f'testing-{secrets.token_urlsafe(8)}'


@pytest.fixture(scope='session')
def local_config(test_id, redis_container):
    # ipc_base_path = Path.cwd() / f'tmp/backend.ai/ipc-{test_id}'
    ipc_base_path = Path.cwd() / f'ipc/ipc-{test_id}'
    ipc_base_path.mkdir(parents=True, exist_ok=True)

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
            'port-range': [19000, 19200],
        },
        'resource': {
            'reserved-cpu': 1,
            'reserved-mem': tx.BinarySize().check('256M'),
            'reserved-disk': tx.BinarySize().check('1G'),
        },
        'logging': {},
        'debug': defaultdict(lambda: False),
        'etcd': {
            'addr': HostPortPair('127.0.0.1', 2379),
            'namespace': f'ns-{test_id}',
        },
        'redis': redis_container,
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
def prepare_images(backend_type):

    async def pull():
        if backend_type == 'docker':
            docker = aiodocker.Docker()
            images_to_pull = [
                'alpine:3.8',
                'nginx:1.17-alpine',
                'redis:5.0.5-alpine',
            ]
            for img in images_to_pull:
                try:
                    await docker.images.inspect(img)
                except aiodocker.exceptions.DockerError as e:
                    assert e.status == 404
                    print(f'Pulling image "{img}" for testing...')
                    await docker.pull(img)
            await docker.close()
        elif backend_type == 'k8s':
            raise NotImplementedError

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


@pytest.fixture(scope='session')
def redis_container(test_id, backend_type, prepare_images):
    if backend_type == 'docker':
        subprocess.run([
            'docker', 'run',
            '-d',
            '-P',
            '--name', f'{test_id}.redis',
            'redis:5.0.5-alpine',
        ], capture_output=True)
        proc = subprocess.run([
            'docker', 'inspect',
            f'{test_id}.redis',
        ], capture_output=True)
        container_info = json.loads(proc.stdout)
        host_port = int(container_info[0]['NetworkSettings']['Ports']['6379/tcp'][0]['HostPort'])
    elif backend_type == 'k8s':
        raise NotImplementedError

    try:
        yield {
            'addr': HostPortPair('localhost', host_port),
            'password': None,
        }
    finally:
        if backend_type == 'docker':
            subprocess.run([
                'docker', 'rm',
                '-f',
                f'{test_id}.redis',
            ], capture_output=True)
        elif backend_type == 'k8s':
            raise NotImplementedError


@pytest.fixture
async def create_container(test_id, backend_type, docker):
    container = None
    cont_id = secrets.token_urlsafe(4)

    if backend_type == 'docker':
        async def _create_container(config):
            nonlocal container
            container = await docker.containers.create_or_replace(
                config=config,
                name=f'kernel.{test_id}-{cont_id}',
            )
            return container
    elif backend_type == 'k8s':
        raise NotImplementedError

    try:
        yield _create_container
    finally:
        if container is not None:
            await container.delete(force=True)
