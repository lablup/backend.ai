import json
import logging
import os
import socket
import sys
from ipaddress import _BaseAddress as BaseIPAddress
from ipaddress import _BaseNetwork as BaseIPNetwork
from ipaddress import ip_address
from pathlib import Path, PosixPath
from typing import Awaitable, Callable, Iterable, Optional

import aiodns
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


def detect_cloud() -> Optional[str]:
    """
    Detect the cloud provider where I am running on.
    """
    # NOTE: Contributions are welcome!
    # Please add other cloud providers such as Rackspace, IBM BlueMix, etc.
    if sys.platform.startswith("linux"):
        # Google Cloud Platform or Amazon AWS (hvm)
        try:
            # AWS Nitro-based instances
            mb = Path("/sys/devices/virtual/dmi/id/board_vendor").read_text().lower()
            if "amazon" in mb:
                return "amazon"
        except IOError:
            pass
        try:
            bios = Path("/sys/devices/virtual/dmi/id/bios_version").read_text().lower()
            if "google" in bios:
                return "google"
            if "amazon" in bios:
                return "amazon"
        except IOError:
            pass
        # Microsoft Azure
        # https://gallery.technet.microsoft.com/scriptcenter/Detect-Windows-Azure-aed06d51
        # TODO: this only works with Debian/Ubuntu instances.
        # TODO: this does not work inside containers.
        try:
            dhcp = Path("/var/lib/dhcp/dhclient.eth0.leases").read_text()
            if "unknown-245" in dhcp:
                return "azure"
            # alternative method is to read /var/lib/waagent/GoalState.1.xml
            # but it requires sudo privilege.
        except IOError:
            pass
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
current_provider = detect_cloud()
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

    if current_provider == "amazon":
        # ref: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
        _metadata_prefix = "http://169.254.169.254/latest/meta-data/"
        _dynamic_prefix = "http://169.254.169.254/latest/dynamic/"

        async def _get_instance_id() -> str:
            return await curl(_metadata_prefix + "instance-id", lambda: f"i-{socket.gethostname()}")

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

    elif current_provider == "azure":
        # ref: https://docs.microsoft.com/azure/virtual-machines/virtual-machines-instancemetadataservice-overview
        _metadata_prefix = "http://169.254.169.254/metadata/instance"

        async def _get_instance_id() -> str:
            data = await curl(
                _metadata_prefix,
                None,
                params={"version": "2017-03-01"},
                headers={"Metadata": "true"},
            )
            if data is None:
                return f"i-{socket.gethostname()}"
            o = json.loads(data)
            return o["compute"]["vmId"]

        async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
            data = await curl(
                _metadata_prefix,
                None,
                params={"version": "2017-03-01"},
                headers={"Metadata": "true"},
            )
            if data is None:
                return "127.0.0.1"
            o = json.loads(data)
            return o["network"]["interface"][0]["ipv4"]["ipaddress"][0]["ipaddress"]

        async def _get_instance_type() -> str:
            data = await curl(
                _metadata_prefix,
                None,
                params={"version": "2017-03-01"},
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
                params={"version": "2017-03-01"},
                headers={"Metadata": "true"},
            )
            if data is None:
                return "azure/unknown"
            o = json.loads(data)
            region = o["compute"]["location"]
            return f"azure/{region}"

    elif current_provider == "google":
        # ref: https://cloud.google.com/compute/docs/storing-retrieving-metadata
        _metadata_prefix = "http://metadata.google.internal/computeMetadata/v1/"

        async def _get_instance_id() -> str:
            return await curl(
                _metadata_prefix + "instance/id",
                lambda: f"i-{socket.gethostname()}",
                headers={"Metadata-Flavor": "Google"},
            )

        async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
            return await curl(
                _metadata_prefix + "instance/network-interfaces/0/ip",
                "127.0.0.1",
                headers={"Metadata-Flavor": "Google"},
            )

        async def _get_instance_type() -> str:
            return await curl(
                _metadata_prefix + "instance/machine-type",
                "unknown",
                headers={"Metadata-Flavor": "Google"},
            )

        async def _get_instance_region() -> str:
            zone = await curl(
                _metadata_prefix + "instance/zone", "unknown", headers={"Metadata-Flavor": "Google"}
            )
            region = zone.rsplit("-", 1)[0]
            return f"google/{region}"

    else:
        _metadata_prefix = None

        async def _get_instance_id() -> str:
            return f"i-{socket.gethostname()}"

        async def _get_instance_ip(subnet_hint: Optional[BaseIPNetwork] = None) -> str:
            if subnet_hint is not None and subnet_hint.prefixlen > 0:
                local_ipaddrs = [*fetch_local_ipaddrs(subnet_hint)]
                if local_ipaddrs:
                    return str(local_ipaddrs[0])
                raise RuntimeError("Could not find my IP address bound to subnet {}", subnet_hint)
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
