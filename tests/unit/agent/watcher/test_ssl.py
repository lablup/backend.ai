from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from ai.backend.agent.watcher import watcher_server
from ai.backend.common.types import HostPortPair


class TestWatcherSSL:
    async def test_loads_cert_chain_from_configured_cert_and_key(self, tmp_path: Path) -> None:
        cert_path = tmp_path / "watcher.crt"
        key_path = tmp_path / "watcher.key"
        config = {
            "logging": MagicMock(),
            "etcd": {"user": None, "password": None, "addrs": [], "namespace": "test"},
            "watcher": {
                "service-addr": HostPortPair("127.0.0.1", 6009),
                "ssl-enabled": True,
                "ssl-cert": cert_path,
                "ssl-key": key_path,
                "soft-reset-available": False,
                "target-service": "backendai-agent.service",
            },
        }
        etcd_context = MagicMock()
        etcd_context.__aenter__ = AsyncMock(
            return_value=AsyncMock(get=AsyncMock(return_value="watcher-token"))
        )
        etcd_context.__aexit__ = AsyncMock(return_value=None)
        ssl_context = MagicMock()

        with (
            patch("ai.backend.agent.watcher.Logger"),
            patch("ai.backend.agent.watcher.AsyncEtcd", return_value=etcd_context),
            patch("ai.backend.agent.watcher.web.AppRunner", return_value=AsyncMock()),
            patch("ai.backend.agent.watcher.web.TCPSite", return_value=AsyncMock()) as tcp_site,
            patch("ai.backend.agent.watcher.ssl.create_default_context", return_value=ssl_context),
        ):
            async with watcher_server(asyncio.get_running_loop(), 0, [config, "ipc://test"]):
                pass

        ssl_context.load_cert_chain.assert_called_once_with(str(cert_path), str(key_path))
        assert tcp_site.call_args.kwargs["ssl_context"] is ssl_context
