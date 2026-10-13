from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Final

from ai.backend.agent.errors.containerd import ProfileNotApplicable, RuntimeProfileLoadError
from ai.backend.common.types import SlotName
from ai.backend.logging.structured import StructuredLogger
from ai.backend.plugin.entrypoint import scan_entrypoints

from .base import RuntimeProfile
from .runc import RUNC_PROFILE_NAME

log = StructuredLogger(logging.getLogger(__spec__.name))

RUNTIME_PROFILE_ENTRYPOINT_GROUP: Final[str] = "backendai_runtime_profile_v1"


def load_runtime_profiles(
    names: Sequence[str],
    options: Mapping[str, Mapping[str, Any]],
) -> list[RuntimeProfile]:
    """
    Load the configured profiles in configured order.
    Each entry point resolves to a callable taking its `[containerd.profiles.<name>]` table.
    """
    if not names:
        return []
    if RUNC_PROFILE_NAME in names:
        raise RuntimeProfileLoadError(
            f"{RUNC_PROFILE_NAME!r} is built in and must not be listed in runtime-profiles"
        )
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise RuntimeProfileLoadError(f"runtime profile {name!r} is listed twice")
        seen.add(name)
    try:
        entrypoints = {ep.name: ep for ep in scan_entrypoints(RUNTIME_PROFILE_ENTRYPOINT_GROUP)}
    except RuntimeError as e:
        raise RuntimeProfileLoadError(str(e)) from e
    profiles: list[RuntimeProfile] = []
    for name in names:
        ep = entrypoints.get(name)
        if ep is None:
            raise RuntimeProfileLoadError(f"runtime profile {name!r} is not installed")
        try:
            profile = ep.load()(options.get(name, {}))
        except Exception as e:  # profiles are third-party code
            raise RuntimeProfileLoadError(f"runtime profile {name!r} failed to load: {e}") from e
        if not isinstance(profile, RuntimeProfile):
            raise RuntimeProfileLoadError(
                f"runtime profile {name!r} does not implement RuntimeProfile"
            )
        if profile.name != name:
            raise RuntimeProfileLoadError(
                f"runtime profile {name!r} reports the name {profile.name!r}"
            )
        log.info("runtime profile loaded", name=name, entrypoint=ep.value)
        profiles.append(profile)
    return profiles


def select_profile(
    configured: Sequence[RuntimeProfile],
    required_slots: frozenset[SlotName],
    slots: Mapping[SlotName, Decimal],
    *,
    builtin: RuntimeProfile,
) -> RuntimeProfile:
    """
    Return the first configured profile that accepts the slots.
    A kernel holding a required slot never falls back to the built-in profile.
    """
    for profile in configured:
        if profile.accepts(slots):
            return profile
    held = sorted(str(s) for s in required_slots if slots.get(s, Decimal(0)) > 0)
    if held:
        raise ProfileNotApplicable(f"no runtime profile accepts a kernel holding {', '.join(held)}")
    return builtin
