from __future__ import annotations

import ipaddress
import re
from typing import Final

from ai.backend.appproxy.coordinator.errors.circuit import InvalidKernelHostError

_HOSTNAME_PATTERN: Final = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]{0,251}[A-Za-z0-9])?\.?")


def find_kernel_host_rejection_reason(kernel_host: str) -> str | None:
    """A hostname is judged by its name, because the proxy resolves it when it connects."""
    try:
        address = ipaddress.ip_address(kernel_host)
    except ValueError:
        if _HOSTNAME_PATTERN.fullmatch(kernel_host) is None:
            return f"kernel_host {kernel_host!r} is not a valid host"
        last_label = kernel_host.rstrip(".").lower().rsplit(".", maxsplit=1)[-1]
        # A resolver reads a numeric last label as an IPv4 address: 2852039166, 0xa9.0xfe.0xa9.0xfe.
        if last_label.isdigit() or last_label.startswith("0x"):
            return f"kernel_host {kernel_host!r} is not a valid host"
        return None
    if address.is_link_local:
        return f"kernel_host {kernel_host!r} is a link-local address"
    return None


def ensure_kernel_host_allowed(kernel_host: str) -> None:
    rejection_reason = find_kernel_host_rejection_reason(kernel_host)
    if rejection_reason is not None:
        raise InvalidKernelHostError(rejection_reason)
