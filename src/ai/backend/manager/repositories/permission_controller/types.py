from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import BatchQuerierResult


class RoleBatchQuerierResult(BatchQuerierResult[RoleRow]):
    pass


class AssignedUserBatchQuerierResult(BatchQuerierResult[UserRow]):
    pass
