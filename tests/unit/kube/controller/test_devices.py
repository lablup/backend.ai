from __future__ import annotations

import json
from typing import Any

import pytest

from ai.backend.kube.controller.devices import (
    DeviceClaim,
    SharePool,
    build_resource_claim,
    plan_shares,
    share_pools,
    translate,
)
from ai.backend.kube.controller.manifests import (
    ControllerSettings,
    build_kernel_pod,
    owner_reference,
)
from ai.backend.kube.controller.naming import ANNOTATION_DEVICES, ANNOTATION_SHARED_DEVICES
from ai.backend.kube.crd.device import (
    DeviceProfileSpec,
    DriverKind,
    FractionStrategy,
    GPUAllocationPolicy,
    SharingMode,
)
from ai.backend.kube.crd.session import KernelSpec, SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError

H100: int = 1650  # 16.5 shares: SM-bound with the default share units
A100: int = 1350


@pytest.fixture
def cuda_profile() -> DeviceProfileSpec:
    return DeviceProfileSpec(
        slot_name="cuda.device",
        sharing_mode=SharingMode.EXCLUSIVE,
        driver_name="gpu.nvidia.com",
        device_class_name="gpu.nvidia.com",
        match_attributes=["numaNode"],
    )


@pytest.fixture
def gpu_kernel(main_kernel: KernelSpec) -> KernelSpec:
    main_kernel.resource_slots = {"cpu": "1", "mem": "1073741824", "cuda.device": "2"}
    return main_kernel


@pytest.fixture
def gpu_claims(gpu_kernel: KernelSpec, cuda_profile: DeviceProfileSpec) -> list[DeviceClaim]:
    return translate(gpu_kernel, {"cuda.device": cuda_profile})


class TestTranslate:
    def test_whole_devices_become_one_claim(self, gpu_claims: list[DeviceClaim]) -> None:
        [claim] = gpu_claims
        assert (claim.name, claim.count, claim.whole_devices) == ("cuda-device", 2, 2)

    def test_zero_slots_need_no_profile(self, main_kernel: KernelSpec) -> None:
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "rocm.device": "0"}
        assert translate(main_kernel, {}) == []

    def test_slot_without_profile_is_rejected(self, gpu_kernel: KernelSpec) -> None:
        with pytest.raises(InvalidSessionWorkloadError):
            translate(gpu_kernel, {})

    def test_fraction_of_an_exclusive_device_is_rejected(
        self, gpu_kernel: KernelSpec, cuda_profile: DeviceProfileSpec
    ) -> None:
        gpu_kernel.resource_slots["cuda.device"] = "1.5"
        with pytest.raises(InvalidSessionWorkloadError):
            translate(gpu_kernel, {"cuda.device": cuda_profile})


class TestResourceClaim:
    def test_requests_the_count_from_the_device_class(
        self, workload: SessionWorkload, gpu_kernel: KernelSpec, gpu_claims: list[DeviceClaim]
    ) -> None:
        claim = build_resource_claim(workload, gpu_kernel, gpu_claims[0], owner_reference(workload))
        [request] = claim["spec"]["devices"]["requests"]
        assert request["exactly"]["deviceClassName"] == "gpu.nvidia.com"
        assert request["exactly"]["count"] == 2
        assert claim["spec"]["devices"]["constraints"] == [
            {"requests": ["cuda-device"], "matchAttribute": "numaNode"}
        ]


class TestPodWithDevices:
    def test_pod_references_the_claim_and_records_the_demand(
        self,
        workload: SessionWorkload,
        gpu_kernel: KernelSpec,
        gpu_claims: list[DeviceClaim],
        settings: ControllerSettings,
    ) -> None:
        pod = build_kernel_pod(workload, gpu_kernel, settings, devices=gpu_claims)
        claim = build_resource_claim(workload, gpu_kernel, gpu_claims[0], owner_reference(workload))
        assert pod["spec"]["resourceClaims"] == [
            {"name": "cuda-device", "resourceClaimName": claim["metadata"]["name"]}
        ]
        assert pod["spec"]["containers"][0]["resources"]["claims"] == [{"name": "cuda-device"}]
        annotations = pod["metadata"]["annotations"]
        assert json.loads(annotations[ANNOTATION_DEVICES]) == {"gpu.nvidia.com/cuda.device": 2}


@pytest.fixture
def shares_profile() -> DeviceProfileSpec:
    return DeviceProfileSpec(
        slot_name="cuda.shares",
        sharing_mode=SharingMode.FRACTION,
        driver_name="cuda.dra.backend.ai",
        device_class_name="cuda-shares.dra.backend.ai",
    )


@pytest.fixture
def h100_pool() -> SharePool:
    return SharePool({"node-a": (H100,) * 8})


@pytest.fixture
def mixed_pool() -> SharePool:
    return SharePool({"node-a": (H100,) * 4, "node-b": (A100,) * 4})


def _shares_kernel(kernel: KernelSpec, shares: str) -> KernelSpec:
    kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.shares": shares}
    return kernel


def _requests(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = manifest["spec"]["devices"]["requests"]
    return requests


class TestFractionShares:
    @pytest.mark.parametrize(("shares", "units"), [("0.5", 50), ("1.5", 150), ("16.5", 1650)])
    def test_shares_within_one_device_are_one_request(
        self,
        main_kernel: KernelSpec,
        shares_profile: DeviceProfileSpec,
        h100_pool: SharePool,
        workload: SessionWorkload,
        shares: str,
        units: int,
    ) -> None:
        kernel = _shares_kernel(main_kernel, shares)
        [claim] = translate(
            kernel, {"cuda.shares": shares_profile}, pools={"cuda.shares": h100_pool}
        )
        [request] = _requests(
            build_resource_claim(workload, kernel, claim, owner_reference(workload))
        )
        assert request["exactly"]["count"] == 1
        assert request["exactly"]["capacity"] == {"requests": {"shares": str(units)}}
        assert (claim.whole_devices, claim.shared_devices) == (0, 1)

    def test_whole_shares_are_not_whole_devices(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec, h100_pool: SharePool
    ) -> None:
        kernel = _shares_kernel(main_kernel, "2")
        [claim] = translate(
            kernel, {"cuda.shares": shares_profile}, pools={"cuda.shares": h100_pool}
        )
        assert [r.shares for r in claim.requests] == [200]
        assert claim.whole_devices == 0

    def test_less_than_a_hundredth_is_rejected(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec
    ) -> None:
        with pytest.raises(InvalidSessionWorkloadError):
            translate(_shares_kernel(main_kernel, "0.004"), {"cuda.shares": shares_profile})

    def test_without_published_capacities_one_request_is_made(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec
    ) -> None:
        [claim] = translate(_shares_kernel(main_kernel, "20"), {"cuda.shares": shares_profile})
        assert [r.shares for r in claim.requests] == [2000]


class TestFractionSplit:
    def test_fill_takes_the_largest_device_first(
        self,
        main_kernel: KernelSpec,
        shares_profile: DeviceProfileSpec,
        h100_pool: SharePool,
        workload: SessionWorkload,
    ) -> None:
        kernel = _shares_kernel(main_kernel, "20")
        [claim] = translate(
            kernel, {"cuda.shares": shares_profile}, pools={"cuda.shares": h100_pool}
        )
        manifest = build_resource_claim(workload, kernel, claim, owner_reference(workload))
        requests = _requests(manifest)
        assert [r["exactly"]["capacity"]["requests"]["shares"] for r in requests] == ["1650", "350"]
        assert manifest["spec"]["devices"]["constraints"] == [
            {
                "requests": ["cuda-shares-0", "cuda-shares-1"],
                "distinctAttribute": "resource.kubernetes.io/pciBusID",
            }
        ]
        assert claim.shared_devices == 2

    def test_evenly_gives_equal_parts(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec, h100_pool: SharePool
    ) -> None:
        profile = shares_profile.model_copy(update={"fraction_strategy": FractionStrategy.EVENLY})
        kernel = _shares_kernel(main_kernel, "20")
        [claim] = translate(kernel, {"cuda.shares": profile}, pools={"cuda.shares": h100_pool})
        assert [r.shares for r in claim.requests] == [1000, 1000]

    def test_evenly_puts_the_remainder_on_the_last_part(self, h100_pool: SharePool) -> None:
        assert plan_shares(3301, h100_pool, FractionStrategy.EVENLY) == [1100, 1100, 1101]

    def test_more_than_any_node_holds_is_rejected(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec
    ) -> None:
        pool = SharePool({"node-a": (H100, H100)})
        with pytest.raises(InvalidSessionWorkloadError):
            translate(
                _shares_kernel(main_kernel, "40"),
                {"cuda.shares": shares_profile},
                pools={"cuda.shares": pool},
            )

    def test_mixed_capacities_get_one_alternative_per_capacity(
        self,
        main_kernel: KernelSpec,
        shares_profile: DeviceProfileSpec,
        mixed_pool: SharePool,
        workload: SessionWorkload,
    ) -> None:
        kernel = _shares_kernel(main_kernel, "20")
        [claim] = translate(
            kernel, {"cuda.shares": shares_profile}, pools={"cuda.shares": mixed_pool}
        )
        first, second = _requests(
            build_resource_claim(workload, kernel, claim, owner_reference(workload))
        )
        # The 16.5-share part fits only an H100; the remainder fits either, the largest first.
        assert [s["name"] for s in first["firstAvailable"]] == [f"cap-{H100}"]
        assert [s["name"] for s in second["firstAvailable"]] == [f"cap-{H100}", f"cap-{A100}"]
        sub = second["firstAvailable"][1]
        assert sub["capacity"] == {"requests": {"shares": "350"}}
        assert sub["selectors"] == [
            {
                "cel": {
                    "expression": 'device.capacity["cuda.dra.backend.ai"].shares'
                    f'.compareTo(quantity("{A100}")) == 0'
                }
            }
        ]

    def test_the_node_needing_fewest_devices_sets_the_plan(self, mixed_pool: SharePool) -> None:
        assert plan_shares(5000, mixed_pool, FractionStrategy.FILL) == [1650, 1650, 1650, 50]


class TestSharePools:
    def test_reads_share_capacities_of_the_profile_driver(
        self, shares_profile: DeviceProfileSpec
    ) -> None:
        slices = [
            {
                "spec": {
                    "driver": "cuda.dra.backend.ai",
                    "nodeName": "node-a",
                    "devices": [
                        {"name": "gpu-0", "capacity": {"shares": {"value": "1650"}}},
                        {
                            "name": "gpu-1",
                            "attributes": {"slotName": {"string": "cuda.shares"}},
                            "capacity": {"shares": {"value": "1350"}},
                        },
                        {
                            "name": "npu-0",
                            "attributes": {"slotName": {"string": "furiosa.device"}},
                            "capacity": {"shares": {"value": "100"}},
                        },
                    ],
                }
            },
            {
                "spec": {
                    "driver": "gpu.nvidia.com",
                    "nodeName": "node-b",
                    "devices": [{"name": "gpu-0", "capacity": {"shares": {"value": "4000"}}}],
                }
            },
        ]
        pool = share_pools(slices, [shares_profile])["cuda.shares"]
        assert pool.capacities == {"node-a": (1650, 1350)}
        assert pool.capacity_name == "shares"

    def test_accepts_the_qualified_capacity_name(self, shares_profile: DeviceProfileSpec) -> None:
        slices = [
            {
                "spec": {
                    "driver": "cuda.dra.backend.ai",
                    "nodeName": "node-a",
                    "devices": [
                        {"name": "gpu-0", "capacity": {"dra.backend.ai/shares": {"value": "800"}}}
                    ],
                }
            }
        ]
        pool = share_pools(slices, [shares_profile])["cuda.shares"]
        assert (pool.capacities, pool.capacity_name) == (
            {"node-a": (800,)},
            "dra.backend.ai/shares",
        )


class TestDevicePluginPolicy:
    @pytest.fixture
    def plugin_profile(self, cuda_profile: DeviceProfileSpec) -> DeviceProfileSpec:
        return cuda_profile.model_copy(update={"extended_resource_name": "nvidia.com/gpu"})

    def test_extended_resource_becomes_a_container_limit(
        self,
        workload: SessionWorkload,
        gpu_kernel: KernelSpec,
        plugin_profile: DeviceProfileSpec,
        settings: ControllerSettings,
    ) -> None:
        claims = translate(
            gpu_kernel, {"cuda.device": plugin_profile}, GPUAllocationPolicy.DEVICE_PLUGIN
        )
        pod = build_kernel_pod(workload, gpu_kernel, settings, devices=claims)
        resources = pod["spec"]["containers"][0]["resources"]
        assert resources["limits"]["nvidia.com/gpu"] == "2"
        assert resources["requests"]["nvidia.com/gpu"] == "2"
        assert "claims" not in resources
        assert "resourceClaims" not in pod["spec"]
        assert ANNOTATION_DEVICES not in pod["metadata"].get("annotations", {})

    def test_dra_policy_ignores_the_extended_resource(
        self, gpu_kernel: KernelSpec, plugin_profile: DeviceProfileSpec
    ) -> None:
        [claim] = translate(gpu_kernel, {"cuda.device": plugin_profile}, GPUAllocationPolicy.DRA)
        assert claim.extended_resource is None

    def test_fraction_profiles_are_rejected(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec
    ) -> None:
        with pytest.raises(InvalidSessionWorkloadError):
            translate(
                _shares_kernel(main_kernel, "0.5"),
                {"cuda.shares": shares_profile},
                GPUAllocationPolicy.DEVICE_PLUGIN,
            )

    def test_extended_resource_needs_an_exclusive_profile(
        self, main_kernel: KernelSpec, plugin_profile: DeviceProfileSpec
    ) -> None:
        profile = plugin_profile.model_copy(update={"sharing_mode": SharingMode.PARTITION})
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.device": "1"}
        with pytest.raises(InvalidSessionWorkloadError):
            translate(main_kernel, {"cuda.device": profile}, GPUAllocationPolicy.DEVICE_PLUGIN)


class TestSharedDeviceAnnotation:
    def test_a_shared_claim_is_not_counted_as_a_device(
        self,
        main_kernel: KernelSpec,
        shares_profile: DeviceProfileSpec,
        h100_pool: SharePool,
        workload: SessionWorkload,
        settings: ControllerSettings,
    ) -> None:
        kernel = _shares_kernel(main_kernel, "20")
        claims = translate(
            kernel, {"cuda.shares": shares_profile}, pools={"cuda.shares": h100_pool}
        )
        pod = build_kernel_pod(workload, kernel, settings, devices=claims)
        annotations = pod["metadata"]["annotations"]
        assert ANNOTATION_DEVICES not in annotations
        assert json.loads(annotations[ANNOTATION_SHARED_DEVICES]) == {"cuda.dra.backend.ai": 2}


class TestPartition:
    def test_a_mig_slot_selects_its_own_devices(
        self, main_kernel: KernelSpec, workload: SessionWorkload
    ) -> None:
        profile = DeviceProfileSpec(
            slot_name="cuda.device:10g-mig",
            sharing_mode=SharingMode.PARTITION,
            driver_name="cuda.dra.backend.ai",
            device_class_name="cuda.dra.backend.ai",
        )
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.device:10g-mig": "1"}
        [claim] = translate(main_kernel, {"cuda.device:10g-mig": profile})
        manifest = build_resource_claim(workload, main_kernel, claim, owner_reference(workload))
        [selector] = manifest["spec"]["devices"]["requests"][0]["exactly"]["selectors"]
        assert selector["cel"]["expression"] == (
            'device.attributes["cuda.dra.backend.ai"].slotName == "cuda.device:10g-mig"'
        )


class TestExternalDriver:
    @pytest.fixture
    def nvidia_profile(self) -> DeviceProfileSpec:
        return DeviceProfileSpec(
            slot_name="cuda.device",
            sharing_mode=SharingMode.EXCLUSIVE,
            driver_kind=DriverKind.EXTERNAL,
            driver_name="gpu.nvidia.com",
            device_class_name="gpu.nvidia.com",
        )

    def test_the_claim_selects_by_device_class_only(
        self, workload: SessionWorkload, gpu_kernel: KernelSpec, nvidia_profile: DeviceProfileSpec
    ) -> None:
        [claim] = translate(gpu_kernel, {"cuda.device": nvidia_profile})
        manifest = build_resource_claim(workload, gpu_kernel, claim, owner_reference(workload))
        [request] = manifest["spec"]["devices"]["requests"]
        assert request["exactly"]["deviceClassName"] == "gpu.nvidia.com"
        assert "selectors" not in request["exactly"]

    def test_the_demand_is_keyed_by_driver(
        self,
        workload: SessionWorkload,
        gpu_kernel: KernelSpec,
        nvidia_profile: DeviceProfileSpec,
        settings: ControllerSettings,
    ) -> None:
        claims = translate(gpu_kernel, {"cuda.device": nvidia_profile})
        pod = build_kernel_pod(workload, gpu_kernel, settings, devices=claims)
        annotations = pod["metadata"]["annotations"]
        assert json.loads(annotations[ANNOTATION_DEVICES]) == {"gpu.nvidia.com/gpu.nvidia.com": 2}
