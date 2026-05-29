"""Unit tests for keypair resource-policy query conditions (SQL generation)."""

from __future__ import annotations

import uuid

from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec
from ai.backend.manager.models.keypair import KeyPairRow  # noqa: F401 - ensure mapper init
from ai.backend.manager.models.keypair.conditions import KeypairConditions
from ai.backend.manager.models.resource_policy import (  # noqa: F401 - ensure mapper init
    KeyPairResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.conditions import KeypairResourcePolicyConditions


class TestExistsKeypairCombined:
    """``exists_keypair_combined`` correlates keypairs back to their resource policy."""

    def test_empty_conditions_still_correlates(self) -> None:
        combined = KeypairResourcePolicyConditions.exists_keypair_combined([])
        sql = str(combined().compile())
        assert "EXISTS" in sql
        assert "keypairs" in sql
        assert "keypair_resource_policies" in sql

    def test_single_exists_with_user_filter(self) -> None:
        inner = [
            KeypairConditions.by_user_id_equals(
                UUIDEqualMatchSpec(value=uuid.uuid4(), negated=False)
            )
        ]
        combined = KeypairResourcePolicyConditions.exists_keypair_combined(inner)
        sql = str(combined().compile())
        # The keypair-level conditions must be folded into a single EXISTS subquery.
        assert sql.count("EXISTS") == 1
        assert "keypairs" in sql

    def test_multiple_conditions_share_one_exists(self) -> None:
        inner = [
            KeypairConditions.by_user_id_equals(
                UUIDEqualMatchSpec(value=uuid.uuid4(), negated=False)
            ),
            KeypairConditions.by_access_key_equals(
                StringMatchSpec(value="AKIA", case_insensitive=False, negated=False)
            ),
            KeypairConditions.by_is_active(True),
        ]
        combined = KeypairResourcePolicyConditions.exists_keypair_combined(inner)
        sql = str(combined().compile())
        assert sql.count("EXISTS") == 1
        # All three keypair conditions are ANDed inside the same subquery.
        assert "access_key" in sql
        assert "is_active" in sql
