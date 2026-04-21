"""Unit tests for KernelRunnerMountProvisioner mount list (BA-4096 regression)."""

from __future__ import annotations

import pytest

from ai.backend.agent.stage.kernel_lifecycle.docker.mount.krunner import (
    KernelRunnerMountProvisioner,
)
from ai.backend.common.types import MountPermission


class TestKernelRunnerMountProvisionerDefaultMounts:
    @pytest.fixture
    def provisioner(self) -> KernelRunnerMountProvisioner:
        return KernelRunnerMountProvisioner()

    def test_default_mounts_do_not_include_warning_doc(
        self,
        provisioner: KernelRunnerMountProvisioner,
    ) -> None:
        """Regression: DO_NOT_STORE_PERSISTENT_FILES_HERE.md must NOT appear
        as a bind mount — it is now copied via ScratchProvisioner."""
        mounts = provisioner._prepare_default_mounts()
        mount_targets = [str(m.target) for m in mounts]
        assert "/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md" not in mount_targets

    def test_default_mounts_include_expected_entries(
        self,
        provisioner: KernelRunnerMountProvisioner,
    ) -> None:
        mounts = provisioner._prepare_default_mounts()
        mount_targets = [str(m.target) for m in mounts]
        assert "/opt/kernel/entrypoint.sh" in mount_targets
        assert "/opt/kernel/extract_dotfiles.py" in mount_targets
        assert "/opt/kernel/fantompass.py" in mount_targets
        assert "/opt/kernel/hash_phrase.py" in mount_targets
        assert "/opt/kernel/words.json" in mount_targets

    def test_default_mounts_are_read_only(
        self,
        provisioner: KernelRunnerMountProvisioner,
    ) -> None:
        mounts = provisioner._prepare_default_mounts()
        for mount in mounts:
            assert mount.permission == MountPermission.READ_ONLY
