"""Login client type search operations the current rules ban.

``description`` is ``sa.Text`` with no index serving partial matches, which
`models/specs/search/AGENTS.md` limits to equality and membership. What is here shipped
before the rule and is removed once the filter is withdrawn or an index is added.
Nothing new goes here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.conditions.string import StringConditions

__all__ = ("DeprecatedLoginClientTypeDescriptionConditions",)


class DeprecatedLoginClientTypeDescriptionConditions(StringConditions):
    """Partial matches on the description column."""

    def __init__(self) -> None:
        super().__init__(LoginClientTypeRow.description)
