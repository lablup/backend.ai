import contextlib
import os
import secrets
import signal
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.pretty import print_fail, print_info

CLI_EXECUTABLE: tuple[str, ...]
if pex_path := os.environ.get("PEX", None):
    CLI_EXECUTABLE = (sys.executable, pex_path)
else:
    CLI_EXECUTABLE = (sys.executable, "-m", "ai.backend.cli")


@contextlib.contextmanager
def container_ssh_ctx(session_ref: str, port: int) -> Iterator[Path | None]:
    """Yield the session's private key, or None when the session holds none (the user uploaded
    only a public key), so ssh falls back to the user's own keys."""
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
    identity_path: Path | None = key_path
    if not key_path.read_bytes().strip():
        key_path.unlink()
        identity_path = None
    print_info(f"running a temporary sshd proxy at localhost:{port} ...", file=sys.stderr)
    # proxy_proc is a background process
    proxy_proc = subprocess.Popen(
        [*CLI_EXECUTABLE, "app", session_ref, "sshd", "-b", f"127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proxy_proc.stdout is None:
        raise RuntimeError("Failed to capture stdout from proxy process")
    try:
        lines: list[bytes] = []
        while True:
            line = proxy_proc.stdout.readline(1024)
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
        yield identity_path
    finally:
        proxy_proc.send_signal(signal.SIGINT)
        proxy_proc.wait()
        if identity_path is not None:
            identity_path.unlink()
