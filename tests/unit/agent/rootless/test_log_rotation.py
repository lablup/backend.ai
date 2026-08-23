"""In-place rotation of a container log the container is still writing to.

The container holds the descriptor for its whole life, so the usual rename-and-reopen would leave
it appending to a file nobody reads — the log would simply stop, with no error anywhere. Rotation
therefore copies the tail out and truncates in place, and the properties that keeps (the layout the
reader expects, and a bounded total) are what these tests hold to.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ai.backend.agent.containerd.log_writer import LOG_FILE_COUNT, max_file_size, rotated_path
from ai.backend.agent.rootless.base import RootlessOciRuntime

# 5 files of 100 bytes each, matching the containerd writer's split.
_TOTAL = 500
_MAX_SIZE = max_file_size(_TOTAL)


@pytest.fixture
def active(tmp_path: Path) -> Path:
    return tmp_path / "kernel-1.log"


def _rotate(active: Path, total: int = _TOTAL) -> None:
    RootlessOciRuntime._rotate_log(active, total)


class TestThreshold:
    def test_a_log_under_the_cap_is_untouched(self, active: Path) -> None:
        active.write_bytes(b"x" * (_MAX_SIZE - 1))

        _rotate(active)

        assert active.stat().st_size == _MAX_SIZE - 1
        assert not rotated_path(active, 1).exists()

    def test_a_full_log_is_rotated(self, active: Path) -> None:
        active.write_bytes(b"x" * _MAX_SIZE)

        _rotate(active)

        assert active.stat().st_size == 0
        assert rotated_path(active, 1).read_bytes() == b"x" * _MAX_SIZE

    def test_a_log_that_vanished_is_not_an_error(self, active: Path) -> None:
        """The sweep is driven by a glob taken moments earlier; a kernel that terminated in between
        has had its log unlinked. Raising here would abort the rest of the pass."""
        _rotate(active)


class TestContentPreserved:
    def test_the_container_keeps_appending_to_the_same_inode(self, active: Path) -> None:
        """The point of truncating rather than renaming: the writer's O_APPEND descriptor must
        still land in the file the reader serves."""
        fd = os.open(active, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, b"x" * _MAX_SIZE)
            _rotate(active)
            os.write(fd, b"after")
        finally:
            os.close(fd)

        assert active.read_bytes() == b"after"

    def test_an_overshooting_log_keeps_only_its_newest_bytes(self, active: Path) -> None:
        """The cap is soft — a burst can outrun the check interval — but the *total* is only
        bounded because every file is. Copying the whole oversized active file across would put a
        single rotated file over the entire budget."""
        active.write_bytes(b"O" * (_MAX_SIZE * 4) + b"N" * _MAX_SIZE)

        _rotate(active)

        assert rotated_path(active, 1).read_bytes() == b"N" * _MAX_SIZE


class TestFileLayout:
    def test_rotated_files_shift_along(self, active: Path) -> None:
        active.write_bytes(b"new" + b"x" * _MAX_SIZE)
        rotated_path(active, 1).write_bytes(b"one")
        rotated_path(active, 2).write_bytes(b"two")

        _rotate(active)

        assert rotated_path(active, 2).read_bytes() == b"one"
        assert rotated_path(active, 3).read_bytes() == b"two"

    def test_the_oldest_file_is_dropped(self, active: Path) -> None:
        """Otherwise the budget is not a budget: the node accumulates one more file per rotation
        for the life of the kernel."""
        active.write_bytes(b"x" * _MAX_SIZE)
        for index in range(1, LOG_FILE_COUNT):
            rotated_path(active, index).write_bytes(f"gen{index}".encode())

        _rotate(active)

        assert not rotated_path(active, LOG_FILE_COUNT).exists()
        assert rotated_path(active, LOG_FILE_COUNT - 1).read_bytes() == b"gen3"

    def test_the_total_stays_within_the_budget(self, active: Path) -> None:
        """What the whole exercise is for. Rotate many times over and the on-disk set must not
        exceed `container_logs.max_length`."""
        for generation in range(LOG_FILE_COUNT * 3):
            with active.open("ab") as f:
                f.write(bytes([65 + generation % 26]) * _MAX_SIZE)
            _rotate(active)

        total = active.stat().st_size + sum(
            rotated_path(active, i).stat().st_size
            for i in range(1, LOG_FILE_COUNT)
            if rotated_path(active, i).exists()
        )
        assert total <= _TOTAL
