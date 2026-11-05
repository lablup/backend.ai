from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

<<<<<<< HEAD
=======
from ai.backend.agent.errors.watcher import (
    InvalidWatcherTokenError,
    WatcherTokenNotConfiguredError,
)
>>>>>>> 2f97c66b3 (feat(BA-8229): require a configured agent watcher token (#16488))
from ai.backend.agent.watcher import auth_middleware, watcher_server

_TOKEN_HEADER = "X-BackendAI-Watcher-Token"


@dataclass(frozen=True)
class _RejectedTokenCase:
    id: str
    expected: str
    headers: dict[str, str]


def _make_request(expected: str, headers: dict[str, str]) -> web.Request:
    request = MagicMock(spec=web.Request)
    request.app = {"token": expected}
    request.headers = headers
    return request


class TestAuthMiddleware:
    async def test_accepts_matching_token(self) -> None:
        response = web.Response()
        handler = AsyncMock(return_value=response)

        result = await auth_middleware(_make_request("secret", {_TOKEN_HEADER: "secret"}), handler)

        assert result is response

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedTokenCase(
                id="different-token", expected="secret", headers={_TOKEN_HEADER: "other"}
            ),
            _RejectedTokenCase(id="missing-header", expected="secret", headers={}),
            _RejectedTokenCase(id="missing-header-with-empty-token", expected="", headers={}),
            _RejectedTokenCase(
                id="non-ascii-token", expected="secret", headers={_TOKEN_HEADER: "비밀"}
            ),
            _RejectedTokenCase(
                id="undecodable-token", expected="secret", headers={_TOKEN_HEADER: "\udcff"}
            ),
        ],
        ids=lambda case: case.id,
    )
    async def test_rejects_token_mismatch(self, case: _RejectedTokenCase) -> None:
        handler = AsyncMock()

        result = await auth_middleware(_make_request(case.expected, case.headers), handler)

        assert result.status == 403
        handler.assert_not_called()


<<<<<<< HEAD
class TestStartupTokenLog:
    @pytest.mark.parametrize(
        "stored_token",
        ["watcher-secret-value", None],
        ids=["configured", "not-configured"],
    )
    async def test_logs_whether_token_is_configured_without_its_value(
        self,
        caplog: pytest.LogCaptureFixture,
        stored_token: str | None,
    ) -> None:
        etcd = AsyncMock()
        etcd.get.return_value = stored_token
        etcd.__aenter__.return_value = etcd
        cfg: dict[str, Any] = {
            "logging": MagicMock(),
            "etcd": {"user": None, "addr": None, "namespace": "test"},
            "watcher": {"ssl-enabled": False, "service-addr": MagicMock()},
        }
=======
def _watcher_cfg() -> dict[str, Any]:
    return {
        "logging": MagicMock(),
        "etcd": {"user": None, "addrs": [], "namespace": "test"},
        "watcher": {"ssl-enabled": False, "service-addr": MagicMock()},
    }


def _mock_etcd(stored_token: str | None) -> AsyncMock:
    etcd = AsyncMock()
    etcd.get.return_value = stored_token
    etcd.__aenter__.return_value = etcd
    return etcd


class TestStartupToken:
    async def test_starts_without_logging_token_value(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
>>>>>>> 2f97c66b3 (feat(BA-8229): require a configured agent watcher token (#16488))
        with (
            patch("ai.backend.agent.watcher.AsyncEtcd", return_value=_mock_etcd("watcher-secret")),
            patch("ai.backend.agent.watcher.Logger"),
            patch("ai.backend.agent.watcher.web.AppRunner", return_value=AsyncMock()),
            patch("ai.backend.agent.watcher.web.TCPSite", return_value=AsyncMock()) as tcp_site,
            caplog.at_level(logging.DEBUG, logger="ai.backend.agent.watcher"),
        ):
            async with watcher_server(
                asyncio.get_running_loop(), 0, (_watcher_cfg(), "ipc://test")
            ):
                pass

<<<<<<< HEAD
        records = [vars(record) for record in caplog.records]
        assert all("watcher-secret-value" not in str(record) for record in records)
        assert any(
            "watcher authentication token loaded" in record.getMessage()
            for record in caplog.records
        )
=======
        tcp_site.return_value.start.assert_awaited_once()
        assert all("watcher-secret" not in str(vars(record)) for record in caplog.records)

    @pytest.mark.parametrize("stored_token", [None, ""], ids=["missing", "empty"])
    async def test_refuses_to_start_without_token(self, stored_token: str | None) -> None:
        with (
            patch("ai.backend.agent.watcher.AsyncEtcd", return_value=_mock_etcd(stored_token)),
            patch("ai.backend.agent.watcher.Logger"),
            patch("ai.backend.agent.watcher.web.AppRunner", return_value=AsyncMock()),
            patch("ai.backend.agent.watcher.web.TCPSite", return_value=AsyncMock()) as tcp_site,
            pytest.raises(WatcherTokenNotConfiguredError),
        ):
            async with watcher_server(
                asyncio.get_running_loop(), 0, (_watcher_cfg(), "ipc://test")
            ):
                pass

        tcp_site.return_value.start.assert_not_awaited()
>>>>>>> 2f97c66b3 (feat(BA-8229): require a configured agent watcher token (#16488))
