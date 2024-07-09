import asyncio
import contextlib
import json
import os
import shutil
import signal
from pathlib import Path
from pprint import pprint
from typing import AsyncIterator, Tuple

import aiohttp
import pytest
from packaging.version import Version
from packaging.version import parse as parse_version

from ai.backend.testutils.bootstrap import get_next_tcp_port
from ai.backend.testutils.pants import get_parallel_slot

from .types import AbstractRedisNode, AbstractRedisSentinelCluster, RedisClusterInfo
from .utils import simple_run_cmd


async def check_if_port_is_clear(host, port):
    while True:
        try:
            async with asyncio.timeout(0.3):
                reader, writer = await asyncio.open_connection(host, port)
        except (ConnectionRefusedError, asyncio.TimeoutError):
            break
        else:
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(0.1)
            continue


class DockerRedisNode(AbstractRedisNode):
    def __init__(
        self,
        node_type: str,
        port: int,
        container_id: str,
        *,
        verbose: bool = False,
    ) -> None:
        self.node_type = node_type
        self.port = port
        self.container_id = container_id
        self.verbose = verbose
        self._cmd_opts = {}
        if not self.verbose:
            self._cmd_opts["stdout"] = asyncio.subprocess.DEVNULL
            self._cmd_opts["stderr"] = asyncio.subprocess.DEVNULL

    @property
    def addr(self) -> Tuple[str, int]:
        return ("127.0.0.1", self.port)

    def __str__(self) -> str:
        return f"DockerRedisNode(cid:{self.container_id[:12]})"

    async def pause(self) -> None:
        assert self.container_id is not None
        print(f"Docker container {self.container_id[:12]} is being paused...")
        p = await simple_run_cmd(["docker", "pause", self.container_id], **self._cmd_opts)
        await p.wait()
        print(f"Docker container {self.container_id[:12]} is paused")

    async def unpause(self) -> None:
        assert self.container_id is not None
        p = await simple_run_cmd(["docker", "unpause", self.container_id], **self._cmd_opts)
        await p.wait()
        print(f"Docker container {self.container_id[:12]} is unpaused")

    async def stop(self, force_kill: bool = False) -> None:
        assert self.container_id is not None
        if force_kill:
            p = await simple_run_cmd(["docker", "kill", self.container_id], **self._cmd_opts)
            await p.wait()
            print(f"Docker container {self.container_id[:12]} is killed")
        else:
            p = await simple_run_cmd(["docker", "stop", self.container_id], **self._cmd_opts)
            await p.wait()
            print(f"Docker container {self.container_id[:12]} is terminated")

    async def start(self) -> None:
        assert self.container_id is not None
        p = await simple_run_cmd(["docker", "start", self.container_id], **self._cmd_opts)
        await p.wait()
        print(f"Docker container {self.container_id[:12]} started")


async def is_snap_docker():
    if not Path("/run/snapd.socket").is_socket():
        return False
    async with aiohttp.ClientSession(
        connector=aiohttp.UnixConnector(path="/run/snapd.socket")
    ) as conn:
        async with conn.get("unix://localhost/v2/snaps?names=docker") as resp:
            if resp.status != 200:
                return False
            try:
                data = await resp.json()
                for pkg_data in data["result"]:
                    if pkg_data["name"] == "docker":
                        return True
                return False
            except KeyError:
                return False


class DockerComposeRedisSentinelCluster(AbstractRedisSentinelCluster):
    async def probe_docker_compose(self) -> tuple[tuple[str, ...], Version]:
        # Try v2 first and fallback to v1
        for compose_cmd in [("docker", "compose"), ("docker-compose",)]:
            try:
                p = await asyncio.create_subprocess_exec(
                    *compose_cmd,
                    "version",
                    "--format=json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                assert p.stdout is not None
                stdout = await p.stdout.read()
                version_data = json.loads(stdout)
                compose_version = parse_version(version_data["version"])
                exit_code = await p.wait()
                if exit_code == 0:
                    return compose_cmd, compose_version
            except FileNotFoundError:
                continue
        else:
            raise RuntimeError("Could not detect the docker compose version")

    @contextlib.asynccontextmanager
    async def make_cluster(self) -> AsyncIterator[RedisClusterInfo]:
        template_cfg_dir = Path(__file__).parent
        template_compose_file = template_cfg_dir / "redis-cluster.yml"
        assert template_compose_file.exists()
        project_name = f"{self.test_ns}_{self.test_case_ns}"
        compose_cmd, compose_version = await self.probe_docker_compose()

        template_cfg_files = [
            "redis-cluster.yml",
            "sentinel.conf",
        ]
        compose_cfg_dir = (
            Path.home() / ".cache" / "bai" / "testing" / f"bai-redis-test-{get_parallel_slot()}"
        )
        allocated_ports = get_next_tcp_port(6)
        ports = {
            "REDIS_MASTER_PORT": allocated_ports[0],
            "REDIS_SLAVE1_PORT": allocated_ports[1],
            "REDIS_SLAVE2_PORT": allocated_ports[2],
            "REDIS_SENTINEL1_PORT": allocated_ports[3],
            "REDIS_SENTINEL2_PORT": allocated_ports[4],
            "REDIS_SENTINEL3_PORT": allocated_ports[5],
        }
        async with asyncio.TaskGroup() as tg:
            for port in ports.values():
                tg.create_task(check_if_port_is_clear("127.0.0.1", port))
        os.environ.update({k: str(v) for k, v in ports.items()})
        os.environ["COMPOSE_PATH"] = str(compose_cfg_dir)
        os.environ["DOCKER_USER"] = f"{os.getuid()}:{os.getgid()}"
        os.environ["NETWORK_NAME"] = f"testnet-{get_parallel_slot()}-{self.test_case_ns}"

        if compose_cfg_dir.exists():
            shutil.rmtree(compose_cfg_dir)
        compose_cfg_dir.mkdir(parents=True)
        for file in template_cfg_files:
            shutil.copy(template_cfg_dir / file, compose_cfg_dir)
        sentinel_tpl = (compose_cfg_dir / "sentinel.conf").read_text()
        sentinel_tpl = sentinel_tpl.replace("REDIS_PASSWORD", "develove")
        sentinel_tpl = sentinel_tpl.replace("REDIS_MASTER_HOST", "node01")
        sentinel_tpl = sentinel_tpl.replace("REDIS_MASTER_PORT", str(ports["REDIS_MASTER_PORT"]))
        sentinel01_cfg = sentinel_tpl.replace("REDIS_SENTINEL_SELF_HOST", "sentinel01")
        sentinel01_cfg = sentinel01_cfg.replace(
            "REDIS_SENTINEL_SELF_PORT", str(ports["REDIS_SENTINEL1_PORT"])
        )
        sentinel02_cfg = sentinel_tpl.replace("REDIS_SENTINEL_SELF_HOST", "sentinel02")
        sentinel02_cfg = sentinel02_cfg.replace(
            "REDIS_SENTINEL_SELF_PORT", str(ports["REDIS_SENTINEL2_PORT"])
        )
        sentinel03_cfg = sentinel_tpl.replace("REDIS_SENTINEL_SELF_HOST", "sentinel03")
        sentinel03_cfg = sentinel03_cfg.replace(
            "REDIS_SENTINEL_SELF_PORT", str(ports["REDIS_SENTINEL3_PORT"])
        )
        (compose_cfg_dir / "sentinel01.conf").write_text(sentinel01_cfg)
        (compose_cfg_dir / "sentinel02.conf").write_text(sentinel02_cfg)
        (compose_cfg_dir / "sentinel03.conf").write_text(sentinel03_cfg)

        compose_file = compose_cfg_dir / "redis-cluster.yml"

        async with asyncio.timeout(30.0):
            cmdargs = [
                *compose_cmd,
                "-p",
                project_name,
                "-f",
                str(compose_file),
                "up",
                "-d",
            ]
            p = await simple_run_cmd(
                cmdargs,
                env=os.environ,
                cwd=compose_cfg_dir,
            )
            await p.wait()
            assert p.returncode == 0, "Compose cluster creation has failed."

        await asyncio.sleep(1.0)
        try:
            p = await simple_run_cmd(
                [
                    *compose_cmd,
                    "-p",
                    project_name,
                    "-f",
                    str(compose_file),
                    "ps",
                    "-a",
                    "--format",
                    "json",
                ],
                cwd=compose_cfg_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                assert p.stdout is not None
                ps_output = []
                if compose_version >= Version("2.21.0"):
                    # Adapt to a breaking change in docker/compose#10918!
                    # Fortunately we only use the "ID" field from each container object.
                    while True:
                        line = await p.stdout.readline()
                        if not line:
                            break
                        ps_output.append(json.loads(line))
                else:
                    ps_output = json.loads(await p.stdout.read())
                pprint(f"{ps_output=}")
            except json.JSONDecodeError:
                pytest.fail(
                    'Cannot parse "docker compose ... ps --format json" output. '
                    "You may need to upgrade to docker-compose v2.0.0.rc.3 or later"
                )
            finally:
                await p.wait()

            if not ps_output:
                pytest.fail(
                    "Cannot detect the temporary Redis cluster running as docker compose containers"
                )

            cids = [item["ID"] for item in ps_output]
            cid_mapping = {}

            p = await simple_run_cmd(
                [
                    "docker",
                    "inspect",
                    *cids,
                ],
                cwd=compose_cfg_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                assert p.stdout is not None
                inspect_output = json.loads(await p.stdout.read())
            except json.JSONDecodeError:
                pytest.fail(
                    'Cannot parse "docker inspect ..." output. '
                    "You may need to upgrade to docker-compose v2.0.0.rc.3 or later"
                )
            finally:
                await p.wait()

            if not inspect_output:
                pytest.fail(
                    "Cannot detect Redis cluster containers running as docker compose containers"
                )

            for container in inspect_output:
                cid_mapping[container["Config"]["Labels"]["com.docker.compose.service"]] = (
                    container["Id"]
                )
                if self.verbose:
                    print(f"--- logs of {container['Id']} ---")
                    try:
                        p = await simple_run_cmd(["docker", "logs", container["Id"]])
                    finally:
                        await p.wait()
                    print("--- end of logs ---")
            print(f"{cids=}")
            print(f"{cid_mapping=}")

            yield RedisClusterInfo(
                node_addrs=[
                    ("127.0.0.1", ports["REDIS_MASTER_PORT"]),
                    ("127.0.0.1", ports["REDIS_SLAVE1_PORT"]),
                    ("127.0.0.1", ports["REDIS_SLAVE2_PORT"]),
                ],
                nodes=[
                    DockerRedisNode(
                        "node",
                        ports["REDIS_MASTER_PORT"],
                        cid_mapping["backendai-half-redis-node01"],
                        verbose=self.verbose,
                    ),
                    DockerRedisNode(
                        "node",
                        ports["REDIS_SLAVE1_PORT"],
                        cid_mapping["backendai-half-redis-node02"],
                        verbose=self.verbose,
                    ),
                    DockerRedisNode(
                        "node",
                        ports["REDIS_SLAVE2_PORT"],
                        cid_mapping["backendai-half-redis-node03"],
                        verbose=self.verbose,
                    ),
                ],
                sentinel_addrs=[
                    ("127.0.0.1", ports["REDIS_SENTINEL1_PORT"]),
                    ("127.0.0.1", ports["REDIS_SENTINEL2_PORT"]),
                    ("127.0.0.1", ports["REDIS_SENTINEL3_PORT"]),
                ],
                sentinels=[
                    DockerRedisNode(
                        "sentinel",
                        ports["REDIS_SENTINEL1_PORT"],
                        cid_mapping["backendai-half-redis-sentinel01"],
                        verbose=self.verbose,
                    ),
                    DockerRedisNode(
                        "sentinel",
                        ports["REDIS_SENTINEL2_PORT"],
                        cid_mapping["backendai-half-redis-sentinel02"],
                        verbose=self.verbose,
                    ),
                    DockerRedisNode(
                        "sentinel",
                        ports["REDIS_SENTINEL3_PORT"],
                        cid_mapping["backendai-half-redis-sentinel03"],
                        verbose=self.verbose,
                    ),
                ],
            )
        finally:
            await asyncio.sleep(0.2)
            async with asyncio.timeout(30.0):
                p = await simple_run_cmd(
                    [
                        *compose_cmd,
                        "-p",
                        project_name,
                        "-f",
                        str(compose_file),
                        "down",
                        "-v",
                    ],
                    cwd=compose_cfg_dir,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await p.wait()
            async with asyncio.TaskGroup() as tg:
                for port in ports.values():
                    tg.create_task(check_if_port_is_clear("127.0.0.1", port))


async def main():
    loop = asyncio.get_running_loop()

    async def redis_task():
        native_cluster = DockerComposeRedisSentinelCluster(
            "testing", "testing-main", "develove", "testing"
        )
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
