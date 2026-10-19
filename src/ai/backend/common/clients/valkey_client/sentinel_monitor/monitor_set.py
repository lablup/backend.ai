from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor import SentinelMonitor
from ai.backend.common.exception import ConfigurationError, ValkeySentinelMonitorNotFound
from ai.backend.common.types import HostPortPair, ValkeyTarget
from ai.backend.common.utils import addr_to_hostport_pair


@dataclass(frozen=True)
class SentinelMonitorKey:
    sentinel_addresses: tuple[HostPortPair, ...]
    service_name: str
    password: str | None
    use_tls: bool
    tls_skip_verify: bool

    @classmethod
    def from_valkey_target(cls, target: ValkeyTarget) -> SentinelMonitorKey | None:
        """None for a standalone target."""
        if not target.sentinel:
            return None
        if not target.service_name:
            raise ConfigurationError({
                "redis": "service_name is required when Sentinel addresses are configured"
            })
        # The master password is the Sentinel password unless sentinel_password is set.
        password = (
            target.sentinel_password if target.sentinel_password is not None else target.password
        )
        return cls(
            sentinel_addresses=tuple(
                HostPortPair(*addr_to_hostport_pair(address)) for address in target.sentinel
            ),
            service_name=target.service_name,
            password=password,
            use_tls=target.use_tls,
            tls_skip_verify=target.tls_skip_verify,
        )


class SentinelMonitorSet:
    """One Sentinel monitor per distinct Sentinel set and service among the given targets."""

    _monitors: dict[SentinelMonitorKey, AbstractSentinelMonitor]

    def __init__(self, targets: Iterable[ValkeyTarget]) -> None:
        self._monitors = {}
        for target in targets:
            key = SentinelMonitorKey.from_valkey_target(target)
            if key is None or key in self._monitors:
                continue
            self._monitors[key] = SentinelMonitor(
                key.sentinel_addresses,
                key.service_name,
                password=key.password,
                use_tls=key.use_tls,
                tls_skip_verify=key.tls_skip_verify,
            )

    async def start(self) -> None:
        await asyncio.gather(*(monitor.start() for monitor in self._monitors.values()))

    async def close(self) -> None:
        for monitor in self._monitors.values():
            await monitor.close()

    def monitor_for(self, target: ValkeyTarget) -> AbstractSentinelMonitor | None:
        """None for a standalone target."""
        key = SentinelMonitorKey.from_valkey_target(target)
        if key is None:
            return None
        monitor = self._monitors.get(key)
        if monitor is None:
            raise ValkeySentinelMonitorNotFound(
                f"No Sentinel monitor for service '{key.service_name}'"
            )
        return monitor
