from __future__ import annotations

from typing import Any

import pytest

from ai.backend.kube.controller.manifests import (
    ControllerSettings,
    SessionSecrets,
    build_kernel_pod,
    build_kernel_secret,
    build_pod_group,
    build_session_network_policy,
    build_session_service,
)
from ai.backend.kube.crd.scheduling import SokovanBindMode
from ai.backend.kube.crd.session import KernelSpec, SessionWorkload, VFolderVolumeMount
from ai.backend.kube.errors import InvalidSessionWorkloadError


def _env(container: dict[str, Any]) -> dict[str, str]:
    return {e["name"]: e["value"] for e in container["env"]}


class TestBuildKernelPod:
    def test_runs_entrypoint_with_runtime_args(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        container = build_kernel_pod(workload, main_kernel, settings)["spec"]["containers"][0]
        assert container["command"] == ["/opt/kernel/entrypoint.sh"]
        assert container["args"][-2:] == ["python", "/usr/bin/python3"]
        assert container["args"][4:6] == ["--session-id", "22222222-0000-0000-0000-000000000001"]

    def test_guaranteed_resources_from_slots(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        resources = build_kernel_pod(workload, main_kernel, settings)["spec"]["containers"][0][
            "resources"
        ]
        assert resources["requests"] == {"cpu": "1.5", "memory": "1073741824"}
        assert resources["limits"] == resources["requests"]

    def test_injects_agent_side_environ(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        env = _env(build_kernel_pod(workload, main_kernel, settings)["spec"]["containers"][0])
        assert env["BACKENDAI_KERNEL_ID"] == "11111111-0000-0000-0000-000000000001"
        assert env["LOCAL_USER_ID"] == "1000"
        assert env["LD_PRELOAD"] == "/opt/kernel/libbaihook.so"
        assert env["GPU_COUNT"] == "0"

    def test_session_uid_overrides_default(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        main_kernel.uid = 2000
        env = _env(build_kernel_pod(workload, main_kernel, settings)["spec"]["containers"][0])
        assert env["LOCAL_USER_ID"] == "2000"

    def test_init_container_picks_krunner_build(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        init = build_kernel_pod(workload, main_kernel, settings)["spec"]["initContainers"][0]
        env = _env(init)
        assert init["image"] == settings.krunner_image
        assert env["KRUNNER_LIBC"] == "static-gnu"
        assert env["KRUNNER_LIBBAIHOOK"] == "libbaihook.ubuntu22.04.x86_64.so"

    def test_peers_resolve_by_hostname(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        spec = build_kernel_pod(workload, main_kernel, settings)["spec"]
        assert spec["hostname"] == "main1"
        assert spec["subdomain"] == "s-1"
        assert spec["dnsConfig"]["searches"] == ["s-1.bai-p.svc.cluster.local"]

    def test_owned_by_the_workload(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        ref = build_kernel_pod(workload, main_kernel, settings)["metadata"]["ownerReferences"][0]
        assert (ref["kind"], ref["uid"], ref["controller"]) == ("SessionWorkload", "uid-1", True)

    def test_rejects_a_kernel_without_memory(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        main_kernel.resource_slots = {"cpu": "1"}
        with pytest.raises(InvalidSessionWorkloadError):
            build_kernel_pod(workload, main_kernel, settings)

    def test_rejects_unresolved_vfolder_mounts(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        main_kernel.mounts = [
            VFolderVolumeMount(
                name="d", vfid="x", host_path="/vfroot/nfs/a", kernel_path="/home/work/d"
            )
        ]
        with pytest.raises(InvalidSessionWorkloadError):
            build_kernel_pod(workload, main_kernel, settings)


class TestBuildKernelSecret:
    def test_carries_config_and_work_files(
        self, workload: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        secrets = SessionSecrets(
            cluster_ssh_keypair={"public_key": "pub", "private_key": "priv"},
            internal_data={
                "11111111-0000-0000-0000-000000000001": {
                    "dotfiles": [{"path": ".vimrc", "perm": "644", "data": "x"}]
                }
            },
            bootstrap_scripts={"11111111-0000-0000-0000-000000000001": "echo hi"},
        )
        data = build_kernel_secret(workload, main_kernel, settings, secrets)["stringData"]
        entries = {
            line.split(" ", 3)[3]: line.split(" ", 3)[:3] for line in data["manifest"].splitlines()
        }
        assert entries["ssh/id_cluster"][0] == "config"
        assert entries["ssh/id_cluster"][2] == "0600"
        assert entries[".vimrc"][0] == "work"
        assert data[entries["bootstrap.sh"][1]] == "echo hi"
        assert "LOCAL_USER_ID=1000\n" in data[entries["environ.txt"][1]]


class TestSessionObjects:
    def test_headless_service_publishes_unready_pods(self, workload: SessionWorkload) -> None:
        spec = build_session_service(workload)["spec"]
        assert spec["clusterIP"] == "None"
        assert spec["publishNotReadyAddresses"] is True

    def test_pod_group_waits_for_every_kernel(self, workload: SessionWorkload) -> None:
        spec = build_pod_group(workload)["spec"]
        assert spec["minMember"] == 1
        assert spec["queue"] == "k8s"


class TestNetworkPolicy:
    def test_session_alone_without_a_persistent_network(
        self, workload: SessionWorkload, settings: ControllerSettings
    ) -> None:
        ingress = build_session_network_policy(workload, settings)["spec"]["ingress"]
        assert len(ingress) == 2

    def test_persistent_network_admits_its_sessions_in_any_namespace(
        self, workload: SessionWorkload, settings: ControllerSettings
    ) -> None:
        workload.spec.network_id = "net-1"
        ingress = build_session_network_policy(workload, settings)["spec"]["ingress"]
        peer = ingress[1]["from"][0]
        assert peer["namespaceSelector"] == {}
        assert peer["podSelector"] == {"matchLabels": {"backend.ai/network-id": "net-1"}}


class TestBindMode:
    def test_binder_mode_names_sokovan_as_the_scheduler(
        self, workload: SessionWorkload, main_kernel: KernelSpec
    ) -> None:
        settings = ControllerSettings(
            krunner_image="k@sha256:abc", bind_mode=SokovanBindMode.BINDER
        )
        spec = build_kernel_pod(workload, main_kernel, settings)["spec"]
        assert spec["schedulerName"] == "sokovan"
        assert spec["schedulingGates"] == [{"name": "scheduling.backend.ai/sokovan"}]


class TestMultiKernelSessions:
    @pytest.fixture
    def two_kernels(self, workload: SessionWorkload, main_kernel: KernelSpec) -> SessionWorkload:
        sub = main_kernel.model_copy(
            update={
                "kernel_id": "11111111-0000-0000-0000-000000000002",
                "cluster_role": "sub",
                "cluster_hostname": "sub1",
            }
        )
        workload.spec.kernels = [main_kernel, sub]
        workload.spec.cluster_size = 2
        return workload

    def test_single_node_session_requires_one_node(self, two_kernels: SessionWorkload) -> None:
        spec = build_pod_group(two_kernels)["spec"]
        assert spec["topology"]["requiredLevels"] == ["kubernetes.io/hostname"]

    def test_multi_node_session_places_kernels_freely(self, two_kernels: SessionWorkload) -> None:
        two_kernels.spec.cluster_mode = "multi-node"
        assert build_pod_group(two_kernels)["spec"].get("topology") is None

    def test_krunner_waits_for_the_peers(
        self, two_kernels: SessionWorkload, main_kernel: KernelSpec, settings: ControllerSettings
    ) -> None:
        pod = build_kernel_pod(two_kernels, main_kernel, settings)
        env = {e["name"]: e["value"] for e in pod["spec"]["initContainers"][0]["env"]}
        assert env["KRUNNER_WAIT_PEERS"] == "sub1.s-1.bai-p.svc.cluster.local"
