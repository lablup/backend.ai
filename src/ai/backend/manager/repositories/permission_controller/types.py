from ...models.rbac_models.role import RoleRow
from ...models.user import UserRow
from ...repositories.base import BatchQuerierResult


class RoleBatchQuerierResult(BatchQuerierResult[RoleRow]):
    pass


class AssignedUserBatchQuerierResult(BatchQuerierResult[UserRow]):
    pass
