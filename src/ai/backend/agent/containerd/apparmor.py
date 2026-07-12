"""AppArmor confinement for containerd kernels.

The Docker backend gets this for free: dockerd loads a `docker-default` profile into the kernel at
startup and applies it to every container it creates. containerd does no such thing — it loads no
profile and sets none — so a containerd kernel runs completely unconfined, which is strictly weaker
isolation than the same kernel gets under Docker. Nothing announces that.

So we do what dockerd does: load an equivalent profile ourselves and name it in the OCI spec. The
policy below is the moby `docker-default` template, which is what these images already run under.
It blocks the writes that let a container reach out of itself — /proc outside its own pids,
/proc/sys except kernel/shm*, sysrq-trigger, kcore, /sys outside cgroups, firmware, securityfs —
and denies mount() outright (runc has already set up the container's mounts by the time the profile
applies, so this costs the workload nothing).

Loading a profile needs privilege (apparmor_parser talks to securityfs). An agent that cannot do it
says so loudly and runs unconfined, exactly as before this existed — refusing to start a kernel
would be a worse trade, and plenty of hosts run SELinux or no LSM at all.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

PROFILE_NAME = "backendai-default"

_APPARMOR_ENABLED_PATH = Path("/sys/module/apparmor/parameters/enabled")

# The moby docker-default policy, renamed. Kept verbatim in shape so it stays diffable against
# upstream: the peer names in the signal/ptrace rules must match the profile name, which is why
# they are interpolated rather than hard-coded.
_PROFILE_TEMPLATE = """
#include <tunables/global>

profile {name} flags=(attach_disconnected,mediate_deleted) {{
  #include <abstractions/base>

  network,
  capability,
  file,
  umount,

  # A privileged host process may signal a container process; container processes may signal
  # each other. Nothing else may signal in.
  signal (receive) peer=unconfined,
  signal (send,receive) peer={name},

  deny @{{PROC}}/* w,
  deny @{{PROC}}/{{[^1-9],[^1-9][^0-9],[^1-9s][^0-9y][^0-9s],[^1-9][^0-9][^0-9][^0-9]*}}/** w,
  deny @{{PROC}}/sys/[^k]** w,
  deny @{{PROC}}/sys/kernel/{{?,??,[^s][^h][^m]**}} w,
  deny @{{PROC}}/sysrq-trigger rwklx,
  deny @{{PROC}}/kcore rwklx,

  deny mount,

  deny /sys/[^f]*/** wklx,
  deny /sys/f[^s]*/** wklx,
  deny /sys/fs/[^c]*/** wklx,
  deny /sys/fs/c[^g]*/** wklx,
  deny /sys/fs/cg[^r]*/** wklx,
  deny /sys/firmware/** rwklx,
  deny /sys/kernel/security/** rwklx,

  # Keep `ps` inside the container from drowning in denials.
  ptrace (trace,read,tracedby,readby) peer={name},
}}
"""


def render_profile(name: str = PROFILE_NAME) -> str:
    return _PROFILE_TEMPLATE.format(name=name)


def is_apparmor_available() -> bool:
    """True if this host has AppArmor enabled and the tool to load a profile with."""
    try:
        if _APPARMOR_ENABLED_PATH.read_text().strip() not in ("Y", "1"):
            return False
    except OSError:
        return False
    return shutil.which("apparmor_parser") is not None


async def ensure_profile_loaded(name: str = PROFILE_NAME) -> str | None:
    """Load (or replace) our profile in the kernel and return its name, or None if we cannot.

    Idempotent: `apparmor_parser -r` replaces an existing profile of the same name, so an agent
    restart re-asserts the policy rather than failing on a leftover.
    """
    if not is_apparmor_available():
        log.info(
            "AppArmor is not available on this host; containers will run unconfined"
            " (the Docker backend would confine them with its docker-default profile)"
        )
        return None

    def _load() -> str | None:
        with tempfile.NamedTemporaryFile("w", suffix=".apparmor", delete=False) as f:
            f.write(render_profile(name))
            profile_path = f.name
        try:
            proc = subprocess.run(
                ["apparmor_parser", "-Kr", profile_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                log.warning(
                    "could not load the '{}' AppArmor profile ({}); containers will run"
                    " unconfined. Loading a profile needs privilege — run the agent as root, or"
                    " preload the profile out of band.",
                    name,
                    proc.stderr.strip() or f"exit {proc.returncode}",
                )
                return None
            return name
        finally:
            Path(profile_path).unlink(missing_ok=True)

    return await asyncio.to_thread(_load)
