"""Pre-flight checks of a workload cluster (suggestion-1122 12): what an install needs from the
cluster, run as a Helm hook Job. Exits non-zero when a required check fails.

python -m ai.backend.kube.preflight [--json] [--gpu-allocation-policy bai|nvidia-dra|device-plugin]
    [--bai-gpu-drivers <driver,...>] [--dynamic-mig-drivers <driver,...>] [--wait-seconds <n>]
"""

from __future__ import annotations

import asyncio
import enum
import json
import sys
import time
from collections.abc import Collection, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Final

import click
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube.crd.base import CRD_VERSION, CustomResource
from ai.backend.kube.crd.device import DeviceProfile, GPUAllocationPolicy
from ai.backend.kube.crd.scheduling import BindRequest, Queue
from ai.backend.kube.crd.schema import build_crd
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs

DRIVER_MODE_LABEL: Final = "dra.backend.ai/driver-mode"
NVIDIA_DRA_DRIVER: Final = "gpu.nvidia.com"
NVIDIA_EXTENDED_RESOURCE: Final = "nvidia.com/gpu"
# What turns the other NVIDIA GPU allocators off on the nodes bai-dra owns.
BAI_POLICY_HINT: Final = (
    "set the NVIDIA DRA driver's gpus.enabled=false (AICR: gpuResourcesEnabledOverride=false;"
    " ComputeDomain stays on) and turn the device plugin off (gpu-operator"
    " devicePlugin.enabled=false, or node label nvidia.com/gpu.deploy.device-plugin=false)"
)
RETRY_INTERVAL_SECONDS: Final = 10.0
_CRDS: Final[Sequence[type[CustomResource]]] = (
    SessionWorkload,
    StorageBinding,
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
    # Fails only until the bai-dra DaemonSets have registered (a fresh install): retried.
    transient: bool = False


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


def check_crd_fields(installed: Mapping[str, Mapping[str, Any]]) -> list[Check]:
    """`installed`: CRD name → its served openAPIV3Schema. Fails when a spec or status field the
    components write is missing: the backendai-crds chart was not upgraded before this one."""
    checks = []
    for crd in _CRDS:
        name = f"{crd.crd.plural}.{crd.crd.group}"
        schema = installed.get(name)
        if schema is None:
            continue
        expected = build_crd(crd)["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        missing = [
            f"{part}.{field}"
            for part in ("spec", "status")
            for field in expected["properties"][part].get("properties", {})
            if field not in schema.get("properties", {}).get(part, {}).get("properties", {})
        ]
        if missing:
            checks.append(
                Check(
                    f"crd fields {name}",
                    Outcome.FAIL,
                    f"missing {', '.join(missing)}: upgrade the backendai-crds chart first",
                )
            )
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
                transient=not drivers,
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


def _gpu_driver_nodes(slices: Sequence[Mapping[str, Any]], drivers: Collection[str]) -> set[str]:
    return {
        rs["spec"]["nodeName"]
        for rs in slices
        if rs.get("spec", {}).get("driver") in drivers and rs["spec"].get("nodeName")
    }


def _bai_gpu_nodes(
    nodes: Sequence[Mapping[str, Any]],
    slices: Sequence[Mapping[str, Any]],
    gpu_drivers: Collection[str] | None,
) -> list[Mapping[str, Any]]:
    """`driver-mode=bai` nodes where bai-dra allocates GPUs. `gpu_drivers`: the bai-dra drivers
    of GPUs (None: every `driver-mode=bai` node)."""
    gpu_nodes = None if gpu_drivers is None else _gpu_driver_nodes(slices, gpu_drivers)
    return [
        node
        for node in nodes
        if (node["metadata"].get("labels") or {}).get(DRIVER_MODE_LABEL) == "bai"
        and (gpu_nodes is None or node["metadata"]["name"] in gpu_nodes)
    ]


def _other_allocators(node: Mapping[str, Any], nvidia_dra: Mapping[str, int]) -> list[str]:
    others = []
    if (count := _gpu_allocatable(node)) > 0:
        others.append(f"device plugin ({NVIDIA_EXTENDED_RESOURCE}: {count})")
    if (count := nvidia_dra.get(node["metadata"]["name"], 0)) > 0:
        others.append(f"{NVIDIA_DRA_DRIVER} ({count} devices)")
    return others


def check_bai_node_ownership(
    nodes: Sequence[Mapping[str, Any]],
    slices: Sequence[Mapping[str, Any]],
    gpu_drivers: Collection[str] | None = None,
) -> list[Check]:
    """A node where bai-dra allocates GPUs has no other GPU allocator (device plugin, NVIDIA DRA
    driver); a node whose bai-dra devices are NPUs may keep its GPUs on another allocator."""
    nvidia_dra = _nvidia_dra_devices(slices)
    checks = []
    for node in _bai_gpu_nodes(nodes, slices, gpu_drivers):
        others = _other_allocators(node, nvidia_dra)
        checks.append(
            Check(
                f"single allocator on {node['metadata']['name']}",
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
    gpu_drivers: Collection[str] | None = None,
) -> Check:
    """The cluster's NVIDIA GPUs and DeviceProfiles agree with the GPU allocation policy.
    The NVIDIA DRA driver's ComputeDomain devices (another driver name) are not GPUs."""
    name = "gpu allocation policy"
    try:
        parsed = GPUAllocationPolicy(policy)
    except ValueError:
        return Check(name, Outcome.FAIL, f"unknown policy {policy!r}")
    nvidia_dra = sum(_nvidia_dra_devices(slices).values())
    plugin_gpus = sum(_gpu_allocatable(n) for n in nodes)
    match parsed:
        case GPUAllocationPolicy.BAI:
            by_node = _nvidia_dra_devices(slices)
            owned = _bai_gpu_nodes(nodes, slices, gpu_drivers)
            shared = sorted(
                f"{n['metadata']['name']}: {', '.join(others)}"
                for n in owned
                if (others := _other_allocators(n, by_node))
            )
            if shared:
                detail = f"GPUs of bai-dra nodes also allocated by {'; '.join(shared)}"
                return Check(name, Outcome.FAIL, f"bai: {detail}; {BAI_POLICY_HINT}")
            return Check(name, Outcome.PASS, f"bai: {len(owned)} bai-dra GPU nodes")
        case GPUAllocationPolicy.NVIDIA_DRA:
            wants_nvidia = any(
                p.get("spec", {}).get("driverName") == NVIDIA_DRA_DRIVER for p in profiles
            )
            if wants_nvidia and nvidia_dra == 0:
                detail = f"a DeviceProfile uses {NVIDIA_DRA_DRIVER} but no node publishes it"
                return Check(name, Outcome.FAIL, f"nvidia-dra: {detail}")
            if nvidia_dra > 0 and plugin_gpus > 0:
                detail = f"{NVIDIA_DRA_DRIVER} and the device plugin both allocate GPUs"
                return Check(name, Outcome.FAIL, f"nvidia-dra: {detail}")
            detail = f"{nvidia_dra} {NVIDIA_DRA_DRIVER} devices"
            return Check(name, Outcome.PASS, f"nvidia-dra: {detail}")
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
            transient=not shared,
        )
    ]


PROBE_COUNTER_SET: Final = "backendai-preflight"


def shared_counters_probe(driver: str) -> dict[str, Any]:
    """A counters-only ResourceSlice, created with dry run: the API server drops the field when
    DRAPartitionableDevices is off."""
    return {
        "apiVersion": "resource.k8s.io/v1",
        "kind": "ResourceSlice",
        "metadata": {"generateName": "backendai-preflight-"},
        "spec": {
            "driver": driver,
            "allNodes": True,
            "pool": {"name": "backendai-preflight", "generation": 0, "resourceSliceCount": 1},
            "sharedCounters": [
                {"name": PROBE_COUNTER_SET, "counters": {"memory-slice-0": {"value": "1"}}}
            ],
        },
    }


def check_shared_counters(
    driver: str, echoed: Mapping[str, Any] | None, error: str | None = None
) -> Check:
    """Dynamic MIG needs shared counters: the dry-run slice must keep them."""
    name = f"DRAPartitionableDevices ({driver})"
    if error is not None:
        return Check(name, Outcome.FAIL, f"dynamic MIG: the API server rejects counters: {error}")
    kept = ((echoed or {}).get("spec") or {}).get("sharedCounters") or []
    if not any(c.get("name") == PROBE_COUNTER_SET for c in kept):
        detail = "dynamic MIG: the API server drops shared counters (feature gate off?)"
        return Check(name, Outcome.FAIL, detail)
    return Check(name, Outcome.PASS, "shared counters accepted")


async def probe_shared_counters(custom: client.CustomObjectsApi, driver: str) -> Check:
    try:
        echoed = await custom.create_cluster_custom_object(
            "resource.k8s.io", "v1", "resourceslices", shared_counters_probe(driver), dry_run="All"
        )
    except ApiException as e:
        return check_shared_counters(driver, None, f"{e.status} {e.reason}")
    return check_shared_counters(driver, echoed)


def should_retry(checks: Sequence[Check]) -> bool:
    """Some check failed, and every failure may still pass once the DaemonSets register."""
    failed = [c for c in checks if c.outcome == Outcome.FAIL]
    return bool(failed) and all(c.transient for c in failed)


async def run_checks(
    api: client.ApiClient,
    gpu_policy: str,
    gpu_drivers: Collection[str] | None = None,
    dynamic_mig_drivers: Collection[str] = (),
) -> list[Check]:
    ext = client.ApiextensionsV1Api(api)
    core = client.CoreV1Api(api)
    custom = client.CustomObjectsApi(api)
    crds = await ext.list_custom_resource_definition()
    served = {c.metadata.name: [v.name for v in c.spec.versions if v.served] for c in crds.items}
    checks = check_crds(served)
    installed = {
        c.metadata.name: api.sanitize_for_serialization(v.schema.open_api_v3_schema)
        for c in crds.items
        for v in c.spec.versions
        if v.name == CRD_VERSION and v.schema is not None
    }
    checks += check_crd_fields(installed)
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
    checks += check_dra_drivers(nodes, slices, profiles)
    checks += check_bai_node_ownership(nodes, slices, gpu_drivers)
    checks.append(check_gpu_policy(gpu_policy, nodes, slices, profiles, gpu_drivers))
    checks += check_consumable_capacity(profiles, slices)
    for driver in dynamic_mig_drivers:
        checks.append(await probe_shared_counters(custom, driver))
    return checks


async def _main(
    as_json: bool,
    gpu_policy: str,
    gpu_drivers: Collection[str] | None,
    dynamic_mig_drivers: Collection[str],
    wait_seconds: float,
) -> int:
    await load_kube_config()
    deadline = time.monotonic() + wait_seconds
    async with client.ApiClient() as api:
        while True:
            checks = await run_checks(api, gpu_policy, gpu_drivers, dynamic_mig_drivers)
            if not should_retry(checks) or time.monotonic() >= deadline:
                break
            click.echo("waiting for the bai-dra drivers to register", err=True)
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)
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
    default=GPUAllocationPolicy.BAI.value,
    help="Who allocates NVIDIA GPUs: bai (bai-dra), nvidia-dra (the NVIDIA DRA driver) or"
    " device-plugin.",
)
@click.option(
    "--bai-gpu-drivers",
    envvar="BACKENDAI_PREFLIGHT_BAI_GPU_DRIVERS",
    default=None,
    help="Comma-separated bai-dra drivers of GPUs. Unset: check every driver-mode=bai node.",
)
@click.option(
    "--dynamic-mig-drivers",
    envvar="BACKENDAI_PREFLIGHT_DYNAMIC_MIG_DRIVERS",
    default="",
    help="Comma-separated bai-dra drivers with dynamic MIG: checks that the API server keeps"
    " shared counters (DRAPartitionableDevices).",
)
@click.option(
    "--wait-seconds",
    envvar="BACKENDAI_PREFLIGHT_WAIT_SECONDS",
    type=click.FloatRange(min=0),
    default=0,
    help="Retry this long while the only failures are drivers that have not registered yet.",
)
def main(
    as_json: bool,
    gpu_policy: str,
    bai_gpu_drivers: str | None,
    dynamic_mig_drivers: str,
    wait_seconds: float,
) -> None:
    quiet_client_logs()
    gpu_drivers = (
        None
        if bai_gpu_drivers is None
        else [d.strip() for d in bai_gpu_drivers.split(",") if d.strip()]
    )
    mig_drivers = [d.strip() for d in dynamic_mig_drivers.split(",") if d.strip()]
    sys.exit(asyncio.run(_main(as_json, gpu_policy, gpu_drivers, mig_drivers, wait_seconds)))


if __name__ == "__main__":
    main()
