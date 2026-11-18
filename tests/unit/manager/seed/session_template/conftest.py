from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
import yaml

from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_policy.row import (
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

# The user the session templates belong to, inserted by `template_owner` so the session
# template tests do not apply the user kind.
_TEMPLATE_OWNER: dict[str, Any] = {
    "uuid": "0198a5a0-0000-7000-8000-000000001201",
    "username": "owner",
    "email": "owner@example.com",
    "domain_id": "0198a5a0-0000-7000-8000-000000001202",
    "domain_name": "templates",
    "resource_policy": "templates",
}

# Session template files written for the tests, one template per file, neither in a
# project. `task` states every field; `cluster` leaves the optional ones to their defaults.
_SESSION_TEMPLATES: dict[str, dict[str, Any]] = {
    "task.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001211",
        "user_id": _TEMPLATE_OWNER["uuid"],
        "type": "task",
        "name": "python",
        "is_active": True,
        "template": {
            "api_version": "6",
            "kind": "task_template",
            "metadata": {"name": "python"},
            "spec": {"kernel": {"image": "python"}},
        },
    },
    "cluster.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001212",
        "user_id": _TEMPLATE_OWNER["uuid"],
        "type": "cluster",
        "template": {
            "api_version": "6",
            "kind": "cluster_template",
            "mode": "single-node",
            "metadata": {"name": "python"},
            "spec": {
                "nodes": [
                    {"role": "main", "session_template": "0198a5a0-0000-7000-8000-000000001211"}
                ]
            },
        },
    },
}


@pytest.fixture
async def template_owner(db: ExtendedAsyncSAEngine) -> str:
    """The owner of the session templates in the graph, in the `templates` domain."""
    owner = _TEMPLATE_OWNER
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(DomainRow).values(id=owner["domain_id"], name=owner["domain_name"])
        )
        await sess.execute(
            sa.insert(UserResourcePolicyRow).values(
                name=owner["resource_policy"],
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
            )
        )
        await sess.execute(sa.insert(UserRow).values(**owner))
        await sess.execute(
            sa.insert(VirtualEntityRow).values(
                entity_type=UserEntityType(), entity_id=owner["uuid"]
            )
        )
    return str(owner["uuid"])


@pytest.fixture
def session_template_files(tmp_path: Path) -> Path:
    """A directory of session template seed files, the shape `seeds/manager/session_template/`
    has."""
    directory = tmp_path / "session_template"
    directory.mkdir()
    for file_name, template in _SESSION_TEMPLATES.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "session_template", "version": 1, "items": [template]})
        )
    return directory


@pytest.fixture
def session_template_seed_dir(session_template_files: Path, template_owner: str) -> Path:
    """The session template files, with their owner already written."""
    return session_template_files


@pytest.fixture
def task_template_id() -> str:
    return str(_SESSION_TEMPLATES["task.yaml"]["id"])
