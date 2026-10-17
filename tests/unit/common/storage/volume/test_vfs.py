from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.storage.volume.vfs import (
    VfsVolumeStatusCheck,
    VfsVolumeStatusCheckArgs,
)

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="the mount read runs GNU stat")

MARKER_FILENAME = ".backend.ai-volume-id"
MARKER_VOLUME_ID = StorageVolumeID(uuid.uuid4())


def _make_check(mount_path: Path) -> VfsVolumeStatusCheck:
    return VfsVolumeStatusCheck(
        VfsVolumeStatusCheckArgs(
            volume_id=StorageVolumeID(uuid.uuid4()),
            mount_path=mount_path,
            marker_filename=MARKER_FILENAME,
        )
    )


class TestVfsVolumeStatusCheck:
    @pytest.fixture
    def mount_with_marker(self, tmp_path: Path) -> Path:
        (tmp_path / MARKER_FILENAME).write_text(f"{MARKER_VOLUME_ID}\n")
        return tmp_path

    @pytest.fixture
    def mount_without_marker(self, tmp_path: Path) -> Path:
        return tmp_path

    @pytest.fixture
    def mount_with_invalid_marker(self, tmp_path: Path) -> Path:
        (tmp_path / MARKER_FILENAME).write_text("volume-1\n")
        return tmp_path

    @pytest.fixture
    def missing_mount(self, tmp_path: Path) -> Path:
        return tmp_path / "missing"

    @pytest.fixture
    def mount_with_unreadable_marker(self, tmp_path: Path) -> Path:
        (tmp_path / MARKER_FILENAME).mkdir()
        return tmp_path

    @pytest.fixture
    def commands_not_on_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PATH", str(tmp_path))

    def test_latest_is_none_before_any_check(self, mount_with_marker: Path) -> None:
        check = _make_check(mount_with_marker)

        assert check.latest() is None

    async def test_records_device_id_and_marker_volume_id(self, mount_with_marker: Path) -> None:
        check = _make_check(mount_with_marker)

        await check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.device_id == os.stat(mount_with_marker).st_dev
        assert result.marker_volume_id == MARKER_VOLUME_ID

    async def test_records_no_marker_volume_id_when_marker_file_is_absent(
        self, mount_without_marker: Path
    ) -> None:
        check = _make_check(mount_without_marker)

        await check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.device_id == os.stat(mount_without_marker).st_dev
        assert result.marker_volume_id is None

    async def test_records_error_when_marker_does_not_hold_a_volume_id(
        self, mount_with_invalid_marker: Path
    ) -> None:
        check = _make_check(mount_with_invalid_marker)

        await check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert "does not hold a volume id" in result.error_msg
        assert result.device_id == os.stat(mount_with_invalid_marker).st_dev
        assert result.marker_volume_id is None

    async def test_records_error_when_mount_cannot_be_read(self, missing_mount: Path) -> None:
        check = _make_check(missing_mount)

        await check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert f"{missing_mount} cannot be read" in result.error_msg
        assert result.device_id is None
        assert result.marker_volume_id is None

    async def test_records_error_when_marker_cannot_be_read(
        self, mount_with_unreadable_marker: Path
    ) -> None:
        check = _make_check(mount_with_unreadable_marker)

        await check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert result.marker_volume_id is None

    @pytest.mark.usefixtures("commands_not_on_path")
    async def test_records_error_when_commands_cannot_start(self, mount_with_marker: Path) -> None:
        check = _make_check(mount_with_marker)

        await check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert result.device_id is None
