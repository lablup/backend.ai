import uuid

from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.model_serving.exceptions import (
    GenericForbidden,
    InvalidAPIParameters,
)
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user_uuid


async def verify_user_access_scopes(
    db: ExtendedAsyncSAEngine, requester_ctx: RequesterCtx, owner_uuid: uuid.UUID
) -> None:
    if requester_ctx.is_authorized is False:
        raise GenericForbidden("Only authorized requests may have access key scopes.")
    if owner_uuid is None or owner_uuid == requester_ctx.user_id:
        return
    async with db.begin_readonly() as conn:
        try:
            await check_if_requester_is_eligible_to_act_as_target_user_uuid(
                conn,
                requester_ctx.user_role,
                requester_ctx.domain_name,
                owner_uuid,
            )
            return
        except ValueError as e:
            raise InvalidAPIParameters(str(e))
        except RuntimeError as e:
            raise GenericForbidden(str(e))
