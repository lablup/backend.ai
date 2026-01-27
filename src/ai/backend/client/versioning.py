from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .func.session import ComputeSession


naming_profile = {
    "path": ("kernel", "session"),
    "session_events_path": ("/stream/kernel/_/events", "/events/session"),
    "name_arg": ("clientSessionToken", "name"),
    "event_name_arg": ("sessionId", "name"),
    "name_gql_field": ("sess_id", "name"),
    "type_gql_field": ("sess_type", "type"),
}


def get_naming(api_version: tuple[int, str], key: str) -> str:
    if api_version[0] <= 4:
        return naming_profile[key][0]
    return naming_profile[key][1]


def get_id_or_name(api_version: tuple[int, str], obj: ComputeSession) -> str:
    if api_version[0] <= 4:
        if obj.name is None:
            raise ValueError("Session name is required for API version <= 4")
        return obj.name
    if obj.id:
        return str(obj.id)
    if obj.name is None:
        raise ValueError("Session must have either id or name")
    return obj.name


def apply_version_aware_fields(
    api_session,
    fields: Sequence[tuple[str, Callable | str]],
) -> Sequence[tuple[str, str]]:
    version_aware_fields = []
    for f in fields:
        if callable(f[1]):
            version_aware_fields.append((f[0], f[1](api_session)))
        else:
            version_aware_fields.append((f[0], f[1]))
    return version_aware_fields
