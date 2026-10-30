import asyncio
import logging
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.common.asyncio import ConsecutiveFailures
from ai.backend.common.configs.loader import EtcdConfigWatcher, LoaderChain
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class ConfigChangeFeed:
    """Reports one change per watch; the first watch fails before reporting anything."""

    watch_count: int

    def __init__(self) -> None:
        self.watch_count = 0

    async def watch(self) -> AsyncIterator[MagicMock]:
        self.watch_count += 1
        if self.watch_count == 1:
            raise ConnectionError("etcd unavailable")
        event = MagicMock()
        event.key = f"config/key-{self.watch_count}"
        yield event


class TestManagerConfigProviderWatcher:
    @pytest.fixture
    def no_retry_delay(self, mocker: MockerFixture) -> None:
        mocker.patch.object(ConsecutiveFailures, "delay_sec", return_value=0)

    @pytest.fixture
    def reloaded_config(self, mocker: MockerFixture) -> MagicMock:
        config = MagicMock(spec=ManagerUnifiedConfig)
        mocker.patch.object(ManagerUnifiedConfig, "model_validate", return_value=config)
        return config

    @pytest.fixture
    def etcd_watcher(self) -> EtcdConfigWatcher:
        watcher = MagicMock(spec=EtcdConfigWatcher)
        watcher.watch = ConfigChangeFeed().watch
        return watcher

    @pytest.mark.usefixtures("no_retry_delay")
    async def test_reload_failure_keeps_previous_config_and_keeps_watching(
        self, etcd_watcher: EtcdConfigWatcher, reloaded_config: MagicMock
    ) -> None:
        loader = MagicMock(spec=LoaderChain)
        loader.load = AsyncMock(side_effect=[RuntimeError("invalid config"), {}])
        initial_config = MagicMock(spec=ManagerUnifiedConfig)
        provider = ManagerConfigProvider(
            loader, initial_config, etcd_watcher, MagicMock(spec=LegacyEtcdLoader)
        )
        try:
            async with asyncio.timeout(5):
                while loader.load.await_count < 1:
                    await asyncio.sleep(0)
                assert provider.config is initial_config
                while loader.load.await_count < 2:
                    await asyncio.sleep(0)
                await asyncio.sleep(0)
            assert provider.config is reloaded_config
        finally:
            await provider.terminate()

    @pytest.mark.usefixtures("no_retry_delay")
    async def test_reload_failure_streak_logs_once_then_recovery(
        self,
        etcd_watcher: EtcdConfigWatcher,
        reloaded_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        loader = MagicMock(spec=LoaderChain)
        loader.load = AsyncMock(side_effect=[RuntimeError("invalid config")] * 3 + [{}])
        provider = ManagerConfigProvider(
            loader,
            MagicMock(spec=ManagerUnifiedConfig),
            etcd_watcher,
            MagicMock(spec=LegacyEtcdLoader),
        )
        try:
            with caplog.at_level(logging.DEBUG, logger="ai.backend.manager.config.provider"):
                async with asyncio.timeout(5):
                    while provider.config is not reloaded_config:
                        await asyncio.sleep(0)
        finally:
            await provider.terminate()

        failures = [
            r
            for r in caplog.records
            if r.getMessage() == "config reload failed, keeping the previous config"
        ]
        assert [r.levelno for r in failures] == [logging.ERROR, logging.DEBUG, logging.DEBUG]
        recovered = [r for r in caplog.records if r.getMessage() == "config reload recovered"]
        assert len(recovered) == 1
        assert recovered[0].levelno == logging.INFO
