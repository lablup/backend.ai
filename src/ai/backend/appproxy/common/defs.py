from typing import Final

from ai.backend.common.types import AgentId

APPPROXY_ANYCAST_STREAM_KEY: Final[str] = "events-appproxy"
APPPROXY_BROADCAST_CHANNEL: Final[str] = "events_all-appproxy"


PERMIT_COOKIE_NAME: Final[str] = "appproxy_permit"

AGENTID_COORDINATOR = AgentId("appproxy-coordinator")
AGENTID_WORKER = AgentId("appproxy-worker")
