"""Append the setup seconds of the pooled container fixtures to `$EXP_FIXTURE_LOG`.

Loaded with `-p exp_fixture_timer`.
"""

from __future__ import annotations

import os
import pathlib
import time
from collections.abc import Iterator
from typing import Any

import pytest

_NAMES = frozenset({"etcd_container", "redis_container", "postgres_container"})


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef: Any) -> Iterator[None]:
    start = time.monotonic()
    yield
    log = os.environ.get("EXP_FIXTURE_LOG")
    if log and fixturedef.argname in _NAMES:
        with pathlib.Path(log).open("a") as f:
            f.write(f"{fixturedef.argname}\t{time.monotonic() - start:.2f}\n")
