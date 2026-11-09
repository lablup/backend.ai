"""Builders for typed runtime options messages."""

from __future__ import annotations

from typing import Final

from ai.backend.agent.containerd._grpcapi.pkg.runtimeoptions.v1 import api_pb2
from ai.backend.agent.containerd.rpc.types import RuntimeOptions

RUNTIME_OPTIONS_TYPE_URL: Final = "runtimeoptions.v1.Options"


def config_path_options(path: str) -> RuntimeOptions:
    """Options that point a shim (e.g. Kata, containerd >= 1.7) at the config file `path`."""
    message = api_pb2.Options(config_path=path)
    return RuntimeOptions(
        type_url=RUNTIME_OPTIONS_TYPE_URL, value=message.SerializeToString(deterministic=True)
    )
