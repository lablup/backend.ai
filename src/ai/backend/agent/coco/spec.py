from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

IMAGE_NAME_ANNOTATION = "io.kubernetes.cri.image-name"
GUEST_MEMORY_ANNOTATION = "io.katacontainers.config.hypervisor.default_memory"
GUEST_VCPUS_ANNOTATION = "io.katacontainers.config.hypervisor.default_vcpus"
GUEST_ENTRYPOINT = "/opt/kernel/bai-cc-entrypoint"
GUEST_MOUNT_CAPABILITY = "SYS_ADMIN"


@dataclass(frozen=True)
class MountSpec:
    source: Path
    target: Path
    read_only: bool


@dataclass(frozen=True)
class ContainerSpec:
    name: str
    image: str
    hostname: str
    command: Sequence[str]
    netns_path: Path
    runtime: str
    memory_bytes: int
    cpuset: str
    dns_servers: Sequence[str]
    entrypoint: str = ""
    workdir: str = ""
    user: str = ""
    env: Mapping[str, str] = field(default_factory=dict)
    labels: Mapping[str, str] = field(default_factory=dict)
    annotations: Mapping[str, str] = field(default_factory=dict)
    devices: Sequence[Path] = field(default_factory=list)
    block_devices: Sequence[tuple[Path, Path]] = field(default_factory=list)
    mounts: Sequence[MountSpec] = field(default_factory=list)

    def to_args(self) -> list[str]:
        args = [
            "--name",
            self.name,
            "--runtime",
            self.runtime,
            "--net",
            f"ns:{self.netns_path}",
            "--hostname",
            self.hostname,
            "--pull",
            "never",
            "--stop-signal",
            "SIGINT",
            "--cap-add",
            GUEST_MOUNT_CAPABILITY,
        ]
        if self.entrypoint:
            args += ["--entrypoint", self.entrypoint]
        if self.workdir:
            args += ["--workdir", self.workdir]
        if self.user:
            args += ["--user", self.user]
        if self.memory_bytes > 0:
            args += ["--memory", str(self.memory_bytes)]
        if self.cpuset:
            args += ["--cpuset-cpus", self.cpuset]
        for server in self.dns_servers:
            args += ["--dns", server]
        for key, value in self.env.items():
            args += ["--env", f"{key}={value}"]
        for key, value in self.labels.items():
            args += ["--label", f"{key}={value}"]
        for key, value in self.annotations.items():
            args += ["--annotation", f"{key}={value}"]
        for device in self.devices:
            args += ["--device", str(device)]
        for host_device, guest_device in self.block_devices:
            args += ["--device", f"{host_device}:{guest_device}"]
        for mount in self.mounts:
            options = ["type=bind", f"src={mount.source}", f"dst={mount.target}"]
            if mount.read_only:
                options.append("readonly")
            args += ["--mount", ",".join(options)]
        args.append(self.image)
        args += list(self.command)
        return args


def build_annotations(
    blob_annotation_key: str,
    blob_value: str,
    image_canonical: str,
    guest_base_memory: int,
    guest_vcpus: int,
) -> dict[str, str]:
    return {
        blob_annotation_key: blob_value,
        IMAGE_NAME_ANNOTATION: image_canonical,
        GUEST_MEMORY_ANNOTATION: str(guest_base_memory >> 20),
        GUEST_VCPUS_ANNOTATION: str(guest_vcpus),
    }
