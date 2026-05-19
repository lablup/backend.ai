"""PoC harness for the containerd native-API backend.

A diagnostic CLI (not part of the agent runtime). It walks the containerd
native-API lifecycle against a real containerd over its socket and reports
per-step results.

Two subcommands:

- ``run`` — the full workload lifecycle: pull an image, prepare a rootfs
  snapshot, create a CNI-attached network namespace, create and start a
  container task in it, then tear everything down. With ``--keep`` the
  workload is left running so connectivity can be tested against it.
- ``net`` — just the network layer: netns + CNI attach/detach.

The point of this harness is to prove the containerd-backend design:
Backend.AI workloads created in a dedicated containerd namespace
(``backendai``) are invisible to a co-located kubelet — unlike CRI
sandboxes, which kubelet reaps — yet still join the cluster CNI fabric.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import sys
import time
import uuid
from collections.abc import Callable, Coroutine, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp
import click

from ai.backend.agent.containerd.network import netns
from ai.backend.agent.containerd.network.base import NetworkProvider
from ai.backend.agent.containerd.network.cilium import CiliumNetworkProvider
from ai.backend.agent.containerd.oci import build_oci_spec

if TYPE_CHECKING:
    from ai.backend.agent.containerd.client.client import ContainerdClient

log = logging.getLogger(__spec__.name)

# containerd task Status enum (containerd/types/task/task.proto) -> name.
_TASK_STATUS = {0: "unknown", 1: "created", 2: "running", 3: "stopped", 4: "paused", 5: "pausing"}

# Default cilium agent REST API socket on the node.
_DEFAULT_CILIUM_AGENT_SOCK = Path("/var/run/cilium/cilium.sock")

_StepBody = Callable[[], Coroutine[Any, Any, dict[str, Any]]]


def _parse_labels(labels_kv: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for kv in labels_kv:
        if "=" not in kv:
            raise click.BadParameter(f"--label expects K=V, got {kv!r}")
        key, _, value = kv.partition("=")
        out[key] = value
    return out


@click.group()
def cli() -> None:
    """PoC harness for the containerd native-API backend."""


@dataclasses.dataclass
class StepResult:
    name: str
    ok: bool
    duration_ms: float
    detail: dict[str, Any]


@cli.command(name="run")
@click.option(
    "--address",
    default="unix:///run/containerd/containerd.sock",
    show_default=True,
    help="containerd native-API gRPC target — typically a unix:// socket.",
)
@click.option(
    "--namespace",
    default="backendai",
    show_default=True,
    help="containerd metadata namespace for Backend.AI workloads.",
)
@click.option(
    "--image",
    default="docker.io/library/busybox:latest",
    show_default=True,
    help="Image reference to pull and run a container with.",
)
@click.option(
    "--network-name",
    default="cilium",
    show_default=True,
    help="CNI conflist name for the network provider.",
)
@click.option(
    "--connect-timeout",
    default=5.0,
    show_default=True,
    type=float,
    help="Seconds to wait for the channel to become ready before bailing out.",
)
@click.option(
    "--keep",
    is_flag=True,
    help="Leave the workload (netns, container, task) running instead of tearing it down.",
)
@click.option(
    "--label",
    "labels_kv",
    multiple=True,
    metavar="K=V",
    help=(
        "Label to push onto the cilium endpoint via the agent's labels API. "
        "Repeatable. Triggers the identity-assignment path that pulls the "
        "endpoint out of 'reserved:init' (see cni-exp.md exp.8)."
    ),
)
@click.option(
    "--check-identity",
    is_flag=True,
    help=(
        "After attach, query the cilium agent and report the endpoint's identity id and label set."
    ),
)
@click.option(
    "--ping",
    "ping_target",
    default=None,
    metavar="ADDR",
    help="If set, ping ADDR from inside the workload netns after start_task.",
)
@click.option(
    "--cilium-agent-sock",
    default=str(_DEFAULT_CILIUM_AGENT_SOCK),
    show_default=True,
    help="Path to the node-local cilium agent REST socket (for --check-identity).",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Emit a single JSON document to stdout instead of human-readable lines.",
)
def run(
    address: str,
    namespace: str,
    image: str,
    network_name: str,
    connect_timeout: float,
    keep: bool,
    labels_kv: tuple[str, ...],
    check_identity: bool,
    ping_target: str | None,
    cilium_agent_sock: str,
    json_output: bool,
) -> None:
    """Walk the full containerd workload lifecycle once and report each step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )
    labels = _parse_labels(labels_kv)
    results = asyncio.run(
        _run_lifecycle(
            address=address,
            namespace=namespace,
            image=image,
            network_name=network_name,
            keep=keep,
            connect_timeout_secs=connect_timeout,
            labels=labels or None,
            check_identity=check_identity,
            ping_target=ping_target,
            cilium_agent_sock=Path(cilium_agent_sock),
        )
    )
    _emit(results, json_output=json_output)
    if not all(r.ok for r in results):
        sys.exit(1)


@cli.command(name="net")
@click.option(
    "--network-name",
    default="cilium",
    show_default=True,
    help="CNI conflist name (matched by the conflist's `name` field).",
)
@click.option(
    "--label",
    "labels_kv",
    multiple=True,
    metavar="K=V",
    help=(
        "Label to push onto the cilium endpoint via the agent's labels API. "
        "Repeatable. Triggers the identity-assignment path."
    ),
)
@click.option(
    "--check-identity",
    is_flag=True,
    help="After attach, query the cilium agent and report the endpoint identity.",
)
@click.option(
    "--ping",
    "ping_target",
    default=None,
    metavar="ADDR",
    help="If set, ping ADDR from inside the netns after attach.",
)
@click.option(
    "--cilium-agent-sock",
    default=str(_DEFAULT_CILIUM_AGENT_SOCK),
    show_default=True,
    help="Path to the node-local cilium agent REST socket (for --check-identity).",
)
@click.option(
    "--keep",
    is_flag=True,
    help=(
        "Leave the netns + CNI attachment in place after the run so the "
        "endpoint can be inspected from outside (e.g. via cilium-dbg)."
    ),
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Emit a single JSON document to stdout instead of human-readable lines.",
)
def net(
    network_name: str,
    labels_kv: tuple[str, ...],
    check_identity: bool,
    ping_target: str | None,
    cilium_agent_sock: str,
    keep: bool,
    json_output: bool,
) -> None:
    """Walk the network layer once: netns -> CNI attach -> detach."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )
    labels = _parse_labels(labels_kv)
    results = asyncio.run(
        _run_network(
            network_name=network_name,
            labels=labels or None,
            check_identity=check_identity,
            ping_target=ping_target,
            cilium_agent_sock=Path(cilium_agent_sock),
            keep=keep,
        )
    )
    _emit(results, json_output=json_output)
    if not all(r.ok for r in results):
        sys.exit(1)


async def _run_lifecycle(
    *,
    address: str,
    namespace: str,
    image: str,
    network_name: str,
    keep: bool,
    connect_timeout_secs: float,
    labels: Mapping[str, str] | None,
    check_identity: bool,
    ping_target: str | None,
    cilium_agent_sock: Path,
) -> list[StepResult]:
    # Deferred import so `--help` works without the agent's full dependency
    # tree (and the generated stubs) being importable.
    from ai.backend.agent.containerd.client.client import ContainerdClient

    # containerd's convention: a container's rootfs snapshot key is the
    # container id. The poc uses one id for the container, the snapshot,
    # and the network namespace.
    workload_id = f"containerd-poc-{uuid.uuid4().hex[:12]}"
    netns_path = netns.netns_path(workload_id)
    provider = CiliumNetworkProvider(network_name=network_name)
    results: list[StepResult] = []
    # Cleanup steps pushed as resources are created, run in reverse at the end.
    cleanups: list[tuple[str, _StepBody]] = []
    # Rootfs mounts from prepare_snapshot, consumed by create_task.
    rootfs: list[Any] = []

    async with ContainerdClient(
        address=address,
        namespace=namespace,
        connect_timeout_secs=connect_timeout_secs,
    ) as cd:
        results.append(await _step("version", lambda: _do_version(cd)))
        results.append(await _step("ensure_namespace", lambda: _do_ensure_namespace(cd)))
        results.append(await _step("pull_image", lambda: _do_pull_image(cd, image)))
        results.append(await _step("get_image", lambda: _do_get_image(cd, image)))

        prepared = await _step(
            "prepare_snapshot", lambda: _do_prepare_snapshot(cd, image, workload_id, rootfs)
        )
        results.append(prepared)
        if prepared.ok:
            cleanups.append(("remove_snapshot", lambda: _do_remove_snapshot(cd, workload_id)))

            netns_created = await _step("create_netns", lambda: _do_create_netns(workload_id))
            results.append(netns_created)
            if netns_created.ok:
                cleanups.append(("delete_netns", lambda: _do_delete_netns(workload_id)))

                attached = await _step(
                    "attach",
                    lambda: _do_attach(provider, workload_id, netns_path, labels=labels),
                )
                results.append(attached)
                if attached.ok:
                    cleanups.append((
                        "detach",
                        lambda: _do_detach(provider, workload_id, netns_path),
                    ))
                    if check_identity:
                        results.append(
                            await _step(
                                "check_identity",
                                lambda: _do_check_identity(workload_id, cilium_agent_sock),
                            )
                        )

                    created = await _step(
                        "create_container",
                        lambda: _do_create_container(cd, image, workload_id, netns_path),
                    )
                    results.append(created)
                    if created.ok:
                        cleanups.append((
                            "delete_container",
                            lambda: _do_delete_container(cd, workload_id),
                        ))

                        task = await _step(
                            "create_task", lambda: _do_create_task(cd, workload_id, rootfs)
                        )
                        results.append(task)
                        if task.ok:
                            cleanups.append((
                                "teardown_task",
                                lambda: _do_teardown_task(cd, workload_id),
                            ))
                            results.append(
                                await _step("start_task", lambda: _do_start_task(cd, workload_id))
                            )
                            results.append(
                                await _step("get_task", lambda: _do_get_task(cd, workload_id))
                            )
                            if ping_target:
                                results.append(
                                    await _step(
                                        "ping",
                                        lambda: _do_ping(workload_id, ping_target),
                                    )
                                )

        if keep:
            log.info("--keep: workload '%s' left running (netns %s)", workload_id, netns_path)
        else:
            for name, body in reversed(cleanups):
                results.append(await _step(name, body))
        results.append(await _step("list_namespaces", lambda: _do_list_namespaces(cd)))
    return results


async def _run_network(
    *,
    network_name: str,
    labels: Mapping[str, str] | None,
    check_identity: bool,
    ping_target: str | None,
    cilium_agent_sock: Path,
    keep: bool = False,
) -> list[StepResult]:
    workload_id = f"containerd-poc-net-{uuid.uuid4().hex[:12]}"
    provider = CiliumNetworkProvider(network_name=network_name)
    results: list[StepResult] = []
    # Cleanup steps pushed as resources are created, run in reverse at the end.
    cleanups: list[tuple[str, _StepBody]] = []

    results.append(await _step("preflight", lambda: _do_net_preflight(provider)))

    created = await _step("create_netns", lambda: _do_create_netns(workload_id))
    results.append(created)
    if created.ok:
        cleanups.append(("delete_netns", lambda: _do_delete_netns(workload_id)))
        path = netns.netns_path(workload_id)
        attached = await _step(
            "attach", lambda: _do_attach(provider, workload_id, path, labels=labels)
        )
        results.append(attached)
        if attached.ok:
            cleanups.append(("detach", lambda: _do_detach(provider, workload_id, path)))
            if check_identity:
                results.append(
                    await _step(
                        "check_identity",
                        lambda: _do_check_identity(workload_id, cilium_agent_sock),
                    )
                )
            if ping_target:
                results.append(
                    await _step(
                        "ping",
                        lambda: _do_ping(workload_id, ping_target),
                    )
                )

    if keep:
        log.info(
            "--keep: netns %s and cilium endpoint left in place (workload %s)",
            netns.netns_path(workload_id),
            workload_id,
        )
    else:
        # Teardown in reverse creation order.
        for name, body in reversed(cleanups):
            results.append(await _step(name, body))
    return results


async def _step(name: str, body: _StepBody) -> StepResult:
    started = time.perf_counter()
    try:
        detail = await body()
    except Exception as exc:
        # Diagnostic harness — surface every failure as a step result so
        # the operator sees which step blew up, not a python traceback.
        elapsed = (time.perf_counter() - started) * 1000.0
        return StepResult(
            name=name,
            ok=False,
            duration_ms=elapsed,
            detail={"error": f"{type(exc).__name__}: {exc}"},
        )
    elapsed = (time.perf_counter() - started) * 1000.0
    return StepResult(name=name, ok=True, duration_ms=elapsed, detail=detail)


async def _do_version(cd: ContainerdClient) -> dict[str, Any]:
    response = await cd.version()
    return {"version": response.version, "revision": response.revision}


async def _do_ensure_namespace(cd: ContainerdClient) -> dict[str, Any]:
    await cd.ensure_namespace()
    return {"namespace": cd.namespace}


async def _do_pull_image(cd: ContainerdClient, image: str) -> dict[str, Any]:
    ref = await cd.pull_image(image)
    return {"image": ref}


async def _do_get_image(cd: ContainerdClient, image: str) -> dict[str, Any]:
    record = await cd.get_image(image)
    return {
        "name": record.name,
        "target_media_type": record.target.media_type,
        "target_digest": record.target.digest,
    }


async def _do_prepare_snapshot(
    cd: ContainerdClient, image: str, snapshot_key: str, rootfs_out: list[Any]
) -> dict[str, Any]:
    mounts = await cd.prepare_image_rootfs(image, snapshot_key)
    rootfs_out.clear()
    rootfs_out.extend(mounts)
    return {
        "snapshot_key": snapshot_key,
        "mount_count": len(mounts),
        "mount_types": sorted({m.type for m in mounts}),
    }


async def _do_create_container(
    cd: ContainerdClient, image: str, container_id: str, netns_path: str
) -> dict[str, Any]:
    spec = build_oci_spec(
        container_id=container_id,
        args=["/bin/sh", "-c", "sleep 3600"],
        netns_path=netns_path,
    )
    await cd.create_container(
        container_id,
        image=image,
        spec=spec,
        snapshot_key=container_id,
        labels={"io.backend.ai/origin": "containerd-poc"},
    )
    return {"container_id": container_id, "netns": netns_path}


async def _do_create_task(
    cd: ContainerdClient, container_id: str, rootfs: list[Any]
) -> dict[str, Any]:
    pid = await cd.create_task(container_id, rootfs=rootfs)
    return {"container_id": container_id, "pid": pid}


async def _do_start_task(cd: ContainerdClient, container_id: str) -> dict[str, Any]:
    pid = await cd.start_task(container_id)
    return {"container_id": container_id, "pid": pid}


async def _do_get_task(cd: ContainerdClient, container_id: str) -> dict[str, Any]:
    process = await cd.get_task(container_id)
    if process is None:
        return {"status": "missing", "pid": 0}
    return {
        "status": _TASK_STATUS.get(process.status, process.status),
        "pid": process.pid,
    }


async def _do_teardown_task(cd: ContainerdClient, container_id: str) -> dict[str, Any]:
    await cd.kill_task(container_id)
    exit_status = await cd.wait_task(container_id)
    await cd.delete_task(container_id)
    return {"container_id": container_id, "exit_status": exit_status}


async def _do_delete_container(cd: ContainerdClient, container_id: str) -> dict[str, Any]:
    await cd.delete_container(container_id)
    return {"container_id": container_id}


async def _do_remove_snapshot(cd: ContainerdClient, snapshot_key: str) -> dict[str, Any]:
    await cd.remove_snapshot(snapshot_key)
    return {"snapshot_key": snapshot_key}


async def _do_list_namespaces(cd: ContainerdClient) -> dict[str, Any]:
    namespaces = await cd.list_namespaces()
    return {"namespaces": sorted(ns.name for ns in namespaces)}


async def _do_net_preflight(provider: NetworkProvider) -> dict[str, Any]:
    await provider.preflight()
    return {"provider": provider.name}


async def _do_create_netns(name: str) -> dict[str, Any]:
    path = await netns.create_netns(name)
    return {"netns": path}


async def _do_attach(
    provider: NetworkProvider,
    workload_id: str,
    netns_path: str,
    *,
    labels: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    attachment = await provider.attach(workload_id, netns_path, labels=labels)
    return {
        "ipv4": attachment.ipv4,
        "mac": attachment.mac,
        "interface": attachment.interface,
        "labels_applied": len(labels) if labels else 0,
    }


async def _do_check_identity(workload_id: str, sock_path: Path) -> dict[str, Any]:
    """Query the cilium agent for the endpoint that backs ``workload_id``.

    Polls briefly because identity may take a moment to materialize.
    Returns identity + the full ``LabelConfigurationStatus`` so the
    operator can see which category each label lives in (``realized.user``
    vs ``derived``) — useful to figure out why ``reserved:init`` is or is
    not removed by our PATCH.
    """
    if not sock_path.exists():
        raise RuntimeError(f"cilium agent socket not found at {sock_path}")
    connector = aiohttp.UnixConnector(path=str(sock_path))
    async with aiohttp.ClientSession(connector=connector) as session:
        endpoint_id: int | None = None
        last_state: dict[str, Any] | None = None
        for _ in range(20):
            async with session.get("http://localhost/v1/endpoint") as resp:
                if resp.status >= 400:
                    raise RuntimeError(
                        f"GET /v1/endpoint -> {resp.status}: {(await resp.text()).strip()}"
                    )
                endpoints = await resp.json()
            for ep in endpoints:
                status = ep.get("status") or {}
                ext = status.get("external-identifiers") or {}
                if ext.get("container-id") != workload_id:
                    continue
                identity = status.get("identity") or {}
                policy_realized = (status.get("policy") or {}).get("realized") or {}
                candidate = {
                    "endpoint_id": ep.get("id"),
                    "identity_id": identity.get("id"),
                    "identity_labels": identity.get("labels", []),
                    "policy_enabled": policy_realized.get("policy-enabled", "unknown"),
                }
                ident_id = candidate["identity_id"]
                if isinstance(ident_id, int) and ident_id >= 256:
                    last_state = candidate
                    endpoint_id = candidate["endpoint_id"]
                    break
            if last_state is not None:
                break
            await asyncio.sleep(0.2)
        if last_state is None or endpoint_id is None:
            raise RuntimeError(
                f"no cilium endpoint matched container-id={workload_id!r} with a real identity"
            )
        # Augment with the full label-category breakdown so we can tell
        # whether reserved:init lives in user / derived / disabled. This
        # is the key diagnostic for the 'reserved:init re-appears' case.
        async with session.get(f"http://localhost/v1/endpoint/{endpoint_id}/labels") as resp:
            if resp.status < 400:
                lstatus = await resp.json()
                realized = lstatus.get("realized") or {}
                last_state["label_realized_user"] = realized.get("user", [])
                last_state["label_derived"] = lstatus.get("derived", [])
                last_state["label_disabled"] = lstatus.get("disabled", [])
                last_state["label_security_relevant"] = lstatus.get("security-relevant", [])
            else:
                last_state["labels_dump_error"] = (
                    f"GET /v1/endpoint/{endpoint_id}/labels -> {resp.status}"
                )
        return last_state


async def _do_ping(netns_name: str, target: str, *, count: int = 3) -> dict[str, Any]:
    """Run ``ping -c COUNT TARGET`` from inside the workload netns.

    Uses ``ip netns exec`` from the host; the netns must be the one
    create_netns set up (the harness reuses ``workload_id`` as the
    netns name, so it works out).
    """
    proc = await asyncio.create_subprocess_exec(
        "ip",
        "netns",
        "exec",
        netns_name,
        "ping",
        "-c",
        str(count),
        "-W",
        "2",
        target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    raw, _ = await proc.communicate()
    output = raw.decode("utf-8", "replace")
    if proc.returncode != 0:
        raise RuntimeError(
            f"ping {target} from netns {netns_name!r} exited {proc.returncode}\n{output}"
        )
    summary = ""
    for line in output.splitlines():
        if "packets transmitted" in line:
            summary = line.strip()
            break
    return {"target": target, "summary": summary or output.splitlines()[-1]}


async def _do_detach(
    provider: NetworkProvider, workload_id: str, netns_path: str
) -> dict[str, Any]:
    await provider.detach(workload_id, netns_path)
    return {"workload_id": workload_id}


async def _do_delete_netns(name: str) -> dict[str, Any]:
    await netns.delete_netns(name)
    return {"netns_name": name}


def _emit(results: list[StepResult], *, json_output: bool) -> None:
    if json_output:
        payload = {
            "results": [dataclasses.asdict(r) for r in results],
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r.ok),
                "failed": sum(1 for r in results if not r.ok),
            },
        }
        click.echo(json.dumps(payload, indent=2, default=str))
        return

    for result in results:
        marker = "✓" if result.ok else "✗"
        click.echo(f"{marker} {result.name} ({result.duration_ms:.1f} ms)")
        for key, value in result.detail.items():
            click.echo(f"    {key}: {value}")

    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    click.echo(f"\n{passed} passed, {failed} failed")
