"""Unit tests for keypair query conditions (SQL generation)."""

from __future__ import annotations

import uuid

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.models.keypair import KeyPairRow  # noqa: F401 - ensure mapper init
from ai.backend.manager.models.keypair.conditions import KeypairConditions


class TestKeypairUserIdConditions:
    """The keypair owner (``user``) filters used by nested resource-policy filters."""

    def test_by_user_id_equals_generates_equality(self) -> None:
        condition = KeypairConditions.by_user_id_equals(
            UUIDEqualMatchSpec(value=uuid.uuid4(), negated=False)
        )
        sql = str(condition().compile())
        assert "keypairs" in sql
        assert "user" in sql
        assert "!=" not in sql

    def test_by_user_id_equals_negated(self) -> None:
        condition = KeypairConditions.by_user_id_equals(
            UUIDEqualMatchSpec(value=uuid.uuid4(), negated=True)
        )
        sql = str(condition().compile())
        assert "!=" in sql

    def test_by_user_id_in_generates_in_clause(self) -> None:
        condition = KeypairConditions.by_user_id_in(
            UUIDInMatchSpec(values=[uuid.uuid4(), uuid.uuid4()], negated=False)
        )
        sql = str(condition().compile())
        assert "IN" in sql
        assert "NOT IN" not in sql

    def test_by_user_id_in_negated(self) -> None:
        condition = KeypairConditions.by_user_id_in(
            UUIDInMatchSpec(values=[uuid.uuid4()], negated=True)
        )
        sql = str(condition().compile())
        assert "NOT IN" in sql
