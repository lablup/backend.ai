from __future__ import annotations

import itertools
from collections.abc import Iterator, Mapping, Sequence
from ipaddress import ip_network
from typing import Final, assert_never

from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.ingress.abc import IngressWriter
from ai.backend.appproxy.worker.types import (
    Circuit,
    InferenceAppInfo,
    InteractiveAppInfo,
    PortFrontendInfo,
    SubdomainFrontendInfo,
)
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKind,
    IngressID,
    IngressKey,
    IngressProtocol,
    IngressTarget,
    IngressTargetGroup,
    IngressTargetGroupID,
    IngressTargetID,
    IngressTokenAccess,
    IngressUserAccess,
    PortFrontend,
    WildcardFrontend,
)

_INGRESS_PROTOCOLS: Final[Mapping[ProxyProtocol, IngressProtocol]] = {
    ProxyProtocol.HTTP: IngressProtocol.HTTP,
    ProxyProtocol.PREOPEN: IngressProtocol.HTTP,
    ProxyProtocol.HTTP2: IngressProtocol.HTTP2,
    ProxyProtocol.GRPC: IngressProtocol.HTTP2,
    ProxyProtocol.TCP: IngressProtocol.TCP,
    ProxyProtocol.VNC: IngressProtocol.TCP,
    ProxyProtocol.RDP: IngressProtocol.TCP,
}


class CircuitIngressSync:
    """Writes the Ingress of each circuit the existing circuit events carry to the in-memory state.

    A circuit without routes has no target group to carry, so its Ingress is removed instead.
    """

    _writer: IngressWriter
    _authority: IngressAuthority
    _revisions: Iterator[int]

    def __init__(self, writer: IngressWriter, authority: IngressAuthority) -> None:
        self._writer = writer
        self._authority = authority
        # Circuits carry no revision; numbering them in arrival order keeps the last write winning.
        self._revisions = itertools.count()

    async def replace_all(self, circuits: Sequence[Circuit]) -> None:
        await self._writer.replace_all([
            self._ingress(circuit, circuit.route_info) for circuit in circuits if circuit.route_info
        ])

    async def apply(self, circuit: Circuit, routes: Sequence[RouteInfo]) -> None:
        if routes:
            await self._writer.apply([self._ingress(circuit, routes)])
        else:
            await self.remove([circuit])

    async def remove(self, circuits: Sequence[Circuit]) -> None:
        await self._writer.remove([
            IngressKey(authority=self._authority, frontend_key=self._frontend(circuit).key())
            for circuit in circuits
        ])

    def _ingress(self, circuit: Circuit, routes: Sequence[RouteInfo]) -> Ingress:
        frontend = self._frontend(circuit)
        allowed_client_ips = [ip_network(cidr) for cidr in circuit.ip_validator.ranges]
        # The worker authenticates http only, so other protocols stay public as they are today.
        if circuit.open_to_public or frontend.protocol != IngressProtocol.HTTP:
            access = IngressAccess(
                mode=IngressAccessMode.PUBLIC, allowed_client_ips=allowed_client_ips
            )
        else:
            match circuit.app_info:
                case InteractiveAppInfo(user_id=user_id):
                    access = IngressAccess(
                        mode=IngressAccessMode.USER,
                        allowed_client_ips=allowed_client_ips,
                        users=IngressUserAccess(allowed_user_ids=[user_id]),
                    )
                case InferenceAppInfo():
                    access = IngressAccess(
                        mode=IngressAccessMode.TOKEN,
                        allowed_client_ips=allowed_client_ips,
                        token=IngressTokenAccess(),
                    )
                case _:
                    assert_never(circuit.app_info)
        target_groups = []
        for route in routes:
            target_id = str(route.route_id or route.session_id)
            target_groups.append(
                IngressTargetGroup(
                    id=IngressTargetGroupID(target_id),
                    weight=round(route.traffic_ratio * 100),
                    targets=[
                        IngressTarget(
                            id=IngressTargetID(target_id),
                            host=route.current_kernel_host,
                            port=route.kernel_port,
                        )
                    ],
                )
            )
        return Ingress(
            id=IngressID(str(circuit.id)),
            authority=self._authority,
            revision=next(self._revisions),
            frontend=frontend,
            access=access,
            backend=IngressBackend(
                id=IngressBackendID(str(circuit.id)), target_groups=target_groups
            ),
        )

    def _frontend(self, circuit: Circuit) -> IngressFrontend:
        protocol = _INGRESS_PROTOCOLS[circuit.protocol]
        match circuit.frontend:
            case PortFrontendInfo(port=port):
                return IngressFrontend(
                    kind=IngressFrontendKind.PORT, protocol=protocol, port=PortFrontend(number=port)
                )
            case SubdomainFrontendInfo(subdomain=subdomain):
                return IngressFrontend(
                    kind=IngressFrontendKind.WILDCARD,
                    protocol=protocol,
                    wildcard=WildcardFrontend(subdomain=subdomain),
                )
