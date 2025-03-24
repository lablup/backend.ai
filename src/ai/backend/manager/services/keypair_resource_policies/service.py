import logging

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
