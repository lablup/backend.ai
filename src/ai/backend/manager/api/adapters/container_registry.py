"""Container registry adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    ContainerRegistryFilter,
    ContainerRegistryOrder,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
    ContainerRegistryNode,
    CreateContainerRegistryPayload,
    DeleteContainerRegistryPayload,
    UpdateContainerRegistryPayload,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryTypeFilter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.container_registry.conditions import ContainerRegistryConditions
from ai.backend.manager.models.container_registry.orders import (
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.creators import (
    ContainerRegistryCreatorSpec,
)
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)
from ai.backend.manager.services.container_registry.actions.create_container_registry import (
    CreateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.search_container_registries import (
    SearchContainerRegistriesAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class ContainerRegistryAdapter(BaseAdapter):
    """Adapter for container registry domain operations."""

    async def admin_search(
        self,
        input: AdminSearchContainerRegistriesInput,
    ) -> AdminSearchContainerRegistriesPayload:
        """Search container registries (admin, no scope) with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = (
            await self._processors.container_registry.search_container_registries.wait_for_complete(
                SearchContainerRegistriesAction(querier=querier)
            )
        )

        return AdminSearchContainerRegistriesPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_create(
        self,
        input: CreateContainerRegistryInput,
    ) -> CreateContainerRegistryPayload:
        """Create a new container registry (superadmin only)."""
        allowed_groups = None
        if input.allowed_groups is not None:
            allowed_groups = AllowedGroupsModel(
                add=input.allowed_groups.add,
                remove=input.allowed_groups.remove,
            )
        spec = ContainerRegistryCreatorSpec(
            url=input.url,
            type=input.type,
            registry_name=input.registry_name,
            is_global=input.is_global,
            project=input.project,
            username=input.username,
            password=input.password,
            ssl_verify=input.ssl_verify,
            extra=input.extra,
            allowed_groups=allowed_groups,
        )
        result = (
            await self._processors.container_registry.create_container_registry.wait_for_complete(
                CreateContainerRegistryAction(creator=Creator(spec=spec))
            )
        )
        return CreateContainerRegistryPayload(registry=self._data_to_dto(result.data))

    async def admin_update(
        self,
        input: UpdateContainerRegistryInput,
    ) -> UpdateContainerRegistryPayload:
        """Update an existing container registry (superadmin only)."""
        allowed_groups_model = None
        if input.allowed_groups is not None:
            allowed_groups_model = AllowedGroupsModel(
                add=input.allowed_groups.add,
                remove=input.allowed_groups.remove,
            )
        spec = ContainerRegistryUpdaterSpec(
            url=(OptionalState.update(input.url) if input.url is not None else OptionalState.nop()),
            type=(
                OptionalState.update(input.type) if input.type is not None else OptionalState.nop()
            ),
            registry_name=(
                OptionalState.update(input.registry_name)
                if input.registry_name is not None
                else OptionalState.nop()
            ),
            is_global=(
                TriState.update(input.is_global) if input.is_global is not None else TriState.nop()
            ),
            project=(
                TriState.update(input.project) if input.project is not None else TriState.nop()
            ),
            username=(
                TriState.update(input.username) if input.username is not None else TriState.nop()
            ),
            password=(
                TriState.update(input.password) if input.password is not None else TriState.nop()
            ),
            ssl_verify=(
                TriState.update(input.ssl_verify)
                if input.ssl_verify is not None
                else TriState.nop()
            ),
            extra=(TriState.update(input.extra) if input.extra is not None else TriState.nop()),
            allowed_groups=(
                TriState.update(allowed_groups_model)
                if allowed_groups_model is not None
                else TriState.nop()
            ),
        )
        updater: Updater[ContainerRegistryRow] = Updater(spec=spec, pk_value=input.id)
        result = (
            await self._processors.container_registry.modify_container_registry.wait_for_complete(
                ModifyContainerRegistryAction(updater=updater)
            )
        )
        return UpdateContainerRegistryPayload(registry=self._data_to_dto(result.data))

    async def admin_delete(
        self,
        input: DeleteContainerRegistryInput,
    ) -> DeleteContainerRegistryPayload:
        """Delete a container registry (superadmin only). This is a hard delete."""
        purger: Purger[ContainerRegistryRow] = Purger(
            row_class=ContainerRegistryRow,
            pk_value=input.id,
        )
        await self._processors.container_registry.delete_container_registry.wait_for_complete(
            DeleteContainerRegistryAction(purger=purger)
        )
        return DeleteContainerRegistryPayload(id=input.id)

    def build_querier(self, input: AdminSearchContainerRegistriesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else [DEFAULT_FORWARD_ORDER]
        orders.append(TIEBREAKER_ORDER)
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ContainerRegistryFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.registry_name is not None:
            condition = self._convert_string_filter(filter.registry_name)
            if condition is not None:
                conditions.append(condition)
        if filter.type is not None:
            conditions.extend(self._convert_type_filter(filter.type))
        if filter.is_global is not None:
            conditions.append(ContainerRegistryConditions.by_is_global(filter.is_global))
        return conditions

    def _convert_string_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ContainerRegistryConditions.by_registry_name_contains,
            equals_factory=ContainerRegistryConditions.by_registry_name_equals,
            starts_with_factory=ContainerRegistryConditions.by_registry_name_starts_with,
            ends_with_factory=ContainerRegistryConditions.by_registry_name_ends_with,
        )

    @staticmethod
    def _convert_type_filter(tf: ContainerRegistryTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if tf.equals is not None:
            conditions.append(ContainerRegistryConditions.by_type_equals(tf.equals))
        if tf.in_ is not None:
            conditions.append(ContainerRegistryConditions.by_type_in(tf.in_))
        if tf.not_equals is not None:
            conditions.append(ContainerRegistryConditions.by_type_not_equals(tf.not_equals))
        if tf.not_in is not None:
            conditions.append(ContainerRegistryConditions.by_type_not_in(tf.not_in))
        return conditions

    @staticmethod
    def _convert_orders(order: list[ContainerRegistryOrder]) -> list[QueryOrder]:
        return [resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchContainerRegistriesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    async def batch_load_by_ids(
        self, ids: Sequence[uuid.UUID]
    ) -> list[ContainerRegistryNode | None]:
        """Batch load container registries by IDs for DataLoader use.

        Returns ContainerRegistryNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[ContainerRegistryConditions.by_ids(ids)],
        )
        action_result = (
            await self._processors.container_registry.search_container_registries.wait_for_complete(
                SearchContainerRegistriesAction(querier=querier)
            )
        )
        registry_map = {item.id: self._data_to_dto(item) for item in action_result.data}
        return [registry_map.get(registry_id) for registry_id in ids]

    @staticmethod
    def _data_to_dto(data: ContainerRegistryData) -> ContainerRegistryNode:
        """Convert data layer type to Pydantic DTO."""
        return ContainerRegistryNode(
            id=data.id,
            url=data.url,
            registry_name=data.registry_name,
            type=data.type,
            project=data.project,
            username=data.username,
            ssl_verify=data.ssl_verify,
            is_global=data.is_global,
            extra=data.extra,
        )
