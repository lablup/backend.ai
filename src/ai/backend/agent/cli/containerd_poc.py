"""PoC harness for the containerd native-API backend.

A diagnostic CLI (not part of the agent runtime). It walks the containerd
native-API lifecycle against a real containerd over its socket and reports
per-step results. It grows as ``ContainerdClient`` gains methods.

The point of this harness is to prove the core assumption of the
containerd-backend design: Backend.AI workloads created in a dedicated
containerd namespace (``backendai``) are invisible to a co-located kubelet
and therefore are not garbage-collected by it — unlike CRI sandboxes,
which kubelet reaps.

Use::

    backend.ai ag containerd-poc run \\
        --address unix:///run/containerd/containerd.sock \\
        --namespace backendai \\
        --image docker.io/library/busybox:latest
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import sys
import time
import uuid
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

import click

from ai.backend.agent.containerd.oci import build_oci_spec

if TYPE_CHECKING:
    from ai.backend.agent.containerd.client.client import ContainerdClient

log = logging.getLogger(__spec__.name)

# containerd task Status enum (containerd/types/task/task.proto) -> name.
_TASK_STATUS = {0: "unknown", 1: "created", 2: "running", 3: "stopped", 4: "paused", 5: "pausing"}


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
    help="Image reference to pull, prepare a rootfs from, and run a container with.",
)
@click.option(
    "--connect-timeout",
    default=5.0,
    show_default=True,
    type=float,
    help="Seconds to wait for the channel to become ready before bailing out.",
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
    connect_timeout: float,
    json_output: bool,
) -> None:
    """Walk the containerd native-API lifecycle once and report each step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )
    results = asyncio.run(
        _run_lifecycle(
            address=address,
            namespace=namespace,
            image=image,
            connect_timeout_secs=connect_timeout,
        )
    )
    _emit(results, json_output=json_output)
    if not all(r.ok for r in results):
        sys.exit(1)


_StepBody = Callable[[], Coroutine[Any, Any, dict[str, Any]]]


async def _run_lifecycle(
    *,
    address: str,
    namespace: str,
    image: str,
    connect_timeout_secs: float,
) -> list[StepResult]:
    # Deferred import so `--help` works without the agent's full dependency
    # tree (and the generated stubs) being importable.
    from ai.backend.agent.containerd.client.client import ContainerdClient

    # containerd's convention: a container's rootfs snapshot key is the
    # container id. The poc uses one id for both.
    workload_id = f"containerd-poc-{uuid.uuid4().hex[:12]}"
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

            created = await _step(
                "create_container", lambda: _do_create_container(cd, image, workload_id)
            )
            results.append(created)
            if created.ok:
                cleanups.append(("delete_container", lambda: _do_delete_container(cd, workload_id)))

                task = await _step("create_task", lambda: _do_create_task(cd, workload_id, rootfs))
                results.append(task)
                if task.ok:
                    cleanups.append(("teardown_task", lambda: _do_teardown_task(cd, workload_id)))
                    results.append(
                        await _step("start_task", lambda: _do_start_task(cd, workload_id))
                    )
                    results.append(await _step("get_task", lambda: _do_get_task(cd, workload_id)))

        # Teardown in reverse creation order.
        for name, body in reversed(cleanups):
            results.append(await _step(name, body))
        results.append(await _step("list_namespaces", lambda: _do_list_namespaces(cd)))
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
    cd: ContainerdClient, image: str, container_id: str
) -> dict[str, Any]:
    spec = build_oci_spec(
        container_id=container_id,
        args=["/bin/sh", "-c", "sleep 3600"],
    )
    await cd.create_container(
        container_id,
        image=image,
        spec=spec,
        snapshot_key=container_id,
        labels={"io.backend.ai/origin": "containerd-poc"},
    )
    return {"container_id": container_id}


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
