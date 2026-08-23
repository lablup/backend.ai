from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, override

import pytest

from ai.backend.agent.containerd.runtime.interface import ImageInfo
from ai.backend.agent.rootless.base import RootlessOciRuntime


class StubRootlessRuntime(RootlessOciRuntime):
    """A backend that supplies nothing but the required hooks.

    Everything under test here is the base's, so the concrete backend must not participate. It
    subclasses the real thing rather than duck-typing it, so an interface change is a `pants check`
    error here too — a stub that has quietly stopped resembling a backend proves nothing.
    """

    backend_name: ClassVar[str] = "stub"

    @override
    def _runtime_env(self) -> dict[str, str]:
        return {}

    @override
    def _launch_argv(self, container_id: str, spec: Mapping[str, Any], gate_dir: Path) -> list[str]:
        return ["/bin/true"]

    @override
    async def _discard_container(self, container_id: str) -> None: ...

    # --- the image surface: a backend's business, never the base's ---
    @override
    async def image_exists(self, image_ref: str) -> bool:
        raise NotImplementedError

    @override
    async def image_digest(self, image_ref: str) -> str | None:
        raise NotImplementedError

    @override
    async def image_config_digest(self, image_ref: str) -> str | None:
        raise NotImplementedError

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        raise NotImplementedError

    @override
    async def list_images(self) -> Sequence[str]:
        raise NotImplementedError

    @override
    async def list_image_infos(self) -> Sequence[ImageInfo]:
        raise NotImplementedError

    @override
    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None:
        raise NotImplementedError

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        raise NotImplementedError

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        raise NotImplementedError

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        raise NotImplementedError

    @override
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
        network: str = "none",
    ) -> None:
        raise NotImplementedError

    @override
    async def commit_container(
        self,
        container_id: str,
        *,
        base_image_ref: str,
        target_ref: str,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        raise NotImplementedError


@pytest.fixture
def runtime(tmp_path: Path) -> StubRootlessRuntime:
    """A runtime whose four roots are all under tmp_path.

    Nothing here touches a container runtime, /proc or /sys/fs/cgroup: every test in this package
    drives a pure function (cgroup file contents, journal replay, log rotation, death reporting)
    and asserts on what it produced.
    """
    return StubRootlessRuntime(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=1000,
        kernel_gid=1000,
    )
