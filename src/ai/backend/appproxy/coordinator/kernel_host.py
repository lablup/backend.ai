from __future__ import annotations

import ipaddress
import re
from typing import Final

from ai.backend.appproxy.coordinator.config import KernelHostConfig
from ai.backend.appproxy.coordinator.errors.circuit import InvalidKernelHostError

_HOSTNAME_PATTERN: Final = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]{0,251}[A-Za-z0-9])?\.?")
_LOOPBACK_HOSTNAME_LABEL: Final = "localhost"


class KernelHostValidator:
    """Decides whether a kernel host may become a proxy target.

    A hostname is judged by its name, because the proxy resolves it when it connects.
    """

    _allow_loopback: bool

    def __init__(self, config: KernelHostConfig) -> None:
        self._allow_loopback = config.allow_loopback

    def ensure_allowed(self, kernel_host: str) -> None:
        rejection_reason = self.find_rejection_reason(kernel_host)
        if rejection_reason is not None:
            raise InvalidKernelHostError(rejection_reason)

    def find_rejection_reason(self, kernel_host: str) -> str | None:
        try:
            address = ipaddress.ip_address(kernel_host)
        except ValueError:
            return self._find_hostname_rejection_reason(kernel_host)
        return self._find_address_rejection_reason(kernel_host, address)

    def _find_address_rejection_reason(
        self, kernel_host: str, address: ipaddress.IPv4Address | ipaddress.IPv6Address
    ) -> str | None:
        target_address = address
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
            target_address = address.ipv4_mapped
        if target_address.is_link_local or target_address.is_multicast:
            return f"kernel_host {kernel_host!r} is a link-local or multicast address"
        if target_address.is_unspecified:
            return f"kernel_host {kernel_host!r} is an unspecified address"
        if target_address.is_loopback and not self._allow_loopback:
            return f"kernel_host {kernel_host!r} is a loopback address"
        return None

    def _find_hostname_rejection_reason(self, kernel_host: str) -> str | None:
        if _HOSTNAME_PATTERN.fullmatch(kernel_host) is None:
            return f"kernel_host {kernel_host!r} is not a valid host"
        last_label = kernel_host.rstrip(".").lower().rsplit(".", maxsplit=1)[-1]
        # A resolver reads a numeric last label as an IPv4 address: 127.1, 0x7f.0.0.1, 2130706433.
        if last_label.isdigit() or last_label.startswith("0x"):
            return f"kernel_host {kernel_host!r} is not a valid host"
        if last_label == _LOOPBACK_HOSTNAME_LABEL and not self._allow_loopback:
            return f"kernel_host {kernel_host!r} is a loopback address"
        return None
