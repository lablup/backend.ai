import enum
import ipaddress
from dataclasses import dataclass

DEFAULT_IPV4_MASK_PREFIX = 24
DEFAULT_IPV6_MASK_PREFIX = 48

MAX_IPV4_PREFIX = 32
MAX_IPV6_PREFIX = 128


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

    The prefixes say how much of the address ``TRUNCATE`` leaves; how deep an
    address has to be cut before it counts as anonymous differs by jurisdiction,
    and an IPv6 prefix an ISP hands out whole is no anonymisation at all.

    Parsing runs in every mode: the address may come from a client-controlled
    ``X-Forwarded-For`` when no trusted proxy is configured, and an unparsable
    value is dropped rather than stored.
    """

    mode: ClientIPMaskingMode
    ipv4_prefix: int = DEFAULT_IPV4_MASK_PREFIX
    ipv6_prefix: int = DEFAULT_IPV6_MASK_PREFIX

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
        prefix = self.ipv4_prefix if address.version == 4 else self.ipv6_prefix
        network = ipaddress.ip_network(f"{address}/{prefix}", strict=False)
        return str(network.network_address)
