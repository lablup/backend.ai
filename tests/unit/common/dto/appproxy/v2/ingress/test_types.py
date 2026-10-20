from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressFrontend,
    IngressFrontendKey,
    IngressFrontendKind,
    IngressKey,
    IngressProtocol,
    IngressRedisKey,
    IngressUserAccess,
    PortFrontend,
    WildcardFrontend,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestIngressFrontend:
    def test_port_frontend_key_is_port_number(self) -> None:
        frontend = IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.TCP,
            port=PortFrontend(number=10205),
        )
        assert frontend.key() == "10205"

    def test_wildcard_frontend_key_is_subdomain(self) -> None:
        frontend = IngressFrontend(
            kind=IngressFrontendKind.WILDCARD,
            protocol=IngressProtocol.HTTP,
            wildcard=WildcardFrontend(subdomain="app-1"),
        )
        assert frontend.key() == "app-1"

    def test_port_kind_without_port_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressFrontend(
                kind=IngressFrontendKind.PORT,
                protocol=IngressProtocol.HTTP,
                wildcard=WildcardFrontend(subdomain="app-1"),
            )

    def test_port_kind_with_both_fields_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressFrontend(
                kind=IngressFrontendKind.PORT,
                protocol=IngressProtocol.HTTP,
                port=PortFrontend(number=10205),
                wildcard=WildcardFrontend(subdomain="app-1"),
            )

    def test_wildcard_kind_without_wildcard_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressFrontend(
                kind=IngressFrontendKind.WILDCARD,
                protocol=IngressProtocol.HTTP,
                port=PortFrontend(number=10205),
            )

    def test_wildcard_with_tcp_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressFrontend(
                kind=IngressFrontendKind.WILDCARD,
                protocol=IngressProtocol.TCP,
                wildcard=WildcardFrontend(subdomain="app-1"),
            )


class TestIngressAccess:
    def test_public_needs_nothing_else(self) -> None:
        access = IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[])
        assert access.users is None

    def test_user_without_users_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressAccess(mode=IngressAccessMode.USER, allowed_client_ips=[])

    def test_user_with_allowed_user_is_accepted(self) -> None:
        owner = uuid4()
        access = IngressAccess(
            mode=IngressAccessMode.USER,
            allowed_client_ips=[],
            users=IngressUserAccess(allowed_user_ids=[owner]),
        )
        assert access.users is not None
        assert access.users.allowed_user_ids == [owner]

    def test_token_without_token_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressAccess(mode=IngressAccessMode.TOKEN, allowed_client_ips=[])


class TestIngressUserAccess:
    def test_open_without_allowed_users_is_accepted(self) -> None:
        access = IngressUserAccess(open=True)
        assert access.allowed_user_ids == []

    def test_closed_without_allowed_users_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngressUserAccess(denied_user_ids=[uuid4()])


class TestIngress:
    def test_valid_payload_is_accepted(self, port_ingress_payload: dict[str, Any]) -> None:
        ingress = Ingress.model_validate(port_ingress_payload)
        assert ingress.frontend.key() == "10205"

    def test_negative_revision_is_rejected(self, port_ingress_payload: dict[str, Any]) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            Ingress.model_validate({**port_ingress_payload, "revision": -1})

    def test_empty_target_groups_is_rejected(self, port_ingress_payload: dict[str, Any]) -> None:
        payload = {**port_ingress_payload, "backend": {"id": "backend-1", "target_groups": []}}
        with pytest.raises(BackendAISchemaValidationFailed):
            Ingress.model_validate(payload)

    def test_negative_weight_is_rejected(self, port_ingress_payload: dict[str, Any]) -> None:
        payload = {
            **port_ingress_payload,
            "backend": {
                "id": "backend-1",
                "target_groups": [{"id": "group-1", "weight": -1, "targets": []}],
            },
        }
        with pytest.raises(BackendAISchemaValidationFailed):
            Ingress.model_validate(payload)

    def test_public_over_tcp_is_accepted(self, port_ingress_payload: dict[str, Any]) -> None:
        payload = {
            **port_ingress_payload,
            "frontend": {"kind": "port", "protocol": "tcp", "port": {"number": 10205}},
        }
        ingress = Ingress.model_validate(payload)
        assert ingress.frontend.protocol == IngressProtocol.TCP

    @pytest.mark.parametrize("protocol", ["tcp", "http2"])
    def test_user_access_over_non_http_is_rejected(
        self, port_ingress_payload: dict[str, Any], protocol: str
    ) -> None:
        payload = {
            **port_ingress_payload,
            "frontend": {"kind": "port", "protocol": protocol, "port": {"number": 10205}},
            "access": {
                "mode": "user",
                "allowed_client_ips": [],
                "users": {"allowed_user_ids": [str(uuid4())]},
            },
        }
        with pytest.raises(BackendAISchemaValidationFailed):
            Ingress.model_validate(payload)

    def test_key_pairs_authority_and_frontend_key(
        self, port_ingress_payload: dict[str, Any]
    ) -> None:
        ingress = Ingress.model_validate(port_ingress_payload)
        assert ingress.key() == IngressKey(
            authority=IngressAuthority("worker-1"), frontend_key=IngressFrontendKey("10205")
        )

    def test_unknown_field_is_ignored(self, port_ingress_payload: dict[str, Any]) -> None:
        ingress = Ingress.model_validate({**port_ingress_payload, "added_later": True})
        assert "added_later" not in ingress.model_dump()


class TestIngressRedisKey:
    def test_key_joins_prefix_authority_and_frontend_key(self) -> None:
        assert IngressRedisKey("appproxy:ingress").of(
            IngressAuthority("worker-1"), IngressFrontendKey("10205")
        ) == ("appproxy:ingress:worker-1:10205")

    def test_pattern_matches_the_authority(self) -> None:
        assert IngressRedisKey("appproxy:ingress").pattern(IngressAuthority("worker-1")) == (
            "appproxy:ingress:worker-1:*"
        )
