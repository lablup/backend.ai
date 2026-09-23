from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from yarl import URL

from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.unified import VolumesConfig
from ai.backend.manager.errors.storage import (
    StorageProxyConnectionError,
)


@dataclass
class StorageScenario:
    manager: StorageSessionManager
    session: MagicMock
    probes: dict[str, MagicMock]
    failures: dict[str, Exception]


@pytest.fixture
async def storage_scenario(request: pytest.FixtureRequest) -> AsyncIterator[StorageScenario]:
    overrides = getattr(request, "param", {})
    if isinstance(overrides, str):
        overrides = {"manager_api": overrides}
    config = VolumesConfig.model_validate({
        "proxies": {
            "shared": {
                "manager_api": "http://a:6022,http://b:6022",
                "client_api": "http://client:6021",
                "secret": "test-secret",
                "ssl_verify": False,
                **overrides,
            }
        },
    })
    session_type = aiohttp.ClientSession
    failures: dict[str, Exception] = {}
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 200
    response.read = AsyncMock(return_value=b'{"volumes": [], "items": []}')
    session = MagicMock(spec=session_type)
    session.close = AsyncMock()
    probes: dict[str, MagicMock] = {}

    @asynccontextmanager
    async def send(method: str, url: URL, **kwargs: Any) -> AsyncIterator[MagicMock]:
        if str(url.origin()) in failures:
            raise failures[str(url.origin())]
        yield response

    session.request = MagicMock(side_effect=send)

    def make_session(*, base_url: URL | None = None, **kwargs: Any) -> MagicMock:
        if base_url is None:
            return session
        probe = MagicMock(spec=session_type)
        probe.close = AsyncMock()
        probe_response = MagicMock(spec=aiohttp.ClientResponse)
        probe_response.status = 200
        probe.get.return_value.__aenter__ = AsyncMock(return_value=probe_response)
        probes[str(base_url)] = probe
        return probe

    with (
        patch("ai.backend.manager.clients.storage_proxy.session_manager.aiohttp.TCPConnector"),
        patch(
            "ai.backend.manager.clients.storage_proxy.session_manager.aiohttp.ClientSession",
            side_effect=make_session,
        ),
    ):
        manager = StorageSessionManager(config)
        try:
            yield StorageScenario(manager, session, probes, failures)
        finally:
            await manager.aclose()


class TestStorageSessionManager:
    @pytest.mark.parametrize("storage_scenario", ["http://a:6022"], indirect=True)
    async def test_single_url(self, storage_scenario: StorageScenario) -> None:
        client = storage_scenario.manager.get_manager_facing_client("shared")
        assert await client.get_volumes() == {"volumes": [], "items": []}
        args = storage_scenario.session.request.call_args
        assert args.args == ("GET", URL("http://a:6022/volumes"))
        assert args.kwargs["headers"] == {"X-BackendAI-Storage-Auth-Token": "test-secret"}
        assert storage_scenario.manager.get_client_api_url("shared") == URL("http://client:6021")

    @pytest.mark.parametrize(
        "storage_scenario", [{}, {"health_check_failure_threshold": 1}], indirect=True
    )
    async def test_failure_is_not_retried_and_next_calls_use_peer(
        self,
        storage_scenario: StorageScenario,
    ) -> None:
        storage_scenario.failures["http://a:6022"] = aiohttp.ClientConnectionError()
        client = storage_scenario.manager.get_manager_facing_client("shared")
        threshold = storage_scenario.manager.config.proxies["shared"].health_check_failure_threshold
        for attempt in range(threshold):
            with pytest.raises(StorageProxyConnectionError):
                await client.create_folder("volume", "folder")
            assert storage_scenario.session.request.call_count == 2 * attempt + 1
            await client.create_folder("volume", "folder")
        assert await client.list_files("volume", "folder", ".") == {"volumes": [], "items": []}
        assert [call.args[1].host for call in storage_scenario.session.request.call_args_list] == [
            "a",
            "b",
        ] * threshold + ["b"]

    @pytest.mark.parametrize(
        "storage_scenario", [{}, {"health_check_probe_path": "/custom-readyz"}], indirect=True
    )
    async def test_probe_failure_and_recovery(self, storage_scenario: StorageScenario) -> None:
        pool = storage_scenario.manager._proxies["shared"].endpoint_pool
        probe = storage_scenario.probes["http://a:6022"]
        probe.get.return_value.__aenter__.return_value.status = 503
        for _ in range(2):
            await pool._check_all_health()
            assert pool.is_healthy("http://a:6022")
        await pool._check_all_health()
        client = storage_scenario.manager.get_manager_facing_client("shared")
        await client.get_volumes()
        assert storage_scenario.session.request.call_args.args[1].host == "b"
        probe.get.assert_called_with(
            storage_scenario.manager.config.proxies["shared"].health_check_probe_path
        )
        probe.get.return_value.__aenter__.return_value.status = 200
        await pool._check_all_health()
        await client.get_volumes()
        assert storage_scenario.session.request.call_args.args[1].host == "a"

    async def test_all_unhealthy_names_proxy(self, storage_scenario: StorageScenario) -> None:
        for probe in storage_scenario.probes.values():
            probe.get.return_value.__aenter__.return_value.status = 503
        for _ in range(3):
            await storage_scenario.manager._proxies["shared"].endpoint_pool._check_all_health()
        with pytest.raises(StorageProxyConnectionError, match="shared"):
            await storage_scenario.manager.get_manager_facing_client("shared").get_volumes()
        storage_scenario.session.request.assert_not_called()

    async def test_close_releases_requests_and_probes(
        self, storage_scenario: StorageScenario
    ) -> None:
        await storage_scenario.manager.aclose()
        storage_scenario.session.close.assert_awaited_once()
        for probe in storage_scenario.probes.values():
            probe.close.assert_awaited_once()
        assert storage_scenario.manager._proxies["shared"].endpoint_pool._health_check_task.done()
