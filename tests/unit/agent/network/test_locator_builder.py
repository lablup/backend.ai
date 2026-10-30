from __future__ import annotations

from typing import Any

import pytest

from ai.backend.agent.docker.locator import DockerContainerLocator
from ai.backend.agent.dummy.locator import DummyContainerLocator
from ai.backend.agent.network.locator_builder import build_container_locator
from ai.backend.common.exception import BackendAISchemaValidationFailed


def _agent_config(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent": agent,
        "container": {"scratch-root": "/tmp/scratches"},
        "resource": {},
        "etcd": {"namespace": "local", "addr": {"host": "127.0.0.1", "port": 2379}},
    }


def test_builds_the_locator_of_the_configured_backend() -> None:
    locator = build_container_locator(_agent_config({"backend": "docker"}))

    assert isinstance(locator, DockerContainerLocator)
    assert locator.rootless is False


async def test_the_dummy_backend_reports_no_containers() -> None:
    locator = build_container_locator(_agent_config({"backend": "dummy"}))

    assert isinstance(locator, DummyContainerLocator)
    await locator.open()
    assert await locator.live_sessions() == {}
    assert await locator.container_pid("cid") is None


def test_refuses_a_config_that_names_no_backend() -> None:
    with pytest.raises(BackendAISchemaValidationFailed):
        build_container_locator(_agent_config({}))
