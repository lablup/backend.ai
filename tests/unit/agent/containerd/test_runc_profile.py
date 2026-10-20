from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ai.backend.agent.containerd.profile.base import (
    GeneratedMountKind,
    KernelLaunch,
    KernelRunnerReadiness,
    RuntimeProfile,
    StdioMode,
)
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import KernelCreationConfig, SlotName


class TestRuncProfile:
    def test_name(self) -> None:
        assert RuncProfile(1.0).name == "runc"

    def test_accepts_any_slots(self) -> None:
        slots = {SlotName("cpu"): Decimal(1), SlotName("confidential.tdx"): Decimal(1)}

        assert RuncProfile(1.0).accepts(slots) is True

    def test_plan(
        self,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        launch = KernelLaunch(
            kernel_id=ownership_data.kernel_id,
            session_id=ownership_data.session_id,
            config=kernel_config,
            slots={},
            devices=(),
            mounts=(),
            trusted_storage_path=Path("/tmp"),
            base_spec={},
        )

        plan = RuncProfile(7.5).plan(launch)

        assert plan.runtime_handler == "io.containerd.runc.v2"
        assert plan.rootfs_image == kernel_config["image"]["canonical"]
        assert plan.spec_patch == {}
        assert plan.allowed_mount_kinds == frozenset(GeneratedMountKind)
        assert plan.stdio is StdioMode.LOG_FILE
        assert plan.readiness == KernelRunnerReadiness(timeout_s=7.5)

    def test_conforms_to_runtime_profile(self) -> None:
        assert isinstance(RuncProfile(1.0), RuntimeProfile)
