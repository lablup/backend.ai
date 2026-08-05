"""Unit tests for BulkUpsertAppConfigFragmentsAction's RBAC target resolution.

``target_element()`` decides the scope the RBAC scope validator authorizes a fragment write
against (BEP-1052): a user/domain fragment targets its USER/DOMAIN scope, while a public
fragment is global-scoped (no RBAC scope element) and thus superadmin-only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.app_config_fragment.upserters import (
    AppConfigFragmentUpserterSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)

_VICTIM_USER_ID = UserID(uuid.uuid4())
_DOMAIN_ID = DomainID(uuid.uuid4())
_VICTIM_USER_SCOPE_ID = AppConfigScopeID(_VICTIM_USER_ID)
_DOMAIN_SCOPE_ID = AppConfigScopeID(_DOMAIN_ID)


@dataclass(frozen=True)
class _ScopeTarget:
    """A fragment scope, and the RBAC scope an upsert at it must authorize against."""

    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeID | None
    expected_element: RBACElementRef
    expected_scope_type: ScopeType


class TestBulkUpsertTargetElement:
    """The upsert action targets the scope it writes at, taken from the action's scope."""

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeTarget(
                scope_type=AppConfigScopeType.USER,
                scope_id=_VICTIM_USER_SCOPE_ID,
                expected_element=RBACElementRef(RBACElementType.USER, str(_VICTIM_USER_ID)),
                expected_scope_type=ScopeType.USER,
            ),
            _ScopeTarget(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                expected_element=RBACElementRef(RBACElementType.DOMAIN, str(_DOMAIN_ID)),
                expected_scope_type=ScopeType.DOMAIN,
            ),
            _ScopeTarget(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                expected_element=RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, ""),
                expected_scope_type=ScopeType.GLOBAL,
            ),
        ],
        ids=[
            "user_scope_targets_the_scope_user",
            "domain_scope_targets_the_domain",
            "public_scope_has_no_scope_element",
        ],
    )
    def test_target_element_follows_the_written_scope(self, case: _ScopeTarget) -> None:
        action = BulkUpsertAppConfigFragmentsAction(
            scope=AppConfigFragmentSearchScope(scope_type=case.scope_type, scope_id=case.scope_id),
            upserter_specs=[
                AppConfigFragmentUpserterSpec(
                    config_name="cfg",
                    scope_type=case.scope_type,
                    scope_id=case.scope_id,
                    config={},
                )
            ],
        )

        assert action.target_element() == case.expected_element
        assert action.scope_type() == case.expected_scope_type
