from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.agent.network import local_subnet, native_attacher


@pytest.fixture(autouse=True)
def local_subnet_state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Keep the durable network state stores out of the real /var/lib state dirs.

    The backends and the attach runner resolve a process-wide owner when none is injected, so any
    test that builds one would otherwise journal against the host's real store. Both registries
    are process-global, so they are cleared around each test to stop owners leaking between them.
    """
    state_dir = tmp_path / "net-local-subnet"
    monkeypatch.setattr(local_subnet, "_DEFAULT_LOCAL_SUBNET_STATE_DIR", state_dir)
    monkeypatch.setattr(native_attacher, "_DEFAULT_IPAM_STATE_DIR", tmp_path / "net-ipam")
    local_subnet._allocators.clear()
    native_attacher._ipams.clear()
    yield state_dir
    local_subnet._allocators.clear()
    native_attacher._ipams.clear()
