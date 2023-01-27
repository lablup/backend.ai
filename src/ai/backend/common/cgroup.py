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
