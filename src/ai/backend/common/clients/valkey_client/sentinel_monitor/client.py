from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Final

from aiotools import cancel_and_wait
from glide import (
    AdvancedGlideClientConfiguration,
    GlideClient,
    GlideClientConfiguration,
    GlideError,
    NodeAddress,
    ServerCredentials,
    TlsAdvancedConfiguration,
)

from ai.backend.common.clients.valkey_client.sentinel_monitor.store import MasterStore
from ai.backend.common.clients.valkey_client.sentinel_monitor.types import (
    SentinelConnectionConfig,
    SentinelMaster,
)
from ai.backend.common.types import HostPortPair
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_SWITCH_MASTER_CHANNEL: Final[str] = "+switch-master"
_HEALTH_CHECK_INTERVAL: Final[float] = 5.0
_RECREATE_THRESHOLD: Final[int] = (
    3  # Recreate the client every this many failed health checks in a row
)
# glide does not apply its request timeout while a lazy connection is still being established.
_REQUEST_TIMEOUT: Final[float] = 1.0
_CONNECTION_TIMEOUT_MS: Final[int] = 1_000


class SentinelClient:
    """One glide connection to one Sentinel, subscribed to `+switch-master`."""

    _address: HostPortPair
    _config: SentinelConnectionConfig
    _service_name: str
    _store: MasterStore
    _glide: GlideClient | None
    _healthy: bool
    _failures: int
    _subscribe_task: asyncio.Task[None] | None
    _health_task: asyncio.Task[None] | None

    def __init__(
        self, address: HostPortPair, service_name: str, config: SentinelConnectionConfig
    ) -> None:
        self._address = address
        self._service_name = service_name
        self._config = config
        self._store = MasterStore()
        self._glide = None
        self._healthy = False
        self._failures = 0
        self._subscribe_task = None
        self._health_task = None

    @property
    def healthy(self) -> bool:
        return self._healthy

    async def start(self) -> None:
        await self._open()
        await self._check_health()
        self._health_task = asyncio.create_task(self._health_loop())

    async def close(self) -> None:
        for task in (self._health_task, self._subscribe_task):
            if task is not None:
                await cancel_and_wait(task)
        if self._glide is not None:
            await self._glide.close()
            self._glide = None
        self._store.close()

    def master(self) -> SentinelMaster | None:
        return self._store.get()

    def watch(self) -> AsyncGenerator[SentinelMaster]:
        """The masters this Sentinel answered."""
        return self._store.watch()

    async def query(self) -> SentinelMaster | None:
        master = await self._fetch()
        if master is not None:
            self._store.set(master)
        return master

    async def _fetch(self) -> SentinelMaster | None:
        if self._glide is None:
            return None
        # During a failover Sentinel raises the epoch before SENTINEL MASTER shows the promoted
        # replica, while GET-MASTER-ADDR-BY-NAME already returns it. Reading the epoch first
        # keeps the address at least as new as the epoch.
        try:
            async with asyncio.timeout(_REQUEST_TIMEOUT):
                state = await self._glide.custom_command(["SENTINEL", "MASTER", self._service_name])
                address = await self._glide.custom_command([
                    "SENTINEL",
                    "GET-MASTER-ADDR-BY-NAME",
                    self._service_name,
                ])
        except (GlideError, TimeoutError) as e:
            log.warning(
                "valkey sentinel query failed",
                exc_info=e,
                sentinel=str(self._address),
                service_name=self._service_name,
            )
            return None
        if not isinstance(state, dict) or not isinstance(address, list) or len(address) != 2:
            return None
        fields = {key: value for key, value in state.items() if isinstance(key, bytes)}
        epoch = fields.get(b"config-epoch")
        host, port = address
        if (
            not isinstance(epoch, bytes)
            or not isinstance(host, bytes)
            or not isinstance(port, bytes)
        ):
            return None
        return SentinelMaster(HostPortPair(host.decode(), int(port)), int(epoch))

    async def _open(self) -> None:
        # A lazy connection keeps the blocking connect out of the event loop.
        glide = await GlideClient.create(self._glide_config())
        self._glide = glide
        self._subscribe_task = asyncio.create_task(self._subscribe_loop(glide))

    async def _recreate(self) -> None:
        log.warning("valkey sentinel client recreated", sentinel=str(self._address))
        if self._subscribe_task is not None:
            await cancel_and_wait(self._subscribe_task)
        if self._glide is not None:
            await self._glide.close()
        await self._open()

    async def _health_loop(self) -> None:
        while True:
            await asyncio.sleep(_HEALTH_CHECK_INTERVAL)
            await self._check_health()

    async def _check_health(self) -> None:
        """glide reconnects by itself; the client is recreated only when that keeps failing."""
        if self._glide is None:
            return
        try:
            async with asyncio.timeout(_REQUEST_TIMEOUT):
                await self._glide.ping()
        except (GlideError, TimeoutError) as e:
            if self._failures == 0:
                log.warning("valkey sentinel unhealthy", exc_info=e, sentinel=str(self._address))
            self._healthy = False
            self._failures += 1
            if self._failures % _RECREATE_THRESHOLD == 0:
                await self._recreate()
            return
        recovered = not self._healthy
        self._healthy = True
        self._failures = 0
        if recovered:
            # The first success after start or a disconnection, catching a switch missed meanwhile.
            await self.query()

    async def _subscribe_loop(self, glide: GlideClient) -> None:
        while True:
            try:
                message = await glide.get_pubsub_message()
            except GlideError as e:
                # glide resubscribes after it reconnects.
                log.warning(
                    "valkey sentinel subscription failed", exc_info=e, sentinel=str(self._address)
                )
                await asyncio.sleep(_HEALTH_CHECK_INTERVAL)
                continue
            payload = message.message
            text = payload if isinstance(payload, str) else bytes(payload).decode()
            # <service-name> <old-ip> <old-port> <new-ip> <new-port>
            if text.partition(" ")[0] == self._service_name:
                await self.query()

    def _glide_config(self) -> GlideClientConfiguration:
        # Sentinel is not a primary, so read-only mode skips the primary detection.
        return GlideClientConfiguration(
            [NodeAddress(host=str(self._address.host), port=self._address.port)],
            credentials=(
                ServerCredentials(password=self._config.password) if self._config.password else None
            ),
            use_tls=self._config.use_tls,
            request_timeout=int(_REQUEST_TIMEOUT * 1000),
            read_only=True,
            lazy_connect=True,
            pubsub_subscriptions=GlideClientConfiguration.PubSubSubscriptions(
                channels_and_patterns={
                    GlideClientConfiguration.PubSubChannelModes.Exact: {_SWITCH_MASTER_CHANNEL},
                },
                callback=None,
                context=None,
            ),
            advanced_config=AdvancedGlideClientConfiguration(
                connection_timeout=_CONNECTION_TIMEOUT_MS,
                tls_config=TlsAdvancedConfiguration(use_insecure_tls=self._config.tls_skip_verify),
            ),
        )
