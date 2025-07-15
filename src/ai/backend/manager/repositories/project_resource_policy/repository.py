import sqlalchemy as sa

from ai.backend.common.decorators import create_layer_aware_repository_decorator
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.resource.creator import ProjectResourcePolicyCreator
from ai.backend.manager.data.resource.modifier import ProjectResourcePolicyModifier
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.errors.resource import ProjectResourcePolicyNotFound
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SASession

# Layer-specific decorator for project_resource_policy repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.PROJECT_RESOURCE_POLICY)


class ProjectResourcePolicyRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def _get_project_resource_policy_by_name(self, session: SASession, name: str) -> ProjectResourcePolicyRow:
        """Private method to get a project resource policy by name using an existing session.
        Raises ProjectResourcePolicyNotFound if not found."""
        query = sa.select(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == name)
        result = await session.execute(query)
        row = result.scalar_one_or_none()
        if row is None:
            raise ProjectResourcePolicyNotFound()
        return row

    @repository_decorator()
    async def create(self, creator: ProjectResourcePolicyCreator) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            fields = creator.fields_to_store()
            db_row = ProjectResourcePolicyRow(**fields)
            db_sess.add(db_row)
            await db_sess.flush()
            return db_row.to_dataclass()

    @repository_decorator()
    async def get_by_name(self, name: str) -> ProjectResourcePolicyData:
        async with self._db.begin_readonly_session() as db_sess:
            row = await self._get_project_resource_policy_by_name(db_sess, name)
            return row.to_dataclass()

    @repository_decorator()
    async def update(self, name: str, modifier: ProjectResourcePolicyModifier) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_project_resource_policy_by_name(db_sess, name)
            fields = modifier.fields_to_update()
            for key, value in fields.items():
                setattr(row, key, value)
            await db_sess.flush()
            return row.to_dataclass()

    @repository_decorator()
    async def delete(self, name: str) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_project_resource_policy_by_name(db_sess, name)
            await db_sess.delete(row)
            return row.to_dataclass()
