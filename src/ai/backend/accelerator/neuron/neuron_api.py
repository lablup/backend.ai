"""
Thin, dependency-free wrappers around the AWS Neuron host interfaces.

Two sources of truth are used, and they are deliberately kept separate:

* ``neuron-ls --json-output`` -- the *static inventory*: which Neuron devices
  exist, how many NeuronCores each has, their PCI BDF, NUMA node and the
  device-level HBM capacity.  This is the only interface that reports capacity,
  so it drives device discovery.
* sysfs under ``/sys/devices/virtual/neuron_device`` -- the *runtime metrics*,
  which the driver models per NeuronCore.  This is world-readable and populated
  even with no workload attached, so it can be polled on every stat tick
  without running any vendor daemon.

``neuron-monitor`` is intentionally *not* used: it is a streaming collector
with a minimum 1-second (default 5-second) report cadence and no one-shot flag,
so consuming it would require running a persistent vendor daemon inside the
agent, which no other accelerator plugin does.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

__all__ = (
    "NEURON_LS_DEFAULT_PATH",
    "SYSFS_NEURON_DEVICE_ROOT",
    "NeuronAPI",
    "NeuronCoreStats",
    "NeuronDeviceInfo",
    "NeuronDriverUnavailableError",
    "NeuronToolError",
    "resolve_neuron_ls_path",
)

# The DLAMI ships the Neuron tools here but only *profile scripts* put this
# directory on PATH.  Under systemd or a container entrypoint the bare name
# `neuron-ls` is therefore `command not found` (exit 127), so the absolute path
# must be probed first and `shutil.which()` only used as a fallback.
NEURON_LS_DEFAULT_PATH: Final = "/opt/aws/neuron/bin/neuron-ls"

SYSFS_NEURON_DEVICE_ROOT: Final = Path("/sys/devices/virtual/neuron_device")

_NEURON_LS_TIMEOUT: Final = 10.0


class NeuronToolError(RuntimeError):
    """Raised when the Neuron host tooling cannot be used or its output cannot be trusted."""


class NeuronDriverUnavailableError(NeuronToolError):
    """
    Raised for the *degraded* host: `neuron-ls` is installed but the
    `aws-neuronx-dkms` driver is not loaded or exposes no device.  The tool then
    exits non-zero with an empty stdout and a single logfmt line on stderr.
    """


def resolve_neuron_ls_path(configured_path: str | None = None) -> str | None:
    """
    Locate an executable ``neuron-ls``, or return ``None`` if the tool is absent.

    Never raises: a missing CLI must disable the plugin rather than abort the
    agent's plugin loading.
    """
    candidates = [configured_path, NEURON_LS_DEFAULT_PATH]
    for candidate in candidates:
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which("neuron-ls")


@dataclass(frozen=True)
class NeuronDeviceInfo:
    """One entry of the ``neuron-ls --json-output`` top-level array."""

    neuron_device: int
    bdf: str
    cpu_affinity: str
    numa_node: int
    connected_to: tuple[int, ...] | None
    nc_count: int
    memory_size: int
    neuroncore_ids: tuple[int, ...]

    @property
    def memory_size_per_core(self) -> int:
        """
        Device HBM capacity attributable to a single NeuronCore.

        ``neuron-ls`` reports capacity only at the device level; the cores of one
        device share that HBM pool, so an even split is the best available
        approximation for per-core accounting.
        """
        if self.nc_count <= 0:
            return 0
        return self.memory_size // self.nc_count

    @classmethod
    def from_json_obj(cls, obj: Any) -> NeuronDeviceInfo:
        if not isinstance(obj, dict):
            raise NeuronToolError(
                f"unexpected neuron-ls entry: expected an object, got {type(obj).__name__}"
            )
        try:
            # `neuron_device` is an int, but `numa_node` is a *string* (e.g. "-1")
            # in the JSON output -- accept either shape for both.
            device_index = _coerce_int(obj["neuron_device"], "neuron_device")
            nc_count = _coerce_int(obj["nc_count"], "nc_count")
            memory_size = _coerce_int(obj["memory_size"], "memory_size")
            numa_node = _coerce_int(obj["numa_node"], "numa_node")
            bdf = str(obj["bdf"])
            cpu_affinity = str(obj.get("cpu_affinity", ""))
        except KeyError as e:
            raise NeuronToolError(f"missing key {e!s} in neuron-ls output") from e

        raw_core_ids = obj.get("neuroncore_ids")
        if isinstance(raw_core_ids, list) and raw_core_ids:
            core_ids = tuple(_coerce_int(v, "neuroncore_ids") for v in raw_core_ids)
        else:
            # Older tool versions omit the list; derive it from the device index.
            core_ids = tuple(range(device_index * nc_count, (device_index + 1) * nc_count))

        # `connected_to` is null on single-device instances and a list of peer
        # device indices on multi-device ones (trn1.32xlarge and friends).
        raw_connected = obj.get("connected_to")
        connected_to: tuple[int, ...] | None
        if raw_connected is None:
            connected_to = None
        elif isinstance(raw_connected, list):
            connected_to = tuple(_coerce_int(v, "connected_to") for v in raw_connected)
        else:
            connected_to = (_coerce_int(raw_connected, "connected_to"),)

        return cls(
            neuron_device=device_index,
            bdf=bdf,
            cpu_affinity=cpu_affinity,
            numa_node=numa_node,
            connected_to=connected_to,
            nc_count=nc_count,
            memory_size=memory_size,
            neuroncore_ids=core_ids,
        )


@dataclass(frozen=True)
class NeuronCoreStats:
    """Per-NeuronCore memory counters read from sysfs (all values in bytes)."""

    device_mem_present: int
    device_mem_peak: int
    host_mem_present: int
    host_mem_peak: int


def _coerce_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise NeuronToolError(f"unexpected boolean for {field!r} in neuron-ls output")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError as e:
            raise NeuronToolError(
                f"could not parse {field!r} from neuron-ls output: {value!r}"
            ) from e
    raise NeuronToolError(f"unexpected type for {field!r} in neuron-ls output: {value!r}")


def _read_sysfs_int(path: Path) -> int:
    """Read a single integer sysfs leaf, returning 0 when it is absent or empty."""
    try:
        raw = path.read_text().strip()
    except (OSError, ValueError):
        return 0
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        return 0


def _read_sysfs_text(path: Path) -> str | None:
    try:
        raw = path.read_text().strip()
    except OSError:
        return None
    return raw or None


class NeuronAPI:
    @classmethod
    async def list_devices(cls, exec_path: str) -> list[NeuronDeviceInfo]:
        """
        Run ``neuron-ls --json-output`` and parse its top-level array.

        :raises NeuronDriverUnavailableError: the tool ran but reported no device
            (driver missing/unloaded): non-zero exit with an empty stdout.
        :raises NeuronToolError: the tool could not be run or its output could not
            be parsed.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                exec_path,
                "--json-output",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as e:
            # Covers FileNotFoundError / PermissionError if the executable
            # disappeared between resolution and invocation.
            raise NeuronToolError(f"could not execute {exec_path}: {e}") from e

        try:
            async with asyncio.timeout(_NEURON_LS_TIMEOUT):
                out, err = await proc.communicate()
        except TimeoutError as e:
            proc.kill()
            await proc.wait()
            raise NeuronToolError(
                f"{exec_path} --json-output timed out after {_NEURON_LS_TIMEOUT}s"
            ) from e

        stdout = out.decode("utf-8", errors="replace").strip()
        stderr = err.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            if not stdout:
                # Degraded host: tool present, driver absent.  stdout is empty and
                # clean, with a single logfmt diagnostic line on stderr.
                raise NeuronDriverUnavailableError(
                    f"{exec_path} found no Neuron device (exit {proc.returncode}): {stderr}"
                )
            raise NeuronToolError(f"{exec_path} failed with exit {proc.returncode}: {stderr}")

        if not stdout:
            raise NeuronDriverUnavailableError(f"{exec_path} produced no output: {stderr}")

        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise NeuronToolError(f"could not parse the output of {exec_path}: {e}") from e

        if not isinstance(parsed, list):
            raise NeuronToolError(
                "unexpected neuron-ls output: expected a top-level array, got "
                f"{type(parsed).__name__}"
            )

        return [NeuronDeviceInfo.from_json_obj(entry) for entry in parsed]

    @classmethod
    def device_sysfs_path(cls, device_index: int) -> Path:
        return SYSFS_NEURON_DEVICE_ROOT / f"neuron{device_index}"

    @classmethod
    def core_sysfs_path(cls, device_index: int, core_index: int) -> Path:
        return cls.device_sysfs_path(device_index) / f"neuron_core{core_index}"

    @classmethod
    def read_device_serial(cls, device_index: int) -> str | None:
        return _read_sysfs_text(cls.device_sysfs_path(device_index) / "info" / "serial_number")

    @classmethod
    def read_device_model_name(cls, device_index: int) -> str | None:
        """e.g. "Trainium1" on trn1, from ``info/architecture/device_name``."""
        return _read_sysfs_text(
            cls.device_sysfs_path(device_index) / "info" / "architecture" / "device_name"
        )

    @classmethod
    def read_device_arch_type(cls, device_index: int) -> str | None:
        """e.g. "NDv2" on trn1, from ``info/architecture/arch_type``."""
        return _read_sysfs_text(
            cls.device_sysfs_path(device_index) / "info" / "architecture" / "arch_type"
        )

    @classmethod
    def read_core_stats(cls, device_index: int, core_index: int) -> NeuronCoreStats:
        """
        Read the per-core memory counters.

        Absent or unreadable leaves are reported as 0 rather than raising: this is
        called on every stat tick and a device that was hot-removed must not take
        the whole agent stat collection down.

        Note that the ``total`` leaves are *cumulative allocation* counters, not
        capacity -- they read 0 on an idle core.  Capacity therefore comes from
        ``neuron-ls``, not from here.
        """
        base = cls.core_sysfs_path(device_index, core_index) / "stats" / "memory_usage"
        return NeuronCoreStats(
            device_mem_present=_read_sysfs_int(base / "device_mem" / "present"),
            device_mem_peak=_read_sysfs_int(base / "device_mem" / "peak"),
            host_mem_present=_read_sysfs_int(base / "host_mem" / "present"),
            host_mem_peak=_read_sysfs_int(base / "host_mem" / "peak"),
        )

    @classmethod
    async def read_core_stats_batch(
        cls,
        core_coords: Sequence[tuple[int, int]],
    ) -> dict[tuple[int, int], NeuronCoreStats]:
        """
        Read the counters for many cores off the event loop in one executor hop.

        Each sysfs read is sub-millisecond, but a trn1.32xlarge has 32 cores, so
        the blocking reads are batched rather than issued from the event loop.
        """

        def _read_all() -> dict[tuple[int, int], NeuronCoreStats]:
            return {coord: cls.read_core_stats(*coord) for coord in core_coords}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _read_all)
