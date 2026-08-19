from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import aiohttp.connector
import aiohttp.resolver
import pytest

from ai.backend.common.networking import force_threaded_dns_resolver


@pytest.fixture
def restore_default_resolver() -> Iterator[None]:
    orig_resolver = aiohttp.resolver.DefaultResolver
    orig_connector: Any = vars(aiohttp.connector)["DefaultResolver"]
    yield
    aiohttp.resolver.DefaultResolver = orig_resolver
    setattr(aiohttp.connector, "DefaultResolver", orig_connector)


def test_force_threaded_dns_resolver_overrides_defaults(
    restore_default_resolver: None,
) -> None:
    force_threaded_dns_resolver()
    assert aiohttp.resolver.DefaultResolver is aiohttp.resolver.ThreadedResolver
    assert vars(aiohttp.connector)["DefaultResolver"] is aiohttp.resolver.ThreadedResolver


async def test_new_connector_uses_threaded_resolver(
    restore_default_resolver: None,
) -> None:
    force_threaded_dns_resolver()
    conn = aiohttp.TCPConnector()
    try:
        # The connector must not fall back to the aiodns/pycares AsyncResolver,
        # whose per-instance c-ares channels leak on long-running services.
        assert isinstance(conn._resolver, aiohttp.resolver.ThreadedResolver)
    finally:
        await conn.close()
