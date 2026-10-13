"""The signed launch spec of a sealed kernel (ADR 0064): written by the agent, bound read-only at /run/bai/spec.jws."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, cast

from ai.backend.agent.errors.containerd import SealedSpecMissing
from ai.backend.common.types import KernelCreationConfig

SPEC_JWS_NAME: Final = "spec.jws"
SPEC_JWS_TARGET: Final = "/run/bai/spec.jws"
_SPEC_JWS_MODE: Final = 0o444


def spec_signature(config: KernelCreationConfig) -> str | None:
    """The spec signature of a sealed kernel; None for an unsealed one."""
    # KernelCreationConfig has no "confidential" key until #15585; then this is config.get(...).
    confidential = cast(Mapping[str, Any], config).get("confidential")
    if confidential is None:
        return None
    signature = confidential.get("signature")
    if not isinstance(signature, str) or not signature:
        raise SealedSpecMissing("the confidential kernel config has no signature")
    return signature


def write_spec_jws(path: Path, signature: str) -> None:
    path.write_bytes(signature.encode("ascii"))
    path.chmod(_SPEC_JWS_MODE)


def spec_jws_mount(source: Path) -> dict[str, Any]:
    # The option order matches SPEC_MOUNT of the ops policy; do not reorder.
    return {
        "destination": SPEC_JWS_TARGET,
        "type": "bind",
        "source": str(source),
        "options": ["rbind", "ro", "rprivate"],
    }
