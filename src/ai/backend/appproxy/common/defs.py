from typing import Final

from ai.backend.common.types import AgentId

APPPROXY_ANYCAST_STREAM_KEY: Final[str] = "events-appproxy"
APPPROXY_BROADCAST_CHANNEL: Final[str] = "events_all-appproxy"


PERMIT_COOKIE_NAME: Final[str] = "appproxy_permit"

# aiohttp.hdrs only defines header names, not media types.
MEDIA_TYPE_JSON: Final[str] = "application/json"
MEDIA_TYPE_HTML: Final[str] = "text/html"

ERROR_TEMPLATE_NAME: Final[str] = "error.jinja2"

AGENTID_COORDINATOR = AgentId("appproxy-coordinator")
AGENTID_WORKER = AgentId("appproxy-worker")

WORKER_SERVICE_GROUP: Final[str] = "appproxy-worker"
WORKER_AUTHORITY_LABEL: Final[str] = "authority"
WORKER_INGRESS_DELIVERY_MODE_LABEL: Final[str] = "ingress-delivery-mode"
WORKER_HOSTNAME_LABEL: Final[str] = "hostname"
WORKER_WILDCARD_DOMAIN_LABEL: Final[str] = "wildcard-domain"
WORKER_TLS_LISTEN_LABEL: Final[str] = "tls-listen"
