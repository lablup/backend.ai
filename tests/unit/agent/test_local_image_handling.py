"""Local (``type=local`` registry) images must never be pulled from a registry."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.agent.dummy.agent import DummyAgent
from ai.backend.common.types import AgentId, AutoPullBehavior, ImageConfig


def _image_config(canonical: str, registry_name: str, *, is_local: bool) -> ImageConfig:
    return ImageConfig(
        architecture="x86_64",
        project="",
        canonical=canonical,
        is_local=is_local,
        digest="sha256:2140e699b3beaf7f96a0081fd9c9406bc3832b435cdb60dfa2d261f7d2f34a1c",
        labels={},
        repo_digest=None,
        registry={
            "name": registry_name,
            "url": "http://127.0.0.1",
            "username": None,
            "password": None,
        },
        auto_pull=AutoPullBehavior.DIGEST,
    )


LOCAL_IMAGE = _image_config("local/ngc-pytorch:26.07-py3", "local", is_local=True)
REMOTE_IMAGE = _image_config(
    "cr.backend.ai/stable/python:3.9-ubuntu20.04", "cr.backend.ai", is_local=False
)


class _ImmediateBackgroundTaskManager:
    """Runs the task inline so the test observes its effects without a real event loop task."""

    async def start(self, func: Any, **kwargs: Any) -> uuid.UUID:
        await func(AsyncMock(), **kwargs)
        return uuid.uuid4()


@dataclass
class AgentUnderTest:
    """A bare agent carrying only what ``check_and_pull()`` touches, plus its stubs."""

    agent: DummyAgent
    check_image: AsyncMock
    pull_image: AsyncMock
    anycast_event: AsyncMock


@pytest.fixture
def agent() -> AgentUnderTest:
    instance = object.__new__(DummyAgent)
    check_image = AsyncMock(return_value=True)
    pull_image = AsyncMock()
    anycast_event = AsyncMock()
    setattr(instance, "id", AgentId("i-test"))
    setattr(instance, "_active_pulls", {})
    setattr(instance, "background_task_manager", _ImmediateBackgroundTaskManager())
    setattr(instance, "local_config", SimpleNamespace(api=SimpleNamespace(pull_timeout=10.0)))
    setattr(instance, "check_image", check_image)
    setattr(instance, "pull_image", pull_image)
    setattr(instance, "anycast_event", anycast_event)
    return AgentUnderTest(instance, check_image, pull_image, anycast_event)


class TestCheckAndPull:
    async def test_local_image_is_never_pulled(self, agent: AgentUnderTest) -> None:
        """A local image lives in the Docker daemon already; pulling it is a hard error."""
        await agent.agent.check_and_pull({"local/ngc-pytorch:26.07-py3": LOCAL_IMAGE})

        agent.check_image.assert_not_awaited()
        agent.pull_image.assert_not_awaited()

    async def test_local_image_still_reports_pull_finished(self, agent: AgentUnderTest) -> None:
        """The scheduler waits for this event, so skipping the pull must not skip the event."""
        await agent.agent.check_and_pull({"local/ngc-pytorch:26.07-py3": LOCAL_IMAGE})

        (call,) = agent.anycast_event.await_args_list
        assert type(call.args[0]).__name__ == "ImagePullFinishedEvent"

    async def test_remote_image_is_pulled_when_missing(self, agent: AgentUnderTest) -> None:
        """The local-image guard must not disable pulling for ordinary registry images."""
        await agent.agent.check_and_pull({
            "cr.backend.ai/stable/python:3.9-ubuntu20.04": REMOTE_IMAGE
        })

        agent.check_image.assert_awaited_once()
        agent.pull_image.assert_awaited_once()
