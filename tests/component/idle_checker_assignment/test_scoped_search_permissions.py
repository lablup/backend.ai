"""Component tests for scoped idle-checker-assignment search RBAC.

POST /v2/idle-checker-assignments/scoped/search runs through
``BulkActionProcessor`` + ``BulkActionRBACValidator``: every scope item is
RBAC-checked against the caller, items are OR'd, and one denied item fails
the whole request.
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentScopeDTO,
    IdleCheckerScopeRefDTO,
    ScopedSearchIdleCheckerAssignmentsInput,
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID

from .conftest import AssignmentSeedData


class TestScopedIdleCheckerAssignmentSearchPermissions:
    async def test_superadmin_sees_assignments_in_any_scope(
        self,
        admin_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
    ) -> None:
        """Superadmin bypasses RBAC and unions assignments across scope kinds."""
        result = await admin_v2_registry.idle_checker_assignment.scoped_search(
            ScopedSearchIdleCheckerAssignmentsInput(
                scope=IdleCheckerAssignmentScopeDTO(
                    items=[
                        IdleCheckerScopeRefDTO(
                            scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
                            scope_id=assignment_seed.domain_id,
                        ),
                        IdleCheckerScopeRefDTO(
                            scope_type=IdleCheckerScopeTypeDTO.PROJECT,
                            scope_id=assignment_seed.project_id,
                        ),
                    ]
                )
            )
        )

        assert {item.id for item in result.items} == {
            assignment_seed.domain_assignment_id,
            assignment_seed.project_assignment_id,
        }

    async def test_project_admin_sees_own_project_assignments(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        project_read_permission: None,
    ) -> None:
        """A user with PROJECT:READ on the project sees that project's assignments."""
        result = await user_v2_registry.idle_checker_assignment.scoped_search(
            ScopedSearchIdleCheckerAssignmentsInput(
                scope=IdleCheckerAssignmentScopeDTO(
                    items=[
                        IdleCheckerScopeRefDTO(
                            scope_type=IdleCheckerScopeTypeDTO.PROJECT,
                            scope_id=assignment_seed.project_id,
                        ),
                    ]
                )
            )
        )

        assert [item.id for item in result.items] == [assignment_seed.project_assignment_id]

    async def test_project_admin_denied_on_unauthorized_scope(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        project_read_permission: None,
    ) -> None:
        """One denied scope item fails the whole request, even with a permitted one."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.scoped_search(
                ScopedSearchIdleCheckerAssignmentsInput(
                    scope=IdleCheckerAssignmentScopeDTO(
                        items=[
                            IdleCheckerScopeRefDTO(
                                scope_type=IdleCheckerScopeTypeDTO.PROJECT,
                                scope_id=assignment_seed.project_id,
                            ),
                            IdleCheckerScopeRefDTO(
                                scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
                                scope_id=assignment_seed.domain_id,
                            ),
                        ]
                    )
                )
            )

    async def test_regular_user_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
    ) -> None:
        """A user without any scope permission is denied."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.scoped_search(
                ScopedSearchIdleCheckerAssignmentsInput(
                    scope=IdleCheckerAssignmentScopeDTO(
                        items=[
                            IdleCheckerScopeRefDTO(
                                scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
                                scope_id=assignment_seed.domain_id,
                            ),
                        ]
                    )
                )
            )

    async def test_project_admin_denied_on_other_project(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        project_read_permission: None,
    ) -> None:
        """PROJECT:READ on one project grants nothing on another project."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.scoped_search(
                ScopedSearchIdleCheckerAssignmentsInput(
                    scope=IdleCheckerAssignmentScopeDTO(
                        items=[
                            IdleCheckerScopeRefDTO(
                                scope_type=IdleCheckerScopeTypeDTO.PROJECT,
                                scope_id=assignment_seed.other_project_id,
                            ),
                        ]
                    )
                )
            )


class TestIdleCheckerAssignmentMutationPermissions:
    """update/purge on super-admin-created assignments, per caller scope permission."""

    async def test_project_admin_updates_assignment_in_own_project(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        project_assignment_manage_permission: None,
    ) -> None:
        """A user with UPDATE at the project scope can update that project's assignment."""
        result = await user_v2_registry.idle_checker_assignment.update(
            assignment_seed.project_assignment_id,
            UpdateIdleCheckerAssignmentInput(
                id=IdleCheckerAssignmentID(assignment_seed.project_assignment_id),
                enabled=False,
            ),
        )

        assert result.idle_checker_assignment.id == assignment_seed.project_assignment_id
        assert result.idle_checker_assignment.enabled is False

    async def test_project_admin_purges_assignment_in_own_project(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        project_assignment_manage_permission: None,
    ) -> None:
        """A user with PURGE at the project scope can purge that project's assignment."""
        result = await user_v2_registry.idle_checker_assignment.purge(
            assignment_seed.project_assignment_id
        )

        assert result.id == assignment_seed.project_assignment_id

    async def test_project_admin_cannot_update_assignment_in_other_project(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        project_assignment_manage_permission: None,
    ) -> None:
        """Manage permission on one project does not reach another project's assignment."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.update(
                assignment_seed.other_project_assignment_id,
                UpdateIdleCheckerAssignmentInput(
                    id=IdleCheckerAssignmentID(assignment_seed.other_project_assignment_id),
                    enabled=False,
                ),
            )

    async def test_superadmin_updates_any_assignment(
        self,
        admin_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
    ) -> None:
        """Superadmin bypasses RBAC for update on any scope's assignment."""
        result = await admin_v2_registry.idle_checker_assignment.update(
            assignment_seed.domain_assignment_id,
            UpdateIdleCheckerAssignmentInput(
                id=IdleCheckerAssignmentID(assignment_seed.domain_assignment_id),
                enabled=False,
            ),
        )

        assert result.idle_checker_assignment.enabled is False
