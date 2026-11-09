from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.containerd import trusted_storage
from ai.backend.agent.containerd.trusted_storage import (
    attach_trusted_storage,
    detach_trusted_storage,
    release_scratch,
    trusted_store_path,
)
from ai.backend.agent.errors.containerd import TrustedStorageUnavailable

from .fakes import FakeLosetup

SIZE = 4 * 2**20


class TestAttach:
    async def test_creates_a_private_sparse_file_and_returns_the_loop_device(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        backing = tmp_path / "k1" / "store.img"

        loop = await attach_trusted_storage(backing, SIZE)

        assert loop == Path("/dev/loop0")
        assert backing.stat().st_size == SIZE
        assert backing.stat().st_mode & 0o777 == 0o600
        assert ("--find", "--show", "--nooverlap", str(backing)) in losetup.calls

    async def test_losetup_failure_removes_the_file(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        losetup.failing.add("--find")
        backing = tmp_path / "store.img"

        with pytest.raises(TrustedStorageUnavailable, match="injected failure"):
            await attach_trusted_storage(backing, SIZE)

        assert not backing.exists()

    async def test_losetup_exit_status_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = tmp_path / "losetup"
        script.write_text("#!/bin/sh\necho 'no free loop' >&2\nexit 7\n")
        script.chmod(0o755)
        monkeypatch.setattr(trusted_storage, "_LOSETUP", str(script))

        with pytest.raises(TrustedStorageUnavailable, match="exited with 7: no free loop"):
            await attach_trusted_storage(tmp_path / "store.img", SIZE)

    async def test_unexpected_device_output_removes_the_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        script = tmp_path / "losetup"
        script.write_text("#!/bin/sh\necho garbage\n")
        script.chmod(0o755)
        monkeypatch.setattr(trusted_storage, "_LOSETUP", str(script))
        backing = tmp_path / "store.img"

        with pytest.raises(TrustedStorageUnavailable, match="unexpected device"):
            await attach_trusted_storage(backing, SIZE)

        assert not backing.exists()


class TestDetach:
    async def test_missing_backing_file_makes_no_losetup_call(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        assert await detach_trusted_storage(tmp_path / "gone.img")
        assert losetup.calls == []

    async def test_failed_query_of_an_existing_file_is_a_failed_detach(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        backing = tmp_path / "here.img"
        backing.write_bytes(b"")
        losetup.failing.add("--noheadings")

        assert not await detach_trusted_storage(backing)


class TestReleaseScratch:
    async def test_detaches_before_removing_the_scratch(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        await attach_trusted_storage(trusted_store_path(tmp_path, "k1"), SIZE)

        await release_scratch(tmp_path, "k1")

        assert losetup.loops == {}
        assert not (tmp_path / "k1").exists()

    async def test_keeps_the_scratch_when_the_detach_fails(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        backing = trusted_store_path(tmp_path, "k1")
        await attach_trusted_storage(backing, SIZE)
        losetup.failing.add("--detach")

        await release_scratch(tmp_path, "k1")

        assert backing.exists()

    async def test_scratch_without_a_trusted_storage_is_just_removed(
        self, tmp_path: Path, losetup: FakeLosetup
    ) -> None:
        (tmp_path / "k1").mkdir()

        await release_scratch(tmp_path, "k1")

        assert losetup.calls == []
        assert not (tmp_path / "k1").exists()
