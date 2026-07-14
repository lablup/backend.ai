"""Unit tests for CreateAppConfigFragmentAction's RBAC target resolution.

``target_element()`` decides the scope the RBAC scope validator authorizes a fragment
create against (BEP-1052): a user/domain fragment targets its USER/DOMAIN scope, while a
public fragment is global-scoped (no RBAC scope element) and thus superadmin-only.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)


def _make_action(
    *,
    scope_type: AppConfigScopeType,
    scope_id: str,
) -> CreateAppConfigFragmentAction:
    return CreateAppConfigFragmentAction(
        creator_spec=AppConfigFragmentCreatorSpec(
            config_name="cfg",
            scope_type=scope_type,
            scope_id=scope_id,
            config={},
        )
    )


@dataclass(frozen=True)
class _ScopeTarget:
    """A fragment scope, and the RBAC scope a create at it must authorize against."""

    scope_type: AppConfigScopeType
    scope_id: str
    expected_element: RBACElementRef
    expected_scope_type: ScopeType


class TestCreateTargetElement:
    """The create action targets the fragment's own scope, taken from its spec."""

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeTarget(
                scope_type=AppConfigScopeType.USER,
                scope_id="victim-user",
                expected_element=RBACElementRef(RBACElementType.USER, "victim-user"),
                expected_scope_type=ScopeType.USER,
            ),
            _ScopeTarget(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id="default",
                expected_element=RBACElementRef(RBACElementType.DOMAIN, "default"),
                expected_scope_type=ScopeType.DOMAIN,
            ),
            _ScopeTarget(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="",
                expected_element=RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, ""),
                expected_scope_type=ScopeType.GLOBAL,
            ),
        ],
        ids=[
            "user_scope_targets_the_spec_user",
            "domain_scope_targets_the_domain",
            "public_scope_has_no_scope_element",
        ],
    )
    def test_target_element_follows_the_fragment_scope(self, case: _ScopeTarget) -> None:
        action = _make_action(scope_type=case.scope_type, scope_id=case.scope_id)

        assert action.target_element() == case.expected_element
        assert action.scope_type() == case.expected_scope_type
