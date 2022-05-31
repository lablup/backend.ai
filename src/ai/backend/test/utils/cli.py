from __future__ import annotations

from pathlib import Path
from typing import (
    Protocol,
    Sequence,
)

import pexpect


EOF = pexpect.EOF
TIMEOUT = pexpect.TIMEOUT


class ClientRunnerFunc(Protocol):

    def __call__(
        self,
        cmdargs: Sequence[str | Path],
        *args,
        **kwargs,
    ) -> pexpect.spawn:
        pass


def run(
    args: Sequence[str | Path],
    *,
    default_timeout: int = 5,
    **kwargs,
) -> pexpect.spawn:
    p = pexpect.spawn(
        str(args[0]),
        [str(arg) for arg in args[1:]],
        timeout=default_timeout,
        **kwargs,
    )
    return p
