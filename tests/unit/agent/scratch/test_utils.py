from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from ai.backend.agent.scratch.types import KernelRecoveryScratchData
from ai.backend.agent.scratch.utils import ScratchConfig
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId, SessionTypes


def _recovery_record(repl_in_port: int) -> KernelRecoveryScratchData:
    kernel_id = KernelId(uuid.uuid4())
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
            session_id=SessionId(uuid.uuid4()),
            agent_id=agent_id,
        ),
        network_id=str(uuid.uuid4()),
        network_driver="bridge",
        session_type=SessionTypes.INTERACTIVE,
        block_service_ports=False,
        domain_socket_proxies=[],
        service_ports=[],
        repl_in_port=repl_in_port,
        repl_out_port=2001,
    )


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """A kernel's config directory, as its creation leaves it."""
    path = tmp_path / "config"
    path.mkdir()
    return path


class TestStageJsonRecoveryData:
    async def test_commit_puts_the_record_in_place_and_leaves_nothing_else(
        self, config_dir: Path
    ) -> None:
        config = ScratchConfig(config_dir)
        staged = await config.stage_json_recovery_data(_recovery_record(repl_in_port=2000))
        assert not config.recovery_file_exists()
        staged.commit()
        loaded = await config.get_json_recovery_data()
        assert loaded is not None
        assert loaded.repl_in_port == 2000
        assert [p.name for p in config_dir.iterdir()] == ["recovery.json"]

    async def test_discard_leaves_the_previous_record_untouched(self, config_dir: Path) -> None:
        config = ScratchConfig(config_dir)
        (await config.stage_json_recovery_data(_recovery_record(repl_in_port=2000))).commit()
        staged = await config.stage_json_recovery_data(_recovery_record(repl_in_port=3000))
        staged.discard()
        loaded = await config.get_json_recovery_data()
        assert loaded is not None
        assert loaded.repl_in_port == 2000
        assert [p.name for p in config_dir.iterdir()] == ["recovery.json"]

    async def test_a_missing_config_directory_is_not_created(self, tmp_path: Path) -> None:
        """The directory is the kernel's own, removed with it; a save must not put it back."""
        gone = tmp_path / "config"
        config = ScratchConfig(gone)
        with pytest.raises(FileNotFoundError):
            await config.stage_json_recovery_data(_recovery_record(repl_in_port=2000))
        assert not gone.exists()
