# Relevant Linux kernel documentations
#
# For /proc filesystem, see
# https://docs.kernel.org/filesystems/proc.html
#
# For cgroup v1, see
# https://docs.kernel.org/admin-guide/cgroup-v1/
#
# For cgroup v2, see
# https://docs.kernel.org/admin-guide/cgroup-v2.html

from pathlib import Path
from typing import Optional

from .types import PID


def get_cgroup_mount_point(version: str, controller: str) -> Path:
    for line in Path("/proc/mounts").read_text().splitlines():
        device, mount_point, fstype, options, _ = line.split(" ", 4)
        match version:
            case "1":
                if fstype == "cgroup":
                    if controller in options.split(","):
                        return Path(mount_point)
            case "2":
                if fstype == "cgroup2":
                    return Path(mount_point)
    raise RuntimeError("could not find the cgroup mount point")


def get_cgroup_controller_id(controller: str) -> str:
    # example data
    # cpu <tab> 1 <tab> ...
    # cpuacct <tab> 1 <tab> ...
    for line in Path("/proc/cgroups").read_text().splitlines():
        name, id, _ = line.split("\t", 2)
        if name == controller:
            return id
    raise RuntimeError(f"could not find the cgroup controller {controller}")


def get_cgroup_of_pid(controller: str, pid: PID) -> str:
    # example data
    # 1:cpu,cpuacct:/<cgroup>
    controller_id = get_cgroup_controller_id(controller)
    for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines():
        id, name, cgroup = line.split(":", 2)
        if id == controller_id:
            return cgroup.removeprefix("/")
    raise RuntimeError(f"could not find the cgroup of PID {pid}")


def get_container_id_of_cgroup(cgroup: str) -> Optional[str]:
    # cgroupfs driver: docker/<id>
    cgroupfs_prefix = "docker/"
    if cgroup.startswith(cgroupfs_prefix):
        return cgroup.removeprefix(cgroupfs_prefix)
    # systemd driver: system.slice/docker-<id>.scope
    systemd_prefix = "system.slice/docker-"
    systemd_suffix = ".scope"
    if cgroup.startswith(systemd_prefix) and cgroup.endswith(systemd_suffix):
        return cgroup.removeprefix(systemd_prefix).removesuffix(systemd_suffix)
    return None
