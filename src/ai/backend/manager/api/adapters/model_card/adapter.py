from __future__ import annotations

import secrets
from collections.abc import Sequence
from typing import assert_never
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    BulkDeleteModelCardsInput,
    CreateModelCardInput,
    DeleteModelCardOptions,
    DeployModelCardInput,
    ModelCardFilter,
    ModelCardOrder,
    ModelCardResourceRequirementFilter,
    ResourceSlotEntryInput,
    ScopedSearchModelCardsInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    BulkDeleteModelCardsPayload,
    BulkDeleteModelCardV2Error,
    CreateModelCardPayload,
    DeleteModelCardPayload,
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
    ModelCardScope,
    ModelCardUsage,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.common.types import MountPermission
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ReplicaSpec,
)
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
    ResourceRequirementEntry,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.model_card.creators import ModelCardCreator
from ai.backend.manager.models.model_card.deprecated_search import (
    ModelCardDeprecatedSearch,
)
from ai.backend.manager.models.model_card.purgers import ModelCardPurger
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.scopes import (
    DomainModelCardTarget,
    ModelCardTarget,
    ProjectModelCardTarget,
    UserModelCardTarget,
)
from ai.backend.manager.models.model_card.searchable_fields import (
    ModelCardResourceRequirementSearchableFields,
    ModelCardSearchableFields,
)
from ai.backend.manager.models.model_card.searchers import (
    ModelCardResourceRequirementSearcher,
    ModelCardSearcher,
)
from ai.backend.manager.models.model_card.updaters import ModelCardUpdater
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.services.deployment.actions.create_deployment import CreateDeploymentAction
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.model_card.actions.bulk_delete import (
    BulkDeleteModelCardAction,
)
from ai.backend.manager.services.model_card.actions.create import CreateModelCardAction
from ai.backend.manager.services.model_card.actions.delete import DeleteModelCardAction
from ai.backend.manager.services.model_card.actions.get import GetModelCardAction
from ai.backend.manager.services.model_card.actions.scan import ScanProjectModelCardsAction
from ai.backend.manager.services.model_card.actions.scoped_search import (
    ScopedSearchModelCardsAction,
)
from ai.backend.manager.services.model_card.actions.scoped_search_requirements import (
    ScopedSearchModelCardResourceRequirementsAction,
)
from ai.backend.manager.services.model_card.actions.search import GlobalSearchModelCardsAction
from ai.backend.manager.services.model_card.actions.update import UpdateModelCardAction
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.types import OptionalState, TriState


def _build_policy_from_strategy_input(
    strategy_input: DeploymentStrategyInput | None,
) -> DeploymentPolicyConfig | None:
    """Convert a DeploymentStrategyInput DTO to DeploymentPolicyConfig.

    Returns ``None`` when the caller did not provide a strategy. The deployment
    service will then fall back to the preset's strategy default (if any).
    """
    if strategy_input is None:
        return None
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    match strategy_input.type:
        case DeploymentStrategy.ROLLING:
            rolling = strategy_input.rolling_update
            if rolling is not None:
                strategy_spec = RollingUpdateSpec(
                    max_surge=rolling.max_surge,
                    max_unavailable=rolling.max_unavailable,
                )
            else:
                strategy_spec = RollingUpdateSpec()
        case DeploymentStrategy.BLUE_GREEN:
            bg = strategy_input.blue_green
            if bg is not None:
                strategy_spec = BlueGreenSpec(
                    auto_promote=bg.auto_promote,
                    promote_delay_seconds=bg.promote_delay_seconds,
                )
            else:
                strategy_spec = BlueGreenSpec()
    return DeploymentPolicyConfig(
        strategy=strategy_input.type,
        strategy_spec=strategy_spec,
    )


_MODEL_CARD_PAGINATION_SPEC = PaginationSpec(
    forward_order=ModelCardSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ModelCardRow.id,
)


def _entries_to_requirements(
    entries: list[ResourceSlotEntryInput],
) -> list[ResourceRequirementEntry]:
    return [
        ResourceRequirementEntry(slot_name=e.resource_type, min_quantity=e.quantity)
        for e in entries
    ]


def _requirements_to_entries(
    reqs: list[ModelCardResourceRequirementData],
) -> list[ResourceSlotEntryInfo]:
    return [ResourceSlotEntryInfo(resource_type=r.slot_name, quantity=r.min_quantity) for r in reqs]


class ModelCardAdapter(BaseAdapter):
    _model_card: ModelCardProcessors
    _deployment: DeploymentProcessors
    _preset: DeploymentRevisionPresetAdapter

    def __init__(
        self,
        model_card: ModelCardProcessors,
        deployment: DeploymentProcessors,
        preset: DeploymentRevisionPresetAdapter,
    ) -> None:
        self._model_card = model_card
        self._deployment = deployment
        self._preset = preset

    async def admin_search(
        self,
        input: SearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        result = await self._model_card.global_search.run(
            GlobalSearchModelCardsAction(
                searcher=GlobalSearcher(
                    used_by=self._usage(input.usage),
                    searcher=self._build_model_card_searcher(input),
                )
            )
        )
        return await self._payload(result)

    def _scope_targets(self, scope: ModelCardScope) -> list[ModelCardTarget]:
        """The scope targets the request named, in the order the input lists them."""
        targets: list[ModelCardTarget] = [
            DomainModelCardTarget(domain_id=DomainID(entry.value)) for entry in scope.domain or ()
        ]
        targets.extend(
            ProjectModelCardTarget(project_id=ProjectID(entry.value))
            for entry in scope.project or ()
        )
        targets.extend(
            UserModelCardTarget(user_id=UserID(entry.value)) for entry in scope.user or ()
        )
        return targets

    def _usage(self, usage: ModelCardUsage | None) -> list[UsedBy]:
        """The uses the request named."""
        if usage is None or usage.uses is None:
            return []
        linked = ModelCardSearchableFields.linked.usage
        return [
            linked.vfolders.uses(VFolderUUID(entity_id)) for entity_id in usage.uses.vfolder or ()
        ]

    def _scoped_search_action(
        self,
        targets: Sequence[ModelCardTarget],
        input: ScopedSearchModelCardsInput | SearchModelCardsInput,
    ) -> ScopedSearchModelCardsAction:
        return ScopedSearchModelCardsAction(
            searcher=ScopedSearcher(
                scopes=targets,
                used_by=self._usage(input.usage),
                searcher=self._build_model_card_searcher(input),
            )
        )

    async def scoped_search(
        self,
        input: ScopedSearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        """Search the model cards the named scopes reach, combined with OR."""
        result = await self._model_card.scoped_search.run(
            self._scoped_search_action(self._scope_targets(input.scope), input)
        )
        return await self._payload(result)

    async def ownership_search(
        self,
        project_id: UUID | None,
        user_id: UUID | None,
        input: SearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        """Search the model cards of the project or the user that owns a vfolder.

        The vfolder itself travels on ``input.usage`` as a use, so the caller has to be
        able to read it as well.
        """
        # A project folder names its project, a personal one its owner and their personal
        # project, so at least one of the two is always given.
        targets: list[ModelCardTarget] = []
        if project_id is not None:
            targets.append(ProjectModelCardTarget(project_id=project_id))
        if user_id is not None:
            targets.append(UserModelCardTarget(user_id=UserID(user_id)))
        result = await self._model_card.scoped_search.run(
            self._scoped_search_action(targets, input)
        )
        return await self._payload(result)

    async def project_search(
        self,
        project_id: UUID,
        input: SearchModelCardsInput,
    ) -> SearchModelCardsPayload:
        result = await self._model_card.scoped_search.run(
            self._scoped_search_action(
                [ProjectModelCardTarget(project_id=ProjectID(project_id))], input
            )
        )
        return await self._payload(result)

    def _build_model_card_searcher(
        self, input: ScopedSearchModelCardsInput | SearchModelCardsInput
    ) -> ModelCardSearcher:
        return self._build_searcher(
            ModelCardSearcher,
            conditions=self._convert_filter(input.filter) if input.filter else [],
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_MODEL_CARD_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    async def _payload(self, result: BatchOpsResult[ModelCardData]) -> SearchModelCardsPayload:
        return SearchModelCardsPayload(
            items=await self._nodes_with_min_resources(result.items),
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, card_id: UUID) -> ModelCardNode:
        result = await self._model_card.get.run(
            GetModelCardAction(model_card_id=ModelCardID(card_id))
        )
        return (await self._nodes_with_min_resources([result.data]))[0]

    async def create(
        self,
        input: CreateModelCardInput,
    ) -> CreateModelCardPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        min_resource = _entries_to_requirements(input.min_resource) if input.min_resource else []
        creator = ModelCardCreator(
            name=input.name,
            vfolder_id=input.vfolder_id,
            domain=input.domain_name or me.domain_name,
            project_id=ProjectID(input.model_store_project_id),
            creator_id=UserID(me.user_id),
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
            readme=input.readme,
            access_level=input.access_level.value,
        )
        result = await self._model_card.create.run(
            CreateModelCardAction(creator=creator, min_resource=min_resource)
        )
        return CreateModelCardPayload(
            model_card=(await self._nodes_with_min_resources([result.data]))[0]
        )

    async def update(
        self,
        input: UpdateModelCardInput,
    ) -> UpdateModelCardPayload:
        updater = ModelCardUpdater(
            card_id=ModelCardID(input.id),
            name=OptionalState.from_unset(input.name),
            author=TriState.from_unset(input.author),
            title=TriState.from_unset(input.title),
            model_version=TriState.from_unset(input.model_version),
            description=TriState.from_unset(input.description),
            task=TriState.from_unset(input.task),
            category=TriState.from_unset(input.category),
            architecture=TriState.from_unset(input.architecture),
            framework=OptionalState.from_unset(input.framework),
            label=OptionalState.from_unset(input.label),
            license=TriState.from_unset(input.license),
            min_resource=TriState.from_unset(input.min_resource).map(_entries_to_requirements),
            readme=TriState.from_unset(input.readme),
            access_level=OptionalState.from_unset(input.access_level).map(lambda x: x.value),
        )
        result = await self._model_card.update.run(
            UpdateModelCardAction(model_card_id=ModelCardID(input.id), updater=updater)
        )
        return UpdateModelCardPayload(
            model_card=(await self._nodes_with_min_resources([result.model_card]))[0]
        )

    async def delete(
        self,
        card_id: UUID,
        options: DeleteModelCardOptions,
    ) -> DeleteModelCardPayload:
        result = await self._model_card.delete.run(
            DeleteModelCardAction(
                model_card_id=ModelCardID(card_id),
                purger=ModelCardPurger(card_id=ModelCardID(card_id)),
                options=options,
            )
        )
        return DeleteModelCardPayload(id=result.id)

    async def admin_bulk_delete(
        self,
        input: BulkDeleteModelCardsInput,
        options: DeleteModelCardOptions,
    ) -> BulkDeleteModelCardsPayload:
        """Bulk-delete model cards and surface per-card success/failure breakdown."""
        result = await self._model_card.bulk_delete.run(
            BulkDeleteModelCardAction(
                ids=[ModelCardID(card_id) for card_id in input.ids],
                options=options,
            )
        )
        return BulkDeleteModelCardsPayload(
            successes=[UUID(str(card_id)) for card_id in result.values()],
            failed=[
                BulkDeleteModelCardV2Error(card_id=UUID(str(card_id)), message=str(error))
                for card_id, error in result.errors().items()
            ],
        )

    async def scan_project(self, project_id: UUID) -> ScanProjectModelCardsPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._model_card.scan.run(
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
        startup_command, runtime_variant_id, and (optionally) deployment-level
        defaults (open_to_public, replica_count, revision_history_limit,
        deployment_strategy). The model card provides the model vfolder and
        project scope. The deployment service's ``_apply_preset`` and
        ``_apply_deployment_level_preset`` merge preset values into the
        creator; any explicit override on ``DeployModelCardInput`` takes
        precedence over the preset default.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")

        model_card = await self._get_model_card_data(card_id)

        # Build optional override values. Leaving these as ``None`` signals the
        # deployment service to fall back to the preset default, then to the
        # system default.
        replica_spec: ReplicaSpec | None = None
        if input.replica_count is not None:
            replica_spec = ReplicaSpec(replica_count=input.replica_count)
        elif input.desired_replica_count != 1:
            # Preserve prior behavior: when the caller specified a non-default
            # ``desired_replica_count``, honor it as an explicit replica count.
            replica_spec = ReplicaSpec(replica_count=input.desired_replica_count)

        network_spec: DeploymentNetworkSpec | None = None
        if input.open_to_public is not None:
            network_spec = DeploymentNetworkSpec(open_to_public=input.open_to_public)

        policy = _build_policy_from_strategy_input(input.deployment_strategy)

        creator = NewDeploymentCreator(
            metadata=DeploymentMetadata(
                name=f"{model_card.name}-{secrets.token_hex(4)}",
                domain=model_card.domain,
                project=input.project_id,
                resource_group=input.resource_group,
                created_user=me.user_id,
                session_owner=me.user_id,
                created_at=None,
                revision_history_limit=input.revision_history_limit,
            ),
            replica_spec=replica_spec,
            network=network_spec,
            # ``resource_spec`` and ``execution`` are intentionally omitted so
            # the revision preset drives image / resource_slots / cluster /
            # runtime_variant. Hard-coding values here would silently override
            # the preset.
            model_revision=ModelRevisionCreator(
                image_id=None,
                mounts=VFolderMountsCreator(
                    model_vfolder_id=model_card.vfolder_id,
                    model_definition_path=None,
                    model_mount_destination="/models",
                    extra_mounts=[],
                    # model-card deploy always mounts the model read-only.
                    model_mount_perm=MountPermission.READ_ONLY,
                ),
                revision_preset_id=input.revision_preset_id,
            ),
            policy=policy,
        )

        result = await self._deployment.create_deployment.run(
            CreateDeploymentAction(
                project_id=ProjectID(creator.metadata.project),
                creator=creator,
                auto_activate=True,
            )
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
        """The presets the card can be deployed on, read as a preset search."""
        return await self._preset.available_presets(ModelCardID(model_card_id), input)

    async def _get_model_card_data(self, card_id: UUID) -> ModelCardData:
        """Fetch a single model card by ID."""
        result = await self._model_card.get.run(
            GetModelCardAction(model_card_id=ModelCardID(card_id))
        )
        return result.data

    def _convert_filter(self, f: ModelCardFilter) -> list[QueryCondition]:
        fields = ModelCardSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(f.entity_id, fields.id.filter),
            *self.apply_string_filter(f.name, fields.name.filter),
            *self.apply_uuid_filter(f.vfolder_id, fields.vfolder_id.filter),
            *self.apply_string_filter(f.domain_name, fields.domain.filter),
            *self.apply_uuid_filter(f.project_id, fields.project_id.filter),
            *self.apply_uuid_filter(f.creator_id, fields.creator_id.filter),
            *self.apply_string_filter(f.author, fields.author.filter),
            *self.apply_string_filter(f.title, fields.title.filter),
            *self.apply_string_filter(f.model_version, fields.model_version.filter),
            *self.apply_string_filter(f.task, fields.task.filter),
            *self.apply_string_filter(f.category, fields.category.filter),
            *self.apply_string_filter(f.architecture, fields.architecture.filter),
            *self.apply_string_filter(f.license, fields.license.filter),
            *self.apply_string_filter(f.access_level, fields.access_level.filter),
            *self._storage_host_conditions(f.storage_host),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_nullable_datetime_filter(f.updated_at, fields.updated_at.filter),
            *self.apply_to_many_filter(
                f.min_resource,
                ModelCardSearchableFields.nested.min_resource.correlation,
                self._convert_requirement_filter,
            ),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _storage_host_conditions(self, host: StringFilter | None) -> list[QueryCondition]:
        """The host of the vfolder the card is built on.

        Deprecated. Callers move to a vfolder search by host followed by
        ``usage: { uses: { vfolder } }``; the reason it is not simply dropped is in
        ``models/model_card/deprecated_search.py``.
        """
        if host is None:
            return []
        storage_host = ModelCardDeprecatedSearch.storage_host
        matches = self.apply_string_filter(host, storage_host.conditions)
        if not matches:
            return []
        return [storage_host.matching(matches)]

    def _convert_requirement_filter(
        self, f: ModelCardResourceRequirementFilter
    ) -> list[QueryCondition]:
        fields = ModelCardResourceRequirementSearchableFields.own
        return [
            *self.apply_string_filter(f.slot_name, fields.slot_name.filter),
            *self.apply_decimal_filter(f.min_quantity, fields.min_quantity.filter),
        ]

    def _convert_orders(self, orders: list[ModelCardOrder]) -> list[QueryOrder]:
        return [self._convert_order(order) for order in orders]

    def _convert_order(self, order: ModelCardOrder) -> QueryOrder:
        fields = ModelCardSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ModelCardOrderField.ENTITY_ID:
                return fields.id.order.apply(ascending)
            case ModelCardOrderField.NAME:
                return fields.name.order.apply(ascending)
            case ModelCardOrderField.VFOLDER_ID:
                return fields.vfolder_id.order.apply(ascending)
            case ModelCardOrderField.DOMAIN_NAME:
                return fields.domain.order.apply(ascending)
            case ModelCardOrderField.PROJECT_ID:
                return fields.project_id.order.apply(ascending)
            case ModelCardOrderField.CREATOR_ID:
                return fields.creator_id.order.apply(ascending)
            case ModelCardOrderField.AUTHOR:
                return fields.author.order.apply(ascending)
            case ModelCardOrderField.TITLE:
                return fields.title.order.apply(ascending)
            case ModelCardOrderField.MODEL_VERSION:
                return fields.model_version.order.apply(ascending)
            case ModelCardOrderField.TASK:
                return fields.task.order.apply(ascending)
            case ModelCardOrderField.CATEGORY:
                return fields.category.order.apply(ascending)
            case ModelCardOrderField.ARCHITECTURE:
                return fields.architecture.order.apply(ascending)
            case ModelCardOrderField.LICENSE:
                return fields.license.order.apply(ascending)
            case ModelCardOrderField.ACCESS_LEVEL:
                return fields.access_level.order.apply(ascending)
            case ModelCardOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case ModelCardOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)
            case _:
                assert_never(order.field)

    async def _nodes_with_min_resources(
        self, cards: Sequence[ModelCardData]
    ) -> list[ModelCardNode]:
        """Convert cards to nodes with their requirements filled in, in one extra read."""
        by_card = await self.min_resources([card.id for card in cards])
        return [self._data_to_node(card, by_card.get(card.id)) for card in cards]

    async def min_resources(
        self, card_ids: Sequence[UUID]
    ) -> dict[UUID, list[ResourceSlotEntryInfo]]:
        """Read the minimum resource requirements of the named cards.

        A second read because the requirements are their own table. GraphQL calls it
        from the field resolver, so a query that skips ``minResource`` skips this.
        """
        if not card_ids:
            return {}
        result = await self._model_card.scoped_search_requirements.run(
            ScopedSearchModelCardResourceRequirementsAction(
                card_ids=[ModelCardID(card_id) for card_id in card_ids],
                searcher=ModelCardResourceRequirementSearcher(pagination=NoPagination()),
            )
        )
        by_card: dict[UUID, list[ModelCardResourceRequirementData]] = {}
        for requirement in result.items:
            by_card.setdefault(requirement.model_card_id, []).append(requirement)
        return {card_id: _requirements_to_entries(reqs) for card_id, reqs in by_card.items()}

    @staticmethod
    def _data_to_node(
        data: ModelCardData,
        min_resource: list[ResourceSlotEntryInfo] | None = None,
    ) -> ModelCardNode:
        return ModelCardNode(
            id=data.id,
            entity_id=data.entity_id(),
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
            min_resource=min_resource,
            readme=data.readme,
            access_level=ModelCardAccessLevel(data.access_level),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
