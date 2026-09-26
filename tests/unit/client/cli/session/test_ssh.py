from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest

from ai.backend.client.cli.session.ssh import container_ssh_ctx

KEY_CONTENT = b"-----BEGIN OPENSSH PRIVATE KEY-----\n"


class FakeStdout:
    _lines: list[bytes]

    def __init__(self, lines: Sequence[bytes]) -> None:
        self._lines = list(lines)

    def readline(self, size: int = -1) -> bytes:
        if not self._lines:
            return b""
        return self._lines.pop(0)


class FakeProxyProc:
    stdout: FakeStdout
    returncode: int

    def __init__(self, port: int) -> None:
        self.stdout = FakeStdout([f"listening at 127.0.0.1:{port}\n".encode()])
        self.returncode = 0

    def send_signal(self, signum: int) -> None:
        pass

    def wait(self) -> int:
        return self.returncode


def _download_dest(cmd: Sequence[str]) -> Path:
    """Emulate the `--dest` option of `backend.ai session download` (default: cwd)."""
    if "--dest" in cmd:
        return Path(cmd[cmd.index("--dest") + 1])
    return Path.cwd()


@pytest.fixture
def fake_ssh_subprocess(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Callable[..., None]:
    """Install stubs for the `session download` and `app ... sshd` subprocesses,
    and point `~/.ssh` at a temporary home directory."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir))

    def install(barrier: threading.Barrier | None = None, download_fails: bool = False) -> None:
        def fake_run(cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
            # The key always lands in the destination directory under its
            # container-side basename, even when the download later fails.
            (_download_dest(cmd) / cmd[-1]).write_bytes(KEY_CONTENT)
            if barrier is not None:
                barrier.wait()
            if download_fails:
                raise subprocess.CalledProcessError(1, list(cmd), output=b"download failed")
            return subprocess.CompletedProcess(list(cmd), 0, stdout=b"")

        def fake_popen(cmd: Sequence[str], **kwargs: Any) -> FakeProxyProc:
            bind_addr = cmd[cmd.index("-b") + 1]
            return FakeProxyProc(int(bind_addr.rsplit(":", maxsplit=1)[1]))

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(subprocess, "Popen", fake_popen)

    return install


def test_container_ssh_ctx_concurrent_invocations_in_same_cwd(
    fake_ssh_subprocess: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Two `session ssh` invocations sharing a working directory must not race on the
    downloaded key file. The barrier holds both between download and rename."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    fake_ssh_subprocess(barrier=threading.Barrier(2, timeout=10))
    key_paths: dict[int, Path] = {}
    errors: dict[int, Exception] = {}

    def run_ssh_ctx(index: int, port: int) -> None:
        try:
            with container_ssh_ctx("mock-session", port) as key_path:
                key_paths[index] = key_path
                assert key_path.read_bytes() == KEY_CONTENT
        except Exception as e:
            errors[index] = e

    threads = [
        threading.Thread(target=run_ssh_ctx, args=(index, port))
        for index, port in enumerate([9922, 9923])
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent invocations failed: {errors}"
    assert len(set(key_paths.values())) == 2
    assert not list(cwd.iterdir()), "the downloaded key must not be left in the cwd"


def test_container_ssh_ctx_leaves_no_key_behind_when_download_fails(
    fake_ssh_subprocess: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    fake_ssh_subprocess(download_fails=True)

    with pytest.raises(SystemExit):
        with container_ssh_ctx("mock-session", 9922):
            pass

    assert not list(cwd.iterdir())
    assert not list((tmp_path / "home" / ".ssh").iterdir())
