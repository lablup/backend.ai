"""Pre-flight checks of a workload cluster (suggestion-1122 12): what an install needs from the
cluster, run as a Helm hook Job. Exits non-zero when a required check fails.

python -m ai.backend.kube.preflight [--json]
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
from ai.backend.kube.crd.device import DeviceProfile
from ai.backend.kube.crd.scheduling import BindRequest, PodGroup, Queue
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs

DRIVER_MODE_LABEL: Final = "dra.backend.ai/driver-mode"
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


async def run_checks(api: client.ApiClient) -> list[Check]:
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
    checks += check_dra_drivers(nodes, slices, profiles)
    checks += check_consumable_capacity(profiles, slices)
    return checks


async def _main(as_json: bool) -> int:
    await load_kube_config()
    async with client.ApiClient() as api:
        checks = await run_checks(api)
    if as_json:
        click.echo(json.dumps([asdict(c) for c in checks], indent=2))
    else:
        for c in checks:
            click.echo(f"[{c.outcome.value:4}] {c.name}: {c.detail}")
    return 1 if any(c.outcome == Outcome.FAIL for c in checks) else 0


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Print the checks as JSON.")
def main(as_json: bool) -> None:
    quiet_client_logs()
    sys.exit(asyncio.run(_main(as_json)))


if __name__ == "__main__":
    main()
