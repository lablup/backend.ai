"""
Gold format compatibility tests for trafaret → pydantic migration.

These tests verify that the same JSON input dict can be parsed by both
trafaret schemas and pydantic DTOs, ensuring backward compatibility
for group (project) registry quota endpoints.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.dto.manager.group import (
    RegistryQuotaReadRequest,
    RegistryQuotaReadResponse,
    RegistryQuotaRequest,
)


class TestRegistryQuotaRequestGoldFormat:
    """Test registry quota create/update endpoint JSON format compatibility."""

    # Trafaret schema from original group.py
    trafaret_schema = t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
        tx.AliasedKey(["quota"]): t.Int,
    })

    @pytest.fixture
    def gold_format_with_group_id(self) -> dict:
        """Gold format JSON with group_id field."""
        return {
            "group_id": str(uuid4()),
            "quota": 1073741824,  # 1GB in bytes
        }

    @pytest.fixture
    def gold_format_with_group_alias(self) -> dict:
        """Gold format JSON with group field (alias for group_id)."""
        return {
            "group": str(uuid4()),
            "quota": 2147483648,  # 2GB in bytes
        }

    @pytest.fixture
    def gold_format_zero_quota(self) -> dict:
        """Gold format JSON with zero quota."""
        return {
            "group_id": str(uuid4()),
            "quota": 0,
        }

    def test_trafaret_parses_with_group_id(self, gold_format_with_group_id: dict) -> None:
        """Verify trafaret can parse with group_id field."""
        result = self.trafaret_schema.check(gold_format_with_group_id)
        assert result["group_id"] == gold_format_with_group_id["group_id"]
        assert result["quota"] == 1073741824

    def test_pydantic_parses_with_group_id(self, gold_format_with_group_id: dict) -> None:
        """Verify pydantic can parse with group_id field."""
        result = RegistryQuotaRequest.model_validate(gold_format_with_group_id)
        assert str(result.group_id) == gold_format_with_group_id["group_id"]
        assert result.quota == 1073741824

    def test_trafaret_parses_with_group_alias(self, gold_format_with_group_alias: dict) -> None:
        """Verify trafaret can parse with group field (alias)."""
        result = self.trafaret_schema.check(gold_format_with_group_alias)
        # AliasedKey normalizes to first key name
        assert result["group_id"] == gold_format_with_group_alias["group"]
        assert result["quota"] == 2147483648

    def test_pydantic_parses_with_group_alias(self, gold_format_with_group_alias: dict) -> None:
        """Verify pydantic can parse with group field (alias)."""
        result = RegistryQuotaRequest.model_validate(gold_format_with_group_alias)
        # AliasChoices normalizes to group_id field
        assert str(result.group_id) == gold_format_with_group_alias["group"]
        assert result.quota == 2147483648

    def test_trafaret_parses_zero_quota(self, gold_format_zero_quota: dict) -> None:
        """Verify trafaret can parse with zero quota."""
        result = self.trafaret_schema.check(gold_format_zero_quota)
        assert result["quota"] == 0

    def test_pydantic_parses_zero_quota(self, gold_format_zero_quota: dict) -> None:
        """Verify pydantic can parse with zero quota."""
        result = RegistryQuotaRequest.model_validate(gold_format_zero_quota)
        assert result.quota == 0


class TestRegistryQuotaReadRequestGoldFormat:
    """Test registry quota read/delete endpoint JSON format compatibility."""

    # Trafaret schema from original group.py
    trafaret_schema = t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
    })

    @pytest.fixture
    def gold_format_with_group_id(self) -> dict:
        """Gold format JSON with group_id field."""
        return {
            "group_id": str(uuid4()),
        }

    @pytest.fixture
    def gold_format_with_group_alias(self) -> dict:
        """Gold format JSON with group field (alias for group_id)."""
        return {
            "group": str(uuid4()),
        }

    def test_trafaret_parses_with_group_id(self, gold_format_with_group_id: dict) -> None:
        """Verify trafaret can parse with group_id field."""
        result = self.trafaret_schema.check(gold_format_with_group_id)
        assert result["group_id"] == gold_format_with_group_id["group_id"]

    def test_pydantic_parses_with_group_id(self, gold_format_with_group_id: dict) -> None:
        """Verify pydantic can parse with group_id field."""
        result = RegistryQuotaReadRequest.model_validate(gold_format_with_group_id)
        assert str(result.group_id) == gold_format_with_group_id["group_id"]

    def test_trafaret_parses_with_group_alias(self, gold_format_with_group_alias: dict) -> None:
        """Verify trafaret can parse with group field (alias)."""
        result = self.trafaret_schema.check(gold_format_with_group_alias)
        # AliasedKey normalizes to first key name
        assert result["group_id"] == gold_format_with_group_alias["group"]

    def test_pydantic_parses_with_group_alias(self, gold_format_with_group_alias: dict) -> None:
        """Verify pydantic can parse with group field (alias)."""
        result = RegistryQuotaReadRequest.model_validate(gold_format_with_group_alias)
        # AliasChoices normalizes to group_id field
        assert str(result.group_id) == gold_format_with_group_alias["group"]


class TestRegistryQuotaReadResponseGoldFormat:
    """Test registry quota read response JSON format compatibility."""

    @pytest.fixture
    def gold_format_response(self) -> dict:
        """Gold format JSON response."""
        return {
            "result": 1073741824,  # 1GB in bytes
        }

    @pytest.fixture
    def gold_format_zero_response(self) -> dict:
        """Gold format JSON response with zero quota."""
        return {
            "result": 0,
        }

    def test_pydantic_creates_response(self, gold_format_response: dict) -> None:
        """Verify pydantic can create response model."""
        result = RegistryQuotaReadResponse.model_validate(gold_format_response)
        assert result.result == 1073741824

    def test_pydantic_serializes_response(self, gold_format_response: dict) -> None:
        """Verify pydantic serializes to expected JSON format."""
        response = RegistryQuotaReadResponse(result=1073741824)
        serialized = response.model_dump(mode="json")
        assert serialized == gold_format_response

    def test_pydantic_creates_zero_response(self, gold_format_zero_response: dict) -> None:
        """Verify pydantic can create response model with zero quota."""
        result = RegistryQuotaReadResponse.model_validate(gold_format_zero_response)
        assert result.result == 0

    def test_pydantic_serializes_zero_response(self, gold_format_zero_response: dict) -> None:
        """Verify pydantic serializes zero quota to expected JSON format."""
        response = RegistryQuotaReadResponse(result=0)
        serialized = response.model_dump(mode="json")
        assert serialized == gold_format_zero_response


class TestRegistryQuotaValidationErrors:
    """Test validation error handling for registry quota requests."""

    def test_pydantic_rejects_missing_group_id(self) -> None:
        """Verify pydantic rejects request without group_id."""
        with pytest.raises(Exception):  # ValidationError
            RegistryQuotaRequest.model_validate({"quota": 1000})

    def test_pydantic_rejects_missing_quota(self) -> None:
        """Verify pydantic rejects request without quota."""
        with pytest.raises(Exception):  # ValidationError
            RegistryQuotaRequest.model_validate({"group_id": str(uuid4())})

    def test_pydantic_rejects_invalid_uuid(self) -> None:
        """Verify pydantic rejects invalid UUID for group_id."""
        with pytest.raises(Exception):  # ValidationError
            RegistryQuotaRequest.model_validate({"group_id": "not-a-uuid", "quota": 1000})

    def test_pydantic_rejects_invalid_quota_type(self) -> None:
        """Verify pydantic rejects non-integer quota."""
        with pytest.raises(Exception):  # ValidationError
            RegistryQuotaRequest.model_validate({"group_id": str(uuid4()), "quota": "not-an-int"})

    def test_trafaret_rejects_missing_group_id(self) -> None:
        """Verify trafaret rejects request without group_id."""
        trafaret_schema = t.Dict({
            tx.AliasedKey(["group_id", "group"]): t.String,
            tx.AliasedKey(["quota"]): t.Int,
        })
        with pytest.raises(t.DataError):
            trafaret_schema.check({"quota": 1000})

    def test_trafaret_rejects_missing_quota(self) -> None:
        """Verify trafaret rejects request without quota."""
        trafaret_schema = t.Dict({
            tx.AliasedKey(["group_id", "group"]): t.String,
            tx.AliasedKey(["quota"]): t.Int,
        })
        with pytest.raises(t.DataError):
            trafaret_schema.check({"group_id": str(uuid4())})
