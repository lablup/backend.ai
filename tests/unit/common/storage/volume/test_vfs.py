from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import Executor, ThreadPoolExecutor
from pathlib import Path

import pytest

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageCheckState, StorageStatusCheckType
from ai.backend.common.storage.volume.vfs import (
    VfsVolumeStatusCheck,
    VfsVolumeStatusCheckArgs,
)


def _make_check(mount_path: Path, executor: Executor) -> VfsVolumeStatusCheck:
    return VfsVolumeStatusCheck(
        VfsVolumeStatusCheckArgs(
            volume_name=StorageVolumeName("volume-1"),
            mount_path=mount_path,
            interval=60.0,
            initial_delay=5.0,
            executor=executor,
        )
    )


class TestVfsVolumeStatusCheck:
    @pytest.fixture
    def executor(self) -> Iterator[Executor]:
        with ThreadPoolExecutor(max_workers=1) as executor:
            yield executor

    @pytest.fixture
    def mount(self, tmp_path: Path) -> Path:
        return tmp_path

    @pytest.fixture
    def missing_mount(self, tmp_path: Path) -> Path:
        return tmp_path / "missing"

    def test_not_checked_before_any_check(self, mount: Path, executor: Executor) -> None:
        check = _make_check(mount, executor)

        result = check.latest()
        assert result.check_type == StorageStatusCheckType.VFS
        assert result.check_state == StorageCheckState.NOT_CHECKED

    async def test_records_device_id(self, mount: Path, executor: Executor) -> None:
        check = _make_check(mount, executor)

        await check.check_status()

        result = check.latest()
        assert result.check_state == StorageCheckState.CHECKED
        assert result.error_msg is None
        assert result.device_id == str(os.stat(mount).st_dev)

    async def test_records_error_when_mount_cannot_be_read(
        self, missing_mount: Path, executor: Executor
    ) -> None:
        check = _make_check(missing_mount, executor)

        await check.check_status()

        result = check.latest()
        assert result.check_state == StorageCheckState.CHECKED
        assert result.error_msg is not None
        assert f"{missing_mount} cannot be read" in result.error_msg
        assert result.device_id is None
