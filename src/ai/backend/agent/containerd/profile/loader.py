from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Final

from ai.backend.agent.containerd.profile.base import RuntimeProfile
from ai.backend.agent.containerd.profile.runc import RUNC_PROFILE_NAME, RuncProfile
from ai.backend.agent.errors.containerd import RuntimeProfileLoadError
from ai.backend.logging.structured import StructuredLogger
from ai.backend.plugin.entrypoint import scan_entrypoints

log = StructuredLogger(logging.getLogger(__spec__.name))

RUNTIME_PROFILE_ENTRYPOINT_GROUP: Final = "backendai_runtime_profile_v1"


def load_runtime_profile(name: str, options: Mapping[str, Mapping[str, Any]]) -> RuntimeProfile:
    """
    Return the built-in runc profile, or the entry point `name` called with its
    `options[name]` table; it must report the same name.
    """
    if name == RUNC_PROFILE_NAME:
        return RuncProfile()
    entrypoints = {ep.name: ep for ep in scan_entrypoints(RUNTIME_PROFILE_ENTRYPOINT_GROUP)}
    ep = entrypoints.get(name)
    if ep is None:
        raise RuntimeProfileLoadError(f"runtime profile {name!r} is not installed")
    try:
        profile: RuntimeProfile = ep.load()(options.get(name, {}))
        conforms = getattr(profile, "name", None) == name and callable(
            getattr(profile, "plan", None)
        )
    except Exception as e:  # profiles are third-party code
        raise RuntimeProfileLoadError(f"runtime profile {name!r} failed to load: {e}") from e
    if not conforms:
        raise RuntimeProfileLoadError(f"runtime profile {name!r} does not implement RuntimeProfile")
    log.info("runtime profile loaded", runtime_profile=name, entrypoint=ep.value)
    return profile
