from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec


@dataclass
class GroupKernelBatchPurgerSpec(BatchPurgerSpec[KernelRow]):
    """PurgerSpec for deleting all kernels belonging to a group."""

    group_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KernelRow]]:
        return sa.select(KernelRow).where(KernelRow.group_id == self.group_id)


@dataclass
class GroupSessionBatchPurgerSpec(BatchPurgerSpec[SessionRow]):
    """PurgerSpec for deleting all sessions belonging to a group."""

    group_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        return sa.select(SessionRow).where(SessionRow.group_id == self.group_id)


@dataclass
class GroupEndpointSessionBatchPurgerSpec(BatchPurgerSpec[SessionRow]):
    """PurgerSpec for deleting sessions associated with group endpoints.

    This spec finds sessions that are connected to endpoints belonging to the group
    through the routing table.
    """

    project_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        # Subquery to get endpoint IDs for the group
        endpoint_subquery = sa.select(EndpointRow.id).where(EndpointRow.project == self.project_id)

        # Subquery to get session IDs from RoutingRow
        session_id_subquery = sa.select(RoutingRow.session).where(
            sa.and_(
                RoutingRow.endpoint.in_(endpoint_subquery),
                RoutingRow.session.is_not(None),
            )
        )

        return sa.select(SessionRow).where(SessionRow.id.in_(session_id_subquery))


@dataclass
class GroupEndpointBatchPurgerSpec(BatchPurgerSpec[EndpointRow]):
    """PurgerSpec for deleting all endpoints belonging to a group."""

    project_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[EndpointRow]]:
        return sa.select(EndpointRow).where(EndpointRow.project == self.project_id)


@dataclass
class GroupBatchPurgerSpec(BatchPurgerSpec[GroupRow]):
    """PurgerSpec for deleting a group."""

    group_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[GroupRow]]:
        return sa.select(GroupRow).where(GroupRow.id == self.group_id)


def create_group_kernel_purger(group_id: UUID) -> BatchPurger[KernelRow]:
    """Create a BatchPurger for deleting all kernels belonging to a group."""
    return BatchPurger(
        spec=GroupKernelBatchPurgerSpec(group_id=group_id),
    )


def create_group_session_purger(group_id: UUID) -> BatchPurger[SessionRow]:
    """Create a BatchPurger for deleting all sessions belonging to a group."""
    return BatchPurger(
        spec=GroupSessionBatchPurgerSpec(group_id=group_id),
    )


def create_group_endpoint_session_purger(group_id: UUID) -> BatchPurger[SessionRow]:
    """Create a BatchPurger for deleting sessions associated with group endpoints."""
    return BatchPurger(
        spec=GroupEndpointSessionBatchPurgerSpec(project_id=group_id),
    )


def create_group_endpoint_purger(group_id: UUID) -> BatchPurger[EndpointRow]:
    """Create a BatchPurger for deleting all endpoints belonging to a group."""
    return BatchPurger(
        spec=GroupEndpointBatchPurgerSpec(project_id=group_id),
    )


def create_group_purger(group_id: UUID) -> BatchPurger[GroupRow]:
    """Create a BatchPurger for deleting a group."""
    return BatchPurger(
        spec=GroupBatchPurgerSpec(group_id=group_id),
        batch_size=1,  # We expect only one row to be deleted
    )
