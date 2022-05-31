from __future__ import annotations

from typing import (
    Callable,
    Sequence,
    Tuple,
    Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from .func.session import ComputeSession


naming_profile = {
    'path': ('kernel', 'session'),
    'session_events_path': ('/stream/kernel/_/events', '/events/session'),
    'name_arg': ('clientSessionToken', 'name'),
    'event_name_arg': ('sessionId', 'name'),
    'name_gql_field': ('sess_id', 'name'),
    'type_gql_field': ('sess_type', 'type'),
}


def get_naming(api_version: Tuple[int, str], key: str) -> str:
    if api_version[0] <= 4:
        return naming_profile[key][0]
    return naming_profile[key][1]


def get_id_or_name(api_version: Tuple[int, str], obj: ComputeSession) -> str:
    if api_version[0] <= 4:
        assert obj.name is not None
        return obj.name
    if obj.id:
        return str(obj.id)
    else:
        assert obj.name is not None
        return obj.name


def apply_version_aware_fields(
    api_session,
    fields: Sequence[Tuple[str, Union[Callable, str]]],
) -> Sequence[Tuple[str, str]]:
    version_aware_fields = []
    for f in fields:
        if callable(f[1]):
            version_aware_fields.append((f[0], f[1](api_session)))
        else:
            version_aware_fields.append((f[0], f[1]))
    return version_aware_fields
