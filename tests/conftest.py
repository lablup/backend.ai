import secrets
from collections.abc import AsyncIterator

import pytest
from pytest import Config, Parser

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.testutils.bootstrap import etcd_container  # noqa: F401


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
