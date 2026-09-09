"""Canonical etcd key layout for the BEP-1078 cluster-network control plane.

Single source of truth for the etcd paths the manager (control plane) writes and the
agent (data plane) reads. Both sides MUST agree on these paths; defining them once here —
instead of in each component — keeps the contract from silently drifting.

Layout:
- ``network/session/{session_id}/`` — per-session state (manager + agents)
  - ``meta``               : SessionNetMeta (manager-written)
  - ``members/{agent_id}`` : per-node membership / VTEP (manager pre-seeds, agent self-writes)
  - ``endpoints/{cid}``    : per-container overlay IP/MAC (manager-written)
  - ``ipam/{ip}``          : per-session IP reservation (manager-internal)
- ``network/agent/{agent_id}/`` — per-agent advertisement (agent-written, manager reads)
  - ``caps`` / ``backend`` / ``vtep``
"""

from __future__ import annotations

__all__ = (
    "sessions_root",
    "session_prefix",
    "session_meta_key",
    "members_prefix",
    "member_key",
    "endpoints_prefix",
    "endpoint_key",
    "session_ipam_key",
    "agent_caps_key",
    "agent_backend_key",
    "agent_boot_key",
    "agent_ready_key",
    "agent_vtep_key",
)


# --- per-session: network/session/{session_id}/... ---


def sessions_root() -> str:
    """Where every session's subtree lives, for the reads that are not about one session --
    an agent asking which sessions still name it as a member."""
    return "network/session/"


def session_prefix(session_id: str) -> str:
    return f"{sessions_root()}{session_id}/"


def session_meta_key(session_id: str) -> str:
    return f"{session_prefix(session_id)}meta"


def members_prefix(session_id: str) -> str:
    return f"{session_prefix(session_id)}members/"


def member_key(session_id: str, agent_id: str) -> str:
    return f"{members_prefix(session_id)}{agent_id}"


def endpoints_prefix(session_id: str) -> str:
    return f"{session_prefix(session_id)}endpoints/"


def endpoint_key(session_id: str, container_id: str) -> str:
    return f"{endpoints_prefix(session_id)}{container_id}"


def session_ipam_prefix(session_id: str) -> str:
    return f"{session_prefix(session_id)}ipam/"


def session_ipam_key(session_id: str, ip: str) -> str:
    return f"{session_ipam_prefix(session_id)}{ip}"


# --- per-agent: network/agent/{agent_id}/... ---


def agent_caps_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/caps"


def agent_ready_key(agent_id: str) -> str:
    """Where an agent says WHAT it is currently able to serve, as a value that only changes when
    that changes.

    Separate from the capability record because that record is also a heartbeat: it carries the
    time it was written, and the agent rewrites it every minute to say it is still there. A
    condition on those bytes fails whenever a create straddles a refresh. A condition on this one
    fails when -- and only when -- the node stops being the node the placement was made on.
    """
    return f"network/agent/{agent_id}/ready"


def agent_boot_key(agent_id: str) -> str:
    """Where an agent records which run of itself is the current one.

    Written by the base agent at every start, before any backend-specific publishing. It is what
    lets the manager tell an advert this run made from one an earlier run of the same agent on the
    same runtime left behind -- which comparing runtime names cannot do.
    """
    return f"network/agent/{agent_id}/boot"


def agent_backend_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/backend"


def agent_vtep_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/vtep"
