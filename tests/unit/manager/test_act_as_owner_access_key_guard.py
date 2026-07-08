"""Guard: owner_access_key is rejected whenever the X-BackendAI-Act-As header is
present, regardless of the value — self-impersonation included.
"""

from __future__ import annotations

import pytest

from ai.backend.common.contexts.user import with_impersonation
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.utils import reject_owner_access_key_while_impersonating


def test_owner_access_key_rejected_while_impersonating() -> None:
    with with_impersonation():
        with pytest.raises(InvalidAPIParameters):
            reject_owner_access_key_while_impersonating("AKIAOWNER")


def test_owner_access_key_rejected_even_for_self_impersonation() -> None:
    # The caller's own key is still rejected: the header presence is what matters.
    with with_impersonation():
        with pytest.raises(InvalidAPIParameters):
            reject_owner_access_key_while_impersonating("AKIACALLER")


def test_none_owner_access_key_is_noop_while_impersonating() -> None:
    with with_impersonation():
        reject_owner_access_key_while_impersonating(None)


def test_owner_access_key_allowed_when_not_impersonating() -> None:
    reject_owner_access_key_while_impersonating("AKIAOWNER")
