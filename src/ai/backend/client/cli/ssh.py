import asyncio
import contextlib
import os
import secrets
import sys
from pathlib import Path
from typing import Iterator

from ai.backend.cli.types import ExitCode

from ..session import Session
from .app import ProxyRunnerContext
from .pretty import print_info


@contextlib.contextmanager
def container_ssh_ctx(session_ref: str, port: int) -> Iterator[Path]:
    random_id = secrets.token_hex(16)
    key_filename = "id_container"
    key_path = Path(f"~/.ssh/id_{random_id}").expanduser()
    with Session() as session:
        try:
            kernel = session.ComputeSession(session_ref)
            kernel.download([key_filename], ".")
        except Exception as e:
            print(e)
            sys.exit(ExitCode.FAILURE)

    # try:
    #     subprocess.run(
    #         ["backend.ai", "session", "download", session_ref, key_filename],
    #         shell=False,
    #         check=True,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.STDOUT,
    #     )
    # except subprocess.CalledProcessError as e:
    #     print_fail(f"Failed to download the SSH key from the session (exit: {e.returncode}):")
    #     print(e.stdout.decode())
    #     sys.exit(ExitCode.FAILURE)
    os.rename(key_filename, key_path)
    print_info(f"running a temporary sshd proxy at localhost:{port} ...", file=sys.stderr)
    # proxy_proc is a background process
    try:
        proxy_ctx = ProxyRunnerContext(
            "127.0.0.1",
            port,
            session_ref,
            "sshd",
            protocol="tcp",
        )
        asyncio.run(proxy_ctx.__aenter__())
    except Exception as e:
        print(e)
        sys.exit(ExitCode.FAILURE)
    # proxy_proc = subprocess.Popen(
    #     [
    #         "backend.ai",
    #         "app",
    #         session_ref,
    #         "sshd",
    #         "-b",
    #         f"127.0.0.1:{port}",
    #     ],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.STDOUT,
    # )
    # assert proxy_proc.stdout is not None
    try:
        # lines: List[bytes] = []
        # while True:
        #     line = proxy_proc.stdout.readline(1024)
        #     if not line:
        #         proxy_proc.wait()
        #         print_fail(
        #             f"Unexpected early termination of the sshd app command "
        #             f"(exit: {proxy_proc.returncode}):"
        #         )
        #         print((b"\n".join(lines)).decode())
        #         sys.exit(ExitCode.FAILURE)
        #     if f"127.0.0.1:{port}".encode() in line:
        #         break
        #     lines.append(line)
        # lines.clear()
        yield key_path
    finally:
        # proxy_proc.send_signal(signal.SIGINT)
        # proxy_proc.wait()
        asyncio.run(proxy_ctx.__aexit__(None, False))
        os.unlink(key_path)
