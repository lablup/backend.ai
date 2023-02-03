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

    os.rename(key_filename, key_path)
    print_info(f"running a temporary sshd proxy at localhost:{port} ...", file=sys.stderr)

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

    try:
        yield key_path
    finally:
        asyncio.run(proxy_ctx.__aexit__(None, False))
        os.unlink(key_path)
