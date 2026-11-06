from typing import Final

from ai.backend.common.types import AgentId

APPPROXY_ANYCAST_STREAM_KEY: Final[str] = "events-appproxy"
APPPROXY_BROADCAST_CHANNEL: Final[str] = "events_all-appproxy"


PERMIT_COOKIE_NAME: Final[str] = "appproxy_permit"

# aiohttp.hdrs only defines header names, not media types.
MEDIA_TYPE_JSON: Final[str] = "application/json"
MEDIA_TYPE_HTML: Final[str] = "text/html"

HOST_HEADER: Final[str] = "Host"
FORWARDED_HEADER: Final[str] = "Forwarded"
X_FORWARDED_FOR_HEADER: Final[str] = "X-Forwarded-For"
X_FORWARDED_HOST_HEADER: Final[str] = "X-Forwarded-Host"
X_FORWARDED_PORT_HEADER: Final[str] = "X-Forwarded-Port"
X_FORWARDED_PROTO_HEADER: Final[str] = "X-Forwarded-Proto"
X_RSTUDIO_PROTO_HEADER: Final[str] = "X-RStudio-Proto"
X_RSTUDIO_REQUEST_HEADER: Final[str] = "X-RStudio-Request"

ERROR_TEMPLATE_NAME: Final[str] = "error.jinja2"

AGENTID_COORDINATOR = AgentId("appproxy-coordinator")
AGENTID_WORKER = AgentId("appproxy-worker")
