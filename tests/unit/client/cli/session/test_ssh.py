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

    def close(self) -> None:
        pass


class FakeProxyProc:
    """A proxy that exits on the first stop request it does not ignore."""

    stdout: FakeStdout
    returncode: int
    ignored_stops: int
    stops: list[str]
    _exited: bool

    def __init__(self, port: int, ignored_stops: int = 0) -> None:
        self.stdout = FakeStdout([f"listening at 127.0.0.1:{port}\n".encode()])
        self.returncode = 0
        self.ignored_stops = ignored_stops
        self.stops = []
        self._exited = False

    def _stop(self, name: str, force: bool = False) -> None:
        self.stops.append(name)
        if force or len(self.stops) > self.ignored_stops:
            self._exited = True

    def send_signal(self, signum: int) -> None:
        self._stop("interrupt")

    def terminate(self) -> None:
        self._stop("terminate")

    def kill(self) -> None:
        self._stop("kill", force=True)

    def wait(self, timeout: float | None = None) -> int:
        if not self._exited:
            if timeout is None:
                raise AssertionError("waited forever on a proxy that has not exited")
            raise subprocess.TimeoutExpired("sshd proxy", timeout)
        return self.returncode


def _download_dest(cmd: Sequence[str]) -> Path:
    """Emulate the `--dest` option of `backend.ai session download` (default: cwd)."""
    if "--dest" in cmd:
        return Path(cmd[cmd.index("--dest") + 1])
    return Path.cwd()


@pytest.fixture
def fake_ssh_subprocess(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Callable[..., list[FakeProxyProc]]:
    """Install stubs for the `session download` and `app ... sshd` subprocesses,
    and point `~/.ssh` at a temporary home directory."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir))

<<<<<<< HEAD
    def install(barrier: threading.Barrier | None = None, download_fails: bool = False) -> None:
=======
    def install(
        barrier: threading.Barrier | None = None,
        download_fails: bool = False,
        key_content: bytes = KEY_CONTENT,
        ignored_stops: int = 0,
    ) -> list[FakeProxyProc]:
        proxies: list[FakeProxyProc] = []

>>>>>>> 188dfe4f9 (fix(BA-8310): stop the session ssh proxy and remove its key on exit (#17304))
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
            proxy = FakeProxyProc(int(bind_addr.rsplit(":", maxsplit=1)[1]), ignored_stops)
            proxies.append(proxy)
            return proxy

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(subprocess, "Popen", fake_popen)
        return proxies

    return install


def test_container_ssh_ctx_concurrent_invocations_in_same_cwd(
    fake_ssh_subprocess: Callable[..., list[FakeProxyProc]],
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
    fake_ssh_subprocess: Callable[..., list[FakeProxyProc]],
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
<<<<<<< HEAD
=======


def test_container_ssh_ctx_yields_none_when_the_session_holds_no_private_key(
    fake_ssh_subprocess: Callable[..., list[FakeProxyProc]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A user who uploaded only a public key gets an empty `id_container`."""
    monkeypatch.chdir(tmp_path)
    fake_ssh_subprocess(key_content=b"")

    with container_ssh_ctx("mock-session", 9922) as key_path:
        assert key_path is None

    assert not list((tmp_path / "home" / ".ssh").iterdir())


@pytest.mark.parametrize(
    ("ignored_stops", "expected_stops"),
    [
        (0, ["interrupt"]),
        (1, ["interrupt", "terminate"]),
        (2, ["interrupt", "terminate", "kill"]),
    ],
    ids=["exits-on-interrupt", "ignores-interrupt", "ignores-terminate"],
)
def test_container_ssh_ctx_stops_the_proxy_and_removes_the_key(
    fake_ssh_subprocess: Callable[..., list[FakeProxyProc]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    ignored_stops: int,
    expected_stops: list[str],
) -> None:
    """A proxy that ignores SIGINT must not leave the call hanging or the key on disk (BA-8310)."""
    monkeypatch.chdir(tmp_path)
    proxies = fake_ssh_subprocess(ignored_stops=ignored_stops)

    with container_ssh_ctx("mock-session", 9922) as key_path:
        assert key_path is not None

    assert proxies[0].stops == expected_stops
    assert not list((tmp_path / "home" / ".ssh").iterdir())


class TestSshAndScpCommandsWithoutSessionKey:
    """`session ssh` and `session scp` for a user who uploaded only a public key."""

    @pytest.fixture
    def ran_commands(self, monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
        """Make the session hold no SSH key and record the commands `subprocess.run` gets."""

        @contextlib.contextmanager
        def no_session_key(session_ref: str, port: int) -> Iterator[Path | None]:
            yield None

        commands: list[list[str]] = []

        def record(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr(lifecycle, "container_ssh_ctx", no_session_key)
        monkeypatch.setattr(subprocess, "run", record)
        return commands

    @pytest.mark.parametrize(
        ("args", "expected"),
        [
            (
                ["ssh", "mysess"],
                [
                    "ssh",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "UserKnownHostsFile=/dev/null",
                    "-o",
                    "NoHostAuthenticationForLocalhost=yes",
                    "work@localhost",
                    "-p",
                    "9922",
                ],
            ),
            (
                ["scp", "mysess", "a", "b"],
                [
                    "scp",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "UserKnownHostsFile=/dev/null",
                    "-o",
                    "NoHostAuthenticationForLocalhost=yes",
                    "-P",
                    "9922",
                    "a",
                    "b",
                ],
            ),
        ],
        ids=["ssh", "scp"],
    )
    def test_passes_no_identity(
        self, ran_commands: list[list[str]], args: list[str], expected: list[str]
    ) -> None:
        result = CliRunner().invoke(lifecycle.session, args)

        assert result.exit_code == 0, result.output
        assert ran_commands == [expected]

    @pytest.mark.parametrize(
        "options",
        [
            ["-i", "mykey"],
            ["-ikey"],
            ["-qi", "mykey"],
            ["-o", "BatchMode=yes"],
        ],
        ids=["value-apart", "value-attached", "bundled-flags", "other-value-option"],
    )
    def test_scp_places_extra_options_before_the_paths(
        self, ran_commands: list[list[str]], options: list[str]
    ) -> None:
        # click takes `a` and `b` as SRC and DST, and passes the options and `c` on as extra
        # arguments. `c` follows the options so that an option taking it as its value shows.
        result = CliRunner().invoke(lifecycle.session, ["scp", "mysess", "a", "b", *options, "c"])

        assert result.exit_code == 0, result.output
        assert ran_commands == [
            [
                "scp",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "NoHostAuthenticationForLocalhost=yes",
                "-P",
                "9922",
                *options,
                "a",
                "b",
                "c",
            ]
        ]
>>>>>>> 188dfe4f9 (fix(BA-8310): stop the session ssh proxy and remove its key on exit (#17304))
