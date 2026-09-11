from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ai.backend.agent.stage.kernel_lifecycle.docker.bootstrap import (
    AgentConfig as BootstrapAgentConfig,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.bootstrap import (
    BootstrapProvisioner,
    BootstrapSpec,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.dotfiles import (
    AgentConfig as DotfileAgentConfig,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.dotfiles import (
    DotfileInput,
    DotfilesProvisioner,
    DotfilesSpec,
)


@pytest.fixture
def dotfile_spec(tmp_path: Path) -> DotfilesSpec:
    return DotfilesSpec(
        dotfiles=[],
        scratch_dir=tmp_path,
        work_dir=tmp_path,
        uid_override=None,
        gid_override=None,
        agent_config=DotfileAgentConfig(kernel_features=frozenset(), kernel_uid=0, kernel_gid=0),
    )


@pytest.fixture
def bootstrap_spec(tmp_path: Path) -> BootstrapSpec:
    return BootstrapSpec(
        work_dir=tmp_path,
        bootstrap_script=None,
        uid_override=None,
        gid_override=None,
        agent_config=BootstrapAgentConfig(kernel_features=frozenset(), kernel_uid=0, kernel_gid=0),
    )


class TestDotfilesProvisioner:
    async def test_exported_ca_paths_have_no_carriage_return(
        self, dotfile_spec: DotfilesSpec
    ) -> None:
        dotfile_spec.dotfiles = [
            DotfileInput(
                path=".bashrc",
                data=(
                    'export REQUESTS_CA_BUNDLE="/tmp/ca.crt"\r\n'
                    'export NODE_EXTRA_CA_CERTS="/tmp/ca.crt"\r\n'
                    'export SSL_CERT_FILE="/tmp/ca.crt"\r\n'
                    'export LAST="ok"'
                ),
                perm="644",
            ),
        ]
        await DotfilesProvisioner().setup(dotfile_spec)

        process = await asyncio.create_subprocess_exec(
            "/bin/bash",
            "--noprofile",
            "--norc",
            "-c",
            'source "$1"; printf "%s\\n" "$REQUESTS_CA_BUNDLE" "$NODE_EXTRA_CA_CERTS" '
            '"$SSL_CERT_FILE" "$LAST"',
            "bash",
            str(dotfile_spec.work_dir / ".bashrc"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        assert process.returncode == 0, stderr
        assert stderr == b""
        assert stdout == b"/tmp/ca.crt\n/tmp/ca.crt\n/tmp/ca.crt\nok\n"


class TestBootstrapProvisioner:
    async def test_crlf_script_runs_with_sh(self, bootstrap_spec: BootstrapSpec) -> None:
        bootstrap_spec.bootstrap_script = 'set -e\r\nif true; then\r\n  printf "ok"\r\nfi\r\n'
        result = await BootstrapProvisioner().setup(bootstrap_spec)
        assert result.bootstrap_path is not None

        process = await asyncio.create_subprocess_exec(
            "/bin/sh",
            str(result.bootstrap_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        assert process.returncode == 0, stderr
        assert stderr == b""
        assert stdout == b"ok"
