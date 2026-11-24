from __future__ import annotations

import asyncio
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock, create_autospec, patch
from uuid import uuid4

import pytest

from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId


@dataclass(frozen=True)
class _ExecResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class _ListFilesCase:
    description: str
    exec_results: Sequence[_ExecResult]
    expected_environ_options: Sequence[str | None]
    expected_files: str
    expected_errors: str


class TestListFiles:
    @pytest.fixture
    def kernel(self) -> DockerKernel:
        return DockerKernel(
            ownership_data=KernelOwnershipData(
                kernel_id=KernelId(uuid4()),
                session_id=SessionId(uuid4()),
                agent_id=AgentId("test-agent-id"),
            ),
            network_id="test-network",
            image=ImageRef(
                name="test-image",
                project="test-project",
                registry="registry.local",
                tag="latest",
                architecture="x86_64",
                is_local=False,
            ),
            version=1,
            network_driver="bridge",
            agent_config={},
            resource_spec=Mock(),
            service_ports=[],
            environ={},
            data={"container_id": "test-container"},
        )

    @pytest.fixture
    def docker_exec_spawn(self, case: _ListFilesCase) -> Iterator[AsyncMock]:
        processes = []
        for result in case.exec_results:
            process = create_autospec(asyncio.subprocess.Process, instance=True)
            process.returncode = result.returncode
            process.communicate = AsyncMock(return_value=(result.stdout, result.stderr))
            processes.append(process)
        with patch(
            "ai.backend.agent.docker.kernel.asyncio.create_subprocess_exec",
            AsyncMock(side_effect=processes),
        ) as spawn:
            yield spawn

    @pytest.mark.parametrize(
        "case",
        [
            _ListFilesCase(
                description="python-loads",
                exec_results=[_ExecResult(0, b"[]", b"")],
                expected_environ_options=[None],
                expected_files="[]",
                expected_errors="",
            ),
            _ListFilesCase(
                description="python-loads-only-with-stubs",
                exec_results=[
                    _ExecResult(127, b"", b"error while loading shared libraries"),
                    _ExecResult(0, b"[]", b""),
                ],
                expected_environ_options=[None, "--env=LD_LIBRARY_PATH=/opt/kernel/glibc-stub"],
                expected_files="[]",
                expected_errors="",
            ),
            _ListFilesCase(
                description="listing-fails",
                exec_results=[_ExecResult(1, b"", b"FileNotFoundError")],
                expected_environ_options=[None],
                expected_files="",
                expected_errors="FileNotFoundError",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_list_files(
        self,
        kernel: DockerKernel,
        docker_exec_spawn: AsyncMock,
        case: _ListFilesCase,
    ) -> None:
        listing = await kernel.list_files("/home/work")

        assert [
            next((arg for arg in call.args if arg.startswith("--env=")), None)
            for call in docker_exec_spawn.await_args_list
        ] == list(case.expected_environ_options)
        assert listing["files"] == case.expected_files
        assert listing["errors"] == case.expected_errors
