from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.errors import InvalidConfigurationSourceError, InvalidSocketPathError
from ai.backend.storage.watcher import WatcherClient


@dataclass
class WatcherInput:
    """Input required for the watcher client setup."""

    local_config: StorageProxyUnifiedConfig
    pidx: int


class WatcherProvider(NonMonitorableDependencyProvider[WatcherInput, WatcherClient | None]):
    """Provider for the privileged watcher client."""

    @property
    @override
    def stage_name(self) -> str:
        return "watcher"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: WatcherInput) -> AsyncIterator[WatcherClient | None]:
        local_config = setup_input.local_config
        if not local_config.storage_proxy.use_watcher:
            yield None
            return

        if os.geteuid() != 0:
            raise InvalidConfigurationSourceError(
                "Storage proxy must be run as root if watcher is enabled. Else, set"
                " `use-watcher` to false in your local config file."
            )
        insock_path = local_config.storage_proxy.watcher_insock_path_prefix
        outsock_path = local_config.storage_proxy.watcher_outsock_path_prefix
        if insock_path is None or outsock_path is None:
            raise InvalidSocketPathError(
                "Socket path must be not null. Please set valid socket path to"
                " `watcher-insock-path-prefix` and `watcher-outsock-path-prefix` in your local"
                " config file."
            )
        watcher_client = WatcherClient(setup_input.pidx, insock_path, outsock_path)
        await watcher_client.init()
        try:
            yield watcher_client
        finally:
            await watcher_client.close()
