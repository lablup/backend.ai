from typing import Final

from ai.backend.common.types import AgentId

APPPROXY_ANYCAST_STREAM_KEY: Final[str] = "events-appproxy"
APPPROXY_BROADCAST_CHANNEL: Final[str] = "events_all-appproxy"


PERMIT_COOKIE_NAME: Final[str] = "appproxy_permit"

# aiohttp.hdrs only defines header names, not media types.
MEDIA_TYPE_JSON: Final[str] = "application/json"
MEDIA_TYPE_HTML: Final[str] = "text/html"

AGENTID_COORDINATOR = AgentId("appproxy-coordinator")
AGENTID_WORKER = AgentId("appproxy-worker")
