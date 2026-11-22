from __future__ import annotations

from typing import Any

from ai.backend.kube.preflight import (
    Outcome,
    check_consumable_capacity,
    check_crds,
    check_dra_drivers,
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
