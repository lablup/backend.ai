from __future__ import annotations

import logging
from pathlib import Path

import pytest

from ai.backend.agent.containerd.scratch import ScratchDirs
from ai.backend.agent.containerd.trusted_storage import (
    attach_trusted_storage,
    detach_trusted_storage,
    release_scratch,
)
from ai.backend.agent.errors.containerd import TrustedStorageUnavailable

from .fakes import FakeLosetup

SIZE = 4 * 2**20


class TestAttach:
    async def test_creates_a_sparse_file_and_returns_the_loop_device(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        backing = tmp_path / "store.img"

        loop = await attach_trusted_storage(backing, SIZE)

        assert loop == Path("/dev/loop0")
        assert backing.stat().st_size == SIZE
        assert backing.stat().st_blocks == 0
        assert oct(backing.stat().st_mode & 0o777) == "0o600"
        assert ("--find", "--show", "--nooverlap", str(backing)) in losetup.calls

    async def test_losetup_failure_raises_and_removes_the_file(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        losetup.failing.add("--find")
        backing = tmp_path / "store.img"

        with pytest.raises(TrustedStorageUnavailable, match="injected failure"):
            await attach_trusted_storage(backing, SIZE)

        assert not backing.exists()

    async def test_missing_directory_raises(self, tmp_path: Path, losetup: FakeLosetup) -> None:
        with pytest.raises(TrustedStorageUnavailable):
            await attach_trusted_storage(tmp_path / "absent" / "store.img", SIZE)

        assert losetup.calls == []


class TestDetach:
    async def test_detaches_the_loop_device_and_keeps_the_file(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        backing = tmp_path / "store.img"
        await attach_trusted_storage(backing, SIZE)

        assert await detach_trusted_storage(backing) is True

        assert losetup.loops == {}
        assert backing.exists()

    async def test_is_idempotent(self, tmp_path: Path, losetup: FakeLosetup) -> None:
        backing = tmp_path / "store.img"
        await attach_trusted_storage(backing, SIZE)

        await detach_trusted_storage(backing)
        assert await detach_trusted_storage(backing) is True

        assert losetup.verbs.count("--detach") == 1

    async def test_missing_file_is_nothing_to_detach(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        assert await detach_trusted_storage(tmp_path / "absent.img") is True
        assert losetup.calls == []

    async def test_failure_is_logged_not_raised(
        self, tmp_path: Path, losetup: FakeLosetup, caplog: pytest.LogCaptureFixture
    ) -> None:
        backing = tmp_path / "store.img"
        await attach_trusted_storage(backing, SIZE)
        losetup.failing.add("--detach")

        with caplog.at_level(logging.WARNING):
            assert await detach_trusted_storage(backing) is False

        assert backing.exists()
        assert any("trusted storage detach failed" in r.getMessage() for r in caplog.records)


class TestReleaseScratch:
    async def test_detaches_then_removes_the_scratch(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        dirs = ScratchDirs.for_kernel(tmp_path, "k1")
        dirs.root.mkdir()
        await attach_trusted_storage(dirs.trusted_store, SIZE)

        await release_scratch(tmp_path, "k1")

        assert losetup.loops == {}
        assert not dirs.root.exists()

    async def test_scratch_is_kept_while_the_device_stays_attached(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        dirs = ScratchDirs.for_kernel(tmp_path, "k1")
        dirs.root.mkdir()
        await attach_trusted_storage(dirs.trusted_store, SIZE)
        losetup.failing.add("--detach")

        await release_scratch(tmp_path, "k1")

        assert dirs.trusted_store.exists()
