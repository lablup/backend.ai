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


def _make_environ_spec(
    mounts: list[dict[str, Any]] | None = None,
) -> EnvironSpec:
    if mounts is None:
        mounts = []

    mock_computer = MagicMock()
    mock_computer.instance.get_additional_gids.return_value = set()
    mock_computer.instance.get_hooks = AsyncMock(return_value=[])
    mock_computer.instance.get_attached_devices = AsyncMock(return_value=[])

    resource_spec = MagicMock()
    resource_spec.allocations = {
        DeviceName("cpu"): {SlotName("cpu"): {0: Decimal(1)}},
        DeviceName("mem"): {SlotName("mem"): {0: Decimal(1024)}},
    }
    resource_spec.device_list = []

    return EnvironSpec(
        agent_info=AgentInfo(
            computers={
                DeviceName("cpu"): mock_computer,
                DeviceName("mem"): mock_computer,
            },
            distro="ubuntu20.04",
            architecture="x86_64",
            kernel_uid=1000,
            kernel_gid=1000,
        ),
        kernel_info=KernelInfo(
            kernel_creation_config=cast(
                KernelCreationConfig,
                {
                    "environ": {},
                    "mounts": mounts,
                    "image": {"labels": {}},
                },
            ),
            kernel_features=frozenset(),
            resource_spec=resource_spec,
            overriding_uid=None,
            overriding_gid=None,
            supplementary_gids=set(),
        ),
    )


def _make_vfolder_mount_json(
    name: str,
    kernel_path: str,
) -> dict[str, Any]:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid4()),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath(f"/data/vfolders/{name}"),
        kernel_path=PurePosixPath(kernel_path),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    ).to_json()


class TestEnvironProvisioner:
    @pytest.fixture
    def provisioner(self) -> EnvironProvisioner:
        return EnvironProvisioner()

    async def test_persistent_paths_no_mounts(self, provisioner: EnvironProvisioner) -> None:
        spec = _make_environ_spec(mounts=[])
        result = await provisioner.setup(spec)
        assert BACKENDAI_PERSISTENT_PATHS not in result.environ

    async def test_persistent_paths_single_mount(self, provisioner: EnvironProvisioner) -> None:
        mounts = [
            _make_vfolder_mount_json("my-data", "/home/work/data"),
        ]
        spec = _make_environ_spec(mounts=mounts)
        result = await provisioner.setup(spec)
        assert result.environ[BACKENDAI_PERSISTENT_PATHS] == "/home/work/data"

    async def test_persistent_paths_multiple_mounts(self, provisioner: EnvironProvisioner) -> None:
        mounts = [
            _make_vfolder_mount_json("my-data", "/home/work/data"),
            _make_vfolder_mount_json("my-model", "/home/work/model"),
        ]
        spec = _make_environ_spec(mounts=mounts)
        result = await provisioner.setup(spec)
        paths = result.environ[BACKENDAI_PERSISTENT_PATHS].split(":")
        assert set(paths) == {"/home/work/data", "/home/work/model"}
