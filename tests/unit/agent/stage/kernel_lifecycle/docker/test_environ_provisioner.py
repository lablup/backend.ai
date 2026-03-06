"""Unit tests for EnvironProvisioner."""

from __future__ import annotations

from decimal import Decimal
from pathlib import PurePosixPath
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.stage.kernel_lifecycle.docker.environ import (
    BACKENDAI_PERSISTENT_PATHS,
    AgentInfo,
    EnvironProvisioner,
    EnvironSpec,
    KernelInfo,
)
from ai.backend.common.types import (
    DeviceName,
    KernelCreationConfig,
    MountPermission,
    SlotName,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)


class TestEnvironProvisioner:
    @pytest.fixture
    def provisioner(self) -> EnvironProvisioner:
        return EnvironProvisioner()

    @pytest.fixture
    def agent_info(self) -> AgentInfo:
        mock_computer = MagicMock()
        mock_computer.instance.get_additional_gids.return_value = set()
        mock_computer.instance.get_hooks = AsyncMock(return_value=[])
        mock_computer.instance.get_attached_devices = AsyncMock(return_value=[])

        return AgentInfo(
            computers={
                DeviceName("cpu"): mock_computer,
                DeviceName("mem"): mock_computer,
            },
            distro="ubuntu20.04",
            architecture="x86_64",
            kernel_uid=1000,
            kernel_gid=1000,
        )

    @pytest.fixture
    def resource_spec(self) -> MagicMock:
        spec = MagicMock()
        spec.allocations = {
            DeviceName("cpu"): {SlotName("cpu"): {0: Decimal(1)}},
            DeviceName("mem"): {SlotName("mem"): {0: Decimal(1024)}},
        }
        spec.device_list = []
        return spec

    @pytest.fixture
    def kernel_info(self, request: pytest.FixtureRequest, resource_spec: MagicMock) -> KernelInfo:
        mounts: tuple[tuple[str, str], ...] = request.param
        mount_jsons: list[dict[str, Any]] = [
            VFolderMount(
                name=name,
                vfid=VFolderID(quota_scope_id=None, folder_id=uuid4()),
                vfsubpath=PurePosixPath("."),
                host_path=PurePosixPath(f"/data/vfolders/{name}"),
                kernel_path=PurePosixPath(kernel_path),
                mount_perm=MountPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.GENERAL,
            ).to_json()
            for name, kernel_path in mounts
        ]

        return KernelInfo(
            kernel_creation_config=cast(
                KernelCreationConfig,
                {
                    "environ": {},
                    "mounts": mount_jsons,
                    "image": {"labels": {}},
                },
            ),
            kernel_features=frozenset(),
            resource_spec=resource_spec,
            overriding_uid=None,
            overriding_gid=None,
            supplementary_gids=set(),
        )

    @pytest.fixture
    def environ_spec(self, agent_info: AgentInfo, kernel_info: KernelInfo) -> EnvironSpec:
        return EnvironSpec(agent_info=agent_info, kernel_info=kernel_info)

    @pytest.mark.parametrize("kernel_info", [()], indirect=True)
    async def test_persistent_paths_not_set_without_mounts(
        self,
        provisioner: EnvironProvisioner,
        environ_spec: EnvironSpec,
    ) -> None:
        result = await provisioner.setup(environ_spec)
        assert BACKENDAI_PERSISTENT_PATHS not in result.environ

    @pytest.mark.parametrize(
        ("kernel_info", "expected_paths"),
        [
            pytest.param(
                (("my-data", "/home/work/data"),),
                {"/home/work/data"},
                id="single_mount",
            ),
            pytest.param(
                (
                    ("my-data", "/home/work/data"),
                    ("my-model", "/home/work/model"),
                ),
                {"/home/work/data", "/home/work/model"},
                id="multiple_mounts",
            ),
        ],
        indirect=["kernel_info"],
    )
    async def test_persistent_paths(
        self,
        provisioner: EnvironProvisioner,
        environ_spec: EnvironSpec,
        expected_paths: set[str],
    ) -> None:
        result = await provisioner.setup(environ_spec)
        paths = set(result.environ[BACKENDAI_PERSISTENT_PATHS].split(":"))
        assert paths == expected_paths
