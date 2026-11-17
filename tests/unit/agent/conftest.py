import secrets
from collections.abc import AsyncIterator, Generator
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from zmq.auth.certs import create_certificates

from ai.backend.agent import agent as agent_module
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.testutils.bootstrap import (  # noqa: F401
    ETCD_PASSWORD,
    ETCD_USER,
    etcd_container,
    redis_container,
)

pytest_plugins = [
    "ai.backend.testutils.otel",
]


@pytest.fixture(scope="session")
def test_id() -> str:
    return f"testing-{secrets.token_urlsafe(8)}"


@pytest.fixture(scope="session")
def rpc_auth_key_config(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Agent config entries pointing at freshly generated RPC auth key files."""
    key_dir = tmp_path_factory.mktemp("rpc-auth-keys")
    manager_public_key, _ = create_certificates(key_dir, "manager")
    _, agent_keypair = create_certificates(key_dir, "agent")
    return {
        "rpc-auth-manager-public-key": Path(manager_public_key),
        "rpc-auth-agent-keypair": Path(agent_keypair),
    }


@pytest.fixture(scope="session", autouse=True)
def test_local_instance_id(session_mocker: MockerFixture, test_id: str) -> Generator[None]:
    mock_generate_local_instance_id = session_mocker.patch.object(
        agent_module,
        "generate_local_instance_id",
    )
    mock_generate_local_instance_id.return_value = f"i-{test_id}"
    yield


@pytest.fixture
async def etcd(
    etcd_container: tuple[str, HostPortPairModel],  # noqa: F811
    test_ns: str,
) -> AsyncIterator[AsyncEtcd]:
    async with AsyncEtcd(
        addrs=[etcd_container[1].to_legacy()],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/testing",
            ConfigScopes.NODE: "node/i-test",
        },
        credentials={"user": ETCD_USER, "password": ETCD_PASSWORD},
    ) as etcd:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        yield etcd
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
