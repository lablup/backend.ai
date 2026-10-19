from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Sequence
from contextlib import ExitStack
from dataclasses import dataclass

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor import SentinelMonitor
from ai.backend.common.types import HostPortPair

SERVICE_NAME = "mymaster"
REDIS_IMAGE = "redis:7-alpine"
SENTINEL_PORT = 26379
# Matches the MASTER argument of `SENTINEL MASTER <name>` in a RESP request.
QUERY_TOKEN = b"\r\nmaster\r\n"
EVENT_TOKENS = (b"\r\nmessage\r\n", b"+switch-master")
WAIT_TIMEOUT = 30.0


def sentinel_config(master_host: str) -> str:
    return "\\n".join([
        f"port {SENTINEL_PORT}",
        "sentinel resolve-hostnames yes",
        f"sentinel monitor {SERVICE_NAME} {master_host} 6379 1",
        f"sentinel down-after-milliseconds {SERVICE_NAME} 1000",
        f"sentinel failover-timeout {SERVICE_NAME} 2000",
    ])


@dataclass
class SentinelNode:
    container: DockerContainer
    address: HostPortPair

    def command(self, *args: str) -> list[str]:
        """Run a command with redis-cli inside the Sentinel container."""
        result = self.container.exec(["redis-cli", "-p", str(SENTINEL_PORT), *args])
        output: bytes = result.output
        return output.decode().split()

    async def master(self) -> HostPortPair:
        host, port = await asyncio.to_thread(
            self.command, "SENTINEL", "GET-MASTER-ADDR-BY-NAME", SERVICE_NAME
        )
        return HostPortPair(host, int(port))

    def fields(self, *args: str) -> list[tuple[str, str]]:
        values = self.command(*args)
        return list(zip(values[::2], values[1::2], strict=False))


@dataclass
class SentinelCluster:
    sentinels: list[SentinelNode]
    # Watches a separate master under the same service name and never fails over.
    stale_sentinel: SentinelNode

    async def master(self) -> HostPortPair:
        return await self.sentinels[0].master()

    async def failover(self) -> HostPortPair:
        """Force a failover and wait until every Sentinel reports the new master."""
        leader = self.sentinels[0]
        previous = await leader.master()
        deadline = time.monotonic() + WAIT_TIMEOUT
        # INPROG / NOGOODSLAVE until the previous failover settles.
        while await asyncio.to_thread(leader.command, "SENTINEL", "FAILOVER", SERVICE_NAME) != [
            "OK"
        ]:
            assert time.monotonic() < deadline, "Sentinel did not start a failover"
            await asyncio.sleep(0.5)
        while (current := await leader.master()) == previous:
            assert time.monotonic() < deadline, "Sentinel did not switch the master"
            await asyncio.sleep(0.1)
        for sentinel in self.sentinels[1:]:
            while await sentinel.master() != current:
                assert time.monotonic() < deadline, "The other Sentinel kept the old master"
                await asyncio.sleep(0.1)
        return current

    async def wait_subscribed(self) -> None:
        deadline = time.monotonic() + WAIT_TIMEOUT
        for sentinel in self.sentinels:
            while not await asyncio.to_thread(sentinel.command, "CLIENT", "LIST", "TYPE", "pubsub"):
                assert time.monotonic() < deadline, "The monitor did not subscribe"
                await asyncio.sleep(0.05)

    def is_ready(self) -> bool:
        leader = self.sentinels[0]
        has_replica = ("flags", "slave") in leader.fields("SENTINEL", "REPLICAS", SERVICE_NAME)
        known_sentinels = len(leader.fields("SENTINEL", "SENTINELS", SERVICE_NAME)) > 0
        return has_replica and known_sentinels


@pytest.fixture(scope="module")
def sentinel_cluster() -> Iterator[SentinelCluster]:
    def redis_server(network: Network, alias: str, *args: str) -> DockerContainer:
        return (
            DockerContainer(REDIS_IMAGE)
            .with_network(network)
            .with_network_aliases(alias)
            .with_command(["redis-server", "--save", "", "--appendonly", "no", *args])
        )

    def sentinel(network: Network, master_host: str) -> DockerContainer:
        return (
            DockerContainer(REDIS_IMAGE)
            .with_network(network)
            .with_exposed_ports(SENTINEL_PORT)
            .with_command([
                "sh",
                "-c",
                f"printf '{sentinel_config(master_host)}\\n' > /tmp/sentinel.conf"
                " && exec redis-sentinel /tmp/sentinel.conf",
            ])
        )

    def node(container: DockerContainer) -> SentinelNode:
        port = int(container.get_exposed_port(SENTINEL_PORT))
        return SentinelNode(container, HostPortPair("127.0.0.1", port))

    with Network() as network, ExitStack() as stack:
        stack.enter_context(redis_server(network, "master"))
        stack.enter_context(redis_server(network, "replica", "--replicaof", "master", "6379"))
        stack.enter_context(redis_server(network, "stale-master"))
        sentinels = [stack.enter_context(sentinel(network, "master")) for _ in range(2)]
        stale = stack.enter_context(sentinel(network, "stale-master"))
        cluster = SentinelCluster([node(s) for s in sentinels], node(stale))
        deadline = time.monotonic() + WAIT_TIMEOUT
        while not cluster.is_ready():
            assert time.monotonic() < deadline, "Sentinels did not discover the deployment"
            time.sleep(0.2)
        yield cluster


class SentinelProxy:
    """Forwards to a Sentinel, counts master queries and can drop `+switch-master` events."""

    upstream: HostPortPair
    query_count: int
    drop_events: bool
    _server: asyncio.Server | None

    def __init__(self, upstream: HostPortPair) -> None:
        self.upstream = upstream
        self.query_count = 0
        self.drop_events = False
        self._server = None

    @property
    def address(self) -> HostPortPair:
        assert self._server is not None
        return HostPortPair("127.0.0.1", self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)

    async def close(self) -> None:
        assert self._server is not None
        self._server.close()
        self._server.close_clients()
        await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        upstream_reader, upstream_writer = await asyncio.open_connection(
            str(self.upstream.host), self.upstream.port
        )
        await asyncio.gather(
            self._forward_requests(reader, upstream_writer),
            self._forward_replies(upstream_reader, writer),
            return_exceptions=True,
        )

    async def _forward_requests(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            while data := await reader.read(65536):
                self.query_count += data.lower().count(QUERY_TOKEN)
                writer.write(data)
                await writer.drain()
        finally:
            writer.close()

    async def _forward_replies(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            while data := await reader.read(65536):
                if self.drop_events and all(token in data for token in EVENT_TOKENS):
                    continue
                writer.write(data)
                await writer.drain()
        finally:
            writer.close()


@pytest.fixture
async def sentinel_proxies(sentinel_cluster: SentinelCluster) -> AsyncIterator[list[SentinelProxy]]:
    proxies = [SentinelProxy(sentinel.address) for sentinel in sentinel_cluster.sentinels]
    for proxy in proxies:
        await proxy.start()
    yield proxies
    for proxy in proxies:
        await proxy.close()


MonitorFactory = Callable[..., Awaitable[SentinelMonitor]]


@pytest.fixture
async def monitor_factory(
    sentinel_cluster: SentinelCluster, sentinel_proxies: list[SentinelProxy]
) -> AsyncIterator[MonitorFactory]:
    monitors: list[SentinelMonitor] = []

    async def create(
        poll_interval: float = 60.0,
        extra_addresses: Sequence[HostPortPair] = (),
    ) -> SentinelMonitor:
        monitor = SentinelMonitor(
            [*extra_addresses, *(proxy.address for proxy in sentinel_proxies)],
            SERVICE_NAME,
            poll_interval=poll_interval,
        )
        await monitor.start()
        monitors.append(monitor)
        await sentinel_cluster.wait_subscribed()
        return monitor

    yield create
    for monitor in monitors:
        await monitor.close()


class TestSentinelMonitorFailover:
    async def test_each_watcher_yields_new_master_once(
        self, sentinel_cluster: SentinelCluster, monitor_factory: MonitorFactory
    ) -> None:
        monitor = await monitor_factory(poll_interval=0.5)
        watchers = [monitor.watch_master() for _ in range(2)]
        initial = await sentinel_cluster.master()
        for watcher in watchers:
            assert await anext(watcher) == initial

        new_master = await sentinel_cluster.failover()

        for watcher in watchers:
            assert await asyncio.wait_for(anext(watcher), WAIT_TIMEOUT) == new_master
        # The events from both Sentinels and the poll have all seen the switch by now.
        await asyncio.sleep(1.5)
        for watcher in watchers:
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(anext(watcher), 0.5)

    async def test_event_from_other_sentinel_when_one_is_silent(
        self,
        sentinel_cluster: SentinelCluster,
        sentinel_proxies: list[SentinelProxy],
        monitor_factory: MonitorFactory,
    ) -> None:
        monitor = await monitor_factory()
        watcher = monitor.watch_master()
        await anext(watcher)
        sentinel_proxies[0].drop_events = True

        new_master = await sentinel_cluster.failover()

        assert await asyncio.wait_for(anext(watcher), WAIT_TIMEOUT) == new_master
        await watcher.aclose()

    async def test_poll_catches_failover_when_every_sentinel_is_silent(
        self,
        sentinel_cluster: SentinelCluster,
        sentinel_proxies: list[SentinelProxy],
        monitor_factory: MonitorFactory,
    ) -> None:
        monitor = await monitor_factory(poll_interval=1.0)
        watcher = monitor.watch_master()
        await anext(watcher)
        for proxy in sentinel_proxies:
            proxy.drop_events = True

        new_master = await sentinel_cluster.failover()

        assert await asyncio.wait_for(anext(watcher), WAIT_TIMEOUT) == new_master
        await watcher.aclose()

    async def test_old_config_epoch_is_ignored(
        self, sentinel_cluster: SentinelCluster, monitor_factory: MonitorFactory
    ) -> None:
        # The failover raises the config epoch above the stale Sentinel's.
        new_master = await sentinel_cluster.failover()
        monitor = await monitor_factory(extra_addresses=[sentinel_cluster.stale_sentinel.address])

        assert await monitor.get_master() == new_master
        assert await monitor.check_master(new_master) == new_master

    async def test_closed_watcher_receives_nothing(
        self, sentinel_cluster: SentinelCluster, monitor_factory: MonitorFactory
    ) -> None:
        monitor = await monitor_factory()
        open_watcher = monitor.watch_master()
        closed_watcher = monitor.watch_master()
        await anext(open_watcher)
        await anext(closed_watcher)
        await closed_watcher.aclose()

        new_master = await sentinel_cluster.failover()

        assert await asyncio.wait_for(anext(open_watcher), WAIT_TIMEOUT) == new_master
        with pytest.raises(StopAsyncIteration):
            await anext(closed_watcher)
        await open_watcher.aclose()

    async def test_watcher_ends_when_monitor_closes(self, monitor_factory: MonitorFactory) -> None:
        monitor = await monitor_factory()
        watcher = monitor.watch_master()
        await anext(watcher)

        await monitor.close()

        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(anext(watcher), WAIT_TIMEOUT)


class TestSentinelMonitorCheckMaster:
    async def test_stale_address_returns_known_master_without_query(
        self, sentinel_proxies: list[SentinelProxy], monitor_factory: MonitorFactory
    ) -> None:
        monitor = await monitor_factory()
        known = await monitor.get_master()
        before = [proxy.query_count for proxy in sentinel_proxies]

        result = await monitor.check_master(HostPortPair("192.0.2.1", 6379))

        assert result == known
        assert [proxy.query_count for proxy in sentinel_proxies] == before
