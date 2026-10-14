from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.dto.appproxy.v2.ingress.request import (
    IngressRemoveRequest,
    IngressReplaceRequest,
    IngressUpsertRequest,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestIngressUpsertRequest:
    def test_distinct_ingresses_are_accepted(
        self, port_ingress_payload: dict[str, Any], wildcard_ingress_payload: dict[str, Any]
    ) -> None:
        request = IngressUpsertRequest.model_validate({
            "ingresses": [port_ingress_payload, wildcard_ingress_payload]
        })
        assert len(request.ingresses) == 2

    def test_empty_ingresses_are_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressUpsertRequest.model_validate({"ingresses": []})

    def test_same_ingress_twice_is_rejected(self, port_ingress_payload: dict[str, Any]) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressUpsertRequest.model_validate({
                "ingresses": [port_ingress_payload, port_ingress_payload]
            })


class TestIngressRemoveRequest:
    def test_keys_are_accepted(self) -> None:
        request = IngressRemoveRequest.model_validate({
            "keys": [{"authority": "worker-1", "frontend_key": "10205"}]
        })
        assert request.keys[0].frontend_key == "10205"

    def test_empty_keys_are_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressRemoveRequest.model_validate({"keys": []})


class TestIngressReplaceRequest:
    def test_empty_ingresses_clear_all(self) -> None:
        request = IngressReplaceRequest.model_validate({"ingresses": []})
        assert request.ingresses == []

    def test_same_ingress_twice_is_rejected(self, port_ingress_payload: dict[str, Any]) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressReplaceRequest.model_validate({
                "ingresses": [port_ingress_payload, port_ingress_payload]
            })
