"""Unit tests for ScratchProvisioner warning doc cloning (BA-4096 regression)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from ai.backend.agent.stage.kernel_lifecycle.docker.scratch import (
    ContainerOwnershipConfig,
    ScratchProvisioner,
    ScratchSpec,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.utils import ScratchUtil
from ai.backend.common.types import BinarySize, KernelId

_SCRATCH_OS = "ai.backend.agent.stage.kernel_lifecycle.docker.scratch.os"


class TestScratchProvisionerCloneFunc:
    @pytest.fixture
    def provisioner(self) -> ScratchProvisioner:
        return ScratchProvisioner()

    @pytest.fixture
    def scratch_spec(self, tmp_path: Path) -> ScratchSpec:
        kernel_id = KernelId(uuid4())
        scratch_root = tmp_path / "scratches"
        scratch_root.mkdir()
        work_dir = ScratchUtil.work_dir(scratch_root, kernel_id)
        work_dir.mkdir(parents=True)
        return ScratchSpec(
            kernel_id=kernel_id,
            container_config=ContainerOwnershipConfig(
                kernel_uid=1000,
                kernel_gid=1000,
                supplementary_gids=set(),
                fallback_kernel_uid=1000,
                fallback_kernel_gid=1000,
                kernel_features=frozenset(),
            ),
            scratch_type="hostdir",
            scratch_root=scratch_root,
            scratch_size=BinarySize(1024),
        )

    def test_clone_copies_warning_doc(
        self,
        provisioner: ScratchProvisioner,
        scratch_spec: ScratchSpec,
    ) -> None:
        """Regression: DO_NOT_STORE_PERSISTENT_FILES_HERE.md must be copied
        into work_dir instead of being bind-mounted separately."""
        provisioner._clone_func(scratch_spec)
        work_dir = ScratchUtil.work_dir(scratch_spec.scratch_root, scratch_spec.kernel_id)

        copied = work_dir / "DO_NOT_STORE_PERSISTENT_FILES_HERE.md"
        assert copied.exists()
        assert copied.stat().st_size > 0

    def test_chown_includes_warning_doc(
        self,
        provisioner: ScratchProvisioner,
        scratch_spec: ScratchSpec,
    ) -> None:
        """When running as root, the warning doc must be chowned like dotfiles."""
        with (
            patch(f"{_SCRATCH_OS}.geteuid", return_value=0),
            patch(f"{_SCRATCH_OS}.chown") as mock_chown,
        ):
            provisioner._clone_func(scratch_spec)

        chowned_paths = {Path(call.args[0]) for call in mock_chown.call_args_list}
        work_dir = ScratchUtil.work_dir(scratch_spec.scratch_root, scratch_spec.kernel_id)
        assert work_dir / "DO_NOT_STORE_PERSISTENT_FILES_HERE.md" in chowned_paths
