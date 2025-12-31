import asyncio
import secrets
from collections.abc import AsyncIterator, Iterator

import pytest
from pytest import Config, Parser

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine
from ai.backend.testutils.bootstrap import etcd_container, postgres_container  # noqa: F401


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        dest="integration",
        default=False,
        help="Enable tests marked as integration",
    )


def pytest_configure(config: Config) -> None:
    # Disable the tests marked as "integration" by default,
    # unless the user gives the "--integration" CLI option.
    markerexpr = getattr(config.option, "markexpr", "")
    if not config.option.integration:
        if markerexpr:
            setattr(config.option, "markexpr", f"({markerexpr}) and not integration")
        else:
            setattr(config.option, "markexpr", "not integration")


@pytest.fixture(scope="session", autouse=True)
def test_ns() -> str:
    """Test namespace for etcd isolation across all tests."""
    return f"test-{secrets.token_hex(8)}"


@pytest.fixture
async def etcd(
    etcd_container: tuple[str, HostPortPairModel],  # noqa: F811
    test_ns: str,
) -> AsyncIterator[AsyncEtcd]:
    """
    Shared etcd fixture for all tests.
    Creates a real AsyncEtcd client with proper scope prefixing.
    """
    etcd = AsyncEtcd(
        addrs=[etcd_container[1].to_legacy()],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/testing",
            ConfigScopes.NODE: "node/i-test",
        },
    )
    try:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        yield etcd
    finally:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        await etcd.close()
        del etcd


@pytest.fixture(scope="session")
def database_connection(
    postgres_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> Iterator[ExtendedAsyncSAEngine]:
    """
    Database connection only - no table creation.
    Use with `with_tables` from ai.backend.testutils.db for selective table loading.

    This is a lightweight alternative to `database_engine` that doesn't
    create any tables or run migrations. Tables should be created per-test
    using the `with_tables` context manager.
    """
    _, addr = postgres_container
    url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"

    engine = create_async_engine(
        url,
        pool_size=8,
        pool_pre_ping=False,
        max_overflow=64,
    )

    yield engine

    asyncio.run(engine.dispose())
