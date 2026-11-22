from __future__ import annotations

import pytest

from ai.backend.kube.controller.adapters import pod_pending_reason
from ai.backend.kube.controller.manifests import (
    ControllerSettings,
    build_kernel_pod,
    scheduler_adapter,
)
from ai.backend.kube.crd.session import KernelSpec, SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError


@pytest.fixture
def two_kernels(workload: SessionWorkload, main_kernel: KernelSpec) -> SessionWorkload:
    sub = main_kernel.model_copy(
        update={
            "kernel_id": "11111111-0000-0000-0000-000000000002",
            "cluster_role": "sub",
            "cluster_hostname": "sub1",
        }
    )
    workload.spec.kernels = [main_kernel, sub]
    return workload


class TestSokovan:
    def test_kernel_pods_join_the_gang_by_the_session_label(
        self, two_kernels: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        pod = build_kernel_pod(two_kernels, main_kernel, settings)
        labels = pod["metadata"]["labels"]
        assert labels["backend.ai/session-id"] == two_kernels.spec.session_id
        assert labels["app.kubernetes.io/managed-by"] == "backendai-session-controller"
        assert not any(
            k.startswith("scheduling.backend.ai/pod") for k in pod["metadata"]["annotations"]
        )
        assert pod["spec"]["schedulingGates"] == [{"name": "scheduling.backend.ai/sokovan"}]

    def test_no_object_is_created_beside_the_pods(
        self, workload: SessionWorkload, settings: ControllerSettings
    ) -> None:
        assert scheduler_adapter(workload, settings).group_objects(workload) == []


class TestKueue:
    def test_pods_carry_the_queue_and_the_pod_group(
        self, two_kernels: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        two_kernels.spec.scheduler_name = "kueue"
        pod = build_kernel_pod(two_kernels, main_kernel, settings)
        labels, annotations = pod["metadata"]["labels"], pod["metadata"]["annotations"]
        assert labels["kueue.x-k8s.io/queue-name"] == "k8s"
        assert labels["kueue.x-k8s.io/pod-group-name"] == "s-1"
        assert annotations["kueue.x-k8s.io/pod-group-total-count"] == "2"
        assert pod["spec"]["schedulerName"] == "default-scheduler"
        assert "schedulingGates" not in pod["spec"]

    def test_the_namespace_gets_a_local_queue(
        self, workload: SessionWorkload, settings: ControllerSettings
    ) -> None:
        workload.spec.scheduler_name = "kueue"
        [queue] = scheduler_adapter(workload, settings).group_objects(workload)
        assert (queue["kind"], queue["metadata"]["name"]) == ("LocalQueue", "k8s")
        assert queue["spec"]["clusterQueue"] == "backendai"


class TestKube:
    def test_single_node_kernels_share_a_node(
        self, two_kernels: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        two_kernels.spec.scheduler_name = "kube"
        pod = build_kernel_pod(two_kernels, main_kernel, settings)
        [term] = pod["spec"]["affinity"]["podAffinity"][
            "requiredDuringSchedulingIgnoredDuringExecution"
        ]
        assert term["topologyKey"] == "kubernetes.io/hostname"

    def test_multi_node_sessions_are_rejected(
        self, two_kernels: SessionWorkload, settings: ControllerSettings
    ) -> None:
        two_kernels.spec.scheduler_name = "kube"
        two_kernels.spec.cluster_mode = "multi-node"
        with pytest.raises(InvalidSessionWorkloadError):
            scheduler_adapter(two_kernels, settings).validate(two_kernels)


class TestUnknownScheduler:
    def test_is_rejected(self, workload: SessionWorkload, settings: ControllerSettings) -> None:
        workload.spec.scheduler_name = "volcano"
        with pytest.raises(InvalidSessionWorkloadError):
            scheduler_adapter(workload, settings)


class TestPodPendingReason:
    def test_kueue_gate_means_admission(self) -> None:
        pod = {"spec": {"schedulingGates": [{"name": "kueue.x-k8s.io/admission"}]}}
        assert pod_pending_reason([pod])[0] == "QueueAdmission"

    def test_unschedulable_condition(self) -> None:
        pod = {
            "spec": {},
            "status": {
                "conditions": [
                    {
                        "type": "PodScheduled",
                        "status": "False",
                        "reason": "Unschedulable",
                        "message": "m",
                    }
                ]
            },
        }
        assert pod_pending_reason([pod]) == ("Unschedulable", "m")
