import logging

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ObjectNotFound
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
    DeleteKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
    ModifyKeyPairResourcePolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KeypairResourcePolicyService:
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def create_keypair_resource_policy(
        self, action: CreateKeyPairResourcePolicyAction
    ) -> CreateKeyPairResourcePolicyActionResult:
        to_store = action.creator.fields_to_store()

        async with self._db.begin_session() as db_sess:
            db_row = KeyPairResourcePolicyRow(**to_store)
            db_sess.add(db_row)
            result = db_row.to_dataclass()

        return CreateKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def modify_keypair_resource_policy(
        self, action: ModifyKeyPairResourcePolicyAction
    ) -> ModifyKeyPairResourcePolicyActionResult:
        name = action.name
        props = action.modifier

        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row: KeyPairResourcePolicyRow = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            to_update = props.fields_to_update()
            for key, value in to_update.items():
                setattr(row, key, value)
            result = row.to_dataclass()

        return ModifyKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def delete_keypair_resource_policy(
        self, action: DeleteKeyPairResourcePolicyAction
    ) -> DeleteKeyPairResourcePolicyActionResult:
        name = action.name
        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            db_row = (await db_sess.execute(query)).scalar_one_or_none()
            if not db_row:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            await db_sess.delete(db_row)
            result = db_row.to_dataclass()

        return DeleteKeyPairResourcePolicyActionResult(keypair_resource_policy=result)
