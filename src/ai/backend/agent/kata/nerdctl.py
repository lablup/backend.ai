"""
nerdctl / containerd shim helpers for the (hacky) KataAgent MVP.

The single functional delta between DockerAgent and KataAgent is *how the
already-assembled ``container_config`` dict gets turned into a running
container*.  DockerAgent hands the dict to ``aiodocker``; KataAgent translates
it into a ``nerdctl run`` invocation against the Kata runtime
(``io.containerd.kata.v2``) so the kernel boots inside a lightweight VM.

This module is intentionally a thin subprocess shim — see
``mvp-findings-kataagent.md`` and BEP-1051 for why the production backend should
drive the containerd gRPC API directly instead.

The translation function (:func:`translate_container_config_to_nerdctl_args`) is
a pure function (modulo the injected volume resolver) so it can be unit-tested
without a Kata host.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Final

from ai.backend.agent.errors.kata import KataVolumeResolutionError, NerdctlError
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: Default containerd runtime handler installed by kata-deploy / kata-manager.
DEFAULT_KATA_RUNTIME: Final[str] = os.environ.get("BACKENDAI_KATA_RUNTIME", "io.containerd.kata.v2")
#: The container engine CLI used to drive containerd. ``nerdctl`` ships an
#: embedded bridge+portmap CNI and implements ``-p`` host-port publishing, which
#: is exactly what the ``127.0.0.1`` repl-port assumption needs (see §6b.4).
DEFAULT_NERDCTL_BIN: Final[str] = os.environ.get("BACKENDAI_NERDCTL_BIN", "nerdctl")
#: containerd namespace nerdctl operates in. Kept separate from Docker's "moby"
#: namespace on purpose so KataAgent and DockerAgent can coexist on one host.
DEFAULT_NERDCTL_NAMESPACE: Final[str] = os.environ.get("BACKENDAI_NERDCTL_NAMESPACE", "default")

#: HostConfig keys this MVP knowingly does NOT translate. We log them once so the
#: findings report can track the gaps (mostly GPU/device + Docker-only knobs).
_UNTRANSLATED_HOSTCONFIG_KEYS: Final[frozenset[str]] = frozenset({
    "PublishAllPorts",  # we publish explicitly via -p
    "LogConfig",  # nerdctl uses its own json logger; `nerdctl logs` still works
    "RestartPolicy",
    "DeviceRequests",  # NVIDIA/GPU — out of scope for the non-confidential MVP
    "Devices",
})


def _nerdctl_base(
    *, nerdctl_bin: str = DEFAULT_NERDCTL_BIN, namespace: str = DEFAULT_NERDCTL_NAMESPACE
) -> list[str]:
    return [nerdctl_bin, "--namespace", namespace]


def translate_container_config_to_nerdctl_args(
    container_config: Mapping[str, Any],
    *,
    name: str,
    runtime: str = DEFAULT_KATA_RUNTIME,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
    resolve_volume: Callable[[str], str] | None = None,
) -> list[str]:
    """
    Translate the Docker-API-style ``container_config`` dict assembled by
    :meth:`DockerKernelCreationContext.start_container` into a full ``nerdctl
    run -d`` argv list.

    :param container_config: the merged container config (Image/Cmd/Env/Mounts/
        Labels/HostConfig.PortBindings/...).
    :param name: container name (``kernel.<image>.<kernel_id>``).
    :param runtime: containerd runtime handler (Kata).
    :param resolve_volume: callback mapping a Docker named-volume to its host
        path. Required if any ``MountTypes.VOLUME`` mounts are present (the
        krunner ``/opt/backend.ai`` volume). Kata/nerdctl cannot share a Docker
        named volume into the guest, so we resolve it to a host path and
        bind-mount instead (see §6b.3 "the one exception").
    """
    args: list[str] = [*_nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace)]
    args += ["run", "-d", "--runtime", runtime, "--name", name]

    if container_config.get("Tty"):
        args.append("-t")
    # NOTE: Docker accepts OpenStdin (`-i`) together with detached (`-d`), but
    # nerdctl rejects `-i -d` ("cannot be specified together"). The kernel runs
    # detached and communicates over ZMQ repl ports (not container stdin), so we
    # intentionally do NOT translate OpenStdin to `-i` (verified on kata-lab-150).
    if stop_signal := container_config.get("StopSignal"):
        args += ["--stop-signal", str(stop_signal)]
    if working_dir := container_config.get("WorkingDir"):
        args += ["-w", str(working_dir)]
    if hostname := container_config.get("Hostname"):
        args += ["--hostname", str(hostname)]

    # Entrypoint: Docker EntryPoint is a list; nerdctl --entrypoint takes one
    # string (the binary). Any extra elements are prepended to the command args.
    entrypoint = container_config.get("EntryPoint") or container_config.get("Entrypoint")
    extra_entry_args: list[str] = []
    if entrypoint:
        entry_list = list(entrypoint)
        args += ["--entrypoint", entry_list[0]]
        extra_entry_args = entry_list[1:]

    for env in container_config.get("Env", []) or []:
        args += ["-e", str(env)]

    for label_key, label_val in (container_config.get("Labels") or {}).items():
        args += ["--label", f"{label_key}={label_val}"]

    host_config: Mapping[str, Any] = container_config.get("HostConfig", {}) or {}

    if host_config.get("Init"):
        args.append("--init")
    if host_config.get("Privileged"):
        args.append("--privileged")

    for cap in host_config.get("CapAdd", []) or []:
        args += ["--cap-add", str(cap)]

    for ulimit in host_config.get("Ulimits", []) or []:
        soft = ulimit["Soft"]
        hard = ulimit["Hard"]
        args += ["--ulimit", f"{ulimit['Name']}={soft}:{hard}"]

    if (shm_size := host_config.get("ShmSize")) is not None:
        args += ["--shm-size", str(shm_size)]

    for sec_opt in host_config.get("SecurityOpt", []) or []:
        args += ["--security-opt", str(sec_opt)]

    # Port publishing — the load-bearing bit for the 127.0.0.1 repl assumption.
    # PortBindings: {"2000/tcp": [{"HostPort": "X", "HostIp": "127.0.0.1"}]}
    for port_proto, bindings in (host_config.get("PortBindings") or {}).items():
        container_port, _, proto = port_proto.partition("/")
        proto = proto or "tcp"
        for binding in bindings or []:
            host_port = binding["HostPort"]
            host_ip = binding.get("HostIp") or "0.0.0.0"
            args += ["-p", f"{host_ip}:{host_port}:{container_port}/{proto}"]

    # Mounts (krunner bind mounts, vfolders, scratch, accelerator mounts).
    for mount in host_config.get("Mounts", []) or []:
        args += ["--mount", _translate_mount(mount, resolve_volume=resolve_volume)]
    # Legacy "Binds" entries ("src:dst:mode"), in case any plugin emits them.
    for bind in host_config.get("Binds", []) or []:
        args += ["-v", str(bind)]

    for key in host_config:
        if key in _UNTRANSLATED_HOSTCONFIG_KEYS:
            log.debug("kata: ignoring untranslated HostConfig.{} for {}", key, name)

    args.append(str(container_config["Image"]))
    args += [str(a) for a in extra_entry_args]
    args += [str(a) for a in (container_config.get("Cmd") or [])]
    return args


def _translate_mount(
    mount: Mapping[str, Any],
    *,
    resolve_volume: Callable[[str], str] | None,
) -> str:
    mount_type = mount.get("Type", "bind")
    target = mount["Target"]
    source = mount["Source"]
    read_only = bool(mount.get("ReadOnly", False))

    if mount_type == "volume":
        # Kata/nerdctl cannot transparently share a Docker named volume into the
        # microVM. Resolve it to a host path and bind-mount it instead.
        if resolve_volume is None:
            raise KataVolumeResolutionError(
                f"named volume {source!r} requires a volume resolver but none was provided"
            )
        source = resolve_volume(str(source))
        mount_type = "bind"

    parts = [f"type={mount_type}", f"source={source}", f"target={target}"]
    if read_only:
        parts.append("readonly")
    return ",".join(parts)


async def _run(
    args: Sequence[str],
    *,
    input_bytes: bytes | None = None,
    timeout_sec: float | None = None,
) -> tuple[int, bytes, bytes]:
    log.trace("kata: exec {}", " ".join(shlex.quote(a) for a in args))
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE if input_bytes is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=input_bytes), timeout=timeout_sec
        )
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode or 0, stdout, stderr


async def nerdctl_run(args: Sequence[str], *, timeout_sec: float = 300.0) -> str:
    """Run a translated ``nerdctl run -d ...`` argv and return the container ID."""
    rc, stdout, stderr = await _run(args, timeout_sec=timeout_sec)
    if rc != 0:
        raise NerdctlError(
            f"nerdctl run failed (rc={rc}): {stderr.decode(errors='replace').strip()}"
        )
    return stdout.decode().strip()


async def nerdctl_stop(
    container_id: str,
    *,
    timeout_secs: int = 10,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
) -> None:
    args = [
        *_nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace),
        "stop",
        "-t",
        str(timeout_secs),
        container_id,
    ]
    rc, _, stderr = await _run(args, timeout_sec=timeout_secs + 30)
    if rc != 0:
        msg = stderr.decode(errors="replace")
        if "no such container" in msg.lower() or "not found" in msg.lower():
            log.warning("kata: stop: container {} already gone", container_id)
            return
        raise NerdctlError(f"nerdctl stop failed (rc={rc}): {msg.strip()}")


async def nerdctl_rm(
    container_id: str,
    *,
    force: bool = True,
    volumes: bool = True,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
) -> None:
    args = [*_nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace), "rm"]
    if force:
        args.append("-f")
    if volumes:
        args.append("-v")
    args.append(container_id)
    rc, _, stderr = await _run(args, timeout_sec=120.0)
    if rc != 0:
        msg = stderr.decode(errors="replace")
        if "no such container" in msg.lower() or "not found" in msg.lower():
            return
        raise NerdctlError(f"nerdctl rm failed (rc={rc}): {msg.strip()}")


async def nerdctl_exec(
    container_id: str,
    command: Sequence[str],
    *,
    user: str | None = None,
    input_bytes: bytes | None = None,
    timeout_sec: float = 60.0,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
) -> tuple[int, bytes, bytes]:
    # NOTE: plain exec (input_bytes=None) is reliable, but streaming bulk data via
    # ``input_bytes`` (``exec -i`` stdin) is NOT a safe transport on the Kata
    # runtime — live validation on kata-lab-150 (2026-06-21) saw it truncate
    # payloads above a few KiB and, with a ``tar`` reader, hang and poison the
    # container's exec channel. Use the rw virtio-fs scratch share for file
    # transfer (see KataKernel). ``input_bytes`` is kept only for short control
    # input; do not push large blobs through it.
    args = [*_nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace), "exec"]
    if input_bytes is not None:
        args.append("-i")  # keep stdin open so we can stream data into the guest
    if user is not None:
        args += ["-u", user]
    args.append(container_id)
    args += list(command)
    return await _run(args, input_bytes=input_bytes, timeout_sec=timeout_sec)


async def nerdctl_logs(
    container_id: str,
    *,
    timeout_sec: float = 60.0,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
) -> str:
    args = [
        *_nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace),
        "logs",
        container_id,
    ]
    rc, stdout, stderr = await _run(args, timeout_sec=timeout_sec)
    if rc != 0:
        raise NerdctlError(
            f"nerdctl logs failed (rc={rc}): {stderr.decode(errors='replace').strip()}"
        )
    # nerdctl interleaves stdout/stderr of the container into both streams here;
    # return both for log collection.
    return stdout.decode(errors="replace") + stderr.decode(errors="replace")


async def nerdctl_list_running_kernel_ids(
    label_key: str,
    *,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
) -> set[str]:
    """Return the set of container IDs of running containers carrying ``label_key``."""
    args = [
        *_nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace),
        "ps",
        "--filter",
        f"label={label_key}",
        "--format",
        "{{.ID}}",
    ]
    rc, stdout, stderr = await _run(args, timeout_sec=30.0)
    if rc != 0:
        raise NerdctlError(
            f"nerdctl ps failed (rc={rc}): {stderr.decode(errors='replace').strip()}"
        )
    return {line.strip() for line in stdout.decode().splitlines() if line.strip()}


async def nerdctl_inspect_kernel_containers(
    label_key: str,
    *,
    nerdctl_bin: str = DEFAULT_NERDCTL_BIN,
    namespace: str = DEFAULT_NERDCTL_NAMESPACE,
) -> list[dict[str, Any]]:
    """Return the docker-compatible ``inspect`` records for every container (any
    state) carrying ``label_key`` in our namespace.

    Used by :meth:`KataAgent.enumerate_containers` to reconcile the kernel
    registry against containerd's namespace — DockerAgent's version queries the
    ``moby`` namespace, which never contains Kata kernels.
    """
    base = _nerdctl_base(nerdctl_bin=nerdctl_bin, namespace=namespace)
    ids_args = [*base, "ps", "-a", "--filter", f"label={label_key}", "--format", "{{.ID}}"]
    rc, stdout, stderr = await _run(ids_args, timeout_sec=30.0)
    if rc != 0:
        raise NerdctlError(
            f"nerdctl ps failed (rc={rc}): {stderr.decode(errors='replace').strip()}"
        )
    ids = [line.strip() for line in stdout.decode().splitlines() if line.strip()]
    if not ids:
        return []
    rc, stdout, stderr = await _run([*base, "inspect", *ids], timeout_sec=60.0)
    if rc != 0:
        raise NerdctlError(
            f"nerdctl inspect failed (rc={rc}): {stderr.decode(errors='replace').strip()}"
        )
    parsed = json.loads(stdout.decode() or "[]")
    return list(parsed)


async def resolve_docker_volume_path(volume_name: str, *, docker_bin: str = "docker") -> str:
    """
    Resolve a Docker *named* volume to its host mountpoint path.

    The krunner volume (``/opt/backend.ai``) is created by ``prepare_krunner_env``
    via dockerd, so we ask dockerd for its on-disk path and bind-mount that into
    the Kata guest (a Docker named volume cannot be shared into the microVM).
    """
    args = [docker_bin, "volume", "inspect", "--format", "{{.Mountpoint}}", volume_name]
    rc, stdout, stderr = await _run(args, timeout_sec=30.0)
    if rc != 0:
        raise KataVolumeResolutionError(
            f"could not resolve docker volume {volume_name!r} "
            f"(rc={rc}): {stderr.decode(errors='replace').strip()}"
        )
    path = stdout.decode().strip()
    if not path:
        raise KataVolumeResolutionError(f"docker volume {volume_name!r} resolved to an empty path")
    return path
