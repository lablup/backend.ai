from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import OperationType


def _make_domain_data() -> DomainData:
    now = datetime.now(tz=UTC)
    return DomainData(
        id=DomainID(uuid.uuid4()),
        name="default",
        description=None,
        is_active=True,
        created_at=now,
        modified_at=now,
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        allowed_docker_registries=[],
        dotfiles=b"",
        integration_name=None,
    )


class TestDomainDataEntityOperations:
    def test_includes_domain_admin_page_read(self) -> None:
        operations = _make_domain_data().entity_operations()

        assert RBACElementType.DOMAIN_ADMIN_PAGE in operations
        assert set(operations[RBACElementType.DOMAIN_ADMIN_PAGE]) == {OperationType.READ}

    def test_admin_resource_entries_unchanged(self) -> None:
        operations = _make_domain_data().entity_operations()

        assert set(operations[RBACElementType.VFOLDER]) == OperationType.admin_operations()
        assert set(operations[RBACElementType.USER]) == OperationType.admin_operations()
