import enum
import ipaddress
from dataclasses import dataclass

_IPV4_MASK_PREFIX = 24
_IPV6_MASK_PREFIX = 48


class ClientIPMaskingTarget(enum.StrEnum):
    """Which recorded client IP a policy row governs.

    ``DEFAULT`` is the fallback the other targets inherit.
    """

    DEFAULT = "default"
    LOGIN_HISTORY = "login_history"
    AUDIT_LOGS = "audit_logs"


class ClientIPMaskingMode(enum.StrEnum):
    NONE = "none"
    TRUNCATE = "truncate"
    DROP = "drop"


@dataclass(frozen=True)
class ClientIPMasker:
    """Turns a raw client IP into the value a record keeps.

    Parsing runs in every mode: the address may come from a client-controlled
    ``X-Forwarded-For`` when no trusted proxy is configured, and an unparsable
    value is dropped rather than stored.
    """

    mode: ClientIPMaskingMode

    def mask(self, client_ip: str | None) -> str | None:
        if client_ip is None:
            return None
        try:
            address = ipaddress.ip_address(client_ip)
        except ValueError:
            return None
        match self.mode:
            case ClientIPMaskingMode.NONE:
                return str(address)
            case ClientIPMaskingMode.TRUNCATE:
                return self._truncate(address)
            case ClientIPMaskingMode.DROP:
                return None

    def _truncate(self, address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
        prefix = _IPV4_MASK_PREFIX if address.version == 4 else _IPV6_MASK_PREFIX
        network = ipaddress.ip_network(f"{address}/{prefix}", strict=False)
        return str(network.network_address)
