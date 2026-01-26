from __future__ import annotations

import uuid

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.data.model_serving.types import (
    EndpointAccessValidationData,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.model_serving.exceptions import (
    GenericForbidden,
    InvalidAPIParameters,
)
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user_uuid


async def verify_user_access_scopes(db: ExtendedAsyncSAEngine, owner_uuid: uuid.UUID) -> None:
    user_data = current_user()
    if user_data is None or user_data.is_authorized is False:
        raise GenericForbidden("Only authorized requests may have access key scopes.")
    if owner_uuid is None or owner_uuid == user_data.user_id:
        return
    async with db.begin_readonly() as conn:
        try:
            await check_if_requester_is_eligible_to_act_as_target_user_uuid(
                conn,
                user_data.role,
                user_data.domain_name,
                owner_uuid,
            )
            return
        except ValueError as e:
            raise InvalidAPIParameters(str(e))
        except RuntimeError as e:
            raise GenericForbidden(str(e))


def validate_endpoint_access(
    validation_data: EndpointAccessValidationData,
) -> bool:
    """Validate user access to endpoint based on role.

    Returns True if the user has access to the endpoint, False otherwise.

    Access rules:
    - SUPERADMIN: Full access to all endpoints
    - ADMIN: Access to endpoints in their domain, except those owned by SUPERADMIN
    - USER/others: Access only to endpoints they own
    """
    user_data = current_user()
    if user_data is None:
        return False

    if validation_data.session_owner_id is None:
        return True

    match user_data.role:
        case UserRole.SUPERADMIN:
            return True
        case UserRole.ADMIN:
            # ADMIN cannot access SUPERADMIN's resources
            if validation_data.session_owner_role == UserRole.SUPERADMIN:
                return False
            return validation_data.domain == user_data.domain_name
        case _:
            return validation_data.session_owner_id == user_data.user_id
