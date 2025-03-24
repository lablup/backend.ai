import logging
from typing import Any

import sqlalchemy as sa

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.base import set_if_set
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    keypair_resource_policies,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.keypair_resource_policies.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policies.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
    DeleteKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policies.actions.modify_keypair_resource_policy import (
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
        name = action.name
        props = action.props

        data = {
            "name": name,
            "default_for_unspecified": DefaultForUnspecified[props.default_for_unspecified],
            "total_resource_slots": ResourceSlot.from_user_input(props.total_resource_slots, None),
            "max_session_lifetime": props.max_session_lifetime,
            "max_concurrent_sessions": props.max_concurrent_sessions,
            "max_concurrent_sftp_sessions": props.max_concurrent_sessions,
            "max_containers_per_session": props.max_containers_per_session,
            "idle_timeout": props.idle_timeout,
            "allowed_vfolder_hosts": props.allowed_vfolder_hosts,
        }
        set_if_set(props, data, "max_pending_session_count")
        set_if_set(
            props,
            data,
            "max_pending_session_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None) if v is not None else None,
        )
        async with self._db.begin_session() as db_sess:
            insert_query = (
                sa.insert(keypair_resource_policies)
                .values(data)
                .returning(*keypair_resource_policies.c)
            )
            result = await db_sess.execute(insert_query)
            inserted_row: KeyPairResourcePolicyRow = result.fetchone()

        return CreateKeyPairResourcePolicyActionResult(keypair_resource_policy=inserted_row)

    async def modify_keypair_resource_policy(
        self, action: ModifyKeyPairResourcePolicyAction
    ) -> ModifyKeyPairResourcePolicyActionResult:
        data: dict[str, Any] = {}
        name = action.name
        props = action.props

        set_if_set(
            props,
            data,
            "default_for_unspecified",
            clean_func=lambda v: DefaultForUnspecified[v],
        )
        set_if_set(
            props,
            data,
            "total_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "max_session_lifetime")
        set_if_set(props, data, "max_concurrent_sessions")
        set_if_set(props, data, "max_concurrent_sftp_sessions")
        set_if_set(props, data, "max_containers_per_session")
        set_if_set(props, data, "idle_timeout")
        set_if_set(props, data, "allowed_vfolder_hosts")
        set_if_set(props, data, "max_pending_session_count")
        set_if_set(
            props,
            data,
            "max_pending_session_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        async with self._db.begin_session() as db_sess:
            update_query = (
                sa.update(keypair_resource_policies)
                .values(data)
                .where(keypair_resource_policies.c.name == name)
                .returning(*keypair_resource_policies.c)
            )
            result = await db_sess.execute(update_query)
            updated_row: KeyPairResourcePolicyRow = result.fetchone()
        return ModifyKeyPairResourcePolicyActionResult(keypair_resource_policy=updated_row)

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
