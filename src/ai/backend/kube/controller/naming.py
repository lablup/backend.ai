from __future__ import annotations

from typing import Final

from ai.backend.kube.crd.session import KernelSpec, SessionWorkload

LABEL_MANAGED_BY: Final = "app.kubernetes.io/managed-by"
MANAGED_BY: Final = "backendai-session-controller"
LABEL_SESSION_ID: Final = "backend.ai/session-id"
LABEL_KERNEL_ID: Final = "backend.ai/kernel-id"
LABEL_CLUSTER_ROLE: Final = "backend.ai/cluster-role"
LABEL_PROJECT_ID: Final = "backend.ai/project-id"
LABEL_USER_ID: Final = "backend.ai/user-id"
LABEL_RESOURCE_GROUP: Final = "backend.ai/resource-group"
LABEL_NETWORK_ID: Final = "backend.ai/network-id"
LABEL_QUEUE: Final = "scheduling.backend.ai/queue"
ANNOTATION_POD_GROUP: Final = "scheduling.backend.ai/pod-group"
ANNOTATION_DEVICES: Final = "scheduling.backend.ai/devices"  # {"<DRA driver>/<slot>": <count>}
# {"<DRA driver>": <count>} of devices the Pod takes a share of; the node must have them.
ANNOTATION_SHARED_DEVICES: Final = "scheduling.backend.ai/shared-devices"
HOSTNAME_LABEL: Final = "kubernetes.io/hostname"
SOKOVAN_SCHEDULER: Final = "sokovan"
SOKOVAN_GATE: Final = "scheduling.backend.ai/sokovan"

FINALIZER: Final = "backend.ai/session-controller"

KERNEL_CONTAINER: Final = "kernel"
KRUNNER_CONTAINER: Final = "krunner"


def session_object_name(session_id: str) -> str:
    """Name of the SessionWorkload, PodGroup and headless Service of a session."""
    return f"s-{session_id}"


def kernel_pod_name(workload: SessionWorkload, kernel: KernelSpec) -> str:
    return f"{workload.metadata['name']}-{kernel.cluster_hostname}"


def kernel_secret_name(workload: SessionWorkload, kernel: KernelSpec) -> str:
    return f"{kernel_pod_name(workload, kernel)}-config"


def session_labels(workload: SessionWorkload) -> dict[str, str]:
    spec = workload.spec
    labels = {
        LABEL_MANAGED_BY: MANAGED_BY,
        LABEL_SESSION_ID: spec.session_id,
        LABEL_RESOURCE_GROUP: spec.resource_group,
        LABEL_USER_ID: spec.owner_user_id,
    }
    if spec.owner_project_id:
        labels[LABEL_PROJECT_ID] = spec.owner_project_id
    if spec.network_id:
        labels[LABEL_NETWORK_ID] = spec.network_id
    return labels


def session_queue(workload: SessionWorkload) -> str:
    return workload.spec.queue or workload.spec.resource_group


def kernel_labels(workload: SessionWorkload, kernel: KernelSpec) -> dict[str, str]:
    return {
        **session_labels(workload),
        LABEL_KERNEL_ID: kernel.kernel_id,
        LABEL_CLUSTER_ROLE: kernel.cluster_role,
        LABEL_QUEUE: session_queue(workload),
    }
