import asyncio
import contextlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
from typing import (
    AsyncIterator,
    Optional,
    Tuple,
)
import aiohttp

import async_timeout
import pytest

from ai.backend.testutils.pants import get_parallel_slot

from .types import (
    AbstractRedisSentinelCluster,
    AbstractRedisNode,
    RedisClusterInfo,
)
from .utils import simple_run_cmd


class DockerRedisNode(AbstractRedisNode):

    def __init__(self, node_type: str, port: int, container_id: str) -> None:
        self.node_type = node_type
        self.port = port + get_parallel_slot() * 10
        self.container_id = container_id

    @property
    def addr(self) -> Tuple[str, int]:
        return ('127.0.0.1', self.port)

    def __str__(self) -> str:
        return f"DockerRedisNode(cid:{self.container_id[:12]})"

    async def pause(self) -> None:
        assert self.container_id is not None
        print(f"Docker container {self.container_id[:12]} is being paused...")
        await simple_run_cmd(
            ['docker', 'pause', self.container_id],
            # stdout=asyncio.subprocess.DEVNULL,
            # stderr=asyncio.subprocess.DEVNULL,
        )
        print(f"Docker container {self.container_id[:12]} is paused")

    async def unpause(self) -> None:
        assert self.container_id is not None
        await simple_run_cmd(
            ['docker', 'unpause', self.container_id],
            # stdout=asyncio.subprocess.DEVNULL,
            # stderr=asyncio.subprocess.DEVNULL,
        )
        print(f"Docker container {self.container_id[:12]} is unpaused")

    async def stop(self, force_kill: bool = False) -> None:
        assert self.container_id is not None
        if force_kill:
            await simple_run_cmd(
                ['docker', 'kill', self.container_id],
                # stdout=asyncio.subprocess.DEVNULL,
                # stderr=asyncio.subprocess.DEVNULL,
            )
            print(f"Docker container {self.container_id[:12]} is killed")
        else:
            await simple_run_cmd(
                ['docker', 'stop', self.container_id],
                # stdout=asyncio.subprocess.DEVNULL,
                # stderr=asyncio.subprocess.DEVNULL,
            )
            print(f"Docker container {self.container_id[:12]} is terminated")

    async def start(self) -> None:
        assert self.container_id is not None
        await simple_run_cmd(
            ['docker', 'start', self.container_id],
            # stdout=asyncio.subprocess.DEVNULL,
            # stderr=asyncio.subprocess.DEVNULL,
        )
        print(f"Docker container {self.container_id[:12]} started")


async def is_snap_docker():
    if not Path('/run/snapd.socket').is_socket():
        return False
    async with aiohttp.ClientSession(connector=aiohttp.UnixConnector(path='/run/snapd.socket')) as conn:
        async with conn.get('unix://localhost/v2/snaps?names=docker') as resp:
            if resp.status != 200:
                return False
            try:
                data = await resp.json()
                for pkg_data in data['result']:
                    if pkg_data['name'] == 'docker':
                        return True
                return False
            except KeyError:
                return False


class DockerComposeRedisSentinelCluster(AbstractRedisSentinelCluster):

    async def probe_docker_compose(self) -> list[str]:
        # Try v2 first and fallback to v1
        p = await asyncio.create_subprocess_exec(
            'docker', 'compose', 'version',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        exit_code = await p.wait()
        if exit_code == 0:
            compose_cmd = ['docker', 'compose']
        else:
            compose_cmd = ['docker-compose']
        return compose_cmd

    @contextlib.asynccontextmanager
    async def make_cluster(self) -> AsyncIterator[RedisClusterInfo]:
        cfg_dir = Path(__file__).parent
        compose_cfg = cfg_dir / 'redis-cluster.yml'
        project_name = f"{self.test_ns}_{self.test_case_ns}"
        compose_cmd = await self.probe_docker_compose()

        snap_compose_dir: Optional[Path] = None

        if await is_snap_docker():  # FIXME: Remove this after we find out how to change pytest rootdir
            files = [
                'redis-cluster.yml',
                'redis-sentinel.dockerfile',
                'sentinel.conf',
            ]
            snap_compose_dir = Path.home() / 'tmp' / f'bai-redis-test-{get_parallel_slot()}'

            def _copy_files():
                nonlocal cfg_dir
                if snap_compose_dir.exists():
                    shutil.rmtree(snap_compose_dir)
                snap_compose_dir.mkdir(parents=True)

                for file in files:
                    shutil.copy(cfg_dir / file, snap_compose_dir)

            await asyncio.get_running_loop().run_in_executor(None, _copy_files)
            compose_cfg = snap_compose_dir / 'redis-cluster.yml'

        ports = {
            'REDIS_MASTER_PORT': 16379 + get_parallel_slot() * 10,
            'REDIS_SLAVE1_PORT': 16380 + get_parallel_slot() * 10,
            'REDIS_SLAVE2_PORT': 16381 + get_parallel_slot() * 10,
            'REDIS_SENTINEL1_PORT': 26379 + get_parallel_slot() * 10,
            'REDIS_SENTINEL2_PORT': 26380 + get_parallel_slot() * 10,
            'REDIS_SENTINEL3_PORT': 26381 + get_parallel_slot() * 10,
        }
        os.environ.update({k: str(v) for k, v in ports.items()})

        async with async_timeout.timeout(30.0):
            p = await simple_run_cmd([
                *compose_cmd,
                '-p', project_name,
                '-f', os.fsencode(compose_cfg),
                'up', '-d', '--build',
            ], stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            assert p.returncode == 0, "Compose cluster creation has failed."

        await asyncio.sleep(0.2)
        try:
            p = await asyncio.create_subprocess_exec(
                *[
                    *compose_cmd,
                    '-p', project_name,
                    '-f', str(compose_cfg),
                    'ps',
                    '--format', 'json',
                ],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            assert p.stdout is not None
            try:
                ps_output = json.loads(await p.stdout.read())
            except json.JSONDecodeError:
                pytest.fail("Cannot parse \"docker compose ... ps --format json\" output. "
                            "You may need to upgrade to docker-compose v2.0.0.rc.3 or later")
            await p.wait()
            worker_cids = {}
            sentinel_cids = {}

            def find_port_node(item):
                if m := re.search(r"--port (\d+) ", item['Command']):
                    return int(m.group(1))
                return None

            def find_port_sentinel(item):
                if m := re.search(r"redis-sentinel(\d+)", item['Name']):
                    return 26379 + (int(m.group(1)) - 1)
                return None

            if not ps_output:
                pytest.fail("Cannot detect the temporary Redis cluster running as docker compose containers")
            for item in ps_output:
                if 'redis-node' in item['Name']:
                    port = find_port_node(item)
                    worker_cids[port] = item['ID']
                elif 'redis-sentinel' in item['Name']:
                    port = find_port_sentinel(item)
                    sentinel_cids[port] = item['ID']

            yield RedisClusterInfo(
                node_addrs=[
                    ('127.0.0.1', ports['REDIS_MASTER_PORT']),
                    ('127.0.0.1', ports['REDIS_SLAVE1_PORT']),
                    ('127.0.0.1', ports['REDIS_SLAVE2_PORT']),
                ],
                nodes=[
                    DockerRedisNode(
                        "node",
                        ports['REDIS_MASTER_PORT'],
                        worker_cids[ports['REDIS_MASTER_PORT']]
                    ),
                    DockerRedisNode(
                        "node",
                        ports['REDIS_SLAVE1_PORT'],
                        worker_cids[ports['REDIS_SLAVE1_PORT']]
                    ),
                    DockerRedisNode(
                        "node",
                        ports['REDIS_SLAVE2_PORT'],
                        worker_cids[ports['REDIS_SLAVE2_PORT']]
                    ),
                ],
                sentinel_addrs=[
                    ('127.0.0.1', ports['REDIS_SENTINEL1_PORT']),
                    ('127.0.0.1', ports['REDIS_SENTINEL2_PORT']),
                    ('127.0.0.1', ports['REDIS_SENTINEL3_PORT']),
                ],
                sentinels=[
                    DockerRedisNode(
                        "sentinel",
                        ports['REDIS_SENTINEL1_PORT'],
                        sentinel_cids[ports['REDIS_SENTINEL1_PORT']]
                    ),
                    DockerRedisNode(
                        "sentinel",
                        ports['REDIS_SENTINEL2_PORT'],
                        sentinel_cids[ports['REDIS_SENTINEL2_PORT']]
                    ),
                    DockerRedisNode(
                        "sentinel",
                        ports['REDIS_SENTINEL3_PORT'],
                        sentinel_cids[ports['REDIS_SENTINEL3_PORT']]
                    ),
                ],
            )
        finally:
            await asyncio.sleep(0.2)
            async with async_timeout.timeout(30.0):
                await simple_run_cmd([
                    *compose_cmd,
                    '-p', project_name,
                    '-f', os.fsencode(compose_cfg),
                    'down',
                ], stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await asyncio.sleep(0.2)


async def main():
    loop = asyncio.get_running_loop()

    async def redis_task():
        native_cluster = DockerComposeRedisSentinelCluster("testing", "testing-main", "develove", "testing")
        async with native_cluster.make_cluster():
            while True:
                await asyncio.sleep(10)

    t = asyncio.create_task(redis_task())
    loop.add_signal_handler(signal.SIGINT, t.cancel)
    loop.add_signal_handler(signal.SIGTERM, t.cancel)
    try:
        await t
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        print("Terminated.")
