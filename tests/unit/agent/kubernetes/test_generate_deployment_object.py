from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.kubernetes.agent import KubernetesKernelCreationContext
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelCreationConfig, KernelId, SessionId


@pytest.fixture
def kernel_creation_context(tmp_path: Path) -> KubernetesKernelCreationContext:
    return KubernetesKernelCreationContext(
        ownership_data=KernelOwnershipData(
            kernel_id=KernelId(uuid4()),
            session_id=SessionId(uuid4()),
            agent_id=AgentId("i-agent"),
        ),
        event_producer=MagicMock(),
        kernel_image=MagicMock(),
        kernel_config=cast(
            KernelCreationConfig,
            {
                "image": {"labels": {}},
                "uid": 1000,
                "main_gid": 1000,
                "supplementary_gids": [],
                "internal_data": None,
            },
        ),
        distro="ubuntu22.04",
        local_config=MagicMock(container=MagicMock(scratch_root=tmp_path)),
        agent_sockpath=tmp_path / "agent.sock",
        computers={},
        workers={},
        static_pvc_name="scratch-pvc",
    )


class TestGenerateDeploymentObject:
    async def test_no_privileged_setting_anywhere_in_deployment_object(
        self,
        kernel_creation_context: KubernetesKernelCreationContext,
    ) -> None:
        deployment = await kernel_creation_context.generate_deployment_object(
            image="python:3.12",
            environ={},
            ports=[],
            command=[],
        )

        assert "privileged" not in json.dumps(deployment)

    async def test_session_container_adds_exactly_ipc_lock_and_sys_nice_capabilities(
        self,
        kernel_creation_context: KubernetesKernelCreationContext,
    ) -> None:
        deployment = await kernel_creation_context.generate_deployment_object(
            image="python:3.12",
            environ={},
            ports=[],
            command=[],
        )

        [session_container] = deployment["spec"]["template"]["spec"]["containers"]
        assert session_container["securityContext"] == {
            "capabilities": {"add": ["IPC_LOCK", "SYS_NICE"]},
        }
