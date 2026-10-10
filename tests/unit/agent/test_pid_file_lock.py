from __future__ import annotations

import errno
import fcntl
import os
from collections.abc import Iterator
from pathlib import Path
from typing import IO, Any

import pytest

from ai.backend.agent.errors.agent import AgentAlreadyRunningError
from ai.backend.agent.server import _hold_pid_file


@pytest.fixture
def pid_file(tmp_path: Path) -> Path:
    return tmp_path / "agent.pid"


@pytest.fixture
def held(pid_file: Path) -> Iterator[IO[str]]:
    handle = _hold_pid_file(pid_file)
    assert handle is not None
    yield handle
    handle.close()


class TestHoldPidFile:
    def test_writes_own_pid(self, pid_file: Path, held: IO[str]) -> None:
        assert pid_file.read_text() == str(os.getpid())

    def test_overwrites_stale_pid(self, pid_file: Path) -> None:
        pid_file.write_text("999999999")

        handle = _hold_pid_file(pid_file)

        assert handle is not None
        assert pid_file.read_text() == str(os.getpid())
        handle.close()

    def test_second_holder_is_refused(self, pid_file: Path, held: IO[str]) -> None:
        with pytest.raises(AgentAlreadyRunningError):
            _hold_pid_file(pid_file)

        assert pid_file.read_text() == str(os.getpid())

    def test_lock_on_unlinked_file_is_not_kept(
        self, pid_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        holder_a = _hold_pid_file(pid_file)
        assert holder_a is not None
        real_flock = fcntl.flock
        holders: list[IO[str]] = []

        def flock_after_a_exits_and_c_starts(fd: Any, operation: int) -> None:
            # B has opened A's file; A unlinks and closes it, then C creates a fresh one.
            monkeypatch.setattr(fcntl, "flock", real_flock)
            pid_file.unlink()
            holder_a.close()
            holder_c = _hold_pid_file(pid_file)
            assert holder_c is not None
            holders.append(holder_c)
            real_flock(fd, operation)

        monkeypatch.setattr(fcntl, "flock", flock_after_a_exits_and_c_starts)

        try:
            with pytest.raises(AgentAlreadyRunningError):
                _hold_pid_file(pid_file)
        finally:
            for holder in holders:
                holder.close()

    def test_lock_is_released_when_handle_closes(self, pid_file: Path) -> None:
        first = _hold_pid_file(pid_file)
        assert first is not None
        first.close()

        second = _hold_pid_file(pid_file)

        assert second is not None
        second.close()

    def test_devnull_is_never_locked(self) -> None:
        first = _hold_pid_file(Path(os.devnull))
        second = _hold_pid_file(Path(os.devnull))

        assert first is None
        assert second is None

    def test_symlink_to_devnull_is_never_locked(self, tmp_path: Path) -> None:
        link = tmp_path / "pid-link"
        link.symlink_to(os.devnull)

        assert _hold_pid_file(link) is None
        assert _hold_pid_file(link) is None

    def test_directory_path_is_never_locked(self, tmp_path: Path) -> None:
        assert _hold_pid_file(tmp_path) is None


def _flock_raising(code: int) -> Any:
    def _flock(fd: Any, operation: int) -> None:
        raise OSError(code, os.strerror(code))

    return _flock


class TestFlockErrno:
    @pytest.mark.parametrize("code", [errno.EWOULDBLOCK, errno.EAGAIN])
    def test_contention_is_already_running(
        self, pid_file: Path, monkeypatch: pytest.MonkeyPatch, code: int
    ) -> None:
        monkeypatch.setattr(fcntl, "flock", _flock_raising(code))

        with pytest.raises(AgentAlreadyRunningError):
            _hold_pid_file(pid_file)

    @pytest.mark.parametrize("code", [errno.ENOLCK, errno.EOPNOTSUPP, errno.EINVAL])
    def test_unsupported_lock_runs_unlocked(
        self,
        pid_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        code: int,
    ) -> None:
        monkeypatch.setattr(fcntl, "flock", _flock_raising(code))

        assert _hold_pid_file(pid_file) is None
        assert pid_file.read_text() == str(os.getpid())
        # The logger is not configured yet when `main()` takes the lock.
        warning = capsys.readouterr().err
        assert "cannot be locked" in warning
        assert errno.errorcode[code] in warning
