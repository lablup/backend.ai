"""Per-kernel preopen-port / service-port collision validator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, override

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionSpecContext,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)

_RESERVED_PORTS: frozenset[int] = frozenset({2000, 2001, 2200, 7681})


class ServicePortRule(SessionSpecValidatorRule):
    """Per-kernel preopen_ports must not collide with reserved or service ports."""

    @override
    def name(self) -> str:
        return "service_port"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        for idx, kernel in enumerate(spec.resource_spec.kernel_specs):
            preopen = set(kernel.preopen_ports)
            if not preopen:
                continue
            conflicts = preopen & _RESERVED_PORTS
            if conflicts:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{idx}] preopen_ports {sorted(conflicts)} "
                        f"collide with reserved ports ({sorted(_RESERVED_PORTS)})."
                    ),
                )
            image_info = context.global_info.image_infos.get(
                kernel.execution_spec.resource_input.image_id
            )
            if image_info is None:
                continue
            image_service_ports = self._image_service_ports(image_info.labels)
            overlap = preopen & image_service_ports
            if overlap:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"kernel_specs[{idx}] preopen_ports {sorted(overlap)} "
                        "collide with ports declared by the image's service "
                        "metadata."
                    ),
                )

    @staticmethod
    def _image_service_ports(image_labels: Mapping[str, Any]) -> frozenset[int]:
        raw = image_labels.get("ai.backend.service-ports") or ""
        ports: set[int] = set()
        for item in str(raw).split(","):
            for tok in item.strip().split(":"):
                tok = tok.strip()
                if tok.isdigit():
                    ports.add(int(tok))
        return frozenset(ports)
