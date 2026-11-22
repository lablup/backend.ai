from __future__ import annotations

import pytest

from ai.backend.kube.controller.manifests import ControllerSettings
from ai.backend.kube.crd.session import (
    KernelImage,
    KernelSpec,
    SessionWorkload,
    SessionWorkloadSpec,
)


@pytest.fixture
def settings() -> ControllerSettings:
    return ControllerSettings(krunner_image="registry.local/krunner@sha256:abc")


@pytest.fixture
def main_kernel() -> KernelSpec:
    return KernelSpec(
        kernel_id="11111111-0000-0000-0000-000000000001",
        image=KernelImage(
            canonical="registry.local/python:3.13",
            labels={
                "ai.backend.base-distro": "ubuntu24.04",
                "ai.backend.runtime-type": "python",
                "ai.backend.runtime-path": "/usr/bin/python3",
            },
        ),
        resource_slots={"cpu": "1.5", "mem": "1073741824"},
        environ={"BACKENDAI_KERNEL_ID": "11111111-0000-0000-0000-000000000001"},
    )


@pytest.fixture
def workload(main_kernel: KernelSpec) -> SessionWorkload:
    return SessionWorkload(
        metadata={"name": "s-1", "namespace": "bai-p", "uid": "uid-1"},
        spec=SessionWorkloadSpec(
            session_id="22222222-0000-0000-0000-000000000001",
            session_name="t",
            owner_user_id="u",
            resource_group="k8s",
            kernels=[main_kernel],
        ),
    )
