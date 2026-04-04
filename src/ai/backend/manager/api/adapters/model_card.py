from __future__ import annotations

import secrets
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    DeleteModelCardsInput,
    DeployModelCardInput,
    ModelCardFilter,
    ModelCardOrder,
    ResourceSlotEntryInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload,
    DeleteModelCardPayload,
    DeleteModelCardsPayload,
    DeployModelCardPayload,
    ModelCardMetadata,
    ModelCardNode,
    ResourceSlotEntryInfo,
    ScanProjectModelCardsPayload,
    SearchModelCardsPayload,
    UpdateModelCardPayload,
)
from ai.backend.common.dto.manager.v2.model_card.types import (
    ModelCardAccessLevel,
    ModelCardOrderField,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.api.adapters.deployment_revision_preset import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.deployment.creator import (
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.model_card.types import ModelCardData, ResourceRequirementEntry
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.resource import ModelCardNotFound
from ai.backend.manager.models.model_card.conditions import ModelCardConditions
from ai.backend.manager.models.model_card.orders import ModelCardOrders
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, combine_conditions_or
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.model_card.creators import ModelCardCreatorSpec
from ai.backend.manager.repositories.model_card.types import ProjectModelCardSearchScope
from ai.backend.manager.repositories.model_card.updaters import ModelCardUpdaterSpec
from ai.backend.manager.services.deployment.actions.create_deployment import CreateDeploymentAction
from ai.backend.manager.services.model_card.actions.available_presets import (
    AvailablePresetsAction,
)
from ai.backend.manager.services.model_card.actions.create import CreateModelCardAction
from ai.backend.manager.services.model_card.actions.delete import DeleteModelCardAction
from ai.backend.manager.services.model_card.actions.scan import ScanProjectModelCardsAction
from ai.backend.manager.services.model_card.actions.search import SearchModelCardsAction
from ai.backend.manager.services.model_card.actions.search_in_project import (
    SearchModelCardsInProjectAction,
)
from ai.backend.manager.services.model_card.actions.update import UpdateModelCardAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _model_card_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ModelCardOrders.created_at(ascending=False),
        backward_order=ModelCardOrders.created_at(ascending=True),
        forward_condition_factory=ModelCardConditions.by_cursor_forward,
        backward_condition_factory=ModelCardConditions.by_cursor_backward,
        tiebreaker_order=ModelCardRow.id.asc(),
    )


def _entries_to_requirements(
    entries: list[ResourceSlotEntryInput],
) -> list[ResourceRequirementEntry]:
    return [
        ResourceRequirementEntry(slot_name=e.resource_type, min_quantity=e.quantity)
        for e in entries
    ]


def _requirements_to_entries(
    reqs: list[ResourceRequirementEntry],
) -> list[ResourceSlotEntryInfo]:
    return [ResourceSlotEntryInfo(resource_type=r.slot_name, quantity=r.min_quantity) for r in reqs]


class ModelCardAdapter(BaseAdapter):
    async def admin_search(
        self,
        input: SearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_model_card_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.model_card.search.wait_for_complete(
            SearchModelCardsAction(querier=querier)
        )
        return SearchModelCardsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def project_search(
        self,
        project_id: UUID,
        input: SearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = ProjectModelCardSearchScope(project_id=project_id, user_id=me.user_id)
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_model_card_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.model_card.search_in_project.wait_for_complete(
            SearchModelCardsInProjectAction(scope=scope, querier=querier)
        )
        return SearchModelCardsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, card_id: UUID) -> ModelCardNode:
        conditions: list[QueryCondition] = [lambda: ModelCardRow.id == card_id]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_model_card_pagination_spec(),
            limit=1,
        )
        result = await self._processors.model_card.search.wait_for_complete(
            SearchModelCardsAction(querier=querier)
        )
        if not result.items:
            raise ModelCardNotFound()
        return self._data_to_node(result.items[0])

    async def create(
        self,
        input: CreateModelCardInput,
    ) -> CreateModelCardPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        min_resource = _entries_to_requirements(input.min_resource) if input.min_resource else []
        creator: RBACEntityCreator[ModelCardRow] = RBACEntityCreator(
            spec=ModelCardCreatorSpec(
                name=input.name,
                vfolder_id=input.vfolder_id,
                domain=input.domain_name or me.domain_name,
                project_id=input.project_id,
                creator_id=me.user_id,
                author=input.author,
                title=input.title,
                model_version=input.model_version,
                description=input.description,
                task=input.task,
                category=input.category,
                architecture=input.architecture,
                framework=input.framework,
                label=input.label,
                license=input.license,
                min_resource=min_resource,
                readme=input.readme,
                access_level=input.access_level.value,
            ),
            element_type=RBACElementType.MODEL_CARD,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.PROJECT,
                element_id=str(input.project_id),
            ),
        )
        result = await self._processors.model_card.create.wait_for_complete(
            CreateModelCardAction(creator=creator)
        )
        return CreateModelCardPayload(model_card=self._data_to_node(result.model_card))

    async def update(
        self,
        input: UpdateModelCardInput,
    ) -> UpdateModelCardPayload:
        min_resource_state: TriState[list[ResourceRequirementEntry]] = TriState.nop()
        if input.min_resource is not SENTINEL:
            if input.min_resource is None:
                min_resource_state = TriState.nullify()
            else:
                min_resource_state = TriState.update(_entries_to_requirements(input.min_resource))

        spec = ModelCardUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            author=(
                TriState.nop()
                if input.author is SENTINEL
                else TriState.nullify()
                if input.author is None
                else TriState.update(input.author)
            ),
            title=(
                TriState.nop()
                if input.title is SENTINEL
                else TriState.nullify()
                if input.title is None
                else TriState.update(input.title)
            ),
            model_version=(
                TriState.nop()
                if input.model_version is SENTINEL
                else TriState.nullify()
                if input.model_version is None
                else TriState.update(input.model_version)
            ),
            description=(
                TriState.nop()
                if input.description is SENTINEL
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            task=(
                TriState.nop()
                if input.task is SENTINEL
                else TriState.nullify()
                if input.task is None
                else TriState.update(input.task)
            ),
            category=(
                TriState.nop()
                if input.category is SENTINEL
                else TriState.nullify()
                if input.category is None
                else TriState.update(input.category)
            ),
            architecture=(
                TriState.nop()
                if input.architecture is SENTINEL
                else TriState.nullify()
                if input.architecture is None
                else TriState.update(input.architecture)
            ),
            framework=(
                OptionalState.update(input.framework)
                if input.framework is not None
                else OptionalState.nop()
            ),
            label=(
                OptionalState.update(input.label)
                if input.label is not None
                else OptionalState.nop()
            ),
            license=(
                TriState.nop()
                if input.license is SENTINEL
                else TriState.nullify()
                if input.license is None
                else TriState.update(input.license)
            ),
            min_resource=min_resource_state,
            readme=(
                TriState.nop()
                if input.readme is SENTINEL
                else TriState.nullify()
                if input.readme is None
                else TriState.update(input.readme)
            ),
            access_level=(
                OptionalState.nop()
                if input.access_level is SENTINEL
                else OptionalState.update(input.access_level.value)
                if input.access_level is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[ModelCardRow] = Updater(spec=spec, pk_value=input.id)
        result = await self._processors.model_card.update.wait_for_complete(
            UpdateModelCardAction(id=input.id, updater=updater)
        )
        return UpdateModelCardPayload(model_card=self._data_to_node(result.model_card))

    async def delete(self, card_id: UUID) -> DeleteModelCardPayload:
        result = await self._processors.model_card.delete.wait_for_complete(
            DeleteModelCardAction(id=card_id)
        )
        return DeleteModelCardPayload(id=result.model_card.id)

    async def bulk_delete(self, input: DeleteModelCardsInput) -> DeleteModelCardsPayload:
        """Delete multiple model cards by ID."""
        for card_id in input.ids:
            await self._processors.model_card.delete.wait_for_complete(
                DeleteModelCardAction(id=card_id)
            )
        return DeleteModelCardsPayload(deleted_count=len(input.ids))

    async def scan_project(self, project_id: UUID) -> ScanProjectModelCardsPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.model_card.scan.wait_for_complete(
            ScanProjectModelCardsAction(
                project_id=project_id,
                requester_id=me.user_id,
            )
        )
        return ScanProjectModelCardsPayload(
            created_count=result.created_count,
            updated_count=result.updated_count,
            errors=result.errors,
        )

    async def deploy(
        self,
        card_id: UUID,
        input: DeployModelCardInput,
    ) -> DeployModelCardPayload:
        """Create a deployment from a model card using a revision preset.

        The revision preset provides image_id, resource_slots, environ,
        startup_command, and runtime_variant_id. The model card provides
        the model vfolder and project scope. The deployment service's
        _apply_preset() merges preset values into the revision creator.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")

        model_card = await self._get_model_card_data(card_id)

        creator = NewDeploymentCreator(
            metadata=DeploymentMetadata(
                name=f"{model_card.name}-{secrets.token_hex(4)}",
                domain=model_card.domain,
                project=input.project_id,
                resource_group=input.resource_group,
                created_user=me.user_id,
                session_owner=me.user_id,
                created_at=None,
                revision_history_limit=10,
            ),
            replica_spec=ReplicaSpec(replica_count=input.desired_replica_count),
            network=DeploymentNetworkSpec(open_to_public=False),
            model_revision=ModelRevisionCreator(
                image_id=None,
                resource_spec=ResourceSpec(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    resource_slots={},
                ),
                mounts=VFolderMountsCreator(
                    model_vfolder_id=model_card.vfolder_id,
                ),
                execution=ExecutionSpec(runtime_variant=RuntimeVariant("custom")),
                model_definition=None,
                revision_preset_id=input.revision_preset_id,
                auto_activate=True,
            ),
        )

        result = await self._processors.deployment.create_deployment.wait_for_complete(
            CreateDeploymentAction(creator=creator)
        )
        return DeployModelCardPayload(
            deployment_id=result.data.id,
            deployment_name=result.data.metadata.name,
        )

    async def available_presets(
        self,
        model_card_id: UUID,
        input: SearchDeploymentRevisionPresetsInput,
    ) -> SearchDeploymentRevisionPresetsPayload:
        action_result = await self._processors.model_card.available_presets.wait_for_complete(
            AvailablePresetsAction(
                model_card_id=model_card_id,
                search_input=input,
            )
        )
        search_result = action_result.result
        return SearchDeploymentRevisionPresetsPayload(
            items=[DeploymentRevisionPresetAdapter._data_to_node(d) for d in search_result.items],
            total_count=search_result.total_count,
            has_next_page=search_result.has_next_page,
            has_previous_page=search_result.has_previous_page,
        )

    async def _get_model_card_data(self, card_id: UUID) -> ModelCardData:
        """Fetch a single model card by ID."""
        conditions: list[QueryCondition] = [lambda: ModelCardRow.id == card_id]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_model_card_pagination_spec(),
            limit=1,
        )
        result = await self._processors.model_card.search.wait_for_complete(
            SearchModelCardsAction(querier=querier)
        )
        items: list[ModelCardData] = result.items
        if not items:
            raise ModelCardNotFound()
        return items[0]

    def _convert_filter(self, filter_: ModelCardFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.domain_name is not None:
            conditions.append(ModelCardConditions.by_domain(filter_.domain_name))
        if filter_.project_id is not None:
            conditions.append(ModelCardConditions.by_project(filter_.project_id))
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=ModelCardConditions.by_name_contains,
                equals_factory=ModelCardConditions.by_name_equals,
                starts_with_factory=ModelCardConditions.by_name_starts_with,
                ends_with_factory=ModelCardConditions.by_name_ends_with,
            )
            if cond:
                conditions.append(cond)
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        return conditions

    def _convert_orders(self, orders: list[ModelCardOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case ModelCardOrderField.NAME:
                    result.append(ModelCardOrders.name(ascending))
                case ModelCardOrderField.CREATED_AT:
                    result.append(ModelCardOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: ModelCardData) -> ModelCardNode:
        return ModelCardNode(
            id=data.id,
            name=data.name,
            vfolder_id=data.vfolder_id,
            domain_name=data.domain,
            project_id=data.project_id,
            creator_id=data.creator_id,
            metadata=ModelCardMetadata(
                author=data.author,
                title=data.title,
                model_version=data.model_version,
                description=data.description,
                task=data.task,
                category=data.category,
                architecture=data.architecture,
                framework=data.framework,
                label=data.label,
                license=data.license,
            ),
            min_resource=(
                _requirements_to_entries(data.min_resource) if data.min_resource else None
            ),
            readme=data.readme,
            access_level=ModelCardAccessLevel(data.access_level),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
