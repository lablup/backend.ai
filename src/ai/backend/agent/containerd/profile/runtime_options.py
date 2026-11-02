"""Builders for the typed runtime options a profile can put in a LaunchPlan."""

from __future__ import annotations

from ai.backend.agent.containerd.rpc.runtime_options import config_path_options
from ai.backend.agent.containerd.rpc.types import RuntimeOptions


def kata_config_path_options(path: str) -> RuntimeOptions:
    """Options that point the Kata shim at the config file `path` (containerd >= 1.7 shims)."""
    return config_path_options(path)
