"""
Unit tests for the (host-independent) container_config -> nerdctl argv
translation used by the KataAgent MVP. These do not require a Kata host.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.agent.errors.kata import KataVolumeResolutionError
from ai.backend.agent.kata.nerdctl import translate_container_config_to_nerdctl_args


def _adjacent(args: list[str], flag: str) -> list[str]:
    """Return every value that immediately follows an occurrence of ``flag``."""
    return [args[i + 1] for i, a in enumerate(args) if a == flag and i + 1 < len(args)]


def _minimal_config() -> dict[str, Any]:
    return {
        "Image": "cr.backend.ai/stable/python:3.11",
        "Tty": True,
        "OpenStdin": True,
        "StopSignal": "SIGINT",
        "EntryPoint": ["/opt/kernel/entrypoint.sh"],
        "Cmd": ["--debug"],
        "Env": ["LD_PRELOAD=/opt/kernel/libbaihook.so", "FOO=bar"],
        "WorkingDir": "/home/work",
        "Hostname": "main1",
        "Labels": {"ai.backend.kernel-id": "k-123"},
        "HostConfig": {
            "Init": True,
            "Privileged": False,
            "CapAdd": ["IPC_LOCK", "SYS_NICE"],
            "Ulimits": [{"Name": "nofile", "Soft": 1048576, "Hard": 1048576}],
            "PortBindings": {
                "2000/tcp": [{"HostPort": "30001", "HostIp": "127.0.0.1"}],
                "2001/tcp": [{"HostPort": "30002", "HostIp": "127.0.0.1"}],
                "8080/tcp": [{"HostPort": "30003", "HostIp": "0.0.0.0"}],
            },
            "Mounts": [
                {
                    "Target": "/opt/kernel/entrypoint.sh",
                    "Source": "/host/runner/entrypoint.sh",
                    "Type": "bind",
                    "ReadOnly": True,
                },
            ],
        },
    }


def test_basic_run_shape() -> None:
    args = translate_container_config_to_nerdctl_args(
        _minimal_config(), name="kernel.python.k-123", runtime="io.containerd.kata.v2"
    )
    assert args[0] == "nerdctl"
    assert "run" in args
    assert "-d" in args
    assert _adjacent(args, "--runtime") == ["io.containerd.kata.v2"]
    assert _adjacent(args, "--name") == ["kernel.python.k-123"]
    # image must appear, and after all flags
    assert "cr.backend.ai/stable/python:3.11" in args
    # cmd args come after the image
    img_idx = args.index("cr.backend.ai/stable/python:3.11")
    assert args[img_idx + 1] == "--debug"


def test_repl_ports_published_on_loopback() -> None:
    args = translate_container_config_to_nerdctl_args(_minimal_config(), name="k", runtime="rt")
    pubs = _adjacent(args, "-p")
    # The load-bearing 127.0.0.1 repl publishing must be preserved verbatim.
    assert "127.0.0.1:30001:2000/tcp" in pubs
    assert "127.0.0.1:30002:2001/tcp" in pubs
    assert "0.0.0.0:30003:8080/tcp" in pubs


def test_env_cap_ulimit_entrypoint() -> None:
    args = translate_container_config_to_nerdctl_args(_minimal_config(), name="k", runtime="rt")
    assert "LD_PRELOAD=/opt/kernel/libbaihook.so" in _adjacent(args, "-e")
    assert "FOO=bar" in _adjacent(args, "-e")
    assert _adjacent(args, "--entrypoint") == ["/opt/kernel/entrypoint.sh"]
    assert "IPC_LOCK" in _adjacent(args, "--cap-add")
    assert "nofile=1048576:1048576" in _adjacent(args, "--ulimit")
    assert "--init" in args
    assert "--privileged" not in args  # Privileged is False
    assert _adjacent(args, "--stop-signal") == ["SIGINT"]


def test_bind_mount_translation() -> None:
    args = translate_container_config_to_nerdctl_args(_minimal_config(), name="k", runtime="rt")
    mounts = _adjacent(args, "--mount")
    assert (
        "type=bind,source=/host/runner/entrypoint.sh,"
        "target=/opt/kernel/entrypoint.sh,readonly" in mounts
    )


def test_named_volume_resolved_to_host_bind() -> None:
    config = _minimal_config()
    config["HostConfig"]["Mounts"].append({
        "Target": "/opt/backend.ai",
        "Source": "backendai-krunner.v10.x86_64.ubuntu24.04",
        "Type": "volume",
        "ReadOnly": True,
    })
    args = translate_container_config_to_nerdctl_args(
        config,
        name="k",
        runtime="rt",
        resolve_volume=lambda name: f"/var/lib/docker/volumes/{name}/_data",
    )
    mounts = _adjacent(args, "--mount")
    # The named volume must become a host-path bind mount (Kata can't share a
    # Docker named volume into the guest).
    assert (
        "type=bind,source=/var/lib/docker/volumes/"
        "backendai-krunner.v10.x86_64.ubuntu24.04/_data,"
        "target=/opt/backend.ai,readonly" in mounts
    )


def test_named_volume_without_resolver_raises() -> None:
    config = _minimal_config()
    config["HostConfig"]["Mounts"].append({
        "Target": "/opt/backend.ai",
        "Source": "backendai-krunner.v10",
        "Type": "volume",
        "ReadOnly": True,
    })
    with pytest.raises(KataVolumeResolutionError):
        translate_container_config_to_nerdctl_args(config, name="k", runtime="rt")
