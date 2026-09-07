"""Component tests for idle-checker-assignment RBAC.

POST /v2/idle-checker-assignments/scoped/search runs through the scope processor:
every scope item is checked against the caller for READ on idle checkers within it,
items are OR'd, and one denied item fails the whole request. Update and purge are relation
writes: the caller must hold the operation on the scope and on the checker.
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentScopeDTO,
    IdleCheckerScopeRefDTO,
    ScopedSearchIdleCheckerAssignmentsInput,
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO

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
        project_assignment_read_permission: None,
    ) -> None:
        """A user with READ on idle checkers in the project sees that project's assignments."""
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
        project_assignment_read_permission: None,
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
        project_assignment_read_permission: None,
    ) -> None:
        """READ within one project grants nothing on another project's bindings."""
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
        """A user holding the switch on the project and on the checker can toggle the binding."""
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
        """A user holding the unlink on the project and on the checker can purge the binding."""
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
        """Manage permission on one project does not reach another project's assignment.

        The id resolves, since the caller reads the checker through their own project,
        but the switch is answered for by the other project too.
        """
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

    async def test_user_cannot_update_assignment_bound_to_own_user_scope(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        user_self_scope_permission: None,
    ) -> None:
        """Owning the user scope does not grant managing the idle check bound to it."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.update(
                assignment_seed.user_assignment_id,
                UpdateIdleCheckerAssignmentInput(
                    id=IdleCheckerAssignmentID(assignment_seed.user_assignment_id),
                    enabled=False,
                ),
            )

    async def test_user_cannot_purge_assignment_bound_to_own_user_scope(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        user_self_scope_permission: None,
    ) -> None:
        """Same for purge — a user must not be able to drop their own idle check."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.purge(assignment_seed.user_assignment_id)

    async def test_project_manager_cannot_reach_user_scope_assignment_of_project_member(
        self,
        user_v2_registry: V2ClientRegistry,
        assignment_seed: AssignmentSeedData,
        user_in_seeded_project: None,
        project_assignment_manage_permission: None,
    ) -> None:
        """A binding on the user's own scope names the user, not the project a user
        belongs to, so project-side rights do not reach it."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.idle_checker_assignment.update(
                assignment_seed.user_assignment_id,
                UpdateIdleCheckerAssignmentInput(
                    id=IdleCheckerAssignmentID(assignment_seed.user_assignment_id),
                    enabled=False,
                ),
            )
