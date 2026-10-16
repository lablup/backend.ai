from __future__ import annotations

from functools import partial
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.appproxy.worker.server import http_client_pool_ctx
from ai.backend.appproxy.worker.types import RootContext


@pytest.mark.parametrize("verify", [True, False])
async def test_coordinator_ssl_verification_follows_config(verify: bool) -> None:
    root_ctx = MagicMock()
    root_ctx.local_config.proxy_worker.verify_coordinator_ssl_certificate = verify
    root_ctx.local_config.proxy_worker.client_pool_cleanup_interval = 600

    async with http_client_pool_ctx(cast(RootContext, root_ctx)):
        factory = cast(
            partial[Any],
            root_ctx.http_client_pool._client_session_factory,
        )
        assert factory.keywords["ssl"] is verify
