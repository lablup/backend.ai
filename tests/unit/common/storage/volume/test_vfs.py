from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.storage.volume.vfs import (
    VfsVolumeStatusCheck,
    VfsVolumeStatusCheckArgs,
)

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
    def mount_with_empty_marker(self, tmp_path: Path) -> Path:
        (tmp_path / MARKER_FILENAME).write_text("\n")
        return tmp_path

    @pytest.fixture
    def mount_with_invalid_marker(self, tmp_path: Path) -> Path:
        (tmp_path / MARKER_FILENAME).write_text("volume-1\n")
        return tmp_path

    @pytest.fixture
    def mount_with_unreadable_marker(self, tmp_path: Path) -> Path:
        (tmp_path / MARKER_FILENAME).mkdir()
        return tmp_path

    @pytest.fixture
    def missing_mount(self, tmp_path: Path) -> Path:
        return tmp_path / "missing"

    def test_latest_is_none_before_any_check(self, mount_with_marker: Path) -> None:
        check = _make_check(mount_with_marker)

        assert check.latest() is None

    def test_records_device_id_and_marker_volume_id(self, mount_with_marker: Path) -> None:
        check = _make_check(mount_with_marker)

        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.device_id == os.stat(mount_with_marker).st_dev
        assert result.marker_volume_id == MARKER_VOLUME_ID

    @pytest.mark.parametrize(
        ("mount_fixture", "reason"),
        [
            ("mount_without_marker", "does not exist"),
            ("mount_with_empty_marker", "is empty"),
            ("mount_with_invalid_marker", "is not a volume id"),
        ],
    )
    def test_records_error_when_marker_does_not_hold_a_volume_id(
        self, mount_fixture: str, reason: str, request: pytest.FixtureRequest
    ) -> None:
        mount_path: Path = request.getfixturevalue(mount_fixture)
        check = _make_check(mount_path)

        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert f"{mount_path / MARKER_FILENAME} does not hold a volume id" in result.error_msg
        assert reason in result.error_msg
        assert result.device_id == os.stat(mount_path).st_dev
        assert result.marker_volume_id is None

    def test_records_error_when_mount_cannot_be_read(self, missing_mount: Path) -> None:
        check = _make_check(missing_mount)

        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert f"{missing_mount} cannot be read" in result.error_msg
        assert result.device_id is None
        assert result.marker_volume_id is None

    def test_records_error_when_marker_cannot_be_read(
        self, mount_with_unreadable_marker: Path
    ) -> None:
        check = _make_check(mount_with_unreadable_marker)

        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert "cannot be read" in result.error_msg
        assert result.device_id is None
        assert result.marker_volume_id is None
