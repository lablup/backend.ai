"""
The distro probe must address local images by the name Docker knows them by, and must still
resolve the C library of images that have no ``ldd`` by executing the library itself.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError
from pytest_mock import MockerFixture

from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.common.types import AutoPullBehavior, ImageConfig

LDD_OUTPUT = ["ldd (Ubuntu GLIBC 2.35-0ubuntu3.4) 2.35\n"]
GLIBC_BANNER = [
    "GNU C Library (Debian GLIBC 2.41-12+deb13u3) stable release version 2.41.\n"
    "Copyright (C) 2025 Free Software Foundation, Inc.\n"
]
MUSL_LOADER_OUTPUT = [
    "musl libc (aarch64)\nVersion 1.2.6\nDynamic Program Loader\n"
    "Usage: /lib/ld-musl-aarch64.so.1 [options] [--] pathname [args]\n"
]

LDD = ("ldd", "--version")
MULTIARCH_GLIBC = ("/lib/x86_64-linux-gnu/libc.so.6",)
MUSL_LOADER_ARM64 = ("/lib/ld-musl-aarch64.so.1",)

# Answers keyed by probe command: output chunks, or None when the binary is absent from the image
# (Docker then fails the container start with an OCI "executable file not found" error).
ProbeAnswers = dict[tuple[str, ...], list[str] | None]


def _image_config(
    canonical: str, registry_name: str, *, is_local: bool, architecture: str = "x86_64"
) -> ImageConfig:
    return ImageConfig(
        architecture=architecture,
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


class FakeProbeDocker:
    """A Docker stand-in whose probe containers answer per command and record their lifecycle."""

    def __init__(self, answers: ProbeAnswers) -> None:
        self.answers = answers
        self.created: list[dict[str, Any]] = []
        self.deleted: list[tuple[str, ...]] = []
        self.containers = MagicMock()
        self.containers.create = self._create

    @property
    def created_commands(self) -> list[tuple[str, ...]]:
        return [tuple(config["Cmd"]) for config in self.created]

    async def _create(self, config: dict[str, Any]) -> MagicMock:
        self.created.append(config)
        cmd = tuple(config["Cmd"])
        answer = self.answers.get(cmd)
        container = MagicMock()
        if answer is None:
            container.start = AsyncMock(
                side_effect=DockerError(
                    400,
                    "OCI runtime create failed: runc create failed: unable to start "
                    f'container process: exec: "{cmd[0]}": stat {cmd[0]}: '
                    "no such file or directory",
                )
            )
        else:
            container.start = AsyncMock()
        container.wait = AsyncMock()
        container.log = AsyncMock(return_value=answer or [])

        async def _delete(**_kwargs: Any) -> None:
            self.deleted.append(cmd)

        container.delete = _delete
        return container


@pytest.fixture
def probe_docker(mocker: MockerFixture) -> Callable[[ProbeAnswers], FakeProbeDocker]:
    """Install a fake Docker whose probe containers answer according to the given table."""

    def _install(answers: ProbeAnswers) -> FakeProbeDocker:
        fake = FakeProbeDocker(answers)

        @asynccontextmanager
        async def _docker() -> AsyncIterator[FakeProbeDocker]:
            yield fake

        mocker.patch("ai.backend.agent.docker.agent.Docker", _docker)
        return fake

    return _install


@pytest.fixture
def created_configs(
    probe_docker: Callable[[ProbeAnswers], FakeProbeDocker],
) -> list[dict[str, Any]]:
    """Capture the container config the distro probe sends to Docker (ldd present)."""
    return probe_docker({LDD: LDD_OUTPUT}).created


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


class TestResolveImageDistroWithoutLdd:
    async def test_ldd_present_runs_a_single_probe(
        self,
        agent: DockerAgent,
        probe_docker: Callable[[ProbeAnswers], FakeProbeDocker],
    ) -> None:
        """Images with ldd keep the one-container probe and its result is cached."""
        fake = probe_docker({LDD: LDD_OUTPUT, MULTIARCH_GLIBC: GLIBC_BANNER})
        image = _image_config("cr.backend.ai/stable/python:3.9-ubuntu22.04", "cr", is_local=False)

        assert await agent.resolve_image_distro(image) == "ubuntu22.04"

        assert fake.created_commands == [LDD]
        assert fake.deleted == [LDD]
        set_image_distro = agent.valkey_stat_client.set_image_distro
        assert isinstance(set_image_distro, AsyncMock)
        set_image_distro.assert_awaited_once_with(
            "2140e699b3beaf7f96a0081fd9c9406bc3832b435cdb60dfa2d261f7d2f34a1c", "ubuntu22.04"
        )

    async def test_missing_ldd_falls_back_to_running_glibc_itself(
        self,
        agent: DockerAgent,
        probe_docker: Callable[[ProbeAnswers], FakeProbeDocker],
    ) -> None:
        """A distroless glibc image has no ldd but libc.so.6 prints its release version."""
        fake = probe_docker({LDD: None, MULTIARCH_GLIBC: GLIBC_BANNER})
        image = _image_config("cr.backend.ai/stable/app:distroless", "cr", is_local=False)

        assert await agent.resolve_image_distro(image) == "ubuntu24.04"

        assert fake.created_commands == [LDD, MULTIARCH_GLIBC]
        assert fake.deleted == [LDD, MULTIARCH_GLIBC], "every probe container is removed"

    @pytest.mark.parametrize(
        "architecture",
        [pytest.param("aarch64", id="linux-spelling"), pytest.param("arm64", id="docker-spelling")],
    )
    async def test_missing_ldd_falls_back_to_the_musl_loader_for_the_image_arch(
        self,
        agent: DockerAgent,
        probe_docker: Callable[[ProbeAnswers], FakeProbeDocker],
        architecture: str,
    ) -> None:
        """The musl loader prints its banner when run without arguments; the path is per arch."""
        fake = probe_docker({MUSL_LOADER_ARM64: MUSL_LOADER_OUTPUT})
        image = _image_config(
            "cr.backend.ai/stable/app:alpine", "cr", is_local=False, architecture=architecture
        )

        assert await agent.resolve_image_distro(image) == "alpine3.8"

        assert fake.created_commands[0] == LDD
        assert fake.created_commands[-1] == MUSL_LOADER_ARM64
        assert "/lib/aarch64-linux-gnu/libc.so.6" in {c[0] for c in fake.created_commands}
        assert fake.deleted == fake.created_commands

    async def test_unrecognized_ldd_output_falls_through_to_the_library(
        self,
        agent: DockerAgent,
        probe_docker: Callable[[ProbeAnswers], FakeProbeDocker],
    ) -> None:
        """An ldd that runs but prints nothing recognizable is not the end of the search."""
        fake = probe_docker({
            LDD: ["ldd: exited with unknown exit code (127)\n"],
            MULTIARCH_GLIBC: GLIBC_BANNER,
        })
        image = _image_config("cr.backend.ai/stable/app:odd", "cr", is_local=False)

        assert await agent.resolve_image_distro(image) == "ubuntu24.04"
        assert fake.created_commands == [LDD, MULTIARCH_GLIBC]

    async def test_no_probe_works_raises_and_cleans_up(
        self,
        agent: DockerAgent,
        probe_docker: Callable[[ProbeAnswers], FakeProbeDocker],
    ) -> None:
        """When nothing answers, the error names what was tried and no container is left behind."""
        fake = probe_docker({})
        image = _image_config("cr.backend.ai/stable/app:scratch", "cr", is_local=False)

        with pytest.raises(RuntimeError, match="tried: ldd --version, /lib/x86_64-linux-gnu"):
            await agent.resolve_image_distro(image)

        assert len(fake.created_commands) == 7
        assert fake.deleted == fake.created_commands
        set_image_distro = agent.valkey_stat_client.set_image_distro
        assert isinstance(set_image_distro, AsyncMock)
        set_image_distro.assert_not_awaited()
