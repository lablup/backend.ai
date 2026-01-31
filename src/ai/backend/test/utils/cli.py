from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import pexpect

EOF = pexpect.EOF
TIMEOUT = pexpect.TIMEOUT


class ClientRunnerFunc(Protocol):
    def __call__(
        self,
        cmdargs: Sequence[str | Path],
        *args: Any,
        **kwargs: Any,
    ) -> pexpect.spawn:
        pass


def run(
    args: Sequence[str | Path],
    *,
    default_timeout: int = 5,
    **kwargs: Any,
) -> pexpect.spawn:
    return pexpect.spawn(
        str(args[0]),
        [str(arg) for arg in args[1:]],
        timeout=default_timeout,
        **kwargs,
    )


def decode(pexpect_capture: bytes | None) -> str:
    if pexpect_capture is None:
        return ""
    return pexpect_capture.decode()
