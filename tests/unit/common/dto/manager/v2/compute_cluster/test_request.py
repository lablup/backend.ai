"""Tests for ai.backend.common.dto.manager.v2.compute_cluster.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    CreateComputeClusterInput,
    UpdateComputeClusterInput,
)
from ai.backend.common.dto.manager.v2.compute_cluster.types import ComputeClusterStatus
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET


class TestCreateComputeClusterInput:
    def test_namespace_prefix_defaults_to_bai(self) -> None:
        inp = CreateComputeClusterInput(
            name="k8s-a", api_server="https://10.0.0.1:6443", kubeconfig="apiVersion: v1"
        )
        assert inp.namespace_prefix == "bai-"
        assert inp.description is None
        assert inp.gateway_addr is None
        assert inp.gateway_public_key is None

    def test_kubeconfig_required(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateComputeClusterInput.model_validate({
                "name": "k8s-a",
                "api_server": "https://10.0.0.1:6443",
            })

    def test_kubeconfig_empty_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateComputeClusterInput(
                name="k8s-a", api_server="https://10.0.0.1:6443", kubeconfig=""
            )

    def test_name_too_long_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateComputeClusterInput(
                name="a" * 65, api_server="https://10.0.0.1:6443", kubeconfig="apiVersion: v1"
            )


class TestUpdateComputeClusterInput:
    def test_every_field_defaults_to_unset(self) -> None:
        inp = UpdateComputeClusterInput()
        assert inp.description is UNSET
        assert inp.api_server is UNSET
        assert inp.kubeconfig is UNSET
        assert inp.namespace_prefix is UNSET
        assert inp.gateway_addr is UNSET
        assert inp.gateway_public_key is UNSET
        assert inp.status is UNSET

    def test_nullable_fields_accept_none(self) -> None:
        inp = UpdateComputeClusterInput(
            description=None, gateway_addr=None, gateway_public_key=None
        )
        assert inp.description is None
        assert inp.gateway_addr is None
        assert inp.gateway_public_key is None

    def test_status_update(self) -> None:
        inp = UpdateComputeClusterInput.model_validate({"status": "LOST"})
        assert inp.status == ComputeClusterStatus.LOST

    def test_unknown_status_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateComputeClusterInput.model_validate({"status": "GONE"})

    def test_namespace_prefix_empty_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateComputeClusterInput(namespace_prefix="")

    def test_omitted_fields_from_json_are_unset(self) -> None:
        inp = UpdateComputeClusterInput.model_validate({"api_server": "https://k8s:6443"})
        assert inp.api_server == "https://k8s:6443"
        assert inp.kubeconfig is UNSET
