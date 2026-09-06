"""The distro probe container must address local images by the name Docker knows them by."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.common.types import AutoPullBehavior, ImageConfig

LDD_OUTPUT = ["ldd (Ubuntu GLIBC 2.35-0ubuntu3.4) 2.35\n"]


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


@pytest.fixture
def created_configs(mocker: MockerFixture) -> list[dict[str, Any]]:
    """Capture the container config the distro probe sends to Docker."""
    captured: list[dict[str, Any]] = []

    container = MagicMock()
    container.start = AsyncMock()
    container.wait = AsyncMock()
    container.log = AsyncMock(return_value=LDD_OUTPUT)
    container.stop = AsyncMock()
    container.delete = AsyncMock()

    async def _create(config: dict[str, Any]) -> MagicMock:
        captured.append(config)
        return container

    docker = MagicMock()
    docker.containers.create = _create

    @asynccontextmanager
    async def _docker() -> AsyncIterator[MagicMock]:
        yield docker

    mocker.patch("ai.backend.agent.docker.agent.Docker", _docker)
    return captured


@pytest.fixture
def agent() -> DockerAgent:
    """A bare agent carrying only the attributes ``resolve_image_distro()`` touches."""
    instance = object.__new__(DockerAgent)
    instance.valkey_stat_client = MagicMock()
    instance.valkey_stat_client.get_image_distro = AsyncMock(return_value=None)
    instance.valkey_stat_client.set_image_distro = AsyncMock()
    return instance


class TestResolveImageDistro:
    async def test_local_image_probed_by_its_docker_name(
        self,
        agent: DockerAgent,
        created_configs: list[dict[str, Any]],
    ) -> None:
        """`local/` is a Backend.AI registry prefix, not part of the Docker image name."""
        image = _image_config("local/ngc-pytorch:26.07-py3", "local", is_local=True)

        distro = await agent.resolve_image_distro(image)

        assert distro == "ubuntu22.04"
        assert created_configs[0]["Image"] == "ngc-pytorch:26.07-py3"

    async def test_remote_image_probed_by_its_canonical_name(
        self,
        agent: DockerAgent,
        created_configs: list[dict[str, Any]],
    ) -> None:
        """Registry-backed images keep the registry prefix, which Docker needs to resolve them."""
        image = _image_config(
            "cr.backend.ai/stable/python:3.9-ubuntu20.04", "cr.backend.ai", is_local=False
        )

        await agent.resolve_image_distro(image)

        assert created_configs[0]["Image"] == "cr.backend.ai/stable/python:3.9-ubuntu20.04"

    async def test_labelled_image_skips_the_probe(
        self,
        agent: DockerAgent,
        created_configs: list[dict[str, Any]],
    ) -> None:
        """An image declaring its base distro needs no probe container at all."""
        image = _image_config("local/ngc-pytorch:26.07-py3", "local", is_local=True)
        image["labels"] = {"ai.backend.base-distro": "ubuntu20.04"}

        assert await agent.resolve_image_distro(image) == "ubuntu20.04"
        assert created_configs == []
