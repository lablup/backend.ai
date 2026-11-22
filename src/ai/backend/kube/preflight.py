"""Pre-flight checks of a workload cluster (suggestion-1122 12): what an install needs from the
cluster, run as a Helm hook Job. Exits non-zero when a required check fails.

python -m ai.backend.kube.preflight [--json] [--gpu-allocation-policy dra|device-plugin]
    [--sokovan-bind-mode gate|binder]
"""

from __future__ import annotations

import asyncio
import enum
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Final

import click
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.crd.base import CRD_VERSION, CustomResource
from ai.backend.kube.crd.device import DeviceProfile, GPUAllocationPolicy
from ai.backend.kube.crd.scheduling import BindRequest, PodGroup, Queue, SokovanBindMode
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs
from ai.backend.kube.scheduler.snapshot import DEDICATED_TAINT_KEY, DEDICATED_TAINT_VALUE

DRIVER_MODE_LABEL: Final = "dra.backend.ai/driver-mode"
NVIDIA_DRA_DRIVER: Final = "gpu.nvidia.com"
NVIDIA_EXTENDED_RESOURCE: Final = "nvidia.com/gpu"
_CRDS: Final[Sequence[type[CustomResource]]] = (
    SessionWorkload,
    StorageBinding,
    PodGroup,
    Queue,
    BindRequest,
    DeviceProfile,
)


class Outcome(enum.StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class Check:
    name: str
    outcome: Outcome
    detail: str


def check_crds(served: Mapping[str, Sequence[str]]) -> list[Check]:
    """`served`: CRD name → versions it serves."""
    checks = []
    for crd in _CRDS:
        name = f"{crd.crd.plural}.{crd.crd.group}"
        versions = served.get(name)
        if versions is None:
            checks.append(Check(f"crd {name}", Outcome.FAIL, "not installed"))
        elif CRD_VERSION not in versions:
            checks.append(Check(f"crd {name}", Outcome.FAIL, f"{CRD_VERSION} not served"))
        else:
            checks.append(Check(f"crd {name}", Outcome.PASS, CRD_VERSION))
    return checks


def check_dra_drivers(
    nodes: Sequence[Mapping[str, Any]],
    slices: Sequence[Mapping[str, Any]],
    profiles: Sequence[Mapping[str, Any]],
) -> list[Check]:
    """Every `driver-mode=bai` node publishes devices, and every DeviceProfile's driver has some."""
    published: dict[str, set[str]] = {}
    for rs in slices:
        spec = rs.get("spec", {})
        if spec.get("nodeName"):
            published.setdefault(spec["nodeName"], set()).add(spec["driver"])
    checks = []
    for node in nodes:
        meta = node["metadata"]
        if (meta.get("labels") or {}).get(DRIVER_MODE_LABEL) != "bai":
            continue
        drivers = published.get(meta["name"])
        checks.append(
            Check(
                f"bai-dra on {meta['name']}",
                Outcome.PASS if drivers else Outcome.FAIL,
                ", ".join(sorted(drivers))
                if drivers
                else "no ResourceSlice (driver not registered)",
            )
        )
    all_drivers = {d for ds in published.values() for d in ds}
    for profile in profiles:
        spec = profile.get("spec", {})
        driver = spec.get("driverName", "")
        checks.append(
            Check(
                f"device profile {profile['metadata']['name']}",
                Outcome.PASS if driver in all_drivers else Outcome.WARN,
                f"{spec.get('slotName')} → {driver}"
                + ("" if driver in all_drivers else " (no node publishes it)"),
            )
        )
    return checks


def _gpu_allocatable(node: Mapping[str, Any]) -> int:
    raw = ((node.get("status") or {}).get("allocatable") or {}).get(NVIDIA_EXTENDED_RESOURCE, "0")
    try:
        return int(raw)
    except ValueError:
        return 0


def _nvidia_dra_devices(slices: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Node name → GPU devices the NVIDIA DRA driver publishes on it."""
    counts: dict[str, int] = {}
    for rs in slices:
        spec = rs.get("spec", {})
        if spec.get("driver") == NVIDIA_DRA_DRIVER and spec.get("nodeName"):
            node = spec["nodeName"]
            counts[node] = counts.get(node, 0) + len(spec.get("devices") or [])
    return counts


def check_sokovan_nodes(nodes: Sequence[Mapping[str, Any]], bind_mode: str) -> Check:
    """In binder mode sokovan places sessions only on nodes with its dedicated taint."""
    name = "sokovan nodes"
    if bind_mode != SokovanBindMode.BINDER:
        return Check(name, Outcome.PASS, f"{bind_mode} mode: kube-scheduler binds")
    dedicated = sorted(
        node["metadata"]["name"]
        for node in nodes
        if any(
            t.get("key") == DEDICATED_TAINT_KEY
            and t.get("value") == DEDICATED_TAINT_VALUE
            and t.get("effect") == "NoSchedule"
            for t in (node.get("spec") or {}).get("taints") or []
        )
    )
    if not dedicated:
        return Check(
            name,
            Outcome.FAIL,
            f"binder mode but no node has {DEDICATED_TAINT_KEY}={DEDICATED_TAINT_VALUE}:NoSchedule",
        )
    return Check(name, Outcome.PASS, ", ".join(dedicated))


def check_bai_node_ownership(
    nodes: Sequence[Mapping[str, Any]], slices: Sequence[Mapping[str, Any]]
) -> list[Check]:
    """A `driver-mode=bai` node's GPUs have no other allocator (device plugin, NVIDIA DRA driver)."""
    nvidia_dra = _nvidia_dra_devices(slices)
    checks = []
    for node in nodes:
        meta = node["metadata"]
        if (meta.get("labels") or {}).get(DRIVER_MODE_LABEL) != "bai":
            continue
        others = []
        if (count := _gpu_allocatable(node)) > 0:
            others.append(f"device plugin ({NVIDIA_EXTENDED_RESOURCE}: {count})")
        if (count := nvidia_dra.get(meta["name"], 0)) > 0:
            others.append(f"{NVIDIA_DRA_DRIVER} ({count} devices)")
        checks.append(
            Check(
                f"single allocator on {meta['name']}",
                Outcome.FAIL if others else Outcome.PASS,
                "GPUs also allocated by " + ", ".join(others) if others else "bai-dra only",
            )
        )
    return checks


def check_gpu_policy(
    policy: str,
    nodes: Sequence[Mapping[str, Any]],
    slices: Sequence[Mapping[str, Any]],
    profiles: Sequence[Mapping[str, Any]],
) -> Check:
    """The cluster's NVIDIA GPUs and DeviceProfiles agree with the GPU allocation policy."""
    name = "gpu allocation policy"
    try:
        parsed = GPUAllocationPolicy(policy)
    except ValueError:
        return Check(name, Outcome.FAIL, f"unknown policy {policy!r}")
    nvidia_dra = sum(_nvidia_dra_devices(slices).values())
    plugin_gpus = sum(_gpu_allocatable(n) for n in nodes)
    match parsed:
        case GPUAllocationPolicy.DRA:
            wants_nvidia = any(
                p.get("spec", {}).get("driverName") == NVIDIA_DRA_DRIVER for p in profiles
            )
            if wants_nvidia and nvidia_dra == 0:
                detail = f"a DeviceProfile uses {NVIDIA_DRA_DRIVER} but no node publishes it"
                return Check(name, Outcome.FAIL, f"dra: {detail}")
            if nvidia_dra > 0 and plugin_gpus > 0:
                detail = f"{NVIDIA_DRA_DRIVER} and the device plugin both allocate GPUs"
                return Check(name, Outcome.FAIL, f"dra: {detail}")
            return Check(name, Outcome.PASS, f"dra: {nvidia_dra} {NVIDIA_DRA_DRIVER} devices")
        case GPUAllocationPolicy.DEVICE_PLUGIN:
            fractions = sorted(
                p["metadata"]["name"]
                for p in profiles
                if p.get("spec", {}).get("sharingMode") == "fraction"
            )
            if fractions:
                detail = f"fraction DeviceProfiles are not allowed: {', '.join(fractions)}"
                return Check(name, Outcome.FAIL, f"device-plugin: {detail}")
            if nvidia_dra > 0:
                detail = f"{NVIDIA_DRA_DRIVER} also publishes {nvidia_dra} devices"
                return Check(name, Outcome.FAIL, f"device-plugin: {detail}")
            return Check(name, Outcome.PASS, f"device-plugin: {plugin_gpus} GPUs allocatable")


def check_consumable_capacity(
    profiles: Sequence[Mapping[str, Any]], slices: Sequence[Mapping[str, Any]]
) -> list[Check]:
    """A fraction profile needs DRAConsumableCapacity: the API server drops the field otherwise."""
    fraction_drivers = {
        p["spec"].get("driverName")
        for p in profiles
        if p.get("spec", {}).get("sharingMode") == "fraction"
    }
    if not fraction_drivers:
        return []
    shared = any(
        d.get("allowMultipleAllocations")
        for rs in slices
        if rs.get("spec", {}).get("driver") in fraction_drivers
        for d in rs["spec"].get("devices") or []
    )
    return [
        Check(
            "DRAConsumableCapacity",
            Outcome.PASS if shared else Outcome.FAIL,
            "shared devices published"
            if shared
            else "fraction profile but no device allows multiple allocations (feature gate off?)",
        )
    ]


async def run_checks(api: client.ApiClient, gpu_policy: str, bind_mode: str) -> list[Check]:
    ext = client.ApiextensionsV1Api(api)
    core = client.CoreV1Api(api)
    custom = client.CustomObjectsApi(api)
    crds = await ext.list_custom_resource_definition()
    served = {c.metadata.name: [v.name for v in c.spec.versions if v.served] for c in crds.items}
    checks = check_crds(served)
    try:
        slices = (
            await custom.list_cluster_custom_object("resource.k8s.io", "v1", "resourceslices")
        )["items"]
        checks.append(Check("resource.k8s.io/v1", Outcome.PASS, "DRA API served"))
    except ApiException as e:
        checks.append(Check("resource.k8s.io/v1", Outcome.FAIL, f"DRA API not served ({e.status})"))
        return checks
    profiles: list[dict[str, Any]] = []
    if any(c.outcome == Outcome.PASS and "deviceprofiles" in c.name for c in checks):
        profiles = (
            await custom.list_cluster_custom_object(
                DeviceProfile.crd.group, CRD_VERSION, DeviceProfile.crd.plural
            )
        )["items"]
    nodes = [api.sanitize_for_serialization(n) for n in (await core.list_node()).items]
    checks.append(check_sokovan_nodes(nodes, bind_mode))
    checks += check_dra_drivers(nodes, slices, profiles)
    checks += check_bai_node_ownership(nodes, slices)
    checks.append(check_gpu_policy(gpu_policy, nodes, slices, profiles))
    checks += check_consumable_capacity(profiles, slices)
    return checks


async def _main(as_json: bool, gpu_policy: str, bind_mode: str) -> int:
    await load_kube_config()
    async with client.ApiClient() as api:
        checks = await run_checks(api, gpu_policy, bind_mode)
    if as_json:
        click.echo(json.dumps([asdict(c) for c in checks], indent=2))
    else:
        for c in checks:
            click.echo(f"[{c.outcome.value:4}] {c.name}: {c.detail}")
    return 1 if any(c.outcome == Outcome.FAIL for c in checks) else 0


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Print the checks as JSON.")
@click.option(
    "--gpu-allocation-policy",
    "gpu_policy",
    envvar="BACKENDAI_GPU_ALLOCATION_POLICY",
    default=GPUAllocationPolicy.DRA.value,
    help="Who allocates NVIDIA GPUs: dra (the NVIDIA DRA driver) or device-plugin.",
)
@click.option(
    "--sokovan-bind-mode",
    "bind_mode",
    envvar="BACKENDAI_SOKOVAN_BIND_MODE",
    type=click.Choice([m.value for m in SokovanBindMode]),
    default=SokovanBindMode.GATE.value,
    help="How sokovan binds placed Pods; binder needs nodes with its dedicated taint.",
)
def main(as_json: bool, gpu_policy: str, bind_mode: str) -> None:
    quiet_client_logs()
    sys.exit(asyncio.run(_main(as_json, gpu_policy, bind_mode)))


if __name__ == "__main__":
    main()
