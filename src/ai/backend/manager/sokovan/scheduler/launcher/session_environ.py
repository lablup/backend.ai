from __future__ import annotations

from collections.abc import Sequence
from itertools import groupby
from operator import attrgetter

from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironSourceKind,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.views.sokovan.lifecycle import KernelBindingData, SessionDataForStart

__all__ = (
    "build_session_environ",
    "count_cluster_replicas",
)


def build_session_environ(session: SessionDataForStart) -> dict[str, str]:
    """The session's own environ with the values of its system session environ rows.

    Among rows sharing a key the most specific scope wins. A ``system`` value overrides the
    session's own entry under that key, and an ``optional`` value yields to it.
    """
    injected: dict[str, SystemSessionEnvironData] = {}
    for row in sorted(session.system_environ, key=_specificity):
        injected[row.key] = row
    system: dict[str, str] = {}
    optional: dict[str, str] = {}
    for key, row in injected.items():
        value = _value_of(row.value_source, session)
        match row.value_source.kind():
            case SystemSessionEnvironSourceKind.SYSTEM:
                system[key] = value
            case SystemSessionEnvironSourceKind.OPTIONAL:
                optional[key] = value
    return {**optional, **session.environ, **system}


def count_cluster_replicas(kernels: Sequence[KernelBindingData]) -> dict[str, int]:
    cluster_role = attrgetter("cluster_role")
    return {
        role: len(list(group))
        for role, group in groupby(sorted(kernels, key=cluster_role), key=cluster_role)
    }


def _specificity(row: SystemSessionEnvironData) -> int:
    return SystemSessionEnvironScopeType.of_owner(row.scope_id).specificity()


def _value_of(source: SystemSessionEnvironValueSource, session: SessionDataForStart) -> str:
    match source:
        case SystemSessionEnvironValueSource.SESSION_ID:
            return str(session.session_id)
        case SystemSessionEnvironValueSource.SESSION_NAME:
            return session.name
        case SystemSessionEnvironValueSource.CLUSTER_SIZE:
            return str(len(session.kernels))
        case SystemSessionEnvironValueSource.CLUSTER_REPLICAS:
            replicas = count_cluster_replicas(session.kernels)
            return ",".join(f"{role}:{count}" for role, count in replicas.items())
        case SystemSessionEnvironValueSource.CLUSTER_HOSTS:
            return ",".join(
                k.cluster_hostname or f"{k.cluster_role}{k.cluster_idx}" for k in session.kernels
            )
        case SystemSessionEnvironValueSource.PREOPEN_PORTS:
            if not session.kernels:
                return ""
            return ",".join(str(port) for port in session.kernels[0].preopen_ports)
        case SystemSessionEnvironValueSource.USER_UUID:
            return str(session.user_uuid)
        case SystemSessionEnvironValueSource.USER_EMAIL:
            return session.user_email
        case SystemSessionEnvironValueSource.USER_NAME:
            return session.user_name
        case SystemSessionEnvironValueSource.ACCESS_KEY:
            return str(session.access_key)
