from __future__ import annotations

from typing import Any

from ai.backend.kube.preflight import (
    Outcome,
    check_bai_node_ownership,
    check_consumable_capacity,
    check_crds,
    check_dra_drivers,
    check_gpu_policy,
    check_sokovan_nodes,
)


def _node(name: str, mode: str | None) -> dict[str, Any]:
    labels = {"dra.backend.ai/driver-mode": mode} if mode else {}
    return {"metadata": {"name": name, "labels": labels}}


def _slice(node: str, driver: str, shared: bool = False) -> dict[str, Any]:
    device: dict[str, Any] = {"name": "d0"}
    if shared:
        device["allowMultipleAllocations"] = True
    return {"spec": {"nodeName": node, "driver": driver, "devices": [device]}}


def _profile(mode: str) -> dict[str, Any]:
    return {
        "metadata": {"name": "p"},
        "spec": {"slotName": "cuda.shares", "sharingMode": mode, "driverName": "gpu.x"},
    }


class TestCRDs:
    def test_missing_crd_fails(self) -> None:
        checks = check_crds({"sessionworkloads.backend.ai": ["v1alpha1"]})
        outcomes = {c.name: c.outcome for c in checks}
        assert outcomes["crd sessionworkloads.backend.ai"] == Outcome.PASS
        assert outcomes["crd podgroups.scheduling.backend.ai"] == Outcome.FAIL


class TestDRADrivers:
    def test_bai_node_without_slices_fails(self) -> None:
        checks = check_dra_drivers(
            [_node("a", "bai"), _node("b", "bai"), _node("c", None)], [_slice("a", "gpu.x")], []
        )
        assert [(c.name, c.outcome) for c in checks] == [
            ("bai-dra on a", Outcome.PASS),
            ("bai-dra on b", Outcome.FAIL),
        ]


class TestConsumableCapacity:
    def test_fraction_profile_without_shared_devices_fails(self) -> None:
        [check] = check_consumable_capacity([_profile("fraction")], [_slice("a", "gpu.x")])
        assert check.outcome == Outcome.FAIL

    def test_shared_devices_pass(self) -> None:
        [check] = check_consumable_capacity(
            [_profile("fraction")], [_slice("a", "gpu.x", shared=True)]
        )
        assert check.outcome == Outcome.PASS

    def test_no_fraction_profile_needs_nothing(self) -> None:
        assert check_consumable_capacity([_profile("exclusive")], []) == []


def _gpu_node(name: str, mode: str | None, gpus: int) -> dict[str, Any]:
    node = _node(name, mode)
    node["status"] = {"allocatable": {"nvidia.com/gpu": str(gpus)}}
    return node


def _named_profile(name: str, mode: str, driver: str) -> dict[str, Any]:
    return {"metadata": {"name": name}, "spec": {"sharingMode": mode, "driverName": driver}}


class TestBaiNodeOwnership:
    def test_bai_node_with_device_plugin_gpus_fails(self) -> None:
        [check] = check_bai_node_ownership([_gpu_node("a", "bai", 8)], [])
        assert check.outcome == Outcome.FAIL

    def test_bai_node_with_nvidia_dra_devices_fails(self) -> None:
        [check] = check_bai_node_ownership([_node("a", "bai")], [_slice("a", "gpu.nvidia.com")])
        assert check.outcome == Outcome.FAIL

    def test_bai_node_owned_by_bai_dra_passes(self) -> None:
        nodes = [_node("a", "bai"), _gpu_node("b", None, 8)]
        checks = check_bai_node_ownership(nodes, [_slice("b", "gpu.nvidia.com")])
        assert [(c.name, c.outcome) for c in checks] == [("single allocator on a", Outcome.PASS)]


class TestGPUPolicy:
    def test_dra_with_nvidia_profile_needs_nvidia_slices(self) -> None:
        profiles = [_named_profile("gpu", "exclusive", "gpu.nvidia.com")]
        assert check_gpu_policy("dra", [], [], profiles).outcome == Outcome.FAIL
        slices = [_slice("a", "gpu.nvidia.com")]
        assert check_gpu_policy("dra", [], slices, profiles).outcome == Outcome.PASS

    def test_dra_without_nvidia_profile_needs_no_nvidia_slices(self) -> None:
        profiles = [_named_profile("npu", "exclusive", "atom.dra.backend.ai")]
        assert check_gpu_policy("dra", [], [], profiles).outcome == Outcome.PASS

    def test_dra_with_device_plugin_gpus_too_fails(self) -> None:
        check = check_gpu_policy(
            "dra", [_gpu_node("a", None, 8)], [_slice("b", "gpu.nvidia.com")], []
        )
        assert check.outcome == Outcome.FAIL

    def test_device_plugin_rejects_fraction_profiles(self) -> None:
        profiles = [_named_profile("fgpu", "fraction", "cuda.dra.backend.ai")]
        check = check_gpu_policy("device-plugin", [_gpu_node("a", None, 8)], [], profiles)
        assert check.outcome == Outcome.FAIL
        assert "fgpu" in check.detail

    def test_device_plugin_with_exclusive_profiles_passes(self) -> None:
        profiles = [_named_profile("gpu", "exclusive", "")]
        check = check_gpu_policy("device-plugin", [_gpu_node("a", None, 8)], [], profiles)
        assert check.outcome == Outcome.PASS

    def test_unknown_policy_fails(self) -> None:
        assert check_gpu_policy("mixed", [], [], []).outcome == Outcome.FAIL


class TestSokovanNodes:
    def test_binder_mode_needs_a_dedicated_node(self) -> None:
        check = check_sokovan_nodes([_node("n1", None)], "binder")
        assert check.outcome == Outcome.FAIL

    def test_a_dedicated_node_passes(self) -> None:
        node = _node("n1", None)
        node["spec"] = {
            "taints": [
                {"key": "sokovan.backend.ai/dedicated", "value": "true", "effect": "NoSchedule"}
            ]
        }
        check = check_sokovan_nodes([node], "binder")
        assert (check.outcome, check.detail) == (Outcome.PASS, "n1")

    def test_gate_mode_needs_no_taint(self) -> None:
        assert check_sokovan_nodes([_node("n1", None)], "gate").outcome == Outcome.PASS
