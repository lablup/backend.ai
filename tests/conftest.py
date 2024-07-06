from pathlib import Path

import pytest

from ai.backend.testutils.bootstrap import sync_file_lock
from ai.backend.testutils.pants import get_parallel_slot


@pytest.fixture(scope="session", autouse=True)
def init_tcp_port_range():
    parallel_slot = get_parallel_slot()
    lock_path = Path(f"~/.cache/bai/testing/port-{parallel_slot}.lock").expanduser()
    port_path = Path(f"~/.cache/bai/testing/port-{parallel_slot}.txt").expanduser()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    print("init_tcp_port_range: enter")
    with sync_file_lock(lock_path):
        if port_path.exists():
            port_path.unlink()
    try:
        yield
    finally:
        with sync_file_lock(lock_path):
            if port_path.exists():
                port_path.unlink()
        print("init_tcp_port_range: exit")
