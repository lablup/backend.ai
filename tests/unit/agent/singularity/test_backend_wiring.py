"""That selecting `agent.backend = "singularity"` actually reaches this backend.

The enum value is turned into a module path by string interpolation
(`importlib.import_module(f"ai.backend.agent.{backend.value}")`), so a backend can be fully
implemented and still be unreachable because one of the four wiring points was missed. Each of
these fails loudly the moment that happens.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ai.backend.agent.singularity.agent import SingularityAgent
from ai.backend.agent.singularity.runtime import SingularityRuntime
from ai.backend.agent.types import AgentBackend, get_agent_discovery
from ai.backend.manager.network.pairing import BACKEND_DRIVER, DRIVER_COMPATIBLE_BACKENDS

_CID = "kernel-1"


class TestBackendSelection:
    def test_the_enum_resolves_to_this_package(self) -> None:
        discovery = get_agent_discovery(AgentBackend.SINGULARITY)

        assert discovery.get_agent_cls() is SingularityAgent

    def test_a_kernel_can_build_its_own_runtime_client(self) -> None:
        """`create_oci_runtime` is what a kernel reaches for when it needs a short-lived client of
        its own (committing, say). Leaving it at the default sent an enroot kernel's commit to a
        containerd daemon that had never heard of the container."""
        discovery = get_agent_discovery(AgentBackend.SINGULARITY)

        assert hasattr(discovery, "create_oci_runtime")

    def test_the_manager_knows_it_speaks_the_bep_1062_data_plane(self) -> None:
        """Pairing decides which network the manager sets up for a session on this agent. Absent
        here, a singularity agent would be handed the Docker-network model it cannot implement."""
        assert "singularity" in DRIVER_COMPATIBLE_BACKENDS["cni"]
        assert BACKEND_DRIVER["singularity"] == "cni"


class TestPull:
    async def test_a_plain_http_registry_is_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """BAI clusters commonly run an internal plain-HTTP registry, and apptainer defaults to
        https — the pull then dies with "server gave HTTP response to HTTPS client" (measured
        live). The enroot backend allows the same thing via ENROOT_ALLOW_HTTP."""
        rt = SingularityRuntime(
            data_path=tmp_path / "data",
            cache_path=tmp_path / "cache",
            runtime_path=tmp_path / "run",
            state_path=tmp_path / "state",
            kernel_uid=os.geteuid(),
            kernel_gid=os.getegid(),
        )
        (tmp_path / "data").mkdir(parents=True)
        seen: list[tuple[str, ...]] = []

        async def _fake_run(*argv: str, **kwargs: object) -> tuple[int, bytes, bytes]:
            seen.append(argv)
            return 1, b"", b"stopped before touching the network"

        monkeypatch.setattr(rt, "_run", _fake_run)

        with pytest.raises(RuntimeError):
            await rt.pull_image("192.168.0.156:5000/stable/python:3.13")

        assert "--no-https" in seen[0]


class TestOpen:
    async def test_the_build_tmpdir_is_created(self, tmp_path: Path) -> None:
        """apptainer will not create APPTAINER_TMPDIR itself; it just refuses to build, and the
        failure reaches the user as an image-pull error naming a path (measured live)."""
        rt = SingularityRuntime(
            data_path=tmp_path / "data",
            cache_path=tmp_path / "cache",
            runtime_path=tmp_path / "run",
            state_path=tmp_path / "state",
            kernel_uid=os.geteuid(),
            kernel_gid=os.getegid(),
        )
        try:
            await rt.open()
            assert rt._tmp_path().is_dir()
            assert rt._runtime_env()["APPTAINER_TMPDIR"] == str(rt._tmp_path())
        finally:
            await rt.close()


class TestContainerLifecycle:
    @pytest.fixture
    def runtime(self, tmp_path: Path) -> SingularityRuntime:
        rt = SingularityRuntime(
            data_path=tmp_path / "data",
            cache_path=tmp_path / "cache",
            runtime_path=tmp_path / "run",
            state_path=tmp_path / "state",
            kernel_uid=os.geteuid(),
            kernel_gid=os.getegid(),
        )
        (tmp_path / "data").mkdir(parents=True)
        rt._sandbox("registry/py:3.12").mkdir()
        return rt

    async def test_creating_a_container_only_makes_an_overlay(
        self, runtime: SingularityRuntime
    ) -> None:
        """The whole point of the overlay: the image sandbox is shared and untouched, so creating
        a container costs two mkdirs rather than a copy of the rootfs."""
        sandbox = runtime._sandbox("registry/py:3.12")
        (sandbox / "usr").mkdir()

        await runtime.create_container(
            _CID, image_ref="registry/py:3.12", command=["/bin/sh"], oci_spec={}
        )

        overlay = runtime._overlay_dir(_CID)
        assert (overlay / "upper").is_dir()
        assert (overlay / "work").is_dir()
        assert list(sandbox.iterdir()) == [sandbox / "usr"]

    async def test_a_missing_image_is_refused(self, runtime: SingularityRuntime) -> None:
        """Launching against an absent sandbox would fail much later, inside apptainer, with a
        message about a path rather than about the image."""
        with pytest.raises(RuntimeError, match="no local sandbox"):
            await runtime.create_container(
                _CID, image_ref="registry/absent:1", command=["/bin/sh"], oci_spec={}
            )

    async def test_the_spec_and_labels_are_retained_for_the_task(
        self, runtime: SingularityRuntime
    ) -> None:
        """`_launch_argv` runs at create_task, long after this, and reads both."""
        labels = {"ai.backend.kernel-id": "k1"}

        await runtime.create_container(
            _CID,
            image_ref="registry/py:3.12",
            command=["/bin/sh"],
            oci_spec={"labels": labels, "env": {"A": "1"}},
        )

        assert runtime._labels[_CID] == labels
        assert runtime._commands[_CID] == ["/bin/sh"]
        assert runtime._images[_CID] == "registry/py:3.12"

    async def test_discarding_reclaims_the_overlay(self, runtime: SingularityRuntime) -> None:
        """Never reused (the name is the kernel id), so a leaked overlay accumulates one per
        kernel this node has ever run — and it holds the container's whole writable state."""
        await runtime.create_container(
            _CID, image_ref="registry/py:3.12", command=["/bin/sh"], oci_spec={}
        )
        (runtime._overlay_dir(_CID) / "upper" / "big").write_bytes(b"x" * 1024)

        await runtime._discard_container(_CID)

        assert not runtime._overlay_dir(_CID).exists()

    async def test_discarding_a_container_that_never_started(
        self, runtime: SingularityRuntime
    ) -> None:
        await runtime._discard_container("never-existed")

    async def test_overlayfs_own_unreadable_workdir_is_reclaimed_too(
        self, runtime: SingularityRuntime
    ) -> None:
        """The leak this caught end-to-end: overlayfs creates its own `work/work` at mode 0000,
        and `shutil.rmtree` cannot scandir that even as its owner. With `ignore_errors=True` the
        failure was silent, so every container left its whole overlay — and everything it had
        written — on disk."""
        await runtime.create_container(
            _CID, image_ref="registry/py:3.12", command=["/bin/sh"], oci_spec={}
        )
        inner = runtime._overlay_dir(_CID) / "work" / "work"
        inner.mkdir()
        (runtime._overlay_dir(_CID) / "upper" / "written-by-the-kernel").write_bytes(b"x")
        inner.chmod(0o000)

        await runtime._discard_container(_CID)

        assert not runtime._overlay_dir(_CID).exists()
