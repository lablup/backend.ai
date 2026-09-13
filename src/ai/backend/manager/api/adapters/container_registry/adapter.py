"""Container registry adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
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
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryGroupsAssociationNotFound
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.container_registry.conditions import ContainerRegistryConditions
from ai.backend.manager.models.container_registry.creators import (
    ContainerRegistryCreator,
    ContainerRegistryProjectCreator,
)
from ai.backend.manager.models.container_registry.orders import (
    DEFAULT_BACKWARD_ORDER,
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.models.container_registry.purgers import (
    ContainerRegistryProjectPurger,
    ContainerRegistryPurger,
)
from ai.backend.manager.models.container_registry.updaters import ContainerRegistryUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.container_registry.actions.create_container_registry import (
    CreateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.search_container_registries import (
    SearchContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.update_container_registry import (
    UpdateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.rbac.actions.relation.base import RelationPair
from ai.backend.manager.services.rbac.actions.relation.create import CreateRelationAction
from ai.backend.manager.services.rbac.actions.relation.purge import PurgeRelationAction
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.types import OptionalState, TriState


def _pagination_spec() -> PaginationSpec:
    """How a page of registries is cut, in either mode. The order runs by id."""
    return PaginationSpec(
        forward_order=DEFAULT_FORWARD_ORDER,
        backward_order=DEFAULT_BACKWARD_ORDER,
        forward_condition_factory=ContainerRegistryConditions.by_cursor_forward,
        backward_condition_factory=ContainerRegistryConditions.by_cursor_backward,
        tiebreaker_order=TIEBREAKER_ORDER,
    )


class ContainerRegistryAdapter(BaseAdapter):
    """Adapter for container registry domain operations."""

    _container_registry: ContainerRegistryProcessors
    _rbac: RbacProcessors

    def __init__(
        self,
        container_registry: ContainerRegistryProcessors,
        rbac: RbacProcessors,
    ) -> None:
        self._container_registry = container_registry
        self._rbac = rbac

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

        action_result = await self._container_registry.search_container_registries.run(
            SearchContainerRegistriesAction(querier=querier)
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
        data = await self.create_registry(input)
        return CreateContainerRegistryPayload(registry=self._data_to_dto(data))

    async def create_registry(
        self,
        input: CreateContainerRegistryInput,
    ) -> ContainerRegistryData:
        """Create the registry and link it to the projects the input names."""
        creator = ContainerRegistryCreator(
            url=input.url,
            type=input.type,
            registry_name=input.registry_name,
            is_global=input.is_global,
            project=input.project,
            username=input.username,
            password=input.password,
            ssl_verify=input.ssl_verify,
            extra=input.extra,
        )
        result = await self._container_registry.create_container_registry.run(
            CreateContainerRegistryAction(creator=creator)
        )
        if input.allowed_groups is not None:
            await self.apply_allowed_groups(
                ContainerRegistryID(result.data.id),
                AllowedGroupsModel(
                    add=input.allowed_groups.add,
                    remove=input.allowed_groups.remove,
                ),
            )
        return result.data

    async def admin_update(
        self,
        input: UpdateContainerRegistryInput,
    ) -> UpdateContainerRegistryPayload:
        """Update an existing container registry (superadmin only)."""
        if input.allowed_groups is not None:
            await self.apply_allowed_groups(
                ContainerRegistryID(input.id),
                AllowedGroupsModel(
                    add=input.allowed_groups.add,
                    remove=input.allowed_groups.remove,
                ),
            )
        updater = ContainerRegistryUpdater(
            registry_id=ContainerRegistryID(input.id),
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
        )
        result = await self._container_registry.update_container_registry.run(
            UpdateContainerRegistryAction(updater=updater)
        )
        return UpdateContainerRegistryPayload(registry=self._data_to_dto(result.data))

    async def apply_allowed_groups(
        self,
        registry_id: ContainerRegistryID,
        allowed_groups: AllowedGroupsModel,
    ) -> None:
        """Link the registry to the projects named to add and unlink it from the ones
        named to remove.

        One run per direction, carrying every pair it names: the permission is asked of
        the registry and of every project, and a project already allowed is left as it
        stands. Removing where no named project was linked raises, as it did while the
        repository wrote these rows beside the update.
        """
        if allowed_groups.add:
            await self._rbac.create_relation.run(
                CreateRelationAction(
                    pairs=[
                        RelationPair(scope=ProjectID(uuid.UUID(raw)), target=registry_id)
                        for raw in allowed_groups.add
                    ],
                    creator=ContainerRegistryProjectCreator(),
                )
            )
        if not allowed_groups.remove:
            return
        result = await self._rbac.purge_relation.run(
            PurgeRelationAction(
                pairs=[
                    RelationPair(scope=ProjectID(uuid.UUID(raw)), target=registry_id)
                    for raw in allowed_groups.remove
                ],
                purger=ContainerRegistryProjectPurger(),
            )
        )
        if not any(unlink.unlinked for unlink in result.results):
            raise ContainerRegistryGroupsAssociationNotFound(
                f"Tried to remove non-existing associations for registry_id: {registry_id}, "
                f"group_ids: {allowed_groups.remove}"
            )

    async def admin_delete(
        self,
        input: DeleteContainerRegistryInput,
    ) -> DeleteContainerRegistryPayload:
        """Delete a container registry (superadmin only). This is a hard delete."""
        purger = ContainerRegistryPurger(registry_id=ContainerRegistryID(input.id))
        await self._container_registry.delete_container_registry.run(
            DeleteContainerRegistryAction(purger=purger)
        )
        return DeleteContainerRegistryPayload(id=input.id)

    def build_querier(self, input: AdminSearchContainerRegistriesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO.

        Both pagination modes the request type carries are read here. Reading only
        the offset pair dropped a caller's cursor without saying so.
        """
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []

        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

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
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_string_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ContainerRegistryConditions.by_registry_name_contains,
            equals_factory=ContainerRegistryConditions.by_registry_name_equals,
            starts_with_factory=ContainerRegistryConditions.by_registry_name_starts_with,
            ends_with_factory=ContainerRegistryConditions.by_registry_name_ends_with,
            in_factory=ContainerRegistryConditions.by_registry_name_in,
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

    async def batch_load_by_ids(
        self, ids: Sequence[ContainerRegistryID]
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
        action_result = await self._container_registry.search_container_registries.run(
            SearchContainerRegistriesAction(querier=querier)
        )
        registry_map = {item.id: self._data_to_dto(item) for item in action_result.data}
        return [registry_map.get(ContainerRegistryID(registry_id)) for registry_id in ids]

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
