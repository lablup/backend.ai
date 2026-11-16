from __future__ import annotations

import pickle
import stat
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from ai.backend.agent.agent import AbstractKernelCreationContext
from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.kubernetes.agent import KubernetesAgent
from ai.backend.agent.scratch.utils import RestartStateStore
from ai.backend.common.types import KernelId


@pytest.fixture
def kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


@pytest.fixture
def scratch_dir(tmp_path: Path, kernel_id: KernelId) -> Path:
    scratch_dir = tmp_path / str(kernel_id)
    (scratch_dir / "config").mkdir(parents=True)
    return scratch_dir


@pytest.fixture
def store(tmp_path: Path, kernel_id: KernelId, scratch_dir: Path) -> RestartStateStore:
    return RestartStateStore(tmp_path, kernel_id)


class TestRestartStateStore:
    async def test_store_writes_outside_config_dir(
        self, store: RestartStateStore, scratch_dir: Path
    ) -> None:
        await store.store("kconfig.dat", b"new")

        assert (scratch_dir / "restart-state" / "kconfig.dat").read_bytes() == b"new"
        assert not (scratch_dir / "config" / "kconfig.dat").exists()
        assert await store.load("kconfig.dat") == b"new"

    async def test_store_restricts_permissions(
        self, store: RestartStateStore, scratch_dir: Path
    ) -> None:
        await store.store("kconfig.dat", b"new")

        state_dir = scratch_dir / "restart-state"
        assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE((state_dir / "kconfig.dat").stat().st_mode) == 0o600
        assert [path.name for path in state_dir.iterdir()] == ["kconfig.dat"]

    async def test_load_falls_back_to_config_dir(
        self, store: RestartStateStore, scratch_dir: Path
    ) -> None:
        (scratch_dir / "config" / "cluster.json").write_bytes(b"old")

        assert await store.load("cluster.json") == b"old"

    async def test_store_removes_file_in_config_dir(
        self, store: RestartStateStore, scratch_dir: Path
    ) -> None:
        (scratch_dir / "config" / "cluster.json").write_bytes(b"old")
        (scratch_dir / "config" / "environ.txt").write_bytes(b"A=1")

        await store.store("cluster.json", b"new")

        assert not (scratch_dir / "config" / "cluster.json").exists()
        assert (scratch_dir / "config" / "environ.txt").exists()
        assert await store.load("cluster.json") == b"new"

    async def test_load_prefers_state_dir(
        self, store: RestartStateStore, scratch_dir: Path
    ) -> None:
        await store.store("kconfig.dat", b"new")
        (scratch_dir / "config" / "kconfig.dat").write_bytes(b"old")

        assert await store.load("kconfig.dat") == b"new"

    async def test_load_missing_file_raises(self, store: RestartStateStore) -> None:
        with pytest.raises(FileNotFoundError):
            await store.load("kconfig.dat")

    async def test_failed_store_keeps_file_in_config_dir(
        self, store: RestartStateStore, scratch_dir: Path
    ) -> None:
        (scratch_dir / "config" / "kconfig.dat").write_bytes(b"old")

        with (
            patch("ai.backend.agent.scratch.utils.os.fdopen", side_effect=OSError),
            pytest.raises(OSError),
        ):
            await store.store("kconfig.dat", b"new")

        assert await store.load("kconfig.dat") == b"old"


@pytest.mark.parametrize("agent_class", [DockerAgent, KubernetesAgent])
async def test_agent_stores_and_loads_restart_state(
    agent_class: Any, tmp_path: Path, kernel_id: KernelId, scratch_dir: Path
) -> None:
    agent = SimpleNamespace(
        local_config=SimpleNamespace(container=SimpleNamespace(scratch_root=tmp_path))
    )

    await agent_class.restart_kernel__store_config(agent, kernel_id, "kconfig.dat", b"new")

    assert (scratch_dir / "restart-state" / "kconfig.dat").read_bytes() == b"new"
    assert not (scratch_dir / "config" / "kconfig.dat").exists()
    assert await agent_class.restart_kernel__load_config(agent, kernel_id, "kconfig.dat") == b"new"


class TestKernelConfigForRestart:
    @pytest.fixture
    def kernel_config(self) -> dict[str, Any]:
        return {
            "environ": {"BACKENDAI_ACCESS_KEY": "access-key"},
            "internal_data": {"ssh_keypair": {"private_key": "private-key"}},
            "image": {
                "canonical": "registry.example.com/python:latest",
                "registry": {
                    "name": "registry.example.com",
                    "url": "https://registry.example.com",
                    "username": "account",
                    "password": "secret",
                },
            },
        }

    def _stored_config(self, kernel_config: dict[str, Any]) -> dict[str, Any]:
        ctx = cast(Any, SimpleNamespace(kernel_config=kernel_config))
        stored = AbstractKernelCreationContext.kernel_config_for_restart(ctx)
        return cast(dict[str, Any], pickle.loads(pickle.dumps(stored)))

    def test_registry_account_is_removed(self, kernel_config: dict[str, Any]) -> None:
        stored = self._stored_config(kernel_config)

        assert stored["image"]["registry"] == {
            "name": "registry.example.com",
            "url": "https://registry.example.com",
            "username": None,
            "password": None,
        }

    def test_other_values_are_kept(self, kernel_config: dict[str, Any]) -> None:
        stored = self._stored_config(kernel_config)

        assert stored["environ"] == kernel_config["environ"]
        assert stored["internal_data"] == kernel_config["internal_data"]
        assert stored["image"]["canonical"] == kernel_config["image"]["canonical"]

    def test_running_config_is_not_changed(self, kernel_config: dict[str, Any]) -> None:
        self._stored_config(kernel_config)

        assert kernel_config["image"]["registry"]["username"] == "account"
        assert kernel_config["image"]["registry"]["password"] == "secret"
