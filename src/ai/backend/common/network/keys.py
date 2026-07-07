"""Canonical etcd key layout for the BEP-1055 cluster-network control plane.

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
    "session_prefix",
    "session_meta_key",
    "members_prefix",
    "member_key",
    "endpoints_prefix",
    "endpoint_key",
    "session_ipam_key",
    "agent_caps_key",
    "agent_backend_key",
    "agent_vtep_key",
)


# --- per-session: network/session/{session_id}/... ---


def session_prefix(session_id: str) -> str:
    return f"network/session/{session_id}/"


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


def session_ipam_key(session_id: str, ip: str) -> str:
    return f"{session_prefix(session_id)}ipam/{ip}"


# --- per-agent: network/agent/{agent_id}/... ---


def agent_caps_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/caps"


def agent_backend_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/backend"


def agent_vtep_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/vtep"
