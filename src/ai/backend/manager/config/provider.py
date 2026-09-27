import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Self

from ai.backend.common.asyncio import ConsecutiveFailures
from ai.backend.common.configs.loader import EtcdConfigWatcher, LoaderChain
from ai.backend.logging.structured import StructuredLogger

from .loader.legacy_etcd_loader import LegacyEtcdLoader
from .unified import ManagerUnifiedConfig

SharedConfigChangeCallback = Callable[[ManagerUnifiedConfig], Awaitable[None]]

log = StructuredLogger(logging.getLogger(__spec__.name))

_WATCH_MAX_RETRY_DELAY_SEC = 30.0


class ManagerConfigProvider:
    _loader: LoaderChain
    _config: ManagerUnifiedConfig
    _etcd_watcher: EtcdConfigWatcher
    _etcd_watcher_task: asyncio.Task[None] | None
    # TODO: Remove `_legacy_etcd_config_loader` when legacy etcd methods are removed
    _legacy_etcd_config_loader: LegacyEtcdLoader

    def __init__(
        self,
        loader: LoaderChain,
        config: ManagerUnifiedConfig,
        etcd_watcher: EtcdConfigWatcher,
        legacy_etcd_config_loader: LegacyEtcdLoader,
    ) -> None:
        self._loader = loader
        self._config = config
        self._etcd_watcher = etcd_watcher
        self._legacy_etcd_config_loader = legacy_etcd_config_loader
        self._etcd_watcher_task = asyncio.create_task(self._run_watcher())

    @classmethod
    async def create(
        cls,
        loader: LoaderChain,
        etcd_watcher: EtcdConfigWatcher,
        legacy_etcd_config_loader: LegacyEtcdLoader,
    ) -> Self:
        raw_config = await loader.load()
        config = ManagerUnifiedConfig.model_validate(raw_config, by_name=True)
        return cls(loader, config, etcd_watcher, legacy_etcd_config_loader)

    @property
    def config(self) -> ManagerUnifiedConfig:
        return self._config

    def reload(self, config: ManagerUnifiedConfig) -> None:
        self._config = config

    @property
    def legacy_etcd_config_loader(self) -> LegacyEtcdLoader:
        return self._legacy_etcd_config_loader

    async def _run_watcher(self) -> None:
        watch_failures = ConsecutiveFailures(max_delay_sec=_WATCH_MAX_RETRY_DELAY_SEC)
        reload_failures = ConsecutiveFailures()
        while True:
            try:
                async for event in self._etcd_watcher.watch():
                    if failure_count := watch_failures.record_success():
                        log.info("config watch recovered", failure_count=failure_count)
                    await self._reload_on_change(event.key, reload_failures)
            except Exception:
                if watch_failures.record_failure():
                    log.exception("config watch failed")
                else:
                    log.debug("config watch failed", failure_count=watch_failures.count)
            await asyncio.sleep(watch_failures.delay_sec())

    async def _reload_on_change(
        self, config_key: str, reload_failures: ConsecutiveFailures
    ) -> None:
        try:
            raw_config = await self._loader.load()
            config = ManagerUnifiedConfig.model_validate(raw_config, by_name=True)
        except Exception:
            if reload_failures.record_failure():
                log.exception(
                    "config reload failed, keeping the previous config", config_key=config_key
                )
            else:
                log.debug(
                    "config reload failed, keeping the previous config",
                    config_key=config_key,
                    failure_count=reload_failures.count,
                )
            return
        if failure_count := reload_failures.record_success():
            log.info("config reload recovered", failure_count=failure_count)
        self._config = config
        log.info("config reloaded on an etcd change", config_key=config_key)

    async def terminate(self) -> None:
        if self._etcd_watcher_task:
            self._etcd_watcher_task.cancel()
            try:
                await self._etcd_watcher_task
            except asyncio.CancelledError:
                pass
