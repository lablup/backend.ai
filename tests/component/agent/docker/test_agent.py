from __future__ import annotations

import secrets
import signal
from collections.abc import Mapping
from http import HTTPStatus
from pickle import PickleError
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.agent import AgentClass
from ai.backend.agent.docker.agent import DockerAgent, _retry_on_stale_connection
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}


@pytest.fixture
async def agent(local_config: Any, test_id: str, mocker: Any, socket_relay_image: Any) -> Any:
    dummy_etcd = DummyEtcd()
    mocked_etcd_get_prefix = AsyncMock(return_value={})
    mocker.patch.object(dummy_etcd, "get_prefix", new=mocked_etcd_get_prefix)
    test_case_id = secrets.token_hex(8)
    kernel_registry = KernelRegistry()
    agent = await DockerAgent.new(
        dummy_etcd,
        local_config,
        stats_monitor=None,
        error_monitor=None,
        skip_initial_scan=True,
        agent_public_key=None,
        kernel_registry=kernel_registry,
        computers={},
        slots={},
        agent_class=AgentClass.PRIMARY,
    )  # for faster test iteration
    agent.local_instance_id = test_case_id  # use per-test private registry file
    try:
        yield agent
    finally:
        await agent.shutdown(signal.SIGTERM)


async def test_init(agent: DockerAgent, mocker: Any) -> None:
    print(agent)


imgref = ImageRef(
    name="lua",
    project="lablup",
    tag="5.3-alpine3.8",
    registry="index.docker.io",
    architecture=DEFAULT_IMAGE_ARCH,
    is_local=False,
)
query_digest = "sha256:b000000000000000000000000000000000000000000000000000000000000001"
digest_matching_image_info = {
    "Id": "sha256:b000000000000000000000000000000000000000000000000000000000000001",
    "RepoTags": [
        "lablup/lua:5.3-alpine3.8",
    ],
}
digest_mismatching_image_info = {
    "Id": "sha256:a000000000000000000000000000000000000000000000000000000000000002",
    "RepoTags": [
        "lablup/lua:5.3-alpine3.8",
    ],
}


async def test_auto_pull_digest_when_digest_matching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.DIGEST
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_digest_when_digest_mismatching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.DIGEST
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_digest_when_missing(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.DIGEST
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=HTTPStatus.NOT_FOUND,
            data={"message": "Simulated missing image"},
        ),
    )
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_called_with(imgref.canonical)


async def test_auto_pull_tag_when_digest_matching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.TAG
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_tag_when_digest_mismatching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.TAG
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_tag_when_missing(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.TAG
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=HTTPStatus.NOT_FOUND,
            data={"message": "Simulated missing image"},
        ),
    )
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_called_with(imgref.canonical)


async def test_auto_pull_none_when_digest_matching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.NONE
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_none_when_digest_mismatching(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.NONE
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


async def test_auto_pull_none_when_missing(agent: DockerAgent, mocker: Any) -> None:
    behavior = AutoPullBehavior.NONE
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=HTTPStatus.NOT_FOUND,
            data={"message": "Simulated missing image"},
        ),
    )
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    with pytest.raises(ImageNotAvailable) as e:
        await agent.check_image(imgref, query_digest, behavior)
    assert e.value.args[0] is imgref
    inspect_mock.assert_called_with(imgref.canonical)


async def test_save_last_registry_exception(agent: DockerAgent, mocker: Any) -> None:
    agent.latest_registry_written_time = MagicMock(return_value=0)  # type: ignore[attr-defined]
    mocker.patch("ai.backend.agent.agent.pickle.dump", side_effect=PickleError)
    registry_state_path = (
        agent.local_config.agent.var_base_path / f"last_registry.{agent.local_instance_id}.dat"
    )
    await agent.save_last_registry()
    assert not registry_state_path.exists()


@pytest.fixture
async def unmanaged_agent(
    local_config: Any, test_id: str, mocker: Any, socket_relay_image: Any
) -> Any:
    """
    Like the ``agent`` fixture, but leaves shutdown entirely to the test so it
    can assert against the lifecycle of the shared aiodocker client.
    """
    dummy_etcd = DummyEtcd()
    mocked_etcd_get_prefix = AsyncMock(return_value={})
    mocker.patch.object(dummy_etcd, "get_prefix", new=mocked_etcd_get_prefix)
    test_case_id = secrets.token_hex(8)
    kernel_registry = KernelRegistry()
    agent = await DockerAgent.new(
        dummy_etcd,
        local_config,
        stats_monitor=None,
        error_monitor=None,
        skip_initial_scan=True,
        agent_public_key=None,
        kernel_registry=kernel_registry,
        computers={},
        slots={},
        agent_class=AgentClass.PRIMARY,
    )
    agent.local_instance_id = test_case_id
    yield agent
    # Best-effort cleanup: close the shared client if the test did not already
    # trigger a full shutdown.  ``Docker.close`` -> ``ClientSession.close`` is
    # safe to call on an already-closed session.
    if not agent.docker.session.closed:
        await agent.docker.close()


async def test_shared_docker_client_open_after_ainit(unmanaged_agent: DockerAgent) -> None:
    assert unmanaged_agent.docker.session.closed is False


async def test_shared_docker_client_closed_after_shutdown(
    unmanaged_agent: DockerAgent,
) -> None:
    assert unmanaged_agent.docker.session.closed is False
    await unmanaged_agent.shutdown(signal.SIGTERM)
    assert unmanaged_agent.docker.session.closed is True


async def test_shared_docker_client_closed_when_super_shutdown_raises(
    unmanaged_agent: DockerAgent, mocker: Any
) -> None:
    # Simulate the base Agent.shutdown raising mid-shutdown — the shared
    # aiodocker client must still be closed so its aiohttp.ClientSession does
    # not leak.
    class _SimulatedShutdownError(Exception):
        pass

    mocker.patch(
        "ai.backend.agent.agent.AbstractAgent.shutdown",
        new=AsyncMock(side_effect=_SimulatedShutdownError("simulated")),
    )
    assert unmanaged_agent.docker.session.closed is False
    with pytest.raises(_SimulatedShutdownError):
        await unmanaged_agent.shutdown(signal.SIGTERM)
    assert unmanaged_agent.docker.session.closed is True


class TestRetryOnStaleConnection:
    """Unit tests for the stale-connection retry helper."""

    async def test_retry_on_stale_connection_retries_once_then_succeeds(self) -> None:
        calls = 0
        sentinel = object()

        async def factory() -> Any:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise aiohttp.ClientConnectionError("stale socket")
            return sentinel

        result = await _retry_on_stale_connection(factory, operation="test_op")
        assert result is sentinel
        assert calls == 2

    async def test_retry_on_stale_connection_retries_once_on_server_disconnected(self) -> None:
        calls = 0
        sentinel = object()

        async def factory() -> Any:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise aiohttp.ServerDisconnectedError()
            return sentinel

        result = await _retry_on_stale_connection(factory, operation="test_op")
        assert result is sentinel
        assert calls == 2

    async def test_retry_on_stale_connection_does_not_retry_other_errors(self) -> None:
        calls = 0
        docker_error = DockerError(
            status=HTTPStatus.CONFLICT,
            data={"message": "simulated conflict"},
        )

        async def factory() -> Any:
            nonlocal calls
            calls += 1
            raise docker_error

        with pytest.raises(DockerError) as exc_info:
            await _retry_on_stale_connection(factory, operation="test_op")
        assert exc_info.value is docker_error
        assert calls == 1

    async def test_retry_on_stale_connection_propagates_persistent_failure(self) -> None:
        calls = 0

        async def factory() -> Any:
            nonlocal calls
            calls += 1
            raise aiohttp.ClientConnectionError(f"persistent failure {calls}")

        with pytest.raises(aiohttp.ClientConnectionError):
            await _retry_on_stale_connection(factory, operation="test_op")
        # First attempt + one retry = 2 invocations total.
        assert calls == 2


async def test_check_image_retries_on_stale_connection(agent: DockerAgent, mocker: Any) -> None:
    """``check_image`` should absorb a one-shot stale-socket error."""
    behavior = AutoPullBehavior.DIGEST
    inspect_mock = AsyncMock(
        side_effect=[
            aiohttp.ClientConnectionError("stale socket"),
            digest_matching_image_info,
        ],
    )
    mocker.patch.object(agent.docker.images, "inspect", new=inspect_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    assert inspect_mock.await_count == 2
