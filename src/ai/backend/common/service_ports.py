import re
from typing import (
    List,
    Sequence,
    Set,
    Type,
)

from .types import ServicePort, ServicePortProtocols

__all__ = (
    'parse_service_ports'
)

_rx_service_ports = re.compile(
    r'^(?P<name>[\w-]+):(?P<proto>\w+):(?P<ports>\[\d+(?:,\d+)*\]|\d+)(?:,|$)')


def parse_service_ports(s: str, exception_cls: Type[Exception] = None) -> Sequence[ServicePort]:
    items: List[ServicePort] = []
    if exception_cls is None:
        exception_cls = ValueError
    used_ports: Set[int] = set()
    while True:
        match = _rx_service_ports.search(s)
        if match:
            s = s[len(match.group(0)):]
            name = match.group('name')
            if not name:
                raise exception_cls('Service port name must be not empty.')
            protocol = match.group('proto')
            if protocol == 'pty':
                # unsupported, skip
                continue
            if protocol not in ('tcp', 'http', 'preopen'):
                raise exception_cls(f'Unsupported service port protocol: {protocol}')
            ports = tuple(map(int, match.group('ports').strip('[]').split(',')))
            for p in ports:
                if p in used_ports:
                    raise exception_cls(f'The port {p} is already used by another service port.')
                if p <= 1024:
                    raise exception_cls(f'The service port number {p} must be '
                                        f'larger than 1024 to run without the root privilege.')
                if p >= 65535:
                    raise exception_cls(f'The service port number {p} must be smaller than 65535.')
                if p in (2000, 2001, 2002, 2003, 2200, 7681):
                    raise exception_cls('The service ports 2000 to 2003, 2200 and 7681 '
                                        'are reserved for internal use.')
                used_ports.add(p)
            items.append({
                'name': name,
                'protocol': ServicePortProtocols(protocol),
                'container_ports': ports,
                'host_ports': (None,) * len(ports),
            })
        else:
            if len(s) > 0:
                raise exception_cls('Invalid format')
            break
    return items
