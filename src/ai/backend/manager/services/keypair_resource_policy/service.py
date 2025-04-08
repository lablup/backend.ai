import logging

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    keypair_resource_policies,
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
        props = action.props

        async with self._db.begin_session() as db_sess:
            inserted_row = props.to_db_row()
            db_sess.add(inserted_row)
            await db_sess.flush()

        return CreateKeyPairResourcePolicyActionResult(keypair_resource_policy=inserted_row)

    async def modify_keypair_resource_policy(
        self, action: ModifyKeyPairResourcePolicyAction
    ) -> ModifyKeyPairResourcePolicyActionResult:
        name = action.name
        props = action.props

        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Keypair resource policy with name {name} not found.")
            props.set_attr(row)

        return ModifyKeyPairResourcePolicyActionResult(keypair_resource_policy=row)

    async def delete_keypair_resource_policy(
        self, action: DeleteKeyPairResourcePolicyAction
    ) -> DeleteKeyPairResourcePolicyActionResult:
        name = action.name
        async with self._db.begin_session() as db_sess:
            delete_query = (
                sa.delete(keypair_resource_policies)
                .where(keypair_resource_policies.c.name == name)
                .returning(*keypair_resource_policies.c)
            )
            result = await db_sess.execute(delete_query)
            deleted_row = result.fetchone()
        return DeleteKeyPairResourcePolicyActionResult(keypair_resource_policy=deleted_row)
