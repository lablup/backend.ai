import functools
import logging

import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import AgentId, ImageAlias
from ai.backend.common.utils import join_non_empty
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.errors.exceptions import ImageNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageRow,
    scan_single_image,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionDBError,
    AliasImageActionResult,
    AliasImageActionValueError,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitActionResult,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionNoSuchAliasError,
    DealiasImageActionResult,
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
    PurgeImageActionByIdObjectDBError,
    PurgeImageActionByIdObjectNotFoundError,
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgedImagesData,
    PurgeImageAction,
    PurgeImageActionResult,
    PurgeImagesAction,
    PurgeImagesActionResult,
)
from ai.backend.manager.services.image.actions.scan_image import (
    ScanImageAction,
    ScanImageActionResult,
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
                if not image_row.is_owned_by(action.user_id):
                    raise ForgetImageActionGenericForbiddenError()
            await image_row.mark_as_deleted(session)
        return ForgetImageActionResult(image=image_row.to_dataclass())

    async def forget_image_by_id(
        self, action: ForgetImageByIdAction
    ) -> ForgetImageByIdActionResult:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.get(session, action.image_id, load_aliases=True)
            if not image_row:
                raise ForgetImageActionByIdObjectNotFoundError()
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_owned_by(action.user_id):
                    raise ForgetImageActionByIdGenericForbiddenError()
            await image_row.mark_as_deleted(session)
        return ForgetImageByIdActionResult(image=image_row.to_dataclass())

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
        except sa.exc.DBAPIError as e:
            raise AliasImageActionDBError(e)
        return AliasImageActionResult(
            image_id=image_alias.image_id,
            image_alias=image_alias.to_dataclass(),
        )

    async def dealias_image(self, action: DealiasImageAction) -> DealiasImageActionResult:
        async with self._db.begin_session() as session:
            existing_alias = await session.scalar(
                sa.select(ImageAliasRow).where(ImageAliasRow.alias == action.alias),
            )
            if existing_alias is None:
                raise DealiasImageActionNoSuchAliasError()
            await session.delete(existing_alias)

        return DealiasImageActionResult(
            image_id=existing_alias.image_id,
            image_alias=existing_alias.to_dataclass(),
        )

    async def modify_image(self, action: ModifyImageAction) -> ModifyImageActionResult:
        props = action.modifier

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
                to_update = props.fields_to_update()
                for key, value in to_update.items():
                    setattr(image_row, key, value)
        except (ValueError, sa.exc.DBAPIError):
            raise ModifyImageActionValueError

        return ModifyImageActionResult(image=image_row.to_dataclass())

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
                if not image_row.is_owned_by(action.user_id):
                    raise PurgeImageActionByIdGenericForbiddenError()
            try:
                await db_session.delete(image_row)
            except sa.exc.DBAPIError as e:
                raise PurgeImageActionByIdObjectDBError(e)
            return PurgeImageByIdActionResult(image=image_row.to_dataclass())

    async def untag_image_from_registry(
        self, action: UntagImageFromRegistryAction
    ) -> UntagImageFromRegistryActionResult:
        async with self._db.begin_readonly_session() as db_session:
            image_row = await ImageRow.get(db_session, action.image_id, load_aliases=True)
            if not image_row:
                raise ImageNotFound
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_owned_by(action.user_id):
                    raise UntagImageFromRegistryActionGenericForbiddenError()

            query = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == image_row.image_ref.registry
            )
            if image_row.image_ref.project:
                query = query.where(ContainerRegistryRow.project == image_row.image_ref.project)

            registry_info = (await db_session.execute(query)).scalar()

            if registry_info.type != ContainerRegistryType.HARBOR2:
                raise NotImplementedError("This feature is only supported for Harbor 2 registries")

        scanner = HarborRegistry_v2(self._db, image_row.image_ref.registry, registry_info)
        await scanner.untag(image_row.image_ref)
        return UntagImageFromRegistryActionResult(image=image_row.to_dataclass())

    async def purge_image(self, action: PurgeImageAction) -> PurgeImageActionResult:
        force, noprune = action.force, action.noprune
        agent_id = action.agent_id
        image_canonical = action.image.name
        arch = action.image.architecture

        async with self._db.begin_session() as session:
            image_identifier = ImageIdentifier(image_canonical, arch)
            image_row = await ImageRow.resolve(session, [image_identifier])

        results = await self._agent_registry.purge_images(
            AgentId(agent_id),
            PurgeImagesReq(images=[image_canonical], force=force, noprune=noprune),
        )

        error = None
        for result in results.responses:
            if result.error:
                error = (
                    f"Failed to purge image {image_canonical} from agent {agent_id}: {result.error}"
                )

        return PurgeImageActionResult(
            purged_image=image_row.to_dataclass(),
            error=error,
            reserved_bytes=image_row.size_bytes,
        )

    async def purge_images(self, action: PurgeImagesAction) -> PurgeImagesActionResult:
        errors = []
        total_reserved_bytes = 0
        force, noprune = action.force, action.noprune

        purged_images_data_list: list[PurgedImagesData] = []
        for key in action.keys:
            agent_id = key.agent_id
            images = key.images

            image_canonicals = [image.name for image in images]
            arch_per_images = {image.name: image.architecture for image in images}

            purged_images_data = PurgedImagesData(purged_images=[], agent_id=agent_id)

            results = await self._agent_registry.purge_images(
                AgentId(agent_id),
                PurgeImagesReq(images=image_canonicals, force=force, noprune=noprune),
            )

            for result in results.responses:
                if not result.error:
                    async with self._db.begin_session() as session:
                        image_canonical = result.image
                        arch = arch_per_images[image_canonical]
                        image_identifier = ImageIdentifier(image_canonical, arch)
                        image_row = await ImageRow.resolve(session, [image_identifier])
                        purged_images_data.purged_images.append(image_canonical)
                        total_reserved_bytes += image_row.size_bytes
                else:
                    errors.append(
                        f"Failed to purge image {image_canonical} from agent {agent_id}: {result.error}"
                    )

            purged_images_data_list.append(purged_images_data)

        return PurgeImagesActionResult(
            purged_images=purged_images_data_list,
            errors=errors,
            total_reserved_bytes=total_reserved_bytes,
        )

    async def scan_image(self, action: ScanImageAction) -> ScanImageActionResult:
        image_canonical = action.canonical
        architecture = action.architecture

        async with self._db.begin_session() as db_session:
            image_row = await ImageRow.resolve(
                db_session,
                [
                    ImageIdentifier(image_canonical, architecture),
                ],
            )
            join = functools.partial(join_non_empty, sep="/")
            registry_key = join(
                image_row.registry,
                image_row.project,
            )

            result = await scan_single_image(db_session, registry_key, image_row, image_canonical)
            return ScanImageActionResult(image=result.images[0], errors=result.errors)

    async def clear_image_custom_resource_limit(
        self, action: ClearImageCustomResourceLimitAction
    ) -> ClearImageCustomResourceLimitActionResult:
        async with self._db.begin_session() as db_sess:
            image_row = await ImageRow.resolve(
                db_sess, [ImageIdentifier(action.image_canonical, action.architecture)]
            )
            image_row._resources = {}
            await db_sess.flush()
        return ClearImageCustomResourceLimitActionResult(image_data=image_row.to_dataclass())
