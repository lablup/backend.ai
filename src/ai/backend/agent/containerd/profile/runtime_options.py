"""Builders for the typed runtime options a profile can put in a LaunchPlan."""

from __future__ import annotations

from typing import Final

from ai.backend.agent.containerd._grpcapi.pkg.runtimeoptions.v1 import api_pb2
from ai.backend.agent.containerd.profile.base import RuntimeOptions

RUNTIME_OPTIONS_TYPE_URL: Final = "runtimeoptions.v1.Options"


def kata_config_path_options(path: str) -> RuntimeOptions:
    """Options that point the Kata shim at the config file `path` (containerd >= 1.7 shims)."""
    message = api_pb2.Options(config_path=path)
    return RuntimeOptions(
        type_url=RUNTIME_OPTIONS_TYPE_URL, value=message.SerializeToString(deterministic=True)
    )
