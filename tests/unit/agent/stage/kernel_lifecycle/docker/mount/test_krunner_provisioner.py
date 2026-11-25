"""Unit tests for KernelRunnerMountProvisioner mount list (BA-4096 regression)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from ai.backend.agent.stage.kernel_lifecycle.docker.mount.krunner import (
    KernelRunnerInfo,
    KernelRunnerMountProvisioner,
    LibcStyle,
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


@dataclass(frozen=True)
class _GlibcStubMountCase:
    libc_style: LibcStyle
    expected_targets_by_source_name: dict[str, str] = field(default_factory=dict)


class TestKernelRunnerMountProvisionerGlibcStubMounts:
    @pytest.fixture
    def provisioner(self) -> KernelRunnerMountProvisioner:
        return KernelRunnerMountProvisioner()

    @pytest.mark.parametrize(
        "case",
        [
            _GlibcStubMountCase(
                libc_style=LibcStyle.GLIBC,
                expected_targets_by_source_name={
                    "glibc-stub.libdl.so.2.x86_64.so": "/opt/kernel/glibc-stub/libdl.so.2",
                    "glibc-stub.libpthread.so.0.x86_64.so": (
                        "/opt/kernel/glibc-stub/libpthread.so.0"
                    ),
                    "glibc-stub.librt.so.1.x86_64.so": "/opt/kernel/glibc-stub/librt.so.1",
                    "glibc-stub.libutil.so.1.x86_64.so": "/opt/kernel/glibc-stub/libutil.so.1",
                },
            ),
            _GlibcStubMountCase(libc_style=LibcStyle.MUSL),
        ],
        ids=lambda case: case.libc_style.value,
    )
    def test_stubs_are_mounted_only_for_glibc(
        self,
        provisioner: KernelRunnerMountProvisioner,
        case: _GlibcStubMountCase,
    ) -> None:
        mounts = provisioner._prepare_glibc_stub_mounts(
            KernelRunnerInfo(
                distro="static-gnu",
                architecture="x86_64",
                libc_style=case.libc_style,
                krunner_volume="krunner-volume",
                krunner_py_version="3.13",
            )
        )
        assert {
            mount.source.name: str(mount.target) for mount in mounts if mount.source is not None
        } == case.expected_targets_by_source_name
