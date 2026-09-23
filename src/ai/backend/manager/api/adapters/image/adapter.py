"""Image domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from functools import lru_cache
from typing import assert_never

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    ImageAliasFilterInputDTO,
    ImageAliasOrderByInputDTO,
    ImageFilterInputDTO,
    ImageOrderByInputDTO,
    PurgeImageInput,
    RestoreImageInput,
    ScopedSearchImagesInput,
    SearchImageAliasesInput,
    UpdateImageInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
    AliasImagePayload,
    ForgetImagePayload,
    ImageAliasNode,
    ImageIdentityInfoDTO,
    ImageMetadataInfoDTO,
    ImageNode,
    ImageRequirementsInfoDTO,
    PurgeImagePayload,
    RestoreImagePayload,
    ScopedSearchImagesPayload,
    SearchImageAliasesPayload,
    UpdateImagePayload,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageAliasOrderField,
    ImageLabelInfo,
    ImageOrderField,
    ImageResourceLimitGQLInfo,
    ImageResourceLimitInfo,
    ImageScope,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
    ImageUsage,
    OrderDirection,
)
from ai.backend.common.types import ImageID
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.image.types import ImageAliasData, ImageData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.image import ImageType
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.image.scopes import (
    ContainerRegistryImageTarget,
    DomainImageTarget,
    ImageTarget,
    ProjectImageTarget,
    PublicImageTarget,
    UserImageTarget,
)
from ai.backend.manager.models.image.searchable_fields import (
    ImageAliasSearchableFields,
    ImageSearchableFields,
)
from ai.backend.manager.models.image.searchers import ImageAliasSearcher, ImageSearcher
from ai.backend.manager.models.image.updaters import ImageUpdate
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.services.image.actions.alias_image import AliasImageByIdAction
from ai.backend.manager.services.image.actions.bulk_get import BulkGetImagesAction
from ai.backend.manager.services.image.actions.bulk_get_aliases import BulkGetImageAliasesAction
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.restore_image import RestoreImageByIdAction
from ai.backend.manager.services.image.actions.scoped_search import (
    ScopedSearchImagesAction,
)
from ai.backend.manager.services.image.actions.search_aliases import SearchAliasesAction
from ai.backend.manager.services.image.actions.search_image_aliases import (
    SearchImageAliasesAction,
)
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction
from ai.backend.manager.services.image.actions.update_image_by_id import UpdateImageByIdAction
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.types import OptionalState, TriState


@lru_cache(maxsize=1)
def _get_image_pagination_spec() -> PaginationSpec:
    """Get pagination spec for Image queries."""
    return PaginationSpec(
        forward_order=ImageSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=ImageRow.id,
    )


@lru_cache(maxsize=1)
def _get_alias_pagination_spec() -> PaginationSpec:
    """Get pagination spec for ImageAlias queries."""
    return PaginationSpec(
        forward_order=ImageAliasSearchableFields.own.alias.order.apply(ascending=True),
        cursor_column=ImageAliasRow.id,
    )


class ImageAdapter(BaseAdapter):
    """Adapter for image domain operations."""

    _image: ImageProcessors

    def __init__(self, image: ImageProcessors) -> None:
        self._image = image

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(
        self, image_ids: Sequence[ImageID]
    ) -> list[ImageNode | Exception | None]:
        """Batch load images by their IDs for DataLoader use, checked per image."""
        if not image_ids:
            return []
        result = await self._image.bulk_get.run(BulkGetImagesAction(ids=list(image_ids)))
        return [
            self._data_to_dto(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def batch_load_aliases_by_ids(
        self, alias_ids: Sequence[ImageAliasID]
    ) -> list[ImageAliasNode | Exception | None]:
        """Batch load image aliases for DataLoader use, checked per owning image."""
        if not alias_ids:
            return []
        ids = [ImageAliasID(alias_id) for alias_id in alias_ids]
        return await self.batch_load_fields(
            self._image.bulk_get_aliases,
            BulkGetImageAliasesAction(ids=ids),
            ids,
            self._alias_data_to_dto,
        )

    # ------------------------------------------------------------------ search

    async def admin_search(self, input: AdminSearchImagesInput) -> AdminSearchImagesPayload:
        """Search images with admin scope, by cursor or by offset as the request names."""
        options = PaginationOptions(
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        limit = input.limit
        if limit is None and not options.has_cursor:
            limit = DEFAULT_PAGE_LIMIT
        action_result = await self._image.search_images.run(
            SearchImagesAction(
                searcher=GlobalSearcher(
                    used_by=self._usage(input.usage),
                    searcher=self._build_image_searcher(input, limit=limit),
                )
            )
        )

        return AdminSearchImagesPayload(
            items=[self._data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _scope_targets(self, scope: ImageScope) -> list[ImageTarget]:
        """The scope targets the request named, in the order the input lists them."""
        targets: list[ImageTarget] = [
            DomainImageTarget(domain_id=DomainID(entry.value)) for entry in scope.domain or ()
        ]
        targets.extend(
            ProjectImageTarget(project_id=ProjectID(entry.value)) for entry in scope.project or ()
        )
        targets.extend(UserImageTarget(user_id=UserID(entry.value)) for entry in scope.user or ())
        targets.extend(
            ContainerRegistryImageTarget(registry_id=ContainerRegistryID(entry.value))
            for entry in scope.container_registry or ()
        )
        if scope.public:
            targets.append(PublicImageTarget())
        return targets

    def _usage(self, usage: ImageUsage | None) -> list[UsedBy]:
        """The uses the request named, sessions before deployments."""
        if usage is None or usage.used_by is None:
            return []
        used_by = usage.used_by
        linked = ImageSearchableFields.linked.usage
        return [
            *(linked.sessions.used_by(SessionID(entity_id)) for entity_id in used_by.session or ()),
            *(
                linked.deployments.used_by(DeploymentID(entity_id))
                for entity_id in used_by.deployment or ()
            ),
        ]

    def _build_image_searcher(
        self,
        input: AdminSearchImagesInput | ScopedSearchImagesInput,
        limit: int | None = None,
    ) -> ImageSearcher:
        conditions = self._convert_filter(input.filter) if input.filter else []
        return self._build_searcher(
            ImageSearcher,
            conditions=conditions,
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_get_image_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit if limit is None else limit,
            offset=input.offset,
        )

    async def scoped_search(self, input: ScopedSearchImagesInput) -> ScopedSearchImagesPayload:
        """Search the images the named scopes reach, combined with OR."""
        action_result = await self._image.scoped_search.run(
            ScopedSearchImagesAction(
                searcher=ScopedSearcher(
                    scopes=self._scope_targets(input.scope),
                    used_by=self._usage(input.usage),
                    searcher=self._build_image_searcher(input),
                )
            )
        )
        return ScopedSearchImagesPayload(
            items=[self._data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_images_gql(
        self,
        input: AdminSearchImagesInput,
    ) -> AdminSearchImagesPayload:
        """Search images with cursor or offset pagination for GQL resolvers."""
        action_result = await self._image.search_images.run(
            SearchImagesAction(
                searcher=GlobalSearcher(
                    used_by=self._usage(input.usage),
                    searcher=self._build_image_searcher(input),
                )
            )
        )

        return AdminSearchImagesPayload(
            items=[self._data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_image_aliases(
        self,
        input: AdminSearchImageAliasesInput,
    ) -> AdminSearchImageAliasesPayload:
        """Search image aliases with cursor or offset pagination for GQL resolvers."""
        conditions = self._convert_alias_filter(input.filter) if input.filter else []
        orders = self._convert_alias_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_alias_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        action_result = await self._image.search_aliases.run(SearchAliasesAction(querier=querier))

        return AdminSearchImageAliasesPayload(
            items=[self._alias_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def scoped_search_aliases(
        self, image_id: ImageID, input: SearchImageAliasesInput
    ) -> SearchImageAliasesPayload:
        """Search the aliases of one image, answered for by the caller's read on it."""
        searcher = self._build_searcher(
            ImageAliasSearcher,
            conditions=self._convert_alias_filter(input.filter) if input.filter else [],
            orders=self._convert_alias_orders(input.order) if input.order else [],
            pagination_spec=_get_alias_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._image.search_image_aliases.run(
            SearchImageAliasesAction(image_id=image_id, searcher=searcher)
        )
        return SearchImageAliasesPayload(
            items=[self._alias_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # ------------------------------------------------------------------ mutations

    async def admin_forget(self, input: ForgetImageInput) -> ForgetImagePayload:
        """Forget (soft-delete) an image by ID."""
        result = await self._image.forget_image_by_id.run(
            ForgetImageByIdAction(image_id=ImageID(input.image_id))
        )
        return ForgetImagePayload(item=self._data_to_dto(result.image))

    async def admin_restore(self, input: RestoreImageInput) -> RestoreImagePayload:
        """Restore a forgotten (soft-deleted) image by ID."""
        result = await self._image.restore_image_by_id.run(
            RestoreImageByIdAction(image_id=ImageID(input.image_id))
        )
        return RestoreImagePayload(item=self._data_to_dto(result.image))

    async def admin_purge(self, input: PurgeImageInput) -> PurgeImagePayload:
        """Purge (hard-delete) an image by ID."""
        result = await self._image.purge_image_by_id.run(
            PurgeImageByIdAction(image_id=ImageID(input.image_id))
        )
        return PurgeImagePayload(item=self._data_to_dto(result.image))

    async def admin_alias(self, input: AliasImageInput) -> AliasImagePayload:
        """Create an alias for an image."""
        result = await self._image.alias_image_by_id.run(
            AliasImageByIdAction(image_id=ImageID(input.image_id), alias=input.alias)
        )
        return AliasImagePayload(
            alias_id=result.image_alias.id,
            alias=result.image_alias.alias,
            image_id=result.image_id,
        )

    async def admin_dealias(self, input: DealiasImageInput) -> AliasImagePayload:
        """Remove an image alias."""
        result = await self._image.dealias_image.run(DealiasImageAction(alias=input.alias))
        return AliasImagePayload(
            alias_id=result.image_alias.id,
            alias=result.image_alias.alias,
            image_id=result.image_id,
        )

    async def admin_update(self, input: UpdateImageInput) -> UpdateImagePayload:
        """Update an image by ID (superadmin only)."""
        update = ImageUpdate(
            name=OptionalState.from_unset(input.name),
            registry=OptionalState.from_unset(input.registry),
            image=OptionalState.from_unset(input.image),
            tag=OptionalState.from_unset(input.tag),
            architecture=OptionalState.from_unset(input.architecture),
            is_local=OptionalState.from_unset(input.is_local),
            size_bytes=OptionalState.from_unset(input.size_bytes),
            image_type=OptionalState.from_unset(input.type).map(ImageType),
            config_digest=OptionalState.from_unset(input.config_digest),
            labels=OptionalState.from_unset(input.labels),
            accelerators=TriState.from_unset(input.supported_accelerators),
            resources=OptionalState.from_unset(input.resource_limits),
        )
        result = await self._image.update_image_by_id.run(
            UpdateImageByIdAction(image_id=ImageID(input.image_id), update=update)
        )
        return UpdateImagePayload(item=self._data_to_dto(result.image))

    # ------------------------------------------------------------------ querier builders

    def _convert_filter(self, filter: ImageFilterInputDTO) -> list[QueryCondition]:
        fields = ImageSearchableFields.own
        alias_fields = ImageAliasSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_string_filter(filter.architecture, fields.architecture.filter),
            *self.apply_uuid_filter(filter.registry_id, fields.registry_id.filter),
            *self.apply_enum_filter(filter.status, fields.status.filter),
            *self.apply_string_filter(filter.image, fields.image.filter),
            *self.apply_string_filter(filter.registry, fields.registry.filter),
            *self.apply_string_filter(filter.project, fields.project.filter),
            *self.apply_string_filter(filter.tag, fields.tag.filter),
            *self.apply_string_filter(filter.config_digest, fields.config_digest.filter),
            *self.apply_string_filter(filter.accelerators, fields.accelerators.filter),
            *self.apply_int_filter(filter.size_bytes, fields.size_bytes.filter),
            *self.apply_bool_filter(filter.is_local, fields.is_local.filter),
            *self.apply_enum_filter(filter.type, fields.type.filter),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.last_used, fields.last_used_at.filter),
            *self.apply_to_many_filter(
                filter.labels,
                ImageSearchableFields.nested.labels.correlation,
                self._convert_entity_label_filter,
            ),
        ]
        if filter.alias is not None:
            alias_conditions = self.apply_string_filter(
                filter.alias.alias, alias_fields.alias.filter
            )
            if alias_conditions:
                conditions.append(
                    ImageSearchableFields.nested.aliases.correlation.some(alias_conditions)
                )

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))

        if filter.OR:
            or_sub: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub.extend(self._convert_filter(sub_filter))
            if or_sub:
                conditions.append(combine_conditions_or(or_sub))

        if filter.NOT:
            not_sub: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub.extend(self._convert_filter(sub_filter))
            if not_sub:
                conditions.append(negate_conditions(not_sub))

        return conditions

    def _convert_alias_filter(self, filter: ImageAliasFilterInputDTO) -> list[QueryCondition]:
        fields = ImageAliasSearchableFields.own
        conditions = [
            *self.apply_string_filter(filter.alias, fields.alias.filter),
            *self.apply_uuid_filter(filter.image_id, fields.image_id.filter),
            *self.apply_uuid_filter(filter.field_id, fields.id.filter),
        ]

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_alias_filter(sub_filter))

        if filter.OR:
            or_sub: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub.extend(self._convert_alias_filter(sub_filter))
            if or_sub:
                conditions.append(combine_conditions_or(or_sub))

        if filter.NOT:
            not_sub: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub.extend(self._convert_alias_filter(sub_filter))
            if not_sub:
                conditions.append(negate_conditions(not_sub))

        return conditions

    def _convert_orders(self, orders: list[ImageOrderByInputDTO]) -> list[QueryOrder]:
        return [self._convert_order(order) for order in orders]

    def _convert_order(self, order: ImageOrderByInputDTO) -> QueryOrder:
        fields = ImageSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ImageOrderField.NAME:
                return fields.name.order.apply(ascending)
            case ImageOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case ImageOrderField.LAST_USED:
                return fields.last_used_at.order.apply(ascending)
            case ImageOrderField.ENTITY_ID:
                return fields.id.order.apply(ascending)
            case ImageOrderField.IMAGE:
                return fields.image.order.apply(ascending)
            case ImageOrderField.PROJECT:
                return fields.project.order.apply(ascending)
            case ImageOrderField.TAG:
                return fields.tag.order.apply(ascending)
            case ImageOrderField.REGISTRY:
                return fields.registry.order.apply(ascending)
            case ImageOrderField.REGISTRY_ID:
                return fields.registry_id.order.apply(ascending)
            case ImageOrderField.ARCHITECTURE:
                return fields.architecture.order.apply(ascending)
            case ImageOrderField.CONFIG_DIGEST:
                return fields.config_digest.order.apply(ascending)
            case ImageOrderField.SIZE_BYTES:
                return fields.size_bytes.order.apply(ascending)
            case ImageOrderField.IS_LOCAL:
                return fields.is_local.order.apply(ascending)
            case ImageOrderField.TYPE:
                return fields.type.order.apply(ascending)
            case ImageOrderField.STATUS:
                return fields.status.order.apply(ascending)
            case ImageOrderField.ACCELERATORS:
                return fields.accelerators.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _convert_alias_orders(self, orders: list[ImageAliasOrderByInputDTO]) -> list[QueryOrder]:
        return [self._convert_alias_order(order) for order in orders]

    def _convert_alias_order(self, order: ImageAliasOrderByInputDTO) -> QueryOrder:
        fields = ImageAliasSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ImageAliasOrderField.ALIAS:
                return fields.alias.order.apply(ascending)
            case ImageAliasOrderField.FIELD_ID:
                return fields.id.order.apply(ascending)
            case _:
                assert_never(order.field)

    @staticmethod
    def _convert_max(value: Decimal | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return None if value.is_infinite() else str(value)
        return str(value)

    def _data_to_dto(self, data: ImageData) -> ImageNode:
        """Convert data layer type to Pydantic DTO."""
        status = ImageStatusType(data.status.value)
        labels = [ImageLabelInfo(key=k, value=v) for k, v in data.labels.label_data.items()]
        tags = [ImageTagInfo(key=e.key, value=e.value) for e in data.tags]
        resource_limits_flat = [
            ImageResourceLimitInfo(
                key=rl.key,
                min=str(rl.min),
                max=self._convert_max(rl.max),
            )
            for rl in data.resource_limits
        ]
        accelerators = data.accelerators
        accelerator_list = (
            [a.strip() for a in accelerators.split(",") if a.strip()] if accelerators else ["*"]
        )
        resource_limits_gql = [
            ImageResourceLimitGQLInfo(
                key=rl.key,
                min=str(rl.min),
                max=str(rl.max) if rl.max is not None else "Infinity",
            )
            for rl in data.resource_limits
        ]
        return ImageNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=str(data.name),
            image=data.image,
            registry=data.registry,
            registry_id=ContainerRegistryID(data.registry_id),
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=ImageTypeEnum(data.type.value),
            status=status,
            labels=labels,
            tags=tags,
            resource_limits=resource_limits_flat,
            accelerators=accelerators,
            config_digest=data.config_digest,
            is_local=data.is_local,
            created_at=data.created_at,
            last_used_at=data.last_used_at,
            identity=ImageIdentityInfoDTO(
                canonical_name=str(data.name),
                namespace=data.image,
                architecture=data.architecture,
            ),
            metadata=ImageMetadataInfoDTO(
                digest=data.config_digest,
                size_bytes=data.size_bytes,
                size_v2=str(data.size_bytes),
                created_at=data.created_at,
                last_used_at=data.last_used_at,
                tags=tags,
                labels=labels,
                status=status,
            ),
            requirements=ImageRequirementsInfoDTO(
                supported_accelerators=accelerator_list,
                resource_limits=resource_limits_gql,
            ),
        )

    @staticmethod
    def _alias_data_to_dto(data: ImageAliasData) -> ImageAliasNode:
        """Convert alias data layer type to Pydantic DTO."""
        return ImageAliasNode(
            id=data.id,
            field_id=data.id,
            alias=data.alias,
        )
