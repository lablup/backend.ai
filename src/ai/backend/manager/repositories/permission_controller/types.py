from __future__ import annotations

from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.base.querier import BatchQuerierResult


class RoleBatchQuerierResult(BatchQuerierResult[RoleRow]):
    pass


class AssignedUserBatchQuerierResult(BatchQuerierResult[UserRow]):
    pass
