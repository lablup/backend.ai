"""Resource policy search operations the current rules ban.

A filter on another entity's column cannot ask whether the caller may read that row,
which `models/specs/search/AGENTS.md` bans. What is here shipped before the rule, is
marked deprecated in the schema, and is removed in the next release. Nothing new goes
here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow

__all__ = ("DeprecatedKeyPairResourcePolicyConditions",)


class DeprecatedKeyPairResourcePolicyConditions:
    """Filters on the keypairs a policy applies to."""

    @staticmethod
    def exists_keypair_combined(keypair_conditions: list[QueryCondition]) -> QueryCondition:
        """Every keypair condition in one EXISTS, so they match the same keypair."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(
                KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name
            )
            for cond in keypair_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner
