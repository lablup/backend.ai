from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.docker.agent import DockerKernelCreationContext
from ai.backend.agent.dotfile import DotfileTargetResolver
from ai.backend.agent.kubernetes.agent import KubernetesKernelCreationContext
from ai.backend.common.dotfile import InvalidDotfilePath


@pytest.fixture
def scratch_dir(tmp_path: Path) -> Path:
    path = tmp_path / "scratch"
    (path / "work").mkdir(parents=True)
    (path / "config").mkdir()
    return path


@pytest.fixture
def work_dir(scratch_dir: Path) -> Path:
    return scratch_dir / "work"


@pytest.fixture
def outside_file(tmp_path: Path) -> Path:
    path = tmp_path / "outside" / "file"
    path.parent.mkdir()
    path.write_text("original")
    return path


class TestDotfileTargetResolver:
    @pytest.mark.parametrize(
        ("raw", "relative"),
        [
            (".bashrc", ".bashrc"),
            (".aws/config", ".aws/config"),
            ("/home/work/.vimrc", ".vimrc"),
        ],
    )
    def test_resolves_under_work_dir(self, work_dir: Path, raw: str, relative: str) -> None:
        assert DotfileTargetResolver(work_dir).resolve(raw) == work_dir.resolve() / relative

    @pytest.mark.parametrize(
        "raw", ["/etc/passwd", "/home/config/kconfig.dat", "../config/kconfig.dat", "kconfig.dat"]
    )
    def test_rejects_by_path_rule(self, work_dir: Path, raw: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            DotfileTargetResolver(work_dir).resolve(raw)

    def test_rejects_file_symlink_leaving_work_dir(
        self, work_dir: Path, outside_file: Path
    ) -> None:
        (work_dir / ".bashrc").symlink_to(outside_file)
        with pytest.raises(InvalidDotfilePath):
            DotfileTargetResolver(work_dir).resolve(".bashrc")

    def test_rejects_directory_symlink_leaving_work_dir(
        self, work_dir: Path, outside_file: Path
    ) -> None:
        (work_dir / ".aws").symlink_to(outside_file.parent)
        with pytest.raises(InvalidDotfilePath):
            DotfileTargetResolver(work_dir).resolve(".aws/new-file")

    def test_rejects_dangling_symlink_leaving_work_dir(
        self, work_dir: Path, outside_file: Path
    ) -> None:
        (work_dir / ".bashrc").symlink_to(outside_file.parent / "missing")
        with pytest.raises(InvalidDotfilePath):
            DotfileTargetResolver(work_dir).resolve(".bashrc")

    def test_rejects_symlink_to_config_dir(self, scratch_dir: Path, work_dir: Path) -> None:
        (work_dir / ".link").symlink_to("../config/kconfig.dat")
        with pytest.raises(InvalidDotfilePath):
            DotfileTargetResolver(work_dir).resolve(".link")

    def test_rejects_symlink_to_work_dir_itself(self, work_dir: Path) -> None:
        (work_dir / ".link").symlink_to(".")
        with pytest.raises(InvalidDotfilePath):
            DotfileTargetResolver(work_dir).resolve(".link")

    def test_follows_symlink_inside_work_dir(self, work_dir: Path) -> None:
        (work_dir / ".real").write_text("")
        (work_dir / ".link").symlink_to(".real")
        assert DotfileTargetResolver(work_dir).resolve(".link") == work_dir.resolve() / ".real"

    def test_paths_below_work_dir_stop_at_work_dir(self, work_dir: Path) -> None:
        resolved = work_dir.resolve()
        resolver = DotfileTargetResolver(work_dir)
        target = resolver.resolve(".aws/sub/config")
        assert resolver.paths_below_work_dir(target) == [
            resolved / ".aws" / "sub" / "config",
            resolved / ".aws" / "sub",
            resolved / ".aws",
        ]


PrepareContainer = Callable[[list[dict[str, str]]], Awaitable[None]]


@pytest.fixture(params=["docker", "kubernetes"])
def prepare_container(
    request: pytest.FixtureRequest, scratch_dir: Path, mocker: MockerFixture
) -> PrepareContainer:
    """Runs a restart of the backend's `prepare_container` on a real scratch directory."""

    async def run_in_executor_sync(_executor: Any, fn: Any, *args: Any) -> Any:
        return fn(*args)

    backend: str = request.param
    context_class: Any = (
        DockerKernelCreationContext if backend == "docker" else KubernetesKernelCreationContext
    )
    kernel_class = "DockerKernel" if backend == "docker" else "KubernetesKernel"
    mocker.patch(f"ai.backend.agent.{backend}.agent.{kernel_class}")
    mocker.patch(
        f"ai.backend.agent.{backend}.agent.run_in_executor_with_context",
        side_effect=run_in_executor_sync,
    )
    config_dir = scratch_dir / "config"
    (config_dir / "environ.txt").write_text("")
    (config_dir / "resource.txt").write_text("")

    async def run(dotfiles: list[dict[str, str]]) -> None:
        ctx = MagicMock()
        ctx.restarting = True
        ctx.scratch_dir = scratch_dir
        ctx.work_dir = scratch_dir / "work"
        ctx.config_dir = config_dir
        ctx.kernel_features = frozenset()
        ctx.internal_data = {"dotfiles": dotfiles}
        ctx.get_overriding_uid.return_value = None
        ctx.get_overriding_gid.return_value = None
        await context_class.prepare_container(ctx, MagicMock(), {}, [], MagicMock())

    return run


class TestPrepareContainer:
    async def test_writes_dotfile_under_work_dir(
        self, prepare_container: PrepareContainer, work_dir: Path
    ) -> None:
        await prepare_container([
            {"path": ".aws/config", "perm": "755", "data": "a\n"},
            {"path": "/home/work/.vimrc", "perm": "644", "data": "b\n"},
        ])
        assert (work_dir / ".aws" / "config").read_text() == "a\n"
        assert (work_dir / ".vimrc").read_text() == "b\n"

    @pytest.mark.parametrize(
        "path", ["/home/config/kconfig.dat", "../config/kconfig.dat", "kconfig.dat"]
    )
    async def test_skips_stored_path_by_path_rule_and_writes_the_rest(
        self, prepare_container: PrepareContainer, scratch_dir: Path, path: str
    ) -> None:
        kconfig = scratch_dir / "config" / "kconfig.dat"
        kconfig.write_text("original")
        await prepare_container([
            {"path": path, "perm": "644", "data": "x\n"},
            {"path": ".vimrc", "perm": "644", "data": "kept\n"},
        ])
        assert kconfig.read_text() == "original"
        assert not (scratch_dir / "work" / "kconfig.dat").exists()
        assert (scratch_dir / "work" / ".vimrc").read_text() == "kept\n"

    async def test_skips_absolute_host_path(
        self, prepare_container: PrepareContainer, outside_file: Path
    ) -> None:
        await prepare_container([{"path": str(outside_file), "perm": "777", "data": "x\n"}])
        assert outside_file.read_text() == "original"
        assert outside_file.stat().st_mode & 0o777 != 0o777

    async def test_skips_symlink_left_in_work_dir_on_restart(
        self, prepare_container: PrepareContainer, work_dir: Path, outside_file: Path
    ) -> None:
        (work_dir / ".bashrc").symlink_to(outside_file)
        await prepare_container([{"path": ".bashrc", "perm": "777", "data": "x\n"}])
        assert outside_file.read_text() == "original"
        assert outside_file.stat().st_mode & 0o777 != 0o777
