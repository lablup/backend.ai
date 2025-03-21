import logging
from typing import Any, MutableMapping

import sqlalchemy as sa
from graphql import Undefined

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.agent.response import PurgeImageResponse
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import AgentId, ImageAlias
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ImageNotFound
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.models.base import set_if_set
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageRow,
    ImageStatus,
    rescan_images,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
    AliasImageActionValueError,
)
from ai.backend.manager.services.image.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
    ClearImagesActionValueError,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionNoSuchAliasError,
    DealiasImageActionResult,
    DealiasImageActionValueError,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionGenericForbiddenError,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageActionByIdGenericForbiddenError,
    ForgetImageActionByIdObjectNotFoundError,
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionResult,
    ModifyImageActionUnknownImageReferenceError,
    ModifyImageActionValueError,
)
from ai.backend.manager.services.image.actions.preload_image import (
    PreloadImageAction,
    PreloadImageActionResult,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageActionByIdGenericForbiddenError,
    PurgeImageActionByIdObjectNotFoundError,
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImagesAction,
    PurgeImagesActionResult,
)
from ai.backend.manager.services.image.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)
from ai.backend.manager.services.image.actions.unload_image import (
    UnloadImageAction,
    UnloadImageActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionGenericForbiddenError,
    UntagImageFromRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ImageService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry

    def __init__(self, db: ExtendedAsyncSAEngine, agent_registry: AgentRegistry) -> None:
        self._db = db
        self._agent_registry = agent_registry

    async def forget_image(self, action: ForgetImageAction) -> ForgetImageActionResult:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(action.reference, action.architecture),
                    ImageAlias(action.reference),
                ],
            )
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(action.user_id):
                    raise ForgetImageActionGenericForbiddenError()
            await image_row.mark_as_deleted(session)
        return ForgetImageActionResult(image=image_row)

    async def forget_image_by_id(
        self, action: ForgetImageByIdAction
    ) -> ForgetImageByIdActionResult:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.get(session, action.image_id, load_aliases=True)
            if not image_row:
                raise ForgetImageActionByIdObjectNotFoundError()
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(action.user_id):
                    raise ForgetImageActionByIdGenericForbiddenError()
            await image_row.mark_as_deleted(session)
            return ForgetImageByIdActionResult(image=image_row)

    async def alias_image(self, action: AliasImageAction) -> AliasImageActionResult:
        try:
            async with self._db.begin_session() as session:
                try:
                    image_row = await ImageRow.resolve(
                        session, [ImageIdentifier(action.image_canonical, action.architecture)]
                    )
                except UnknownImageReference:
                    raise ImageNotFound
                else:
                    image_alias = ImageAliasRow(alias=action.alias, image_id=image_row.id)
                    image_row.aliases.append(image_alias)
        except ValueError:
            raise AliasImageActionValueError
        return AliasImageActionResult(image_id=image_alias.image_id, image_alias=image_alias)

    async def dealias_image(self, action: DealiasImageAction) -> DealiasImageActionResult:
        try:
            async with self._db.begin_session() as session:
                existing_alias = await session.scalar(
                    sa.select(ImageAliasRow).where(ImageAliasRow.alias == action.alias),
                )
                if existing_alias is None:
                    raise DealiasImageActionNoSuchAliasError()
                await session.delete(existing_alias)
        except ValueError:
            raise DealiasImageActionValueError()
        return DealiasImageActionResult(
            image_id=existing_alias.image_id, image_alias=existing_alias
        )

    async def clear_images(self, action: ClearImagesAction) -> ClearImagesActionResult:
        try:
            async with self._db.begin_session() as session:
                await session.execute(
                    sa.update(ImageRow)
                    .where(ImageRow.registry == action.registry)
                    .where(ImageRow.status != ImageStatus.DELETED)
                    .values(status=ImageStatus.DELETED)
                )
        except ValueError:
            raise ClearImagesActionValueError()
        return ClearImagesActionResult()

    async def modify_image(self, action: ModifyImageAction) -> ModifyImageActionResult:
        data: MutableMapping[str, Any] = {}
        props = action.props

        set_if_set(props, data, "name")
        set_if_set(props, data, "registry")
        set_if_set(props, data, "image")
        set_if_set(props, data, "tag")
        set_if_set(props, data, "architecture")
        set_if_set(props, data, "is_local")
        set_if_set(props, data, "size_bytes")
        set_if_set(props, data, "type")
        set_if_set(props, data, "digest", target_key="config_digest")
        set_if_set(
            props,
            data,
            "supported_accelerators",
            clean_func=lambda v: ",".join(v),
            target_key="accelerators",
        )
        set_if_set(props, data, "labels", clean_func=lambda v: {pair.key: pair.value for pair in v})

        # TODO: graphql Undefined를 여기서 쓰면 안 될 듯.
        if props.resource_limits is not Undefined:
            resources_data = {}
            for limit_option in props.resource_limits:
                limit_data = {}
                if (
                    limit_option.min is not None
                    and limit_option.min is not Undefined
                    and len(limit_option.min) > 0
                ):
                    limit_data["min"] = limit_option.min
                if (
                    limit_option.max is not None
                    and limit_option.max is not Undefined
                    and len(limit_option.max) > 0
                ):
                    limit_data["max"] = limit_option.max
                resources_data[limit_option.key] = limit_data
            data["resources"] = resources_data

        try:
            async with self._db.begin_session() as db_sess:
                try:
                    image_row = await ImageRow.resolve(
                        db_sess,
                        [
                            ImageIdentifier(action.target, action.architecture),
                            ImageAlias(action.target),
                        ],
                    )
                except UnknownImageReference:
                    raise ModifyImageActionUnknownImageReferenceError
                for k, v in data.items():
                    setattr(image_row, k, v)
        except ValueError:
            raise ModifyImageActionValueError

        return ModifyImageActionResult(image=image_row)

    async def preload_image(self, action: PreloadImageAction) -> PreloadImageActionResult:
        raise NotImplementedError

    async def unload_image(self, action: UnloadImageAction) -> UnloadImageActionResult:
        raise NotImplementedError

    async def purge_image_by_id(self, action: PurgeImageByIdAction) -> PurgeImageByIdActionResult:
        async with self._db.begin_session() as db_session:
            image_row = await ImageRow.get(db_session, action.image_id, load_aliases=True)
            if not image_row:
                raise PurgeImageActionByIdObjectNotFoundError()
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(action.user_id):
                    raise PurgeImageActionByIdGenericForbiddenError()
            await db_session.delete(image_row)
            return PurgeImageByIdActionResult(image=image_row)

    async def untag_image_from_registry(
        self, action: UntagImageFromRegistryAction
    ) -> UntagImageFromRegistryActionResult:
        async with self._db.begin_readonly_session() as db_session:
            image_row = await ImageRow.get(db_session, action.image_id, load_aliases=True)
            if not image_row:
                raise ImageNotFound
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(action.user_id):
                    raise UntagImageFromRegistryActionGenericForbiddenError()

            query = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == image_row.image_ref.registry
            )

            registry_info = (await db_session.execute(query)).scalar()

            if registry_info.type != ContainerRegistryType.HARBOR2:
                raise NotImplementedError("This feature is only supported for Harbor 2 registries")

        scanner = HarborRegistry_v2(self._db, image_row.image_ref.registry, registry_info)
        await scanner.untag(image_row.image_ref)
        return UntagImageFromRegistryActionResult(image=image_row)

    async def purge_images(self, action: PurgeImagesAction) -> PurgeImagesActionResult:
        errors = []
        image_canonicals = [image.name for image in action.images]
        arch_per_images = {image.name: image.architecture for image in action.images}
        reserved_bytes: int = 0
        responses: list[PurgeImageResponse] = []

        results = await self._agent_registry.purge_images(
            AgentId(action.agent_id), image_canonicals
        )

        for result in results.responses:
            image_canonical = result.image
            arch = arch_per_images[result.image]

            if not result.error:
                image_identifier = ImageIdentifier(image_canonical, arch)
                async with self._db.begin_session() as session:
                    image_row = await ImageRow.resolve(session, [image_identifier])
                    reserved_bytes += int(image_row.size_bytes)
                    responses.append(result)
            else:
                error_msg = f"Failed to purge images {image_canonical} from agent {action.agent_id}: {result.error}"
                log.error(error_msg)
                errors.append(error_msg)

        return PurgeImagesActionResult(
            results=responses, errors=errors, reserved_bytes=reserved_bytes
        )

    async def rescan_images(self, action: RescanImagesAction) -> RescanImagesActionResult:
        result = await rescan_images(self._db, action.registry, action.project)
        return RescanImagesActionResult(result=result)
