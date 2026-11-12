from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.docker.agent import DockerKernelCreationContext
from ai.backend.agent.resources import Mount
from ai.backend.common.types import MountPermission, MountTypes


@dataclass(frozen=True)
class _MountPointCase:
    target: str
    source_is_dir: bool
    expected_dirs_in_work: frozenset[str]


@dataclass(frozen=True)
class _ProcessMountsSituation:
    ctx: MagicMock
    work_dir: Path
    mounts: list[Mount]


class TestProcessMounts:
    @pytest.fixture
    def process_mounts_situation(
        self, case: _MountPointCase, tmp_path: Path
    ) -> _ProcessMountsSituation:
        work_dir = tmp_path / "scratch" / "work"
        work_dir.mkdir(parents=True)
        source = tmp_path / "vfolder"
        if case.source_is_dir:
            source.mkdir()
        else:
            source.write_text("file")
        ctx = MagicMock(spec=DockerKernelCreationContext)
        ctx.work_dir = work_dir
        ctx.container_configs = []
        ctx._create_mount_points_in_work_dir = partial(
            DockerKernelCreationContext._create_mount_points_in_work_dir, ctx
        )
        mount = Mount(MountTypes.BIND, source, Path(case.target), MountPermission.READ_ONLY)
        return _ProcessMountsSituation(ctx=ctx, work_dir=work_dir, mounts=[mount])

    @pytest.mark.parametrize(
        "case",
        [
            _MountPointCase(
                target="/home/work/hejo-repo-cache/core",
                source_is_dir=True,
                expected_dirs_in_work=frozenset({"hejo-repo-cache", "hejo-repo-cache/core"}),
            ),
            _MountPointCase(
                target="/mnt/data",
                source_is_dir=True,
                expected_dirs_in_work=frozenset(),
            ),
            _MountPointCase(
                target="/home/work/config.yaml",
                source_is_dir=False,
                expected_dirs_in_work=frozenset(),
            ),
        ],
        ids=["nested-dir-below-work", "dir-outside-work", "file-below-work"],
    )
    async def test_creates_mount_points_of_dirs_below_work(
        self,
        process_mounts_situation: _ProcessMountsSituation,
        case: _MountPointCase,
    ) -> None:
        await DockerKernelCreationContext.process_mounts(
            process_mounts_situation.ctx, process_mounts_situation.mounts
        )

        work_dir = process_mounts_situation.work_dir
        dirs_in_work = {str(p.relative_to(work_dir)) for p in work_dir.rglob("*") if p.is_dir()}
        assert dirs_in_work == case.expected_dirs_in_work
