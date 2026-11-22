"""The request translator: a kernel's device slots → ResourceClaims, by DeviceProfile (suggestion 4.8)."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Final

from ai.backend.kube.controller.naming import (
    ANNOTATION_DEVICES,
    ANNOTATION_SHARED_DEVICES,
    kernel_labels,
    kernel_pod_name,
)
from ai.backend.kube.crd.device import DeviceProfileSpec, SharingMode
from ai.backend.kube.crd.session import KernelSpec, SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError

INTRINSIC_SLOTS: Final = ("cpu", "mem")
_RX_NAME: Final = re.compile(r"[^a-z0-9-]+")


@dataclass(frozen=True)
class DeviceClaim:
    """One slot of one kernel, satisfied by one ResourceClaim."""

    slot_name: str
    name: str  # the Pod's claim name and the request name
    profile: DeviceProfileSpec
    count: int
    capacity: Mapping[str, str] = field(default_factory=dict)  # per device, for a shared one

    @property
    def whole_devices(self) -> int:
        """Devices the claim holds alone; a share of a device is not counted."""
        return 0 if self.capacity else self.count


def claim_name(slot_name: str) -> str:
    return _RX_NAME.sub("-", slot_name.lower()).strip("-")


def device_slots(kernel: KernelSpec) -> dict[str, Decimal]:
    """The kernel's non-zero slots other than CPU and memory."""
    return {
        slot: Decimal(raw)
        for slot, raw in kernel.resource_slots.items()
        if slot not in INTRINSIC_SLOTS and Decimal(raw) != 0
    }


def translate(kernel: KernelSpec, profiles: Mapping[str, DeviceProfileSpec]) -> list[DeviceClaim]:
    claims = []
    unsupported = []
    for slot, amount in sorted(device_slots(kernel).items()):
        profile = profiles.get(slot)
        if profile is None:
            unsupported.append(slot)
            continue
        claims.append(_claim(kernel, slot, amount, profile))
    if unsupported:
        raise InvalidSessionWorkloadError(
            f"kernel {kernel.kernel_id}: no DeviceProfile for slots {', '.join(unsupported)}"
        )
    return claims


def _claim(
    kernel: KernelSpec, slot: str, amount: Decimal, profile: DeviceProfileSpec
) -> DeviceClaim:
    whole = amount == amount.to_integral_value()
    match profile.sharing_mode:
        case SharingMode.EXCLUSIVE | SharingMode.PARTITION if whole:
            return DeviceClaim(slot, claim_name(slot), profile, int(amount))
        case SharingMode.FRACTION if whole:
            # Whole devices of a shared kind: the capacity's default takes all of each.
            return DeviceClaim(slot, claim_name(slot), profile, int(amount))
        case SharingMode.FRACTION if amount < 1 and profile.capacity_conversions:
            capacity = {
                c.capacity: str(int(amount * Decimal(str(c.factor))))
                for c in profile.capacity_conversions
            }
            return DeviceClaim(slot, claim_name(slot), profile, 1, capacity)
        case SharingMode.EXCLUSIVE | SharingMode.PARTITION | SharingMode.FRACTION:
            raise InvalidSessionWorkloadError(
                f"kernel {kernel.kernel_id}: {slot} {amount} is neither whole devices nor a part"
                " of one device"
            )
        case _:
            raise InvalidSessionWorkloadError(
                f"kernel {kernel.kernel_id}: {slot} uses sharing mode {profile.sharing_mode},"
                " which the controller does not translate yet"
            )


def slot_selector(profile: DeviceProfileSpec) -> str:
    return f'device.attributes["{profile.driver_name}"].slotName == "{profile.slot_name}"'


def device_key(profile: DeviceProfileSpec) -> str:
    """How sokovan counts the devices of a profile: `<driver>/<slot>`."""
    return f"{profile.driver_name}/{profile.slot_name}"


def resource_claim_name(workload: SessionWorkload, kernel: KernelSpec, claim: DeviceClaim) -> str:
    return f"{kernel_pod_name(workload, kernel)}-{claim.name}"


def build_resource_claim(
    workload: SessionWorkload,
    kernel: KernelSpec,
    claim: DeviceClaim,
    owner: Mapping[str, Any],
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "deviceClassName": claim.profile.device_class_name,
        "allocationMode": "ExactCount",
        "count": claim.count,
    }
    if claim.capacity:
        request["capacity"] = {"requests": dict(claim.capacity)}
    if claim.profile.sharing_mode in (SharingMode.EXCLUSIVE, SharingMode.PARTITION):
        # A whole GPU and a MIG instance of one driver differ by the slot they serve.
        request["selectors"] = [{"cel": {"expression": slot_selector(claim.profile)}}]
    spec: dict[str, Any] = {"devices": {"requests": [{"name": claim.name, "exactly": request}]}}
    if claim.profile.match_attributes and claim.count > 1:
        spec["devices"]["constraints"] = [
            {"requests": [claim.name], "matchAttribute": attr}
            for attr in claim.profile.match_attributes
        ]
    if claim.profile.opaque_config:
        spec["devices"]["config"] = [
            {
                "requests": [claim.name],
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


def pod_device_parts(
    workload: SessionWorkload, kernel: KernelSpec, claims: Sequence[DeviceClaim]
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, str]]:
    """The Pod's `resourceClaims`, the kernel container's `resources.claims` and annotations."""
    if not claims:
        return [], [], {}
    whole: dict[str, int] = {}
    shared: dict[str, int] = {}
    for c in claims:
        if c.whole_devices:
            key = device_key(c.profile)
            whole[key] = whole.get(key, 0) + c.count
        else:
            shared[c.profile.driver_name] = shared.get(c.profile.driver_name, 0) + c.count
    annotations = {}
    if whole:
        annotations[ANNOTATION_DEVICES] = json.dumps(whole, sort_keys=True)
    if shared:
        annotations[ANNOTATION_SHARED_DEVICES] = json.dumps(shared, sort_keys=True)
    return (
        [
            {"name": c.name, "resourceClaimName": resource_claim_name(workload, kernel, c)}
            for c in claims
        ],
        [{"name": c.name} for c in claims],
        annotations,
    )
