from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.worker.errors.ingress import IngressNotRegisteredError
from ai.backend.appproxy.worker.proxy.frontend.tcp import TCPFrontend
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressFrontendKey

_PORT = 10200


@dataclass(frozen=True)
class _TCPConnectionSituation:
    frontend: TCPFrontend
    reader: MagicMock
    writer: MagicMock
    backend: MagicMock


class TestTCPFrontend:
    @pytest.fixture
    def connection_to_a_slot_with_no_ingress(
        self, mocker: pytest_mock.MockerFixture
    ) -> _TCPConnectionSituation:
        root_context = mocker.MagicMock()
        root_context.ingress_state.reader.get = AsyncMock(
            side_effect=IngressNotRegisteredError("no layer holds the frontend")
        )
        frontend = TCPFrontend(root_context)
        backend = mocker.MagicMock(
            circuit=mocker.MagicMock(id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372")),
            bind=AsyncMock(),
        )
        frontend.backends[IngressFrontendKey(f"port-{_PORT}")] = backend
        return _TCPConnectionSituation(
            frontend=frontend,
            reader=mocker.MagicMock(),
            writer=mocker.MagicMock(wait_closed=AsyncMock()),
            backend=backend,
        )

    async def test_connection_to_a_slot_with_no_ingress_is_closed_without_reaching_the_backend(
        self, connection_to_a_slot_with_no_ingress: _TCPConnectionSituation
    ) -> None:
        situation = connection_to_a_slot_with_no_ingress
        await situation.frontend.pipe(_PORT, situation.reader, situation.writer)
        situation.backend.bind.assert_not_awaited()
        situation.writer.close.assert_called_once()
