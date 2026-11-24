import contextlib
import os
import secrets
import signal
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Final

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.pretty import print_fail, print_info

CLI_EXECUTABLE: tuple[str, ...]
if pex_path := os.environ.get("PEX", None):
    CLI_EXECUTABLE = (sys.executable, pex_path)
else:
    CLI_EXECUTABLE = (sys.executable, "-m", "ai.backend.cli")

# The proxy does not always exit on SIGINT (BA-8310), so stopping it escalates
# to SIGTERM and then SIGKILL after each of these timeouts in seconds.
_PROXY_INTERRUPT_TIMEOUT: Final[float] = 10.0
_PROXY_TERMINATE_TIMEOUT: Final[float] = 5.0


def _exited_within(proxy_proc: subprocess.Popen[bytes], timeout: float) -> bool:
    try:
        proxy_proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return True


def _stop_proxy(proxy_proc: subprocess.Popen[bytes]) -> None:
    proxy_proc.send_signal(signal.SIGINT)
    if _exited_within(proxy_proc, _PROXY_INTERRUPT_TIMEOUT):
        return
    proxy_proc.terminate()
    if _exited_within(proxy_proc, _PROXY_TERMINATE_TIMEOUT):
        return
    proxy_proc.kill()
    proxy_proc.wait()


@contextlib.contextmanager
def container_ssh_ctx(session_ref: str, port: int) -> Iterator[Path]:
    random_id = secrets.token_hex(16)
    key_filename = "id_container"
    # Create ssh directory with recommended permissions if not exists
    ssh_dir = Path("~/.ssh").expanduser()
    ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    key_path = ssh_dir / f"id_{random_id}"
    # `session download` keeps the container-side basename, so concurrent invocations
    # sharing a destination directory race on the same file. Give each one its own
    # directory, inside `ssh_dir` to keep the rename below on a single filesystem.
    with tempfile.TemporaryDirectory(dir=ssh_dir) as download_dir:
        try:
            subprocess.run(
                [
                    *CLI_EXECUTABLE,
                    "session",
                    "download",
                    "--dest",
                    download_dir,
                    session_ref,
                    key_filename,
                ],
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print_fail(f"Failed to download the SSH key from the session (exit: {e.returncode}):")
            print(e.stdout.decode())
            sys.exit(ExitCode.FAILURE)
        (Path(download_dir) / key_filename).rename(key_path)
    print_info(f"running a temporary sshd proxy at localhost:{port} ...", file=sys.stderr)
    # proxy_proc is a background process
    proxy_proc = subprocess.Popen(
        [*CLI_EXECUTABLE, "app", session_ref, "sshd", "-b", f"127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    proxy_stdout = proxy_proc.stdout
    if proxy_stdout is None:
        raise RuntimeError("Failed to capture stdout from proxy process")
    try:
        lines: list[bytes] = []
        while True:
            line = proxy_stdout.readline(1024)
            if not line:
                proxy_proc.wait()
                print_fail(
                    "Unexpected early termination of the sshd app command "
                    f"(exit: {proxy_proc.returncode}):"
                )
                print((b"\n".join(lines)).decode())
                sys.exit(ExitCode.FAILURE)
            if f"127.0.0.1:{port}".encode() in line:
                break
            lines.append(line)
        lines.clear()
        yield key_path
    finally:
<<<<<<< HEAD
        proxy_proc.send_signal(signal.SIGINT)
        proxy_proc.wait()
        Path(key_path).unlink()
=======
        try:
            _stop_proxy(proxy_proc)
        finally:
            proxy_stdout.close()
            if identity_path is not None:
                identity_path.unlink(missing_ok=True)
>>>>>>> 188dfe4f (fix(BA-8310): stop the session ssh proxy and remove its key on exit (#17304))
