from __future__ import annotations

from ai.backend.kube.controller.naming import LABEL_SESSION_GROUP, kernel_labels
from ai.backend.kube.crd.session import SessionGroupSpec, SessionWorkload

GROUP_ID = "33333333-0000-0000-0000-000000000001"


class TestKernelLabels:
    def test_a_session_in_a_group_labels_its_kernels_with_the_group(
        self, workload: SessionWorkload
    ) -> None:
        workload.spec.session_group = SessionGroupSpec(id=GROUP_ID)
        labels = kernel_labels(workload, workload.spec.kernels[0])
        assert labels[LABEL_SESSION_GROUP] == GROUP_ID

    def test_a_session_without_a_group_has_no_group_label(self, workload: SessionWorkload) -> None:
        assert LABEL_SESSION_GROUP not in kernel_labels(workload, workload.spec.kernels[0])
