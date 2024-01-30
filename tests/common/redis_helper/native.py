from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import textwrap
from pathlib import Path
from typing import AsyncIterator, Sequence, Tuple

from ai.backend.testutils.pants import get_parallel_slot

from .types import AbstractRedisNode, AbstractRedisSentinelCluster, RedisClusterInfo


class NativeRedisNode(AbstractRedisNode):
    proc: asyncio.subprocess.Process | None

    def __init__(self, node_type: str, port: int, start_args: Sequence[str | bytes]) -> None:
        self.node_type = node_type
        self.port = port + get_parallel_slot() * 10
        self.start_args = start_args
        self.proc = None

    @property
    def addr(self) -> Tuple[str, int]:
        return ("127.0.0.1", self.port)

    def __str__(self) -> str:
        if self.proc is None:
            return "NativeRedisNode(not-running)"
        return f"NativeRedisNode(pid:{self.proc.pid})"

    async def pause(self) -> None:
        assert self.proc is not None
        self.proc.send_signal(signal.SIGSTOP)
        await asyncio.sleep(0)

    async def unpause(self) -> None:
        assert self.proc is not None
        self.proc.send_signal(signal.SIGCONT)
        await asyncio.sleep(0)

    async def stop(self, force_kill: bool = False) -> None:
        assert self.proc is not None
        try:
            if force_kill:
                self.proc.kill()
            else:
                self.proc.terminate()
            exit_code = await self.proc.wait()
            print(
                f"Redis {self.node_type} (pid:{self.proc.pid}) has terminated with exit code"
                f" {exit_code}."
            )
        except ProcessLookupError:
            print(f"Redis {self.node_type} (pid:{self.proc.pid}) already terminated")
        finally:
            self.proc = None

    async def start(self) -> None:
        assert self.proc is None
        self.proc = await asyncio.create_subprocess_exec(
            *self.start_args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,  # prevent signal propagation
        )
        print(f"Redis {self.node_type} (pid:{self.proc.pid}, port:{self.port}) started.")


class NativeRedisSentinelCluster(AbstractRedisSentinelCluster):
    @contextlib.asynccontextmanager
    async def make_cluster(self) -> AsyncIterator[RedisClusterInfo]:
        nodes = []
        sentinels = []
        sentinel_config = textwrap.dedent(
            f"""
        sentinel resolve-hostnames yes
        sentinel monitor {self.service_name} 127.0.0.1 16379 2
        sentinel auth-pass {self.service_name} {self.password}
        sentinel down-after-milliseconds {self.service_name} 1000
        sentinel failover-timeout {self.service_name} 5000
        sentinel parallel-syncs {self.service_name} 2
        protected-mode no
        """
        ).lstrip()
        for node_port in [16379, 16380, 16381]:
            rdb_path = Path(f"node.{node_port}.rdb")
            try:
                rdb_path.unlink()
            except FileNotFoundError:
                pass
            node = NativeRedisNode(
                "node",
                node_port,
                [
                    "redis-server",
                    "--bind",
                    "127.0.0.1",
                    "--port",
                    str(node_port),
                    "--requirepass",
                    self.password,
                    "--masterauth",
                    self.password,
                ]
                + ([] if node_port == 16379 else ["--slaveof", "127.0.0.1", "16379"])
                + [
                    "--cluster-announce-ip",
                    "127.0.0.1",
                    "--min-slaves-to-write",
                    "1",
                    "--min-slaves-max-lag",
                    "10",
                    "--dbfilename",
                    str(rdb_path),
                ],
            )
            nodes.append(node)
        for sentinel_port in [26379, 26380, 26381]:
            # Redis sentinels store their states in the config files (not rdb!),
            # so the files should be separate to each sentinel instance.
            sentinel_conf_path = Path(f"sentinel.{sentinel_port}.conf")
            sentinel_conf_path.write_text(sentinel_config)
            sentinel = NativeRedisNode(
                "sentinel",
                sentinel_port,
                [
                    "redis-server",
                    os.fsencode(sentinel_conf_path),
                    "--bind",
                    "127.0.0.1",
                    "--port",
                    str(sentinel_port),
                    "--sentinel",
                ],
            )
            sentinels.append(sentinel)
        await asyncio.gather(*[node.start() for node in nodes])
        await asyncio.sleep(0.1)
        await asyncio.gather(*[sentinel.start() for sentinel in sentinels])
        try:
            yield RedisClusterInfo(
                node_addrs=[
                    ("127.0.0.1", 16379),
                    ("127.0.0.1", 16380),
                    ("127.0.0.1", 16381),
                ],
                nodes=nodes,
                sentinel_addrs=[
                    ("127.0.0.1", 26379),
                    ("127.0.0.1", 26380),
                    ("127.0.0.1", 26381),
                ],
                sentinels=sentinels,
            )
        except asyncio.CancelledError:
            raise
        finally:
            await asyncio.gather(*[sentinel.stop() for sentinel in sentinels])
            await asyncio.sleep(0.1)
            await asyncio.gather(*[node.stop() for node in nodes])


async def main():
    loop = asyncio.get_running_loop()

    async def redis_task():
        native_cluster = NativeRedisSentinelCluster(
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
