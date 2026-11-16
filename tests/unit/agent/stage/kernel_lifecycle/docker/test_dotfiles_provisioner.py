from __future__ import annotations

from pathlib import Path

from ai.backend.agent.stage.kernel_lifecycle.docker.dotfiles import (
    AgentConfig,
    DotfileInput,
    DotfilesProvisioner,
    DotfilesSpec,
)


def _spec(scratch_dir: Path, dotfiles: list[DotfileInput]) -> DotfilesSpec:
    return DotfilesSpec(
        dotfiles=dotfiles,
        scratch_dir=scratch_dir,
        work_dir=scratch_dir / "work",
        uid_override=None,
        gid_override=None,
        agent_config=AgentConfig(kernel_features=frozenset(), kernel_uid=1000, kernel_gid=1000),
    )


class TestDotfilesProvisioner:
    async def test_writes_only_paths_under_work_dir(self, tmp_path: Path) -> None:
        scratch_dir = tmp_path / "scratch"
        (scratch_dir / "work").mkdir(parents=True)
        (scratch_dir / "config").mkdir()
        kconfig = scratch_dir / "config" / "kconfig.dat"
        kconfig.write_text("original")

        result = await DotfilesProvisioner().setup(
            _spec(
                scratch_dir,
                [
                    DotfileInput(path="/home/config/kconfig.dat", data="x", perm="644"),
                    DotfileInput(path="../config/kconfig.dat", data="x", perm="644"),
                    DotfileInput(path=".aws/config", data="kept", perm="755"),
                ],
            )
        )

        assert kconfig.read_text() == "original"
        assert (scratch_dir / "work" / ".aws" / "config").read_text() == "kept\n"
        assert [Path(d.path).name for d in result.processed_dotfiles] == ["config"]
        assert [Path(p.path).name for p in result.processed_dotfiles[0].dir_own_permissions] == [
            "config",
            ".aws",
        ]
