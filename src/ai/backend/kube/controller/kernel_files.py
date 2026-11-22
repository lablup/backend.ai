"""Files the kernel reads from `/home/config` and `/home/work`, carried in a Secret.

The krunner init container (`deploy/krunner/install.sh`) reads `manifest` and copies each key
to its place as the kernel user. The Agent writes the same files on the host.
"""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Final

from ai.backend.common.dotfile import (
    DotfilePath,
    InvalidDotfilePath,
    validate_dotfile_perm,
)
from ai.backend.kube.errors import InvalidSessionWorkloadError

MANIFEST_KEY: Final = "manifest"
AREAS: Final = frozenset({"config", "work"})
_RX_MODE: Final = re.compile(r"0?[0-7]{3}")
_RX_CONTROL: Final = re.compile(r"[\x00-\x1f\x7f-\x9f]")


@dataclass(frozen=True)
class KernelFile:
    area: str  # "config" → /home/config, "work" → /home/work
    path: str
    content: str
    mode: str = "0644"


@dataclass
class KernelFiles:
    files: list[KernelFile] = field(default_factory=list)

    def add(self, area: str, path: str, content: str, mode: str = "0644") -> None:
        _check_file(area, path, mode)
        self.files.append(KernelFile(area, path, content, mode))

    def to_secret_data(self) -> dict[str, str]:
        """Each manifest line is `<area> <key> <mode> <base64 of the path>`: no field can hold
        a space or a newline, whatever the path."""
        data: dict[str, str] = {}
        lines: list[str] = []
        for idx, f in enumerate(self.files):
            key = f"f{idx}"
            data[key] = f.content
            encoded = base64.b64encode(f.path.encode()).decode()
            lines.append(f"{f.area} {key} {f.mode} {encoded}")
        data[MANIFEST_KEY] = "".join(f"{line}\n" for line in lines)
        return data


def _check_file(area: str, path: str, mode: str) -> None:
    """A path relative to its area, without control characters or `..`, and an octal mode."""
    parts = PurePosixPath(path).parts
    if (
        area not in AREAS
        or not _RX_MODE.fullmatch(mode)
        or not parts
        or path.startswith("/")
        or ".." in parts
        or path != path.strip()
        or _RX_CONTROL.search(path)
    ):
        raise InvalidSessionWorkloadError(f"invalid kernel file {area}:{path!r} ({mode!r})")


def render_environ(environ: Mapping[str, str]) -> str:
    return "".join(f"{k}={v}\n" for k, v in environ.items())


def render_resource_txt(slots: Mapping[str, str], mounts: list[str]) -> str:
    return (
        "SCRATCH_SIZE=0m\n"
        f"MOUNTS={','.join(mounts)}\n"
        f"SLOTS={json.dumps(dict(slots), separators=(',', ':'))}\n"
        "UNIFIED_DEVICES=[]\n"
    )


def build_kernel_files(
    *,
    environ: Mapping[str, str],
    slots: Mapping[str, str],
    mounts: list[str],
    session_name: str,
    internal_data: Mapping[str, Any],
    cluster_ssh_keypair: Mapping[str, str] | None,
    bootstrap_script: str | None,
) -> KernelFiles:
    kf = KernelFiles()
    environ_txt = render_environ(environ)
    resource_txt = render_resource_txt(slots, mounts)
    kf.add("config", "environ.txt", environ_txt)
    kf.add("config", "environ_base.txt", environ_txt)
    kf.add("config", "resource.txt", resource_txt)
    kf.add("config", "resource_base.txt", resource_txt)
    kf.add("config", "session_name.txt", session_name)
    if docker_creds := internal_data.get("docker_credentials"):
        kf.add("config", "docker-creds.json", json.dumps(docker_creds), "0600")
    if cluster_ssh_keypair is not None:
        kf.add("config", "ssh/id_cluster", cluster_ssh_keypair["private_key"], "0600")
        kf.add("config", "ssh/id_cluster.pub", cluster_ssh_keypair["public_key"])
    if keypair := internal_data.get("ssh_keypair"):
        kf.add("work", ".ssh/authorized_keys", keypair["public_key"], "0600")
        kf.add("work", ".ssh/id_rsa", keypair["private_key"], "0600")
        kf.add("work", "id_container", keypair["private_key"], "0600")
    if bootstrap_script:
        kf.add("work", "bootstrap.sh", bootstrap_script, "0755")
    # Later dotfiles overwrite earlier ones, as on the Agent.
    for dotfile in internal_data.get("dotfiles", []):
        try:
            relative = DotfilePath(dotfile["path"]).relative
            perm = validate_dotfile_perm(dotfile["perm"])
        except (InvalidDotfilePath, KeyError, TypeError):
            continue
        content = dotfile["data"] if dotfile["data"].endswith("\n") else dotfile["data"] + "\n"
        kf.add("work", str(relative), content, perm)
    return kf
