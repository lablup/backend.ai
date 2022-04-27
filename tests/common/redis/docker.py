import asyncio
import contextlib
import json
import os
from pathlib import Path
import re
import signal
from typing import (
    AsyncIterator,
    Tuple,
)

import async_timeout
import pytest

from .types import (
    AbstractRedisSentinelCluster,
    AbstractRedisNode,
    RedisClusterInfo,
)
from .utils import simple_run_cmd


class DockerRedisNode(AbstractRedisNode):

    def __init__(self, node_type: str, port: int, container_id: str) -> None:
        self.node_type = node_type
        self.port = port
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
                    ('127.0.0.1', 16379),
                    ('127.0.0.1', 16380),
                    ('127.0.0.1', 16381),
                ],
                nodes=[
                    DockerRedisNode("node", 16379, worker_cids[16379]),
                    DockerRedisNode("node", 16380, worker_cids[16380]),
                    DockerRedisNode("node", 16381, worker_cids[16381]),
                ],
                sentinel_addrs=[
                    ('127.0.0.1', 26379),
                    ('127.0.0.1', 26380),
                    ('127.0.0.1', 26381),
                ],
                sentinels=[
                    DockerRedisNode("sentinel", 26379, sentinel_cids[26379]),
                    DockerRedisNode("sentinel", 26380, sentinel_cids[26380]),
                    DockerRedisNode("sentinel", 26381, sentinel_cids[26381]),
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
