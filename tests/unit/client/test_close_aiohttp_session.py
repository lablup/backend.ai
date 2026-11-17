from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from ai.backend.client.session import _close_aiohttp_session


def _make_proto() -> SimpleNamespace:
    return SimpleNamespace(connection_lost=MagicMock(), eof_received=MagicMock())


def _make_session(protos: list[SimpleNamespace]) -> MagicMock:
    handlers = [SimpleNamespace(transport=SimpleNamespace(_ssl_protocol=p)) for p in protos]
    session = MagicMock()
    session.connector._conns = {"key": [(h, 0.0) for h in handlers]}

    async def close() -> None:
        for proto in protos:
            proto.connection_lost(None)

    session.close = close
    return session


class TestCloseAiohttpSession:
    async def test_each_transport_calls_its_own_original_callbacks(self) -> None:
        protos = [_make_proto() for _ in range(3)]
        originals: list[tuple[Any, Any]] = [(p.connection_lost, p.eof_received) for p in protos]
        session = _make_session(protos)

        # The patched connection_lost is what close() invokes on each proto.
        await _close_aiohttp_session(session)
        for proto in protos:
            proto.eof_received()

        for orig_lost, orig_eof in originals:
            orig_lost.assert_called_once_with(None)
            orig_eof.assert_called_once_with()
