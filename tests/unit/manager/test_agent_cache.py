from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.common.contexts.request_id import with_request_id
from ai.backend.manager.agent_cache import PeerInvoker

TEST_REQUEST_ID = "test-request-id"


class TestPeerInvokerRequestId:
    @pytest.fixture
    def request_id(self) -> Iterator[str]:
        """Set up request_id context for the test."""
        with with_request_id(TEST_REQUEST_ID):
            yield TEST_REQUEST_ID

    async def test_includes_request_id_in_rpc_body(self, request_id: str) -> None:
        """Verify that request_id from context is included in RPC body."""
        mock_invoke = AsyncMock(return_value={"result": "ok"})

        invoker = object.__new__(PeerInvoker)
        invoker.last_used = time.monotonic()

        with patch.object(invoker, "invoke", mock_invoke):
            invoker.call = PeerInvoker._CallStub(invoker)
            await invoker.call.some_method("arg1", kwarg1="value1")

        call_args = mock_invoke.call_args
        assert call_args is not None
        request_body: dict[str, Any] = call_args[0][1]
        assert request_body["request_id"] == request_id
        assert request_body["args"] == ("arg1",)
        assert request_body["kwargs"] == {"kwarg1": "value1"}
