from __future__ import annotations

import secrets
import signal
from pickle import PickleError
from typing import Any, Mapping
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.types import AutoPullBehavior


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}


@pytest.fixture
async def agent(local_config, test_id, mocker, socket_relay_image):
    dummy_etcd = DummyEtcd()
    mocked_etcd_get_prefix = AsyncMock(return_value={})
    mocker.patch.object(dummy_etcd, "get_prefix", new=mocked_etcd_get_prefix)
    test_case_id = secrets.token_hex(8)
    agent = await DockerAgent.new(
        dummy_etcd,
        local_config,
        stats_monitor=None,
        error_monitor=None,
        skip_initial_scan=True,
        agent_public_key=None,
    )  # for faster test iteration
    agent.local_instance_id = test_case_id  # use per-test private registry file
    try:
        yield agent
    finally:
        await agent.shutdown(signal.SIGTERM)


@pytest.mark.asyncio
async def test_init(agent, mocker):
    print(agent)


imgref = ImageRef("index.docker.io/lablup/lua:5.3-alpine3.8", architecture=DEFAULT_IMAGE_ARCH)
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


@pytest.mark.asyncio
async def test_auto_pull_digest_when_digest_matching(agent, mocker):
    behavior = AutoPullBehavior.DIGEST
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_digest_when_digest_mismatching(agent, mocker):
    behavior = AutoPullBehavior.DIGEST
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_awaited_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_digest_when_missing(agent, mocker):
    behavior = AutoPullBehavior.DIGEST
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=404,
            data={"message": "Simulated missing image"},
        ),
    )
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_called_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_tag_when_digest_matching(agent, mocker):
    behavior = AutoPullBehavior.TAG
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_tag_when_digest_mismatching(agent, mocker):
    behavior = AutoPullBehavior.TAG
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_tag_when_missing(agent, mocker):
    behavior = AutoPullBehavior.TAG
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=404,
            data={"message": "Simulated missing image"},
        ),
    )
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert pull
    inspect_mock.assert_called_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_none_when_digest_matching(agent, mocker):
    behavior = AutoPullBehavior.NONE
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_matching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_none_when_digest_mismatching(agent, mocker):
    behavior = AutoPullBehavior.NONE
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(return_value=digest_mismatching_image_info)
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    pull = await agent.check_image(imgref, query_digest, behavior)
    assert not pull
    inspect_mock.assert_awaited_with(imgref.canonical)


@pytest.mark.asyncio
async def test_auto_pull_none_when_missing(agent, mocker):
    behavior = AutoPullBehavior.NONE
    docker_mock = MagicMock()
    docker_mock.close = AsyncMock()
    docker_mock.images = MagicMock()
    inspect_mock = AsyncMock(
        side_effect=DockerError(
            status=404,
            data={"message": "Simulated missing image"},
        ),
    )
    docker_mock.images.inspect = inspect_mock
    mocker.patch("ai.backend.agent.docker.agent.Docker", return_value=docker_mock)
    with pytest.raises(ImageNotAvailable) as e:
        await agent.check_image(imgref, query_digest, behavior)
    assert e.value.args[0] is imgref
    inspect_mock.assert_called_with(imgref.canonical)


@pytest.mark.asyncio
async def test_save_last_registry_exception(agent, mocker):
    agent.latest_registry_written_time = MagicMock(return_value=0)
    mocker.patch("ai.backend.agent.agent.pickle.dump", side_effect=PickleError)
    registry_state_path = (
        agent.local_config["agent"]["var-base-path"]
        / f"last_registry.{agent.local_instance_id}.dat"
    )
    await agent.save_last_registry()
    assert not registry_state_path.exists()
