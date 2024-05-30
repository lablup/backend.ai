import contextlib
import os
import secrets
import signal
import subprocess
import sys
from pathlib import Path
from typing import Iterator, List

from ai.backend.cli.types import ExitCode

from ..pretty import print_fail, print_info

CLI_EXECUTABLE: tuple[str, ...]
if pex_path := os.environ.get("PEX", None):
    CLI_EXECUTABLE = (sys.executable, pex_path)
else:
    CLI_EXECUTABLE = (sys.executable, "-m", "ai.backend.cli")


@contextlib.contextmanager
def container_ssh_ctx(session_ref: str, port: int) -> Iterator[Path]:
    random_id = secrets.token_hex(16)
    key_filename = "id_container"
    key_path = Path(f"~/.ssh/id_{random_id}").expanduser()
    try:
        subprocess.run(
            [*CLI_EXECUTABLE, "session", "download", session_ref, key_filename],
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print_fail(f"Failed to download the SSH key from the session (exit: {e.returncode}):")
        print(e.stdout.decode())
        sys.exit(ExitCode.FAILURE)
    os.rename(key_filename, key_path)
    print_info(f"running a temporary sshd proxy at localhost:{port} ...", file=sys.stderr)
    # proxy_proc is a background process
    proxy_proc = subprocess.Popen(
        [*CLI_EXECUTABLE, "app", session_ref, "sshd", "-b", f"127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proxy_proc.stdout is not None
    try:
        lines: List[bytes] = []
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
        yield key_path
    finally:
        proxy_proc.send_signal(signal.SIGINT)
        proxy_proc.wait()
        os.unlink(key_path)
