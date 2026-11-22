"""The request translator: a kernel's device slots → ResourceClaims, by DeviceProfile (suggestion 4.8).

Fraction slots (`cuda.shares`) are absolute shares: `s` becomes a `shares: round(s * 100)`
capacity request, split across devices when no single device holds it (suggestion 5.3, 5.4).
An exclusive profile with `sharedSlot` asks for whole devices of that fraction slot.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Final

from kubernetes.utils.quantity import parse_quantity

from ai.backend.kube.controller.naming import (
    ANNOTATION_DEVICES,
    ANNOTATION_SHARED_DEVICES,
    kernel_labels,
    kernel_pod_name,
    session_labels,
)
from ai.backend.kube.crd.device import (
    DeviceProfileSpec,
    DriverKind,
    FractionStrategy,
    GPUAllocationPolicy,
    SharingMode,
)
from ai.backend.kube.crd.session import KernelSpec, SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError

INTRINSIC_SLOTS: Final = ("cpu", "mem")
SHARES_CAPACITY: Final = "shares"  # a bare key: in the domain of the device's driver
SHARES_CAPACITY_QUALIFIED: Final = "dra.backend.ai/shares"
SHARE_UNITS_PER_SHARE: Final = 100
PCI_BUS_ID_ATTRIBUTE: Final = "resource.kubernetes.io/pciBusID"
SLOT_NAME_ATTRIBUTE: Final = "slotName"
STANDARD_ATTRIBUTE_DOMAIN: Final = "resource.kubernetes.io"
_STANDARD_ATTRIBUTES: Final = frozenset({"numaNode", "pcieRoot", "pciBusID"})
# ComputeDomain of the NVIDIA DRA driver (v0.5, namespaced): IMEX channels for multi-node NVLink.
COMPUTE_DOMAIN_GROUP: Final = "resource.nvidia.com"
COMPUTE_DOMAIN_VERSION: Final = "v1beta1"
COMPUTE_DOMAIN_PLURAL: Final = "computedomains"
COMPUTE_DOMAIN_CLAIM: Final = "compute-domain-channel"
_SLOT_NAME_ATTRIBUTES: Final = ("slotName", "dra.backend.ai/slotName")
_RX_NAME: Final = re.compile(r"[^a-z0-9-]+")


@dataclass(frozen=True)
class DeviceRequest:
    """One request of a claim."""

    name: str
    count: int = 1
    shares: int | None = None  # 0.01-share units per device, for a fraction request
    # Share capacities of the devices to try in order (`firstAvailable`), for a split request
    # in a pool of devices of different capacities.
    alternatives: tuple[int, ...] = ()


@dataclass(frozen=True)
class DeviceClaim:
    """One slot of one kernel: a ResourceClaim, or an extended resource of a device plugin."""

    slot_name: str
    name: str  # the Pod's claim name
    profile: DeviceProfileSpec
    requests: tuple[DeviceRequest, ...]
    shares_capacity: str = SHARES_CAPACITY
    extended_resource: str | None = None  # set: a container limit instead of a claim

    @property
    def count(self) -> int:
        return sum(r.count for r in self.requests)

    @property
    def is_fraction(self) -> bool:
        return any(r.shares is not None for r in self.requests)

    @property
    def on_shared_devices(self) -> bool:
        """The claim's devices have `shares` capacity, which the scheduler accounts by claim."""
        return self.is_fraction or self.profile.shared_slot is not None

    @property
    def whole_devices(self) -> int:
        """Devices of the profile's own slot the claim holds alone."""
        return 0 if self.on_shared_devices else self.count

    @property
    def shared_devices(self) -> int:
        """Distinct devices with `shares` capacity the claim takes a share of, or all of."""
        if self.is_fraction:
            return len(self.requests)
        return self.count if self.profile.shared_slot is not None else 0


@dataclass(frozen=True)
class SharePool:
    """Share capacities (0.01-share units) of the devices of one fraction profile, by node."""

    capacities: Mapping[str, tuple[int, ...]] = field(default_factory=dict)
    capacity_name: str = SHARES_CAPACITY

    @property
    def distinct(self) -> tuple[int, ...]:
        """Distinct capacities, largest first."""
        return tuple(sorted({c for caps in self.capacities.values() for c in caps}, reverse=True))


def claim_name(slot_name: str) -> str:
    return _RX_NAME.sub("-", slot_name.lower()).strip("-")


def device_slots(kernel: KernelSpec) -> dict[str, Decimal]:
    """The kernel's non-zero slots other than CPU and memory."""
    return {
        slot: Decimal(raw)
        for slot, raw in kernel.resource_slots.items()
        if slot not in INTRINSIC_SLOTS and Decimal(raw) != 0
    }


def needs_share_pools(
    kernels: Iterable[KernelSpec], profiles: Mapping[str, DeviceProfileSpec]
) -> bool:
    return any(
        (p := profiles.get(slot)) is not None and p.sharing_mode == SharingMode.FRACTION
        for k in kernels
        for slot in device_slots(k)
    )


def _attribute(device: Mapping[str, Any], names: Sequence[str]) -> Any:
    attrs: Mapping[str, Mapping[str, Any]] = device.get("attributes") or {}
    for name in names:
        if (value := attrs.get(name)) is not None:
            return next(iter(value.values()), None)
    return None


def share_pools(
    resource_slices: Iterable[Mapping[str, Any]], profiles: Iterable[DeviceProfileSpec]
) -> dict[str, SharePool]:
    """Slot name → the share capacities its driver publishes in ResourceSlices."""
    pools: dict[str, SharePool] = {}
    for profile in profiles:
        if profile.sharing_mode != SharingMode.FRACTION:
            continue
        by_node: dict[str, list[int]] = defaultdict(list)
        capacity_name = SHARES_CAPACITY
        for rs in resource_slices:
            spec = rs.get("spec") or {}
            if spec.get("driver") != profile.driver_name:
                continue
            node = spec.get("nodeName") or (spec.get("pool") or {}).get("name") or ""
            for raw in spec.get("devices") or []:
                device = raw.get("basic", raw)  # v1beta1 nests the device under `basic`
                slot = _attribute(device, _SLOT_NAME_ATTRIBUTES)
                if slot is not None and slot != profile.slot_name:
                    continue
                capacity: Mapping[str, Mapping[str, Any]] = device.get("capacity") or {}
                for name in (SHARES_CAPACITY, SHARES_CAPACITY_QUALIFIED):
                    if name in capacity:
                        value = capacity[name].get("value", capacity[name])
                        by_node[node].append(int(parse_quantity(value)))
                        capacity_name = name
                        break
        pools[profile.slot_name] = SharePool(
            {node: tuple(sorted(caps, reverse=True)) for node, caps in by_node.items()},
            capacity_name,
        )
    return pools


def translate(
    kernel: KernelSpec,
    profiles: Mapping[str, DeviceProfileSpec],
    policy: GPUAllocationPolicy = GPUAllocationPolicy.BAI,
    pools: Mapping[str, SharePool] | None = None,
) -> list[DeviceClaim]:
    claims = []
    unsupported = []
    for slot, amount in sorted(device_slots(kernel).items()):
        profile = profiles.get(slot)
        if profile is None:
            unsupported.append(slot)
            continue
        if profile.shared_slot is not None:
            _check_shared_slot(kernel, profile, profiles, policy)
        pool = (pools or {}).get(slot, SharePool())
        claims.append(_claim(kernel, slot, amount, profile, policy, pool))
    if unsupported:
        raise InvalidSessionWorkloadError(
            f"kernel {kernel.kernel_id}: no DeviceProfile for slots {', '.join(unsupported)}"
        )
    return claims


def _check_shared_slot(
    kernel: KernelSpec,
    profile: DeviceProfileSpec,
    profiles: Mapping[str, DeviceProfileSpec],
    policy: GPUAllocationPolicy,
) -> None:
    """A `sharedSlot` profile is exclusive and matches the driver and DeviceClass of the fraction
    profile of that slot."""
    prefix = f"kernel {kernel.kernel_id}: {profile.slot_name} (sharedSlot {profile.shared_slot})"
    if policy != GPUAllocationPolicy.BAI:
        raise InvalidSessionWorkloadError(
            f"{prefix}: the {policy} GPU allocation policy has no shared devices"
        )
    if profile.sharing_mode != SharingMode.EXCLUSIVE:
        raise InvalidSessionWorkloadError(
            f"{prefix}: sharing mode is {profile.sharing_mode}, not exclusive"
        )
    shared = profiles.get(profile.shared_slot or "")
    if shared is None or shared.sharing_mode != SharingMode.FRACTION:
        raise InvalidSessionWorkloadError(f"{prefix}: no fraction DeviceProfile for that slot")
    if (shared.driver_name, shared.device_class_name) != (
        profile.driver_name,
        profile.device_class_name,
    ):
        raise InvalidSessionWorkloadError(
            f"{prefix}: driver and DeviceClass differ from those of {shared.slot_name}"
        )


def _claim(
    kernel: KernelSpec,
    slot: str,
    amount: Decimal,
    profile: DeviceProfileSpec,
    policy: GPUAllocationPolicy,
    pool: SharePool,
) -> DeviceClaim:
    name = claim_name(slot)
    whole = amount == amount.to_integral_value()
    if policy != GPUAllocationPolicy.BAI and profile.sharing_mode == SharingMode.FRACTION:
        raise InvalidSessionWorkloadError(
            f"kernel {kernel.kernel_id}: {slot} is a fraction of a device, which the"
            f" {policy} GPU allocation policy does not support"
        )
    if policy == GPUAllocationPolicy.DEVICE_PLUGIN:
        if profile.extended_resource_name:
            if profile.sharing_mode != SharingMode.EXCLUSIVE:
                raise InvalidSessionWorkloadError(
                    f"kernel {kernel.kernel_id}: {slot} names an extended resource but its"
                    f" sharing mode is {profile.sharing_mode}, not exclusive"
                )
            if not whole:
                raise InvalidSessionWorkloadError(
                    f"kernel {kernel.kernel_id}: {slot} {amount} is not a whole number of devices"
                )
            return DeviceClaim(
                slot,
                name,
                profile,
                (DeviceRequest(name, int(amount)),),
                extended_resource=profile.extended_resource_name,
            )
    match profile.sharing_mode:
        case SharingMode.EXCLUSIVE | SharingMode.PARTITION if whole:
            return DeviceClaim(slot, name, profile, (DeviceRequest(name, int(amount)),))
        case SharingMode.EXCLUSIVE | SharingMode.PARTITION:
            raise InvalidSessionWorkloadError(
                f"kernel {kernel.kernel_id}: {slot} {amount} is not a whole number of devices"
            )
        case SharingMode.FRACTION:
            units = int((amount * SHARE_UNITS_PER_SHARE).to_integral_value(rounding=ROUND_HALF_UP))
            if units < 1:
                raise InvalidSessionWorkloadError(
                    f"kernel {kernel.kernel_id}: {slot} {amount} is less than 0.01 shares"
                )
            parts = plan_shares(units, pool, profile.fraction_strategy)
            if parts is None:
                raise InvalidSessionWorkloadError(
                    f"kernel {kernel.kernel_id}: {slot} {amount} exceeds the shares of every node"
                )
            if len(parts) == 1:
                requests: tuple[DeviceRequest, ...] = (DeviceRequest(name, 1, parts[0]),)
            else:
                distinct = pool.distinct
                requests = tuple(
                    DeviceRequest(
                        f"{name}-{idx}",
                        1,
                        part,
                        tuple(c for c in distinct if c >= part) if len(distinct) > 1 else (),
                    )
                    for idx, part in enumerate(parts)
                )
            return DeviceClaim(slot, name, profile, requests, pool.capacity_name)
        case _:
            raise InvalidSessionWorkloadError(
                f"kernel {kernel.kernel_id}: {slot} uses sharing mode {profile.sharing_mode},"
                " which the controller does not translate yet"
            )


def plan_shares(units: int, pool: SharePool, strategy: FractionStrategy | str) -> list[int] | None:
    """Per-device parts of `units`, or None when no node holds them.

    One part when a device holds it (or the pool is unknown); otherwise the plan of the node
    that needs the fewest devices.
    """
    if not pool.capacities or units <= max(pool.distinct):
        return [units]
    plans = []
    for node, caps in sorted(pool.capacities.items()):
        plan = (
            _evenly(units, caps)
            if FractionStrategy(strategy) == FractionStrategy.EVENLY
            else _fill(units, caps)
        )
        if plan is not None:
            plans.append(plan)
    return min(plans, key=len) if plans else None


def _fill(units: int, caps: Sequence[int]) -> list[int] | None:
    """The largest devices first, each as full as it goes."""
    parts = []
    remaining = units
    for cap in sorted(caps, reverse=True):
        if remaining <= 0:
            break
        take = min(cap, remaining)
        parts.append(take)
        remaining -= take
    return parts if remaining <= 0 else None


def _evenly(units: int, caps: Sequence[int]) -> list[int] | None:
    """Equal parts on the fewest devices; the last part takes the rounding remainder."""
    ordered = sorted(caps, reverse=True)
    for n in range(max(1, math.ceil(units / ordered[0])), len(ordered) + 1):
        base = units // n
        parts = [base] * (n - 1) + [units - base * (n - 1)]
        if all(p <= c for p, c in zip(sorted(parts, reverse=True), ordered, strict=False)):
            return parts
    return None


def attribute_name(profile: DeviceProfileSpec, name: str) -> str:
    """The fully qualified attribute the profile's driver publishes for a Backend.AI name:
    `attributeMap` first, then the standard attributes, then the driver's own domain."""
    mapped = profile.attribute_map.get(name)
    if mapped is None:
        mapped = f"{STANDARD_ATTRIBUTE_DOMAIN}/{name}" if name in _STANDARD_ATTRIBUTES else name
    return mapped if "/" in mapped else f"{profile.driver_name}/{mapped}"


def attribute_cel(profile: DeviceProfileSpec, name: str) -> str:
    domain, _, attr = attribute_name(profile, name).rpartition("/")
    return f"device.attributes[{json.dumps(domain)}].{attr}"


def attribute_selector(profile: DeviceProfileSpec, name: str, value: str) -> str:
    """CEL matching devices whose attribute (a Backend.AI name, e.g. `model`) equals `value`."""
    return f"{attribute_cel(profile, name)} == {json.dumps(value)}"


def slot_selector(profile: DeviceProfileSpec) -> str | None:
    """None for an external driver that publishes no slot attribute: its DeviceClass selects."""
    if (
        profile.driver_kind == DriverKind.EXTERNAL
        and SLOT_NAME_ATTRIBUTE not in profile.attribute_map
    ):
        return None
    return attribute_selector(
        profile, SLOT_NAME_ATTRIBUTE, profile.shared_slot or profile.slot_name
    )


def capacity_selector(profile: DeviceProfileSpec, capacity_name: str, value: int) -> str:
    domain, _, name = capacity_name.rpartition("/")
    return (
        f'device.capacity["{domain or profile.driver_name}"].{name}'
        f'.compareTo(quantity("{value}")) == 0'
    )


def device_key(profile: DeviceProfileSpec) -> str:
    """How sokovan counts the devices of a profile: `<driver>/<slot it is published for>`. An
    external driver's devices without a slotName attribute count under the driver name."""
    if slot_selector(profile) is None:
        return f"{profile.driver_name}/{profile.driver_name}"
    return f"{profile.driver_name}/{profile.shared_slot or profile.slot_name}"


def resource_claim_name(workload: SessionWorkload, kernel: KernelSpec, claim: DeviceClaim) -> str:
    return f"{kernel_pod_name(workload, kernel)}-{claim.name}"


def _request_body(
    claim: DeviceClaim, request: DeviceRequest, capacity: int | None = None
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "deviceClassName": claim.profile.device_class_name,
        "allocationMode": "ExactCount",
        "count": request.count,
    }
    selectors = []
    if claim.profile.sharing_mode in (SharingMode.EXCLUSIVE, SharingMode.PARTITION):
        # A whole GPU and a MIG instance of one driver differ by the slot they serve.
        if (slot := slot_selector(claim.profile)) is not None:
            selectors.append({"cel": {"expression": slot}})
    if request.shares is not None:
        body["capacity"] = {"requests": {claim.shares_capacity: str(request.shares)}}
    if capacity is not None:
        selectors.append({
            "cel": {"expression": capacity_selector(claim.profile, claim.shares_capacity, capacity)}
        })
    if selectors:
        body["selectors"] = selectors
    return body


def build_resource_claim(
    workload: SessionWorkload,
    kernel: KernelSpec,
    claim: DeviceClaim,
    owner: Mapping[str, Any],
) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    for request in claim.requests:
        if request.alternatives:
            requests.append({
                "name": request.name,
                "firstAvailable": [
                    {"name": f"cap-{capacity}", **_request_body(claim, request, capacity)}
                    for capacity in request.alternatives
                ],
            })
        else:
            requests.append({"name": request.name, "exactly": _request_body(claim, request)})
    names = [r.name for r in claim.requests]
    constraints: list[dict[str, Any]] = []
    if len(claim.requests) > 1:
        constraints.append({
            "requests": names,
            "distinctAttribute": attribute_name(claim.profile, PCI_BUS_ID_ATTRIBUTE),
        })
    if claim.profile.match_attributes and claim.count > 1:
        constraints += [
            {"requests": names, "matchAttribute": attribute_name(claim.profile, attr)}
            for attr in claim.profile.match_attributes
        ]
    spec: dict[str, Any] = {"devices": {"requests": requests}}
    if constraints:
        spec["devices"]["constraints"] = constraints
    if claim.profile.opaque_config:
        spec["devices"]["config"] = [
            {
                "requests": names,
                "opaque": {
                    "driver": claim.profile.driver_name,
                    "parameters": claim.profile.opaque_config,
                },
            }
        ]
    return {
        "apiVersion": "resource.k8s.io/v1",
        "kind": "ResourceClaim",
        "metadata": {
            "name": resource_claim_name(workload, kernel, claim),
            "namespace": workload.metadata["namespace"],
            "labels": kernel_labels(workload, kernel),
            "ownerReferences": [dict(owner)],
        },
        "spec": spec,
    }


@dataclass(frozen=True)
class PodDeviceParts:
    pod_claims: list[dict[str, Any]]  # the Pod's `resourceClaims`
    container_claims: list[dict[str, str]]  # the kernel container's `resources.claims`
    extended_resources: dict[str, str]  # device plugin resource → count, limits and requests
    annotations: dict[str, str]


def needs_compute_domain(
    workload: SessionWorkload, devices: Mapping[str, Sequence[DeviceClaim]]
) -> bool:
    """A session of several kernels with a device of a `computeDomain` profile."""
    return len(workload.spec.kernels) > 1 and any(
        c.profile.compute_domain for claims in devices.values() for c in claims
    )


def compute_domain_name(workload: SessionWorkload) -> str:
    return str(workload.metadata["name"])


def compute_domain_channel_template(workload: SessionWorkload) -> str:
    """The ResourceClaimTemplate the NVIDIA DRA driver creates for the ComputeDomain."""
    return f"{compute_domain_name(workload)}-channel"


def build_compute_domain(workload: SessionWorkload, owner: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": f"{COMPUTE_DOMAIN_GROUP}/{COMPUTE_DOMAIN_VERSION}",
        "kind": "ComputeDomain",
        "metadata": {
            "name": compute_domain_name(workload),
            "namespace": workload.metadata["namespace"],
            "labels": session_labels(workload),
            "ownerReferences": [dict(owner)],
        },
        "spec": {
            "numNodes": len(workload.spec.kernels),
            "channel": {
                "resourceClaimTemplate": {"name": compute_domain_channel_template(workload)}
            },
        },
    }


def pod_device_parts(
    workload: SessionWorkload,
    kernel: KernelSpec,
    claims: Sequence[DeviceClaim],
    *,
    compute_domain: bool = False,
) -> PodDeviceParts:
    whole: dict[str, int] = {}
    shared: dict[str, int] = {}
    extended: dict[str, int] = {}
    for c in claims:
        if c.extended_resource is not None:
            extended[c.extended_resource] = extended.get(c.extended_resource, 0) + c.count
        elif not c.on_shared_devices:
            key = device_key(c.profile)
            whole[key] = whole.get(key, 0) + c.whole_devices
        else:
            driver = c.profile.driver_name
            shared[driver] = shared.get(driver, 0) + c.shared_devices
    annotations = {}
    if whole:
        annotations[ANNOTATION_DEVICES] = json.dumps(whole, sort_keys=True)
    if shared:
        annotations[ANNOTATION_SHARED_DEVICES] = json.dumps(shared, sort_keys=True)
    dra = [c for c in claims if c.extended_resource is None]
    pod_claims = [
        {"name": c.name, "resourceClaimName": resource_claim_name(workload, kernel, c)} for c in dra
    ]
    container_claims = [{"name": c.name} for c in dra]
    if compute_domain:
        pod_claims.append({
            "name": COMPUTE_DOMAIN_CLAIM,
            "resourceClaimTemplateName": compute_domain_channel_template(workload),
        })
        container_claims.append({"name": COMPUTE_DOMAIN_CLAIM})
    return PodDeviceParts(
        pod_claims=pod_claims,
        container_claims=container_claims,
        extended_resources={k: str(v) for k, v in extended.items()},
        annotations=annotations,
    )
