import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, SlotName, SlotTypes, VFolderHostPermission
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


async def test_domain_default_value_correctly_generated(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    domain_name = "test_domain_default"
    minimum_required_data = {
        "name": domain_name,
    }
    async with database_engine.begin_session() as session:
        await session.execute(sa.insert(DomainRow).values(minimum_required_data))

        result = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))

        assert result.description is None
        assert result.is_active is True
        assert result.integration_id is None
        assert result.total_resource_slots == ResourceSlot.from_user_input({}, None)
        assert result.allowed_vfolder_hosts == {}
        assert result.allowed_docker_registries == []
        assert result.dotfiles == b"\x90"


async def test_domain_data_insertion(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    domain_name = "test_data_insertion"
    data = {
        "name": domain_name,
        "description": "test description",
        "is_active": False,
        "total_resource_slots": ResourceSlot.from_user_input(
            {"a": "1", "b": "2g"}, {SlotName("a"): SlotTypes.COUNT, SlotName("b"): SlotTypes.BYTES}
        ),
        "allowed_vfolder_hosts": {
            "local:volume1": [
                "modify-vfolder",
            ]
        },
        "allowed_docker_registries": ["example_registry"],
        "integration_id": "test_integration_id",
        "dotfiles": b"test_dotfiles",
    }

    async with database_engine.begin_session() as session:
        await session.execute(sa.insert(DomainRow).values(data))

        result = await session.scalar(sa.select(DomainRow).where(DomainRow.name == domain_name))
        assert result.description == data["description"]
        assert result.is_active == data["is_active"]
        assert result.integration_id == data["integration_id"]
        assert result.total_resource_slots == data["total_resource_slots"]
        assert result.allowed_vfolder_hosts == {"local:volume1": {VFolderHostPermission.MODIFY}}
        assert result.allowed_docker_registries == data["allowed_docker_registries"]
        assert result.dotfiles == data["dotfiles"]
        assert result.created_at is not None
        assert result.modified_at is not None
