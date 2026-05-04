"""V1 PoC harness for the containerd backend.

This is a diagnostic CLI, not part of the agent's runtime. It walks
the CRI lifecycle (Version → ImageStatus/Pull → RunPodSandbox →
PodSandboxStatus → CreateContainer → StartContainer → ContainerStatus
→ optional pause → teardown) against a real containerd over its CRI
socket, and reports per-step results.

The point is to verify the V1 cilium-mode assumptions documented in
the project memory:

1. Synthetic ``PodSandboxConfig.metadata`` (no backing Pod object in
   the API server) does not cause Cilium CNI to reject the sandbox —
   it should fall back to ``reserved:init`` identity and still hand
   out an IP from the cluster pod CIDR.
2. ``RemovePodSandbox`` triggers CNI DEL cleanly so the assigned IP
   returns to the pool (no leak).
3. The agent process can reach containerd's CRI socket with the
   expected permissions.

Use::

    backend.ai ag cri-poc run \\
        --target unix:///run/containerd/containerd.sock \\
        --image docker.io/library/busybox:latest \\
        --pod-namespace backendai-kernels \\
        --pod-name kernel-poc

The script keeps containers alive with ``sleep infinity`` so the
operator can inspect from another shell while the lifecycle is paused
(``--pause`` flag).
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
from typing import Any

import click

log = logging.getLogger(__spec__.name)


@click.group()
def cli() -> None:
    """V1 PoC harness for the containerd / CRI backend."""


@dataclasses.dataclass
class StepResult:
    name: str
    ok: bool
    duration_ms: float
    detail: dict[str, Any]


@cli.command(name="run")
@click.option(
    "--target",
    default="unix:///run/containerd/containerd.sock",
    show_default=True,
    help="CRI gRPC target — typically a unix:// socket.",
)
@click.option(
    "--connect-timeout",
    default=5.0,
    show_default=True,
    type=float,
    help="Seconds to wait for the CRI channel to become ready before bailing out.",
)
@click.option(
    "--image",
    default="docker.io/library/busybox:latest",
    show_default=True,
    help="Image to pull (if absent) and run inside the sandbox.",
)
@click.option(
    "--pod-namespace",
    default="backendai-kernels",
    show_default=True,
    help="Synthetic K8s namespace stamped into PodSandboxConfig.metadata.namespace.",
)
@click.option(
    "--pod-name",
    default=None,
    help=("Synthetic Pod name. Defaults to 'cri-poc-<uuid>' so each run is unique."),
)
@click.option(
    "--pause",
    is_flag=True,
    help=(
        "After StartContainer, pause until ENTER is pressed so the operator can "
        "inspect the sandbox from another shell (e.g. `cilium endpoint list`, "
        "`crictl pods`, `nsenter`)."
    ),
)
@click.option(
    "--keep",
    is_flag=True,
    help="Skip teardown so the sandbox + container remain for post-mortem.",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Emit a single JSON document to stdout instead of human-readable lines.",
)
def run(
    target: str,
    connect_timeout: float,
    image: str,
    pod_namespace: str,
    pod_name: str | None,
    pause: bool,
    keep: bool,
    json_output: bool,
) -> None:
    """Walk the full CRI lifecycle once and report each step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )

    effective_pod_name = pod_name or f"cri-poc-{uuid.uuid4().hex[:8]}"
    results = asyncio.run(
        _run_lifecycle(
            target=target,
            connect_timeout_secs=connect_timeout,
            image=image,
            pod_namespace=pod_namespace,
            pod_name=effective_pod_name,
            pause=pause,
            keep=keep,
        )
    )
    _emit(results, json_output=json_output)
    if not all(r.ok for r in results):
        sys.exit(1)


async def _run_lifecycle(
    *,
    target: str,
    connect_timeout_secs: float,
    image: str,
    pod_namespace: str,
    pod_name: str,
    pause: bool,
    keep: bool,
) -> list[StepResult]:
    # Imports are deferred so `--help` works without the agent's full
    # dependency tree being available.
    from ai.backend.agent.containerd.cri.client import CriClient
    from ai.backend.agent.containerd.cri.generated import api_pb2

    results: list[StepResult] = []

    async with CriClient(target=target, connect_timeout_secs=connect_timeout_secs) as cri:
        results.append(
            await _step(
                "version",
                lambda: _do_version(cri),
            )
        )

        results.append(
            await _step(
                "image_status",
                lambda: _do_image_status(cri, api_pb2, image),
            )
        )

        if not results[-1].detail.get("present"):
            results.append(
                await _step(
                    "pull_image",
                    lambda: _do_pull_image(cri, api_pb2, image),
                )
            )

        sandbox_uid = uuid.uuid4().hex
        sandbox_config = _build_sandbox_config(api_pb2, pod_namespace, pod_name, sandbox_uid)
        sandbox_id_holder: dict[str, str] = {}
        results.append(
            await _step(
                "run_pod_sandbox",
                lambda: _do_run_sandbox(cri, sandbox_config, sandbox_id_holder),
            )
        )
        sandbox_id = sandbox_id_holder.get("id")

        if sandbox_id:
            results.append(
                await _step(
                    "pod_sandbox_status",
                    lambda: _do_sandbox_status(cri, sandbox_id),
                )
            )

            container_id_holder: dict[str, str] = {}
            container_config = _build_container_config(api_pb2, image, pod_name)
            results.append(
                await _step(
                    "create_container",
                    lambda: _do_create_container(
                        cri,
                        sandbox_id,
                        container_config,
                        sandbox_config,
                        container_id_holder,
                    ),
                )
            )
            container_id = container_id_holder.get("id")

            if container_id:
                results.append(
                    await _step(
                        "start_container",
                        lambda: _do_start_container(cri, container_id),
                    )
                )
                results.append(
                    await _step(
                        "container_status",
                        lambda: _do_container_status(cri, container_id),
                    )
                )

                if pause:
                    click.echo(
                        f"\n[pause] sandbox={sandbox_id} container={container_id} — "
                        "press ENTER to continue teardown..."
                    )
                    await asyncio.to_thread(input)

                if not keep:
                    results.append(
                        await _step(
                            "stop_container",
                            lambda: _do_stop_container(cri, container_id),
                        )
                    )
                    results.append(
                        await _step(
                            "remove_container",
                            lambda: _do_remove_container(cri, container_id),
                        )
                    )

            if not keep:
                results.append(
                    await _step(
                        "stop_pod_sandbox",
                        lambda: _do_stop_sandbox(cri, sandbox_id),
                    )
                )
                results.append(
                    await _step(
                        "remove_pod_sandbox",
                        lambda: _do_remove_sandbox(cri, sandbox_id),
                    )
                )

    return results


# --------------------------------------------------------------------- #
# Step runner
# --------------------------------------------------------------------- #


async def _step(
    name: str,
    body: Callable[[], Coroutine[Any, Any, dict[str, Any]]],
) -> StepResult:
    started = time.perf_counter()
    try:
        detail = await body()
    except Exception as exc:
        # Diagnostic harness — every failure is surfaced as a step result
        # so the operator sees which step blew up, not a python traceback.
        elapsed = (time.perf_counter() - started) * 1000.0
        return StepResult(
            name=name,
            ok=False,
            duration_ms=elapsed,
            detail={"error": f"{type(exc).__name__}: {exc}"},
        )
    elapsed = (time.perf_counter() - started) * 1000.0
    return StepResult(name=name, ok=True, duration_ms=elapsed, detail=detail)


# --------------------------------------------------------------------- #
# Step bodies — each returns a JSON-serialisable detail dict.
# --------------------------------------------------------------------- #


async def _do_version(cri: Any) -> dict[str, Any]:
    response = await cri.version()
    return {
        "runtime_name": response.runtime_name,
        "runtime_version": response.runtime_version,
        "runtime_api_version": response.runtime_api_version,
        "version": response.version,
    }


async def _do_image_status(cri: Any, api_pb2: Any, image: str) -> dict[str, Any]:
    response = await cri.image_status(api_pb2.ImageSpec(image=image))
    return {
        "present": bool(response.image.id),
        "id": response.image.id,
        "size": response.image.size,
    }


async def _do_pull_image(cri: Any, api_pb2: Any, image: str) -> dict[str, Any]:
    image_ref = await cri.pull_image(api_pb2.ImageSpec(image=image))
    return {"image_ref": image_ref}


async def _do_run_sandbox(
    cri: Any,
    sandbox_config: Any,
    holder: dict[str, str],
) -> dict[str, Any]:
    sandbox_id = await cri.run_pod_sandbox(sandbox_config)
    holder["id"] = sandbox_id
    return {"sandbox_id": sandbox_id}


async def _do_sandbox_status(cri: Any, sandbox_id: str) -> dict[str, Any]:
    response = await cri.pod_sandbox_status(sandbox_id, verbose=True)
    status = response.status
    network = status.network
    return {
        "state": status.state,
        "ip": network.ip,
        "additional_ips": [ip.ip for ip in network.additional_ips],
        "labels": dict(status.labels),
        "info_keys": sorted(response.info.keys()),
    }


async def _do_create_container(
    cri: Any,
    sandbox_id: str,
    container_config: Any,
    sandbox_config: Any,
    holder: dict[str, str],
) -> dict[str, Any]:
    container_id = await cri.create_container(
        sandbox_id=sandbox_id,
        config=container_config,
        sandbox_config=sandbox_config,
    )
    holder["id"] = container_id
    return {"container_id": container_id}


async def _do_start_container(cri: Any, container_id: str) -> dict[str, Any]:
    await cri.start_container(container_id)
    return {"container_id": container_id}


async def _do_container_status(cri: Any, container_id: str) -> dict[str, Any]:
    response = await cri.container_status(container_id)
    status = response.status
    return {
        "state": status.state,
        "image": status.image.image,
        "exit_code": status.exit_code,
        "reason": status.reason,
    }


async def _do_stop_container(cri: Any, container_id: str) -> dict[str, Any]:
    await cri.stop_container(container_id, grace_period_secs=5)
    return {"container_id": container_id}


async def _do_remove_container(cri: Any, container_id: str) -> dict[str, Any]:
    await cri.remove_container(container_id)
    return {"container_id": container_id}


async def _do_stop_sandbox(cri: Any, sandbox_id: str) -> dict[str, Any]:
    await cri.stop_pod_sandbox(sandbox_id)
    return {"sandbox_id": sandbox_id}


async def _do_remove_sandbox(cri: Any, sandbox_id: str) -> dict[str, Any]:
    await cri.remove_pod_sandbox(sandbox_id)
    return {"sandbox_id": sandbox_id}


# --------------------------------------------------------------------- #
# Proto builders — minimal viable PodSandboxConfig + ContainerConfig.
# --------------------------------------------------------------------- #


def _build_sandbox_config(
    api_pb2: Any,
    namespace: str,
    name: str,
    uid: str,
) -> Any:
    # cgroup_parent on systemd-cgroup hosts must be the PARENT SLICE
    # name (e.g. 'system.slice'), not a 'slice:prefix:name' triple.
    # The triple form makes runc create that as the sandbox's own
    # SCOPE unit, after which containerd appends the sandbox id with
    # a path separator to form '<scope>/<sandbox_id>.scope' — systemd
    # rejects that as 'Invalid unit name or type' because unit names
    # cannot contain '/'.
    #
    # Passing a plain slice (no colons) lets containerd's CRI plugin
    # create the sandbox scope INSIDE that slice using its own naming
    # convention, which produces a valid systemd unit.
    #
    # 'system.slice' is used because it always exists; on a real k8s
    # node the conventional choice would be a per-pod slice under
    # 'kubepods.slice' that kubelet would have set up. The PoC is not
    # k8s, so we don't try to mimic that. The sandbox's per-instance
    # uniqueness comes from the sandbox id assigned by containerd, not
    # from the parent cgroup.
    cgroup_parent = "system.slice"

    return api_pb2.PodSandboxConfig(
        metadata=api_pb2.PodSandboxMetadata(
            name=name,
            uid=uid,
            namespace=namespace,
            attempt=0,
        ),
        hostname=name,
        log_directory=f"/var/log/pods/{namespace}_{name}_{uid}",
        labels={
            "io.backend.ai/origin": "cri-poc",
        },
        annotations={
            "io.backend.ai/poc": "v1-cilium-validation",
        },
        linux=api_pb2.LinuxPodSandboxConfig(
            cgroup_parent=cgroup_parent,
            security_context=api_pb2.LinuxSandboxSecurityContext(
                namespace_options=api_pb2.NamespaceOption(
                    network=api_pb2.POD,
                    pid=api_pb2.CONTAINER,
                    ipc=api_pb2.POD,
                ),
            ),
        ),
    )


def _build_container_config(api_pb2: Any, image: str, pod_name: str) -> Any:
    return api_pb2.ContainerConfig(
        metadata=api_pb2.ContainerMetadata(name=f"{pod_name}-main", attempt=0),
        image=api_pb2.ImageSpec(image=image),
        # `sleep infinity` keeps the container alive so the operator can
        # nsenter / probe it during the optional --pause window.
        command=["/bin/sh"],
        args=["-c", "sleep infinity"],
        labels={"io.backend.ai/origin": "cri-poc"},
        log_path=f"{pod_name}.log",
    )


# --------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------- #


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
