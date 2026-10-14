from __future__ import annotations

import logging
from pathlib import Path

import pytest

from ai.backend.agent.containerd.trusted_storage import (
    attach_trusted_storage,
    detach_trusted_storage,
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

    async def test_is_repeatable(self, tmp_path: Path, losetup: FakeLosetup) -> None:
        backing = tmp_path / "store.img"

        first = await attach_trusted_storage(backing, SIZE)
        second = await attach_trusted_storage(backing, SIZE)

        assert first == second
        assert losetup.verbs.count("--find") == 1

    async def test_losetup_failure_raises_and_removes_the_file(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        losetup.failing.add("--find")
        backing = tmp_path / "store.img"

        with pytest.raises(TrustedStorageUnavailable, match="injected failure"):
            await attach_trusted_storage(backing, SIZE)

        assert not backing.exists()

    async def test_unwritable_directory_raises(self, tmp_path: Path, losetup: FakeLosetup) -> None:
        with pytest.raises(TrustedStorageUnavailable):
            await attach_trusted_storage(tmp_path / "absent" / "store.img", SIZE)

        assert losetup.calls == []


class TestDetach:
    async def test_detaches_the_loop_device_and_deletes_the_file(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        backing = tmp_path / "store.img"
        await attach_trusted_storage(backing, SIZE)

        await detach_trusted_storage(backing)

        assert losetup.loops == {}
        assert not backing.exists()

    async def test_is_idempotent(self, tmp_path: Path, losetup: FakeLosetup) -> None:
        backing = tmp_path / "store.img"
        await attach_trusted_storage(backing, SIZE)

        await detach_trusted_storage(backing)
        calls = len(losetup.calls)
        await detach_trusted_storage(backing)

        assert len(losetup.calls) == calls

    async def test_failure_is_logged_not_raised_and_keeps_the_file(
        self, tmp_path: Path, losetup: FakeLosetup, caplog: pytest.LogCaptureFixture
    ) -> None:
        backing = tmp_path / "store.img"
        await attach_trusted_storage(backing, SIZE)
        losetup.failing.add("--detach")

        with caplog.at_level(logging.WARNING):
            await detach_trusted_storage(backing)

        assert backing.exists()
        assert any("trusted storage release failed" in r.getMessage() for r in caplog.records)
