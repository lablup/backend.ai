import asyncio
import asyncio.staggered
import base64
import enum
import functools
import json
import logging
import os
import socket
import uuid
from ipaddress import _BaseAddress as BaseIPAddress
from ipaddress import _BaseNetwork as BaseIPNetwork
from ipaddress import ip_address
from pathlib import Path, PosixPath
from typing import Awaitable, Callable, Iterable, Optional

import aiodns
import aiohttp
import ifaddr
import psutil

from .utils import curl

__all__ = (
    "detect_cloud",
    "current_provider",
    "get_instance_id",
    "get_instance_ip",
    "get_instance_type",
    "get_instance_region",
    "get_root_fs_type",
    "get_wsl_version",
)

log = logging.getLogger(__spec__.name)


class CloudProvider(enum.StrEnum):
    AWS = "amazon"
    GCP = "google"
    AZURE = "azure"


def is_containerized() -> bool:
    """
    Check if I am running inside a Linux container.
    """
    try:
        cginfo = Path("/proc/self/cgroup").read_text()
        if "/docker/" in cginfo or "/lxc/" in cginfo:
            return True
        return False
    except IOError:
        return False


async def _detect_aws(session: aiohttp.ClientSession) -> CloudProvider:
    async with session.get(
        "http://169.254.169.254/latest/meta-data/",
    ):
        return CloudProvider.AWS


async def _detect_azure(session: aiohttp.ClientSession) -> CloudProvider:
    async with session.get(
        "http://169.254.169.254/metadata/instance/compute",
        params={"api-version": "2021-02-01"},
        headers={"Metadata": "true"},
    ):
        return CloudProvider.AZURE


async def _detect_gcp(session: aiohttp.ClientSession) -> CloudProvider:
    async with session.get(
        "http://169.254.169.254/computeMetadata/v1/instance/id",
        headers={"Metadata-Flavor": "Google"},
    ):
        return CloudProvider.GCP


async def detect_cloud() -> Optional[CloudProvider]:
    """
    Detect the cloud provider using asyncio.staggered_race()
    to get the fastest returning result from multiple metadata URL detectors.
    """
    async with aiohttp.ClientSession(
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(connect=0.3),
    ) as session:
        detection_tasks = [
            functools.partial(_detect_aws, session),
            functools.partial(_detect_azure, session),
            functools.partial(_detect_gcp, session),
        ]
        winner_value, winner_index, exceptions = await asyncio.staggered.staggered_race(
            detection_tasks,
            delay=0.001,
        )
        if winner_value is not None:
            return winner_value
    return None


def fetch_local_ipaddrs(cidr: BaseIPNetwork) -> Iterable[BaseIPAddress]:
    proto = socket.AF_INET if cidr.version == 4 else socket.AF_INET6
    for adapter in ifaddr.get_adapters():
        if not adapter.ips:
            continue
        for entry in adapter.ips:
            if entry.is_IPv4 and proto == socket.AF_INET:
                assert isinstance(entry.ip, str)
                addr = ip_address(entry.ip)
            elif entry.is_IPv6 and proto == socket.AF_INET6:
                assert isinstance(entry.ip, tuple)
                addr = ip_address(entry.ip[0])
            else:
                continue
            if addr in cidr:
                yield addr


def get_root_fs_type() -> tuple[PosixPath, str]:
    for partition in psutil.disk_partitions():
        if partition.mountpoint == "/":
            return PosixPath(partition.device), partition.fstype
    raise RuntimeError("Could not find the root filesystem from the mounts.")


def get_wsl_version() -> int:
    """
    Returns the current WSL version we are running on, and 0 if we are not on WSL.

    ref) https://github.com/snapcore/snapd/blob/3a88dc38ca122eba97192dba3aad30f3bd3e3081/release/release.go#L116-L172
    """
    if not Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists() and not Path("/run/WSL").exists():
        return 0
    try:
        _, root_fs_type = get_root_fs_type()
    except RuntimeError:
        return 2
    if root_fs_type in ("wslfs", "lxfs"):
        return 1
    return 2


# Detect upon module load.
try:
    try:
        loop = asyncio.get_running_loop()
        current_provider = loop.run_until_complete(detect_cloud())
    except RuntimeError:
        current_provider = asyncio.run(detect_cloud())
except Exception as e:
    log.warning(f"Failed to detect cloud provider: {e}")
    current_provider = None

if current_provider is None:
    log.info("Detected environment: on-premise setup")
    log.info("The agent node ID is set using the hostname.")
else:
    log.info(f"Detected environment: {current_provider} cloud")
    log.info("The agent node ID will follow the instance ID.")

_defined: bool = False
get_instance_id: Callable[[], Awaitable[str]]
get_instance_ip: Callable[[Optional[BaseIPNetwork]], Awaitable[str]]
get_instance_type: Callable[[], Awaitable[str]]
get_instance_region: Callable[[], Awaitable[str]]


def _define_functions():
    global _defined
    global get_instance_id
    global get_instance_ip
    global get_instance_type
    global get_instance_region
    if _defined:
        return

    match current_provider:
        case CloudProvider.AWS:
            # ref: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
            _metadata_prefix = "http://169.254.169.254/latest/meta-data/"
            _dynamic_prefix = "http://169.254.169.254/latest/dynamic/"

            async def _get_instance_id() -> str:
                return await curl(
                    _metadata_prefix + "instance-id", lambda: f"i-{socket.gethostname()}"
                )

            async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
                return await curl(_metadata_prefix + "local-ipv4", "127.0.0.1")

            async def _get_instance_type() -> str:
                return await curl(_metadata_prefix + "instance-type", "unknown")

            async def _get_instance_region() -> str:
                doc = await curl(_dynamic_prefix + "instance-identity/document", None)
                if doc is None:
                    return "amazon/unknown"
                region = json.loads(doc)["region"]
                return f"amazon/{region}"

        case CloudProvider.AZURE:
            # ref: https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-serviceb
            _metadata_prefix = "http://169.254.169.254/metadata/instance"

            async def _get_instance_id() -> str:
                data = await curl(
                    _metadata_prefix,
                    None,
                    params={"api-version": "2021-02-01"},
                    headers={"Metadata": "true"},
                )
                if data is None:
                    return f"i-{socket.gethostname()}"
                o = json.loads(data)
                vm_name = o["compute"]["name"]  # unique within the resource group
                vm_id = uuid.UUID(o["compute"]["vmId"])  # prevent conflicts across resource group
                vm_id_hash = base64.b32encode(vm_id.bytes[-5:]).decode().lower()
                return f"i-{vm_name}-{vm_id_hash}"

            async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
                data = await curl(
                    _metadata_prefix,
                    None,
                    params={"api-version": "2021-02-01"},
                    headers={"Metadata": "true"},
                )
                if data is None:
                    return "127.0.0.1"
                o = json.loads(data)
                return o["network"]["interface"][0]["ipv4"]["ipAddress"][0]["privateIpAddress"]

            async def _get_instance_type() -> str:
                data = await curl(
                    _metadata_prefix,
                    None,
                    params={"api-version": "2021-02-01"},
                    headers={"Metadata": "true"},
                )
                if data is None:
                    return "unknown"
                o = json.loads(data)
                return o["compute"]["vmSize"]

            async def _get_instance_region() -> str:
                data = await curl(
                    _metadata_prefix,
                    None,
                    params={"api-version": "2021-02-01"},
                    headers={"Metadata": "true"},
                )
                if data is None:
                    return "azure/unknown"
                o = json.loads(data)
                region = o["compute"]["location"]
                return f"azure/{region}"

        case CloudProvider.GCP:
            # ref: https://cloud.google.com/compute/docs/storing-retrieving-metadata
            _metadata_prefix = "http://169.254.169.254/computeMetadata/v1/"

            async def _get_instance_id() -> str:
                vm_id = await curl(
                    _metadata_prefix + "instance/id",
                    None,
                    headers={"Metadata-Flavor": "Google"},
                )
                if vm_id is None:
                    return f"i-{socket.gethostname()}"
                vm_name = await curl(
                    _metadata_prefix + "instance/name",
                    None,
                    headers={"Metadata-Flavor": "Google"},
                )
                vm_id_hash = base64.b32encode(int(vm_id).to_bytes(8, "big")[-5:]).decode().lower()
                return f"i-{vm_name}-{vm_id_hash}"

            async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
                return await curl(
                    _metadata_prefix + "instance/network-interfaces/0/ip",
                    "127.0.0.1",
                    headers={"Metadata-Flavor": "Google"},
                )

            async def _get_instance_type() -> str:
                value = await curl(
                    _metadata_prefix + "instance/machine-type",
                    "unknown",
                    headers={"Metadata-Flavor": "Google"},
                )
                return value.rsplit("/")[-1]

            async def _get_instance_region() -> str:
                value = await curl(
                    _metadata_prefix + "instance/zone",
                    "unknown",
                    headers={"Metadata-Flavor": "Google"},
                )
                region = value.rsplit("/")[-1]
                return f"google/{region}"

        case _:
            _metadata_prefix = None

            async def _get_instance_id() -> str:
                return f"i-{socket.gethostname()}"

            async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
                if subnet_hint is not None and subnet_hint.prefixlen > 0:
                    local_ipaddrs = [*fetch_local_ipaddrs(subnet_hint)]
                    if local_ipaddrs:
                        return str(local_ipaddrs[0])
                    raise RuntimeError(
                        f"Could not find my IP address bound to subnet {subnet_hint}"
                    )
                try:
                    myself = socket.gethostname()
                    resolver = aiodns.DNSResolver()
                    result = await resolver.gethostbyname(myself, socket.AF_INET)
                    return result.addresses[0]
                except aiodns.error.DNSError:
                    return "127.0.0.1"

            async def _get_instance_type() -> str:
                return "default"

            async def _get_instance_region() -> str:
                return os.environ.get("BACKEND_REGION", "local")

    get_instance_id = _get_instance_id
    get_instance_ip = _get_instance_ip
    get_instance_type = _get_instance_type
    get_instance_region = _get_instance_region
    _defined = True


_define_functions()
