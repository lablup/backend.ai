"""Shared counters of partitionable devices (KEP-4815): what still fits next to the allocations.

bai-dra's dynamic MIG publishes per GPU a counter set that the whole GPU consumes in full and
each MIG placement in part (`go/bai-dra-driver/nvmig`).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

from kubernetes.utils.quantity import parse_quantity

# (driver, pool, counter set) → counter → value
type _Counters = dict[tuple[str, str, str], dict[str, Decimal]]
# (driver, pool, device)
type _DeviceKey = tuple[str, str, str]


def _quantity(counter: Mapping[str, Any]) -> Decimal:
    return Decimal(str(parse_quantity(counter.get("value", "0"))))


def _allocated_devices(claims: Iterable[Mapping[str, Any]]) -> set[_DeviceKey]:
    """Devices held by an allocation; a shared device once, however many shares it has."""
    held = set()
    for claim in claims:
        allocation = (claim.get("status") or {}).get("allocation") or {}
        for result in (allocation.get("devices") or {}).get("results") or []:
            if result.get("adminAccess"):
                continue
            held.add((result["driver"], result["pool"], result["device"]))
    return held


def without_counter_blocked_devices(
    resource_slices: Iterable[Mapping[str, Any]],
    resource_claims: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """The slices without the unallocated devices whose counters no longer fit, e.g. the MIG
    placements of a GPU allocated whole, or a GPU one of whose MIG placements is allocated."""
    slices = list(resource_slices)
    available: _Counters = {}
    consumption: dict[_DeviceKey, list[tuple[str, dict[str, Decimal]]]] = {}
    for rs in slices:
        spec = rs.get("spec") or {}
        driver, pool = spec.get("driver", ""), (spec.get("pool") or {}).get("name", "")
        for counter_set in spec.get("sharedCounters") or []:
            available[driver, pool, counter_set["name"]] = {
                name: _quantity(c) for name, c in (counter_set.get("counters") or {}).items()
            }
        for device in spec.get("devices") or []:
            if uses := device.get("consumesCounters"):
                consumption[driver, pool, device["name"]] = [
                    (
                        u["counterSet"],
                        {n: _quantity(c) for n, c in (u.get("counters") or {}).items()},
                    )
                    for u in uses
                ]
    if not consumption:
        return slices
    held = _allocated_devices(resource_claims)
    for key in held & consumption.keys():
        driver, pool, _ = key
        for counter_set, counters in consumption[key]:
            remaining = available.get((driver, pool, counter_set), {})
            for name, value in counters.items():
                if name in remaining:
                    remaining[name] -= value

    def fits(key: _DeviceKey) -> bool:
        driver, pool, _ = key
        for counter_set, counters in consumption.get(key, []):
            remaining = available.get((driver, pool, counter_set), {})
            if any(remaining.get(n, Decimal(0)) < v for n, v in counters.items()):
                return False
        return True

    out: list[Mapping[str, Any]] = []
    for rs in slices:
        spec = rs.get("spec") or {}
        driver, pool = spec.get("driver", ""), (spec.get("pool") or {}).get("name", "")
        devices = spec.get("devices") or []
        kept = [
            d
            for d in devices
            if (key := (driver, pool, d["name"])) in held or key not in consumption or fits(key)
        ]
        out.append(rs if len(kept) == len(devices) else {**rs, "spec": {**spec, "devices": kept}})
    return out
