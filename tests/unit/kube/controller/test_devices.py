from __future__ import annotations

import json

import pytest

from ai.backend.kube.controller.devices import (
    DeviceClaim,
    build_resource_claim,
    translate,
)
from ai.backend.kube.controller.manifests import (
    ControllerSettings,
    build_kernel_pod,
    owner_reference,
)
from ai.backend.kube.controller.naming import ANNOTATION_DEVICES, ANNOTATION_SHARED_DEVICES
from ai.backend.kube.crd.device import CapacityConversion, DeviceProfileSpec, SharingMode
from ai.backend.kube.crd.session import KernelSpec, SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError


@pytest.fixture
def cuda_profile() -> DeviceProfileSpec:
    return DeviceProfileSpec(
        slot_name="cuda.device",
        sharing_mode=SharingMode.EXCLUSIVE,
        driver_name="cuda.dra.backend.ai",
        device_class_name="cuda.dra.backend.ai",
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
        assert (claim.name, claim.count) == ("cuda-device", 2)

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
        assert request["exactly"]["deviceClassName"] == "cuda.dra.backend.ai"
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
        assert json.loads(annotations[ANNOTATION_DEVICES]) == {"cuda.dra.backend.ai/cuda.device": 2}


@pytest.fixture
def shares_profile() -> DeviceProfileSpec:
    return DeviceProfileSpec(
        slot_name="cuda.shares",
        sharing_mode=SharingMode.FRACTION,
        driver_name="cuda.dra.backend.ai",
        device_class_name="cuda.dra.backend.ai",
        capacity_conversions=[CapacityConversion(capacity="shares", factor=100)],
    )


class TestFraction:
    def test_part_of_a_device_requests_capacity(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec, workload: SessionWorkload
    ) -> None:
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.shares": "0.5"}
        [claim] = translate(main_kernel, {"cuda.shares": shares_profile})
        manifest = build_resource_claim(workload, main_kernel, claim, owner_reference(workload))
        request = manifest["spec"]["devices"]["requests"][0]["exactly"]
        assert request["count"] == 1
        assert request["capacity"] == {"requests": {"shares": "50"}}
        assert claim.whole_devices == 0

    def test_whole_shares_take_whole_devices(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec
    ) -> None:
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.shares": "2"}
        [claim] = translate(main_kernel, {"cuda.shares": shares_profile})
        assert (claim.count, claim.capacity, claim.whole_devices) == (2, {}, 2)

    def test_more_than_one_device_in_parts_is_rejected(
        self, main_kernel: KernelSpec, shares_profile: DeviceProfileSpec
    ) -> None:
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.shares": "1.5"}
        with pytest.raises(InvalidSessionWorkloadError):
            translate(main_kernel, {"cuda.shares": shares_profile})

    def test_a_shared_claim_is_not_counted_as_a_device(
        self,
        main_kernel: KernelSpec,
        shares_profile: DeviceProfileSpec,
        workload: SessionWorkload,
        settings: ControllerSettings,
    ) -> None:
        main_kernel.resource_slots = {"cpu": "1", "mem": "1", "cuda.shares": "0.5"}
        claims = translate(main_kernel, {"cuda.shares": shares_profile})
        pod = build_kernel_pod(workload, main_kernel, settings, devices=claims)
        annotations = pod["metadata"]["annotations"]
        assert ANNOTATION_DEVICES not in annotations
        assert json.loads(annotations[ANNOTATION_SHARED_DEVICES]) == {"cuda.dra.backend.ai": 1}


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
