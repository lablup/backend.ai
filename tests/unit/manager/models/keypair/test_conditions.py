"""Unit tests for keypair query conditions (SQL generation)."""

from __future__ import annotations

import uuid

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.models.keypair import KeyPairRow  # noqa: F401 - ensure mapper init
from ai.backend.manager.models.keypair.conditions import KeypairConditions


class TestKeypairUserIdConditions:
    """Tests for keypair owner (user UUID) conditions in KeypairConditions."""

    def test_by_user_id_equals_generates_equality(self) -> None:
        user_uuid = uuid.uuid4()
        spec = UUIDEqualMatchSpec(value=user_uuid, negated=False)
        condition = KeypairConditions.by_user_id_equals(spec)
        sql = str(condition().compile())
        assert "keypairs" in sql
        assert "user" in sql

    def test_by_user_id_equals_negated(self) -> None:
        user_uuid = uuid.uuid4()
        spec = UUIDEqualMatchSpec(value=user_uuid, negated=True)
        condition = KeypairConditions.by_user_id_equals(spec)
        sql = str(condition().compile())
        assert "!=" in sql or "NOT" in sql.upper()

    def test_by_user_id_in_generates_in_clause(self) -> None:
        user_uuids = [uuid.uuid4(), uuid.uuid4()]
        spec = UUIDInMatchSpec(values=user_uuids, negated=False)
        condition = KeypairConditions.by_user_id_in(spec)
        sql = str(condition().compile())
        assert "keypairs" in sql
        assert "IN" in sql.upper()

    def test_by_user_id_in_negated(self) -> None:
        user_uuids = [uuid.uuid4(), uuid.uuid4()]
        spec = UUIDInMatchSpec(values=user_uuids, negated=True)
        condition = KeypairConditions.by_user_id_in(spec)
        sql = str(condition().compile())
        assert "NOT IN" in sql.upper()
