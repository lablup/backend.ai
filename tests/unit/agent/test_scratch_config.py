from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from ai.backend.agent.scratch.types import KernelRecoveryScratchData
from ai.backend.agent.scratch.utils import ScratchConfig
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId, SessionTypes


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config(config_path: Path) -> ScratchConfig:
    return ScratchConfig(config_path)


@pytest.fixture
def sample_scratch_data() -> KernelRecoveryScratchData:
    kernel_id = KernelId(uuid.uuid4())
    session_id = SessionId(uuid.uuid4())
    agent_id = AgentId("test-agent")
    return KernelRecoveryScratchData(
        id=kernel_id,
        agent_id=agent_id,
        image_ref=ImageRef(
            name="python",
            project="stable",
            tag="3.10-ubuntu22.04",
            registry="cr.backend.ai",
            architecture="x86_64",
            is_local=False,
        ),
        version=1,
        ownership_data=KernelOwnershipData(
            kernel_id=kernel_id,
            session_id=session_id,
            agent_id=agent_id,
        ),
        network_id=str(uuid.uuid4()),
        network_driver="bridge",
        session_type=SessionTypes.INTERACTIVE,
        block_service_ports=False,
        domain_socket_proxies=[],
        service_ports=[],
        repl_in_port=2000,
        repl_out_port=2001,
    )


class TestRecoveryFileExists:
    def test_returns_false_when_no_file(self, config: ScratchConfig) -> None:
        assert config.recovery_file_exists() is False

    def test_returns_true_when_file_exists(self, config: ScratchConfig, config_path: Path) -> None:
        (config_path / "recovery.json").write_text("{}")
        assert config.recovery_file_exists() is True


class TestGetJsonRecoveryData:
    async def test_returns_none_when_file_missing(self, config: ScratchConfig) -> None:
        result = await config.get_json_recovery_data()
        assert result is None

    async def test_returns_parsed_data(
        self,
        config: ScratchConfig,
        config_path: Path,
        sample_scratch_data: KernelRecoveryScratchData,
    ) -> None:
        (config_path / "recovery.json").write_text(sample_scratch_data.model_dump_json())
        result = await config.get_json_recovery_data()
        assert result is not None
        assert result.id == sample_scratch_data.id
        assert result.agent_id == sample_scratch_data.agent_id

    async def test_raises_on_invalid_json(self, config: ScratchConfig, config_path: Path) -> None:
        (config_path / "recovery.json").write_text("not valid json")
        with pytest.raises(Exception):
            await config.get_json_recovery_data()


class TestGetKernelEnviron:
    async def test_parses_environ_file(self, config: ScratchConfig, config_path: Path) -> None:
        (config_path / "environ.txt").write_text("FOO=bar\nBAZ=qux\n")
        result = await config.get_kernel_environ()
        assert result == {"FOO": "bar", "BAZ": "qux"}

    async def test_handles_value_with_equals(
        self, config: ScratchConfig, config_path: Path
    ) -> None:
        (config_path / "environ.txt").write_text("KEY=val=ue\n")
        result = await config.get_kernel_environ()
        assert result["KEY"] == "val=ue"

    async def test_raises_on_missing_file(self, config: ScratchConfig) -> None:
        with pytest.raises(FileNotFoundError):
            await config.get_kernel_environ()


class TestGetKernelResourceSpec:
    async def test_raises_on_missing_file(self, config: ScratchConfig) -> None:
        with pytest.raises(FileNotFoundError):
            await config.get_kernel_resource_spec()

    async def test_parses_resource_file(self, config: ScratchConfig, config_path: Path) -> None:
        resource_content = 'SCRATCH_SIZE=0\nSLOTS={"cpu": "1", "mem": "1073741824"}\nMOUNTS=\n'
        (config_path / "resource.txt").write_text(resource_content)
        result = await config.get_kernel_resource_spec()
        assert result is not None
        assert result.scratch_disk_size == 0


class TestSaveJsonRecoveryData:
    async def test_creates_file(
        self,
        config: ScratchConfig,
        config_path: Path,
        sample_scratch_data: KernelRecoveryScratchData,
    ) -> None:
        await config.save_json_recovery_data(sample_scratch_data)
        filepath = config_path / "recovery.json"
        assert filepath.is_file()
        data = json.loads(filepath.read_text())
        assert data["agent_id"] == str(sample_scratch_data.agent_id)

    async def test_roundtrip(
        self,
        config: ScratchConfig,
        sample_scratch_data: KernelRecoveryScratchData,
    ) -> None:
        await config.save_json_recovery_data(sample_scratch_data)
        loaded = await config.get_json_recovery_data()
        assert loaded is not None
        assert loaded.id == sample_scratch_data.id
        assert loaded.network_driver == sample_scratch_data.network_driver
        assert loaded.repl_in_port == sample_scratch_data.repl_in_port
