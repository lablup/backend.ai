from __future__ import annotations

import ipaddress
import re
from typing import Annotated, Final

from pydantic import AfterValidator

_HOSTNAME_PATTERN: Final = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]{0,251}[A-Za-z0-9])?\.?")


def _validate_kernel_host(kernel_host: str) -> str:
    """A hostname is judged by its name, because the proxy resolves it when it connects."""
    address: ipaddress.IPv4Address | ipaddress.IPv6Address | None
    try:
        address = ipaddress.ip_address(kernel_host)
    except ValueError:
        address = None
    if address is not None:
        if address.is_link_local:
            raise ValueError(f"kernel host {kernel_host!r} is a link-local address")
        return kernel_host
    if _HOSTNAME_PATTERN.fullmatch(kernel_host) is None:
        raise ValueError(f"kernel host {kernel_host!r} is not a valid host")
    last_label = kernel_host.rstrip(".").lower().rsplit(".", maxsplit=1)[-1]
    # A resolver reads a numeric last label as an IPv4 address: 2852039166, 0xa9.0xfe.0xa9.0xfe.
    if last_label.isdigit() or last_label.startswith("0x"):
        raise ValueError(f"kernel host {kernel_host!r} is not a valid host")
    return kernel_host


KernelHost = Annotated[str, AfterValidator(_validate_kernel_host)]
